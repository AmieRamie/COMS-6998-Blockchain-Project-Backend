from web3 import Web3
from web3.exceptions import ContractLogicError, Web3RPCError
import json
import os
from datetime import datetime
from decimal import Decimal

class ReceiptsContractInterface:
    def __init__(self,ganache_url):
        self.web3 = Web3(Web3.HTTPProvider(ganache_url))
        assert self.web3.is_connected()
        with open("build/contracts/ReceiptManager.json") as f:
            self.contract_json = json.load(f)
            self.contract_abi = self.contract_json["abi"]
            self.contract_bytecode = self.contract_json["bytecode"]
    def issue_receipt(self,contract_address, seller_address, buyer_address, amount_eth):
        """Issues a receipt for the given buyer address and amount (in Ether) using a specific contract."""
        # Convert amount to Wei, since Ether is the base unit in web3.py
        amount_wei = self.web3.to_wei(amount_eth, 'ether')
        
        # Create a contract instance for the specific seller's contract address
        seller_contract = self.web3.eth.contract(address=contract_address, abi=self.contract_abi)
        
        # Send the transaction to the contract's issueReceipt function
        tx_hash = seller_contract.functions.issueReceipt(buyer_address).transact({
            'from': seller_address,  # Pass in the seller's address from the API
            'value': amount_wei  # The amount to hold in escrow
        })
        
        # Wait for the transaction receipt to confirm
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        # Retrieve the actual timestamp from the block containing this transaction
        block = self.web3.eth.get_block(tx_receipt['blockNumber'])
        purchase_time = datetime.utcfromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        # Retrieve the ReceiptIssued event data from the transaction receipt
        receipt_event = seller_contract.events.ReceiptIssued().process_log(tx_receipt.logs[0])
        
        # Extract the receiptIndex from the event
        receipt_index = receipt_event['args']['receiptIndex']
        
        # Format the receipt object to return to the frontend
        receipt_details = {
            "buyer_address": buyer_address,
            "seller_address":seller_address,
            "seller_contract_address": contract_address,
            "amount": amount_eth,  # Return amount in Ether for readability
            "purchase_time":  purchase_time,
            "transaction_hash": tx_receipt['transactionHash'].hex(),
            "block_number": tx_receipt['blockNumber'],
            "status": "Success" if tx_receipt['status'] == 1 else "Failed",
            "receipt_index": receipt_index
        }
        return receipt_details
    def request_return(self,contract_address, buyer_address, receiptIndex):
        """Request a return for a specific receipt and capture revert reasons if it fails."""
        # Create a contract instance for the specific seller's contract address
        contract = self.web3.eth.contract(address=contract_address, abi=self.contract_abi)
        try:
            tx_hash = contract.functions.requestReturn(receiptIndex).transact({
                'from': buyer_address
            })
            
            # Wait for the transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Return transaction details if successful
            return {
                "transaction_hash": tx_receipt['transactionHash'].hex(),
                "status": "Success" if tx_receipt['status'] == 1 else "Failed",
                "transaction_receipt": tx_receipt
            }
            
        except ContractLogicError as e:
        # Decode any unexpected errors during the actual transact call
            # print("ERRRRRRRROR:",e)
            error_message = e.args[1].get('reason', '')
            print('Error Message:', error_message)
            # error_message = decode_revert_message(error_data)
            return {
                "status": "Failed",
                "reason": str(error_message)
            }
    def release_funds(self,contract_address, buyer_address, receipt_index, seller_address):
        """Releases funds to the seller after the return window has expired."""
        contract = self.web3.eth.contract(address=contract_address, abi=self.contract_abi)
        try:
            tx_hash = contract.functions.releaseFunds(buyer_address, receipt_index).transact({
                'from': seller_address
            })
        
            # Wait for the transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "transaction_hash": tx_receipt['transactionHash'].hex(),
                "status": "Success" if tx_receipt['status'] == 1 else "Failed",
                "transaction_receipt": tx_receipt
            }
        except ContractLogicError as e:
            # Decode any unexpected errors during the actual transact call
            error_message = e.args[1].get('reason', '')
            print('Error Message:', error_message)
            # error_message = decode_revert_message(error_data)
            return {
                "status": "Failed",
                "reason": str(error_message)
            }
    def deploy_new_contract(self,seller_account,return_window_days):
        """Deploy a new instance of the ReceiptManager contract and return the address."""
        ReceiptManager = self.web3.eth.contract(abi=self.contract_abi, bytecode=self.contract_bytecode)
        tx_hash = ReceiptManager.constructor(return_window_days).transact({'from': seller_account})
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt.contractAddress

    def get_all_accounts_on_ganache(self):
        accounts = self.web3.eth.accounts
        return accounts
        
    def get_balance_of_account(self, account):
        balance_wei = self.web3.eth.get_balance(account)
        balance_eth = self.web3.from_wei(balance_wei, 'ether')
        return balance_eth
    
    def get_balance_of_contract(self, contract_address):
        balance_wei = self.web3.eth.get_balance(contract_address)
        balance_eth = self.web3.from_wei(balance_wei, 'ether')
        return balance_eth



