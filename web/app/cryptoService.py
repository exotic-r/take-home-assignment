from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from typing import Union

import requests
import logging

from web3 import Web3
from config import *
from exceptions import TransactionNotFoundException, TransactionNotFoundExceptionByTimeRange


class CryptoService:

    @staticmethod
    def get_ether_scan_params(start_block, end_block) -> dict:
        return {
            'module': 'account',
            'action': 'tokentx',
            'contractaddress': '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2',
            'address': '0x4e83362442b8d1bec281594cea3050c8eb01311c',
            'page': 1,
            'offset': 100,
            'startblock': start_block,
            'endblock': end_block,
            'sort': 'asc',
            'apikey': ETHER_SCAN_API_KEY,
        }

    @classmethod
    def get_transaction_fee_by_tx_hash(cls, tx_hash: str) -> Union[int, Decimal]:
        response = requests.get(ETHER_SCAN_BASE_URL, params={})
        if response.status_code != HTTPStatus.OK:
            raise response.raise_for_status()

        response_json = response.json()
        if response_json['message'] == 'No transactions found':
            raise TransactionNotFoundException(tx_hash)

        result = response_json['result'][0]
        return CryptoService.calculate_tx_fee(result['gasPrice'], result['gasUsed'], result['timeStamp'])

    @classmethod
    def get_transaction_fee_by_time_range(cls, start_time: int, end_time: int):
        start_block, end_block = CryptoService.get_block_number(start_time), CryptoService.get_block_number(end_time)
        response = requests.get(ETHER_SCAN_BASE_URL, params=CryptoService.get_ether_scan_params(start_block, end_block))

        response_json = response.json()
        if response_json['message'] == 'No transactions found':
            raise TransactionNotFoundExceptionByTimeRange(start_time, end_time)

        fees = [CryptoService.calculate_tx_fee(result['gasPrice'], result['gasUsed'], result['timeStamp'])
                for result in response_json['result']]
        return fees

    @classmethod
    def get_block_number(cls, time_stamp: int) -> int:
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

        return int(response_json['result'])

    @classmethod
    def calculate_tx_fee(cls, gasPrice, gasUsed, timeStamp):
        tx_cost_wei = int(float(gasPrice) * float(gasUsed))
        tx_cost_eth = Web3.fromWei(tx_cost_wei, "ether")

        time_string = CryptoService.__timestamp_to_dateTime(int(timeStamp))
        rate = CryptoService.__get_fx_rate(time_string)
        tx_cost_usdt = rate * tx_cost_eth

        logging.info(f"tx cost - USDT: {tx_cost_usdt:.2f}, wei: {tx_cost_wei:.0f},"
                     f" eth: {tx_cost_eth:.2f}, fx rate: {rate:.2f}")

        return tx_cost_usdt

    @classmethod
    def __get_fx_rate(cls, time) -> Decimal:
        # return Decimal(1300)

        headers = {'X-CoinAPI-Key': COIN_API_KEY}
        params = {'time': time}
        response = requests.get(COIN_API_EXCHANGE_RATE_URL, params=params, headers=headers)
        response_json = response.json()

        return Decimal(response_json['rate'])

    @staticmethod
    def __timestamp_to_dateTime(timestamp: int) -> str:
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
