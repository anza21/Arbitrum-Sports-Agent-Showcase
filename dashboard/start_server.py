#!/usr/bin/env python3
"""
Dashboard Server Starter
========================

Starts the Superior Agents Dashboard Flask application.

This script sets up the environment and starts the Flask application
to serve the dashboard API endpoints.
"""

import os
import sys

# Add the dashboard directory to Python path
sys.path.insert(0, '/app/dashboard')

# Import and run the Flask application
from app import app

if __name__ == '__main__':
    print("🚀 Starting Superior Agents Dashboard...")
    print(f"📊 Database path: {os.getenv('SQLITE_PATH', '/app/agent/db/superior-agents.db')}")
    print(f"🔗 RAG service URL: {os.getenv('RAG_SERVICE_URL', 'http://localhost:8080')}")
    print(f"⛓️ Arbitrum RPC URL: {os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')}")
    print(f"💰 Wallet address: {os.getenv('WALLET_ADDRESS', 'Not configured')}")
    
    # Run Flask application
    app.run(host='0.0.0.0', port=5000, debug=False)