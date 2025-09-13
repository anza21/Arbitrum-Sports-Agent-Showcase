import os
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 CHECKING USDC CONTRACT ---")
    
    # Load .env from the project root
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    wallet_address = os.getenv('WALLET_ADDRESS')
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')
    usdc_address = os.getenv('USDC_CONTRACT_ADDRESS')

    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    
    print(f"Wallet: {wallet_address}")
    print(f"USDC Contract: {usdc_address}")
    print(f"Network: Optimism")
    
    # Try different USDC contract addresses on Optimism
    usdc_addresses = [
        "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",  # From .env
        "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",  # USDC on Optimism
        "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",  # USDT on Optimism
    ]
    
    usdc_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'
    
    for addr in usdc_addresses:
        try:
            contract = w3.eth.contract(address=w3.to_checksum_address(addr), abi=usdc_abi)
            balance = contract.functions.balanceOf(wallet_address).call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            
            print(f"\nContract: {addr}")
            print(f"Symbol: {symbol}")
            print(f"Decimals: {decimals}")
            print(f"Balance: {balance / (10**decimals)} {symbol}")
            
        except Exception as e:
            print(f"\nContract: {addr}")
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
