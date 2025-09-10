#!/usr/bin/env python3
"""
Full System Diagnostic Script for Superior Agent v1
===================================================

This script performs comprehensive testing of all core agent services
to verify system health and functionality.

Usage: python agent/scripts/full_system_diagnostic.py
"""

import os
import sys
import traceback
import docker
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import services
from agent.src.services.wallet_service import WalletService
from agent.src.services.news_service import NewsService
from agent.src.services.weather_service import WeatherService
from agent.src.services.the_odds_service import TheOddsService
from agent.src.client.rag import RAGClient
from agent.src.genner import get_genner
from agent.src.container import ContainerManager
from agent.src import config
from agent.src.config import ClaudeConfig
import uuid

def print_test_header(service_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"Testing {service_name}...")
    print(f"{'='*60}")

def print_result(success, message=""):
    """Print test result with color coding"""
    if success:
        print(f"✅ SUCCESS {message}")
    else:
        print(f"❌ FAILURE {message}")

def test_wallet_service():
    """Test WalletService USDC and ETH balance retrieval"""
    print_test_header("WalletService")
    
    try:
        wallet_service = WalletService()
        
        # Test wallet address (Commander's wallet)
        test_wallet = "0xCbAAA5415B9A7A64b4a11d88a64917173eA1A187"
        
        # Test USDC balance
        print("- Testing USDC balance retrieval...")
        usdc_balance = wallet_service.get_usdc_balance(test_wallet)
        
        if isinstance(usdc_balance, float) and usdc_balance >= 0:
            print_result(True, f"- USDC Balance: {usdc_balance}")
        else:
            print_result(False, f"- Invalid USDC balance: {usdc_balance}")
            return False
        
        # Test ETH balance
        print("- Testing ETH balance retrieval...")
        eth_balance = wallet_service.get_eth_balance(test_wallet)
        
        if isinstance(eth_balance, float) and eth_balance >= 0:
            print_result(True, f"- ETH Balance: {eth_balance}")
            return True
        else:
            print_result(False, f"- Invalid ETH balance: {eth_balance}")
            return False
            
    except Exception as e:
        print_result(False, f"- Exception: {str(e)}")
        return False

def test_news_service():
    """Test NewsService API functionality"""
    print_test_header("NewsService")
    
    try:
        news_service = NewsService()
        
        # Test news retrieval
        print("- Testing news retrieval for 'Arbitrum'...")
        news_articles = news_service.get_news_for_team("Arbitrum")
        
        if isinstance(news_articles, list):
            print_result(True, f"- Retrieved {len(news_articles)} articles")
            return True
        else:
            print_result(False, f"- Invalid response: {type(news_articles)}")
            return False
            
    except Exception as e:
        print_result(False, f"- Exception: {str(e)}")
        return False

def test_weather_service():
    """Test WeatherService API functionality"""
    print_test_header("WeatherService")
    
    try:
        weather_service = WeatherService()
        
        # Test weather retrieval
        print("- Testing weather retrieval for 'London'...")
        weather_data = weather_service.get_weather_by_city("London")
        
        if weather_data is not None and isinstance(weather_data, dict):
            temp = weather_data.get('temperature', {}).get('current', 'N/A')
            print_result(True, f"- Weather data retrieved, temperature: {temp}°C")
            return True
        else:
            print_result(False, f"- Invalid weather data: {weather_data}")
            return False
            
    except Exception as e:
        print_result(False, f"- Exception: {str(e)}")
        return False

def test_odds_service():
    """Test TheOddsService API functionality"""
    print_test_header("TheOddsService")
    
    try:
        # Initialize with test mode
        odds_service = TheOddsService(test_mode=True)
        
        # Test available sports
        print("- Testing available sports retrieval...")
        sports = odds_service.get_available_sports()
        
        if isinstance(sports, list) and len(sports) > 0:
            print_result(True, f"- Retrieved {len(sports)} sports")
            
            # Test odds for first sport
            first_sport = sports[0]['key']
            print(f"- Testing odds retrieval for '{first_sport}'...")
            odds = odds_service.get_sports_odds(first_sport)
            
            if isinstance(odds, list):
                print_result(True, f"- Retrieved {len(odds)} odds records")
                return True
            else:
                print_result(False, f"- Invalid odds data: {type(odds)}")
                return False
        else:
            print_result(False, f"- Invalid sports list: {sports}")
            return False
            
    except Exception as e:
        print_result(False, f"- Exception: {str(e)}")
        return False

