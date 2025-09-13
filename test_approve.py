import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

ERC20_ABI = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]'

rpc_url = os.getenv('ARBITRUM_RPC_URL')
private_key = os.getenv('PRIVATE_KEY')
usdc_address = os.getenv('USDC_CONTRACT_ADDRESS')
sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS')

w3 = Web3(Web3.HTTPProvider(rpc_url))
account = w3.eth.account.from_key(private_key)

print(f"Account: {account.address}")
print(f"USDC Address: {usdc_address}")
print(f"Sports AMM Address: {sports_amm_address}")

usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=ERC20_ABI)

# Test different gas configurations
try:
    print("\n--- Test 1: No gas parameters ---")
    tx1 = usdc_contract.functions.approve(sports_amm_address, 1000000).build_transaction({
        'from': account.address, 
        'nonce': w3.eth.get_transaction_count(account.address)
    })
    print("✅ Success: No gas parameters")
except Exception as e:
    print(f"❌ Error: {e}")

try:
    print("\n--- Test 2: With gasPrice ---")
    tx2 = usdc_contract.functions.approve(sports_amm_address, 1000000).build_transaction({
        'from': account.address, 
        'nonce': w3.eth.get_transaction_count(account.address),
        'gasPrice': w3.eth.gas_price
    })
    print("✅ Success: With gasPrice")
except Exception as e:
    print(f"❌ Error: {e}")

try:
    print("\n--- Test 3: With gas limit ---")
    tx3 = usdc_contract.functions.approve(sports_amm_address, 1000000).build_transaction({
        'from': account.address, 
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 100000
    })
    print("✅ Success: With gas limit")
except Exception as e:
    print(f"❌ Error: {e}")

try:
    print("\n--- Test 4: With both gas and gasPrice ---")
    tx4 = usdc_contract.functions.approve(sports_amm_address, 1000000).build_transaction({
        'from': account.address, 
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price
    })
    print("✅ Success: With both gas and gasPrice")
except Exception as e:
    print(f"❌ Error: {e}")
