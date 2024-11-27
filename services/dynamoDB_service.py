import json
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import os
from decimal import Decimal

class SellersDyanmoDB:
    def __init__(self, table_name='Sellers'):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-2',
            aws_access_key_id=os.getenv('blockchain_class_access_key'),
            aws_secret_access_key=os.getenv('blockchain_class_secret_key')
        )
        self.table = self.dynamodb.Table(table_name)

    def insert_seller(self, seller_data):
        """
        Inserts a new seller record into the Sellers table.
        Expects seller_data to be a dictionary with 'seller_address' and 'seller_contract'.
        """
        try:
            response = self.table.put_item(
                Item=seller_data,
                ConditionExpression="attribute_not_exists(seller_address)"
            )
            print("Seller inserted successfully:", response)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print("Seller already exists.")
            else:
                print("Error inserting seller:", e.response['Error']['Message'])

    def seller_exists(self, seller_address):
        """
        Checks if a seller exists in the table.
        Returns True if the seller exists, False otherwise.
        """
        try:
            response = self.table.get_item(Key={'seller_address': seller_address})
            return 'Item' in response  # Returns True if item exists, False otherwise
        except ClientError as e:
            print("Error checking seller existence:", e.response['Error']['Message'])
            return False
    def get_all_sellers(self):
        """
        Retrieves all sellers with their associated contract addresses.
        Returns a list of dictionaries, each containing 'seller_address' and 'seller_contract_address'.
        """
        try:
            sellers = []
            response = self.table.scan(
                ProjectionExpression="seller_address, seller_contract_address, return_window_days"
            )
            
            # Append the first batch of items
            sellers.extend(response.get('Items', []))
            
            # Continue fetching if there are more items (pagination)
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ProjectionExpression="seller_address, seller_contract_address, return_window_days",
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                sellers.extend(response.get('Items', []))
                
            print(f"Retrieved {len(sellers)} sellers.")
            return sellers
        except ClientError as e:
            print(f"Error retrieving sellers: {e.response['Error']['Message']}")
            return []
    def clear_table(self):
        """Clears all items from the Sellers table."""
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            
            with self.table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key={'seller_address': item['seller_address']})
            
            # Paginate if there are more items
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items = response.get('Items', [])
                with self.table.batch_writer() as batch:
                    for item in items:
                        batch.delete_item(Key={'seller_address': item['seller_address']})

            print("Sellers table cleared successfully.")
        except ClientError as e:
            print(f"Error clearing Sellers table: {e.response['Error']['Message']}")
        
