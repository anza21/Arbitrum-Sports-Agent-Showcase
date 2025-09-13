#!/usr/bin/env python3
import os
print("=== Environment Test ===")
print(f"ARBITRUM_RPC_URL: {os.getenv('ARBITRUM_RPC_URL', 'NOT SET')}")
print(f"WALLET_ADDRESS: {os.getenv('WALLET_ADDRESS', 'NOT SET')}")
print(f"PRIVATE_KEY: {os.getenv('PRIVATE_KEY', 'NOT SET')}")
print(f"OVERTIME_REST_API_KEY: {os.getenv('OVERTIME_REST_API_KEY', 'NOT SET')}")
print(f"USDC_CONTRACT_ADDRESS: {os.getenv('USDC_CONTRACT_ADDRESS', 'NOT SET')}")
print(f"SPORTS_AMM_ADDRESS: {os.getenv('SPORTS_AMM_ADDRESS', 'NOT SET')}")
print("=== Test Complete ===")
