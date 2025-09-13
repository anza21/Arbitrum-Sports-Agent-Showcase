import os
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 TESTING CORRECT USDC CONTRACT ---")
    
    # Load .env from the project root
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    wallet_address = os.getenv('WALLET_ADDRESS')
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')

    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    
    print(f"Wallet: {wallet_address}")
    
    # The correct USDC.e contract address on Optimism
    usdc_address = "0x7F5c764cBc14f9669B88837ca1490cCa17c31607"
    
    usdc_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'
    
    try:
        contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=usdc_abi)
        balance = contract.functions.balanceOf(wallet_address).call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        
        print(f"\nContract: {usdc_address}")
        print(f"Symbol: {symbol}")
        print(f"Decimals: {decimals}")
        print(f"Balance: {balance / (10**decimals)} {symbol}")
        
        if balance > 0:
            print("✅ USDC balance found!")
            print(f"Available for betting: {balance / (10**decimals)} {symbol}")
        else:
            print("❌ No USDC balance found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    # Also check ETH balance
    eth_balance = w3.eth.get_balance(wallet_address)
    print(f"\nETH Balance: {w3.from_wei(eth_balance, 'ether')} ETH")
    
    if eth_balance < w3.to_wei(0.001, 'ether'):
        print("⚠️ Low ETH balance - may not be enough for gas")
    else:
        print("✅ ETH balance sufficient for gas")

if __name__ == "__main__":
    main()
