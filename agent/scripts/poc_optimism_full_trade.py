import os
import json
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

# --- ABIs ---
ERC20_ABI = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]'
SPORTS_AMM_ABI = '[{"inputs":[{"components":[{"internalType":"bytes32","name":"gameId","type":"bytes32"},{"internalType":"uint16","name":"sportId","type":"uint16"},{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint256","name":"maturity","type":"uint256"},{"internalType":"uint8","name":"status","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"},{"internalType":"uint256","name":"playerId","type":"uint256"},{"internalType":"uint256[]","name":"odds","type":"uint256[]"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"uint8","name":"position","type":"uint8"},{"components":[{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint8","name":"position","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"}],"internalType":"struct SportsAMMV2.CombinedPosition[][]","name":"combinedPositions","type":"tuple[][]"},{"internalType":"bool","name":"live","type":"bool"}],"internalType":"struct SportsAMMV2.TradeData[]","name":"_tradeData","type":"tuple[]"},{"internalType":"uint256","name":"_buyInAmount","type":"uint256"},{"internalType":"uint256","name":"_totalQuote","type":"uint256"},{"internalType":"uint256","name":"_slippage","type":"uint256"},{"internalType":"address","name":"_referrer","type":"address"},{"internalType":"address","name":"_collateral","type":"address"},{"internalType":"bool","name":"_isLive","type":"bool"}],"name":"trade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'

def get_market_data(market_id, api_key):
    url = f"https://api.overtime.io/overtime-v2/networks/10/markets/{market_id}"
    headers = {"x-api-key": api_key}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_quote(trade_data_for_quote, buy_in, api_key):
    url = "https://api.overtime.io/overtime-v2/networks/10/quote"
    headers = {"x-api-key": api_key}
    payload = {
        "buyInAmount": buy_in,
        "tradeData": trade_data_for_quote,
        "collateral": "USDC"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def main():
    print("--- 🔥 TRUE FINALE v2: Starting Quote-to-Trade PoC on OPTIMISM ---")

    # Load .env from the project root
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    wallet_address = os.getenv('WALLET_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    api_key = os.getenv('OVERTIME_REST_API_KEY')
    
    # Using verified Optimism addresses
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS')
    # Use the correct USDC contract address for Optimism (found the actual one!)
    usdc_address = "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85"  # Correct USDC on Optimism
    
    # Debug: Print environment variables
    print(f"Wallet Address: {wallet_address}")
    print(f"USDC Address: {usdc_address}")
    print(f"Sports AMM Address: {sports_amm_address}")
    print(f"API Key: {api_key[:10]}..." if api_key else "API Key: None")

    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    account = w3.eth.account.from_key(private_key)
    print(f"✅ Connected to Optimism. Using Wallet: {account.address}")

    # --- LIVE BET PARAMETERS (Provided by Role +) ---
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    position = 1  # Away
    buy_in_amount_usd = 3.08
    
    try:
        # --- STEP 1: GET MARKET & QUOTE FROM API ---
        print("\n--- Step 1: Fetching Market Data and Quote from Overtime API ---")
        market = get_market_data(market_id, api_key)
        
        trade_data_for_quote = [{
            "gameId": market['gameId'], "sportId": market['subLeagueId'], "typeId": market['typeId'],
            "maturity": market['maturity'], "status": market['status'], "line": market['line'],
            "playerId": market['playerProps']['playerId'], "odds": [o['normalizedImplied'] for o in market['odds']],
            "merkleProof": market['proof'], "position": position,
            "combinedPositions": market['combinedPositions'], "live": False
        }]

        quote = get_quote(trade_data_for_quote, buy_in_amount_usd, api_key)
        print("✅ Quote received successfully.")
        total_quote = w3.to_wei(quote['quoteData']['totalQuote']['normalizedImplied'], 'ether')
        buy_in_amount_wei = int(buy_in_amount_usd * (10**6))

        # --- STEP 2: APPROVE ---
        print("\n--- Step 2: Approving USDC for Trade ---")
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=ERC20_ABI)
        
        # Get current gas price
        try:
            gas_price = w3.eth.gas_price
            print(f"Current gas price: {gas_price} wei")
        except Exception as e:
            print(f"Error getting gas price: {e}")
            gas_price = w3.to_wei('0.001', 'gwei')  # Fallback gas price for Optimism
            print(f"Using fallback gas price: {gas_price} wei")
        
        approve_tx = usdc_contract.functions.approve(sports_amm_address, buy_in_amount_wei).build_transaction({
            'from': account.address, 
            'nonce': w3.eth.get_transaction_count(account.address), 
            'gas': 100000, 
            'gasPrice': gas_price
        })
        signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
        approve_tx_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
        print(f"✅ Approve TX sent: {approve_tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(approve_tx_hash)
        print("✅ Approval confirmed!")
        print("⏳ Waiting 5 seconds before trade...")
        time.sleep(5)

        # --- STEP 3: TRADE ---
        print("\n--- Step 3: Executing TRADE on Optimism with Quote Data ---")
        sports_amm_contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=SPORTS_AMM_ABI)
        print("✅ Sports AMM contract initialized")
        
        # Reconstruct trade data with correct wei formatting for the contract
        print("🔧 Building trade data...")
        trade_data_for_contract = [{
            'gameId': market['gameId'], 'sportId': market['subLeagueId'], 'typeId': market['typeId'],
            'maturity': market['maturity'], 'status': market['status'], 'line': int(market['line'] * 100),
            'playerId': market['playerProps']['playerId'], 'odds': [w3.to_wei(o['normalizedImplied'], 'ether') for o in market['odds']],
            'merkleProof': market['proof'], 'position': position, 'combinedPositions': market['combinedPositions'], 'live': False
        }]
        print("✅ Trade data constructed")

        print("🔧 Building trade transaction...")
        trade_tx = sports_amm_contract.functions.trade(
            trade_data_for_contract,
            buy_in_amount_wei,
            total_quote,
            w3.to_wei(0.02, 'ether'), # Slippage
            '0x0000000000000000000000000000000000000000', # Referrer
            w3.to_checksum_address(usdc_address), # Collateral
            False # isLive
        ).build_transaction({
            'from': account.address, 
            'nonce': w3.eth.get_transaction_count(account.address), 
            'gas': 2000000, 
            'gasPrice': gas_price
        })
        print("✅ Trade transaction built")

        signed_trade_tx = w3.eth.account.sign_transaction(trade_tx, private_key)
        trade_tx_hash = w3.eth.send_raw_transaction(signed_trade_tx.raw_transaction)
        print(f"✅ Trade TX sent! Hash: {trade_tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(trade_tx_hash, timeout=120)
        
        if receipt.status == 1:
            print("\n" + "="*50)
            print("🎉🎉🎉 MISSION ACCOMPLISHED! Autonomous USDC bet CONFIRMED!")
            print(f"🌐 View on Etherscan: https://optimistic.etherscan.io/tx/{trade_tx_hash.hex()}")
            print("="*50)
        else:
            print(f"⚠️ Trade transaction FAILED on-chain. Status: {receipt.status}")

    except Exception as e:
        print(f"🔥 AN ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
