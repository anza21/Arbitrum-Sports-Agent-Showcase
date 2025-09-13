import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 DEBUGGING TRADE DATA ---")
    
    # Load .env from the project root
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    wallet_address = os.getenv('WALLET_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    api_key = os.getenv('OVERTIME_REST_API_KEY')
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS')
    usdc_address = "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85"

    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    account = w3.eth.account.from_key(private_key)
    
    print(f"Wallet: {account.address}")
    
    # Get market data
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    url = f"https://api.overtime.io/overtime-v2/networks/10/markets/{market_id}"
    headers = {"x-api-key": api_key}
    response = requests.get(url, headers=headers)
    market = response.json()
    
    print(f"\n--- MARKET DATA ---")
    print(f"Game ID: {market.get('gameId')}")
    print(f"Sport ID: {market.get('subLeagueId')}")
    print(f"Type ID: {market.get('typeId')}")
    print(f"Line: {market.get('line')}")
    print(f"Status: {market.get('status')}")
    print(f"Maturity: {market.get('maturity')}")
    print(f"Player Props: {market.get('playerProps')}")
    print(f"Odds: {market.get('odds')}")
    print(f"Proof: {market.get('proof')}")
    print(f"Combined Positions: {market.get('combinedPositions')}")
    
    # Check if market is still active
    if market.get('status') != 0:
        print(f"\n❌ Market is not active! Status: {market.get('status')}")
        return
    
    # Get quote
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
    
    quote_url = "https://api.overtime.io/overtime-v2/networks/10/quote"
    quote_payload = {
        "buyInAmount": 3.08,
        "tradeData": trade_data_for_quote,
        "collateral": "USDC"
    }
    
    quote_response = requests.post(quote_url, headers=headers, json=quote_payload)
    if quote_response.status_code != 200:
        print(f"\n❌ Quote failed: {quote_response.status_code}")
        print(f"Response: {quote_response.text}")
        return
        
    quote_data = quote_response.json()
    print(f"\n--- QUOTE DATA ---")
    print(f"Quote: {quote_data}")
    
    # Check USDC balance
    usdc_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]'
    usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=usdc_abi)
    usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    print(f"\n--- WALLET STATUS ---")
    print(f"USDC Balance: {usdc_balance / (10**6)} USDC")
    
    if usdc_balance < 3.08 * (10**6):
        print(f"❌ Insufficient USDC balance!")
        return
    
    # Check allowance
    allowance_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]'
    allowance_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=allowance_abi)
    allowance = allowance_contract.functions.allowance(account.address, sports_amm_address).call()
    print(f"USDC Allowance: {allowance / (10**6)} USDC")
    
    if allowance < 3.08 * (10**6):
        print(f"❌ Insufficient allowance!")
        return
    
    print(f"\n✅ All checks passed! Ready for trade.")

if __name__ == "__main__":
    main()
