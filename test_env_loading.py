import os
from dotenv import load_dotenv

print("Before load_dotenv:")
print(f"USDC_CONTRACT_ADDRESS: {os.getenv('USDC_CONTRACT_ADDRESS')}")

load_dotenv()

print("After load_dotenv:")
print(f"USDC_CONTRACT_ADDRESS: {os.getenv('USDC_CONTRACT_ADDRESS')}")

# Test all relevant variables
variables = [
    'ARBITRUM_RPC_URL',
    'WALLET_ADDRESS', 
    'PRIVATE_KEY',
    'OVERTIME_REST_API_KEY',
    'USDC_CONTRACT_ADDRESS',
    'SPORTS_AMM_ADDRESS'
]

print("\nAll variables:")
for var in variables:
    value = os.getenv(var)
    if value:
        print(f"{var}: {value[:20]}..." if len(value) > 20 else f"{var}: {value}")
    else:
        print(f"{var}: None")
