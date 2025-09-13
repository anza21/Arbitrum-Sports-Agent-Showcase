import os
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 CHECKING MARKET STATUS ---")
    
    # Load .env from the project root
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    api_key = os.getenv('OVERTIME_REST_API_KEY')
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    
    print(f"Market ID: {market_id}")
    
    # Get market data
    url = f"https://api.overtime.io/overtime-v2/networks/10/markets/{market_id}"
    headers = {"x-api-key": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        market = response.json()
        
        print(f"\n--- MARKET DETAILS ---")
        print(f"Game ID: {market.get('gameId')}")
        print(f"Sport ID: {market.get('subLeagueId')}")
        print(f"Type ID: {market.get('typeId')}")
        print(f"Line: {market.get('line')}")
        print(f"Status: {market.get('status')}")
        print(f"Maturity: {market.get('maturity')}")
        print(f"Player Props: {market.get('playerProps')}")
        print(f"Odds: {market.get('odds')}")
        print(f"Proof: {market.get('proof')}")
        print(f"Combined Positions: {market.get('combinedPositions')}")
        
        # Check if market is still active
        status = market.get('status', -1)
        if status == 0:
            print("\n✅ Market is ACTIVE")
        elif status == 1:
            print("\n⚠️ Market is PAUSED")
        elif status == 2:
            print("\n❌ Market is CANCELLED")
        elif status == 3:
            print("\n❌ Market is RESOLVED")
        else:
            print(f"\n❓ Market status unknown: {status}")
            
        # Check if we can get a quote
        print(f"\n--- TESTING QUOTE ---")
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
        
        quote_url = "https://api.overtime.io/overtime-v2/networks/10/quote"
        quote_payload = {
            "buyInAmount": 3.08,
            "tradeData": trade_data_for_quote,
            "collateral": "USDC"
        }
        
        quote_response = requests.post(quote_url, headers=headers, json=quote_payload)
        if quote_response.status_code == 200:
            quote_data = quote_response.json()
            print("✅ Quote successful!")
            print(f"Quote data: {quote_data}")
        else:
            print(f"❌ Quote failed: {quote_response.status_code}")
            print(f"Response: {quote_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
