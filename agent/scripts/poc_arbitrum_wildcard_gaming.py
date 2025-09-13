import os
import json
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🏆 WILDCARD GAMING: Using Confirmed Open Market ---")
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
    
    # --- Use the confirmed open market from Overtime Markets ---
    print("\n--- Step 1: Getting Wildcard Gaming Market Data ---")
    
    # Market ID from the Overtime Markets URL
    market_id = "0x3230323530393133434435303638414400000000000000000000000000000000"
    market_url = f"https://api.overtime.io/overtime-v2/networks/42161/markets/{market_id}"
    headers = {"x-api-key": api_key}
    
    try:
        market = requests.get(market_url, headers=headers).json()
        print(f"✅ Market data received")
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
        
        # Check if market is tradeable
        if not market.get('isOpen', False):
            print("❌ Market is not open")
            return
        if market.get('isResolved', False):
            print("❌ Market is already resolved")
            return
        if market.get('isCancelled', False):
            print("❌ Market is cancelled")
            return
        if market.get('isPaused', False):
            print("❌ Market is paused")
            return
        if len(market.get('proof', [])) == 0:
            print("❌ No merkle proof available")
            return
            
        print("✅ Market is tradeable!")
        
    except Exception as e:
        print(f"❌ Failed to get market data: {e}")
        return

    # --- Get quote ---
    print("\n--- Step 2: Getting Quote ---")
    
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
        "position": 1,  # Away team (Oxygen Esports)
        "combinedPositions": market['combinedPositions'], 
        "live": False
    }]

    quote_url = "https://api.overtime.io/overtime-v2/networks/42161/quote"
    payload = {"buyInAmount": 3.08, "tradeData": trade_data_for_quote, "collateral": "USDC"}
    
    try:
        quote = requests.post(quote_url, headers=headers, json=payload).json()
        
        if 'quoteData' not in quote:
            print(f"❌ Quote failed: {quote}")
            return
            
        print("✅ Quote received successfully")
        print(f"Quote Data: {quote['quoteData']}")
        
    except Exception as e:
        print(f"❌ Quote request failed: {e}")
        return

    # --- Check USDC allowance ---
    print("\n--- Step 3: Checking USDC Allowance ---")
    buy_in_amount_wei = int(3.08 * (10**6))
    allowance_abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]
    allowance_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=allowance_abi)
    current_allowance = allowance_contract.functions.allowance(account.address, w3.to_checksum_address(sports_amm_address)).call()
    print(f"Current USDC allowance: {current_allowance / (10**6)} USDC")
    
    if current_allowance < buy_in_amount_wei:
        print("Approving USDC...")
        usdc_abi = [{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=usdc_abi)
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

    # --- Execute trade with BOTH ABI versions ---
    print("\n--- Step 4: Testing Both ABI Versions ---")
    
    # ABI Version 1: Our original structure
    abi_v1 = '[{"inputs":[{"components":[{"internalType":"bytes32","name":"gameId","type":"bytes32"},{"internalType":"uint16","name":"sportId","type":"uint16"},{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint256","name":"maturity","type":"uint256"},{"internalType":"uint8","name":"status","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"},{"internalType":"uint256","name":"playerId","type":"uint256"},{"internalType":"uint256[]","name":"odds","type":"uint256[]"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"uint8","name":"position","type":"uint8"},{"components":[{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint8","name":"position","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"}],"internalType":"struct SportsAMMV2.CombinedPosition[][]","name":"combinedPositions","type":"tuple[][]"},{"internalType":"bool","name":"live","type":"bool"}],"internalType":"struct SportsAMMV2.TradeData[]","name":"_tradeData","type":"tuple[]"},{"internalType":"uint256","name":"_buyInAmount","type":"uint256"},{"internalType":"uint256","name":"_totalQuote","type":"uint256"},{"internalType":"uint256","name":"_slippage","type":"uint256"},{"internalType":"address","name":"_referrer","type":"address"},{"internalType":"address","name":"_collateral","type":"address"},{"internalType":"bool","name":"_isLive","type":"bool"}],"name":"trade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
    
    # ABI Version 2: Overtime dev's structure
    abi_v2 = '[{"inputs":[{"internalType":"address","name":"_collateral","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"},{"internalType":"uint256[]","name":"_marketIds","type":"uint256[]"},{"internalType":"uint8[]","name":"_positions","type":"uint8[]"},{"internalType":"uint256[]","name":"_oddsInWei","type":"uint256[]"},{"internalType":"bytes32[][]","name":"_merkleProofs","type":"bytes32[][]"},{"internalType":"address","name":"_referrer","type":"address"}],"name":"trade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
    
    for i, abi in enumerate([abi_v1, abi_v2], 1):
        print(f"\n--- Testing ABI Version {i} ---")
        try:
            sports_amm = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=abi)
            
            if i == 1:  # ABI Version 1
                # Convert data types for ABI v1
                trade_data_for_contract = [{
                    "gameId": bytes.fromhex(market['gameId'][2:]),  # bytes32
                    "sportId": int(market['subLeagueId']),  # uint16
                    "typeId": int(market['typeId']),  # uint16
                    "maturity": int(market['maturity']),  # uint256
                    "status": int(market['status']),  # uint8
                    "line": int(market['line'] * 100),  # int256 (convert to cents)
                    "playerId": int(market['playerProps']['playerId']),  # uint256
                    "odds": [w3.to_wei(o['normalizedImplied'], 'ether') for o in market['odds']],  # uint256[] (convert to wei)
                    "merkleProof": [bytes.fromhex(p[2:]) for p in market['proof']],  # bytes32[]
                    "position": 1,  # uint8
                    "combinedPositions": market['combinedPositions'],  # CombinedPosition[][]
                    "live": False  # bool
                }]
                
                total_quote = w3.to_wei(quote['quoteData']['totalQuote']['normalizedImplied'], 'ether')
                
                # Try gas estimation
                gas_estimate = sports_amm.functions.trade(
                    trade_data_for_contract, 
                    buy_in_amount_wei, 
                    total_quote, 
                    w3.to_wei(0.02, 'ether'),  # 2% slippage
                    '0x0000000000000000000000000000000000000000',  # No referrer
                    w3.to_checksum_address(usdc_address),  # USDC collateral
                    False  # Not live
                ).estimate_gas({'from': account.address})
                
                print(f"✅ ABI Version {i}: Gas estimate successful: {gas_estimate}")
                
            else:  # ABI Version 2
                # Prepare data for ABI v2
                collateral = w3.to_checksum_address(usdc_address)
                amount = buy_in_amount_wei
                market_ids = [int(market['gameId'], 16)]  # Convert hex to int
                positions = [1]  # Away team
                odds_in_wei = [w3.to_wei(o['normalizedImplied'], 'ether') for o in market['odds']]
                merkle_proofs = [[w3.to_bytes(hexstr=p) for p in market['proof']]]
                referrer = "0x0000000000000000000000000000000000000000"
                
                # Try gas estimation
                gas_estimate = sports_amm.functions.trade(
                    collateral,
                    amount,
                    market_ids,
                    positions,
                    odds_in_wei,
                    merkle_proofs,
                    referrer
                ).estimate_gas({'from': account.address})
                
                print(f"✅ ABI Version {i}: Gas estimate successful: {gas_estimate}")
                
        except Exception as e:
            print(f"❌ ABI Version {i}: Gas estimation failed: {e}")
            continue
    
    print(f"\n--- Summary ---")
    print(f"Market: {market.get('homeTeam', 'N/A')} vs {market.get('awayTeam', 'N/A')}")
    print(f"Market ID: {market_id}")
    print(f"Status: {market.get('status', 'N/A')}")
    print(f"Is Open: {market.get('isOpen', 'N/A')}")
    print(f"Proof Length: {len(market.get('proof', []))}")

if __name__ == "__main__": 
    main()
