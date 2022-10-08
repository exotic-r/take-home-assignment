import json

from flask import Flask
from flask_caching import Cache

from cryptoService import CryptoService

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
    return 'Welcome to our app'


@app.route("/transaction-fee/<tx_hash>", methods=['GET'])
@cache.cached()
def transaction_fee(tx_hash):
    fee = service.get_transaction_fee(tx_hash)

    return app.response_class(
        response=json.dumps({'transaction fee': fee}),
        status=200,
        mimetype='application/json'
    )


@app.before_request
def init_http_client():
    global service
    service = CryptoService()


if __name__ == "__main__":
    app.run(port=8080)
