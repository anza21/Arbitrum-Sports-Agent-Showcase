import os, json, time, requests
from web3 import Web3
from dotenv import load_dotenv

ERC20_ABI = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]'

def get_market_data(market_id, api_key):
    url = f"https://api.overtime.io/overtime-v2/networks/42161/markets/{market_id}"
    headers = {"x-api-key": api_key}; r = requests.get(url, headers=headers); r.raise_for_status(); return r.json()

def get_quote(trade_data, buy_in, api_key):
    url = "https://api.overtime.io/overtime-v2/networks/42161/quote"
    headers = {"x-api-key": api_key}; payload = {"buyInAmount": buy_in, "tradeData": trade_data, "collateral": "USDC"}; r = requests.post(url, headers=headers, json=payload); r.raise_for_status(); return r.json()

def main():
    print("--- 🏆 DEBUG VICTORY LAP: Starting Debug Session ---")
    load_dotenv()
    
    # Debug environment variables
    rpc_url = os.getenv('ARBITRUM_RPC_URL')
    wallet_address = os.getenv('WALLET_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    api_key = os.getenv('OVERTIME_REST_API_KEY')
    usdc_address = os.getenv('USDC_CONTRACT_ADDRESS')
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS')
    
    print(f"RPC URL: {rpc_url}")
    print(f"Wallet: {wallet_address}")
    print(f"Private Key: {private_key[:10] if private_key else 'None'}...")
    print(f"API Key: {api_key[:10] if api_key else 'None'}...")
    print(f"USDC Address: {usdc_address}")
    print(f"Sports AMM Address: {sports_amm_address}")
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)
    print(f"✅ Connected to Arbitrum. Wallet: {account.address}")
    
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    position = 1
    buy_in_amount_usd = 3.08
    
    try:
        print("\n--- Step 1: Get Quote from API ---")
        market = get_market_data(market_id, api_key)
        print(f"Market data retrieved: {market['gameId']}")
        
        trade_data_quote = [{"gameId": market['gameId'],"sportId": market['subLeagueId'],"typeId": market['typeId'],"maturity": market['maturity'],"status": market['status'],"line": market['line'],"playerId": market['playerProps']['playerId'],"odds": [o['normalizedImplied'] for o in market['odds']],"merkleProof": market['proof'],"position": position,"combinedPositions": market['combinedPositions'],"live": False}]
        
        quote = get_quote(trade_data_quote, buy_in_amount_usd, api_key)
        print(f"Quote received: {quote['quoteData']['totalQuote']['normalizedImplied']}")
        
        total_quote = w3.to_wei(quote['quoteData']['totalQuote']['normalizedImplied'], 'ether')
        buy_in_amount_wei = int(buy_in_amount_usd * (10**6))
        print(f"Total quote: {total_quote}")
        print(f"Buy in amount wei: {buy_in_amount_wei}")
        print("✅ Quote received.")

        print("\n--- Step 2: Approve USDC ---")
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=ERC20_ABI)
        
        print(f"Building approve transaction...")
        print(f"Spender: {sports_amm_address}")
        print(f"Amount: {buy_in_amount_wei}")
        print(f"From: {account.address}")
        print(f"Nonce: {w3.eth.get_transaction_count(account.address)}")
        
        # --- DEFINITIVE FIX: ADDED GAS PARAMETERS ---
        approve_tx = usdc_contract.functions.approve(sports_amm_address, buy_in_amount_wei).build_transaction({
            'from': account.address, 
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price
        })
        
        print(f"✅ Approve transaction built successfully")
        print(f"Transaction: {approve_tx}")
        
    except Exception as e: 
        print(f"🔥 AN ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__": main()
