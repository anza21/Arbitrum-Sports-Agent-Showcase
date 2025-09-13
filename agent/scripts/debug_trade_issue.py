import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 DEBUG: Investigating Trade Issue ---")
    load_dotenv()

    # --- Load variables ---
    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    wallet_address = os.getenv('WALLET_ADDRESS', '0xCbAAA6b243E392D5a26C3CeF0458E735CBe1A187')
    private_key = os.getenv('PRIVATE_KEY', '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef')
    api_key = os.getenv('OVERTIME_REST_API_KEY', 'your_api_key_here')
    usdc_address = os.getenv('USDC_CONTRACT_ADDRESS', '0xaf88d065e77c8cC2239327C5EDb3A432268e5831')
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS', '0x289cf7f046d34b228c04db7bfe1562d5a3b7c49e')

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum RPC")
        return

    account = w3.eth.account.from_key(private_key)
    print(f"✅ Connected to Arbitrum. Wallet: {account.address}")

    # --- Check market data ---
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    print(f"\n--- Step 1: Fetching Market Data ---")
    
    market_url = f"https://api.overtime.io/overtime-v2/networks/42161/markets/{market_id}"
    headers = {"x-api-key": api_key}
    
    try:
        market_response = requests.get(market_url, headers=headers)
        print(f"Market API Status: {market_response.status_code}")
        
        if market_response.status_code == 200:
            market = market_response.json()
            print(f"✅ Market data received")
            print(f"Game ID: {market.get('gameId', 'N/A')}")
            print(f"Sport ID: {market.get('subLeagueId', 'N/A')}")
            print(f"Type ID: {market.get('typeId', 'N/A')}")
            print(f"Status: {market.get('status', 'N/A')}")
            print(f"Line: {market.get('line', 'N/A')}")
            print(f"Odds: {market.get('odds', [])}")
        else:
            print(f"❌ Market API failed: {market_response.text}")
            return
    except Exception as e:
        print(f"❌ Market API error: {e}")
        return

    # --- Check quote ---
    print(f"\n--- Step 2: Fetching Quote ---")
    
    trade_data_for_quote = [{
        "gameId": market['gameId'], 
        "sportId": market['subLeagueId'], 
        "typeId": market['typeId'],
        "maturity": market['maturity'], 
        "status": market['status'], 
        "line": market['line'],
        "playerId": market['playerProps']['playerId'], 
        "odds": [o['normalizedImplied'] for o in market['odds']],
        "merkleProof": market['proof'], 
        "position": 1,
        "combinedPositions": market['combinedPositions'], 
        "live": False
    }]

    quote_url = "https://api.overtime.io/overtime-v2/networks/42161/quote"
    payload = {"buyInAmount": 3.08, "tradeData": trade_data_for_quote, "collateral": "USDC"}
    
    try:
        quote_response = requests.post(quote_url, headers=headers, json=payload)
        print(f"Quote API Status: {quote_response.status_code}")
        
        if quote_response.status_code == 200:
            quote = quote_response.json()
            print(f"✅ Quote received")
            print(f"Quote data: {json.dumps(quote, indent=2)}")
        else:
            print(f"❌ Quote API failed: {quote_response.text}")
            return
    except Exception as e:
        print(f"❌ Quote API error: {e}")
        return

    # --- Check contract addresses ---
    print(f"\n--- Step 3: Checking Contract Addresses ---")
    print(f"USDC Address: {usdc_address}")
    print(f"Sports AMM Address: {sports_amm_address}")
    
    # Check if contracts exist
    try:
        usdc_code = w3.eth.get_code(w3.to_checksum_address(usdc_address))
        print(f"USDC Contract Code Length: {len(usdc_code)} bytes")
        
        sports_amm_code = w3.eth.get_code(w3.to_checksum_address(sports_amm_address))
        print(f"Sports AMM Contract Code Length: {len(sports_amm_code)} bytes")
        
        if len(usdc_code) == 0:
            print("❌ USDC contract not found at address")
        if len(sports_amm_code) == 0:
            print("❌ Sports AMM contract not found at address")
    except Exception as e:
        print(f"❌ Contract check error: {e}")

    # --- Check wallet balance ---
    print(f"\n--- Step 4: Checking Wallet Balance ---")
    try:
        eth_balance = w3.eth.get_balance(account.address)
        print(f"ETH Balance: {w3.from_wei(eth_balance, 'ether')} ETH")
        
        # Check USDC balance
        usdc_abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=usdc_abi)
        usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
        print(f"USDC Balance: {usdc_balance / (10**6)} USDC")
    except Exception as e:
        print(f"❌ Balance check error: {e}")

if __name__ == "__main__":
    main()
