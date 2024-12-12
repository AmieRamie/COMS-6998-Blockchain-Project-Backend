# Receipt Management System

A decentralized application for secure receipt management and automated escrow services using blockchain technology. The system enables sellers to issue digital receipts and manages funds in escrow, with automated release mechanisms and return functionality.

## Overview

This project consists of two main components:
- **Frontend**: React-based user interface ([Frontend Repository](https://github.com/kevinshi-git/COMS-6998-Blockchain-Project/tree/main/blockchain))
- **Backend**: Smart contract and API server ([Backend Repository]([https://github.com/kevinshi-git/COMS-6998-Blockchain-Project-Backend](https://github.com/AmieRamie/COMS-6998-Blockchain-Project-Backend/)))

## Architecture

### Technology Stack

#### Frontend
- React.js for UI components
- Web3.js for blockchain interactions
- Material-UI for styling
- MetaMask integration for wallet connectivity

#### Backend
- FastAPI framework for RESTful API
- Python Web3.py for smart contract interactions
- AWS DynamoDB for off-chain data storage
- Solidity for smart contract development
- Truffle & Ganache for blockchain development environment

## Smart Contract Features

The smart contract (`./contracts/ReceiptManager.sol`) implements:

- **Receipt Issuance**: Sellers can issue receipts with automated escrow
- **Return Management**: Built-in return window with automated fund handling
- **Escrow Services**: Automatic fund management and release
- **Receipt Verification**: On-chain receipt validation and retrieval

## Backend Services

### Core Components

```
services/
├── smart_contract_interactions.py  # Blockchain interface
├── dynamoDB_service.py            # Database operations
├── dataservice.py                 # Business logic layer
└── main.py                        # API endpoints
```

### API Endpoints

- `POST /issue_receipt`: Create new receipt with escrow
- `POST /request_return`: Process return requests
- `GET /receipt/{receipt_id}`: Fetch receipt details
- `POST /release_funds`: Release escrowed funds
- Full API documentation: [OpenAPI Docs](https://w6998-backend-745799261495.us-east4.run.app/docs)

## Getting Started

### Prerequisites

- Node.js (v14+)
- Python 3.8+
- AWS Account
- MetaMask wallet
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/kevinshi-git/COMS-6998-Blockchain-Project-Backend
   cd COMS-6998-Blockchain-Project-Backend
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install blockchain tools**
   ```bash
   npm install -g truffle ganache
   ```

4. **Configure AWS credentials**
   ```bash
   export blockchain_class_access_key=<your_access_key>
   export blockchain_class_secret_key=<your_secret_key>
   ```

5. **Start local blockchain**
   ```bash
   ganache
   ```

6. **Deploy smart contracts**
   ```bash
   truffle compile
   truffle migrate
   ```

7. **Launch backend server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../COMS-6998-Blockchain-Project/blockchain
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

## Testing

### Smart Contract Testing
```bash
truffle test
```

### API Testing
1. Open `Testing Contract.ipynb`
2. Execute cells sequentially to test API endpoints
3. Check test coverage with:
   ```bash
   pytest --cov=services tests/
   ```
