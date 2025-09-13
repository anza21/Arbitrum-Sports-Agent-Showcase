import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 TEST: Trade Step Only ---")
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

    # --- Get market data ---
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    market_url = f"https://api.overtime.io/overtime-v2/networks/42161/markets/{market_id}"
    headers = {"x-api-key": api_key}
    market = requests.get(market_url, headers=headers).json()
    
    # --- Get quote ---
    trade_data_for_quote = [{
        "gameId": market['gameId'], "sportId": market['subLeagueId'], "typeId": market['typeId'],
        "maturity": market['maturity'], "status": market['status'], "line": market['line'],
        "playerId": market['playerProps']['playerId'], "odds": [o['normalizedImplied'] for o in market['odds']],
        "merkleProof": market['proof'], "position": 1,
        "combinedPositions": market['combinedPositions'], "live": False
    }]

    quote_url = "https://api.overtime.io/overtime-v2/networks/42161/quote"
    payload = {"buyInAmount": 3.08, "tradeData": trade_data_for_quote, "collateral": "USDC"}
    quote = requests.post(quote_url, headers=headers, json=payload).json()

    # --- Test contract interaction without sending transaction ---
    print(f"\n--- Testing Contract Interaction ---")
    
    # Simple ABI for testing
    simple_abi = '[{"inputs":[{"internalType":"bytes32","name":"gameId","type":"bytes32"},{"internalType":"uint16","name":"sportId","type":"uint16"},{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint256","name":"maturity","type":"uint256"},{"internalType":"uint8","name":"status","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"},{"internalType":"uint256","name":"playerId","type":"uint256"},{"internalType":"uint256[]","name":"odds","type":"uint256[]"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"uint8","name":"position","type":"uint8"},{"internalType":"bool","name":"live","type":"bool"}],"name":"testTrade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
    
    try:
        sports_amm = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=simple_abi)
        
        # Test data conversion
        test_data = {
            "gameId": bytes.fromhex(market['gameId'][2:]),  # bytes32
            "sportId": int(market['subLeagueId']),  # uint16
            "typeId": int(market['typeId']),  # uint16
            "maturity": int(market['maturity']),  # uint256
            "status": int(market['status']),  # uint8
            "line": int(market['line'] * 100),  # int256
            "playerId": int(market['playerProps']['playerId']),  # uint256
            "odds": [w3.to_wei(o['normalizedImplied'], 'ether') for o in market['odds']],  # uint256[]
            "merkleProof": [bytes.fromhex(p[2:]) for p in market['proof']] if market['proof'] else [],  # bytes32[]
            "position": 1,  # uint8
            "live": False  # bool
        }
        
        print(f"✅ Data conversion successful")
        print(f"Game ID: {test_data['gameId']}")
        print(f"Sport ID: {test_data['sportId']}")
        print(f"Odds: {test_data['odds']}")
        print(f"Merkle Proof: {test_data['merkleProof']}")
        
        # Try to build transaction (without sending)
        try:
            tx = sports_amm.functions.testTrade(
                test_data['gameId'],
                test_data['sportId'],
                test_data['typeId'],
                test_data['maturity'],
                test_data['status'],
                test_data['line'],
                test_data['playerId'],
                test_data['odds'],
                test_data['merkleProof'],
                test_data['position'],
                test_data['live']
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 500000,
                'gasPrice': int(w3.eth.gas_price * 1.1)
            })
            print(f"✅ Transaction building successful")
        except Exception as e:
            print(f"❌ Transaction building failed: {e}")
            
    except Exception as e:
        print(f"❌ Contract interaction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
