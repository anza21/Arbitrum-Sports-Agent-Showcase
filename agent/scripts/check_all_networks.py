import os
from web3 import Web3
from dotenv import load_dotenv

def main():
    print("--- 🔍 CHECKING ALL NETWORKS ---")
    
    load_dotenv(os.path.join('.', '.env'))
    wallet_address = os.getenv('WALLET_ADDRESS')
    
    print(f"Wallet: {wallet_address}")
    
    # Different networks and their USDC contracts
    networks = {
        "Optimism": {
            "rpc": "https://optimism-mainnet.infura.io/v3/629b952d90de4cef8ac371da8cb7b115",
            "chain_id": 10,
            "usdc_contracts": [
                "0x81C9A7B55A4df39A9B7B5F781ec0e53539694873",  # Native USDC
                "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",  # USDC.e
            ]
        },
        "Ethereum": {
            "rpc": "https://mainnet.infura.io/v3/629b952d90de4cef8ac371da8cb7b115",
            "chain_id": 1,
            "usdc_contracts": [
                "0xA0b86a33E6441b8c4C8C0E4b8b8c4C8C0E4b8b8c4",  # USDC on Ethereum
            ]
        },
        "Arbitrum": {
            "rpc": "https://arbitrum-mainnet.infura.io/v3/629b952d90de4cef8ac371da8cb7b115",
            "chain_id": 42161,
            "usdc_contracts": [
                "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # USDC on Arbitrum
            ]
        }
    }
    
    usdc_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'
    
    for network_name, network_info in networks.items():
        print(f"\n--- {network_name} ---")
        try:
            w3 = Web3(Web3.HTTPProvider(network_info["rpc"]))
            chain_id = w3.eth.chain_id
            print(f"Chain ID: {chain_id}")
            
            if chain_id != network_info["chain_id"]:
                print(f"⚠️ Expected Chain ID {network_info['chain_id']}, got {chain_id}")
                continue
                
            for contract_addr in network_info["usdc_contracts"]:
                try:
                    contract = w3.eth.contract(address=w3.to_checksum_address(contract_addr), abi=usdc_abi)
                    balance = contract.functions.balanceOf(wallet_address).call()
                    symbol = contract.functions.symbol().call()
                    decimals = contract.functions.decimals().call()
                    
                    print(f"Contract: {contract_addr}")
                    print(f"Symbol: {symbol}")
                    print(f"Balance: {balance / (10**decimals)} {symbol}")
                    
                    if balance > 0:
                        print(f"✅ FOUND USDC: {balance / (10**decimals)} {symbol}")
                        
                except Exception as e:
                    print(f"Contract {contract_addr}: Error - {e}")
                    
        except Exception as e:
            print(f"Network error: {e}")

if __name__ == "__main__":
    main()
