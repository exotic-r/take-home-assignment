# Take-home-assignment

A simple RESTful service that interacts with the Ethereum network to get real time/historical 
transaction fee in USBT for all the Uniswap WETH-USDC transactions.

## Getting Started

### Build with
The app is written in Python 3.9

### Prerequisities
To run this app in a container, you would need docker installed in your machine.

[How to install Docker](https://docs.docker.com/get-docker/) 

### Usage

#### How to run the app

## Consideration

### Availability
The service should be deployed to multiple hosts across multiple data centres to ensure high availability.

### Scalability
Flask was used to simply demonstrate the feature of retrieving transaction fees.
To scale this service, we would need another library suitable for it.

### Reliability