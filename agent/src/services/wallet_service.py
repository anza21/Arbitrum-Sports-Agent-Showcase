from web3 import Web3
from typing import Optional
from agent.src import config

class WalletService:
    def __init__(self):
        # Initialize connection to Arbitrum RPC
        self.w3 = Web3(Web3.HTTPProvider(config.ARBITRUM_RPC_URL))
        
        # USDC.e contract address on Arbitrum
        self.usdc_address = '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'
        
        # Minimal ABI for balanceOf
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Initialize USDC.e contract
        self.usdc_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.usdc_address),
            abi=self.erc20_abi
        )

    def get_usdc_balance(self, wallet_address: str) -> float:
        """
        Get USDC.e balance for a given wallet address on Arbitrum
        
        Args:
            wallet_address (str): The wallet address to check
            
        Returns:
            float: The USDC.e balance in standard decimal form
        """
        try:
            # Convert address to checksum format
            checksum_address = self.w3.to_checksum_address(wallet_address)
            
            # Get raw balance in wei
            balance_wei = self.usdc_contract.functions.balanceOf(checksum_address).call()
            
            # Convert to standard decimal form (USDC.e has 6 decimals)
            balance = float(balance_wei) / (10 ** 6)
            
            return balance
            
        except Exception as e:
            print(f"Error getting USDC.e balance: {str(e)}")
            return 0.0

    def get_eth_balance(self, wallet_address: str) -> float:
        """
        Get ETH balance for a given wallet address on Arbitrum
        
        Args:
            wallet_address (str): The wallet address to check
            
        Returns:
            float: The ETH balance in Ether (converted from Wei)
        """
        try:
            # Convert address to checksum format
            checksum_address = self.w3.to_checksum_address(wallet_address)
            
            # Get raw balance in Wei
            balance_wei = self.w3.eth.get_balance(checksum_address)
            
            # Convert from Wei to Ether (1 Ether = 10^18 Wei)
            balance_eth = float(balance_wei) / (10 ** 18)
            
            return balance_eth
            
        except Exception as e:
            print(f"Error getting ETH balance: {str(e)}")
            return 0.0
