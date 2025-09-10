import sys
import os
import uuid
import docker # Ensure docker is imported
import time

# --- MASTER SAFETY SWITCH ---
# Set to True to execute real on-chain transactions
# Set to False to run in simulation mode (generates code but does not execute)
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
from agent.src.services.weather_service import WeatherService
from agent.src.services.search_service import SearchService

def start_betting_agent():
    """
    Initializes and starts the BettingAgent in an infinite loop.
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

    # ONE-SHOT EXECUTION: Execute only once, then exit
    # while True:  # DISABLED for single execution
    print("\n" + "="*50)
    print(f"--- STARTING ONE-SHOT EXECUTION: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
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
    temp_weather_service = WeatherService() if os.getenv('OPENWEATHERMAP_API_KEY') else None
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

        # --- Η υπάρχουσα λογική συναρμολόγησης και εκτέλεσης μπαίνει εδώ μέσα ---
        print("--- Assembling Agent Components ---")

        # Correctly initialize ContainerManager with error handling
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
            print(f"--- WARNING: Container manager initialization failed: {e}, continuing without it ---")
            container_manager = None

        # Correctly initialize other components
        rag_client = RAGClient(agent_id=agent_id, session_id=session_id, base_url="http://rag-api:32771")
        db = SQLiteDB(db_path="/app/agent/db/superior-agents.db")
        sensor = TradingSensor(
            eth_address=os.getenv("WALLET_ADDRESS", "0x0000000000000000000000000000000000000000"),
            infura_project_id=os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
            etherscan_api_key=os.getenv("ETHERSCAN_API_KEY", "mock_api_key")
        )
        genner = get_genner(backend="mock", stream_fn=None)  # Use mock backend for now

        # Use only the two required prompts
        prompts_dict = {
            "system_prompt": BettingPromptGenerator.get_default_prompts()["system_prompt"],
            "research_code_prompt_first": BettingPromptGenerator.get_default_prompts()["research_code_prompt_first"],
        }
        prompt_generator = BettingPromptGenerator(prompts=prompts_dict)

        # Initialize NewsService
        news_service = NewsService()
        
        # Initialize WalletService
        wallet_service = WalletService()
        
        # Initialize other services
        overtime_service = OvertimeService()
        the_odds_service = TheOddsService(os.getenv('THE_ODDS_API_KEY')) if os.getenv('THE_ODDS_API_KEY') else None
        weather_service = WeatherService() if os.getenv('OPENWEATHERMAP_API_KEY') else None
        search_service = SearchService()

        print(f"--- Initializing Betting Agent (ID: {agent_id}, Session: {session_id}) ---")

        # Get wallet balances for main agent initialization
        wallet_address = config.WALLET_ADDRESS
        eth_balance = wallet_service.get_eth_balance(wallet_address)
        wallet_balance = wallet_service.get_usdc_balance(wallet_address)
        
        # Display wallet balances at the start of each cycle
        print(f"\n--- Current Wallet Balances: ---")
        print(f"  - USDC.e: ${wallet_balance:.2f}")
        print(f"  - ETH: {eth_balance:.6f}")

        agent = BettingAgent(
            db=db,
            sensor=sensor,
            genner=genner,
            container_manager=container_manager,
            rag_client=rag_client,
            overtime_service=overtime_service,
            news_service=news_service,
            wallet_service=wallet_service,
            the_odds_service=the_odds_service,
            weather_service=weather_service,
            search_service=search_service,
            eth_balance=eth_balance
        )

        print("--- Betting Agent Initialized. Final Test: Overtime Service... ---")
        
        # Get raw data directly from overtime service first
        print("--- FETCHING RAW DATA FROM OVERTIME SERVICE ---")
        raw_markets = agent.overtime_service.get_sports_data()
        
        # Debug: Print raw data structure
        if raw_markets:
            import json
            print("--- RAW DATA STRUCTURE FROM OVERTIME API ---")
            print(f"Type: {type(raw_markets)}")
            if isinstance(raw_markets, dict):
                print(f"Keys: {list(raw_markets.keys())}")
                if len(raw_markets) > 0:
                    first_key = list(raw_markets.keys())[0]
                    print(f"First category ({first_key}) data:")
                    print(json.dumps(raw_markets[first_key], indent=2))
            elif isinstance(raw_markets, list) and len(raw_markets) > 0:
                print("First market data:")
                print(json.dumps(raw_markets[0], indent=2))
        
        # Get processed data directly (this already calls process_raw_market_data internally)
        processed_games = agent.get_sports_data()
        if processed_games:
            import json
            print("--- First 2 processed games for verification: ---")
            print(json.dumps(processed_games[:2], indent=2))
            print(f"--- SUCCESS: Fetched and processed {len(processed_games)} games. Agent intelligence layer is active. ---")

            # Call the new strategy function
            strategy_prompt = agent.formulate_betting_strategy(processed_games)

            # For now, we'll use the processed games as valid games
            # In a full implementation, this would be filtered based on strategy
            valid_games = processed_games[:10]  # Take first 10 games for testing
            
            # Manage bankroll to assign bet amounts using the real balance
            final_decisions = agent.manage_bankroll(valid_games, wallet_balance)

            if final_decisions:
                import json
                print("\n--- Final Decisions with Bet Amounts: ---")
                print(json.dumps(final_decisions[:5], indent=2)) # Print first 5 final decisions

                # Save each decision to the RAG memory
                for decision in final_decisions:
                    agent.save_decision_to_rag(decision)

                # Generate the code based on the final decisions
                executable_code = agent.generate_betting_code(final_decisions)
                if executable_code:
                    print("\n--- Generated Executable Code: ---")
                    print("------------------------------------")
                    print(executable_code)
                    print("------------------------------------")

                    # --- EXECUTION STAGE ---
                    if EXECUTE_ON_CHAIN and final_decisions:
                        print("\n--- GO FOR LAUNCH: EXECUTING ON-CHAIN TRANSACTIONS ---")

                        # Execute the code in the secure container
                        if agent.container_manager:
                            print("\n--- Handing code to ContainerManager for execution... ---")
                            execution_result = agent.container_manager.run_code_in_con(executable_code, "betting_execution")
                            
                            if execution_result.is_ok():
                                execution_output, reflected_code = execution_result.unwrap()
                                print("--- EXECUTION COMPLETE ---")
                                print(f"Execution Output: {execution_output}")
                                print("--- Reflected Code ---")
                                print(reflected_code)
                            else:
                                error_msg = execution_result.err()
                                print("--- EXECUTION FAILED ---")
                                print(f"Error: {error_msg}")
                        else:
                            print("--- EXECUTION HALTED: ContainerManager not available. ---")
                    elif not EXECUTE_ON_CHAIN:
                        print("\n--- SIMULATION MODE: On-chain execution is disabled. ---")
                    # --- END OF CYCLE ---

            print("\n--- Testing Wallet Service ---")
            try:
                # Refresh balances for testing
                current_eth_balance = wallet_service.get_eth_balance(wallet_address)
                current_usdc_balance = wallet_service.get_usdc_balance(wallet_address)
                print(f"--- SUCCESS: Wallet balances fetched successfully. ---")
                print(f"  - ETH Balance: {current_eth_balance:.6f} ETH")
                print(f"  - USDC.e Balance: {current_usdc_balance:.2f} USDC.e")
            except Exception as e:
                print(f"--- FAILURE: Could not fetch wallet balances. Error: {e} ---")

            print("\n--- Testing News Service ---")
            # We will test the news service with a well-known team
            test_team_name = "Manchester City"
            news_articles = agent.news_service.get_news_for_team(test_team_name)

            if news_articles is not None:
                import json
                print(f"--- SUCCESS: News Service fetched {len(news_articles)} articles for {test_team_name}. ---")
                # Print titles of fetched articles for verification
                for article in news_articles:
                    print(f"  - {article.get('title')}")
            else:
                print(f"--- FAILURE: News Service could not fetch articles for {test_team_name}. Check API key or service. ---")
        else:
            print("--- WARNING: No processed games found in the data. ---")

        # --- Τέλος της κύριας λογικής ---

    # --- FEEDBACK LOOP TEST DISABLED FOR PRODUCTION ---
    # Mock mode has been disabled for real trading
    
    # Real feedback loop: Check and update any pending bets
    agent.check_and_update_pending_bets()

    # ONE-SHOT EXECUTION: No sleep, exit after completion
    print(f"\n--- ONE-SHOT EXECUTION COMPLETE. Agent exiting. ---")

if __name__ == "__main__":
    start_betting_agent()
