import os
import json
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🏆 CORRECT STRUCTURE: Using Overtime Dev's Structure ---")
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
    
    # --- Get market data ---
    print("\n--- Step 1: Getting Market Data ---")
    
    market_id = "0x3230323530393133343938323534463400000000000000000000000000000000"
    market_url = f"https://api.overtime.io/overtime-v2/networks/42161/markets/{market_id}"
    headers = {"x-api-key": api_key}
    market = requests.get(market_url, headers=headers).json()
    
    print(f"Market: {market.get('homeTeam', 'N/A')} vs {market.get('awayTeam', 'N/A')}")
    print(f"Type: {market.get('type', 'N/A')} - {market.get('originalMarketName', 'N/A')}")
    print(f"Line: {market.get('line', 'N/A')}")
    print(f"Status: {market.get('status', 'N/A')}")
    print(f"Proof Length: {len(market.get('proof', []))}")

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
        "position": 1,  # Away team
        "combinedPositions": market['combinedPositions'], 
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

    # --- Execute trade with CORRECT structure from Overtime dev ---
    print("\n--- Step 4: Executing TRADE with Correct Structure ---")
    
    # Use the CORRECT ABI structure from the Overtime dev
    correct_abi = '[{"inputs":[{"internalType":"address","name":"_collateral","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"},{"internalType":"uint256[]","name":"_marketIds","type":"uint256[]"},{"internalType":"uint8[]","name":"_positions","type":"uint8[]"},{"internalType":"uint256[]","name":"_oddsInWei","type":"uint256[]"},{"internalType":"bytes32[][]","name":"_merkleProofs","type":"bytes32[][]"},{"internalType":"address","name":"_referrer","type":"address"}],"name":"trade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
    
    sports_amm = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=correct_abi)
    
    # Prepare trade data according to Overtime dev's structure
    collateral = w3.to_checksum_address(usdc_address)
    amount = buy_in_amount_wei  # 3.08 USDC in wei
    market_ids = [int(market['gameId'], 16)]  # Convert hex to int
    positions = [1]  # Away team
    odds_in_wei = [w3.to_wei(o['normalizedImplied'], 'ether') for o in market['odds']]  # Convert to 18-decimal wei
    merkle_proofs = [[w3.to_bytes(hexstr=p) for p in market['proof']]]  # Convert hex strings to bytes
    referrer = "0x0000000000000000000000000000000000000000"
    
    print(f"Trade Parameters:")
    print(f"  Collateral: {collateral}")
    print(f"  Amount: {amount} wei ({amount / (10**6)} USDC)")
    print(f"  Market IDs: {market_ids}")
    print(f"  Positions: {positions}")
    print(f"  Odds in Wei: {odds_in_wei}")
    print(f"  Merkle Proofs: {len(merkle_proofs[0])} proofs")
    print(f"  Referrer: {referrer}")
    
    # Try to estimate gas first
    try:
        gas_estimate = sports_amm.functions.trade(
            collateral,
            amount,
            market_ids,
            positions,
            odds_in_wei,
            merkle_proofs,
            referrer
        ).estimate_gas({'from': account.address})
        print(f"✅ Gas estimate: {gas_estimate}")
    except Exception as e:
        print(f"❌ Gas estimation failed: {e}")
        print("This indicates the transaction will fail. Stopping here.")
        return
    
    # Build and send trade transaction
    trade_tx = sports_amm.functions.trade(
        collateral,
        amount,
        market_ids,
        positions,
        odds_in_wei,
        merkle_proofs,
        referrer
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
