from datetime import datetime
from decimal import Decimal
from http import HTTPStatus

import requests
from web3 import Web3

from config import *


class CryptoService:

    @staticmethod
    def get_transaction_fee(tx_hash: str) -> Decimal:
        params = {
            'module': 'account',
            'action': 'tokentx',
            'contractaddress': '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2',
            'address': '0x4e83362442b8d1bec281594cea3050c8eb01311c',
            'page': 1,
            'offset': 100,
            'startblock': 0,
            'endblock': 27025780,
            'sort': 'asc',
            'apikey': ETHER_SCAN_API_KEY,
        }

        response = requests.get(ETHER_SCAN_BASE_URL, params=params)
        if response.status_code != HTTPStatus.OK:
            print("Error getting transaction details")
            return -1

        response_json = response.json()
        if response_json['message'] == 'No transactions found':
            print("Error")
            return -1

        result = response_json['result'][0]
        tx_cost_wei = int(float(result['gasPrice']) * float(result['gasUsed']))
        tx_cost_eth = Web3.fromWei(tx_cost_wei, "ether")

        time_string = CryptoService.__timestamp_to_dateTime(int(result['timeStamp']))
        rate = CryptoService.__get_fx_rate(time_string)
        tx_cost_usdt = rate * tx_cost_eth

        print(f"tx cost - USDT: {tx_cost_usdt}, wei: {tx_cost_wei},"
              f" eth: {tx_cost_eth}, fx rate: {rate}")
        return tx_cost_usdt

    @staticmethod
    def __get_fx_rate(time) -> Decimal:
        # return Decimal(1300)

        headers = {'X-CoinAPI-Key': COIN_API_KEY}
        params = {'time': time}
        response = requests.get(COIN_API_EXCHANGE_RATE_URL, params=params, headers=headers)
        response_json = response.json()

        return Decimal(response_json['rate'])

    @staticmethod
    def __timestamp_to_dateTime(timestamp: int) -> str:
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
