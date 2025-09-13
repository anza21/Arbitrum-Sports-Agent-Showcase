import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 DEBUG: Market Data Analysis ---")
    load_dotenv()

    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum RPC")
        return

    account = w3.eth.account.from_key(os.getenv('PRIVATE_KEY', '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'))
    sports_amm_address = '0xfb64E79A562F7250131cf528242CEB10fDC82395'
    usdc_address = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831'
    
    print(f"✅ Connected to Arbitrum. Wallet: {account.address}")

    # --- Get market data ---
    api_key = os.getenv('OVERTIME_REST_API_KEY', 'your_api_key_here')
    market_id = "0x3230323530393133343938323534463400000000000000000000000000000000"
    
    market_url = f"https://api.overtime.io/overtime-v2/networks/42161/markets/{market_id}"
    headers = {"x-api-key": api_key}
    market = requests.get(market_url, headers=headers).json()
    
    print(f"\n--- Market Analysis ---")
    print(f"Game: {market.get('homeTeam', 'N/A')} vs {market.get('awayTeam', 'N/A')}")
    print(f"Type: {market.get('type', 'N/A')} - {market.get('originalMarketName', 'N/A')}")
    print(f"Line: {market.get('line', 'N/A')}")
    print(f"Status: {market.get('status', 'N/A')}")
    print(f"Is Open: {market.get('isOpen', 'N/A')}")
    print(f"Is Resolved: {market.get('isResolved', 'N/A')}")
    print(f"Is Cancelled: {market.get('isCancelled', 'N/A')}")
    print(f"Is Paused: {market.get('isPaused', 'N/A')}")
    print(f"Player Props: {market.get('playerProps', {})}")
    print(f"Odds: {market.get('odds', [])}")
    print(f"Proof Length: {len(market.get('proof', []))}")

    # --- Check if market is actually tradeable ---
    print(f"\n--- Market Tradeability Check ---")
    
    if market.get('status') != 0:
        print(f"❌ Market status is not 0 (active): {market.get('status')}")
    else:
        print(f"✅ Market status is active")
        
    if not market.get('isOpen', False):
        print(f"❌ Market is not open: {market.get('isOpen')}")
    else:
        print(f"✅ Market is open")
        
    if market.get('isResolved', False):
        print(f"❌ Market is already resolved: {market.get('isResolved')}")
    else:
        print(f"✅ Market is not resolved")
        
    if market.get('isCancelled', False):
        print(f"❌ Market is cancelled: {market.get('isCancelled')}")
    else:
        print(f"✅ Market is not cancelled")
        
    if market.get('isPaused', False):
        print(f"❌ Market is paused: {market.get('isPaused')}")
    else:
        print(f"✅ Market is not paused")

    # --- Try different market types ---
    print(f"\n--- Testing Different Market Types ---")
    
    # Get all markets and find a better one
    markets_url = "https://api.overtime.io/overtime-v2/networks/42161/markets"
    response = requests.get(markets_url, headers=headers)
    
    if response.status_code == 200:
        markets_data = response.json()
        if isinstance(markets_data, list):
            markets = markets_data
        elif isinstance(markets_data, dict) and 'markets' in markets_data:
            markets = markets_data['markets']
        else:
            markets = []
            
        print(f"Found {len(markets)} total markets")
        
        # Look for a simple moneyline market
        for market in markets[:5]:
            market_type = market.get('type', '')
            is_open = market.get('isOpen', False)
            status = market.get('status', -1)
            proof_length = len(market.get('proof', []))
            
            print(f"\nMarket: {market.get('homeTeam', 'N/A')} vs {market.get('awayTeam', 'N/A')}")
            print(f"  Type: {market_type}")
            print(f"  Status: {status}")
            print(f"  Is Open: {is_open}")
            print(f"  Proof Length: {proof_length}")
            
            if (market_type == 'winner' and 
                is_open and 
                status == 0 and 
                proof_length > 0):
                print(f"  ✅ This looks like a good market for testing!")
                
                # Test this market
                try:
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
                    quote = requests.post(quote_url, headers=headers, json=payload).json()
                    
                    if 'quoteData' in quote:
                        print(f"  ✅ Quote successful for this market!")
                        print(f"  Quote: {quote['quoteData']}")
                        break
                    else:
                        print(f"  ❌ Quote failed for this market: {quote}")
                        
                except Exception as e:
                    print(f"  ❌ Error testing market: {e}")
            else:
                print(f"  ❌ Not suitable for trading")

if __name__ == "__main__":
    main()
