#!/usr/bin/env python3
"""
LLM Connection Test Script - Brain Diagnostic
Tests OpenRouter connection and LLM model communication
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add agent src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from client.openrouter import OpenRouter, OpenRouterError

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
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model": os.getenv("AGENT_LLM_MODEL", "deepseek/deepseek-r1")
    }

def test_llm_connection():
    """Test LLM connection through OpenRouter"""
    print("=" * 60)
    print("🧠 BRAIN DIAGNOSTIC - LLM CONNECTION TEST")
    print("=" * 60)
    
    # Load environment variables
    env_vars = load_env_vars()
    
    print(f"API Key: {'✓ Present' if env_vars['api_key'] else '✗ Missing'}")
    print(f"Model: {env_vars['model']}")
    
    if not env_vars['api_key']:
        print("\n❌ FAILURE: OPENROUTER_API_KEY not found in environment")
        print("Please set OPENROUTER_API_KEY in your .env file")
        return False
    
    try:
        # Initialize OpenRouter client
        print(f"\n🔗 Initializing OpenRouter client...")
        client = OpenRouter(
            api_key=env_vars['api_key'],
            base_url="https://openrouter.ai/api/v1",
            model=env_vars['model']
        )
        print("✓ Client initialized successfully")
        
        # Test simple completion
        print(f"\n🧪 Testing LLM completion with model: {env_vars['model']}")
        
        test_messages = [
            {"role": "user", "content": "Reply with exactly: 'Brain diagnostic successful'"}
        ]
        
        response = client.create_chat_completion(
            messages=test_messages,
            max_tokens=50,
            temperature=0.1
        )
        
        print(f"\n📤 Request sent to: {env_vars['model']}")
        print(f"📥 Response received: {response}")
        
        if "successful" in response.lower():
            print("\n✅ SUCCESS: Brain diagnostic completed successfully!")
            print("🧠 LLM connection is working properly")
            return True
        else:
            print(f"\n⚠️ PARTIAL SUCCESS: LLM responded but unexpected content: {response}")
            return True
            
    except OpenRouterError as e:
        print(f"\n❌ OPENROUTER ERROR: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    """Main diagnostic function"""
    try:
        success = test_llm_connection()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 BRAIN DIAGNOSTIC: PASSED")
            print("The LLM 'brain' is functioning correctly")
        else:
            print("💥 BRAIN DIAGNOSTIC: FAILED")
            print("The LLM 'brain' needs attention")
        print("=" * 60)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
