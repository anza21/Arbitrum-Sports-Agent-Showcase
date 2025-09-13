import os
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 TESTING DIFFERENT SPORTS AMM CONTRACTS ---")
    
    load_dotenv(os.path.join('.', '.env'))
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')
    
    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    
    # Try different possible Sports AMM contract addresses
    contracts_to_test = [
        "0xFb4e4811C7A811E098A556bD79B64c20b479E431",  # Current one
        "0x0000000000000000000000000000000000000000",  # Zero address
        "0x1234567890123456789012345678901234567890",  # Placeholder
    ]
    
    # Simple ABI to test if contract responds
    test_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'
    
    for contract_addr in contracts_to_test:
        print(f"\n--- Testing Contract: {contract_addr} ---")
        
        try:
            # Check if contract has code
            code = w3.eth.get_code(contract_addr)
            if code == b'':
                print("❌ No code")
                continue
            else:
                print(f"✅ Has code ({len(code)} bytes)")
            
            # Try to call a simple function
            contract = w3.eth.contract(address=w3.to_checksum_address(contract_addr), abi=test_abi)
            
            try:
                name = contract.functions.name().call()
                print(f"✅ Name: {name}")
            except Exception as e:
                print(f"⚠️ Name call failed: {e}")
            
            try:
                symbol = contract.functions.symbol().call()
                print(f"✅ Symbol: {symbol}")
            except Exception as e:
                print(f"⚠️ Symbol call failed: {e}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Check if we can find the contract from the market data
    print(f"\n--- CHECKING MARKET DATA FOR CONTRACT INFO ---")
    
    try:
        api_key = os.getenv('OVERTIME_REST_API_KEY')
        market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
        url = f"https://api.overtime.io/overtime-v2/networks/10/markets/{market_id}"
        headers = {"x-api-key": api_key}
        
        response = requests.get(url, headers=headers)
        market = response.json()
        
        # Look for any contract-related fields
        for key, value in market.items():
            if isinstance(value, str) and value.startswith('0x') and len(value) == 42:
                print(f"Potential contract address: {key} = {value}")
                
    except Exception as e:
        print(f"Error checking market data: {e}")

if __name__ == "__main__":
    main()
