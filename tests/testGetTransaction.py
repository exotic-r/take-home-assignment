import unittest

import celery.states
import requests
from unittest import TestCase


class TestGetTransaction(TestCase):
    base_url = 'http://0.0.0.0:8000/v1'

    def test_successfully_get_transaction_fee_by_tx_hash(self):
        # https://etherscan.io/tx/0x8d3e463cdab56374495e5e26b2ab7a6ba271708d919e4d2eb391bf0f2cad44d7
        tx_hash = '0x8d3e463cdab56374495e5e26b2ab7a6ba271708d919e4d2eb391bf0f2cad44d7'
        response = requests.get(f'{self.base_url}/fee/{tx_hash}')
        result = response.json().get('fee')

        self.assertAlmostEqual(result, 3.13, 2)

    def test_invalid_tx_hash(self):
        invalid_tx_hash = '0x8d3e463cdab56374495e5e26b2ab7a6ba271708d919e4d2eb391bf0f2cad44dd'
        response = requests.get(f'{self.base_url}/fee/{invalid_tx_hash}')
        result = response.json().get('message')
        expected = f"Transaction with hash: '{invalid_tx_hash}' not found."

        self.assertEqual(result, expected)

    def test_get_fee_by_time_range(self):
        start, end = 1620299304, 1620299904
        response = requests.get(
            f'{self.base_url}/fee?start_time={start}&end_time={end}')
        result = response.json().get('fees')
        expected = [31.267892702199998,
                    36.911568375,
                    33.7032459876,
                    44.532188315999996,
                    37.2460448772]

        self.assertEqual(result, expected)

    def test_get_fee_by_time_range_and_action(self):
        start, end = 1620299304, 1620299904
        action = 'tokentx'
        response = requests.get(
            f'{self.base_url}/fee?start_time={start}&end_time={end}&action_type={action}')
        result = response.json().get('fees')
        expected = [31.267892702199998,
                    36.911568375,
                    33.7032459876,
                    44.532188315999996,
                    37.2460448772]

        self.assertEqual(result, expected)

    def test_get_empty_result_by_time_range(self):
        start, end = 1620299302, 1620299302
        response = requests.get(
            f'{self.base_url}/fee?start_time={start}&end_time={end}')
        result = response.json().get('fees')

        self.assertEqual(result, [])

    def test_invalid_timestamp(self):
        start, end = 1, 1
        response = requests.get(
            f'{self.base_url}/fee?start_time={start}&end_time={end}')
        result = response.json().get('message')

        expected = "Invalid timestamp start time: 1, end time: 1"
        self.assertEqual(result, expected)

    def test_trigger_get_historic_transaction_and_get_status(self):
        response = requests.post(f'{self.base_url}/')
        result = response.json().get('task_id')

        self.assertTrue(result)

        response = requests.get(f'{self.base_url}/status/{result}')
        result = response.json().get('state')

        self.assertIn(result, celery.states.ALL_STATES)

    def test_invalid_task_id_status(self):
        task_id = 12345678
        response = requests.get(f'{self.base_url}/status/{task_id}')
        result = response.json().get('state')

        # default behaviour by celery
        self.assertEqual(result, celery.states.PENDING)

if __name__ == '__main__':
    unittest.main()
