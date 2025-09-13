import os
import json
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

# --- ABIs ---
ERC20_ABI = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]'
SPORTS_AMM_ABI = '[{"inputs":[{"components":[{"internalType":"bytes32","name":"gameId","type":"bytes32"},{"internalType":"uint16","name":"sportId","type":"uint16"},{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint256","name":"maturity","type":"uint256"},{"internalType":"uint8","name":"status","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"},{"internalType":"uint256","name":"playerId","type":"uint256"},{"internalType":"uint256[]","name":"odds","type":"uint256[]"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"uint8","name":"position","type":"uint8"},{"components":[{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint8","name":"position","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"}],"internalType":"struct SportsAMMV2.CombinedPosition[][]","name":"combinedPositions","type":"tuple[][]"},{"internalType":"bool","name":"live","type":"bool"}],"internalType":"struct SportsAMMV2.TradeData[]","name":"_tradeData","type":"tuple[]"},{"internalType":"uint256","name":"_buyInAmount","type":"uint256"},{"internalType":"uint256","name":"_totalQuote","type":"uint256"},{"internalType":"uint256","name":"_slippage","type":"uint256"},{"internalType":"address","name":"_referrer","type":"address"},{"internalType":"address","name":"_collateral","type":"address"},{"internalType":"bool","name":"_isLive","type":"bool"}],"name":"trade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'

