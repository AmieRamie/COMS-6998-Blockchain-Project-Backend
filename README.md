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


Start the local blockchain network using Ganache:

```shell
ganache
```

By default, Ganache will run on `127.0.0.1:8545` because this is how we defined in `truffle-config.js`.


## Usage

Run `pip install -r requirements.txt` to install the required packages.

Start the server:

```shell
python main.py
```


## Testing

### API Endpoints

We tests our API endpoints in the jupyter notebook - `Testing Contract.ipynb`.


### Unit tests for smart contracts

Run all unit tests under the `test` directory:

```shell
truffle test
```
