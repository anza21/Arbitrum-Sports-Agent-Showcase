#!/usr/bin/env python3
"""
Dashboard API for Superior Betting Agent
========================================

A Flask API that provides endpoints to monitor and retrieve data from the betting agent.

Endpoints:
- GET /api/bets: Returns all betting decisions stored in the agent's database
- GET /api/status: Returns agent status and current wallet balance  
- GET /api/summary: Returns betting performance summary with P&L metrics
- GET /api/recommendations: Returns agent's pending recommendations for manual execution

Author: Superior Agents Dashboard
"""

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from dataclasses import dataclass
import glob
from web3 import Web3

# Setup logging
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Αντικατέστησε το CORS(app) με αυτό:
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
DATABASE_PATH = "/app/agent/db/superior-agents.db"  # Force absolute path
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8080")
ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")

def get_eth_price():
    """Get current ETH price from CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        response = requests.get(url)
        response.raise_for_status()
        price_data = response.json()
        return price_data['ethereum']['usd']
    except Exception:
        return 3500.0  # Fallback

def get_eth_balance(w3, wallet_address):
    """Get ETH balance for wallet address"""
    try:
        raw_balance = w3.eth.get_balance(w3.to_checksum_address(wallet_address))
        return w3.from_wei(raw_balance, 'ether')
    except Exception:
        return 0.0

def get_recommendations_by_cycle():
    """Get recommendations grouped by cycle/timestamp"""
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        # Get recommendations with cycle grouping based on cycle_id
        cursor.execute("""
            SELECT 
                ar.market_id,
                ar.teams,
                ar.recommended_amount,
                ar.position,
                ar.confidence_score,
                ar.reasoning,
                ar.kelly_fraction,
                ar.odds,
                ar.status,
                ar.created_at,
                ar.cycle_id,
                ac.cycle_start_time,
                DATE(ar.created_at) as cycle_date,
                STRFTIME('%H', ar.created_at) as cycle_hour
            FROM agent_recommendations ar
            LEFT JOIN agent_cycles ac ON ar.cycle_id = ac.cycle_id
            WHERE ar.status = 'pending_manual_execution'
            ORDER BY ar.created_at DESC
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        recommendations = []
        
        position_names = {0: "Home", 1: "Away", 2: "Draw"}
        
        for row in rows:
            try:
                odds_data = json.loads(row['odds']) if row['odds'] else [0, 0, 0]
            except:
                odds_data = [0, 0, 0]
            
            position = row['position'] if row['position'] is not None else 0
            expected_odds = odds_data[position] if position < len(odds_data) else 0
            
            recommendation = {
                'id': f"{row['market_id']}_{row['created_at']}",
                'market_id': row['market_id'],
                'teams': row['teams'],
                'recommended_amount': float(row['recommended_amount']) if row['recommended_amount'] else 0,
                'position_name': position_names.get(position, f"Position {position}"),
                'confidence_score': float(row['confidence_score']) if row['confidence_score'] else 0.5,
                'reasoning': row['reasoning'] or "",
                'kelly_fraction': float(row['kelly_fraction']) if row['kelly_fraction'] else 0,
                'expected_odds': expected_odds,
                'status': row['status'] or 'pending',
                'created_at': row['created_at'],
                'cycle_date': row['cycle_date'],
                'cycle_hour': int(row['cycle_hour']) if row['cycle_hour'] else 0,
                'cycle_label': f"Cycle {row['cycle_id'] or 'Unknown'} - {row['cycle_date']} {row['cycle_hour'] or '00'}:00",
                'cycle_id': row['cycle_id'],
                'cycle_start_time': row['cycle_start_time']
            }
            recommendations.append(recommendation)
        
        connection.close()
        return recommendations
        
    except Exception as e:
        print(f"Database error in get_recommendations_by_cycle: {e}")
        return []

# USDC.e contract address on Arbitrum
USDC_ADDRESS = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831' # DEFINITIVE FIX: Hardcoded Native USDC Address

