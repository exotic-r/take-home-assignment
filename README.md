# Take-home-assignment

A RESTful service that interacts with the Ethereum network to get real time/historical 
transaction fee in USBC for all the Uniswap WETH-USDC transactions.


## Overview Design

It is written in Python 3.9. Uses the Flask web framework to expose endpoints.
Provides `Dockerfile` and `docker-compose` files to run the app in container.
Redis is used to store transactions:fee mapping for future query. 
Celery worker is used to run background task to get all the historic transaction fees.

Furthermore, it uses Web3 library and Alchemy as its remote node provider, Crypto Compare API, and Ether Scan API 
to get the final transaction fee.

Since Binance API was banned in Singapore, I had to look for an alternative API that exposes ETH/USDC exchange fee.
[Crypto Compare API](https://min-api.cryptocompare.com/documentation?key=Historical&cat=dataHistohour)
 was used for this purpose. 
One thing to note is that the Crypto Compare does not expose exchange rate older than 7 days on a lower timeframe.
Because of this, hourly price will be used.

## Getting Started

### GET API KEY
Free versions of the API KEY can be found in `web/config.py`.\
For better availability replace it with your own with less limitation.

### Install
Docker: [How to install Docker](https://docs.docker.com/get-docker/)

### Run the app

```commandline
git clone https://github.com/exotic-r/take-home-assignment.git
cd take-home-assignment
docker-compose up -d --build
```

### Run functional tests

```commandline
# after running the app

cd take-home-assignment
python3 -m unittest
```

## REST API

### GET transaction fee by transaction hash
`GET /v1/fee/<tx_hash>`

REQUEST: 
```commandline
curl -i -H 'Accept: application/json' http://localhost:8000/v1/fee/0x125e0b641d4a4b08806bf52c0c6757648c9963bcda8681e4f996f09e00d4c2cc
```
RESPONSE: 
```
HTTP/1.1 200 OK
Server: gunicorn
Date: Sat, 15 Oct 2022 16:26:42 GMT
Connection: close
Content-Type: application/json
Content-Length: 22

{"fee": 430.926001440}
```

### GET transaction fee by time range
`GET /v1/fee?start_time=<start_time>&end_time=<end_time>?action_type=<action_type>`

actionType is optional, default value is 'tokentx' (ERC20) since most of the transaction are ERC20
- txlist: normal transaction
- txlistinternal: internal transaction
- tokennfttx: ERC721 transaction

REQUEST: 
```commandline
curl -i -H 'Accept: application/json' http://localhost:8000/v1/fee?start_time=1620299304&end_time=1620299904
```

RESPONSE: 
```
HTTP/1.1 200 OK
Server: gunicorn
Date: Sat, 15 Oct 2022 16:45:26 GMT
Connection: close
Content-Type: application/json
Content-Length: 179

{"fees": [11.6024442765, 13.6966190625, 12.5061204870, 16.524370170, 13.8207318390, 19.26177065362529175, 12.6791433570, 8.8548343695, 11.141295480, 11.7389738970, 12.3384697920]}
```

### POST trigger background task to get historical transaction fee
`POST /v1/`

actionType is optional, default value is 'tokentx' (ERC20) since most of the transactions are ERC20
- txlist: normal transaction
- txlistinternal: internal transaction
- tokennfttx: ERC721 transaction

REQUEST: 
```commandline
curl -i -X POST http://localhost:8000/v1/

curl --data 'action_type=tokentx' -X POST http://localhost:8000/v1/
```
RESPONSE:
```
HTTP/1.1 200 OK
Server: gunicorn
Date: Sat, 15 Oct 2022 16:48:04 GMT
Connection: close
Content-Type: application/json
Content-Length: 51

{"task_id": "9daf389e-bbab-4c5f-9ffa-396574aa069e"}
```


### GET status of task
`POST /v1/status/<task_id>`

REQUEST: 
```commandline
curl -i -H 'Accept: application/json' http://localhost:8000/v1/status/9daf389e-bbab-4c5f-9ffa-396574aa069e
```
RESPONSE:
```
HTTP/1.1 200 OK
Server: gunicorn
Date: Sun, 16 Oct 2022 13:12:55 GMT
Connection: close
Content-Type: application/json
Content-Length: 26

{"queue_state": "PENDING"}
```

## TODO
Due to the time constraints, a lot of shortcuts were make.'
Below are the list of things to explore for future development.

- write unit tests
- retry logic 
- health check endpoint
- dashboard to monitor background task status