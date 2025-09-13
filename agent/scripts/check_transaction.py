import os
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 CHECKING TRANSACTION DETAILS ---")
    load_dotenv()

    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum RPC")
        return

    # Transaction hash from the failed trade
    tx_hash = "11adcb53931205e51c39b4ee33ddb220a6dda70bbf60f5267e89b2a908cdfeac"
    
    try:
        # Get transaction details
        tx = w3.eth.get_transaction(tx_hash)
        print(f"Transaction Details:")
        print(f"  From: {tx['from']}")
        print(f"  To: {tx['to']}")
        print(f"  Gas: {tx['gas']}")
        print(f"  Gas Price: {tx['gasPrice']}")
        print(f"  Value: {tx['value']}")
        print(f"  Data Length: {len(tx['input'])} bytes")
        
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"\nTransaction Receipt:")
        print(f"  Status: {receipt['status']}")
        print(f"  Gas Used: {receipt['gasUsed']}")
        print(f"  Block Number: {receipt['blockNumber']}")
        print(f"  Transaction Index: {receipt['transactionIndex']}")
        
        if receipt['status'] == 0:
            print(f"\n❌ Transaction Failed!")
            print(f"Gas Used: {receipt['gasUsed']} / {tx['gas']}")
            
            # Try to get revert reason
            try:
                # Get the block where the transaction was mined
                block = w3.eth.get_block(receipt['blockNumber'])
                
                # Try to call the transaction again to get revert reason
                print(f"\nTrying to get revert reason...")
                
                # This is a simplified approach - in practice you'd need to trace the transaction
                print(f"Transaction failed but was included in block {receipt['blockNumber']}")
                print(f"This usually means the transaction reverted due to:")
                print(f"1. Insufficient gas")
                print(f"2. Contract logic reverted")
                print(f"3. Invalid parameters")
                print(f"4. Contract state issue")
                
            except Exception as e:
                print(f"Could not get detailed revert reason: {e}")
        else:
            print(f"\n✅ Transaction Succeeded!")
            
    except Exception as e:
        print(f"❌ Error checking transaction: {e}")

if __name__ == "__main__":
    main()
