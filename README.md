# W6998 Receipt Management System Backend

This repo includes the backend of the W6998 Receipt Management System. The system is a decentralized application that allows users to store and manage their receipts. We use the [Python web3 library](https://github.com/ethereum/web3.py) to interact with the smart contract, and we use [FastAPI](https://fastapi.tiangolo.com/) to build the API endpoints.


Our frontend repo can be found [here](https://github.com/kevinshi-git/COMS-6998-Blockchain-Project/tree/main/blockchain).

## Setup


We use Truffle to compile and deploy the smart contracts to local network.

Install Truffle and [Ganache](https://archive.trufflesuite.com/ganache/):

```shell
npm install -g truffle ganache
```

Compile the smart contracts:

```shell
truffle compile
```

After compiling successfully, you should see that `build/contracts` directory is created with the compiled smart contract `ReceiptManager.json`.


Start the local blockchain network using Ganache:

```shell
ganache
```

By default, Ganache will run on `127.0.0.1:8545` because this is how we defined in `truffle-config.js`.


## Usage

Run `ganache` to start the local blockchain network.

We are using AWS DynamoDB to store the seller information. The following environment variables need to be set before running the server:

```shell
export blockchain_class_access_key=<your aws access key>
export blockchain_class_secret_key=<your aws secret access key>
```

Start the server:

```shell
python main.py
```

Check out the OpenAPI documentation [here](https://w6998-backend-745799261495.us-east4.run.app/docs).


## Testing

### API Endpoints

We tests our API endpoints in the jupyter notebook - `Testing Contract.ipynb`.


### Unit tests for smart contracts

Run all unit tests under the `test` directory:

```shell
truffle test
```