def test_genner_llm():
    """Test Genner LLM functionality"""
    print_test_header("Genner (LLM)")
    
    try:
        # Try to get a working LLM backend
        backends_to_try = ["claude", "openai", "deepseek"]
        
        for backend in backends_to_try:
            try:
                print(f"- Attempting to initialize {backend} backend...")
                genner = get_genner(
                    backend=backend,
                    stream_fn=None
                )
                
                # Test simple generation
                from agent.src.agent_types import ChatHistory, Message
                
                test_messages = ChatHistory([
                    Message(role="user", content="What is the Kelly Criterion? Please provide a brief explanation in 2-3 sentences.")
                ])
                
                print(f"- Testing generation with {backend}...")
                result = genner.ch_completion(test_messages)
                
                if result.is_ok():
                    response = result.unwrap()
                    if isinstance(response, str) and len(response) > 10:
                        print_result(True, f"- LLM generated {len(response)} character response using {backend}")
                        print(f"- Sample response: {response[:100]}...")
                        return True
                    else:
                        print_result(False, f"- Invalid response from {backend}: {response}")
                else:
                    print_result(False, f"- {backend} failed: {result.err()}")
                    
            except Exception as e:
                print(f"- {backend} backend failed: {str(e)}")
                continue
        
        print_result(False, "- All LLM backends failed")
        return False
        
    except Exception as e:
        print_result(False, f"- Exception: {str(e)}")
        return False

def test_rag_client():
    """Test RAG Client save/search functionality"""
    print_test_header("RAG Client")
    
    try:
        # Get RAG service URL from environment
        rag_url = os.getenv('RAG_SERVICE_URL', 'http://rag-api:32771')
        
        # Initialize RAG client
        print(f"- Initializing RAG client with URL: {rag_url}...")
        rag_client = RAGClient(
            agent_id="diagnostic_test",
            session_id=str(uuid.uuid4()),
            base_url=rag_url
        )
        
        # Test simple save operation (using update_document method)
        print("- Testing document save...")
        test_doc = {
            "strategy": "Test diagnostic strategy",
            "content": "This is a test document for system diagnostics",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        save_result = rag_client.update_document("diagnostic_test_doc", test_doc)
        
        if save_result:
            print_result(True, "- Document saved successfully")
            
            # Test search operation
            print("- Testing document search...")
            search_result = rag_client.query_documents("diagnostic strategy test")
            
            if search_result:
                print_result(True, f"- Search completed, result type: {type(search_result)}")
                return True
            else:
                print_result(False, "- Search returned empty result")
                return False
        else:
            print_result(False, "- Document save failed")
            return False
            
    except Exception as e:
        print_result(False, f"- Exception: {str(e)}")
        print(f"- Traceback: {traceback.format_exc()}")
        return False

def test_container_manager():
    """Test ContainerManager initialization"""
    print_test_header("ContainerManager")
    
    try:
        # Initialize Docker client
        print("- Initializing Docker client...")
        docker_client = docker.from_env()
        
        # Test ContainerManager initialization
        print("- Testing ContainerManager initialization...")
        container_manager = ContainerManager(
            client=docker_client,
            container_identifier="diagnostic-test-container",
            host_cache_folder="/tmp/diagnostic_cache",
            in_con_env={"PYTHONUNBUFFERED": "1"}
        )
        
        print_result(True, "- ContainerManager initialized successfully")
        return True
        
    except Exception as e:
        print_result(False, f"- Exception: {str(e)}")
        return False

def main():
    """Run complete system diagnostic"""
    print("🚀 SUPERIOR AGENT v1 - FULL SYSTEM DIAGNOSTIC")
    print("=" * 80)
    print("Checking all core services and components...")
    
    # Track results
    test_results = {}
    
    # Run all tests
    test_results["WalletService"] = test_wallet_service()
    test_results["NewsService"] = test_news_service()
    test_results["WeatherService"] = test_weather_service()
    test_results["TheOddsService"] = test_odds_service()
    test_results["Genner (LLM)"] = test_genner_llm()
    test_results["RAG Client"] = test_rag_client()
    test_results["ContainerManager"] = test_container_manager()
    
    # Print summary
    print("\n" + "=" * 80)
    print("🏁 DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for service, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{service:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} services operational")
    
    if passed == total:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
    elif passed >= total * 0.7:
        print("⚠️  MOST SYSTEMS OPERATIONAL - Minor issues detected")
    else:
        print("🚨 CRITICAL ISSUES DETECTED - System needs attention")
    
    return test_results

if __name__ == "__main__":
    main()
