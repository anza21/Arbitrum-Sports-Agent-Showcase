import os
from web3 import Web3
from dotenv import load_dotenv

def verify_balance():
    """A simple, isolated script to test ETH balance fetching."""
    print("--- 🔬 Starting ETH Balance Verification Script ---")

    # Load .env file from the project root
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Attempting to load .env from: {dotenv_path}")

    rpc_url = os.getenv('ARBITRUM_RPC_URL')
    wallet_address = os.getenv('WALLET_ADDRESS')

    print(f"Read RPC URL: {'OK' if rpc_url else 'FAILED'}")
    print(f"Read Wallet Address: {'OK' if wallet_address else 'FAILED'}")

    if not rpc_url or not wallet_address:
        print("❌ CRITICAL FAILURE: Could not read ARBITRUM_RPC_URL or WALLET_ADDRESS from .env file.")
        return

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print(f"❌ CONNECTION FAILURE: Could not connect to RPC URL: {rpc_url}")
            return
        
        print("✅ Successfully connected to Arbitrum network.")
        
        checksum_address = w3.to_checksum_address(wallet_address)
        print(f"Checking balance for address: {checksum_address}")

        raw_balance = w3.eth.get_balance(checksum_address)
        eth_balance = w3.from_wei(raw_balance, 'ether')

        print("\n" + "="*50)
        print(f"🎉 SUCCESS! Live ETH Balance: {eth_balance:.8f} ETH")
        print("="*50)

    except Exception as e:
        print("\n" + "="*50)
        print(f"🔥 AN ERROR OCCURRED: {e}")
        print("="*50)

if __name__ == "__main__":
    verify_balance()
