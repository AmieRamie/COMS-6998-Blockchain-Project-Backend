from pydantic import BaseModel
from typing import List

class create_seller_contract(BaseModel):
    seller_account_address:str
    return_window_days:int

class issue_receipt_model(BaseModel):
    seller_address:str
    buyer_address:str
    amount_eth:float
    item_name:str

class get_seller_receipts_model(BaseModel):
    seller_address:str

class get_buyer_receipts_model(BaseModel):
    buyer_address:str

class request_return_model(BaseModel):
    # seller_address:str
    # buyer_address:str
    # receipt_index:int
    transaction_hash:str

class release_return_model(BaseModel):
    transaction_hash:str

class credentials(BaseModel):
    username:str
    password:str
