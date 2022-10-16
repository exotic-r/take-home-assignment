import json
import logging
from decimal import Decimal
from http import HTTPStatus
from typing import Union, Any

import requests
from eth_typing import HexStr
from redis.client import Redis
from web3 import Web3

from exceptions import *
from utils import *


class CryptoService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.w3 = self.__connect_alchemy()
        self.last_processed_block = START_BLOCK

    @staticmethod
    def __connect_alchemy() -> Web3:
        """
        connect to web3 http provider
        :return: Web3 instance
        """
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
        :return: fee
        """
        cached_data = self.redis.get(tx_hash)
        if cached_data is not None:
            return Decimal(cached_data.decode('utf-8').strip('"'))

        transaction = self.w3.eth.get_transaction(tx_hash)

        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        timestamp = self.w3.eth.get_block(
            transaction['blockNumber']).get('timestamp')

        fee, _ = self.__calculate_tx_fee(
            transaction['gasPrice'], receipt['gasUsed'], timestamp)
        self.redis.set(tx_hash, json.dumps(str(fee)))
        return fee

    def get_transactions_fee_by_time_range(self, start_time: int, end_time: int) -> tuple[list[Decimal], int]:
        """
        Get a list of transaction fees between 2 time range
        :param start_time:
        :param end_time:
        :return: fees
        """
        start_block, end_block = self.__get_block_number(
            start_time), self.__get_block_number(end_time)

        if 'Error! Invalid timestamp' in (start_block, end_block):
            raise InvalidTimestamp(start_time, end_time)

        seen_transactions = set()

        def request_fees(page_: int):
            params = get_ether_scan_params(
                start_block, end_block, page_, ETHER_SCAN_OFFSET)
            response = requests.get(ETHER_SCAN_BASE_URL, params=params)
            if response.status_code != HTTPStatus.OK:
                raise response.raise_for_status()

            response_json = response.json()

            chuck = []
            status_code_ = HTTPStatus.OK
            last_processed_timestamp = -1

            if response_json['result']:
                for result in response_json['result']:
                    tx_hash = result['hash']
                    if tx_hash in seen_transactions:
                        continue

                    seen_transactions.add(tx_hash)
                    cached_data = self.redis.get(tx_hash)
                    if cached_data is not None:
                        chuck.append(
                            Decimal(cached_data.decode('utf-8').strip('"')))
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
        fees = []

        while True:
            fees_chuck, status_code, last_processed_time = request_fees(page)
            fees.extend(fees_chuck)

            if len(fees) >= MAX_FEES_PER_REQUEST:
                fees = fees[:MAX_FEES_PER_REQUEST]
                logging.info(
                    f"Processed {len(fees)} transactions, use separate request to get fees")
                break
            if status_code == HTTPStatus.TOO_MANY_REQUESTS:
                break
            if not len(fees) or not fees_chuck:
                break

            page += 1

        # TODO: since there is a max_cap on the number of transactions to return in a single api call
        # could we useful to use <last_processed_time> to inform the caller the last processed time
        return fees, last_processed_time

    def get_historic_fees(self):
        """
        Background task to get all the historical fees
        :return: None
        """
        page = 0

        while True:
            params = get_ether_scan_params(
                self.last_processed_block, END_BLOCK, page, ETHER_SCAN_OFFSET)
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

    @staticmethod
    def __get_block_number(timestamp: int) -> Union[str, Any]:
        """
        Get eth block number by timestamp
        :param timestamp:
        :return: block number
        """
        params = {
            'module': 'block',
            'action': 'getblocknobytime',
            'timestamp': timestamp,
            'closest': 'before',
            'apikey': ETHER_SCAN_API_KEY,
        }
        response = requests.get(ETHER_SCAN_BASE_URL, params=params)
        if response.status_code != HTTPStatus.OK:
            raise response.raise_for_status()

        response_json = response.json()
        block_number = response_json['result']

        return block_number

    def __calculate_tx_fee(self, gasPrice, gasUsed, timestamp):
        """
        Use Web3 library to get exchange rate by timestamp
        :param gasPrice:
        :param gasUsed:
        :param timestamp:
        :returns: fee in USDC, status code
        """
        tx_cost_wei = int(float(gasPrice) * float(gasUsed))
        tx_cost_eth = Web3.fromWei(tx_cost_wei, "ether")

        rate, status_code = self.__get_fx_rate(timestamp)

        if not rate:
            return 0, status_code

        tx_cost_usdt = rate * tx_cost_eth

        logging.info(f"timestamp: {timestamp}, tx cost - USDT: {tx_cost_usdt:.2f}, wei: {tx_cost_wei:.0f},"
                     f" eth: {tx_cost_eth:.5f}, fx rate: {rate:.2f}")

        return tx_cost_usdt, status_code

    @staticmethod
    def __get_fx_rate(timestamp) -> tuple[Decimal, int]:
        """
        Use coin API to get  the fx rate of ETH/USDT at date_time
        :param timestamp:
        :return: exchange rate, status code
        """
        status_code = HTTPStatus.OK

        params = {'fsym': 'ETH', 'tsym': 'USDC',
                  'limit': 1, 'toTs': timestamp, 'api_key': CRYPTO_COMPARE_API_KEY}
        response = requests.get(
            CRYPTO_COMPARE_HISTORY_HOUR_URL, params=params)

        if response.status_code != HTTPStatus.OK:
            if response.status_code == 550:
                logging.error(
                    f"Error retrieving fx rate for timestamp: {timestamp}, returning fx rate 0")
                return Decimal(0), 550
            return Decimal(0), 500

        response_json = response.json()
        if response_json.get('Response') == 'Error':
            # Crypto Compare returns 200 but the response is actually an 'error'
            # due to too many requests (429)
            if response_json.get('Message') == 'You are over your rate limit please upgrade your account!':
                logging.error(f"Error retrieving fx rate for date time: {timestamp} due to too many requests, "
                              f"returning fx rate 0")
                status_code = HTTPStatus.TOO_MANY_REQUESTS
            return Decimal(0), status_code

        if response_json.get('Response') != 'Success':
            logging.error(
                "Failed to get ETH/USDC exchange rate, defaulting to 0")
            return Decimal(0), 500

        try:
            # TODO: do better finding the closest price by timestamp
            fx_rate = Decimal(response_json['Data']['Data'][1]['open'])
        except RuntimeError as e:
            logging.error(
                f"Failed to get ETH/USDC exchange rate, defaulting to 0 error_msg: {e}")
            return Decimal(0), 500

        return fx_rate, status_code
