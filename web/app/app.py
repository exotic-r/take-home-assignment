import json
import logging

from http import HTTPStatus
from flask import Flask, request
from requests import HTTPError
from redis import Redis
from web3.exceptions import TransactionNotFound

from cryptoService import CryptoService
from decimalEncoder import DecimalEncoder
from exceptions import *
from celery_app import get_historic_transaction

app = Flask(__name__)
redis = Redis(host='redis')
service = CryptoService(redis)

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


@app.route("/v1/transaction-fee/<tx_hash>", methods=['GET'])
def transaction_fee_by_tx_hash(tx_hash):
    try:
        fee = service.get_transaction_fee_by_tx_hash(tx_hash)

        return app.response_class(
            response=json.dumps({'fee': fee}, cls=DecimalEncoder),
            status=HTTPStatus.OK,
            mimetype='application/json'
        )
    except HTTPError as e:
        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=e.response.status_code,
            mimetype='application/json'
        )
    except (TransactionNotFound, TransactionNotUniswap) as e:
        return app.response_class(
            response=json.dumps({'exception': str(e)}),
            status=HTTPStatus.BAD_REQUEST,
            mimetype='application/json'
        )


@app.route("/v1/transaction-fee", methods=['GET'])
def transaction_fee_by_time_range():
    args = request.args
    start_time = args.get('start_time')
    end_time = args.get('end_time')

    if not start_time or not end_time:
        return app.response_class(
            response=json.dumps(
                {'message': "Either query param start_time or end_time is not provided."}),
            status=HTTPStatus.BAD_REQUEST,
            mimetype='application/json'
        )

    try:
        result = service.get_transactions_fee_by_time_range(
            int(start_time), int(end_time))

        return app.response_class(
            response=json.dumps({'fees': result[0]},
                                cls=DecimalEncoder),
            status=HTTPStatus.OK,
            mimetype='application/json'
        )
    except HTTPError as e:
        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=e.response.status_code,
            mimetype='application/json'
        )
    except TransactionNotFoundExceptionByTimeRange as e:
        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=HTTPStatus.BAD_REQUEST,
            mimetype='application/json'
        )


@app.route('/v1/', methods=['POST'])
def task_get_historic_transaction():
    task = get_historic_transaction.delay()
    return app.response_class(
        response=json.dumps({'task_id': task.id}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )


@app.route('/v1/status/<task_id>')
def task_status(task_id):
    task = get_historic_transaction.AsyncResult(task_id)
    return app.response_class(
        response=json.dumps({'queue_state': task.state}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )


if __name__ == "__main__":
    app.run(port=8080)
