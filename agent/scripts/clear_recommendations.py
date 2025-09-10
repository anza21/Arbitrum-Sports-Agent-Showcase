#!/usr/bin/env python3
"""
Clear Recommendations Database Script
=====================================

This script clears all old, potentially corrupted recommendations from the database
to allow for fresh, clean data generation.

Author: Superior Agents System
"""

import sqlite3
import os
import sys

def clear_recommendations():
    """Clear all recommendations from the database"""
    try:
        # Database path
        db_path = "/app/agent/db/superior-agents.db"
        
        print("🗑️  Starting database cleanup...")
        print(f"📁 Database path: {db_path}")
        
        # Check if database exists
        if not os.path.exists(db_path):
            print(f"❌ Database not found at {db_path}")
            return False
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count existing recommendations
        cursor.execute("SELECT COUNT(*) FROM agent_recommendations")
        count_before = cursor.fetchone()[0]
        print(f"📊 Found {count_before} existing recommendations")
        
        if count_before == 0:
            print("✅ Database is already clean - no recommendations to delete")
            conn.close()
            return True
        
        # Clear all recommendations
        print("🧹 Clearing all recommendations...")
        cursor.execute("DELETE FROM agent_recommendations")
        
        # Commit changes
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM agent_recommendations")
        count_after = cursor.fetchone()[0]
        
        # Close connection
        conn.close()
        
        if count_after == 0:
            print(f"✅ Successfully cleared {count_before} recommendations")
            print("🎯 Database is now clean and ready for fresh data")
            return True
        else:
            print(f"❌ Failed to clear all recommendations. Remaining: {count_after}")
            return False
            
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧹 SUPERIOR AGENTS DATABASE CLEANUP")
    print("=" * 50)
    
    success = clear_recommendations()
    
    if success:
        print("\n✅ Database cleanup completed successfully!")
        print("🚀 Ready for fresh data generation")
        sys.exit(0)
    else:
        print("\n❌ Database cleanup failed!")
        sys.exit(1)
