#!/usr/bin/env python3
"""
Standalone test script for OvertimeService integration.
This script tests the OvertimeService without depending on the complex import system.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_overtime_service():
    """Test the OvertimeService integration."""
    print("=== Testing OvertimeService Integration ===")
    
    try:
        # Import the service directly
        from services.overtime_service import OvertimeService
        
        # Initialize the service
        service = OvertimeService()
        print("✅ OvertimeService initialized successfully")
        
        # Test fetching market data
        print("\n--- Attempting to fetch market data from Overtime Protocol... ---")
        market_data = service.get_sports_markets()
        
        if market_data:
            print(f"--- SUCCESS: Fetched {len(market_data)} markets. ---")
            # Print the first 2 markets for verification
            print(json.dumps(market_data[:2], indent=2))
            return True
        else:
            print("--- FAILURE: No market data received. ---")
            return False
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_overtime_service()
    if success:
        print("\n🎉 OvertimeService integration test PASSED!")
    else:
        print("\n💥 OvertimeService integration test FAILED!")
        sys.exit(1)
