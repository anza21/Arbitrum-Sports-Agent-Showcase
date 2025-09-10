import sys
import os
import uuid
import docker
import time

# --- MASTER SAFETY SWITCH ---
EXECUTE_ON_CHAIN = True

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from agent.src import config
from agent.src.agent.betting import BettingAgent, BettingPromptGenerator
from agent.src.container import ContainerManager
from agent.src.client.rag import RAGClient
from agent.src.genner import get_genner
from agent.src.sensor.trading import TradingSensor
from agent.src.db.sqlite import SQLiteDB
from agent.src.services.news_service import NewsService
from agent.src.services.wallet_service import WalletService
from agent.src.services.overtime_service import OvertimeService
from agent.src.services.the_odds_service import TheOddsService
from agent.src.services.search_service import SearchService

def start_betting_agent():
    """
    Initializes and starts the BettingAgent.
    """
    print("--- Environment variables loaded via Docker env_file ---")
    
    # Debug: Print critical environment variables (without showing sensitive values)
    critical_vars = ['WALLET_ADDRESS', 'ARBITRUM_RPC_URL', 'THE_ODDS_API_KEY', 'OPENWEATHERMAP_API_KEY']
    print("--- Critical Environment Variables Status: ---")
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: {'*' * min(len(value), 20)} (loaded)")
        else:
            print(f"  ✗ {var}: NOT SET")
    print("--- End Environment Variables Status ---")

    while True:
        print("\n" + "="*50)
        print(f"--- STARTING NEW CYCLE: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        print("="*50)

        # First, check and update results of past bets
        print("--- Checking for pending bets to update... ---")
        agent_id = "betting-agent-001"
        session_id = str(uuid.uuid4())

        # Create a temporary agent instance for updating pending bets
        temp_rag_client = RAGClient(agent_id=agent_id, session_id=session_id, base_url="http://rag-api:32771")
        temp_db = SQLiteDB(db_path="/app/agent/db/superior-agents.db")
        temp_sensor = TradingSensor(
            eth_address=os.getenv("WALLET_ADDRESS", "0x0000000000000000000000000000000000000000"),
            infura_project_id=os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
            etherscan_api_key=os.getenv("ETHERSCAN_API_KEY", "mock_api_key")
        )
        temp_genner = get_genner(backend="mock", stream_fn=None)
        temp_prompts_dict = {
            "system_prompt": BettingPromptGenerator.get_default_prompts()["system_prompt"],
            "research_code_prompt_first": BettingPromptGenerator.get_default_prompts()["research_code_prompt_first"],
        }
        temp_prompt_generator = BettingPromptGenerator(prompts=temp_prompts_dict)
        temp_news_service = NewsService()
        temp_wallet_service = WalletService()
        temp_overtime_service = OvertimeService()
        temp_the_odds_service = TheOddsService(os.getenv('THE_ODDS_API_KEY')) if os.getenv('THE_ODDS_API_KEY') else None
        temp_weather_service = None  # WeatherService() if os.getenv('OPENWEATHERMAP_API_KEY') else None
        temp_search_service = SearchService()

        # Get ETH balance for temp agent
        temp_wallet_address = "0xCbAAA5415B9A7A64b4a11d88a64917173eA1A187"  # Commander's wallet
        temp_eth_balance = temp_wallet_service.get_eth_balance(temp_wallet_address)
        
        temp_agent = BettingAgent(
            db=temp_db,
            sensor=temp_sensor,
            genner=temp_genner,
            container_manager=None,  # Not needed for updates
            rag_client=temp_rag_client,
            overtime_service=temp_overtime_service,
            news_service=temp_news_service,
            wallet_service=temp_wallet_service,
            the_odds_service=temp_the_odds_service,
            weather_service=temp_weather_service,
            search_service=temp_search_service,
            eth_balance=temp_eth_balance
        )

        # Check and update pending bets
        temp_agent.check_and_update_pending_bets()

        # --- Main logic ---
        print("--- Assembling Agent Components ---")

        # Initialize ContainerManager with error handling
        try:
            docker_client = docker.from_env()
            
            # Prepare execution environment variables
            execution_env_vars = {
                "AGENT_ID": agent_id, 
                "SESSION_ID": session_id,
                "ARBITRUM_RPC_URL": os.getenv("ARBITRUM_RPC_URL"),
                "PRIVATE_KEY": os.getenv("PRIVATE_KEY"),
                "WALLET_ADDRESS": os.getenv("WALLET_ADDRESS"),
                "OVERTIME_CONTRACT": os.getenv("OVERTIME_CONTRACT")
            }
            
            container_manager = ContainerManager(
                client=docker_client,
                container_identifier=f"{agent_id}-{session_id}",
                host_cache_folder="/tmp",
                in_con_env=execution_env_vars
            )
            print("--- Container Manager Initialized Successfully ---")
            
        except Exception as e:
            print(f"--- ERROR: Failed to initialize ContainerManager: {e} ---")
            print("--- CRITICAL: Cannot continue without ContainerManager. Exiting. ---")
            return

        # Continue with the rest of the agent logic...
        print("--- Testing Wallet Service ---")
        wallet_balance = temp_wallet_service.get_wallet_balances(temp_wallet_address)
        if wallet_balance:
            print("--- SUCCESS: Wallet balances fetched successfully. ---")
            print(f"  - ETH Balance: {wallet_balance.get('eth_balance', 0):.6f} ETH")
            print(f"  - USDC.e Balance: {wallet_balance.get('usdc_balance', 0):.2f} USDC.e")
        else:
            print("--- FAILURE: Unable to fetch wallet balances. ---")

        # Test news service
        print("--- Testing News Service ---")
        test_team_name = "Manchester City"
        news_articles = temp_news_service.get_sports_news(test_team_name, max_articles=5)

        if news_articles is not None:
            print(f"--- SUCCESS: News Service fetched {len(news_articles)} articles for {test_team_name}. ---")
            for article in news_articles:
                print(f"  - {article.get('title')}")
        else:
            print(f"--- FAILURE: News Service could not fetch articles for {test_team_name}. Check API key or service. ---")

        # Real feedback loop: Check and update any pending bets
        temp_agent.check_and_update_pending_bets()

        # Sleep for 12 hours before next cycle
        sleep_duration_seconds = 720 * 60  # Sleep for 12 hours (720 minutes)
        print(f"\n--- CYCLE COMPLETE. Agent sleeping for {sleep_duration_seconds / 60} minutes. ---")
        time.sleep(sleep_duration_seconds)

if __name__ == "__main__":
    start_betting_agent()
