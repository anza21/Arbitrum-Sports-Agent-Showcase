#!/usr/bin/env python3
"""
Test script for the Dashboard API
"""

import os
import sys
import time
import requests
import json
from threading import Thread

# Set up environment variables
os.environ['SQLITE_PATH'] = '/home/anza/project/superior-agents-clean/superior-agent-v1/db/superior-agents.db'
os.environ['RAG_SERVICE_URL'] = 'http://localhost:8080'
os.environ['ARBITRUM_RPC_URL'] = 'https://arb1.arbitrum.io/rpc'

# Import our app
from app import app

def start_server():
    """Start Flask server in a separate thread"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def test_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:5000"
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    endpoints_to_test = [
        "/api/health",
        "/api/status", 
        "/api/bets",
        "/api/summary",
        "/"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\n--- Testing {endpoint} ---")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    print("Response (formatted):")
                    print(json.dumps(json_data, indent=2))
                except:
                    print("Response (raw):")
                    print(response.text)
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error testing {endpoint}: {e}")

if __name__ == "__main__":
    print("Starting Dashboard API Test...")
    
    # Start server in background thread
    server_thread = Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Test endpoints
    test_endpoints()
    
    print("\nAPI testing completed!")
