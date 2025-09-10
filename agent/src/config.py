# agent/src/config.py
import os
from dotenv import load_dotenv
from dataclasses import dataclass

# Load .env file from the parent directory of 'src'
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Wallet & Blockchain ---
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

# --- External APIs ---
THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

# --- Genner Configuration Classes ---
@dataclass
class ClaudeConfig:
    name: str = "claude"
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4096
    temperature: float = 0.7

@dataclass
class DeepseekConfig:
    name: str = "deepseek"
    model: str = "deepseek-reasoner"
    max_tokens: int = 8192
    temperature: float = 0.7

@dataclass
class OAIConfig:
    name: str = "openai"
    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7

@dataclass
class OllamaConfig:
    name: str = "ollama"
    model: str = "llama2"
    max_tokens: int = 4096
    temperature: float = 0.7

@dataclass
class OpenRouterConfig:
    name: str = "openrouter"
    model: str = "anthropic/claude-3-sonnet"
    max_tokens: int = 4096
    temperature: float = 0.7