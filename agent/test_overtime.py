#!/usr/bin/env python3
"""
Simple test file for OvertimeService integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.overtime_service import OvertimeService
import json

if __name__ == "__main__":
    # Αυτός ο κώδικας είναι προσωρινός, μόνο για τη δοκιμή
    print("--- Initializing Test Run ---")
    
    # Προσωρινή άμεση κλήση στο service για επαλήθευση
    overtime = OvertimeService()
    markets = overtime.get_sports_data()
    if markets:
        print(f"--- SUCCESS: Fetched {len(markets)} markets from Overtime. ---")
        print("--- Sample Market Data: ---")
        print(json.dumps(markets[:1], indent=2))
    else:
        print("--- FAILURE: Could not fetch market data. ---")
