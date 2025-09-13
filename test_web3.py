import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

rpc_url = os.getenv('ARBITRUM_RPC_URL')
private_key = os.getenv('PRIVATE_KEY')

print(f"RPC URL: {rpc_url}")
print(f"Private Key: {private_key[:10]}...")

w3 = Web3(Web3.HTTPProvider(rpc_url))
print(f"Connected: {w3.is_connected()}")

account = w3.eth.account.from_key(private_key)
print(f"Account: {account.address}")

# Test getting nonce
nonce = w3.eth.get_transaction_count(account.address)
print(f"Nonce: {nonce}")

# Test getting gas price
try:
    gas_price = w3.eth.gas_price
    print(f"Gas Price: {gas_price}")
except Exception as e:
    print(f"Gas Price Error: {e}")

# Test getting balance
balance = w3.eth.get_balance(account.address)
print(f"Balance: {balance}")
