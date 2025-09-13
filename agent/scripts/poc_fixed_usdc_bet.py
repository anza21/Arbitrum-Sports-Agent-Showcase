import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv
import sys
sys.path.append('/home/anza/project/superior-agents-clean/superior-agent-v1')
from agent.src.contracts.overtime_abi import OVERTIME_SPORTS_AMM_ABI

# --- MINIMAL ERC20 ABI FOR APPROVE ---
ERC20_ABI = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'

def main():
    print("🔧 FIXED VERSION: Starting Corrected USDC Betting PoC")
    print("=" * 70)

    # 1. Load Environment Variables
    load_dotenv()
    rpc_url = os.getenv('ARBITRUM_RPC_URL')
    wallet_address = os.getenv('WALLET_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS')
    usdc_address = os.getenv('USDC_CONTRACT_ADDRESS') or "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

    # 2. Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)
    print(f"✅ Connected to Arbitrum. Using Wallet: {account.address}")
    print(f"🔗 Chain ID: {w3.eth.chain_id}")

    # 3. Load Contracts
    sports_amm_contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=OVERTIME_SPORTS_AMM_ABI)
    usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=ERC20_ABI)

    # 4. === LIVE BET PARAMETERS (Updated by Role +) ===
    market_id = "0x3230323530393132364244323832374200000000000000000000000000000000"
    position = 1  # 1 for Away team
    buy_in_amount_usd = 3.08
    usdc_decimals = 6
    buy_in_amount_wei = int(buy_in_amount_usd * (10**usdc_decimals))
    
    print(f"🎯 Target: 'The Otter Side vs Odivelas Sports Club'")
    print(f"📊 Position: Away team (Odivelas Sports Club)")
    print(f"💰 Amount: ${buy_in_amount_usd} USDC")
    print(f"🏟️ Market ID: {market_id}")
    print(f"🏦 Sports AMM: {sports_amm_address}")
    print(f"💵 USDC Contract: {usdc_address}")
    print("=" * 70)
    
    try:
        # --- STEP A: CHECK ALLOWANCE & APPROVE IF NEEDED ---
        print("\n🔍 Step A: Checking USDC Allowance...")
        allowance = usdc_contract.functions.allowance(account.address, w3.to_checksum_address(sports_amm_address)).call()
        print(f"   Current allowance: {allowance} wei ({allowance / (10**usdc_decimals):.2f} USDC)")
        print(f"   Required amount: {buy_in_amount_wei} wei ({buy_in_amount_usd} USDC)")
        
        if allowance < buy_in_amount_wei:
            print(f"   ⚠️ Insufficient allowance. Sending APPROVE transaction...")
            approve_tx = usdc_contract.functions.approve(w3.to_checksum_address(sports_amm_address), buy_in_amount_wei).build_transaction({
                'from': account.address, 
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': w3.to_wei('0.1', 'gwei'),  # Use gasPrice instead of maxFeePerGas
            })
            signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
            approve_tx_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
            print(f"   ✅ Approve transaction sent! Hash: {approve_tx_hash.hex()}")
            print("   ⏳ Waiting for confirmation...")
            w3.eth.wait_for_transaction_receipt(approve_tx_hash)
            print("   ✅ Approval confirmed!")
            time.sleep(10) # Wait for propagation
        else:
            print("   ✅ Sufficient allowance already set.")

        # --- STEP B: EXECUTE TRADE ---
        print("\n🚀 Step B: Executing TRADE transaction...")
        print("   📡 Calling buyFromAMM function...")
        
        # Try to estimate gas first
        try:
            gas_estimate = sports_amm_contract.functions.buyFromAMM(
                w3.to_bytes(hexstr=market_id),
                position,
                buy_in_amount_wei
            ).estimate_gas({'from': account.address})
            print(f"   📊 Gas estimate: {gas_estimate}")
        except Exception as e:
            print(f"   ⚠️ Gas estimation failed: {e}")
            gas_estimate = 2000000
        
        trade_tx = sports_amm_contract.functions.buyFromAMM(
            w3.to_bytes(hexstr=market_id),
            position,
            buy_in_amount_wei
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': int(gas_estimate * 1.2),  # Add 20% buffer
            'gasPrice': w3.to_wei('0.1', 'gwei'),  # Use gasPrice instead of maxFeePerGas
        })
        
        print("   🔐 Signing transaction...")
        signed_trade_tx = w3.eth.account.sign_transaction(trade_tx, private_key)
        
        print("   📤 Sending transaction to blockchain...")
        trade_tx_hash = w3.eth.send_raw_transaction(signed_trade_tx.raw_transaction)
        print(f"   ✅ Trade transaction sent! Hash: {trade_tx_hash.hex()}")
        
        print("   ⏳ Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(trade_tx_hash, timeout=120)
        
        if receipt.status == 1:
            print("\n" + "🎉" * 20)
            print("🎉🎉🎉 FIXED! Autonomous USDC bet CONFIRMED!")
            print("🎉🎉🎉 VICTORY! VICTORY! VICTORY!")
            print("🎉" * 20)
            print(f"🌐 View on Arbiscan: https://arbiscan.io/tx/{trade_tx_hash.hex()}")
            print(f"📊 Transaction Hash: {trade_tx_hash.hex()}")
            print(f"💰 Amount: ${buy_in_amount_usd} USDC")
            print(f"🎯 Position: Away team (Odivelas Sports Club)")
            print("🏆 THE SUPERIOR AGENT HAS SUCCESSFULLY PLACED AN AUTONOMOUS BET!")
            print("🎉" * 20)
        else:
            print("\n" + "⚠️" * 20)
            print("⚠️ Trade transaction FAILED on-chain. Check Arbiscan for details.")
            print(f"🌐 https://arbiscan.io/tx/{trade_tx_hash.hex()}")
            print("⚠️" * 20)

    except Exception as e:
        print(f"\n🔥 AN ERROR OCCURRED: {e}")
        print("📋 Full error details:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