@dataclass
class BetData:
    """Data structure for betting information"""
    bet_id: str
    agent_id: str
    market_id: str
    bet_amount: float
    odds: float
    status: str
    created_at: str
    updated_at: str

@dataclass  
class StrategyData:
    """Data structure for strategy/decision information from RAG"""
    strategy_id: str
    agent_id: str
    summarized_desc: str
    full_desc: str
    parameters: Dict
    strategy_result: str
    created_at: str

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_bets(self, agent_id: Optional[str] = None) -> List[BetData]:
        """Retrieve all bets from the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if agent_id:
                    cursor.execute("""
                        SELECT bet_id, agent_id, market_id, bet_amount, odds, status, created_at, updated_at
                        FROM sup_bets 
                        WHERE agent_id = ?
                        ORDER BY created_at DESC
                    """, (agent_id,))
                else:
                    cursor.execute("""
                        SELECT bet_id, agent_id, market_id, bet_amount, odds, status, created_at, updated_at
                        FROM sup_bets 
                        ORDER BY created_at DESC
                    """)
                
                rows = cursor.fetchall()
                return [BetData(*row) for row in rows]
        except Exception as e:
            print(f"Error retrieving bets: {e}")
            return []
    
    def get_strategies(self, agent_id: Optional[str] = None) -> List[StrategyData]:
        """Retrieve strategies from the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if agent_id:
                    cursor.execute("""
                        SELECT strategy_id, agent_id, summarized_desc, full_desc, 
                               parameters, strategy_result, created_at
                        FROM sup_strategies 
                        WHERE agent_id = ?
                        ORDER BY created_at DESC
                    """, (agent_id,))
                else:
                    cursor.execute("""
                        SELECT strategy_id, agent_id, summarized_desc, full_desc, 
                               parameters, strategy_result, created_at
                        FROM sup_strategies 
                        ORDER BY created_at DESC
                    """)
                
                rows = cursor.fetchall()
                strategies = []
                for row in rows:
                    try:
                        parameters = json.loads(row[4]) if row[4] else {}
                    except:
                        parameters = {}
                    strategies.append(StrategyData(
                        strategy_id=row[0],
                        agent_id=row[1], 
                        summarized_desc=row[2],
                        full_desc=row[3],
                        parameters=parameters,
                        strategy_result=row[5],
                        created_at=row[6]
                    ))
                return strategies
        except Exception as e:
            print(f"Error retrieving strategies: {e}")
            return []
            
    def get_agent_sessions(self) -> List[Dict]:
        """Get agent session information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT agent_id, session_id, status, started_at, cycle_count, last_cycle
                    FROM sup_agent_sessions 
                    ORDER BY started_at DESC
                """)
                
                rows = cursor.fetchall()
                return [
                    {
                        "agent_id": row[0],
                        "session_id": row[1], 
                        "status": row[2],
                        "started_at": row[3],
                        "cycle_count": row[4],
                        "last_cycle": row[5]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error retrieving agent sessions: {e}")
            return []
    
    def query_db(self, query: str) -> List:
        """Execute a query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error executing query: {e}")
            return []

class RAGManager:
    """Handles RAG database operations to retrieve agent decisions"""
    
    def __init__(self, rag_url: str):
        self.rag_url = rag_url
        
    def get_betting_decisions(self, agent_id: str, limit: int = 100) -> List[Dict]:
        """Retrieve betting decisions from RAG database"""
        try:
            # Query RAG for betting-related decisions
            response = requests.post(f"{self.rag_url}/get_relevant_document_raw_v4", json={
                "notification_query": "betting decision strategy game outcome",
                "agent_id": agent_id,
                "top_k": limit
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "data" in data:
                    decisions = []
                    for item in data["data"]:
                        metadata = item.get("metadata", {})
                        # Extract strategy data which contains betting information
                        strategy_data = metadata.get("strategy_data", "")
                        try:
                            # Parse JSON if it's a string
                            if isinstance(strategy_data, str):
                                strategy_info = json.loads(strategy_data)
                            else:
                                strategy_info = strategy_data
                            
                            decisions.append({
                                "reference_id": metadata.get("reference_id"),
                                "created_at": metadata.get("created_at"),
                                "strategy_data": strategy_info,
                                "score": item.get("score", 0)
                            })
                        except:
                            # If not JSON, include as text
                            decisions.append({
                                "reference_id": metadata.get("reference_id"),
                                "created_at": metadata.get("created_at"),
                                "strategy_data": strategy_data,
                                "score": item.get("score", 0)
                            })
                    return decisions
            return []
        except Exception as e:
            print(f"Error retrieving RAG decisions: {e}")
            return []

class WalletManager:
    """Handles wallet balance queries"""
    
    def __init__(self):
        self.arbitrum_rpc = ARBITRUM_RPC_URL
        
    def get_wallet_balance(self, wallet_address: str) -> Dict[str, float]:
        """Get wallet balance for ETH and USDC.e"""
        try:
            from web3 import Web3
            
            w3 = Web3(Web3.HTTPProvider(self.arbitrum_rpc))
            
            # Get ETH balance
            eth_balance_wei = w3.eth.get_balance(wallet_address)
            eth_balance = float(w3.from_wei(eth_balance_wei, 'ether'))
            
            # Get USDC.e balance
            usdc_abi = [{
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf", 
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }]
            
            usdc_contract = w3.eth.contract(
                address=w3.to_checksum_address(USDC_ADDRESS),
                abi=usdc_abi
            )
            
            usdc_balance_raw = usdc_contract.functions.balanceOf(
                w3.to_checksum_address(wallet_address)
            ).call()
            usdc_balance = float(usdc_balance_raw) / (10 ** 6)  # USDC.e has 6 decimals
            
            return {
                "eth_balance": eth_balance,
                "usdc_balance": usdc_balance,
                "total_value_usd": eth_balance * 2000 + usdc_balance  # Rough estimate
            }
        except Exception as e:
            print(f"Error getting wallet balance: {e}")
            return {"eth_balance": 0, "usdc_balance": 0, "total_value_usd": 0}

# Initialize managers
db_manager = DatabaseManager(DATABASE_PATH)
rag_manager = RAGManager(RAG_SERVICE_URL)
wallet_manager = WalletManager()

@app.route('/api/wallet-status', methods=['GET'])
def get_wallet_status():
    """Get live wallet status with ETH balance and USD value"""
    try:
        rpc_url = os.getenv('ARBITRUM_RPC_URL')
        wallet_address = os.getenv('WALLET_ADDRESS')
        
        if not rpc_url or not wallet_address:
            return jsonify({"error": "Wallet or RPC not configured"}), 500

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            return jsonify({"error": "Could not connect to Arbitrum"}), 500
        
        eth_balance = get_eth_balance(w3, wallet_address)
        eth_usd_price = get_eth_price()
        wallet_usd_value = float(eth_balance) * eth_usd_price
        
        # Gas Reserve Logic (copy from agent)
        gas_reserve_eth = 0.002
        available_eth = float(eth_balance) - gas_reserve_eth
        available_usd = available_eth * eth_usd_price

        return jsonify({
            "eth_balance": f"{float(eth_balance):.8f}",
            "wallet_usd_value": f"{wallet_usd_value:.2f}",
            "available_for_betting_usd": f"{max(0, available_usd):.2f}"
        })
    except Exception as e:
        logger.error(f"Error getting wallet status: {e}")
        return jsonify({"error": "Failed to get wallet status"}), 500

@app.route('/api/bets', methods=['GET'])
def get_bets():
    try:
        db_manager = DatabaseManager(DATABASE_PATH)
        # Query the correct table where the agent saves decisions
        query = "SELECT market_id, teams, recommended_amount, position, confidence_score, reasoning, status, created_at FROM agent_recommendations ORDER BY created_at DESC"
        recommendations = db_manager.query_db(query)

        bet_list = []
        for row in recommendations:
            bet_list.append({
                "market_id": row[0],
                "teams": row[1],
                "amount": row[2],
                "position": row[3],
                "confidence": row[4],
                "reasoning": row[5],
                "status": row[6],
                "created_at": row[7]
            })

        return jsonify(bet_list)
    except Exception as e:
        logger.error(f"Error fetching bets from agent_recommendations: {e}")
        return jsonify({"error": "Failed to fetch bet recommendations"}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Get agent status and wallet information
    
    Query parameters:
    - agent_id: Specific agent ID (optional)
    """
    try:
        agent_id = request.args.get('agent_id')
        
        # Get agent sessions
        sessions = db_manager.get_agent_sessions()
        
        # Filter by agent_id if provided
        if agent_id:
            sessions = [s for s in sessions if s['agent_id'] == agent_id]
        
        # Get wallet balance if we have a wallet address
        wallet_info = {"message": "No wallet configured"}
        
        # Try to get wallet balance from environment or database
        # Check multiple possible environment variable names
        wallet_address = (
            os.getenv("ETH_WALLET_ADDRESS") or 
            os.getenv("WALLET_ADDRESS") or 
            os.getenv("ETH_ADDRESS")
        )
        
        # If no direct wallet address, try to derive from private key
        if not wallet_address:
            eth_private_key = os.getenv("ETH_PRIVATE_KEY")
            if eth_private_key:
                try:
                    from web3 import Web3
                    account = Web3().eth.account.from_key(eth_private_key)
                    wallet_address = account.address
                    print(f"Dashboard: Derived wallet address from private key: {wallet_address[:10]}...")
                except Exception as e:
                    print(f"Dashboard: Failed to derive wallet address from private key: {e}")
        
        if wallet_address:
            print(f"Dashboard: Fetching balance for wallet {wallet_address[:10]}...")
            wallet_info = wallet_manager.get_wallet_balance(wallet_address)
            print(f"Dashboard: Got balance - ETH: {wallet_info.get('eth_balance', 0):.6f}, USDC.e: {wallet_info.get('usdc_balance', 0):.2f}")
        else:
            print("Dashboard: No wallet address found in environment variables")
        
        # Get latest session info
        latest_session = sessions[0] if sessions else None
        
        result = {
            "agent_status": "running" if latest_session and latest_session['status'] == 'running' else "stopped",
            "latest_session": latest_session,
            "all_sessions": sessions,
            "wallet_info": wallet_info,
            "database_available": os.path.exists(DATABASE_PATH),
            "rag_service_url": RAG_SERVICE_URL,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to get status: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """
    Get betting performance summary with P&L metrics
    
    Query parameters:
    - agent_id: Specific agent ID (optional)
    - days: Number of days to look back (default: 30)
    """
    try:
        agent_id = request.args.get('agent_id')
        days = int(request.args.get('days', 30))
        
        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=days)
        
        # Get bets and strategies
        db_bets = db_manager.get_bets(agent_id)
        db_strategies = db_manager.get_strategies(agent_id)
        
        # Filter by date
        recent_bets = [
            bet for bet in db_bets 
            if datetime.fromisoformat(bet.created_at.replace('Z', '+00:00').replace('+00:00', '')) > date_threshold
        ]
        
        recent_strategies = [
            strategy for strategy in db_strategies
            if datetime.fromisoformat(strategy.created_at.replace('Z', '+00:00').replace('+00:00', '')) > date_threshold  
        ]
        
        # Get manual executions for real performance data
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Get manual executions within the time period
            date_threshold = datetime.now() - timedelta(days=days)
            cursor.execute("""
                SELECT executed_amount, user_notes, executed_at 
                FROM manual_executions 
                WHERE executed_at >= ?
                ORDER BY executed_at DESC
            """, (date_threshold.isoformat(),))
            
            manual_executions = cursor.fetchall()
        
        # Calculate real performance metrics from manual executions
        total_bets = len(manual_executions)
        won_bets = len([bet for bet in manual_executions if 'Won' in bet[1] or 'Win' in bet[1]])
        lost_bets = len([bet for bet in manual_executions if 'Lost' in bet[1]])
        pending_bets = len([bet for bet in manual_executions if 'Open' in bet[1]])
        
        win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
        
        # Calculate P&L from manual executions
        total_wagered = sum(bet[0] for bet in manual_executions if bet[0] > 0)  # Exclude $0 combo components
        total_losses = sum(bet[0] for bet in manual_executions if 'Lost' in bet[1])
        
        # For open bets, we don't know the outcome yet, so no winnings calculated
        total_winnings = 0  # Will be updated when bets are resolved
        net_pnl = total_winnings - total_losses
        
        # Extract P&L information from strategy parameters if available
        strategy_pnl = 0
        for strategy in recent_strategies:
            if strategy.parameters and isinstance(strategy.parameters, dict):
                pnl_value = strategy.parameters.get('pnl', 0) or strategy.parameters.get('pnl_usdce', 0)
                if pnl_value:
                    try:
                        strategy_pnl += float(pnl_value)
                    except:
                        pass
        
        result = {
            "summary_period_days": days,
            "total_bets": total_bets,
            "won_bets": won_bets,
            "lost_bets": lost_bets,
            "pending_bets": pending_bets,
            "win_rate_percentage": round(win_rate, 2),
            "total_wagered": round(total_wagered, 2),
            "total_winnings": round(total_winnings, 2),
            "total_losses": round(total_losses, 2),
            "net_pnl_from_bets": round(net_pnl, 2),
            "strategy_pnl": round(strategy_pnl, 2),
            "total_strategies": len(recent_strategies),
            "database_path": DATABASE_PATH,
            "agent_id_filter": agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to calculate summary: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """
    Get agent's pending recommendations for manual execution
    
    Returns:
        JSON response with pending recommendations
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get pending recommendations from the agent_recommendations table
        query = """
        SELECT 
            id, market_id, teams, recommended_amount, position, 
            confidence_score, reasoning, kelly_fraction, odds, 
            timestamp, status, created_at
        FROM agent_recommendations 
        WHERE status = 'pending_manual_execution'
        ORDER BY timestamp DESC
        LIMIT 20
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        
        recommendations = []
        position_names = {0: "Home", 1: "Away", 2: "Draw"}
        seen_markets = set()  # For deduplication
        
        for row in rows:
            try:
                odds_data = json.loads(row[8]) if row[8] else []
            except:
                odds_data = []
            
            # Create a unique key for deduplication (market_id + teams + position)
            dedup_key = f"{row[1]}_{row[2]}_{row[4]}"
            
            # Skip if we've already seen this combination
            if dedup_key in seen_markets:
                continue
            seen_markets.add(dedup_key)
            
            recommendation = {
                "id": row[0],
                "market_id": row[1],
                "teams": row[2],
                "recommended_amount": row[3],
                "position": row[4],
                "position_name": position_names.get(row[4], f"Position {row[4]}"),
                "confidence_score": row[5],
                "reasoning": row[6],
                "kelly_fraction": row[7],
                "odds": odds_data,
                "timestamp": row[9],
                "status": row[10],
                "created_at": row[11],
                "formatted_date": datetime.fromtimestamp(row[9]).strftime("%Y-%m-%d %H:%M:%S") if row[9] else None
            }
            recommendations.append(recommendation)
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "total_recommendations": len(recommendations),
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        })
        
    except sqlite3.Error as e:
        return jsonify({
            "status": "error", 
            "error": f"Database error: {str(e)}",
            "recommendations": []
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "recommendations": []
        }), 500

@app.route('/api/recommendations/combos', methods=['GET'])
def get_combo_recommendations():
    """Get agent combo/parlay recommendations"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get combo recommendations
        query = """
        SELECT 
            id, combo_id, teams, recommended_amount, combined_odds,
            confidence_score, reasoning, component_markets, component_teams,
            expected_profit, timestamp, status, created_at
        FROM combo_recommendations 
        WHERE status = 'pending_manual_execution'
        ORDER BY timestamp DESC
        LIMIT 10
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        combos = []
        for row in rows:
            try:
                component_markets = json.loads(row[7]) if row[7] else []
                component_teams = json.loads(row[8]) if row[8] else []
            except:
                component_markets = []
                component_teams = []
            
            combo = {
                'id': row[0],
                'combo_id': row[1],
                'teams': row[2],
                'recommended_amount': row[3],
                'combined_odds': row[4],
                'confidence_score': row[5],
                'reasoning': row[6],
                'component_markets': component_markets,
                'component_teams': component_teams,
                'expected_profit': row[9],
                'timestamp': row[10],
                'status': row[11],
                'created_at': row[12],
                'bet_type': 'parlay',
                'position_name': 'Combo/Parlay'
            }
            
            combos.append(combo)
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'combos': combos,
            'total_combos': len(combos),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "error": f"Error fetching combo recommendations: {str(e)}",
            "combos": []
        }), 500

