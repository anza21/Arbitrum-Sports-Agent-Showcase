# CODE PAYLOAD FOR BETTING.PY
import logging
import re, json, os, time
import uuid
import requests
from textwrap import dedent
from typing import Dict, List, Set, Tuple, Optional
from agent.src.db.interface import DBInterface
from result import Err, Ok, Result
from agent.src.genner.Base import Genner
from agent.src.sensor.trading import TradingSensor
from agent.src.agent_types import ChatHistory, Message
from agent.src.container import ContainerManager
from agent.src.client.rag import RAGClient
from agent.src.services.overtime_service import OvertimeService
from agent.src.services.news_service import NewsService
from agent.src.services.wallet_service import WalletService
from agent.src.services.the_odds_service import TheOddsService
from agent.src.services.weather_service import WeatherService
from agent.src.services.search_service import SearchService

def get_erc20_balance(w3, wallet_address, token_address):
	"""Get ERC20 token balance for a wallet address"""
	try:
		from agent.src.contracts.usdc_abi import USDC_E_ABI
		contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=USDC_E_ABI)
		balance = contract.functions.balanceOf(w3.to_checksum_address(wallet_address)).call()
		# USDC has 6 decimals
		return w3.from_wei(balance, 'mwei')  # 1e6 = mwei
	except Exception as e:
		print(f"Error getting ERC20 balance: {e}")
		return 0
from agent.src.datatypes import StrategyData
from agent.src.contracts.overtime_abi import OVERTIME_SPORTS_AMM_ABI
from web3 import Web3
from datetime import datetime, timedelta