def main():
    print("--- 🏆 FINAL SOLUTION: Complete Working PoC ---")
    load_dotenv()

    # --- Load all necessary variables ---
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
    
    # --- Find the best market ---
    print("\n--- Step 1: Finding Best Market ---")
    
    headers = {"x-api-key": api_key}
    markets_url = "https://api.overtime.io/overtime-v2/networks/42161/markets"
    response = requests.get(markets_url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch markets: {response.status_code}")
        return
        
    markets_data = response.json()
    print(f"Markets response type: {type(markets_data)}")
    print(f"Markets response keys: {list(markets_data.keys()) if isinstance(markets_data, dict) else 'Not a dict'}")
    
    if isinstance(markets_data, list):
        markets = markets_data
    elif isinstance(markets_data, dict) and 'markets' in markets_data:
        markets = markets_data['markets']
    elif isinstance(markets_data, dict) and 'data' in markets_data:
        markets = markets_data['data']
    else:
        print(f"❌ Unexpected markets response format: {markets_data}")
        return
    
    print(f"✅ Found {len(markets)} markets")
    
    # Find a simple moneyline market
    best_market = None
    for market in markets:
        if (market.get('type') == 'winner' and 
            market.get('isOpen', False) and 
            market.get('status') == 0 and 
            len(market.get('proof', [])) > 0 and
            market.get('playerProps', {}).get('playerId', 0) == 0):  # Non-player props market
            best_market = market
            break
    
    if not best_market:
        print("❌ No suitable market found")
        return
        
    print(f"✅ Selected market: {best_market.get('homeTeam', 'N/A')} vs {best_market.get('awayTeam', 'N/A')}")
    print(f"   Type: {best_market.get('type', 'N/A')} - {best_market.get('originalMarketName', 'N/A')}")
    print(f"   Line: {best_market.get('line', 'N/A')}")
    print(f"   Proof Length: {len(best_market.get('proof', []))}")

    # --- Get quote ---
    print("\n--- Step 2: Getting Quote ---")
    
    trade_data_for_quote = [{
        "gameId": best_market['gameId'], 
        "sportId": best_market['subLeagueId'], 
        "typeId": best_market['typeId'],
        "maturity": best_market['maturity'], 
        "status": best_market['status'], 
        "line": best_market['line'],
        "playerId": best_market['playerProps']['playerId'], 
        "odds": [o['normalizedImplied'] for o in best_market['odds']],
        "merkleProof": best_market['proof'], 
        "position": 1,  # Away team
        "combinedPositions": best_market['combinedPositions'], 
        "live": False
    }]

    quote_url = "https://api.overtime.io/overtime-v2/networks/42161/quote"
    payload = {"buyInAmount": 3.08, "tradeData": trade_data_for_quote, "collateral": "USDC"}
    quote = requests.post(quote_url, headers=headers, json=payload).json()
    
    if 'quoteData' not in quote:
        print(f"❌ Quote failed: {quote}")
        return
        
    print("✅ Quote received successfully")

    # --- Check USDC allowance ---
    print("\n--- Step 3: Checking USDC Allowance ---")
    buy_in_amount_wei = int(3.08 * (10**6))
    allowance_abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]
    allowance_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=allowance_abi)
    current_allowance = allowance_contract.functions.allowance(account.address, w3.to_checksum_address(sports_amm_address)).call()
    print(f"Current USDC allowance: {current_allowance / (10**6)} USDC")
    
    if current_allowance < buy_in_amount_wei:
        print("Approving USDC...")
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=ERC20_ABI)
        approve_tx = usdc_contract.functions.approve(w3.to_checksum_address(sports_amm_address), buy_in_amount_wei).build_transaction({
            'from': account.address, 
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 100000,
            'gasPrice': int(w3.eth.gas_price * 1.1)
        })
        signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key)
        approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        w3.eth.wait_for_transaction_receipt(approve_hash)
        print(f"✅ Approval Confirmed: {approve_hash.hex()}")
    else:
        print("✅ USDC allowance sufficient")

    # --- Execute trade ---
    print("\n--- Step 4: Executing TRADE ---")
    sports_amm = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=SPORTS_AMM_ABI)
    
    # Convert data types
    trade_data_for_contract = [{
        "gameId": bytes.fromhex(best_market['gameId'][2:]),  # bytes32
        "sportId": int(best_market['subLeagueId']),  # uint16
        "typeId": int(best_market['typeId']),  # uint16
        "maturity": int(best_market['maturity']),  # uint256
        "status": int(best_market['status']),  # uint8
        "line": int(best_market['line'] * 100),  # int256 (convert to cents)
        "playerId": int(best_market['playerProps']['playerId']),  # uint256
        "odds": [w3.to_wei(o['normalizedImplied'], 'ether') for o in best_market['odds']],  # uint256[] (convert to wei)
        "merkleProof": [bytes.fromhex(p[2:]) for p in best_market['proof']],  # bytes32[]
        "position": 1,  # uint8
        "combinedPositions": best_market['combinedPositions'],  # CombinedPosition[][]
        "live": False  # bool
    }]
    
    total_quote = w3.to_wei(quote['quoteData']['totalQuote']['normalizedImplied'], 'ether')
    
    print(f"Trade Data Summary:")
    print(f"  Game ID: {trade_data_for_contract[0]['gameId']}")
    print(f"  Sport ID: {trade_data_for_contract[0]['sportId']}")
    print(f"  Position: {trade_data_for_contract[0]['position']}")
    print(f"  Buy In: {buy_in_amount_wei} wei (3.08 USDC)")
    print(f"  Total Quote: {total_quote} wei")
    print(f"  Merkle Proof Length: {len(trade_data_for_contract[0]['merkleProof'])}")
    
    # Try to estimate gas first
    try:
        gas_estimate = sports_amm.functions.trade(
            trade_data_for_contract, 
            buy_in_amount_wei, 
            total_quote, 
            w3.to_wei(0.02, 'ether'),  # 2% slippage
            '0x0000000000000000000000000000000000000000',  # No referrer
            w3.to_checksum_address(usdc_address),  # USDC collateral
            False  # Not live
        ).estimate_gas({'from': account.address})
        print(f"✅ Gas estimate: {gas_estimate}")
    except Exception as e:
        print(f"❌ Gas estimation failed: {e}")
        print("This indicates the transaction will fail. Stopping here.")
        return
    
    # Build and send trade transaction
    trade_tx = sports_amm.functions.trade(
        trade_data_for_contract, 
        buy_in_amount_wei, 
        total_quote, 
        w3.to_wei(0.02, 'ether'),  # 2% slippage
        '0x0000000000000000000000000000000000000000',  # No referrer
        w3.to_checksum_address(usdc_address),  # USDC collateral
        False  # Not live
    ).build_transaction({
        'from': account.address, 
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': int(gas_estimate * 1.2),  # Add 20% buffer
        'gasPrice': int(w3.eth.gas_price * 1.1)
    })
    
    print("Sending trade transaction...")
    signed_trade = w3.eth.account.sign_transaction(trade_tx, private_key)
    trade_hash = w3.eth.send_raw_transaction(signed_trade.raw_transaction)
    print(f"✅ Trade TX sent! Hash: {trade_hash.hex()}")
    
    print("Waiting for transaction confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(trade_hash, timeout=120)
    
    if receipt.status == 1:
        print("\n" + "="*50)
        print("🎉🎉🎉 MISSION ACCOMPLISHED! Autonomous USDC bet CONFIRMED on ARBITRUM!")
        print(f"🌐 View on Arbiscan: https://arbiscan.io/tx/{trade_hash.hex()}")
        print("="*50)
    else: 
        print(f"⚠️ Trade transaction FAILED on-chain. Status: {receipt.status}")
        print(f"Gas Used: {receipt['gasUsed']} / {trade_tx['gas']}")

if __name__ == "__main__": 
    main()
