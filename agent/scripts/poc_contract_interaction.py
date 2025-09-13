import os
import json
from web3 import Web3

def main():
    """
    A Proof-of-Concept script to verify read-only interaction
    with the Overtime Sports AMM smart contract on Arbitrum.
    """
    print("--- 🚀 Starting Smart Contract Interaction PoC ---")

    # 1. Load Environment Variables
    rpc_url = os.getenv('ARBITRUM_RPC_URL')
    contract_address = os.getenv('OVERTIME_CONTRACT')

    if not rpc_url or not contract_address:
        print("❌ ERROR: ARBITRUM_RPC_URL and OVERTIME_CONTRACT must be set in .env file.")
        return

    print(f"🔗 RPC URL: {rpc_url}")
    print(f"📜 Contract Address: {contract_address}")

    # 2. Initialize Web3 Connection
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("❌ ERROR: Failed to connect to Arbitrum network via RPC.")
            return
        print(f"✅ Successfully connected to Arbitrum. Chain ID: {w3.eth.chain_id}")
    except Exception as e:
        print(f"❌ ERROR: Could not initialize Web3 connection: {e}")
        return

    # 3. Load Minimal ABI for a simple read function
    # We will use the 'name' function which is standard for ERC20 tokens
    minimal_abi = '[{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]'
    
    # 4. Interact with the Smart Contract
    try:
        sports_amm_contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=minimal_abi)
        
        print("\n📞 Calling 'name()' read-only function on the contract...")
        token_name = sports_amm_contract.functions.name().call()
        
        print(f"✅ SUCCESS! Contract returned token name: {token_name}")
        print("\n--- PoC Successful: We can connect and read from the contract. ---")

    except Exception as e:
        print(f"❌ ERROR: Failed to interact with the smart contract: {e}")
        print("--- PoC Failed: Could not read from the contract. ---")

if __name__ == "__main__":
    main()