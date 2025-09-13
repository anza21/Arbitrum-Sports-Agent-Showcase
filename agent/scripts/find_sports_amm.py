import os
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 FINDING SPORTS AMM CONTRACT ---")
    
    load_dotenv(os.path.join('.', '.env'))
    api_key = os.getenv('OVERTIME_REST_API_KEY')
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')
    
    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    
    # Get market data to see if there's contract info
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    url = f"https://api.overtime.io/overtime-v2/networks/10/markets/{market_id}"
    headers = {"x-api-key": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        market = response.json()
        
        print(f"Market data keys: {list(market.keys())}")
        
        # Look for contract addresses in the market data
        for key, value in market.items():
            if 'contract' in key.lower() or 'address' in key.lower():
                print(f"{key}: {value}")
                
    except Exception as e:
        print(f"Error getting market data: {e}")
    
    # Try common Sports AMM contract addresses on Optimism
    sports_amm_addresses = [
        "0xFb4e4811C7A811E098A556bD79B64c20b479E431",  # Current one
        "0x0000000000000000000000000000000000000000",  # Placeholder
        "0x1234567890123456789012345678901234567890",  # Placeholder
    ]
    
    print(f"\n--- CHECKING SPORTS AMM ADDRESSES ---")
    
    for addr in sports_amm_addresses:
        try:
            code = w3.eth.get_code(addr)
            if code != b'':
                print(f"✅ {addr}: Has code ({len(code)} bytes)")
            else:
                print(f"❌ {addr}: No code")
        except Exception as e:
            print(f"❌ {addr}: Error - {e}")
    
    # Check if we can find the contract from the API
    print(f"\n--- CHECKING API ENDPOINTS ---")
    
    try:
        # Try to get network info
        network_url = "https://api.overtime.io/overtime-v2/networks/10"
        response = requests.get(network_url, headers=headers)
        if response.status_code == 200:
            network_data = response.json()
            print(f"Network data: {network_data}")
        else:
            print(f"Network endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"Error getting network data: {e}")

if __name__ == "__main__":
    main()