@app.route('/api/recommendations/cycles', methods=['GET'])
def get_recommendations_cycles():
    """Get agent recommendations grouped by cycles"""
    try:
        recommendations = get_recommendations_by_cycle()
        
        # Group by cycles
        cycles = {}
        for rec in recommendations:
            cycle_key = rec['cycle_label']
            if cycle_key not in cycles:
                cycles[cycle_key] = {
                    'cycle_date': rec['cycle_date'],
                    'cycle_hour': rec['cycle_hour'],
                    'cycle_label': cycle_key,
                    'recommendations': [],
                    'count': 0
                }
            cycles[cycle_key]['recommendations'].append(rec)
            cycles[cycle_key]['count'] += 1
        
        # Convert to list and sort by date
        cycle_list = list(cycles.values())
        cycle_list.sort(key=lambda x: f"{x['cycle_date']} {x['cycle_hour']:02d}", reverse=True)
        
        return jsonify({
            'status': 'success',
            'cycles': cycle_list,
            'total_cycles': len(cycle_list),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'cycles': [],
            'total_cycles': 0,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/bets/manual_execution', methods=['POST'])
def mark_manual_execution():
    """Mark a recommendation as manually executed"""
    try:
        data = request.get_json()
        market_id = data.get('market_id')
        amount = data.get('amount')
        user_notes = data.get('notes', '')
        
        if not market_id or not amount:
            return jsonify({
                'status': 'error',
                'message': 'market_id and amount are required'
            }), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Update recommendation status
        cursor.execute("""
            UPDATE agent_recommendations 
            SET status = 'manually_executed', 
                user_notes = ?
            WHERE market_id = ? AND status = 'pending_manual_execution'
        """, (user_notes, market_id))
        
        # Insert into manual executions tracking
        cursor.execute("""
            INSERT INTO manual_executions 
            (market_id, executed_amount, executed_at, user_notes) 
            VALUES (?, ?, ?, ?)
        """, (market_id, amount, datetime.now().isoformat(), user_notes))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Manual execution recorded',
            'market_id': market_id,
            'amount': amount
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Superior Agents Dashboard API",
        "timestamp": datetime.now().isoformat(),
        "database_exists": os.path.exists(DATABASE_PATH),
        "rag_service_configured": bool(RAG_SERVICE_URL)
    })

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Serve the dashboard frontend"""
    from flask import send_from_directory
    return send_from_directory('/app/dashboard', 'index.html')

@app.route('/dashboard/<path:filename>')
def dashboard_static(filename):
    """Serve static dashboard files"""
    from flask import send_from_directory
    return send_from_directory('/app/dashboard', filename)

@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        "service": "Superior Agents Dashboard API",
        "endpoints": {
            "/api/bets": "GET - Retrieve all betting decisions and bets",
            "/api/status": "GET - Get agent status and wallet information", 
            "/api/summary": "GET - Get betting performance summary with P&L metrics",
            "/api/recommendations": "GET - Get agent's pending recommendations for manual execution",
            "/api/health": "GET - Health check endpoint",
            "/dashboard": "GET - Dashboard frontend HTML interface"
        },
        "parameters": {
            "agent_id": "Filter results by specific agent ID (optional)",
            "limit": "Maximum number of results for /api/bets (default: 100)",
            "days": "Number of days to look back for /api/summary (default: 30)"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/pnl_history", methods=["GET"])
def get_pnl_history():
    """
    Get historical P&L data for the chart.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Query to get all executed bets and parse P&L from user_notes
        query = """
        SELECT executed_at, executed_amount, user_notes
        FROM manual_executions
        ORDER BY executed_at ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        pnl_by_date = {}
        cumulative_pnl = 0

        for row in rows:
            date = datetime.fromisoformat(row[0]).strftime("%Y-%m-%d")
            amount = float(row[1])
            notes = row[2].lower()

            daily_pnl = 0
            if "won" in notes or "win" in notes:
                # Assuming an average odds of 1.8 for profit calculation
                daily_pnl = amount * 0.8
            elif "lost" in notes:
                daily_pnl = -amount

            if date not in pnl_by_date:
                pnl_by_date[date] = 0
            pnl_by_date[date] += daily_pnl

        sorted_dates = sorted(pnl_by_date.keys())
        
        labels = []
        data = []

        for date in sorted_dates:
            cumulative_pnl += pnl_by_date[date]
            labels.append(date)
            data.append(round(cumulative_pnl, 2))

        return jsonify({"status": "success", "labels": labels, "data": data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/recommendation/<int:rec_id>", methods=["GET"])
def get_recommendation_detail(rec_id):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        query = "SELECT * FROM agent_recommendations WHERE id = ? LIMIT 1"
        cursor.execute(query, (rec_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            # Map row to a dictionary
            keys = [description[0] for description in cursor.description]
            recommendation = dict(zip(keys, row))
            return jsonify({"status": "success", "data": recommendation})
        else:
            return jsonify({"status": "error", "message": "Recommendation not found"}), 404
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# In-memory state for agent control (for demonstration)
agent_control_state = {
    "status": "running",
    "max_risk": 20
}

@app.route("/api/agent/control", methods=["GET", "POST"])
def agent_control():
    global agent_control_state
    if request.method == "POST":
        data = request.get_json()
        if "status" in data and data["status"] in ["running", "paused"]:
            agent_control_state["status"] = data["status"]
        if "max_risk" in data:
            agent_control_state["max_risk"] = int(data["max_risk"])
        print(f"AGENT CONTROL - New state: {agent_control_state}")
        return jsonify({"status": "success", "new_state": agent_control_state})
    
    # GET request returns current state
    return jsonify(agent_control_state)

@app.route('/api/recommendations/<int:rec_id>/dismiss', methods=['POST'])
def dismiss_recommendation(rec_id):
    try:
        conn = get_db_connection()
        conn.execute("UPDATE agent_recommendations SET status = 'dismissed' WHERE id = ?", (rec_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Recommendation {rec_id} dismissed."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

if __name__ == '__main__':
    print("Starting Superior Agents Dashboard API...")
    print(f"Database path: {DATABASE_PATH}")
    print(f"RAG service URL: {RAG_SERVICE_URL}")
    print(f"Database exists: {os.path.exists(DATABASE_PATH)}")
    
    # Run on all interfaces so it can be accessed from outside the container
    app.run(host='0.0.0.0', port=5000, debug=True)
