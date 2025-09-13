import os
import sys
import json
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.contracts.overtime_abi import OVERTIME_SPORTS_AMM_ABI

def main():
    print("--- 🚀 Starting Direct On-Chain ETH Betting PoC ---")

    # 1. Load Environment Variables from .env
    rpc_url = os.getenv('ARBITRUM_RPC_URL')
    wallet_address = os.getenv('WALLET_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    contract_address = os.getenv('OVERTIME_CONTRACT')

    if not all([rpc_url, wallet_address, private_key, contract_address]):
        print("❌ ERROR: Ensure ARBITRUM_RPC_URL, WALLET_ADDRESS, PRIVATE_KEY, and OVERTIME_CONTRACT are set.")
        return

    # 2. Initialize Web3 Connection
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("❌ ERROR: Failed to connect to Arbitrum network.")
        return
    print(f"✅ Connected to Arbitrum. Chain ID: {w3.eth.chain_id}")
    print(f"👤 Using Wallet: {wallet_address}")

    # 3. Load Contract
    sports_amm_contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=OVERTIME_SPORTS_AMM_ABI)
    
    # 4. Define Bet Parameters (using a real, open market for testing)
    # This is a placeholder market - in a real scenario, we'd fetch an open one.
    market_id = '0x53504f5254535f414d4d5f746f5f5265736f6c76655f4d41524b45545f323034' # Example Market ID
    position = 0  # 0 for Home
    bet_amount_in_eth = 0.0001
    bet_amount_in_wei = w3.to_wei(bet_amount_in_eth, 'ether')
    
    print(f"🎯 Preparing to bet {bet_amount_in_eth} ETH on market '{market_id}', position {position}")

    try:
        # 5. Build the Transaction
        # Using the buyFromAMM function which is payable and accepts ETH
        tx = sports_amm_contract.functions.buyFromAMM(
            w3.to_bytes(hexstr=market_id),
            position,
            bet_amount_in_wei
        ).build_transaction({
            'from': wallet_address,
            'value': bet_amount_in_wei,
            'nonce': w3.eth.get_transaction_count(wallet_address),
            'gas': 1000000, # Set a reasonable gas limit
            'maxFeePerGas': w3.to_wei('0.2', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('0.1', 'gwei'),
        })

        # 6. Sign the Transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)

        # 7. Send the Transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"✅ SUCCESS: Transaction sent!")
        print(f"🔗 Transaction Hash: {tx_hash.hex()}")
        print(f"🌐 View on Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
        
        # 8. Wait for the transaction receipt (optional but good practice)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("✅ Transaction confirmed successfully!")
        else:
            print("⚠️ Transaction failed after being sent.")

    except Exception as e:
        print(f"❌ ERROR: Failed to send transaction: {e}")
        print("--- PoC Failed. Check wallet balance, market validity, and .env configuration. ---")

if __name__ == "__main__":
    main()
