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
    print("--- 🏆 POSTMAN FINALE: Starting Definitive On-Chain USDC Betting PoC on ARBITRUM ---")
    load_dotenv()

    # --- Load all necessary variables ---
    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    wallet_address = os.getenv('WALLET_ADDRESS', '0xCbAAA6b243E392D5a26C3CeF0458E735CBe1A187')
    private_key = os.getenv('PRIVATE_KEY', '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef')
    api_key = os.getenv('OVERTIME_REST_API_KEY', 'your_api_key_here')
    usdc_address = os.getenv('USDC_CONTRACT_ADDRESS', '0xaf88d065e77c8cC2239327C5EDb3A432268e5831')
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS', '0xfb64E79A562F7250131cf528242CEB10fDC82395')

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum RPC")
        return
    
    account = w3.eth.account.from_key(private_key)
    print(f"✅ Connected to Arbitrum. Wallet: {account.address}")
    print(f"🔧 Using USDC Address: {usdc_address}")
    print(f"🔧 Using Sports AMM Address: {sports_amm_address}")
    
    # --- Live market data ---
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    position = 1
    buy_in_amount_usd = 3.08

    try:
        # === STEP 1: GET MARKET & QUOTE (Code inspired by POSTMAN) ===
        print("\n--- Step 1: Fetching Quote from Overtime API ---")
        
        market_url = f"https://api.overtime.io/overtime-v2/networks/42161/markets/{market_id}"
        headers = {"x-api-key": api_key}
        market = requests.get(market_url, headers=headers).json()
        
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

        # === STEP 2: APPROVE USDC ===
        print("\n--- Step 2: Approving USDC for Trade ---")
        buy_in_amount_wei = int(buy_in_amount_usd * (10**6))
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=ERC20_ABI)
        approve_tx = usdc_contract.functions.approve(w3.to_checksum_address(sports_amm_address), buy_in_amount_wei).build_transaction({
            'from': account.address, 
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price
        })
        signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key); approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        w3.eth.wait_for_transaction_receipt(approve_hash)
        print(f"✅ Approval Confirmed: {approve_hash.hex()}")
        time.sleep(15)

        # === STEP 3: EXECUTE TRADE WITH QUOTE DATA ===
        print("\n--- Step 3: Executing TRADE on Arbitrum ---")
        sports_amm = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=SPORTS_AMM_ABI)
        
        trade_data_for_contract = [{"gameId": market['gameId'],"sportId": market['subLeagueId'],"typeId": market['typeId'],"maturity": market['maturity'],"status": market['status'],"line": int(market['line'] * 100),"playerId": market['playerProps']['playerId'],"odds": [w3.to_wei(o['normalizedImplied'], 'ether') for o in market['odds']],"merkleProof": market['proof'],"position": position,"combinedPositions": market['combinedPositions'],"live": False}]
        total_quote = w3.to_wei(quote['quoteData']['totalQuote']['normalizedImplied'], 'ether')
        
        trade_tx = sports_amm.functions.trade(
            trade_data_for_contract, buy_in_amount_wei, total_quote, 
            w3.to_wei(0.02, 'ether'), '0x0000000000000000000000000000000000000000', 
            w3.to_checksum_address(usdc_address), False
        ).build_transaction({
            'from': account.address, 
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 500000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_trade = w3.eth.account.sign_transaction(trade_tx, private_key); trade_hash = w3.eth.send_raw_transaction(signed_trade.raw_transaction)
        print(f"✅ Trade TX sent! Hash: {trade_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(trade_hash, timeout=120)
        
        if receipt.status == 1:
            print("\n" + "="*50); print("🎉🎉🎉 MISSION ACCOMPLISHED! Autonomous USDC bet CONFIRMED on ARBITRUM!"); print(f"🌐 View on Arbiscan: https://arbiscan.io/tx/{trade_hash.hex()}"); print("="*50)
        else: print(f"⚠️ Trade transaction FAILED on-chain. Status: {receipt.status}")

    except Exception as e: print(f"🔥 AN ERROR OCCURRED: {e}")

if __name__ == "__main__": main()
