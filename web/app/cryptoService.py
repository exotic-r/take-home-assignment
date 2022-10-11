import json
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from typing import Union

import requests
import logging

from eth_typing import HexStr
from web3 import Web3
from config import *
from exceptions import TransactionNotFoundException, TransactionNotFoundExceptionByTimeRange
from utils import *


class CryptoService:
    def __init__(self, redis):
        self.redis = redis
        self.w3 = self.__connect_alchemy()

    def __connect_alchemy(self):
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
        if cached_data:
            return Decimal(cached_data.decode('utf-8').strip('"'))

        transaction = self.w3.eth.get_transaction(tx_hash)
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        timestamp = self.w3.eth.getBlock(transaction['blockNumber']).timestamp

        fee, _ = self.calculate_tx_fee(transaction['gasPrice'], receipt['gasUsed'], timestamp)
        self.redis.set(tx_hash, json.dumps(str(fee)))
        return fee

    def get_transactions_fee_by_time_range(self, start_time: int, end_time: int) -> Decimal:
        start_block, end_block = self.get_block_number(start_time), self.get_block_number(end_time)

        def request_fees(page_: int, offset_: int):
            params = get_ether_scan_params(start_block, end_block, page_, offset_)
            response = requests.get(ETHER_SCAN_BASE_URL, params=params)
            if response.status_code != HTTPStatus.OK:
                raise response.raise_for_status()

            response_json = response.json()
            if response_json['message'] == 'No transactions found':
                raise TransactionNotFoundExceptionByTimeRange(
                    start_time, end_time)

            _fees = []
            status_code_ = None

            for result in response_json['result']:
                tx_hash = result['hash']
                cached_data = self.redis.get(tx_hash)
                if cached_data:
                    _fees.append(Decimal(cached_data.decode('utf-8').strip('"')))
                else:
                    fee, status_code_ = self.calculate_tx_fee(result['gasPrice'], result['gasUsed'],
                                                              result['timeStamp'])
                    if status_code_ in (550, HTTPStatus.TOO_MANY_REQUESTS):
                        break
                    _fees.append(fee)
                    self.redis.set(tx_hash, json.dumps(str(fee)))
            return _fees, status_code_

        # number of transactions to retrieve for each http call to ether scan
        # for the purpose of this exercise, we will keep it small
        offset = 10
        page = 1
        fees = []

        while len(fees) % offset == 0:
            fees, status_code = request_fees(page, offset)
            fees.extend(fees)

            if status_code == HTTPStatus.TOO_MANY_REQUESTS:
                break
            page += 1
        return fees

    def get_block_number(self, time_stamp: int) -> int:
        cached_data = self.redis.get(time_stamp)
        if cached_data:
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

    def calculate_tx_fee(self, gasPrice, gasUsed, time_stamp):
        tx_cost_wei = int(float(gasPrice) * float(gasUsed))
        tx_cost_eth = Web3.fromWei(tx_cost_wei, "ether")

        date_time = CryptoService.__timestamp_to_dateTime(int(time_stamp))
        rate, status_code = self.__get_fx_rate(date_time)

        if not rate:
            return 0, status_code

        tx_cost_usdt = rate * tx_cost_eth

        logging.info(f"tx cost - USDT: {tx_cost_usdt:.2f}, wei: {tx_cost_wei:.0f},"
                     f" eth: {tx_cost_eth:.5f}, fx rate: {rate:.2f}")

        return tx_cost_usdt, status_code

    def __get_fx_rate(self, date_time) -> tuple[Decimal, int]:
        """
        Use coin API to get  the fx rate of ETH/USDT at date_time
        :param date_time:
        :return:
        """
        # return Decimal(1300)
        status_code = HTTPStatus.OK
        cached_data = self.redis.get(date_time)

        if cached_data:
            return Decimal(cached_data.decode('utf-8').strip('"')), status_code

        headers = {'X-CoinAPI-Key': COIN_API_KEY}
        params = {'time': date_time}
        response = requests.get(
            COIN_API_EXCHANGE_RATE_URL, params=params, headers=headers)
        if response.status_code != HTTPStatus.OK:
            if response.status_code == 550:
                logging.error(
                    f"Error retrieving fx rate for date time: {date_time}, returning fx rate 0")
                return Decimal(0), 550
            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                logging.error(f"Error retrieving fx rate for date time: {date_time} due to too many requests, "
                              f"returning fx rate 0")
                return Decimal(0), HTTPStatus.TOO_MANY_REQUESTS
            raise response.raise_for_status()

        response_json = response.json()

        fx_rate = Decimal(response_json['rate'])
        self.redis.set(date_time, json.dumps(str(fx_rate)))

        return fx_rate, status_code

    @staticmethod
    def __timestamp_to_dateTime(timestamp: int) -> str:
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
