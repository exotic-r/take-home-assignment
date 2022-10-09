import json
import logging

from http import HTTPStatus
from flask import Flask, request
from flask_caching import Cache
from requests import HTTPError

from cryptoService import CryptoService
from decimalEncoder import DecimalEncoder
from exceptions import *
from RedisClient import RedisClient

config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
}
app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

@app.route('/')
def index():
    return 'Welcome to our flask app'


@app.route("/transaction-fee/<tx_hash>", methods=['GET'])
@cache.cached()
def transaction_fee_by_tx_hash(tx_hash):
    try:
        fee = service.get_transaction_fee_by_tx_hash(tx_hash)

        return app.response_class(
            response=json.dumps({'transaction fee': fee}, cls=DecimalEncoder),
            status=HTTPStatus.OK,
            mimetype='application/json'
        )
    except HTTPError as e:
        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=e.response.status_code,
            mimetype='application/json'
        )
    except TransactionNotFoundException as e:
        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=HTTPStatus.BAD_REQUEST,
            mimetype='application/json'
        )

@app.route("/transaction-fee", methods=['GET'])
@cache.cached()
def transaction_fee_by_time_range():
    args = request.args
    start_time = args.get('start_time')
    end_time = args.get('end_time')

    if not start_time or not end_time:
        return app.response_class(
            response=json.dumps({'message': "Either query param start_time or end_time is not provided."}),
            status=HTTPStatus.BAD_REQUEST,
            mimetype='application/json'
        )

    try:
        fees = service.get_transactions_fee_by_time_range(int(start_time), int(end_time))

        return app.response_class(
            response=json.dumps({'transaction fees': fees}, cls=DecimalEncoder),
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


@app.before_request
def init_http_client():
    global service
    redis = RedisClient()
    service = CryptoService(redis)


# if __name__ == "__main__":
#     app.run(port=8080)
