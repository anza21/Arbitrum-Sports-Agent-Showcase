import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 DEBUGGING TRADE FAILURE ---")
    
    # Load .env from the project root
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    wallet_address = os.getenv('WALLET_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    api_key = os.getenv('OVERTIME_REST_API_KEY')
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS')
    usdc_address = os.getenv('USDC_CONTRACT_ADDRESS')

    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    account = w3.eth.account.from_key(private_key)
    
    print(f"Wallet: {account.address}")
    
    # Check ETH balance
    eth_balance = w3.eth.get_balance(account.address)
    print(f"ETH Balance: {w3.from_wei(eth_balance, 'ether')} ETH")
    
    # Check USDC balance
    usdc_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]'
    usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=usdc_abi)
    usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    print(f"USDC Balance: {usdc_balance / (10**6)} USDC")
    
    # Check USDC allowance
    allowance_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]'
    allowance_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=allowance_abi)
    allowance = allowance_contract.functions.allowance(account.address, sports_amm_address).call()
    print(f"USDC Allowance: {allowance / (10**6)} USDC")
    
    # Get market data to check structure
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    url = f"https://api.overtime.io/overtime-v2/networks/10/markets/{market_id}"
    headers = {"x-api-key": api_key}
    response = requests.get(url, headers=headers)
    market = response.json()
    
    print("\n--- MARKET DATA STRUCTURE ---")
    print(f"Game ID: {market.get('gameId')}")
    print(f"Sport ID: {market.get('subLeagueId')}")
    print(f"Type ID: {market.get('typeId')}")
    print(f"Line: {market.get('line')}")
    print(f"Status: {market.get('status')}")
    print(f"Player Props: {market.get('playerProps', {}).get('playerId')}")
    print(f"Odds: {[o.get('normalizedImplied') for o in market.get('odds', [])]}")
    print(f"Proof: {market.get('proof')}")
    print(f"Combined Positions: {market.get('combinedPositions')}")

if __name__ == "__main__":
    main()
