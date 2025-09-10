#!/usr/bin/env python3
"""
RAG Memory Test Script - Memory Diagnostic
Tests RAG API connection and basic functionality
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

def load_env_vars():
    """Load environment variables from .env file"""
    # Look for .env in agent directory
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        # Look for .env in project root
        env_path = Path(__file__).parent.parent.parent / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from: {env_path}")
    else:
        print("⚠️ No .env file found - using system environment variables")
    
    return {
        "rag_url": os.getenv("RAG_SERVICE_URL", "http://rag-api:32771")
    }

def test_health_check(rag_url):
    """Test RAG API health endpoint"""
    print("\n" + "="*50)
    print("📡 TEST 1: RAG API HEALTH CHECK")
    print("="*50)
    
    try:
        # Test health endpoint
        health_url = f"{rag_url.rstrip('/')}/health"
        print(f"🔗 Testing health endpoint: {health_url}")
        
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print(f"📥 Response: {response.status_code} - {response.text}")
            print("✅ SUCCESS: RAG API health check passed!")
            return True
        else:
            print(f"❌ FAILURE: Health check failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR: Could not connect to RAG API")
        print(f"Error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ TIMEOUT ERROR: RAG API did not respond in time")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_save_and_search(rag_url):
    """Test RAG API save and search functionality"""
    print("\n" + "="*50)
    print("💾 TEST 2: RAG SAVE & SEARCH FUNCTIONALITY")
    print("="*50)
    
    try:
        # Test save endpoint directly
        print("🔗 Testing save endpoint directly...")
        save_url = f"{rag_url.rstrip('/')}/save_result_batch_v4"
        
        # Create test payload
        test_payload = [{
            "notification_key": "Lakers vs Warriors Over 220.5 - Memory Diagnostic Test",
            "strategy_data": json.dumps({
                "strategy_id": "test_memory_diagnostic_001",
                "summarized_desc": "Memory diagnostic test strategy",
                "outcome": "pending",
                "confidence": 0.8
            }),
            "reference_id": "test_memory_diagnostic_001",
            "agent_id": "test_agent_diagnostic",
            "session_id": "test_session_diagnostic",
            "created_at": datetime.now().isoformat()
        }]
        
        print(f"📤 Sending save request to: {save_url}")
        save_response = requests.post(save_url, json=test_payload, timeout=30)
        
        if save_response.status_code == 200:
            print(f"📥 Save response: {save_response.json()}")
            print("✅ SUCCESS: Data saved to RAG memory!")
            save_success = True
        else:
            print(f"❌ Save failed with status {save_response.status_code}")
            print(f"Response: {save_response.text}")
            save_success = False
        
        # Test search endpoint
        print("\n🔍 Testing search functionality...")
        search_url = f"{rag_url.rstrip('/')}/relevant_strategy_raw_v4"
        search_payload = {
            "query": "Lakers Warriors diagnostic test",
            "agent_id": "test_agent_diagnostic", 
            "session_id": "test_session_diagnostic",
            "top_k": 5
        }
        
        print(f"📤 Sending search request to: {search_url}")
        search_response = requests.post(search_url, json=search_payload, timeout=30)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(f"📥 Search results: {len(search_data.get('data', []))} items found")
            
            if search_data.get('data'):
                for i, item in enumerate(search_data['data'][:3]):  # Show first 3
                    ref_id = item.get('metadata', {}).get('reference_id', 'unknown')
                    print(f"  Result {i+1}: {ref_id}")
                    
                print("✅ SUCCESS: Search functionality working!")
                search_success = True
            else:
                print("⚠️ PARTIAL SUCCESS: Search endpoint working but no results returned")
                search_success = True
        else:
            print(f"❌ Search failed with status {search_response.status_code}")
            print(f"Response: {search_response.text}")
            search_success = False
        
        return save_success and search_success
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR: Could not connect to RAG API")
        print(f"Error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ TIMEOUT ERROR: RAG API did not respond in time")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR during save/search test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main diagnostic function"""
    print("=" * 60)
    print("🧠 MEMORY DIAGNOSTIC - RAG API TEST")
    print("=" * 60)
    
    # Load environment variables
    env_vars = load_env_vars()
    rag_url = env_vars['rag_url']
    
    print(f"RAG Service URL: {rag_url}")
    
    try:
        # Test 1: Health Check
        health_success = test_health_check(rag_url)
        
        # Test 2: Save & Search (only if health check passed)
        if health_success:
            save_search_success = test_save_and_search(rag_url)
        else:
            print("\n⚠️ Skipping save/search test due to failed health check")
            save_search_success = False
        
        # Final results
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS:")
        print("=" * 60)
        print(f"Health Check: {'✅ PASSED' if health_success else '❌ FAILED'}")
        print(f"Save & Search: {'✅ PASSED' if save_search_success else '❌ FAILED'}")
        
        overall_success = health_success and save_search_success
        
        print("\n" + "=" * 60)
        if overall_success:
            print("🎉 MEMORY DIAGNOSTIC: PASSED")
            print("The RAG 'memory' is functioning correctly")
        else:
            print("💥 MEMORY DIAGNOSTIC: FAILED")
            print("The RAG 'memory' needs attention")
        print("=" * 60)
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
