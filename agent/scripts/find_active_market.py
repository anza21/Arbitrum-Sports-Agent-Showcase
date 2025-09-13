import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 FINDING ACTIVE MARKET FOR TRADING ---")
    load_dotenv()

    api_key = os.getenv('OVERTIME_REST_API_KEY', 'your_api_key_here')
    headers = {"x-api-key": api_key}

    try:
        # Get all markets for Arbitrum
        markets_url = "https://api.overtime.io/overtime-v2/networks/42161/markets"
        response = requests.get(markets_url, headers=headers)
        
        if response.status_code == 200:
            markets_data = response.json()
            print(f"✅ API Response received")
            print(f"Response type: {type(markets_data)}")
            print(f"Response keys: {list(markets_data.keys()) if isinstance(markets_data, dict) else 'Not a dict'}")
            
            # Check if markets is a list or if it's nested
            if isinstance(markets_data, list):
                markets = markets_data
            elif isinstance(markets_data, dict) and 'markets' in markets_data:
                markets = markets_data['markets']
            else:
                print(f"Unexpected response structure: {markets_data}")
                return
                
            print(f"✅ Found {len(markets)} markets")
            
            # Look for active markets with valid data
            active_markets = []
            for i, market in enumerate(markets[:10]):  # Check first 10 markets
                try:
                    market_id = market.get('id', '')
                    game_id = market.get('gameId', '')
                    status = market.get('status', -1)
                    odds = market.get('odds', [])
                    proof = market.get('proof', [])
                    
                    print(f"\nMarket ID: {market_id}")
                    print(f"Game ID: {game_id}")
                    print(f"Status: {status}")
                    print(f"Odds Count: {len(odds)}")
                    print(f"Proof Length: {len(proof)}")
                    print(f"Player Props: {market.get('playerProps', {})}")
                    
                    # Check if market is suitable for trading
                    if (status == 0 and  # Active status
                        len(odds) >= 2 and  # Has odds
                        len(proof) > 0 and  # Has merkle proof
                        game_id and  # Has game ID
                        market.get('playerProps', {}).get('playerId', 0) > 0):  # Has player ID
                        
                        active_markets.append(market)
                        print(f"✅ This market looks good for trading!")
                    else:
                        print(f"❌ This market is not suitable")
                        
                except Exception as e:
                    print(f"❌ Error processing market: {e}")
                    continue
            
            print(f"\n--- SUMMARY ---")
            print(f"Total markets checked: 10")
            print(f"Active markets found: {len(active_markets)}")
            
            if active_markets:
                print(f"\n🎯 RECOMMENDED MARKET FOR TRADING:")
                best_market = active_markets[0]
                print(f"Market ID: {best_market['id']}")
                print(f"Game ID: {best_market['gameId']}")
                print(f"Status: {best_market['status']}")
                print(f"Odds: {best_market['odds']}")
                print(f"Proof: {best_market['proof']}")
                print(f"Player Props: {best_market['playerProps']}")
            else:
                print(f"\n❌ No suitable markets found for trading")
                
        else:
            print(f"❌ Failed to fetch markets: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
