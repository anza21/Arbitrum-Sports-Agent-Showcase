import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv
import sys
sys.path.append('/home/anza/project/superior-agents-clean/superior-agent-v1')
from agent.src.contracts.overtime_abi import OVERTIME_SPORTS_AMM_ABI

# --- MINIMAL ERC20 ABI FOR APPROVE ---
ERC20_ABI = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]'

def main():
    print("--- 🚀 Starting Direct On-Chain USDC Betting PoC ---")

    # 1. Load Environment Variables
    load_dotenv()
    rpc_url = os.getenv('ARBITRUM_RPC_URL')
    wallet_address = os.getenv('WALLET_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS')
    usdc_address = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831" # Official USDC on Arbitrum

    if not all([rpc_url, wallet_address, private_key, sports_amm_address]):
        print("❌ ERROR: Ensure all required .env variables are set.")
        return

    # 2. Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    print(f"✅ Connected to Arbitrum. Chain ID: {w3.eth.chain_id}")
    account = w3.eth.account.from_key(private_key)
    print(f"👤 Using Wallet: {account.address}")

    # 3. Load Contracts
    sports_amm_contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=OVERTIME_SPORTS_AMM_ABI)
    usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=ERC20_ABI)

    # 4. Define Bet Parameters
    # For PoC, we'll use a simple market identifier
    # In production, this would come from the Overtime API
    market_address = "0x53504f5254535f414d4d5f746f5f5265736f6c76655f4d41524b45545f323034"
    position = 0  # Home
    buy_in_amount_usd = 3.08
    usdc_decimals = 6
    buy_in_amount_wei = int(buy_in_amount_usd * (10**usdc_decimals))
    
    print(f"📊 Bet Parameters:")
    print(f"   - Market: {market_address}")
    print(f"   - Position: {position}")
    print(f"   - Amount: {buy_in_amount_usd} USDC ({buy_in_amount_wei} wei)")
    print(f"   - Sports AMM: {sports_amm_address}")
    print(f"   - USDC Contract: {usdc_address}")
    
    try:
        # --- STEP A: APPROVE ---
        print(f"\n--- Step A: Approving {buy_in_amount_usd} USDC for Sports AMM contract ---")
        approve_tx = usdc_contract.functions.approve(
            w3.to_checksum_address(sports_amm_address),
            buy_in_amount_wei
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 100000,
            'maxFeePerGas': w3.to_wei('0.2', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('0.1', 'gwei'),
        })
        signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
        approve_tx_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
        print(f"✅ Approve transaction sent! Hash: {approve_tx_hash.hex()}")
        print("Waiting for confirmation...")
        w3.eth.wait_for_transaction_receipt(approve_tx_hash)
        print("✅ Approval confirmed!")

        # --- STEP B: TRADE ---
        # Allow a few seconds for the approval to propagate
        time.sleep(5)
        print(f"\n--- Step B: Executing trade for {buy_in_amount_usd} USDC ---")
        
        try:
            # The 'trade' function is complex. We will use the simpler 'buyFromAMM' for this PoC.
            # The 'trade' function is for parlays, 'buyFromAMM' is for singles.
            trade_tx = sports_amm_contract.functions.buyFromAMM(
                w3.to_bytes(hexstr=market_address),
                position,
                buy_in_amount_wei
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 1500000,
                'maxFeePerGas': w3.to_wei('0.2', 'gwei'),
                'maxPriorityFeePerGas': w3.to_wei('0.1', 'gwei'),
            })
            signed_trade_tx = w3.eth.account.sign_transaction(trade_tx, private_key)
            trade_tx_hash = w3.eth.send_raw_transaction(signed_trade_tx.raw_transaction)
            print(f"✅ Trade transaction sent! Hash: {trade_tx_hash.hex()}")
            print("Waiting for confirmation...")
            
            # Wait with timeout for transaction confirmation
            receipt = w3.eth.wait_for_transaction_receipt(trade_tx_hash, timeout=120)
            
            if receipt.status == 1:
                print("🎉 VICTORY! Autonomous USDC bet placed successfully!")
                print(f"🌐 View on Arbiscan: https://arbiscan.io/tx/{trade_tx_hash.hex()}")
            else:
                print("⚠️ Trade transaction failed after being sent.")
                
        except Exception as trade_error:
            print(f"⚠️ Trade step failed (this may be due to market parameters): {trade_error}")
            print("✅ However, the APPROVE step was successful, demonstrating the two-step process!")

    except Exception as e:
        print(f"🔥 AN ERROR OCCURRED: {e}")

if __name__ == "__main__":
    main()
