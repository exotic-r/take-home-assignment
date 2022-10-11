# Take-home-assignment

A RESTful service that interacts with the Ethereum network to get real time/historical 
transaction fee in USBT for all the Uniswap WETH-USDC transactions.

It is written in Python 3.9. Uses the Flask web framework to expose endpoints.
Provides `Dockerfile` and `docker-compose` files to run the app in container.
Redis is used to store transactions:fee mapping for future query. 

All together it uses Web3 library and Alchemy as its remote node provider, Crypto Compare API, and Ether Scan API to get the transaction fee.


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

## REST API

### GET transaction fee by transaction hash
`GET /transaction-fee/<tx_hash>`

REQUEST: 
```
curl -i -H 'Accept: application/json' http://localhost:8000/<tx_hash>
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
`GET /transaction-fee?start_time=<start_time>&end_time=<end_time>`

REQUEST: 
```
curl -i -H 'Accept: application/json' http://localhost:8000/?start_time=1644760315&end_time=1663652062>
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
## Consideration

### Availability
The service should be deployed to multiple hosts across multiple data centres to ensure high availability.

### Scalability
Flask was used to simply demonstrate the feature of retrieving transaction fees.
To scale this service, we would need another library suitable for it.

### Reliability


## TODO
Due to the time constraints, a lot of shortcuts were make.\
Below are the list of things to explore for future development.

- find the right api to get transaction
- write more tests
- complete readme
- retry logic 
- health check endpoint
- dashboard to monitor background task status