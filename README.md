# W6998 Receipt Management System Backend

This repo includes the backend of the W6998 Receipt Management System. The system is a decentralized application that allows users to store and manage their receipts. We use the [Python web3 library](https://github.com/ethereum/web3.py) to interact with the smart contract, and we use [FastAPI](https://fastapi.tiangolo.com/) to build the API endpoints.


Our frontend repo can be found [here](https://github.com/kevinshi-git/COMS-6998-Blockchain-Project/tree/main/blockchain).

## Backend Design

**Libraries and Frameworks**
- Truffle + Ganache to develop and test the smart contract
- Python (boto3) + FastAPI to interact with Ganache and build the API endpoints
- DynamoDB to store buyer, seller, account, and receipt information in parallel to the smart contract to have faster access

**Smart Contract Functions** <br> 
Found under ```./contracts/ReceiptManager.sol```
- ```issue_receipt```: Called by a seller for a specific buyer, SC issues the receipt and holds funds in escrow
- ```request_return```: Buyer can request a return for a specific transaction within the return window. If return is valid, funds are sent back to buyer's account
- ```release_funds```: Releases funds to the seller if the return window has expired.
- ```getReceipt```: Retrieves details for specified receipt
 
**Abstraction**
Found under ```./services```
- ```smart_contract_interactions.py```: Python interface to smart contract functions
- ```dynamoDB_service.py```: Python interface to DynamoDB to be able to store user account, seller smart contract, and receipt info in a DynamoDB
- ```dataservice.py```: Python interface to connect the smart contracts interface with the dynamoDB interface so both stay in sync with each other. Also provides additional business logic for the endpoints
- ```main.py```: Fast API endpoints of above functions used by frontend
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
