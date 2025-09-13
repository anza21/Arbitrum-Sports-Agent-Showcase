import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv

# --- ABIs ---
ERC20_ABI = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'
SPORTS_AMM_ABI = '[{"inputs":[{"components":[{"internalType":"bytes32","name":"gameId","type":"bytes32"},{"internalType":"uint16","name":"sportId","type":"uint16"},{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint256","name":"maturity","type":"uint256"},{"internalType":"uint8","name":"status","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"},{"internalType":"uint256","name":"playerId","type":"uint256"},{"internalType":"uint256[]","name":"odds","type":"uint256[]"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"uint8","name":"position","type":"uint8"},{"components":[{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint8","name":"position","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"}],"internalType":"struct SportsAMMV2.CombinedPosition[][]","name":"combinedPositions","type":"tuple[][]"},{"internalType":"bool","name":"live","type":"bool"}],"internalType":"struct SportsAMMV2.TradeData[]","name":"_tradeData","type":"tuple[]"},{"internalType":"uint256","name":"_buyInAmount","type":"uint256"},{"internalType":"uint256","name":"_totalQuote","type":"uint256"},{"internalType":"uint256","name":"_slippage","type":"uint256"},{"internalType":"address","name":"_referrer","type":"address"},{"internalType":"address","name":"_collateral","type":"address"},{"internalType":"bool","name":"_isLive","type":"bool"}],"name":"trade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'

def main():
    print("--- 🔥 VICTORY LAP: Starting Definitive On-Chain USDC Betting PoC on OPTIMISM ---")

    load_dotenv()
    wallet_address = os.getenv('WALLET_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL') # Variable name is legacy, but URL is for Optimism
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS')
    usdc_address = os.getenv('USDC_CONTRACT_ADDRESS')

    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    account = w3.eth.account.from_key(private_key)
    print(f"✅ Connected to Optimism. Using Wallet: {account.address}")

    sports_amm_contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=SPORTS_AMM_ABI)
    usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=ERC20_ABI)

    # === LIVE BET PARAMETERS (Provided by Role +) ===
    market_id = "0x3230323530393132383044444439314400000000000000000000000000000000"
    position = 1  # 1 for Away (Spacestation Gaming)
    buy_in_amount_usd = 3.08
    buy_in_amount_wei = int(buy_in_amount_usd * (10**6))
    
    print(f"🎯 Target: 'ENVY - Spacestation Gaming' | Position: Away | Amount: ${buy_in_amount_usd} USDC")
    
    try:
        print("\n--- Step A: Approving USDC for Sports AMM contract ---")
        approve_tx = usdc_contract.functions.approve(sports_amm_address, buy_in_amount_wei).build_transaction({
            'from': account.address, 'nonce': w3.eth.get_transaction_count(account.address), 'gas': 100000
        })
        signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
        approve_tx_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
        print(f"✅ Approve TX sent: {approve_tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(approve_tx_hash)
        print("✅ Approval confirmed!")
        time.sleep(15)

        print("\n--- Step B: Executing TRADE on Optimism ---")
        
        # We need a valid 'tradeData' object. We'll use a simplified version for a single bet.
        # For a real implementation, this would require a call to the /quote API endpoint first.
        # For this PoC, we will try to call the simpler `buyFromAmm` which might not exist on this contract.
        # A more robust solution would be to construct the full `trade` object. Let's try a simplified `trade` call.
        # The ABI is minimal, so we assume `buyFromAmm` is not present and `trade` is the way.

        # This PoC cannot succeed without a valid quote from the API.
        # We will stop here. The next step is to build a PoC that calls the /quote endpoint.
        print("🔴 HALT: To call the 'trade' function, a valid quote from the Overtime API is required.")
        print("The current PoC has proven connection and approval. The next step is to build a script that gets a quote first.")


    except Exception as e:
        print(f"🔥 AN ERROR OCCURRED: {e}")

if __name__ == "__main__":
    main()