class ReceiptDyanmoDB:
    def __init__(self,table_name='Receipts'):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-2',  # Update with your region
            aws_access_key_id=os.getenv('blockchain_class_access_key'),
            aws_secret_access_key=os.getenv('blockchain_class_secret_key')
        )
        # create_receipts_table(table_name)
        self.table = self.dynamodb.Table(table_name)

    def insert_receipt(self, receipt_details):
        """Inserts a new receipt record in DynamoDB."""
        try:
            if 'amount' in receipt_details:
                receipt_details['amount'] = Decimal(str(receipt_details['amount']))
            
            # Insert the record, only if transaction_hash doesn't already exist
            response = self.table.put_item(
                Item=receipt_details
            )
            print("Data saved successfully:", response)
        except ClientError as e:
            print("Error saving data to DynamoDB:", e.response['Error']['Message'])

    def search_by_transaction_id(self, transaction_id):
        """Searches for a receipt by transaction ID (primary key)."""
        try:
            response = self.table.get_item(Key={'transaction_hash': transaction_id})
            return response.get('Item')
        except ClientError as e:
            print(f"Failed to retrieve receipt: {e.response['Error']['Message']}")
            return None

    def search_by_buyer_address(self, buyer_address, filter_by=None, sort_by=None, ascending=True):
        """Searches receipts by buyer address with optional filtering and sorting."""
        return self._search_by_attribute('buyer_address', buyer_address, filter_by, sort_by, ascending)

    def search_by_seller_address(self, seller_address, filter_by=None, sort_by=None, ascending=True):
        """Searches receipts by seller address with optional filtering and sorting."""
        return self._search_by_attribute('seller_address', seller_address, filter_by, sort_by, ascending)

    def _search_by_attribute(self, attribute, value, filter_by=None, sort_by=None, ascending=True):
        """Internal method to search by a specific attribute (buyer or seller) with filtering and sorting."""
        try:
            # Query using the specified attribute
            response = self.table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr(attribute).eq(value)
            )
            items = response.get('Items', [])
            
            # Filter items if a filter criterion is provided
            if filter_by:
                if 'amount' in filter_by:
                    amount_filter = Decimal(str(filter_by['amount']))
                    items = [item for item in items if item['amount'] == amount_filter]
                if 'purchase_time' in filter_by:
                    items = [item for item in items if item['purchase_time'] == filter_by['purchase_time']]

            # Sort items if a sorting criterion is provided
            if sort_by:
                reverse_order = not ascending
                if sort_by == 'amount':
                    items.sort(key=lambda x: x['amount'], reverse=reverse_order)
                elif sort_by == 'purchase_time':
                    items.sort(key=lambda x: x['purchase_time'], reverse=reverse_order)
            
            return items
        except ClientError as e:
            print(f"Failed to search receipts: {e.response['Error']['Message']}")
            return None
        
    def get_receipt_details(self, transaction_hash):
        """
        Retrieves contract_address, buyer_address, seller_address, and receipt_index for a given transaction_hash.
        """
        try:
            response = self.table.get_item(Key={'transaction_hash': transaction_hash})
            item = response.get('Item')
            
            if not item:
                print("No item found with the given transaction hash.")
                return None
            
            # Extract the required fields
            receipt_details = {
                'contract_address': item.get('seller_contract_address'),
                'buyer_address': item.get('buyer_address'),
                'seller_address': item.get('seller_address'),
                'receipt_index': int(item.get('receipt_index'))
            }
            return receipt_details
        except ClientError as e:
            print(f"Error retrieving receipt details: {e.response['Error']['Message']}")
            return None
        
    def change_receipt_status(self, transaction_hash,status,time_key):
        """
        Updates the receipt to mark funds as released.
        Adds or updates a 'status' attribute to 'FundsReleased'.
        """
        try:
            response = self.table.update_item(
                Key={'transaction_hash': transaction_hash},
                UpdateExpression=f"SET #status = :status, {time_key} = :release_time",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':release_time': Decimal(datetime.timestamp(datetime.now()))  # Storing current timestamp
                }
            )
            print("Marked as funds released:", response)
        except ClientError as e:
            print(f"Error marking funds released: {e.response['Error']['Message']}")

    def get_all_transactions(self,max_number_of_pages = 5):
        """Retrieves all transactions from the DynamoDB table."""
        try:
            # Initialize an empty list to store all transactions
            transactions = []

            # Use the scan operation to retrieve all items
            response = self.table.scan()

            # Append the first batch of items to the list
            transactions.extend(response.get('Items', []))

            # Continue fetching if there are more items
            page = 1
            while 'LastEvaluatedKey' in response:
                if page>max_number_of_pages:
                    break
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                transactions.extend(response.get('Items', []))
                page+=1
            print(f"Retrieved {len(transactions)} transactions.")
            return transactions
        except ClientError as e:
            print(f"Error retrieving transactions: {e.response['Error']['Message']}")
            return None

    def get_unique_buyers(self):
        """Retrieves all unique buyer addresses."""
        try:
            unique_buyers = set()
            buyers = []
            response = self.table.scan(
                ProjectionExpression="buyer_address"
            )
            
            for item in response.get('Items', []):
                buyer_address = item['buyer_address']
                if buyer_address not in unique_buyers:
                    unique_buyers.add(buyer_address)
                    buyers.append(buyer_address)
                
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ProjectionExpression="buyer_address",
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                for item in response.get('Items', []):
                    buyer_address = item['buyer_address']
                    if buyer_address not in unique_buyers:
                        unique_buyers.add(buyer_address)
                        buyers.append(buyer_address)

            print(f"Found {len(buyers)} unique buyers.")
            return buyers
        except ClientError as e:
            print(f"Error retrieving unique buyers: {e.response['Error']['Message']}")
            return []

    def clear_table(self):
        """Clears all items from the Receipts table."""
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            
            with self.table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key={'transaction_hash': item['transaction_hash']})
            
            # Paginate if there are more items
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items = response.get('Items', [])
                with self.table.batch_writer() as batch:
                    for item in items:
                        batch.delete_item(Key={'transaction_hash': item['transaction_hash']})

            print("Receipts table cleared successfully.")
        except ClientError as e:
            print(f"Error clearing Receipts table: {e.response['Error']['Message']}")

