import unittest
from unittest import TestCase
from unittest.mock import MagicMock, patch

from web.cryptoService import CryptoService


class TestCryptoService(TestCase):

    @patch('redis.Redis')
    def test_get_transaction_fee_by_tx_hash(self, mock_redis):
        tx_hash = '0x1234'
        expected = 100.0

        service = CryptoService(mock_redis)
        result = service.get_transaction_fee_by_tx_hash(tx_hash)

        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
