import os
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 💰 GETTING USDC FOR TESTING ---")
    
    # Load .env from the project root
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    wallet_address = os.getenv('WALLET_ADDRESS')
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')
    usdc_address = os.getenv('USDC_CONTRACT_ADDRESS')

    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    
    print(f"Wallet: {wallet_address}")
    
    # Check current USDC balance
    usdc_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]'
    usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=usdc_abi)
    usdc_balance = usdc_contract.functions.balanceOf(wallet_address).call()
    print(f"Current USDC Balance: {usdc_balance / (10**6)} USDC")
    
    if usdc_balance > 0:
        print("✅ We already have USDC!")
        return
    
    print("\n🔍 SEARCHING FOR USDC SOURCES...")
    
    # Check Optimism faucets
    print("\n1. Checking Optimism Faucets:")
    faucets = [
        "https://app.optimism.io/faucet",
        "https://faucet.optimism.io/",
        "https://optimism-faucet.vercel.app/"
    ]
    
    for faucet in faucets:
        print(f"   - {faucet}")
    
    print("\n2. Alternative Options:")
    print("   - Bridge USDC from Ethereum mainnet")
    print("   - Buy USDC on Optimism DEX")
    print("   - Use Optimism Gateway bridge")
    
    print("\n3. Manual Steps Required:")
    print("   - Go to https://app.optimism.io/bridge")
    print("   - Connect wallet: 0xCbAAA6b243E392D5a26C3CeF0458E735CBe1A187")
    print("   - Bridge USDC from Ethereum to Optimism")
    print("   - Or buy USDC directly on Optimism")
    
    print("\n4. For Testing Purposes:")
    print("   - Minimum needed: 3.08 USDC")
    print("   - Recommended: 10+ USDC for gas and testing")
    
    print("\n⚠️  TRADE CANNOT PROCEED WITHOUT USDC BALANCE")

if __name__ == "__main__":
    main()