class AccountsDynamoDB:
    def __init__(self, table_name='Accounts'):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-2',
            aws_access_key_id=os.getenv('blockchain_class_access_key'),
            aws_secret_access_key=os.getenv('blockchain_class_secret_key')
        )
        self.table = self.dynamodb.Table(table_name)

    def insert_account(self, accounts_data):
        try:
            response = self.table.put_item(
                Item=accounts_data,
                ConditionExpression="attribute_not_exists(user_id)"
            )
            print("Account address inserted successfully:", response)
            return True,f"Account address inserted successfully"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print("Account already exists.")
                return False,f"Account already exists."
            else:
                return False,f"Error creating account: {e.response['Error']['Message']}"
    def account_exists(self, user_id):
        """
        Checks if a seller exists in the table.
        Returns True if the seller exists, False otherwise.
        """
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            print(response)
            item = response.get('Item', {})
            if len(list(item.keys()))==0:
                return []
            else:
                return [item]
        except ClientError as e:
            print("Error checking seller existence:", e.response['Error']['Message'])
            return {}
    def address_used(self, address):
        """Searches receipts by buyer address with optional filtering and sorting."""
        return self._search_by_attribute('account_address', address)      
    def get_all_accounts(self):
        """
        Retrieves all sellers with their associated contract addresses.
        Returns a list of dictionaries, each containing 'seller_address' and 'seller_contract_address'.
        """
        try:
            accounts = []
            response = self.table.scan(
                ProjectionExpression="user_id, account_address"
            )
            
            # Append the first batch of items
            accounts.extend(response.get('Items', []))
            
            # Continue fetching if there are more items (pagination)
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ProjectionExpression="user_id, account_address",
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                accounts.extend(response.get('Items', []))
                
            print(f"Retrieved {len(accounts)} accounts.")
            return accounts
        except ClientError as e:
            print(f"Error retrieving accounts: {e.response['Error']['Message']}")
            return []
    def _search_by_attribute(self, attribute, value):
        """Internal method to search by a specific attribute (buyer or seller) with filtering and sorting."""
        try:
            # Query using the specified attribute
            response = self.table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr(attribute).eq(value)
            )
            items = response.get('Items', [])        
            return items
        except ClientError as e:
            print(f"Failed to search receipts: {e.response['Error']['Message']}")
            return []
    
    def clear_table(self):
        """Clears all items from the Accounts table."""
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            
            with self.table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key={'user_id': item['user_id']})
            
            # Paginate if there are more items
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items = response.get('Items', [])
                with self.table.batch_writer() as batch:
                    for item in items:
                        batch.delete_item(Key={'user_id': item['user_id']})

            return "Accounts table cleared successfully."
        except ClientError as e:
            return f"Error clearing Accounts table: {e.response['Error']['Message']}"
