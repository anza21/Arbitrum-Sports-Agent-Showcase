#!/usr/bin/env python3
"""
Balance Verification Script
Cross-verifies wallet balance using Web3/RPC and Arbiscan API methods
"""

import os
import requests
import json
from web3 import Web3
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "0xCbAAA5415B9A7A64b4a11d88a64917173eA1A187")
USDC_CONTRACT = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
ARBISCAN_API_URL = "https://api.arbiscan.io/api"
ARBISCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "YourApiKeyToken")
ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")

# USDC.e has 6 decimals
USDC_DECIMALS = 6

def get_balance_web3():
    """Method 1: Get balance using Web3/RPC (same as WalletService)"""
    try:
        # Connect to Arbitrum One network using environment variable
        w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC_URL))
        
        if not w3.is_connected():
            return "ERROR: Could not connect to Arbitrum RPC"
        
        # Fix EIP-55 checksum
        checksum_wallet = Web3.to_checksum_address(WALLET_ADDRESS)
        checksum_contract = Web3.to_checksum_address(USDC_CONTRACT)
        
        # USDC.e ABI for balanceOf function
        usdc_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        # Create contract instance
        contract = w3.eth.contract(address=checksum_contract, abi=usdc_abi)
        
        # Get balance
        balance_wei = contract.functions.balanceOf(checksum_wallet).call()
        balance_usdc = Decimal(balance_wei) / Decimal(10 ** USDC_DECIMALS)
        
        return f"{balance_usdc:.2f} USDC.e"
        
    except Exception as e:
        return f"ERROR: {str(e)}"

def get_balance_web3_alternative():
    """Method 1b: Get balance using alternative RPC endpoint"""
    try:
        # Try alternative RPC endpoint
        w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/arbitrum'))
        
        if not w3.is_connected():
            return "ERROR: Could not connect to alternative RPC"
        
        # Fix EIP-55 checksum
        checksum_wallet = Web3.to_checksum_address(WALLET_ADDRESS)
        checksum_contract = Web3.to_checksum_address(USDC_CONTRACT)
        
        # USDC.e ABI for balanceOf function
        usdc_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        # Create contract instance
        contract = w3.eth.contract(address=checksum_contract, abi=usdc_abi)
        
        # Get balance
        balance_wei = contract.functions.balanceOf(checksum_wallet).call()
        balance_usdc = Decimal(balance_wei) / Decimal(10 ** USDC_DECIMALS)
        
        return f"{balance_usdc:.2f} USDC.e"
        
    except Exception as e:
        return f"ERROR: {str(e)}"

def get_balance_arbiscan():
    """Method 2: Get balance using Arbiscan API"""
    try:
        # Check if API key is properly configured
        if ARBISCAN_API_KEY == "YourApiKeyToken" or not ARBISCAN_API_KEY:
            return "ERROR: ETHERSCAN_API_KEY not configured in environment"
            
        params = {
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': USDC_CONTRACT,
            'address': WALLET_ADDRESS,
            'tag': 'latest',
            'apikey': ARBISCAN_API_KEY
        }
        
        response = requests.get(ARBISCAN_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == '1':
            balance_wei = int(data.get('result', '0'))
            balance_usdc = Decimal(balance_wei) / Decimal(10 ** USDC_DECIMALS)
            return f"{balance_usdc:.2f} USDC.e"
        else:
            return f"API ERROR: {data.get('message', 'Unknown error')}"
            
    except requests.exceptions.RequestException as e:
        return f"REQUEST ERROR: {str(e)}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def get_balance_public_rpc():
    """Method 3: Get balance using public RPC call"""
    try:
        # Use public RPC endpoint with direct JSON-RPC call
        url = "https://arb1.arbitrum.io/rpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [
                {
                    "to": USDC_CONTRACT,
                    "data": f"0x70a08231000000000000000000000000{WALLET_ADDRESS[2:]}"
                },
                "latest"
            ],
            "id": 1
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'result' in data:
            balance_hex = data['result']
            if balance_hex == '0x':
                balance_wei = 0
            else:
                balance_wei = int(balance_hex, 16)
            
            balance_usdc = Decimal(balance_wei) / Decimal(10 ** USDC_DECIMALS)
            return f"{balance_usdc:.2f} USDC.e"
        else:
            return f"RPC ERROR: {data.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    """Main verification function"""
    print("=" * 60)
    print("           BALANCE VERIFICATION DIAGNOSTIC")
    print("=" * 60)
    print(f"Wallet: {WALLET_ADDRESS}")
    print(f"Token: USDC.e ({USDC_CONTRACT})")
    print(f"Network: Arbitrum One")
    print(f"RPC URL: {ARBITRUM_RPC_URL}")
    print(f"API Key: {'Configured' if ARBISCAN_API_KEY != 'YourApiKeyToken' else 'NOT CONFIGURED'}")
    print("-" * 60)
    
    # Method 1: Web3/RPC (Primary)
    print("Method 1 (Web3/RPC - Primary):")
    web3_result = get_balance_web3()
    print(f"  Result: {web3_result}")
    
    print()
    
    # Method 1b: Web3/RPC (Alternative)
    print("Method 1b (Web3/RPC - Alternative):")
    web3_alt_result = get_balance_web3_alternative()
    print(f"  Result: {web3_alt_result}")
    
    print()
    
    # Method 2: Arbiscan API
    print("Method 2 (Arbiscan API):")
    arbiscan_result = get_balance_arbiscan()
    print(f"  Result: {arbiscan_result}")
    
    print()
    
    # Method 3: Public RPC
    print("Method 3 (Public RPC):")
    public_rpc_result = get_balance_public_rpc()
    print(f"  Result: {public_rpc_result}")
    
    print("-" * 60)
    
    # Analysis
    print("ANALYSIS:")
    successful_methods = []
    
    if "ERROR" not in web3_result:
        successful_methods.append("Primary RPC")
    if "ERROR" not in web3_alt_result:
        successful_methods.append("Alternative RPC")
    if "ERROR" not in arbiscan_result:
        successful_methods.append("Arbiscan API")
    if "ERROR" not in public_rpc_result:
        successful_methods.append("Public RPC")
    
    if len(successful_methods) == 0:
        print("  All methods failed - check network connectivity")
    elif len(successful_methods) == 1:
        print(f"  Only {successful_methods[0]} succeeded - potential RPC issue")
    else:
        print(f"  {len(successful_methods)} methods succeeded - compare results")
        
        # Compare successful results
        results = []
        if "ERROR" not in web3_result:
            results.append(("Primary RPC", web3_result))
        if "ERROR" not in web3_alt_result:
            results.append(("Alternative RPC", web3_alt_result))
        if "ERROR" not in public_rpc_result:
            results.append(("Public RPC", public_rpc_result))
            
        if len(results) > 1:
            print("  Result Comparison:")
            for method, result in results:
                print(f"    {method}: {result}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
