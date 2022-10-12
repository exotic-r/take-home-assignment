import os
from http import HTTPStatus

import requests

import config
from celery import Celery
from utils import get_ether_scan_params

celery = Celery(
    'worker',
    broker=os.environ.get("CELERY_BROKER_URL"),
    backend=os.environ.get("CELERY_RESULT_BACKEND"),
)


@celery.task(name='get_historic_transaction')
def get_historic_transaction(service):
    # start_block = 0
    # end_block = 999999999
    # page = 1
    # offset = 10
    # fees = []
    #
    # def request_fees(page_: int, offset_: int):
    #     params = get_ether_scan_params(start_block, end_block, page_, offset_)
    #     response = requests.get(config.ETHER_SCAN_BASE_URL, params=params)
    #     if response.status_code != HTTPStatus.OK:
    #         raise response.raise_for_status()
    #
    #     response_json = response.json()
    #
    #     _fees = []
    #     status_code_ = None
    #
    #     for result in response_json['result']:
    #         tx_hash = result['hash']
    #         time_stamp = result['timeStamp']
    #         fee, status_code_ = service.calculate_tx_fee(result['gasPrice'], result['gasUsed'],
    #                                                   result['timeStamp'])
    #         if status_code_ == HTTPStatus.TOO_MANY_REQUESTS:
    #             break
    #         _fees.append(fee)
    #     return _fees, status_code_
    #
    # while len(fees) % offset == 0:
    #     fees, status_code = request_fees(page, offset)
    #     fees.extend(fees)
    #
    #     if status_code == HTTPStatus.TOO_MANY_REQUESTS:
    #         break
    #     page += 1
    #
    # return fees
    return -1
