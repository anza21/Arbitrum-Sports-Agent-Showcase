import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 VERIFICATION: Using Official Postman Documentation ---")
    load_dotenv()

    # --- Load variables ---
    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    wallet_address = os.getenv('WALLET_ADDRESS', '0xCbAAA6b243E392D5a26C3CeF0458E735CBe1A187')
    private_key = os.getenv('PRIVATE_KEY', '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef')
    api_key = os.getenv('OVERTIME_REST_API_KEY', 'your_api_key_here')
    usdc_address = os.getenv('USDC_CONTRACT_ADDRESS', '0xaf88d065e77c8cC2239327C5EDb3A432268e5831')
    sports_amm_address = '0xfb64E79A562F7250131cf528242CEB10fDC82395'

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum RPC")
        return

    account = w3.eth.account.from_key(private_key)
    print(f"✅ Connected to Arbitrum. Wallet: {account.address}")

    # --- Step 1: Verify Market Data using Postman Documentation ---
    print(f"\n--- Step 1: Verifying Market Data (Postman Docs) ---")
    
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
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
            print(f"Maturity: {market.get('maturity', 'N/A')}")
            print(f"Odds: {json.dumps(market.get('odds', []), indent=2)}")
            print(f"Player Props: {json.dumps(market.get('playerProps', {}), indent=2)}")
        else:
            print(f"❌ Market API failed: {market_response.text}")
            return
    except Exception as e:
        print(f"❌ Market API error: {e}")
        return

    # --- Step 2: Verify Quote using Postman Documentation ---
    print(f"\n--- Step 2: Verifying Quote (Postman Docs) ---")
    
    # According to Postman docs, the trade data structure should be:
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
        "position": 1,  # 0=Home, 1=Away, 2=Draw
        "combinedPositions": market['combinedPositions'], 
        "live": False
    }]

    print(f"Trade Data for Quote: {json.dumps(trade_data_for_quote, indent=2)}")

    quote_url = "https://api.overtime.io/overtime-v2/networks/42161/quote"
    payload = {
        "buyInAmount": 3.08, 
        "tradeData": trade_data_for_quote, 
        "collateral": "USDC"
    }
    
    try:
        quote_response = requests.post(quote_url, headers=headers, json=payload)
        print(f"Quote API Status: {quote_response.status_code}")
        
        if quote_response.status_code == 200:
            quote = quote_response.json()
            print(f"✅ Quote received")
            print(f"Quote Response: {json.dumps(quote, indent=2)}")
        else:
            print(f"❌ Quote API failed: {quote_response.text}")
            return
    except Exception as e:
        print(f"❌ Quote API error: {e}")
        return

    # --- Step 3: Verify Contract Addresses ---
    print(f"\n--- Step 3: Verifying Contract Addresses ---")
    print(f"USDC Address: {usdc_address}")
    print(f"Sports AMM Address: {sports_amm_address}")
    
    try:
        usdc_code = w3.eth.get_code(w3.to_checksum_address(usdc_address))
        print(f"USDC Contract Code Length: {len(usdc_code)} bytes")
        
        sports_amm_code = w3.eth.get_code(w3.to_checksum_address(sports_amm_address))
        print(f"Sports AMM Contract Code Length: {len(sports_amm_code)} bytes")
        
        if len(usdc_code) == 0:
            print("❌ USDC contract not found at address")
        else:
            print("✅ USDC contract found")
            
        if len(sports_amm_code) == 0:
            print("❌ Sports AMM contract not found at address")
        else:
            print("✅ Sports AMM contract found")
    except Exception as e:
        print(f"❌ Contract check error: {e}")

    # --- Step 4: Check Wallet Balance ---
    print(f"\n--- Step 4: Checking Wallet Balance ---")
    try:
        eth_balance = w3.eth.get_balance(account.address)
        print(f"ETH Balance: {w3.from_wei(eth_balance, 'ether')} ETH")
        
        # Check USDC balance
        usdc_abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=usdc_abi)
        usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
        print(f"USDC Balance: {usdc_balance / (10**6)} USDC")
        
        if usdc_balance < 3.08 * (10**6):
            print("❌ Insufficient USDC balance for trade")
        else:
            print("✅ Sufficient USDC balance for trade")
    except Exception as e:
        print(f"❌ Balance check error: {e}")

    # --- Step 5: Analyze Trade Data Structure ---
    print(f"\n--- Step 5: Analyzing Trade Data Structure ---")
    print("According to Postman documentation:")
    print("- gameId: Should be bytes32")
    print("- sportId: Should be uint16") 
    print("- typeId: Should be uint16")
    print("- maturity: Should be uint256")
    print("- status: Should be uint8")
    print("- line: Should be int256")
    print("- playerId: Should be uint256")
    print("- odds: Should be uint256[]")
    print("- merkleProof: Should be bytes32[]")
    print("- position: Should be uint8 (0=Home, 1=Away, 2=Draw)")
    print("- combinedPositions: Should be CombinedPosition[][]")
    print("- live: Should be bool")

    # Check our data types
    print(f"\nOur data types:")
    print(f"gameId: {type(market['gameId'])} = {market['gameId']}")
    print(f"sportId: {type(market['subLeagueId'])} = {market['subLeagueId']}")
    print(f"typeId: {type(market['typeId'])} = {market['typeId']}")
    print(f"maturity: {type(market['maturity'])} = {market['maturity']}")
    print(f"status: {type(market['status'])} = {market['status']}")
    print(f"line: {type(market['line'])} = {market['line']}")
    print(f"playerId: {type(market['playerProps']['playerId'])} = {market['playerProps']['playerId']}")
    print(f"odds: {type([o['normalizedImplied'] for o in market['odds']])} = {[o['normalizedImplied'] for o in market['odds']]}")
    print(f"position: {type(1)} = {1}")

if __name__ == "__main__":
    main()
