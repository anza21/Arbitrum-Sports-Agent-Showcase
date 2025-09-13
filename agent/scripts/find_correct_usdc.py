import os
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 FINDING CORRECT USDC CONTRACT ---")
    
    load_dotenv(os.path.join('.', '.env'))
    wallet_address = os.getenv('WALLET_ADDRESS')
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')

    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    
    print(f"Wallet: {wallet_address}")
    print(f"Expected USDC Balance: 11.997371 USDC")
    
    # Common USDC contract addresses on Optimism
    usdc_contracts = [
        "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",  # USDC.e (bridged)
        "0x81C9A7B55A4df39A9B7B5F781ec0e53539694873",  # Native USDC
        "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",  # Another USDC
        "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",  # USDT
    ]
    
    usdc_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'
    
    for contract_addr in usdc_contracts:
        try:
            contract = w3.eth.contract(address=w3.to_checksum_address(contract_addr), abi=usdc_abi)
            balance = contract.functions.balanceOf(wallet_address).call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            
            balance_formatted = balance / (10**decimals)
            
            print(f"\nContract: {contract_addr}")
            print(f"Symbol: {symbol}")
            print(f"Decimals: {decimals}")
            print(f"Balance: {balance_formatted} {symbol}")
            
            if abs(balance_formatted - 11.997371) < 0.001:
                print(f"✅ MATCH FOUND! This is the correct USDC contract!")
                print(f"Use this address: {contract_addr}")
                return contract_addr
                
        except Exception as e:
            print(f"\nContract {contract_addr}: Error - {e}")
    
    print("\n❌ No matching USDC contract found")
    return None

if __name__ == "__main__":
    main()
