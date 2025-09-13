import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 DEBUG: ABI Issue Analysis ---")
    load_dotenv()

    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum RPC")
        return

    account = w3.eth.account.from_key(os.getenv('PRIVATE_KEY', '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'))
    sports_amm_address = '0xfb64E79A562F7250131cf528242CEB10fDC82395'
    
    print(f"✅ Connected to Arbitrum. Wallet: {account.address}")
    print(f"🔧 Sports AMM Address: {sports_amm_address}")

    # --- Test 1: Check if contract has the trade function ---
    print(f"\n--- Test 1: Checking Contract Functions ---")
    try:
        # Get contract code
        code = w3.eth.get_code(w3.to_checksum_address(sports_amm_address))
        print(f"Contract code length: {len(code)} bytes")
        
        # Try to call a simple function first
        simple_abi = '[{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"type":"function"}]'
        contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=simple_abi)
        
        try:
            owner = contract.functions.owner().call()
            print(f"✅ Contract owner: {owner}")
        except Exception as e:
            print(f"❌ Owner call failed: {e}")
            
    except Exception as e:
        print(f"❌ Contract check failed: {e}")

    # --- Test 2: Try different ABI versions ---
    print(f"\n--- Test 2: Testing Different ABI Versions ---")
    
    # Version 1: Our current ABI
    abi_v1 = '[{"inputs":[{"components":[{"internalType":"bytes32","name":"gameId","type":"bytes32"},{"internalType":"uint16","name":"sportId","type":"uint16"},{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint256","name":"maturity","type":"uint256"},{"internalType":"uint8","name":"status","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"},{"internalType":"uint256","name":"playerId","type":"uint256"},{"internalType":"uint256[]","name":"odds","type":"uint256[]"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"uint8","name":"position","type":"uint8"},{"components":[{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint8","name":"position","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"}],"internalType":"struct SportsAMMV2.CombinedPosition[][]","name":"combinedPositions","type":"tuple[][]"},{"internalType":"bool","name":"live","type":"bool"}],"internalType":"struct SportsAMMV2.TradeData[]","name":"_tradeData","type":"tuple[]"},{"internalType":"uint256","name":"_buyInAmount","type":"uint256"},{"internalType":"uint256","name":"_totalQuote","type":"uint256"},{"internalType":"uint256","name":"_slippage","type":"uint256"},{"internalType":"address","name":"_referrer","type":"address"},{"internalType":"address","name":"_collateral","type":"address"},{"internalType":"bool","name":"_isLive","type":"bool"}],"name":"trade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
    
    # Version 2: Simplified ABI without combinedPositions
    abi_v2 = '[{"inputs":[{"components":[{"internalType":"bytes32","name":"gameId","type":"bytes32"},{"internalType":"uint16","name":"sportId","type":"uint16"},{"internalType":"uint16","name":"typeId","type":"uint16"},{"internalType":"uint256","name":"maturity","type":"uint256"},{"internalType":"uint8","name":"status","type":"uint8"},{"internalType":"int256","name":"line","type":"int256"},{"internalType":"uint256","name":"playerId","type":"uint256"},{"internalType":"uint256[]","name":"odds","type":"uint256[]"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"uint8","name":"position","type":"uint8"},{"internalType":"bool","name":"live","type":"bool"}],"internalType":"struct SportsAMMV2.TradeData[]","name":"_tradeData","type":"tuple[]"},{"internalType":"uint256","name":"_buyInAmount","type":"uint256"},{"internalType":"uint256","name":"_totalQuote","type":"uint256"},{"internalType":"uint256","name":"_slippage","type":"uint256"},{"internalType":"address","name":"_referrer","type":"address"},{"internalType":"address","name":"_collateral","type":"address"},{"internalType":"bool","name":"_isLive","type":"bool"}],"name":"trade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
    
    # Test both ABIs
    for i, abi in enumerate([abi_v1, abi_v2], 1):
        print(f"\nTesting ABI Version {i}:")
        try:
            contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=abi)
            
            # Try to get function signature
            trade_func = contract.functions.trade
            print(f"✅ Trade function found in ABI {i}")
            
            # Try to build a simple transaction (without sending)
            try:
                # Create minimal test data
                test_data = [{
                    "gameId": b'\x00' * 32,  # Empty bytes32
                    "sportId": 0,
                    "typeId": 0,
                    "maturity": 0,
                    "status": 0,
                    "line": 0,
                    "playerId": 0,
                    "odds": [0],
                    "merkleProof": [],
                    "position": 0,
                    "live": False
                }]
                
                if i == 1:  # ABI v1 has combinedPositions
                    test_data[0]["combinedPositions"] = []
                
                # Try to build transaction
                tx = trade_func(
                    test_data,
                    0,  # _buyInAmount
                    0,  # _totalQuote
                    0,  # _slippage
                    '0x0000000000000000000000000000000000000000',  # _referrer
                    '0x0000000000000000000000000000000000000000',  # _collateral
                    False  # _isLive
                ).build_transaction({
                    'from': account.address,
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'gas': 100000,
                    'gasPrice': w3.eth.gas_price
                })
                print(f"✅ Transaction building successful with ABI {i}")
                
            except Exception as e:
                print(f"❌ Transaction building failed with ABI {i}: {e}")
                
        except Exception as e:
            print(f"❌ ABI {i} failed: {e}")

    # --- Test 3: Check if this is actually the right contract ---
    print(f"\n--- Test 3: Contract Verification ---")
    try:
        # Try to get contract name or other identifying info
        name_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"}]'
        contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=name_abi)
        
        try:
            name = contract.functions.name().call()
            print(f"✅ Contract name: {name}")
        except:
            print("❌ Could not get contract name")
            
        # Try to get version
        version_abi = '[{"constant":true,"inputs":[],"name":"version","outputs":[{"name":"","type":"string"}],"type":"function"}]'
        contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=version_abi)
        
        try:
            version = contract.functions.version().call()
            print(f"✅ Contract version: {version}")
        except:
            print("❌ Could not get contract version")
            
    except Exception as e:
        print(f"❌ Contract verification failed: {e}")

if __name__ == "__main__":
    main()
