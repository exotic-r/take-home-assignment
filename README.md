# Take-home-assignment

A RESTful service that interacts with the Ethereum network to get real time/historical 
transaction fee in USBC for all the Uniswap WETH-USDC transactions.


## Overview Design

It is written in Python 3.9. Uses the Flask web framework to expose endpoints.
Provides `Dockerfile` and `docker-compose` files to run the app in container.
Redis is used to store transactions:fee mapping for future query. 

All together it uses Web3 library and Alchemy as its remote node provider, Crypto Compare API, and Ether Scan API 
to get the transaction fee.

Since Binance was banned in Singapore, I had to look for an alternative API that exposes ETH/USDC exchange fee.
[Crypto Compare API](https://min-api.cryptocompare.com/documentation?key=Historical&cat=dataHistominute)
 was used for this purpose


## Getting Started

### GET API KEY
Free versions of the API KEY can be found in `web/app/config.py`.\
For better accessibility and performance replace it with your own with less limitation.

### Install
Docker: [How to install Docker](https://docs.docker.com/get-docker/)

### Run the app

```commandline
git clone https://github.com/exotic-r/take-home-assignment.git
cd take-home-assignment
docker-compose build
docker-compose up
```

### Run tests

```commandline

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
Date: Thu, 24 Feb 2011 12:36:30 GMT
Status: 200 OK
Content-Type: application/json
Content-Length: 2
[]
```

### GET transaction fee by time range
`GET /v1/fee?start_time=<start_time>&end_time=<end_time>`

REQUEST: 
```commandline
curl -i -H 'Accept: application/json' http://localhost:8000/v1/fee?start_time=1644760315&end_time=1663652062
```
RESPONSE: 
```
HTTP/1.1 200 OK
Date: Thu, 24 Feb 2011 12:36:30 GMT
Status: 200 OK
Content-Type: application/json
Content-Length: 2
[]
```

### POST trigger background task to get historical transaction fee
`POST /v1/`

REQUEST: 
```commandline
curl -i -H 'Accept: application/json' http://localhost:8000/v1/
```
RESPONSE:
```
HTTP/1.1 200 OK
Date: Thu, 24 Feb 2011 12:36:30 GMT
Status: 200 OK
Content-Type: application/json
Content-Length: 2
[]
```

## TODO
Due to the time constraints, a lot of shortcuts were make.\
Below are the list of things to explore for future development.

- write more tests
- complete readme
- retry logic 
- health check endpoint
- dashboard to monitor background task status