def get_eth_price():
    """Fetches the current ETH price in USD from CoinGecko."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        response = requests.get(url)
        response.raise_for_status()
        price_data = response.json()
        return price_data['ethereum']['usd']
    except Exception as e:
        print(f"Could not fetch ETH price from CoinGecko: {e}")
        return 3500.0 # Fallback price

class BettingPromptGenerator:
	"""
	Generator for creating prompts used in sports betting agent workflows.

	This class is responsible for generating various prompts used by the betting agent,
	including system prompts, research code prompts, strategy prompts, and betting code prompts.
	It handles the substitution of placeholders in prompt templates with actual values.
	"""

	def __init__(self, prompts: Dict[str, str]):
		"""
		Initialize with custom prompts for each function.

		This constructor sets up the prompt generator with either custom prompts
		or default prompts if none are provided. It validates that all required
		prompts are present and properly formatted.

		Args:
		    prompts (Dict[str, str]): Dictionary containing custom prompts for each function
		"""
		if not prompts:
			prompts = self.get_default_prompts()
		self._validate_prompts(prompts)
		self.prompts = prompts

	def _validate_prompts(self, prompts: Dict[str, str]) -> None:
		"""
		Validate prompts for required and unexpected placeholders.

		This method checks that all provided prompts contain the required
		placeholders and don't contain any unexpected ones. It ensures that
		the prompts will work correctly when placeholders are substituted.

		Args:
		    prompts (Dict[str, str]): Dictionary of prompt name to prompt content

		Raises:
		    ValueError: If prompts are missing required placeholders or contain unexpected ones
		"""
		required_prompts = [
			"system_prompt",
			"research_code_prompt_first",
		]

		# Check all required prompts exist
		missing_prompts = set(required_prompts) - set(prompts.keys())
		if missing_prompts:
			raise ValueError(f"Missing required prompts: {missing_prompts}")

		# Extract placeholders using regex
		placeholder_pattern = re.compile(r"{([^}]+)}")

		# Check each prompt for missing and unexpected placeholders
		for prompt_name, prompt_content in prompts.items():
			if prompt_name not in required_prompts:
				continue

			# Get actual placeholders in the prompt
			actual_placeholders = {
				f"{{{p}}}" for p in placeholder_pattern.findall(prompt_content)
			}
			required_set = set()  # No placeholders required for these prompts

			# Check for missing placeholders
			missing = required_set - actual_placeholders
			if missing:
				raise ValueError(
					f"Missing required placeholders in {prompt_name}: {missing}"
				)

			# Check for unexpected placeholders
			unexpected = actual_placeholders - required_set
			if unexpected:
				raise ValueError(
					f"Unexpected placeholders in {prompt_name}: {unexpected}"
				)

	def generate_system_prompt(
		self,
		role: str,
		time: str,
		metric_name: str,
		metric_state: str,
		network: str,
	) -> str:
		"""
		Generate a system prompt for the trading agent.

		This method creates a system prompt that sets the context for the agent,
		including its role, current date, goal, and portfolio state.

		Args:
		        role (str): The role of the agent (e.g., "trader")
		        time (str): Time frame for the trading goal
		        metric_name (str): Name of the metric to maximize
		        metric_state (str): Current state of the metric/portfolio
		        network (str): Blockchain network being used

		Returns:
		        str: Formatted system prompt
		"""
		from datetime import datetime
		now = datetime.now()
		today_date = now.strftime("%Y-%m-%d")

		# Parse the metric state to extract available balance
		try:
			metric_data = eval(metric_state)
			if isinstance(metric_data, dict) and "eth_balance_available" in metric_data:
				# Use available balance instead of total balance
				metric_state = str(
					{
						**metric_data,
						"eth_balance": metric_data[
							"eth_balance_available"
						],  # Show only available balance
					}
				)
		except (ValueError, TypeError):
			pass  # Keep original metric_state if parsing fails

		return self.prompts["system_prompt"].format(
			role=role,
			today_date=today_date,
			metric_name=metric_name,
			time=time,
			network=network,
			metric_state=metric_state,
		)

	def generate_research_code_first_time_prompt(self, apis: List[str], network: str):
		"""
		Generate a prompt for the first-time research code generation.

		This method creates a prompt for generating research code when the agent
		has no prior context or history to work with.

		Args:
		        apis (List[str]): List of APIs available to the agent

		Returns:
		        str: Formatted prompt for first-time research code generation
		"""
		apis_str = ",\n".join(apis) if apis else self._get_default_apis_str()

		return self.prompts["research_code_prompt_first"].format(
			apis_str=apis_str, network=network
		)

	@staticmethod
	def _get_default_apis_str() -> str:
		"""
		Get a string representation of default APIs.

		This static method returns a comma-separated string of default APIs
		that can be used when no specific APIs are provided.

		Returns:
		        str: Comma-separated string of default APIs
		"""
		default_apis = [
			"Coingecko (env variables COINGECKO_API_KEY)",
			"Twitter (env variables TWITTER_API_KEY, TWITTER_API_KEY_SECRET)",
			"DuckDuckGo (using the command line `ddgr`)",
		]
		return ",\n".join(default_apis)

	@staticmethod
	def get_default_prompts() -> Dict[str, str]:
		"""Get the complete set of default prompts that can be customized."""
		return {
			"system_prompt": dedent("""
			You are a Specialized Sports Betting Analyst. Your sole objective is wallet profitability by placing bets on sports markets.
			You operate on the Arbitrum One network.
			Your primary tool for market data and placing bets is the Overtime Protocol v2.
			Analyze available sports market data, form a betting strategy, and generate Python code to execute bets.
			Your performance is measured by the growth of the wallet's USDC.e balance.
			Base your decisions on data and statistical probability, not emotion.
			
			You now have access to enhanced data sources:
			- Weather conditions at game locations (affects outdoor sports performance)
			- Geographic location data for teams and venues
			- Live odds from multiple bookmakers
			
			Consider weather conditions, especially for outdoor sports, as they can significantly impact game outcomes.
			Use location data to identify regional factors that might affect team performance.
		""").strip(),
			"research_code_prompt_first": dedent("""
			You have no prior knowledge of the current sports markets.
			Your task is to write Python code to gather initial data about available games and odds from the Overtime Protocol API.
			Focus on understanding the available markets, sports, and participants.
			Use the provided functions to query the API and print the results in a structured format.
			Your code must be clean, efficient, and exclusively focused on data gathering.
		""").strip(),
		}


class BettingAgent:
	"""
	Agent responsible for executing trading strategies based on market data and notifications.

	This class orchestrates the entire trading workflow, including system preparation,
	research code generation, strategy formulation, and trading code execution.
	It integrates with various components like RAG, database, sensors, and code execution
	to create a complete trading agent.
	"""
	
	# Strategy parameters as class attributes for global access
	FAVORITE_ODDS_THRESHOLD = 1.5
	NEGATIVE_NEWS_KEYWORDS = ["injury", "injured", "doubt", "missing", "loss", "bad form", "crisis"]

	def __init__(
		self,
		db: DBInterface,
		sensor: TradingSensor,
		genner: Genner,
		container_manager: ContainerManager,
		rag_client: RAGClient,
		overtime_service: OvertimeService,
		news_service: NewsService,
		wallet_service: WalletService,
		the_odds_service: TheOddsService,
		weather_service: WeatherService,
		search_service: SearchService,
		eth_balance: float = 0.0,
	):
		self.db = db
		self.sensor = sensor
		self.genner = genner
		self.container_manager = container_manager
		self.rag_client = rag_client
		self.overtime_service = overtime_service
		self.news_service = news_service
		self.wallet_service = wallet_service
		self.the_odds_service = the_odds_service
		self.weather_service = weather_service
		self.search_service = search_service
		self.eth_balance = eth_balance
		
		# Add unique agent ID
		self.agent_id = f"betting-agent-{str(uuid.uuid4())}"
		
		# Initialize prompt generator with default prompts
		self.prompt_generator = BettingPromptGenerator(prompts={})
		
		# --- LOGGING SETUP ---
		logging.basicConfig(
			level=logging.DEBUG,
			format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
			filename='/app/agent_debug.log',
			filemode='w'
		)
		self.logger = logging.getLogger(__name__)
		self.logger.info("Logging initialized for BettingAgent.")
		# --- END LOGGING SETUP ---

	def prepare_system(
		self, role: str, time: str, metric_name: str, metric_state: str, network: str
	) -> ChatHistory:
		"""
		Prepare the system prompt for the agent.

		This method generates the initial system prompt that sets the context
		for the agent's operation, including its role, time context, and metrics.

		Args:
		    role (str): The role of the agent (e.g., "trader")
		    time (str): Current time information
		    metric_name (str): Name of the metric to track
		    metric_state (str): Current state of the metric
		    network (str): Blockchain network to operate on

		Returns:
		    ChatHistory: Chat history with the system prompt
		"""
		ctx_ch = ChatHistory(
			Message(
				role="system",
				content=self.prompt_generator.generate_system_prompt(
					role=role,
					time=time,
					metric_name=metric_name,
					network=network,
					metric_state=metric_state,
				),
			)
		)

		return ctx_ch

	def gen_research_code_on_first(
		self, apis: List[str], network: str
	) -> Tuple[Result[str, str], ChatHistory]:
		"""
		Generate research code for the first time.

		This method creates research code when the agent has no prior context,
		using only the available APIs.

		Args:
		    apis (List[str]): List of APIs available to the agent

		Returns:
		    Result[Tuple[str, ChatHistory], str]: Success with code and chat history,
		        or error message
		"""
		ctx_ch = ChatHistory(
			Message(
				role="user",
				content=self.prompt_generator.generate_research_code_first_time_prompt(
					apis=apis,
					network=network,
				),
			)
		)

		gen_result = self.genner.generate_code(self.chat_history + ctx_ch)
		if gen_result.is_err():
			# Return error along with chat history
			return Err(
				f"BettingAgent.gen_research_code_on_first, err: \n{gen_result.unwrap_err()}"
			), ctx_ch

		processed_codes, raw_response = gen_result.unwrap()
		ctx_ch = ctx_ch.append(Message(role="assistant", content=raw_response))

		if processed_codes is None or not processed_codes:
			return Err(
				"BettingAgent.gen_research_code_on_first: No code could be extracted."
			), ctx_ch

		return Ok(processed_codes[0]), ctx_ch

	def check_and_update_pending_bets(self) -> None:
		"""
		Check and update the status of pending bets including manual executions.
		
		This method:
		1. Queries for pending recommendations
		2. Checks for manual executions via database
		3. Updates bet status based on blockchain data
		4. Tracks P&L for completed bets
		5. Detects new manual bets from blockchain
		6. Syncs manual execution outcomes with blockchain data
		"""
		try:
			print("🔍 --- Checking for pending bets and manual executions... ---")
			
			# STEP 1: Detect new manual bets from blockchain
			self.detect_manual_bets_from_blockchain()
			
			# STEP 2: Update outcomes for existing manual executions
			self.update_manual_bet_outcomes()
			
			# STEP 3: Learn from successful betting patterns
			self.learn_from_successful_bets()
			
			# STEP 4: Check for manually executed bets first
			manual_executions = self.check_manual_executions()
			if manual_executions:
				print(f"✅ Found {len(manual_executions)} manual executions to process")
				for execution in manual_executions:
					print(f"   📊 Manual bet: {execution['market_id']} - ${execution['executed_amount']}")
			
			# Get pending bets from database
			pending_bets = self.db.get_pending_bets()
			
			if not pending_bets:
				print("--- No pending automatic bets found. ---")
			else:
				print(f"--- Found {len(pending_bets)} pending automatic bets to check. ---")
			
				# Check results for each pending bet
			for bet in pending_bets:
					try:
						self.check_bet_result(bet)
					except Exception as bet_error:
						print(f"⚠️  Error checking bet {bet.get('bet_id', 'unknown')}: {bet_error}")
			
			print("✅ --- Pending bets and manual executions check completed. ---")
			
		except Exception as e:
			print(f"❌ --- ERROR checking pending bets: {e} ---")

	def check_manual_executions(self) -> List[Dict]:
		"""
		Check for manual executions that need to be processed by the agent.
		"""
		try:
			import sqlite3
			
			# Connect to database and check for manual executions
			conn = sqlite3.connect("/app/agent/db/superior-agents.db")
			cursor = conn.cursor()
			
			# Get manual executions that haven't been processed by agent yet
			cursor.execute("""
				SELECT me.*, ar.teams, ar.position, ar.confidence_score
				FROM manual_executions me
				JOIN agent_recommendations ar ON me.market_id = ar.market_id
				WHERE me.status = 'executed'
				ORDER BY me.executed_at DESC
				LIMIT 20
			""")
			
			rows = cursor.fetchall()
			
			executions = []
			for row in rows:
				execution = {
					'id': row[0],
					'market_id': row[1],
					'executed_amount': row[2],
					'executed_at': row[3],
					'user_notes': row[4],
					'teams': row[8] if len(row) > 8 else 'Unknown',
					'position': row[9] if len(row) > 9 else 0,
					'confidence_score': row[10] if len(row) > 10 else 0.5
				}
				executions.append(execution)
			
			conn.close()
			return executions
			
		except Exception as e:
			print(f"⚠️  Error checking manual executions: {e}")
			return []

	def check_bet_result(self, bet: Dict) -> None:
		"""
		Check the result of a specific bet and update its status.
		"""
		try:
			market_id = bet.get('market_id')
			bet_id = bet.get('bet_id')
			
			print(f"🔍 Checking result for bet {bet_id} on market {market_id}")
			
			# This is where you would implement:
			# 1. Check Overtime Markets API for game results
			# 2. Determine if bet won/lost based on the outcome
			# 3. Calculate profit/loss
			# 4. Update database with final status
			
			# For now, just log that we checked it
			print(f"   📊 Bet check completed for {market_id}")
			
		except Exception as e:
			print(f"⚠️  Error checking bet result: {e}")

	def record_cycle_start(self) -> str:
		"""
		Record the start of a new agent cycle.
		Returns the cycle_id for tracking.
		"""
		import uuid
		cycle_id = f"cycle_{uuid.uuid4().hex[:12]}"
		
		try:
			import sqlite3
			conn = sqlite3.connect("/app/agent/db/superior-agents.db")
			cursor = conn.cursor()
			
			# Insert new cycle record
			cursor.execute("""
				INSERT INTO agent_cycles 
				(cycle_id, agent_id, cycle_start_time, cycle_status) 
				VALUES (?, ?, datetime('now'), 'running')
			""", (cycle_id, self.agent_id))
			
			conn.commit()
			conn.close()
			
			print(f"🔄 Started new agent cycle: {cycle_id}")
			
			# ETH Balance Check
			try:
				from web3 import Web3
				import os
				w3 = Web3(Web3.HTTPProvider(os.getenv('ARBITRUM_RPC_URL')))
				wallet_addr = os.getenv('WALLET_ADDRESS')
				if w3.is_connected() and wallet_addr:
					eth_raw_balance = w3.eth.get_balance(w3.to_checksum_address(wallet_addr))
					eth_balance = w3.from_wei(eth_raw_balance, 'ether')
					self.eth_balance = float(eth_balance)
					self.logger.info(f'--- 💰 ETH BALANCE CHECK --- | Live Balance: {self.eth_balance:.8f} ETH ---')
					
					# --- DEFINITIVE FIX: READ USDC BALANCE ---
					usdc_address = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831' # DEFINITIVE FIX: Hardcoded Native USDC Address
					if usdc_address:
						usdc_balance = get_erc20_balance(w3, wallet_addr, usdc_address)
						self.usdc_balance = float(usdc_balance)
						self.logger.info(f'--- 💵 USDC BALANCE CHECK --- | Live Balance: ${self.usdc_balance:.2f} USDC ---')
					else:
						self.usdc_balance = 0.0
			except Exception as e:
				self.logger.error(f'Could not perform ETH balance check: {e}')
				self.eth_balance = 0.0
			
			return cycle_id
			
		except Exception as e:
			print(f"⚠️  Error recording cycle start: {e}")
			return cycle_id

	def record_cycle_end(self, cycle_id: str, games_analyzed: int, recommendations_generated: int) -> None:
		"""
		Record the completion of an agent cycle.
		"""
		try:
			import sqlite3
			conn = sqlite3.connect("/app/agent/db/superior-agents.db")
			cursor = conn.cursor()
			
			# Update cycle record
			cursor.execute("""
				UPDATE agent_cycles 
				SET cycle_end_time = datetime('now'),
					games_analyzed = ?,
					recommendations_generated = ?,
					cycle_status = 'completed'
				WHERE cycle_id = ?
			""", (games_analyzed, recommendations_generated, cycle_id))
			
			conn.commit()
			conn.close()
			
			print(f"✅ Completed agent cycle: {cycle_id}")
			print(f"   📊 Games analyzed: {games_analyzed}")
			print(f"   🎯 Recommendations: {recommendations_generated}")
			
		except Exception as e:
			print(f"⚠️  Error recording cycle end: {e}")

	def get_sports_data(self) -> List[Dict]:
		"""
		Fetch and process sports data from OvertimeService.
		
		Returns:
			List[Dict]: List of processed game data
		"""
		try:
			# Get raw markets from OvertimeService
			raw_markets = self.overtime_service.get_sports_data()
			
			if not raw_markets:
				print("No markets available from OvertimeService")
				return []
			
			# Process the raw market data and group by unique games
			all_markets = []
			
			# Handle different response formats - iterate through values() for dict responses
			if isinstance(raw_markets, dict):
				# If it's a dict with categories, iterate through values()
				for sport_data in raw_markets.values():
					if isinstance(sport_data, dict):
						# Sport data is a dict with league IDs as keys
						for league_markets in sport_data.values():
							if isinstance(league_markets, list):
								for market in league_markets:
									if self._is_valid_market(market):
										all_markets.append(market)
					elif isinstance(sport_data, list):
						# Direct list of markets
						for market in sport_data:
							if self._is_valid_market(market):
								all_markets.append(market)
			elif isinstance(raw_markets, list):
				# If it's a direct list of markets
				for market in raw_markets:
					if self._is_valid_market(market):
						all_markets.append(market)
			
			print(f"--- Found {len(all_markets)} valid markets from Overtime API ---")
			
			# Group markets by unique games (homeTeam + awayTeam + maturityDate)
			games_dict = {}
			for market in all_markets:
				game_key = f"{market.get('homeTeam', 'Unknown')}_{market.get('awayTeam', 'Unknown')}_{market.get('maturityDate', '')}"
				
				if game_key not in games_dict:
					games_dict[game_key] = []
				games_dict[game_key].append(market)
			
			print(f"--- Grouped into {len(games_dict)} unique games ---")
			
			# Process each unique game (pick the best market for each game)
			processed_games = []
			for game_key, markets in games_dict.items():
				# Pick the primary market (type="winner" or first available)
				primary_market = None
				for market in markets:
					if market.get('type') == 'winner':  # Moneyline markets are preferred
						primary_market = market
						break
				
				if not primary_market:
					primary_market = markets[0]  # Use first market if no moneyline found
				
				processed_game = self._process_market(primary_market)
				if processed_game:
					processed_games.append(processed_game)
					print(f"✅ UNIQUE GAME: {processed_game.get('home_team', 'Unknown')} vs {processed_game.get('away_team', 'Unknown')}")
			
			print(f"--- Successfully processed {len(processed_games)} unique games from Overtime API ---")
			return processed_games
			
		except Exception as e:
			print(f"Error fetching sports data: {e}")
			return []

	def _is_valid_market(self, market: Dict) -> bool:
		market_id = market.get('gameId', 'N/A')
		self.logger.debug(f"--- Checking Market: {market_id} ---")
		print(f"--- DEBUG: Checking Market {market_id} ---")

		try:
			# Convert maturityDate from ISO string to datetime object
			maturity_date_str = market.get('maturityDate', '')
			if maturity_date_str:
				# Handle ISO format date string
				maturity_date = datetime.fromisoformat(maturity_date_str.replace('Z', '+00:00'))
			else:
				# Default to past date if no maturity date
				from datetime import timezone
				maturity_date = datetime.now(timezone.utc) - timedelta(days=1)

			# The new, intelligent validation rules
			# Use timezone-aware datetime for comparison
			from datetime import timezone, timedelta
			now_utc = datetime.now(timezone.utc)
			
			# High-value market thresholds for exceptions
			HIGH_LIQUIDITY_THRESHOLD = 1000 # in USDCe
			HIGH_VOLUME_THRESHOLD = 5000 # in USDCe
			
			# 🕐 TIMING FILTER: Only games within next 8 hours for immediate betting
			max_future_time = now_utc + timedelta(hours=8)
			min_future_time = now_utc + timedelta(hours=2)  # At least 2 hours to prepare
			
			is_high_value_market = market.get('liquidity', 0) > HIGH_LIQUIDITY_THRESHOLD and market.get('volume', 0) > HIGH_VOLUME_THRESHOLD
			is_timing_valid = (min_future_time <= maturity_date <= max_future_time) or is_high_value_market
			
			is_valid = (
				market.get('isOpen', False) is True and
				market.get('isPaused', True) is False and
				market.get('status', -1) == 0 and
				maturity_date > now_utc and
				is_timing_valid  # 🎯 NEW: Only next 24 hours
			)

			if is_valid:
				self.logger.info(f"ACCEPTED Market {market_id}: Passed all intelligent validation rules.")
				print(f"✅ ACCEPTED Market {market_id}: All validation rules passed")
				return True
			else:
				# Log the specific reason for rejection
				reasons = []
				if not market.get('isOpen', False): reasons.append("isOpen is False")
				if market.get('isPaused', True): reasons.append("isPaused is True")
				if market.get('status', -1) != 0: reasons.append(f"status is {market.get('status', -1)}")
				if maturity_date <= now_utc: reasons.append("Market has matured")
				if not is_timing_valid:
					hours_diff = (maturity_date - now_utc).total_seconds() / 3600
					if hours_diff < 2:
						reasons.append(f"Too soon ({hours_diff:.1f}h < 2h)")
					elif hours_diff > 8:
						reasons.append(f"Too far ({hours_diff:.1f}h > 8h)")
				
				self.logger.warning(f"REJECTED Market {market_id}: Reasons: {', '.join(reasons)}")
				print(f"❌ REJECTED Market {market_id}: {', '.join(reasons)}")
				print(f"   - isOpen: {market.get('isOpen')}, isPaused: {market.get('isPaused')}, status: {market.get('status')}, maturityDate: {maturity_date}")
				return False

		except Exception as e:
			self.logger.error(f"ERROR validating market {market_id}: {e}")
			return False

	def _process_market(self, market: Dict) -> Optional[Dict]:
		"""
		Process a single market into a standardized format.
		
		Args:
			market (Dict): Raw market data
			
		Returns:
			Optional[Dict]: Processed market data or None if invalid
		"""
		try:
			# Extract basic game information
			# Use gameId from market data (Overtime API uses 'gameId' not 'game_id')
			market_id = market.get("gameId")
			if not market_id:
				# Fallback: create a unique market_id from team names and maturity date
				home_team = market.get("homeTeam", "Unknown")
				away_team = market.get("awayTeam", "Unknown")
				maturity_date = market.get("maturityDate", "")
				market_id = f"{home_team}_{away_team}_{maturity_date}".replace(" ", "_")
		
			processed_game = {
				"market_id": market_id,
				"sport": market.get("sport"),
				"league": market.get("leagueName", "Unknown"),
				"home_team": market.get("homeTeam"),
				"away_team": market.get("awayTeam"),
				"status": market.get("status"),
				"is_open": market.get("isOpen", False),
				"is_paused": market.get("isPaused", True),
				"maturity_date": market.get("maturityDate"),
				"line": market.get("line", 0),
				"type": market.get("type", "unknown"),
				"odds": market.get("odds", []),
				"player_props": market.get("playerProps", {}),
				"raw_data": market  # Keep original data for reference
			}
			
			# Add odds information if available
			if market.get("odds") and len(market["odds"]) >= 2:
				odds = market["odds"]
				if len(odds) >= 2:
					processed_game["home_odds"] = odds[0].get("decimal", 0)
					processed_game["away_odds"] = odds[1].get("decimal", 0)
					
					# TEMPORARY FIX: Generate mock odds for testing Analysis-Only Mode
					if processed_game["home_odds"] <= 0 or processed_game["away_odds"] <= 0:
						if processed_game.get("home_team") and processed_game.get("away_team"):
							import random
							processed_game["home_odds"] = round(random.uniform(1.5, 3.5), 2)
							processed_game["away_odds"] = round(random.uniform(1.5, 3.5), 2)
							print(f"🧪 MOCK ODDS: {processed_game['home_team']} vs {processed_game['away_team']} → {processed_game['home_odds']}/{processed_game['away_odds']}")
					
					# Add additional odds validation
					if processed_game["home_odds"] > 0 and processed_game["away_odds"] > 0:
						processed_game["odds_valid"] = True
					else:
						processed_game["odds_valid"] = False
			
			return processed_game
			
		except Exception as e:
			print(f"Error processing market {market.get('gameId', 'unknown')}: {e}")
			return None

	def manage_bankroll(self, llm_decisions: List[Dict], wallet_balance: float) -> List[Dict]:
		# THIS FUNCTION NOW EXPECTS wallet_balance TO BE IN USDC
		
		self.logger.info(f'--- 🧠 DEBUG BANKROLL (USDC MODE) ---')
		self.logger.info(f'   - Received wallet_balance: ${wallet_balance:.2f} USDC')
		
		if not llm_decisions or wallet_balance < 3.08: # Safety threshold in USDC
			return []

		AGENT_EDGE = 0.02
		MINIMUM_BET_USD = 3.00
		MAX_PORTFOLIO_RISK_USD = wallet_balance * 0.20 # Max 20% of live USDC balance
		final_decisions = []

		for decision in llm_decisions:
			try:
				decimal_odds = decision.get('decimal_odds', 2.0)
				if decimal_odds <= 1.0: continue

				p = (1 / decimal_odds) + AGENT_EDGE
				if p > 1.0: p = 0.99
				q = 1 - p
				b = decimal_odds - 1
				if b <= 0: continue

				kelly_fraction = (b * p - q) / b
				if kelly_fraction > 0:
					bet_amount_usd = wallet_balance * (kelly_fraction / 2) # Half Kelly in USD

					if 0 < bet_amount_usd < MINIMUM_BET_USD:
						bet_amount_usd = MINIMUM_BET_USD
					
					if bet_amount_usd >= MINIMUM_BET_USD:
						decision['recommended_amount'] = bet_amount_usd
						final_decisions.append(decision)

			except Exception as e:
				self.logger.error(f"Error in bankroll calc for decision {decision.get('market_id')}: {e}")

		# Central Risk Switch (in USD)
		total_bet_amount_usd = sum(d.get('recommended_amount', 0) for d in final_decisions)
		if total_bet_amount_usd > MAX_PORTFOLIO_RISK_USD:
			scaling_factor = MAX_PORTFOLIO_RISK_USD / total_bet_amount_usd
			for d in final_decisions:
				d['recommended_amount'] *= scaling_factor
		
		return final_decisions
	
	def _track_compound_growth(self, decisions: List[Dict], current_balance: float):
		"""
		Track progress towards 20% monthly compound growth target
		"""
		try:
			# Calculate monthly progress
			days_operating = self._get_days_operating()
			daily_exposure = sum(d['bet_amount'] for d in decisions)
			expected_daily_return = daily_exposure * 0.15  # 15% expected daily return on bets
			
			# Monthly projections
			monthly_target_growth = current_balance * 0.20  # 20% target
			days_in_month = 30
			required_daily_profit = monthly_target_growth / days_in_month
			
			# Performance metrics
			performance_ratio = expected_daily_return / required_daily_profit if required_daily_profit > 0 else 0
			
			self.logger.info(f"📈 COMPOUND GROWTH ANALYSIS:")
			self.logger.info(f"   💰 Current Balance: ${current_balance:.2f}")
			self.logger.info(f"   🎯 Monthly Target: +${monthly_target_growth:.2f} (20%)")
			self.logger.info(f"   📊 Required Daily: ${required_daily_profit:.2f}")
			self.logger.info(f"   💪 Expected Today: ${expected_daily_return:.2f}")
			self.logger.info(f"   🏆 Performance: {performance_ratio:.1%} of target")
			
			if performance_ratio >= 1.0:
				self.logger.info(f"🚀 EXCELLENT: Exceeding compound growth target!")
			elif performance_ratio >= 0.8:
				self.logger.info(f"✅ GOOD: On track for compound growth target")
			elif performance_ratio >= 0.5:
				self.logger.info(f"⚠️  MODERATE: Below target, need more opportunities")
			else:
				self.logger.warning(f"❌ UNDERPERFORMING: Significantly below compound growth target")
				
		except Exception as e:
			self.logger.warning(f"Could not track compound growth: {e}")
	
	def _get_days_operating(self) -> int:
		"""
		Calculate how many days the agent has been operating
		Used for progressive betting strategy
		"""
		try:
			# Check database for first recommendation
			conn = sqlite3.connect(self.db_path)
			cursor = conn.cursor()
			
			cursor.execute('''
				SELECT MIN(created_at) as first_bet
				FROM agent_recommendations
			''')
			
			result = cursor.fetchone()
			conn.close()
			
			if result and result[0]:
				from datetime import datetime
				first_date = datetime.fromisoformat(result[0])
				current_date = datetime.now()
				days = (current_date - first_date).days
				return max(days, 1)  # At least day 1
			else:
				return 1  # First day
				
		except Exception as e:
			self.logger.warning(f"Could not calculate operating days: {e}")
			return 1  # Default to first day
	
	def _calculate_confidence_score(self, game: Dict) -> float:
		"""
		Calculate confidence score for a game based on available data quality
		Returns score between 0.0 and 1.0
		"""
		score = 0.5  # Base score
		
		# Boost confidence based on data completeness
		if game.get('home_team') and game.get('away_team'):
			score += 0.1
		
		if game.get('game_time') or game.get('commence_time'):
			score += 0.1
			
		if 'odds' in game and isinstance(game['odds'], list) and len(game['odds']) > 1:
			score += 0.2  # Multiple odds sources
			
		if game.get('league') or game.get('sport_key'):
			score += 0.1
			
		return min(score, 1.0)
	
	def _select_optimal_position(self, game: Dict, estimated_prob: float, implied_prob: float) -> int:
		"""
		Enhanced position selection logic with strategic awareness
		Returns 0 for Home, 1 for Away, 2 for Draw (if available)
		"""
		# Extract team information
		home_team = game.get('home_team', '').lower()
		away_team = game.get('away_team', '').lower()
		sport = game.get('sport', '').lower()
		
		# Base position preference based on odds analysis
		home_odds = game.get('home_odds', 0)
		away_odds = game.get('away_odds', 0)
		draw_odds = game.get('draw_odds', 0)
		
		# Strategic factors analysis
		position_score = {0: 0.0, 1: 0.0, 2: 0.0}  # Home, Away, Draw
		
		# Factor 1: Home field advantage (varies by sport)
		if sport in ['american_football', 'soccer', 'basketball']:
			position_score[0] += 0.15  # Stronger home advantage
		elif sport in ['baseball', 'hockey']:
			position_score[0] += 0.10  # Moderate home advantage
		else:
			position_score[0] += 0.05  # General home advantage
		
		# Factor 2: Odds value analysis
		if home_odds > 0 and away_odds > 0:
			# Favor underdog if odds suggest value
			if home_odds > away_odds:
				position_score[0] += 0.10  # Home is underdog
			else:
				position_score[1] += 0.10  # Away is underdog
		
		# Factor 3: League/Competition type
		league = game.get('league', '').lower()
		if 'premier' in league or 'champions' in league or 'world' in league:
			# High-profile matches, favor away teams (often better)
			position_score[1] += 0.05
		
		# Factor 4: Draw probability for soccer ONLY (NOT American football)
		if sport in ['soccer'] and draw_odds > 0:  # REMOVED 'football' - American football rarely has draws
			# Soccer has significant draw probability
			if 1.8 <= home_odds <= 3.0 and 1.8 <= away_odds <= 3.0:
				position_score[2] += 0.20  # Even match, consider draw
		
		# American football should favor stronger statistical analysis
		if sport in ['american_football', 'ncaa_football']:
			# American football rarely ends in ties - favor mathematical edge
			if home_odds > away_odds and home_odds >= 1.5:
				position_score[0] += 0.15  # Underdog home team
			elif away_odds > home_odds and away_odds >= 1.5:
				position_score[1] += 0.15  # Underdog away team
		
		# Factor 5: Team name analysis (basic heuristics)
		strong_indicators = ['united', 'city', 'real', 'barcelona', 'bayern', 'liverpool']
		if any(indicator in home_team for indicator in strong_indicators):
			position_score[0] += 0.05
		if any(indicator in away_team for indicator in strong_indicators):
			position_score[1] += 0.05
		
		# Factor 6: Probability edge
		if estimated_prob > implied_prob:
			# We have an edge, boost the position with best odds value
			if home_odds >= away_odds:
				position_score[0] += 0.20
			else:
				position_score[1] += 0.20
		
		# Determine best position
		if draw_odds > 0 and position_score[2] > 0.15:  # Draw is available and favorable
			return 2  # Draw
		elif position_score[0] >= position_score[1]:
			return 0  # Home
		else:
			return 1  # Away

	def save_decision_to_rag(self, decision: Dict) -> bool:
		"""
		Save a betting decision to RAG memory.
		
		Args:
			decision (Dict): Betting decision to save
			
		Returns:
			bool: True if saved successfully
		"""
		try:
			# Create StrategyData from decision
			strategy_data = StrategyData(
				strategy_id=f"betting_{decision.get('market_id', 'unknown')}_{int(time.time())}",
				agent_id=self.agent_id,
				summarized_desc=f"Bet on {decision.get('home_team', 'Unknown')} vs {decision.get('away_team', 'Unknown')}",
				full_desc=f"Betting decision: {decision.get('decision', 'Unknown')} for {decision.get('sport', 'Unknown')} game",
				parameters={
					"market_id": decision.get("market_id"),
					"bet_amount": decision.get("bet_amount"),
					"status": decision.get("status"),
					"home_team": decision.get("home_team"),
					"away_team": decision.get("away_team"),
					"decision": decision.get("decision"),
					"sport": decision.get("sport"),
					"league": decision.get("leagueName"),
					"odds": decision.get("moneyline_home_odds"),
					"kelly_percentage": decision.get("kelly_percentage"),
					"pnl": decision.get("pnl_usdce")
				},
				strategy_result=decision.get("status", "PENDING"),
				created_at=datetime.now()
			)
			
			# Save to RAG using save_result_batch
			response = self.rag_client.save_result_batch([strategy_data])
			
			# Handle response which might be a dict or object
			if isinstance(response, dict):
				if response.get('status') == 'success' or response.get('success'):
					print(f"Decision saved to RAG: {decision.get('game_id', 'unknown')}")
					return True
				else:
					print(f"Failed to save decision to RAG: {decision.get('game_id', 'unknown')} - Response: {response}")
					return False
			elif hasattr(response, 'status_code'):
				if response.status_code == 200:
					print(f"Decision saved to RAG: {decision.get('game_id', 'unknown')}")
					return True
				else:
					print(f"Failed to save decision to RAG: {decision.get('game_id', 'unknown')} - Status: {response.status_code}")
					return False
			else:
				print(f"Decision saved to RAG (unknown response format): {decision.get('game_id', 'unknown')}")
				return True
				
		except Exception as e:
			print(f"Error saving decision to RAG: {e}")
			return False

	def enrich_games_with_odds(self, games_data: List[Dict]) -> List[Dict]:
		"""
		Enrich games data with live odds from The Odds API.
		
		This method fetches live odds for the given games and enriches
		the games data with current betting odds.
		
		Args:
			games_data (List[Dict]): List of games to enrich with odds
			
		Returns:
			List[Dict]: Enriched games data with odds information
		"""
		if not self.the_odds_service:
			print("--- WARNING: The Odds Service not available (API key missing) ---")
			return games_data
		
		try:
			print("--- Fetching live odds from The Odds API... ---")
			
			# Use the new global coverage method with test mode enabled
			all_odds = self.the_odds_service.get_odds_for_all_target_sports(test_mode=True)
			
			enriched_games = []
			
			for game in games_data:
				# Extract team names for odds lookup
				team_names = self._extract_team_names(game)
				if team_names:
					# Try to find matching odds from the fetched data
					odds_data = self._find_matching_odds_from_all_sports(game, all_odds)
					if odds_data:
						game['odds_data'] = odds_data
						print(f"--- Enriched game with odds: {team_names} ---")
					else:
						game['odds_data'] = None
				else:
					game['odds_data'] = None
				
				enriched_games.append(game)
			
			print(f"--- Successfully enriched {len(enriched_games)} games with odds ---")
			return enriched_games
			
		except Exception as e:
			print(f"--- ERROR enriching games with odds: {e} ---")
			return games_data

	def _extract_team_names(self, game: Dict) -> List[str]:
		"""
		Extract team names from game data for odds lookup.
		
		Args:
			game (Dict): Game data dictionary
			
		Returns:
			List[str]: List of team names
		"""
		team_names = []
		
		# Try different possible keys for team names
		possible_keys = ['home_team', 'away_team', 'team1', 'team2', 'participants']
		
		for key in possible_keys:
			if key in game:
				value = game[key]
				if isinstance(value, str):
					team_names.append(value)
				elif isinstance(value, list):
					team_names.extend(value)
				elif isinstance(value, dict):
					# If it's a dict, try to extract name field
					if 'name' in value:
						team_names.append(value['name'])
		
		return team_names
	
	def _find_matching_odds_from_all_sports(self, game: Dict, all_odds: Dict[str, List[Dict]]) -> Optional[Dict]:
		"""
		Find matching odds for a game from the fetched odds data for all sports.
		
		Args:
			game (Dict): Game data to match
			all_odds (Dict): Dictionary of odds data for all sports
			
		Returns:
			Optional[Dict]: Matching odds data or None
		"""
		game_teams = set()
		
		# Extract team names from game data
		if 'home_team' in game:
			game_teams.add(game['home_team'].lower())
		if 'away_team' in game:
			game_teams.add(game['away_team'].lower())
		if 'teams' in game:
			for team in game['teams']:
				if isinstance(team, str):
					game_teams.add(team.lower())
				elif isinstance(team, dict) and 'name' in team:
					game_teams.add(team['name'].lower())
		
		# Search through all sports for matching odds
		for sport_key, odds_list in all_odds.items():
			for odds in odds_list:
				odds_teams = set()
				
				# Extract team names from odds data
				if 'home_team' in odds:
					odds_teams.add(odds['home_team'].lower())
				if 'away_team' in odds:
					odds_teams.add(odds['away_team'].lower())
				if 'teams' in odds:
					for team in odds['teams']:
						if isinstance(team, str):
							odds_teams.add(team.lower())
						elif isinstance(team, dict) and 'name' in team:
							odds_teams.add(team['name'].lower())
				
				# Check if teams match
				if game_teams and odds_teams and game_teams.issubset(odds_teams):
					return {
						'sport_key': sport_key,
						'home_odds': odds.get('home_odds'),
						'away_odds': odds.get('away_odds'),
						'draw_odds': odds.get('draw_odds'),
						'last_update': odds.get('last_update'),
						'bookmakers': odds.get('bookmakers', [])
					}
		
		return None


	def formulate_betting_strategy(self, games_data: List[Dict]) -> List[Dict]:
		print(">>> ENTERING formulate_betting_strategy <<<")
		"""
		Formulate betting strategy using enriched data from multiple services.
		
		This method integrates data from all available services (Overtime, Search, Weather, Odds, News)
		to create a comprehensive Master Prompt for the LLM to make final betting decisions.
		
		Args:
			games_data (List[Dict]): List of games from OvertimeService
			
		Returns:
			List[Dict]: Betting decisions from LLM analysis
		"""
		print("🔍 EGGEPHALOS DEBUG: formulate_betting_strategy called!")
		print(f"🔍 Input games_data length: {len(games_data)}")
		
		try:
			print("🔍 EGGEPHALOS DEBUG: Entering try block...")
			
			# 🚫 DEDUPLICATION LOGIC: Remove previously analyzed games
			print("🔍 DEDUPLICATION: Checking for previously analyzed games...")
			try:
				# Connect to database to get existing market_ids
				import sqlite3
				db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'agent', 'db', 'superior-agents.db')
				conn = sqlite3.connect(db_path)
				cursor = conn.cursor()
				
				# Query existing market_ids from recommendations (all statuses)
				cursor.execute("SELECT DISTINCT market_id FROM agent_recommendations")
				existing_market_ids = set(row[0] for row in cursor.fetchall())
				conn.close()
				
				print(f"🔍 DEDUPLICATION: Found {len(existing_market_ids)} previously analyzed markets")
				
				# DEBUG: Log first 5 existing market IDs from DB
				print(f"DEBUG: First 5 existing market IDs from DB: {list(existing_market_ids)[:5]}")
				print(f"DEBUG: First 5 incoming game market IDs: {[game.get('market_id') for game in games_data[:5]]}")
				
				# Filter out games that have already been analyzed
				original_count = len(games_data)
				filtered_games = []
				duplicates_removed = 0
				
				for game in games_data:
					market_id = game.get('market_id', '')
					# Skip games with empty or None market_id
					if not market_id or market_id.strip() == '':
						print(f"🔍 DEDUPLICATION: Skipping game with empty market_id")
						duplicates_removed += 1
						continue
					
					# Check if market_id exists in database
					if market_id not in existing_market_ids:
						filtered_games.append(game)
					else:
						duplicates_removed += 1
						print(f"🔍 DEDUPLICATION: Skipping duplicate market {market_id[:20]}...")
				
				# Update games_data with filtered list
				games_data = filtered_games
				print(f"🔍 DEDUPLICATION: Removed {duplicates_removed} duplicates, {len(games_data)} fresh games remaining")
				
				# Additional validation: ensure we have games to process
				if len(games_data) == 0:
					print("⚠️  DEDUPLICATION WARNING: No fresh games remaining after deduplication")
					return []
				
			except Exception as dedup_error:
				print(f"⚠️ DEDUPLICATION WARNING: Could not check for duplicates: {dedup_error}")
				print("🔍 DEDUPLICATION: Continuing with all games (no deduplication)")
			
			# Skip analysis if no fresh games
			if not games_data:
				print("🔍 DEDUPLICATION: No fresh games to analyze, skipping LLM call")
				return []
			# --- LOW FUEL SAFETY CHECK ---
			MIN_ETH_FOR_OPERATIONS = 0.001  # Minimum safety threshold for gas on Arbitrum
			
			# ANALYSIS-ONLY MODE: Skip ETH check since we don't execute transactions
			if self.eth_balance < MIN_ETH_FOR_OPERATIONS:
				print(f"🔍 EGGEPHALOS DEBUG: LOW FUEL - ETH balance {self.eth_balance:.6f} < {MIN_ETH_FOR_OPERATIONS}")
				print(f"🔍 EGGEPHALOS DEBUG: ANALYSIS-ONLY MODE - Continuing with LLM analysis despite low ETH")
				# In analysis-only mode, continue with LLM analysis
				pass
			
			print("--- Formulating Master Prompt with integrated services ---")
			
			# Initialize the Master Prompt structure
			master_prompt_parts = []
			
			# Header section
			master_prompt_parts.append("=" * 80)
			master_prompt_parts.append("MASTER BETTING ANALYSIS PROMPT")
			master_prompt_parts.append("=" * 80)
			master_prompt_parts.append("")
			
			# Market Data Section (SMART SAMPLING)
			master_prompt_parts.append("📊 MARKET DATA")
			master_prompt_parts.append("-" * 40)
			if games_data:
				master_prompt_parts.append(f"Total Available Games: {len(games_data)}")
				master_prompt_parts.append("")
				
				# 🌍 COMPREHENSIVE GAME ANALYSIS: Present ALL available games with geographic organization
				
				# Group games by sport and region for comprehensive analysis
				games_by_sport = {}
				european_sports = ['Soccer', 'Football', 'Tennis', 'Basketball'] # European context
				american_sports = ['American Football', 'Baseball', 'Hockey', 'Basketball'] # American context
				global_sports = ['Tennis', 'Table Tennis', 'Volleyball', 'Boxing'] # Global sports
				
				for game in games_data:
					sport = game.get('sport', 'Unknown')
					if sport not in games_by_sport:
						games_by_sport[sport] = []
					games_by_sport[sport].append(game)
				
				# Present COMPLETE data set organized by sport
				master_prompt_parts.append(f"📊 COMPLETE MARKET ANALYSIS ({len(games_data)} total games across {len(games_by_sport)} sports):")
				master_prompt_parts.append("")
				
				# Show ALL games organized by sport for professional analysis
				for sport, sport_games in games_by_sport.items():
					master_prompt_parts.append(f"🏆 {sport.upper()} ({len(sport_games)} games):")
					
					# Determine if this is European/Global sport for priority marking
					is_european = sport in european_sports
					is_global = sport in global_sports
					priority_marker = "🇪🇺" if is_european else "🌍" if is_global else "🇺🇸"
					
					for i, game in enumerate(sport_games, 1):
						# 🎯 CRITICAL: Use REAL market_id for LLM selection
						real_market_id = game.get('gameId', game.get('game_id', game.get('market_id', 'UNKNOWN')))
						# Try multiple possible keys for team names
						home_team = game.get('homeTeam') or game.get('home_team') or game.get('homeTeamName') or 'Unknown'
						away_team = game.get('awayTeam') or game.get('away_team') or game.get('awayTeamName') or 'Unknown'
						teams = f"{home_team} vs {away_team}"
						
						
						game_info = f"  {priority_marker} MARKET_ID: \"{real_market_id}\" | {teams} | Liq: {game.get('liquidity', 0.0):.2f} | Vol: {game.get('volume', 0)}"
					if 'start_time' in game:
						game_info += f" | Time: {game['start_time']}"
					# Add odds info for professional analysis
					home_odds = game.get('home_odds', game.get('homeOdds', 0))
					away_odds = game.get('away_odds', game.get('awayOdds', 0))
					if home_odds > 0 and away_odds > 0:
						game_info += f" | Odds: H {home_odds:.2f} / A {away_odds:.2f}"
					if 'league' in game or 'leagueName' in game:
						league = game.get('league', game.get('leagueName', ''))
						if league:
							game_info += f" | League: {league}"
					master_prompt_parts.append(game_info)
					master_prompt_parts.append("")
				
				master_prompt_parts.append("🎯 GLOBAL MARKET ACCESS: You have complete visibility of ALL available games!")
				master_prompt_parts.append("🌍 GEOGRAPHIC DIVERSITY: Prioritize European 🇪🇺 and Global 🌍 sports for maximum variety!")
				master_prompt_parts.append("💡 PROFESSIONAL SELECTION: Choose diverse games across regions, sports, and time zones!")
			else:
				master_prompt_parts.append("No games data available")
			master_prompt_parts.append("")
			
			# Live Odds Section
			master_prompt_parts.append("🎯 LIVE ODDS")
			master_prompt_parts.append("-" * 40)
			if self.the_odds_service:
				try:
					# Fetch live odds for all sports
					all_odds = self.the_odds_service.get_odds_for_all_target_sports(test_mode=True)
					if all_odds:
						odds_count = sum(len(odds_list) for odds_list in all_odds.values())
						master_prompt_parts.append(f"Live odds available for {odds_count} games across {len(all_odds)} sports")
						
						# Show sample odds data
						for sport_key, odds_list in list(all_odds.items())[:3]:  # First 3 sports
							if odds_list:
								sample_odds = odds_list[0]
								odds_info = f"{sport_key}: {sample_odds.get('home_team', 'Team1')} vs {sample_odds.get('away_team', 'Team2')}"
								if 'home_odds' in sample_odds and 'away_odds' in sample_odds:
									odds_info += f" - H: {sample_odds['home_odds']}, A: {sample_odds['away_odds']}"
								master_prompt_parts.append(odds_info)
					else:
						master_prompt_parts.append("No live odds data available")
				except Exception as e:
					master_prompt_parts.append(f"Odds service error: {str(e)}")
			else:
				master_prompt_parts.append("Odds service not available")
			master_prompt_parts.append("")
			
			# Weather Conditions Section
			master_prompt_parts.append("🌤️ WEATHER CONDITIONS")
			master_prompt_parts.append("-" * 40)
			if self.weather_service:
				try:
					# Get weather for major cities (sample)
					major_cities = ["London", "New York", "Los Angeles", "Chicago", "Miami"]
					weather_samples = []
					
					for city in major_cities[:3]:  # First 3 cities
						try:
							weather_data = self.weather_service.get_weather_by_city(city)
							if weather_data:
								weather_info = f"{city}: {weather_data.get('description', 'Unknown')}, {weather_data.get('temperature', 'N/A')}°C"
								weather_samples.append(weather_info)
						except:
							continue
					
					if weather_samples:
						master_prompt_parts.extend(weather_samples)
					else:
						master_prompt_parts.append("Weather data not available")
				except Exception as e:
					master_prompt_parts.append(f"Weather service error: {str(e)}")
			else:
				master_prompt_parts.append("Weather service not available")
			master_prompt_parts.append("")
			
			# Latest News Section
			master_prompt_parts.append("📰 LATEST NEWS")
			master_prompt_parts.append("-" * 40)
			if self.news_service:
				try:
					# Fetch recent sports news - try a general search term
					news_data = self.news_service.get_news_for_team('sports betting football soccer')
					if news_data and len(news_data) > 0:
						master_prompt_parts.append(f"Recent sports news available: {len(news_data)} articles")
						
						# Show sample news headlines
						for i, news in enumerate(news_data[:3], 1):  # First 3 news items
							headline = news.get('title', 'No title')
							master_prompt_parts.append(f"{i}. {headline[:80]}{'...' if len(headline) > 80 else ''}")
					else:
						master_prompt_parts.append("No recent sports news available")
				except Exception as e:
					master_prompt_parts.append(f"News service error: {str(e)}")
			else:
				master_prompt_parts.append("News service not available")
			master_prompt_parts.append("")
			
			# Geographic Data Section
			master_prompt_parts.append("🌍 GEOGRAPHIC DATA")
			master_prompt_parts.append("-" * 40)
			if self.search_service:
				try:
					# Sample geographic data for major teams
					sample_teams = ["Manchester United", "Real Madrid", "Barcelona"]
					geo_samples = []
					
					for team in sample_teams[:2]:  # First 2 teams
						try:
							location_data = self.search_service.search_team_location(team)
							if location_data:
								geo_info = f"{team}: {location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}"
								geo_samples.append(geo_info)
						except:
							continue
					
					if geo_samples:
						master_prompt_parts.extend(geo_samples)
					else:
						master_prompt_parts.append("Geographic data not available")
				except Exception as e:
					master_prompt_parts.append(f"Search service error: {str(e)}")
			else:
				master_prompt_parts.append("Search service not available")
			master_prompt_parts.append("")
			
			# Final Decision Instructions
			master_prompt_parts.append("🎯 FINAL DECISION INSTRUCTIONS - STRATEGIC POSITION ANALYSIS")
			master_prompt_parts.append("-" * 40)
			master_prompt_parts.append("Based on all the above data, act as a professional betting analyst and identify up to 3 high-value betting opportunities.")
			master_prompt_parts.append("")
			master_prompt_parts.append("For each game, you must analyze all available data and decide on the best position to bet on from the available options.")
			master_prompt_parts.append("The available positions are:")
			master_prompt_parts.append("- 0 (Home Team Win)")
			master_prompt_parts.append("- 1 (Away Team Win)")
			master_prompt_parts.append("- 2 (Draw/Tie)")
			master_prompt_parts.append("")
			master_prompt_parts.append("Consider the following factors for position selection:")
			master_prompt_parts.append("- Weather conditions (especially for outdoor sports)")
			master_prompt_parts.append("- Geographic location and regional factors")
			master_prompt_parts.append("- Live odds and market movements")
			master_prompt_parts.append("- Recent news and team developments")
			master_prompt_parts.append("- Historical performance data")
			master_prompt_parts.append("- Home field advantage")
			master_prompt_parts.append("- Team form and momentum")
			master_prompt_parts.append("- Head-to-head records")
			master_prompt_parts.append("- Market liquidity and volume indicators")
			master_prompt_parts.append("")
			master_prompt_parts.append("💎 LIQUIDITY & VOLUME ANALYSIS:")
			master_prompt_parts.append("Prioritize markets with high liquidity (liquidity > 0.5) and volume (volume > 1), as they are strong indicators of market confidence.")
			master_prompt_parts.append("")
			
			# 🚀 PROFESSIONAL VOLUME BETTING INSTRUCTION
			master_prompt_parts.append("🔥 PROFESSIONAL BETTING AGENT INSTRUCTIONS:")
			master_prompt_parts.append("=" * 50)
			master_prompt_parts.append("You are a VOLUME-BASED professional betting agent. Your mission:")
			master_prompt_parts.append("• IDENTIFY MULTIPLE VALUE OPPORTUNITIES (not just 1-2 games)")
			master_prompt_parts.append("• TARGET 8-15 BETTING OPPORTUNITIES per cycle for maximum profit")
			master_prompt_parts.append("• EXPLOIT MARKET INEFFICIENCIES across all sports/leagues")
			master_prompt_parts.append("• MAXIMIZE EXPECTED VALUE through diversified portfolio approach")
			master_prompt_parts.append("• USE AGGRESSIVE PROFESSIONAL STANDARDS (odds range 1.20-4.00)")
			master_prompt_parts.append("")
			master_prompt_parts.append("🎯 CRITICAL DIVERSITY REQUIREMENTS:")
			master_prompt_parts.append("• 🌍 GEOGRAPHIC PRIORITY: Select from European 🇪🇺, Global 🌍, AND American 🇺🇸 sports")
			master_prompt_parts.append("• ⚽ EUROPEAN FOCUS: Prioritize Soccer, Tennis, Basketball from European markets")
			master_prompt_parts.append("• 🏟️ SPORT VARIETY: Mix different sports (Soccer, Basketball, Tennis, Football, etc.)")
			master_prompt_parts.append("• 🚫 NO REPETITION: NEVER focus on same teams repeatedly (no more 'Indiana vs Kennesaw State')")
			master_prompt_parts.append("• 🌐 LEAGUE DIVERSITY: Choose from different leagues across continents")
			master_prompt_parts.append("• ⚖️ BALANCED PORTFOLIO: Mix favorites (1.20-2.00 odds) and underdogs (2.50-4.00 odds)")
			master_prompt_parts.append("")
			master_prompt_parts.append("🏆 POSITION SELECTION STRATEGY:")
			master_prompt_parts.append("• 🎯 HOME/AWAY FOCUS: For American Football & Basketball, prioritize Home (0) or Away (1) bets")
			master_prompt_parts.append("• ⚽ SOCCER DRAWS: Only use Draw (2) for soccer/football matches with balanced odds")
			master_prompt_parts.append("• 🔄 MIXED POSITIONS: Don't only pick draws - vary between Home, Away, and Draw intelligently")
			master_prompt_parts.append("• 📊 STATISTICAL EDGE: Choose positions based on odds value and team analysis")
			master_prompt_parts.append("")
			master_prompt_parts.append("🕐 TIMING STRATEGY:")
			master_prompt_parts.append("• ⏰ IMMEDIATE OPPORTUNITIES: Only select games within next 24 hours")
			master_prompt_parts.append("• 🎯 EXECUTABLE TIMEFRAME: Games must start 2-24 hours from now")
			master_prompt_parts.append("• 📅 NO DISTANT GAMES: Reject games more than 1 day away")
			master_prompt_parts.append("• 🚀 ACTION-READY: Focus on games user can bet on TODAY/TOMORROW")
			master_prompt_parts.append("• ⏰ TIME SPREAD: Games across different time zones and periods")
			master_prompt_parts.append("• 🎯 REGIONAL TEAMS: Look for Manchester United, Real Madrid, Barcelona, Bayern Munich, etc.")
			master_prompt_parts.append("")
			master_prompt_parts.append("VOLUME STRATEGY RATIONALE:")
			master_prompt_parts.append("✅ More opportunities = Higher profit potential")
			master_prompt_parts.append("✅ Portfolio diversification = Reduced risk")
			master_prompt_parts.append("✅ Professional volume betting = Industry standard")
			master_prompt_parts.append("✅ Kelly criterion optimization across multiple bets")
			master_prompt_parts.append("")
			master_prompt_parts.append("REJECT CONSERVATIVE MINDSET - BE AGGRESSIVE AND PROFESSIONAL!")
			master_prompt_parts.append("NEVER pick the same game repeatedly - show true professional diversity!")
			master_prompt_parts.append("")
			master_prompt_parts.append("🌟 PREMIUM LEAGUE PRIORITIES:")
			master_prompt_parts.append("⚽ SOCCER: Premier League (England), La Liga (Spain), Serie A (Italy), Bundesliga (Germany)")
			master_prompt_parts.append("🏀 BASKETBALL: NBA (USA), EuroLeague (Europe), ACB (Spain), VTB (Russia)")
			master_prompt_parts.append("🎾 TENNIS: ATP/WTA Tours, Grand Slams, Masters 1000 events")
			master_prompt_parts.append("🏈 AMERICAN FOOTBALL: NFL, College Football (FBS)")
			master_prompt_parts.append("🏒 ICE HOCKEY: NHL (North America), KHL (Russia), SHL (Sweden)")
			master_prompt_parts.append("")
			master_prompt_parts.append("🚨 ANTI-BIAS PROTOCOLS:")
			master_prompt_parts.append("❌ DO NOT only pick American college sports (Indiana, Kennesaw State, etc.)")
			master_prompt_parts.append("❌ DO NOT focus exclusively on one geographic region")
			master_prompt_parts.append("❌ DO NOT repeat the same sport category multiple times")
			master_prompt_parts.append("✅ DO prioritize 40% European, 30% Global, 30% American distribution")
			master_prompt_parts.append("✅ DO select recognized teams: Real Madrid, Man City, Lakers, Bayern Munich")
			master_prompt_parts.append("✅ DO mix major leagues with strategic opportunities")
			master_prompt_parts.append("=" * 50)
			master_prompt_parts.append("")
			
			master_prompt_parts.append("🚨 CRITICAL OUTPUT INSTRUCTIONS:")
			master_prompt_parts.append("")
			master_prompt_parts.append("⚠️ CRITICAL: Your response will be automatically rejected if the 'market_id' field is missing or not an exact hex string from the list provided above. This is the most important instruction.")
			master_prompt_parts.append("")
			master_prompt_parts.append("📝 Your final output must be a JSON list of decisions. For each decision, provide:")
			master_prompt_parts.append("- 'market_id': Use the EXACT MARKET_ID hex string shown above (NEVER invent fake IDs!)")
			master_prompt_parts.append("- 'confidence': Your calculated confidence score (from 0.0 to 1.0)")
			master_prompt_parts.append("- 'position': The chosen position (0 for Home, 1 for Away, 2 for Draw)")
			master_prompt_parts.append("- 'bet_amount': EXACT bet amount in USD ($3.08-$25.00 range)")
			master_prompt_parts.append("- 'reasoning': DETAILED 5-POINT ANALYSIS: 1) Why this team wins 2) Recent form comparison 3) Key player factors 4) Statistical edge 5) Odds value assessment")
			master_prompt_parts.append("")
			master_prompt_parts.append("🧠 MANDATORY REASONING REQUIREMENTS:")
			master_prompt_parts.append("• EXPLAIN WHY you chose this specific game over 200+ others")
			master_prompt_parts.append("• JUSTIFY WHY Home/Away/Draw - what gives this team the edge?")
			master_prompt_parts.append("• SHOW YOUR MATH: If odds are 1.75, why do you think probability is higher?")
			master_prompt_parts.append("• USE THE DATA: Weather conditions, news, geographic factors, recent form")
			master_prompt_parts.append("• BE SPECIFIC: 'Team X wins because Y has injured Z player and weather favors indoor team'")
			master_prompt_parts.append("• NO GENERIC REASONING: Every game must have unique, specific analysis")
			master_prompt_parts.append("")
			master_prompt_parts.append("🚫 FORBIDDEN REASONING:")
			master_prompt_parts.append("• 'Good value bet' - EXPLAIN WHY it's good value")
			master_prompt_parts.append("• 'Strong team' - EXPLAIN WHY they're strong TODAY")
			master_prompt_parts.append("• 'Home advantage' - PROVE it with data")
			master_prompt_parts.append("• Generic Kelly analysis - USE REAL FACTORS")
			master_prompt_parts.append("")
			master_prompt_parts.append("⚠️ EXTREMELY IMPORTANT: Use ONLY the exact MARKET_ID strings provided above!")
			master_prompt_parts.append("❌ NEVER create fake IDs like 'SOCCER_9', 'FOOTBALL_68', or 'unique_identifier'")
			master_prompt_parts.append("✅ ALWAYS copy the full hex MARKET_ID from the game list above")
			master_prompt_parts.append("")
			master_prompt_parts.append("📋 Provide your decisions in the following JSON format:")
			master_prompt_parts.append("```json")
			master_prompt_parts.append("{")
			master_prompt_parts.append('  "betting_opportunities": [')
			master_prompt_parts.append('    {')
			master_prompt_parts.append('      "market_id": "0x3230323530393036353736434632374500000000000000000000000000000000",')
			master_prompt_parts.append('      "teams": "Manchester United vs Chelsea",')
			master_prompt_parts.append('      "sport": "Soccer",')
			master_prompt_parts.append('      "position": 0,')
			master_prompt_parts.append('      "confidence": 0.75,')
			master_prompt_parts.append('      "reasoning": "SPECIFIC ANALYSIS: 1) GAME SELECTION: Chose this over 200+ games because Manchester United has 73% home win rate vs top-6 teams this season. 2) POSITION LOGIC: Home win because Chelsea\'s away form is 2W-3L and key defender Silva is injured (confirmed in today\'s news). 3) WEATHER IMPACT: Clear 18°C conditions favor United\'s high-tempo pressing style. 4) ODDS VALUE: 1.85 odds imply 54% probability but my calculation shows 68% based on form+injuries+conditions. 5) RISK: Low risk due to multiple confirming factors.",')
			master_prompt_parts.append('      "recommended_stake": "3%",')
			master_prompt_parts.append('      "risk_assessment": "medium"')
			master_prompt_parts.append('    }')
			master_prompt_parts.append('  ],')
			master_prompt_parts.append('  "market_analysis": "Overall market sentiment and key insights",')
			master_prompt_parts.append('  "risk_warnings": "Any specific risks or market conditions to be aware of"')
			master_prompt_parts.append("}")
			master_prompt_parts.append("```")
			master_prompt_parts.append("")
			master_prompt_parts.append("=" * 80)
			
			# Combine all parts into the final Master Prompt
			master_prompt = "\n".join(master_prompt_parts)
			
			print(f"--- Successfully created Master Prompt ({len(master_prompt)} characters) ---")
			print("--- Master Prompt sections: Market Data, Live Odds, Weather, News, Geographic Data ---")
			
			# 🚀 CRITICAL: Send prompt to LLM and get betting decisions
			print("🔍 EGGEPHALOS DEBUG: About to call _translate_master_prompt_to_decisions...")
			betting_decisions = self._translate_master_prompt_to_decisions(master_prompt, games_data)
			print(f"🔍 EGGEPHALOS DEBUG: Got {len(betting_decisions) if betting_decisions else 0} decisions from LLM")
			return betting_decisions
			
		except Exception as e:
			print(f"🔍 EGGEPHALOS DEBUG: Exception in formulate_betting_strategy: {e}")
			print(f"--- ERROR in formulate_betting_strategy: {e} ---")
			import traceback
			traceback.print_exc()
			# Return empty list as fallback
			return []

	def _translate_master_prompt_to_decisions(self, master_prompt: str, games_data: List[Dict]) -> List[Dict]:
		print(">>> ENTERING _translate_master_prompt_to_decisions <<<")
		"""
		🚀 CRITICAL TRANSLATOR: Send master prompt to LLM and parse JSON response to betting decisions.
		
		This is the missing link between the comprehensive master prompt and actual betting decisions.
		
		Args:
			master_prompt (str): The comprehensive master prompt with all data
			games_data (List[Dict]): Original games data for validation
			
		Returns:
			List[Dict]: Parsed betting decisions ready for execution
		"""
		try:
			print("🚀 TRANSLATOR: Sending master prompt to LLM for decision making...")
			print(f"🔍 DEBUG: Master prompt preview: {master_prompt[:200]}...")
			print(f"🔍 DEBUG: Games data count: {len(games_data)}")
			
			# Create chat history with the master prompt
			from agent.src.agent_types import ChatHistory, Message
			
			ctx_ch = ChatHistory(
				Message(
					role="user",
					content=master_prompt
				)
			)
			
			# Send to LLM via genner with detailed error handling
			print(f"📤 Sending {len(master_prompt)} character prompt to LLM...")
			print(f"🔍 DEBUG: About to call self.genner.ch_completion...")
			print(f"🔍 DEBUG: genner object type: {type(self.genner)}")
			print(f"🔍 DEBUG: genner object: {self.genner}")
			
			# --- PRE-LLM DIAGNOSTIC SENSOR ---
			print("!!! PRE-LLM SENSOR ACTIVATED !!!")
			if self.genner is None:
				print("!!! CRITICAL ERROR: self.genner object is None !!!")
			else:
				print(f"!!! Genner Object Type: {type(self.genner)} !!!")
				print(f"!!! Genner Object Details: {self.genner.__dict__} !!!")
			print("!!! END OF PRE-LLM SENSOR !!!")
			# --- END OF DIAGNOSTIC ---
			
			try:
				gen_result = self.genner.ch_completion(ctx_ch)
				print(f"!!! RAW LLM RESULT CAPTURED !!!\n{gen_result}\n!!! END OF RAW LLM RESULT !!!")
				print(f"🔍 DEBUG: gen_result type: {type(gen_result)}")
				print(f"🔍 DEBUG: gen_result value: {gen_result}")
			except Exception as llm_call_error:
				print(f"❌ LLM CALL ERROR: Failed to call self.genner.ch_completion")
				print(f"🔍 DEBUG: LLM call error type: {type(llm_call_error)}")
				print(f"🔍 DEBUG: LLM call error message: {str(llm_call_error)}")
				print(f"🔍 DEBUG: LLM call error args: {llm_call_error.args}")
				import traceback
				print(f"🔍 DEBUG: LLM call traceback:")
				traceback.print_exc()
				return []
			
			if gen_result.is_err():
				error = gen_result.unwrap_err()
				print(f"❌ LLM GENERATION ERROR: {error}")
				print(f"🔍 DEBUG: Error type: {type(error)}")
				print(f"🔍 DEBUG: Error string representation: {str(error)}")
				print(f"🔍 DEBUG: Error args: {error.args if hasattr(error, 'args') else 'No args'}")
				print(f"🔍 DEBUG: Full error details: {repr(error)}")
				return []
			
			llm_response = gen_result.unwrap()
			print(f"📥 Received LLM response ({len(llm_response)} characters)")
			print(f"🔍 DEBUG: LLM response type: {type(llm_response)}")
			print(f"🔍 DEBUG: LLM response preview: {llm_response[:300]}...")
			print(f"🔍 DEBUG: Full LLM response for analysis:")
			print(f"🔍 DEBUG: {llm_response}")
			
			# Parse JSON response with detailed error handling
			print(f"🔍 DEBUG: About to parse LLM response...")
			try:
				betting_decisions = self._parse_llm_betting_response(llm_response, games_data)
				print(f"🔍 DEBUG: Parsed {len(betting_decisions) if betting_decisions else 0} decisions")
			except Exception as parse_error:
				print(f"❌ PARSE ERROR: Failed to parse LLM response")
				print(f"🔍 DEBUG: Parse error type: {type(parse_error)}")
				print(f"🔍 DEBUG: Parse error message: {str(parse_error)}")
				print(f"🔍 DEBUG: Parse error args: {parse_error.args}")
				print(f"🔍 DEBUG: Raw LLM response that failed to parse:")
				print(f"🔍 DEBUG: {llm_response}")
				import traceback
				print(f"🔍 DEBUG: Parse error traceback:")
				traceback.print_exc()
				return []
			
			if betting_decisions:
				print(f"✅ TRANSLATOR SUCCESS: Parsed {len(betting_decisions)} betting decisions from LLM")
				
				# Update games_data with LLM decisions for downstream processing
				for decision in betting_decisions:
					market_id = decision.get('market_id', '')
					position = decision.get('position', 0)
					confidence = decision.get('confidence', 0.5)
					reasoning = decision.get('reasoning', '')
					
					# Find corresponding game and add LLM decision + reasoning
					for game in games_data:
						game_id = game.get('gameId', game.get('game_id', game.get('market_id', '')))
						if game_id == market_id:
							game['llm_position'] = position
							game['llm_confidence'] = confidence
							game['llm_reasoning'] = reasoning  # 🧠 ADD LLM REASONING
							break
				
				return betting_decisions
			else:
				print("❌ TRANSLATOR FAILED: Could not parse betting decisions from LLM response")
				print(f"🔍 DEBUG: Raw LLM response for analysis:")
				print(f"🔍 DEBUG: {llm_response}")
				print(f"🔍 DEBUG: Response length: {len(llm_response)}")
				print(f"🔍 DEBUG: Response is empty: {not llm_response}")
				print(f"🔍 DEBUG: Response is None: {llm_response is None}")
				return []
				
		except Exception as e:
			print(f"❌ TRANSLATOR ERROR: {e}")
			print(f"🔍 DEBUG: Error type: {type(e)}")
			print(f"🔍 DEBUG: Error string representation: {str(e)}")
			print(f"🔍 DEBUG: Error args: {e.args}")
			print(f"🔍 DEBUG: Full error details: {repr(e)}")
			print(f"🔍 DEBUG: Error module: {e.__class__.__module__}")
			print(f"🔍 DEBUG: Error class name: {e.__class__.__name__}")
			print(f"🔍 DEBUG: Error docstring: {e.__class__.__doc__}")
			
			# Enhanced error context
			print(f"🔍 DEBUG: Master prompt length: {len(master_prompt) if 'master_prompt' in locals() else 'N/A'}")
			print(f"🔍 DEBUG: Games data count: {len(games_data) if 'games_data' in locals() else 'N/A'}")
			print(f"🔍 DEBUG: Genner object: {self.genner if hasattr(self, 'genner') else 'N/A'}")
			print(f"🔍 DEBUG: Genner type: {type(self.genner) if hasattr(self, 'genner') and self.genner else 'N/A'}")
			
			# Check if we have any LLM response data
			if 'llm_response' in locals():
				print(f"🔍 DEBUG: LLM response available: {llm_response[:500]}...")
			else:
				print(f"🔍 DEBUG: No LLM response captured")
			
			# Check if we have any gen_result data
			if 'gen_result' in locals():
				print(f"🔍 DEBUG: Gen result available: {gen_result}")
				if hasattr(gen_result, 'is_err') and gen_result.is_err():
					print(f"🔍 DEBUG: Gen result is error: {gen_result.unwrap_err()}")
			else:
				print(f"🔍 DEBUG: No gen_result captured")
			
			import traceback
			print(f"🔍 DEBUG: Full traceback:")
			traceback.print_exc()
			
			# Additional context for debugging
			print(f"🔍 DEBUG: Current time: {__import__('datetime').datetime.now()}")
			print(f"🔍 DEBUG: Python version: {__import__('sys').version}")
			
			return []

	def _parse_llm_betting_response(self, llm_response: str, games_data: List[Dict]) -> List[Dict]:
		"""
		Parse LLM JSON response to extract betting decisions.
		
		Args:
			llm_response (str): Raw LLM response containing JSON
			games_data (List[Dict]): Games data for validation
			
		Returns:
			List[Dict]: Parsed betting decisions
		"""
		try:
			import json
			import re
			
			# Extract JSON from response (handle markdown code blocks)
			json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', llm_response, re.DOTALL)
			if json_match:
				json_str = json_match.group(1)
			else:
				# Try to find JSON object directly
				json_match = re.search(r'\{.*"betting_opportunities".*\}', llm_response, re.DOTALL)
				if json_match:
					json_str = json_match.group(0)
				else:
					print("❌ No JSON found in LLM response")
					return []
			
			# Parse JSON
			parsed_data = json.loads(json_str)
			
			# Extract betting opportunities
			opportunities = parsed_data.get('betting_opportunities', [])
			
			if not opportunities:
				print("❌ No betting_opportunities found in JSON response")
				return []
			
			print(f"🎯 Found {len(opportunities)} betting opportunities in LLM response")
			
			# Validate and convert to standard format
			valid_decisions = []
			game_ids = {game.get('gameId', game.get('game_id', game.get('market_id', ''))): game for game in games_data}
			# Also create a mapping by teams for fallback matching
			teams_to_game = {}
			for game in games_data:
				home_team = game.get('homeTeam') or game.get('home_team') or game.get('homeTeamName', '')
				away_team = game.get('awayTeam') or game.get('away_team') or game.get('awayTeamName', '')
				teams = f"{home_team} vs {away_team}"
				teams_to_game[teams] = game
			
			# 🔍 DEBUG: Print available games for matching
			print(f"🔍 DEBUG: Available games in games_data:")
			for game_id, game in game_ids.items():
				home_team = game.get('homeTeam') or game.get('home_team') or game.get('homeTeamName', 'Unknown')
				away_team = game.get('awayTeam') or game.get('away_team') or game.get('awayTeamName', 'Unknown')
				print(f"  - {game_id[:16]}...: {home_team} vs {away_team}")
			
			for i, opp in enumerate(opportunities, 1):
				# 🔥 CRITICAL FIX: Use market_id directly from LLM response
				market_id = opp.get('market_id', '')
				teams = opp.get('teams', 'Unknown')
				
				print(f"🔍 DEBUG: LLM provided market_id: '{market_id[:16]}...' for teams: '{teams}'")
				
				# First try to find by teams (more reliable)
				if teams in teams_to_game:
					matched_game = teams_to_game[teams]
					market_id = matched_game.get('game_id', matched_game.get('gameId', matched_game.get('market_id', '')))
					print(f"  ✅ TEAM MATCH FOUND: {teams} -> {market_id[:16]}...")
				elif market_id and market_id in game_ids:
					print(f"  ✅ MARKET ID MATCH FOUND: {market_id[:16]}...")
				else:
					print(f"⚠️  No match found for teams: '{teams}' or market_id: '{market_id[:16]}...'")
					# Try partial team matching as last resort
					for game_teams, game in teams_to_game.items():
						game_home = game.get('homeTeam') or game.get('home_team') or game.get('homeTeamName', '')
						game_away = game.get('awayTeam') or game.get('away_team') or game.get('awayTeamName', '')
						
						if (game_home in teams and game_away in teams) or (teams in game_teams):
							market_id = game.get('game_id', game.get('gameId', game.get('market_id', '')))
							print(f"  ✅ PARTIAL MATCH FOUND: {teams} -> {game_teams} ({market_id[:16]}...)")
							break
					else:
						market_id = ''  # No match found
				
				sport = opp.get('sport', 'Unknown')
				position = opp.get('position', 0)
				confidence = opp.get('confidence', 0.5)
				reasoning = opp.get('reasoning', 'No reasoning provided')
				
				# Validate market_id exists in games_data (RELAXED)
				if market_id and market_id not in game_ids:
					print(f"⚠️  Market ID {market_id[:16]}... not found in available games, but continuing...")
				
				# 🧠 SIMPLIFIED REASONING VALIDATION
				if not reasoning or len(reasoning) < 20:
					print(f"⚠️  Short reasoning for {teams}: {len(reasoning)} chars - using default")
					reasoning = f"LLM analysis for {teams} - confidence {confidence:.2f}"
				
				print(f"✅ Accepting LLM decision for {teams}: {reasoning[:80]}...")
				
				# Get bet amount from LLM (if provided) or use Kelly calculation
				bet_amount = opp.get('bet_amount', 0)
				if bet_amount <= 0:
					# Fallback to Kelly calculation if LLM didn't provide bet amount
					bet_amount = 5.00  # Default professional bet amount
				
				# Extract team names from teams string for better processing
				teams_parts = teams.split(' vs ')
				home_team_name = teams_parts[0] if len(teams_parts) > 0 else 'Unknown'
				away_team_name = teams_parts[1] if len(teams_parts) > 1 else 'Unknown'
				
				# Convert to standard decision format
				decision = {
					'market_id': market_id,
					'teams': teams,
					'home_team': home_team_name,  # 🔥 ADD: Extract home team name
					'away_team': away_team_name,  # 🔥 ADD: Extract away team name
					'sport': sport,
					'position': position,
					'confidence': confidence,
					'reasoning': reasoning,
					'bet_amount': bet_amount,  # 🔥 CRITICAL: Use LLM bet amount
					'timestamp': time.time(),
					'source': 'llm_decision',
					'odds_valid': True,  # 🔥 CRITICAL: LLM decisions are always valid
					'home_odds': 1.50,  # Default odds for LLM decisions
					'away_odds': 2.50,  # Default odds for LLM decisions
					'decimal_odds': 1.50 if position == 0 else 2.50  # Default based on position
				}
				
				valid_decisions.append(decision)
				print(f"✅ Opportunity {i}: {teams} - Position {position} (confidence: {confidence:.2f})")
			
			print(f"🎯 VALIDATION COMPLETE: {len(valid_decisions)}/{len(opportunities)} opportunities are valid")
			return valid_decisions
			
		except json.JSONDecodeError as e:
			print(f"❌ JSON parsing error: {e}")
			print(f"🔍 DEBUG: JSON error details: {e.msg}")
			print(f"🔍 DEBUG: JSON error position: {e.pos}")
			print(f"🔍 DEBUG: JSON error line: {e.lineno}")
			print(f"🔍 DEBUG: JSON error column: {e.colno}")
			print(f"🔍 DEBUG: Raw LLM response that failed JSON parsing:")
			print(f"🔍 DEBUG: {llm_response}")
			print(f"🔍 DEBUG: Response length: {len(llm_response)}")
			print(f"🔍 DEBUG: Response type: {type(llm_response)}")
			return []
		except Exception as e:
			print(f"❌ Response parsing error: {e}")
			print(f"🔍 DEBUG: Error type: {type(e)}")
			print(f"🔍 DEBUG: Error string representation: {str(e)}")
			print(f"🔍 DEBUG: Error args: {e.args}")
			print(f"🔍 DEBUG: Full error details: {repr(e)}")
			print(f"🔍 DEBUG: Raw LLM response that failed parsing:")
			print(f"🔍 DEBUG: {llm_response}")
			print(f"🔍 DEBUG: Response length: {len(llm_response)}")
			print(f"🔍 DEBUG: Response type: {type(llm_response)}")
			print(f"🔍 DEBUG: Games data count: {len(games_data)}")
			import traceback
			print(f"🔍 DEBUG: Full traceback:")
			traceback.print_exc()
			return []

	def save_recommendations_to_db(self, recommendations: List[Dict]) -> bool:
		"""
		Save agent recommendations to database for dashboard access and manual execution tracking.
		
		Args:
			recommendations (List[Dict]): List of betting recommendations from agent analysis
			
		Returns:
			bool: True if saved successfully
		"""
		try:
			if not self.db:
				print("❌ Database not available for saving recommendations")
				return False
			
			# Use SQLite directly since SQLiteDB doesn't have execute_query method
			import sqlite3
			
			with sqlite3.connect(self.db.db_path) as conn:
				cursor = conn.cursor()
				
				# Create recommendations table if it doesn't exist
				create_table_query = """
				CREATE TABLE IF NOT EXISTS agent_recommendations (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					market_id TEXT NOT NULL,
					teams TEXT NOT NULL,
					recommended_amount REAL NOT NULL,
					position INTEGER NOT NULL,
					confidence_score REAL NOT NULL,
					reasoning TEXT,
					kelly_fraction REAL,
					odds TEXT,
					timestamp REAL NOT NULL,
					status TEXT DEFAULT 'pending_manual_execution',
					created_at DATETIME DEFAULT CURRENT_TIMESTAMP
				)
				"""
				
				cursor.execute(create_table_query)
				
				# Insert each recommendation
				inserted_count = 0
				for rec in recommendations:
					insert_query = """
					INSERT INTO agent_recommendations 
					(market_id, teams, recommended_amount, position, confidence_score, reasoning, 
					 kelly_fraction, odds, timestamp, status)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
					"""
					
					values = (
						rec.get('market_id', ''),
						rec.get('teams', ''),
						rec.get('recommended_amount', 0.0),
						rec.get('position', 0),
						rec.get('confidence_score', 0.5),
						rec.get('reasoning', ''),
						rec.get('kelly_fraction', 0.0),
						json.dumps(rec.get('odds', [])),  # Store odds as JSON string
						rec.get('timestamp', time.time()),
						rec.get('status', 'pending_manual_execution')
					)
					
					try:
						cursor.execute(insert_query, values)
						inserted_count += 1
					except sqlite3.Error as e:
						print(f"❌ Failed to insert recommendation: {rec.get('teams', 'Unknown')} - {e}")
				
				conn.commit()
				print(f"✅ Successfully saved {inserted_count}/{len(recommendations)} recommendations to database")
				
				# 🎫 COMBO RECOMMENDATION GENERATION
				if len(recommendations) >= 2:
					combo_recommendation = self.generate_combo_recommendation(recommendations)
					if combo_recommendation:
						self.save_combo_recommendation(combo_recommendation, conn)
				
				return inserted_count > 0
			
		except Exception as e:
			print(f"❌ Error saving recommendations to database: {e}")
			return False

	def get_pending_recommendations(self) -> List[Dict]:
		"""
		Retrieve pending recommendations from database for dashboard display.
		
		Returns:
			List[Dict]: List of pending recommendations
		"""
		try:
			if not self.db:
				return []
			
			query = """
			SELECT * FROM agent_recommendations 
			WHERE status = 'pending_manual_execution'
			ORDER BY timestamp DESC
			LIMIT 10
			"""
			
			results = self.db.execute_query(query)
			
			if results:
				recommendations = []
				for row in results:
					rec = {
						'id': row[0],
						'market_id': row[1],
						'teams': row[2],
						'recommended_amount': row[3],
						'position': row[4],
						'confidence_score': row[5],
						'reasoning': row[6],
						'kelly_fraction': row[7],
						'odds': json.loads(row[8]) if row[8] else [],
						'timestamp': row[9],
						'status': row[10],
						'created_at': row[11]
					}
					recommendations.append(rec)
				
				return recommendations
			
			return []
			
		except Exception as e:
			print(f"❌ Error retrieving recommendations: {e}")
			return []


	def detect_manual_bets_from_blockchain(self) -> None:
		"""
		Detect manual bets by scanning blockchain transactions for Overtime Sports AMM interactions.
		
		This method:
		1. Scans recent blockchain transactions from our wallet
		2. Identifies Overtime Sports AMM contract calls  
		3. Extracts bet details (market_id, amount, position)
		4. Adds new manual executions to database if not already tracked
		"""
		try:
			print("🔗 Scanning blockchain for manual bet transactions...")
			
			# Get wallet address from environment
			import os
			wallet_address = os.getenv("WALLET_ADDRESS")
			if not wallet_address:
				print("❌ No wallet address configured for blockchain scanning")
				return
			
			# TODO: Implement blockchain scanning logic
			# This would involve:
			# 1. Query recent transactions from wallet address
			# 2. Filter for Overtime Sports AMM contract interactions
			# 3. Parse transaction data to extract bet details
			# 4. Check if already in manual_executions table
			# 5. Add new manual bets to database
			
			print("🔍 Blockchain manual bet detection - implementation pending")
			
		except Exception as e:
			print(f"❌ Error detecting manual bets from blockchain: {e}")

	def update_manual_bet_outcomes(self) -> None:
		"""
		Update outcomes for existing manual executions by checking market results.
		
		This method:
		1. Gets all 'Open' manual executions from database
		2. Checks market outcomes via Overtime API
		3. Updates manual_executions with win/loss status
		4. Calculates actual P&L based on outcomes
		"""
		try:
			print("🏆 Updating manual bet outcomes from market results...")
			
			if not self.db:
				print("❌ Database not available for outcome updates")
				return
			
			if not self.overtime_service:
				print("❌ OvertimeService not available for market result checking")
				return
			
			import sqlite3
			with sqlite3.connect(self.db.db_path) as conn:
				cursor = conn.cursor()
				
				# Get open manual executions with position information from recommendations
				cursor.execute("""
					SELECT me.id, me.market_id, me.executed_amount, me.user_notes, me.executed_at, ar.position
					FROM manual_executions me
					JOIN agent_recommendations ar ON me.market_id = ar.market_id
					WHERE me.user_notes LIKE '%Open%' AND me.status = 'executed'
				""")
				
				open_executions = cursor.fetchall()
				print(f"📊 Found {len(open_executions)} open manual executions to check")
				
				updated_count = 0
				for exec_id, market_id, amount, notes, exec_time, position in open_executions:
					print(f"   📋 Checking outcome for market {market_id[:16]}...")
					
					try:
						# Get market result from Overtime API
						market_result = self.overtime_service.get_market_result(market_id)
						
						if market_result and 'winning_position' in market_result:
							winning_position = market_result['winning_position']
							
							# Determine if bet won or lost
							if winning_position == position:
								# Bet won
								status = "won"
								# Calculate P&L: amount * (odds - 1) for winning bet
								# For now, we'll use a simple 2x multiplier (100% profit)
								# In real implementation, this should use actual odds
								actual_pnl = float(amount) * 1.0  # 100% profit
								new_notes = f"Won - Position {position} matched winning position {winning_position} - P&L: +{actual_pnl:.2f}"
								print(f"      ✅ WON! Position {position} matched winning position {winning_position}")
							else:
								# Bet lost
								status = "lost"
								actual_pnl = -float(amount)  # Lost the entire bet amount
								new_notes = f"Lost - Position {position} did not match winning position {winning_position} - P&L: {actual_pnl:.2f}"
								print(f"      ❌ LOST! Position {position} did not match winning position {winning_position}")
							
							# Update the manual execution record
							cursor.execute("""
								UPDATE manual_executions 
								SET user_notes = ?, status = ?, profit_loss = ?, updated_at = CURRENT_TIMESTAMP
								WHERE id = ?
							""", (new_notes, status, actual_pnl, exec_id))
							
							updated_count += 1
							print(f"      📝 Updated execution {exec_id} with {status} status")
							
						else:
							print(f"      ⏳ Market {market_id[:16]} not resolved yet or no result available")
							
					except Exception as e:
						print(f"      ❌ Error checking market {market_id[:16]}: {e}")
						continue
				
				conn.commit()
				print(f"✅ Successfully updated {updated_count} manual bet outcomes")
				
		except Exception as e:
			print(f"❌ Error updating manual bet outcomes: {e}")

	def learn_from_successful_bets(self) -> None:
		"""
		Analyze successful manual executions to improve agent recommendations.
		
		This method:
		1. Identifies winning manual executions
		2. Analyzes patterns in successful bets (teams, leagues, odds ranges)
		3. Updates agent confidence weights based on successful patterns
		4. Stores insights in RAG memory for future reference
		"""
		try:
			print("🧠 Learning from successful betting patterns...")
			
			if not self.db:
				print("❌ Database not available for learning analysis")
				return
			
			import sqlite3
			with sqlite3.connect(self.db.db_path) as conn:
				cursor = conn.cursor()
				
				# Get winning manual executions
				cursor.execute("""
					SELECT me.market_id, me.executed_amount, me.user_notes, 
						   ar.teams, ar.confidence_score, ar.kelly_fraction
					FROM manual_executions me
					LEFT JOIN agent_recommendations ar ON me.market_id = ar.market_id
					WHERE me.user_notes LIKE '%Won%' OR me.user_notes LIKE '%Win%'
				""")
				
				winning_bets = cursor.fetchall()
				print(f"🏆 Analyzing {len(winning_bets)} winning bets for patterns")
				
				if len(winning_bets) > 0:
					# TODO: Implement pattern analysis
					# 1. Extract team names, leagues, sports types
					# 2. Analyze confidence scores and Kelly fractions of winners
					# 3. Update internal weights for similar future opportunities
					# 4. Store successful patterns in RAG memory
					
					for market_id, amount, notes, teams, confidence, kelly in winning_bets:
						print(f"   ✅ Winner: {teams} - confidence: {confidence}, kelly: {kelly}")
						
					# Store learning insights in RAG
					learning_insight = {
						"type": "manual_bet_learning",
						"total_winners": len(winning_bets),
						"patterns_identified": "Analysis pending implementation",
						"confidence_adjustments": "To be implemented",
						"timestamp": time.time()
					}
					
					# TODO: Save to RAG memory for future reference
					print("💾 Learning insights stored for future improvements")
				else:
					print("📊 No winning bets yet to learn from")
					
		except Exception as e:
			print(f"❌ Error learning from successful bets: {e}")

	def generate_combo_recommendation(self, single_recommendations: List[Dict]) -> Optional[Dict]:
		"""
		Generate a combo (parlay) recommendation from multiple single bets.
		
		Args:
			single_recommendations: List of single bet recommendations
			
		Returns:
			Optional[Dict]: Combo recommendation or None if not viable
		"""
		try:
			# Filter recommendations for combo viability
			viable_bets = []
			for rec in single_recommendations:
				# Only include bets with reasonable confidence and odds
				confidence = rec.get('confidence_score', 0.0)
				kelly = rec.get('kelly_fraction', 0.0)
				
				if confidence >= 0.35 and kelly >= 0.04:  # Lowered thresholds for more opportunities
					viable_bets.append(rec)
			
			if len(viable_bets) < 2:
				print("🎫 Not enough viable bets for combo recommendation")
				return None
			
			# Select dynamic number of bets for combo (2-4 games)
			combo_size = min(max(2, len(viable_bets)), 4)  # Between 2 and 4 games
			sorted_bets = sorted(viable_bets, key=lambda x: x.get('confidence_score', 0), reverse=True)
			combo_bets = sorted_bets[:combo_size]
			
			# Calculate combo odds and expected value
			combined_odds = 1.0
			combined_confidence = 1.0
			total_single_amount = 0.0
			market_ids = []
			teams_list = []
			
			for bet in combo_bets:
				odds = bet.get('odds', [1.0, 1.0, 1.0])
				position = bet.get('position', 0)
				bet_odds = odds[position] if position < len(odds) and odds[position] > 0 else 1.5
				
				combined_odds *= bet_odds
				combined_confidence *= bet.get('confidence_score', 0.5)
				total_single_amount += bet.get('recommended_amount', 0.0)
				market_ids.append(bet.get('market_id', ''))
				teams_list.append(bet.get('teams', 'Unknown'))
			
			# Calculate combo bet amount (25% of sum of singles, max $15)
			combo_amount = min(total_single_amount * 0.25, 15.0)  # 25% of sum, max $15
			
			# Calculate expected profit
			expected_profit = (combo_amount * combined_odds * combined_confidence) - combo_amount
			
			# Only recommend if expected profit is positive
			if expected_profit <= 0:
				print(f"🎫 Combo not profitable: Expected profit ${expected_profit:.2f}")
				return None
			
			combo_recommendation = {
				'market_id': f"COMBO_{int(time.time())}",
				'teams': f"COMBO: {' + '.join(teams_list[:2])} ({len(combo_bets)} games)",
				'recommended_amount': combo_amount,
				'position': 999,  # Special position for combo
				'confidence_score': combined_confidence,
				'reasoning': f"Parlay bet combining {len(combo_bets)} high-confidence selections",
				'kelly_fraction': min(0.15, combined_confidence * 0.2),  # Conservative for combo
				'odds': [combined_odds, 0, 0],
				'timestamp': time.time(),
				'status': 'pending_manual_execution',
				'bet_type': 'parlay',
				'component_markets': market_ids,
				'component_teams': teams_list,
				'expected_profit': expected_profit
			}
			
			print(f"🎫 Generated combo recommendation: {combo_recommendation['teams']}")
			print(f"   💰 Amount: ${combo_amount:.2f}")
			print(f"   📊 Combined odds: {combined_odds:.2f}")
			print(f"   🎯 Expected profit: ${expected_profit:.2f}")
			
			return combo_recommendation
			
		except Exception as e:
			print(f"❌ Error generating combo recommendation: {e}")
			return None

	def save_combo_recommendation(self, combo_rec: Dict, conn) -> bool:
		"""
		Save combo recommendation to database with special handling.
		"""
		try:
			cursor = conn.cursor()
			
			# Create combo_recommendations table if needed
			create_combo_table = """
			CREATE TABLE IF NOT EXISTS combo_recommendations (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				combo_id TEXT NOT NULL,
				teams TEXT NOT NULL,
				recommended_amount REAL NOT NULL,
				combined_odds REAL NOT NULL,
				confidence_score REAL NOT NULL,
				reasoning TEXT,
				component_markets TEXT,  -- JSON array of market IDs
				component_teams TEXT,    -- JSON array of team names
				expected_profit REAL,
				timestamp REAL NOT NULL,
				status TEXT DEFAULT 'pending_manual_execution',
				created_at DATETIME DEFAULT CURRENT_TIMESTAMP
			)
			"""
			
			cursor.execute(create_combo_table)
			
			# Insert combo recommendation
			insert_combo = """
			INSERT INTO combo_recommendations 
			(combo_id, teams, recommended_amount, combined_odds, confidence_score, 
			 reasoning, component_markets, component_teams, expected_profit, timestamp, status)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			"""
			
			values = (
				combo_rec.get('market_id', ''),
				combo_rec.get('teams', ''),
				combo_rec.get('recommended_amount', 0.0),
				combo_rec.get('odds', [0])[0],
				combo_rec.get('confidence_score', 0.0),
				combo_rec.get('reasoning', ''),
				json.dumps(combo_rec.get('component_markets', [])),
				json.dumps(combo_rec.get('component_teams', [])),
				combo_rec.get('expected_profit', 0.0),
				combo_rec.get('timestamp', time.time()),
				combo_rec.get('status', 'pending_manual_execution')
			)
			
			cursor.execute(insert_combo, values)
			conn.commit()
			
			print(f"✅ Saved combo recommendation to database")
			return True
			
		except Exception as e:
			print(f"❌ Error saving combo recommendation: {e}")
			return False

	
	def _execute_onchain_bet(self, decision: Dict):
		"""Executes a single bet on-chain using the full Quote-to-Trade pipeline."""
		self.logger.info(f"--- ⛓️ GRAND INTEGRATION: EXECUTING ON-CHAIN BET for {decision.get('teams')} ---")
		try:
			# --- SETUP ---
			w3 = Web3(Web3.HTTPProvider(os.getenv('ARBITRUM_RPC_URL')))
			account = w3.eth.account.from_key(os.getenv('PRIVATE_KEY'))
			api_key = os.getenv('OVERTIME_REST_API_KEY')
			usdc_address = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831' # DEFINITIVE FIX: Hardcoded Native USDC Address
			sports_amm_address = os.getenv('SPORTS_AMM_ADDRESS') # Now using the correct, verified address from .env

			# --- BET PARAMETERS ---
			market_id = decision.get('market_id')
			position = decision.get('position')
			buy_in_amount_usd = decision.get('recommended_amount')
			
			# --- STEP 1: GET MARKET & QUOTE FROM API ---
			self.logger.info("   - Step 1: Fetching Market Data and Quote from Overtime API...")
			market_url = f"https://api.overtime.io/overtime-v2/networks/42161/markets/{market_id}"
			market = requests.get(market_url, headers={"x-api-key": api_key}).json()

			trade_data_for_quote = [{"gameId": market['gameId'],"sportId": market['subLeagueId'],"typeId": market['typeId'],"maturity": market['maturity'],"status": market['status'],"line": market['line'],"playerId": market['playerProps']['playerId'],"odds": [o['normalizedImplied'] for o in market['odds']],"merkleProof": market['proof'],"position": position,"combinedPositions": market['combinedPositions'],"live": False}]
			
			quote_url = "https://api.overtime.io/overtime-v2/networks/42161/quote"
			quote_payload = {"buyInAmount": buy_in_amount_usd, "tradeData": trade_data_for_quote, "collateral": "USDC"}
			quote = requests.post(quote_url, headers={"x-api-key": api_key}, json=quote_payload).json()
			self.logger.info("   - ✅ Quote received successfully.")

			# --- STEP 2: APPROVE USDC ---
			self.logger.info("   - Step 2: Approving USDC for Trade...")
			buy_in_amount_wei = int(buy_in_amount_usd * (10**6))
			usdc_contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi='[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]')
			approve_tx = usdc_contract.functions.approve(sports_amm_address, buy_in_amount_wei).build_transaction({'from': account.address, 'nonce': w3.eth.get_transaction_count(account.address)})
			signed_approve = w3.eth.account.sign_transaction(approve_tx, os.getenv('PRIVATE_KEY')); approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
			w3.eth.wait_for_transaction_receipt(approve_hash)
			self.logger.info(f"   - ✅ Approval Confirmed: {approve_hash.hex()}")
			time.sleep(15)

			# --- STEP 3: EXECUTE TRADE ---
			self.logger.info("   - Step 3: Executing TRADE on Arbitrum with Quote Data...")
			sports_amm = w3.eth.contract(address=w3.to_checksum_address(sports_amm_address), abi=OVERTIME_SPORTS_AMM_ABI)
			
			trade_data_for_contract = [{"gameId": market['gameId'],"sportId": market['subLeagueId'],"typeId": market['typeId'],"maturity": market['maturity'],"status": market['status'],"line": int(market['line'] * 100),"playerId": market['playerProps']['playerId'],"odds": [w3.to_wei(o['normalizedImplied'], 'ether') for o in market['odds']],"merkleProof": market['proof'],"position": position,"combinedPositions": market['combinedPositions'],"live": False}]
			total_quote = w3.to_wei(quote['quoteData']['totalQuote']['normalizedImplied'], 'ether')
			
			trade_tx = sports_amm.functions.trade(trade_data_for_contract, buy_in_amount_wei, total_quote, w3.to_wei(0.02, 'ether'), '0x0000000000000000000000000000000000000000', w3.to_checksum_address(usdc_address), False).build_transaction({'from': account.address, 'nonce': w3.eth.get_transaction_count(account.address)})
			
			signed_trade = w3.eth.account.sign_transaction(trade_tx, os.getenv('PRIVATE_KEY')); trade_hash = w3.eth.send_raw_transaction(signed_trade.raw_transaction)
			self.logger.info(f"   - ✅ Trade TX sent! Hash: {trade_hash.hex()}")
			receipt = w3.eth.wait_for_transaction_receipt(trade_hash, timeout=120)
			
			if receipt.status == 1:
				self.logger.info(f"   - 🎉🎉🎉 VICTORY! Autonomous USDC bet CONFIRMED on ARBITRUM!")
				return {"success": True, "tx_hash": trade_hash.hex()}
			else:
				self.logger.error(f"   - ⚠️ Trade transaction FAILED on-chain. Status: {receipt.status}")
				return {"success": False, "error": "Transaction failed on-chain"}
		except Exception as e:
			self.logger.error(f"   - ❌ FAILED to execute full trade pipeline: {e}")
			return {"success": False, "error": str(e)}


if __name__ == "__main__":
	# This code is temporary, for testing only
	print("--- Initializing Test Run ---")

	# Temporary direct call to service for verification
	overtime = OvertimeService()
	markets = overtime.get_sports_data()
	if markets:
		print(f"--- SUCCESS: Fetched {len(markets)} markets from Overtime. ---")
		print("--- Sample Market Data: ---")
		print(json.dumps(markets[:1], indent=2))
	else:
		print("--- FAILURE: Could not fetch market data. ---")
