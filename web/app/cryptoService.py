import json
import logging
from decimal import Decimal
from http import HTTPStatus

import requests
from eth_typing import HexStr
from web3 import Web3

from exceptions import *
from utils import *


class CryptoService:
    def __init__(self, redis):
        self.redis = redis
        self.w3 = self.__connect_alchemy()
        self.last_processed_block = START_BLOCK

    @staticmethod
    def __connect_alchemy():
        w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

        if w3.isConnected():
            logging.info("Successfully connected to Alchemy")
        else:
            raise RuntimeError("Error while connecting to Alchemy")

        return w3

    def get_transaction_fee_by_tx_hash(self, tx_hash: HexStr) -> Decimal:
        """
        Get transactions fee for a single tx hash
        If the fee is not stored in redis, query ether scan to get the fee
        """
        cached_data = self.redis.get(tx_hash)
        if cached_data is not None:
            return Decimal(cached_data.decode('utf-8').strip('"'))

        transaction = self.w3.eth.get_transaction(tx_hash)

        # verify it is Uniswap transaction
        to_, from_ = transaction['to'], transaction['from']
        if UNISWAP_ADDRESS not in (to_, from_):
            raise TransactionNotUniswap(tx_hash)

        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        timestamp = self.w3.eth.getBlock(transaction['blockNumber']).timestamp

        fee, _ = self.__calculate_tx_fee(transaction['gasPrice'], receipt['gasUsed'], timestamp)
        self.redis.set(tx_hash, json.dumps(str(fee)))
        return fee

    def get_transactions_fee_by_time_range(self, start_time: int, end_time: int) -> tuple[list[Decimal], int]:

        start_block, end_block = self.__get_block_number(start_time), self.__get_block_number(end_time)

        def request_fees(page_: int):
            params = get_ether_scan_params(start_block, end_block, page_, ETHER_SCAN_OFFSET)
            response = requests.get(ETHER_SCAN_BASE_URL, params=params)
            if response.status_code != HTTPStatus.OK:
                raise response.raise_for_status()

            response_json = response.json()
            if response_json['message'] == 'No transactions found' or not response_json.get('result'):
                raise TransactionNotFoundExceptionByTimeRange(
                    start_time, end_time)

            chuck = []
            status_code_ = HTTPStatus.OK

            for result in response_json['result']:
                tx_hash = result['hash']
                cached_data = self.redis.get(tx_hash)
                if cached_data is not None:
                    chuck.append(Decimal(cached_data.decode('utf-8').strip('"')))
                else:
                    fee, status_code_ = self.__calculate_tx_fee(result['gasPrice'], result['gasUsed'],
                                                                result['timeStamp'])
                    if status_code_ in (550, HTTPStatus.TOO_MANY_REQUESTS):
                        break
                    chuck.append(fee)
                    self.redis.set(tx_hash, json.dumps(str(fee)))

            last_processed_timestamp = response_json['result'][-1]['timeStamp']
            return chuck, status_code_, last_processed_timestamp

        page = 1
        last_processed_time = 0
        fees = []

        while len(fees) % ETHER_SCAN_OFFSET == 0:
            fees_chuck, status_code, last_processed_time = request_fees(page)
            fees.extend(fees_chuck)

            if len(fees) >= MAX_FEES_PER_REQUEST:
                logging.info(f"Processed {len(fees)} transactions, use separate request to get fees")
                break
            if status_code == HTTPStatus.TOO_MANY_REQUESTS:
                break

            page += 1

        # TODO: handle letting requestor know up to what timstamp have been processed

        return fees, last_processed_time

    def get_historic_fees(self):
        page = 0

        while True:
            params = get_ether_scan_params(self.last_processed_block, END_BLOCK, page, ETHER_SCAN_OFFSET)
            response = requests.get(ETHER_SCAN_BASE_URL, params=params)
            if response.status_code != HTTPStatus.OK:
                raise response.raise_for_status()

            response_json = response.json()
            result = response_json['result']

            if not result:
                logging.info("Finished processing all historic transactions")
                break

            for result in response_json['result']:
                tx_hash = result['hash']
                cached_data = self.redis.get(tx_hash)
                if cached_data is None:
                    fee, status_code_ = self.__calculate_tx_fee(result['gasPrice'], result['gasUsed'],
                                                                result['timeStamp'])
                    if status_code_ in (550, HTTPStatus.TOO_MANY_REQUESTS):
                        break
                    self.redis.set(tx_hash, json.dumps(str(fee)))
                self.last_processed_block = result['blockNumber']


    def __get_block_number(self, time_stamp: int) -> int:
        cached_data = self.redis.get(time_stamp)
        if cached_data is not None:
            return cached_data.decode('utf-8')

        params = {
            'module': 'block',
            'action': 'getblocknobytime',
            'timestamp': time_stamp,
            'closest': 'before',
            'apikey': ETHER_SCAN_API_KEY,
        }
        response = requests.get(ETHER_SCAN_BASE_URL, params=params)
        if response.status_code != HTTPStatus.OK:
            raise response.raise_for_status()

        response_json = response.json()
        block_number = response_json['result']
        self.redis.set(time_stamp, json.dumps(block_number))

        return block_number

    def __calculate_tx_fee(self, gasPrice, gasUsed, time_stamp):
        tx_cost_wei = int(float(gasPrice) * float(gasUsed))
        tx_cost_eth = Web3.fromWei(tx_cost_wei, "ether")

        rate, status_code = self.__get_fx_rate(time_stamp)

        if not rate:
            return 0, status_code

        tx_cost_usdt = rate * tx_cost_eth

        logging.info(f"timestamp: {time_stamp}, tx cost - USDT: {tx_cost_usdt:.2f}, wei: {tx_cost_wei:.0f},"
                     f" eth: {tx_cost_eth:.5f}, fx rate: {rate:.2f}")

        return tx_cost_usdt, status_code

    def __get_fx_rate(self, timestamp) -> tuple[Decimal, int]:
        """
        Use coin API to get  the fx rate of ETH/USDT at date_time
        :param timestamp:
        :return:
        """
        status_code = HTTPStatus.OK

        cached_data = self.redis.get(timestamp)
        if cached_data is not None:
            return Decimal(cached_data.decode('utf-8').strip('"')), status_code

        headers = {'Apikey': CRYPTO_COMPARE_API_KEY}
        params = {'fsym': 'ETH', 'tsym': 'USDC', 'limit': 1, 'toTs': 1665503460}
        response = requests.get(CRYPTO_COMPARE_URL, params=params, headers=headers)

        if response.status_code != HTTPStatus.OK:
            if response.status_code == 550:
                logging.error(
                    f"Error retrieving fx rate for timestamp: {timestamp}, returning fx rate 0")
                return Decimal(0), 550
            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                logging.error(f"Error retrieving fx rate for date time: {timestamp} due to too many requests, "
                              f"returning fx rate 0")
                return Decimal(0), HTTPStatus.TOO_MANY_REQUESTS
            raise response.raise_for_status()

        response_json = response.json()
        if response_json.get('Response') != 'Success':
            logging.error("Failed to retrieve ETH/USDC exchange rate, defaulting to 0")
            return Decimal(0), 500

        fx_rate = Decimal(response_json['Data']['Data'][0]['open'])
        self.redis.set(timestamp, json.dumps(str(fx_rate)))

        return fx_rate, status_code
