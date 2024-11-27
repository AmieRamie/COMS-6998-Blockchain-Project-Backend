from fastapi import FastAPI, Response, HTTPException, File, UploadFile, Form, Request, BackgroundTasks,Depends
from fastapi.responses import RedirectResponse,JSONResponse, StreamingResponse, PlainTextResponse
import uvicorn
from web3.datastructures import AttributeDict
from hexbytes import HexBytes
from typing import Any
from services.dataservice import DataService
from services.models import create_seller_contract, issue_receipt_model, get_seller_receipts_model,get_buyer_receipts_model, request_return_model, release_return_model,credentials
from fastapi.middleware.cors import CORSMiddleware
import json
import requests

ds = DataService()
app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def make_json_serializable(data):
    if isinstance(data, AttributeDict):
        return {k: make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_json_serializable(i) for i in data]
    elif isinstance(data, HexBytes):
        return data.hex()  # Convert HexBytes to hex string
    elif isinstance(data, bytes):
        return data.decode("utf-8")  # Convert bytes to string if possible
    elif isinstance(data, (int, float, str, bool)) or data is None:
        return data
    else:
        return str(data) 

@app.get("/reset_tables")
async def reset_tables():
    try:
        message = ds.clear_tables()
        response = ds.restart_ganache()
        with open('data.json', 'w') as json_file:
            json.dump({}, json_file, indent=4)
        return {'ganache_response':response,'accounts_table_response':message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/get_all_accounts_in_network") #
async def get_all_accounts_in_network():
    try:
        all_accounts = ds.get_all_network_accounts()
        return {'all_accounts':all_accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/get_sellers_w_contracts")
async def get_sellers_w_contracts():
    try:
        all_sellers = ds.get_sellers_with_contracts()
        return all_sellers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_seller_contract")
async def create_seller_contract(params:create_seller_contract):
    try:
        create_seller_contract_json = params.dict()
        contract_address,success = ds.create_seller_account_contract(create_seller_contract_json['seller_account_address'],create_seller_contract_json['return_window_days'])
        if success:
            return {'seller_address':create_seller_contract_json['seller_account_address'], 'contract_address':contract_address, 'return_window_days':create_seller_contract_json['return_window_days']}
        else:
            raise HTTPException(status_code=500, detail='Seller already exists')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/issue_receipt")
async def issue_receipt(params:issue_receipt_model):
    try:
        issue_receipt_json = params.dict()
        receipt_details, success, error_message = ds.issue_receipt(issue_receipt_json['seller_address'], issue_receipt_json['buyer_address'], issue_receipt_json['amount_eth'], issue_receipt_json['item_name'])
        if success:
            return {'success':success,'receipt_details':receipt_details}
        else:
            raise HTTPException(status_code=500, detail=error_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_seller_receipts")
async def get_seller_receipts(params:get_seller_receipts_model):
    try:
        get_seller_receipts_json = params.dict()
        all_receipts, success = ds.get_receipts_for_seller(get_seller_receipts_json['seller_address'])
        if success:
            return {'success':success,'all_receipts':all_receipts}
        else:
            raise HTTPException(status_code=500, detail='error with DynamoDB lookup')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_buyer_receipts")
async def get_buyer_receipts(params:get_buyer_receipts_model):
    try:
        get_buyer_receipts_json = params.dict()
        all_receipts, success = ds.get_receipts_for_buyer(get_buyer_receipts_json['buyer_address'])
        if success:
            return {'success':success,'all_receipts':all_receipts}
        else:
            raise HTTPException(status_code=500, detail='error with DynamoDB lookup')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/request_return")
async def request_return(params:request_return_model):
    try:
        request_return_json = params.dict()
        return_request_details, success, error_message = ds.request_return(request_return_json['transaction_hash'])
        print(return_request_details, success, error_message)
        if success:
            return {'success':success,'return_request_details':make_json_serializable(return_request_details)}
        else:
            raise HTTPException(status_code=500, detail=error_message)
    except Exception as e:
        print('For some reason the exception is firing', e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/release_funds") #wait for return window to pass then seller can get money
async def release_funds(params:release_return_model):
    try:
        release_return_json = params.dict()
        release_return_details, success, error_message = ds.funds_release(release_return_json['transaction_hash'])
        print(release_return_details, success, error_message)
        if success:
            return {'success':success,'release_return_details':make_json_serializable(release_return_details)}
        else:
            raise HTTPException(status_code=500, detail=error_message)
    except Exception as e:
        print('For some reason the exception is firing', e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify_login") 
async def verify_login(params:credentials):
    try:
        credentials_return_json = params.dict()
        username=credentials_return_json["username"]
        password=credentials_return_json["password"]
        response = ds.verify_login(username,password)
        return response
    except Exception as e:
        print('For some reason the exception is firing', e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_new_user") 
async def create_new_user(params:credentials):
    try:
        credentials_return_json = params.dict()
        username=credentials_return_json["username"]
        password=credentials_return_json["password"]
        response = ds.create_new_user(username,password)
        return response
    except Exception as e:
        print('For some reason the exception is firing', e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_user_data")
async def get_user_data():
    try:
        all_accounts = ds.get_all_accounts()
        return all_accounts
    except Exception as e:
        print('For some reason the exception is firing', e)
        raise HTTPException(status_code=500, detail=str(e))





    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)