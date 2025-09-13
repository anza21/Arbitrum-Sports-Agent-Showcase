import os
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 CHECKING SPORTS AMM CONTRACT ---")
    
    load_dotenv(os.path.join('.', '.env'))
    optimism_rpc_url = os.getenv('ARBITRUM_RPC_URL')
    sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS')
    
    w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
    
    print(f"Sports AMM Address: {sports_amm_address}")
    
    # Check if contract exists
    try:
        code = w3.eth.get_code(sports_amm_address)
        if code == b'':
            print("❌ Contract has no code - address is invalid!")
            return
        else:
            print(f"✅ Contract has code ({len(code)} bytes)")
    except Exception as e:
        print(f"❌ Error checking contract: {e}")
        return
    
    # Check if contract is a proxy
    try:
        # Try to call a simple function to see if contract responds
        simple_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"}]'
        contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=simple_abi)
        name = contract.functions.name().call()
        print(f"✅ Contract name: {name}")
    except Exception as e:
        print(f"⚠️ Contract doesn't respond to name() call: {e}")
    
    # Check if this is the correct Sports AMM contract
    try:
        # Try to call a Sports AMM specific function
        sports_amm_abi = '[{"constant":true,"inputs":[],"name":"sportsAMM","outputs":[{"name":"","type":"address"}],"type":"function"}]'
        contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=sports_amm_abi)
        sports_amm = contract.functions.sportsAMM().call()
        print(f"✅ Sports AMM: {sports_amm}")
    except Exception as e:
        print(f"⚠️ Not a Sports AMM contract: {e}")
    
    # Check if contract has trade function
    try:
        trade_abi = '[{"constant":false,"inputs":[{"name":"_tradeData","type":"tuple[]"},{"name":"_buyInAmount","type":"uint256"},{"name":"_totalQuote","type":"uint256"},{"name":"_slippage","type":"uint256"},{"name":"_referrer","type":"address"},{"name":"_collateral","type":"address"},{"name":"_isLive","type":"bool"}],"name":"trade","outputs":[],"type":"function"}]'
        contract = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=trade_abi)
        print("✅ Contract has trade function")
    except Exception as e:
        print(f"❌ Contract doesn't have trade function: {e}")

if __name__ == "__main__":
    main()
