from web3 import Web3
from web3.exceptions import ContractLogicError, Web3RPCError
import json
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import os 
from services.dynamoDB_service import ReceiptDyanmoDB,SellersDyanmoDB, AccountsDynamoDB
from services.smart_contract_interactions import ReceiptsContractInterface
import subprocess
import time

def find_and_kill_process(port):
    """Find and kill the process running on a specific port."""
    try:
        # Find the process using the specified port
        result = subprocess.check_output(f"lsof -i :{port} | grep LISTEN", shell=True).decode("utf-8")
        # Extract the PID (Process ID)
        pid = int(result.split()[1])
        # Kill the process
        os.kill(pid, 9)
        print(f"Stopped process with PID {pid} running on port {port}.")
    except subprocess.CalledProcessError:
        print(f"No process found running on port {port}.")

class DataService:
    def __init__(self):
        self.seller_Dynamo_DB = SellersDyanmoDB()
        self.receipt_Dynamo_DB = ReceiptDyanmoDB()
        self.accounts_Dynamo_DB = AccountsDynamoDB()
        self.receipt_smart_contract_interface = ReceiptsContractInterface("http://127.0.0.1:8545")
        self.all_sellers = self.get_sellers_with_contracts()
    def get_all_network_accounts(self):
        all_accounts = self.receipt_smart_contract_interface.get_all_accounts_on_ganache()
        all_accounts_enriched = [{'account_index':i,'account_address':account,'balance':self.get_account_balance(account)} for i,account in enumerate(all_accounts)]
        return all_accounts_enriched
    def get_sellers_with_contracts(self):
        all_sellers = self.seller_Dynamo_DB.get_all_sellers()
        return {dictionary['seller_address']:dictionary for dictionary in all_sellers}
    def get_account_balance(self,account_address):
        balance_eth = self.receipt_smart_contract_interface.get_balance_of_account(account_address)
        return balance_eth
    def create_seller_account_contract(self,account_address,return_window_days):
        seller_exists = self.seller_Dynamo_DB.seller_exists(account_address)
        if seller_exists==False:
            contract_address = self.receipt_smart_contract_interface.deploy_new_contract(account_address,return_window_days)
            self.seller_Dynamo_DB.insert_seller({'seller_address':account_address,'seller_contract_address':contract_address,'return_window_days':return_window_days})
            self.all_sellers[account_address] = {'seller_address':account_address,'seller_contract_address':contract_address,'return_window_days':return_window_days}
            return contract_address, True
        else:
            return None, False
    def issue_receipt(self, seller_address, buyer_address, amount_eth, item_name):
        # all_sellers = self.get_sellers_with_contracts()
        if seller_address in self.all_sellers.keys():
            contract_address = self.all_sellers[seller_address]['seller_contract_address']
            receipt_details = self.receipt_smart_contract_interface.issue_receipt(contract_address,seller_address, buyer_address, amount_eth)
            receipt_details['item_name'] = item_name
            receipt_details['status'] = 'Active'
            self.receipt_Dynamo_DB.insert_receipt(receipt_details)
            return receipt_details, True, None
        else:
            return None, False, "Seller address does not have an associated contract"
    def get_receipts_for_seller(self,seller_address):
        all_seller_receipts = self.receipt_Dynamo_DB.search_by_seller_address(seller_address)
        if isinstance(all_seller_receipts,list):
            return all_seller_receipts, True
        else:
            return [], False
    def get_receipts_for_buyer(self,buyer_address):
        all_buyer_receipts = self.receipt_Dynamo_DB.search_by_buyer_address(buyer_address)
        if isinstance(all_buyer_receipts,list):
            return all_buyer_receipts, True
        else:
            return [], False
    def request_return(self, transaction_hash):
        # all_sellers = self.get_sellers_with_contracts()
        receipt_details = self.receipt_Dynamo_DB.get_receipt_details(transaction_hash)
        print(receipt_details)
        if receipt_details['seller_address'] in self.all_sellers.keys():
            return_request_details = self.receipt_smart_contract_interface.request_return(receipt_details['contract_address'], receipt_details['buyer_address'], receipt_details['receipt_index'])
            print("return_request_details:",return_request_details)
            if return_request_details['status'] == 'Success':
                self.receipt_Dynamo_DB.change_receipt_status(transaction_hash,'Returned','return_time')
                return return_request_details, True, None
            else:
                return None, False, return_request_details['reason']
        else:
            return None, False, "Seller address does not have an associated contract"
    def funds_release(self, transaction_hash):
        # all_sellers = self.get_sellers_with_contracts()
        receipt_details = self.receipt_Dynamo_DB.get_receipt_details(transaction_hash)
        print(receipt_details)
        if receipt_details['seller_address'] in self.all_sellers.keys():
            release_return_details = self.receipt_smart_contract_interface.release_funds(receipt_details['contract_address'], receipt_details['buyer_address'], receipt_details['receipt_index'],receipt_details['seller_address'])
            if release_return_details['status'] == 'Success':
                self.receipt_Dynamo_DB.change_receipt_status(transaction_hash,'Funds Released to Seller','funds_release_time')
                return release_return_details, True, None
            else:
                return None, False, release_return_details['reason']
        else:
            return None, False, "Seller address does not have an associated contract"

    def create_new_user(self, username, pwd,return_window):
        all_network_accounts = self.get_all_network_accounts()
        all_network_addresses = [account['account_address'] for account in all_network_accounts]
        found_address = False
        for network_address in all_network_addresses:
            response = self.accounts_Dynamo_DB.address_used(network_address)
            if len(response)==0:
                found_address = True
                break
        if found_address==False:
            return {"success":False,"message":"All 10 account addresses in Ganache network have been taken"}
        success, message = self.accounts_Dynamo_DB.insert_account({'user_id':username,'account_address':network_address,'password':pwd})
        if not success:
            res={"success":success,"message":message}
            return res
        contract,success=self.create_seller_account_contract(network_address,return_window)
        return {"success":success,"message":message+" Contract: "+contract}
    def verify_login(self,username,pwd):
        accounts = self.accounts_Dynamo_DB.account_exists(username)
        if len(accounts)==0:
            return {"success":False,"message":"Account doesn't exist"}
        account = accounts[0]
        if account['password'] == pwd:
            return {"success":True,"message":"Password is right"}
        else:
            return {"success":False,"message":"Password is wrong"}

    def get_all_accounts(self):
        all_accounts = self.accounts_Dynamo_DB.get_all_accounts()
        return all_accounts
    
    def clear_tables(self):
        self.seller_Dynamo_DB.clear_table()
        self.receipt_Dynamo_DB.clear_table()
        self.accounts_Dynamo_DB.clear_table()
    def restart_ganache(self,port=8545):
        try:
            find_and_kill_process(port)
            # Wait for a moment to ensure the port is freed
            time.sleep(2)

            # Start a new Ganache instance on the specified port
            subprocess.Popen(
                ["ganache-cli", "--port", str(port), "--deterministic", "--accounts", "10", "--defaultBalanceEther", "10000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return {"success":True, "message":"Ganache restarted with fresh accounts"}
        except Exception as e:
            return {"success":False, "message":str(e)}