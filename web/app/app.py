import json
from http import HTTPStatus

from flask import Flask
from flask_caching import Cache
from requests import HTTPError

from cryptoService import CryptoService
from decimalEncoder import DecimalEncoder
from exceptions import TransactionNotFoundException

config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
}
app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)


@app.route('/')
def index():
    return 'Welcome to our flask app'


@app.route("/transaction-fee/<tx_hash>", methods=['GET'])
@cache.cached()
def transaction_fee(tx_hash):
    try:
        fee = service.get_transaction_fee(tx_hash)
    except HTTPError as e:
        return app.response_class(
            response=json.dumps({'error': str(e)}),
            status=e.response.status_code,
            mimetype='application/json'
        )
    except TransactionNotFoundException as e:
        return app.response_class(
            response=json.dumps({'error': str(e)}),
            status=HTTPStatus.BAD_REQUEST,
            mimetype='application/json'
        )

    return app.response_class(
        response=json.dumps({'transaction fee': fee}, cls=DecimalEncoder),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )


@app.before_request
def init_http_client():
    global service
    service = CryptoService()


# if __name__ == "__main__":
#     app.run()
