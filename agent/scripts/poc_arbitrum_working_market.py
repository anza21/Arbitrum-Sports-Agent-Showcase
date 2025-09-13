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
    print("--- 🏆 WORKING MARKET: Using Active Market with Valid Merkle Proof ---")
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
    
    # --- Use a working market from the API response ---
    # This market has valid merkle proof and is active
    market_id = "0x3230323530393133343938323534463400000000000000000000000000000000"
    position = 1  # Away team
    buy_in_amount_usd = 3.08

    try:
        # === STEP 1: GET MARKET & QUOTE ===
        print("\n--- Step 1: Fetching Quote from Overtime API ---")
        
        market_url = f"https://api.overtime.io/overtime-v2/networks/42161/markets/{market_id}"
        headers = {"x-api-key": api_key}
        market = requests.get(market_url, headers=headers).json()
        
        print(f"Market Details:")
        print(f"  Game: {market.get('homeTeam', 'N/A')} vs {market.get('awayTeam', 'N/A')}")
        print(f"  Type: {market.get('type', 'N/A')} - {market.get('originalMarketName', 'N/A')}")
        print(f"  Line: {market.get('line', 'N/A')}")
        print(f"  Status: {market.get('status', 'N/A')}")
        print(f"  Odds Count: {len(market.get('odds', []))}")
        print(f"  Proof Length: {len(market.get('proof', []))}")
        
        trade_data_for_quote = [{
            "gameId": market['gameId'], "sportId": market['subLeagueId'], "typeId": market['typeId'],
            "maturity": market['maturity'], "status": market['status'], "line": market['line'],
            "playerId": market['playerProps']['playerId'], "odds": [o['normalizedImplied'] for o in market['odds']],
            "merkleProof": market['proof'], "position": position,
            "combinedPositions": market['combinedPositions'], "live": False
        }]

        quote_url = "https://api.overtime.io/overtime-v2/networks/42161/quote"
        payload = {"buyInAmount": buy_in_amount_usd, "tradeData": trade_data_for_quote, "collateral": "USDC"}
        quote = requests.post(quote_url, headers=headers, json=payload).json()
        print("✅ Quote received successfully.")

        # === STEP 2: CHECK USDC ALLOWANCE ===
        print("\n--- Step 2: Checking USDC Allowance ---")
        buy_in_amount_wei = int(buy_in_amount_usd * (10**6))
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

        # === STEP 3: EXECUTE TRADE WITH WORKING MARKET ===
        print("\n--- Step 3: Executing TRADE with Working Market ---")
        sports_amm = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=SPORTS_AMM_ABI)
        
        # Convert data types - using the working market data
        trade_data_for_contract = [{
            "gameId": bytes.fromhex(market['gameId'][2:]),  # bytes32
            "sportId": int(market['subLeagueId']),  # uint16
            "typeId": int(market['typeId']),  # uint16
            "maturity": int(market['maturity']),  # uint256
            "status": int(market['status']),  # uint8
            "line": int(market['line'] * 100),  # int256 (convert to cents)
            "playerId": int(market['playerProps']['playerId']),  # uint256
            "odds": [w3.to_wei(o['normalizedImplied'], 'ether') for o in market['odds']],  # uint256[] (convert to wei)
            "merkleProof": [bytes.fromhex(p[2:]) for p in market['proof']],  # bytes32[] - NOW HAS VALID PROOF!
            "position": int(position),  # uint8
            "combinedPositions": market['combinedPositions'],  # CombinedPosition[][]
            "live": False  # bool
        }]
        
        total_quote = w3.to_wei(quote['quoteData']['totalQuote']['normalizedImplied'], 'ether')
        
        print(f"Trade Data Summary:")
        print(f"  Game ID: {trade_data_for_contract[0]['gameId']}")
        print(f"  Sport ID: {trade_data_for_contract[0]['sportId']}")
        print(f"  Position: {trade_data_for_contract[0]['position']}")
        print(f"  Buy In: {buy_in_amount_wei} wei ({buy_in_amount_usd} USDC)")
        print(f"  Total Quote: {total_quote} wei")
        print(f"  Merkle Proof Length: {len(trade_data_for_contract[0]['merkleProof'])}")
        print(f"  Merkle Proof: {[p.hex() for p in trade_data_for_contract[0]['merkleProof'][:3]]}...")  # Show first 3
        
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

    except Exception as e: 
        print(f"🔥 AN ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__": 
    main()
