#!/usr/bin/env python3
"""
Contract Debug Script - Diagnosing buyFromAMM failures
"""
import os
from web3 import Web3
import json

# Arbitrum connection
ARBITRUM_RPC_URL = "https://arbitrum-mainnet.infura.io/v3/your-infura-key"  
w3 = Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc"))

# Contract details
CONTRACT_ADDRESS = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"  # Example - need real address
FAILED_MARKET_ID = "0x32303235303930364646464639414333000000000000000000000000000000"

# Minimal ABI for testing
MINIMAL_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "_market", "type": "bytes32"},
            {"internalType": "uint256", "name": "_position", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"}
        ],
        "name": "buyFromAMM",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

def test_contract_interaction():
    print("🔍 ARBITRUM CONTRACT DEBUGGING")
    print(f"📡 Network: {w3.eth.chain_id}")
    print(f"📋 Contract: {CONTRACT_ADDRESS}")
    print(f"🎯 Market ID: {FAILED_MARKET_ID}")
    
    # Create contract instance
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=MINIMAL_ABI)
    
    # Test wallet address
    wallet_address = "0x1234567890123456789012345678901234567890"  # Example
    
    # Try to estimate gas for the transaction
    try:
        gas_estimate = contract.functions.buyFromAMM(
            FAILED_MARKET_ID, 
            0,  # position
            1000000  # 1 USDC.e in wei (6 decimals)
        ).estimate_gas({'from': wallet_address})
        
        print(f"✅ Gas Estimate: {gas_estimate}")
        
    except Exception as e:
        print(f"❌ Gas Estimation Failed: {e}")
        print(f"🔍 Error Type: {type(e).__name__}")
        
        # Try to get more detailed error info
        if hasattr(e, 'message'):
            print(f"📝 Error Message: {e.message}")
        
        # Check if it's a contract revert
        if "execution reverted" in str(e):
            print("🚨 CONTRACT REVERTED - Possible reasons:")
            print("   - Market ID doesn't exist")
            print("   - Market is closed/resolved")
            print("   - Insufficient liquidity")
            print("   - Wrong position parameter")
            print("   - Amount validation failed")

if __name__ == "__main__":
    test_contract_interaction()
