import unittest
import requests
from unittest import TestCase

class TestCryptoService(TestCase):
    base_url = 'http://0.0.0.0:8000/v1'

    def test_successfuly_get_transaction_fee_by_tx_hash(self):
        # https://etherscan.io/tx/0x8d3e463cdab56374495e5e26b2ab7a6ba271708d919e4d2eb391bf0f2cad44d7
        tx_hash = '0x8d3e463cdab56374495e5e26b2ab7a6ba271708d919e4d2eb391bf0f2cad44d7'
        response = requests.get(f'{self.base_url}/fee/{tx_hash}')
        result = response.json().get('fee')

        self.assertAlmostEqual(result, 3.13, 2)


if __name__ == '__main__':
    unittest.main()
