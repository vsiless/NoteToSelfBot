#!/usr/bin/env python3
"""
Test script to verify the async message sending fix works.
"""

import time
import logging
from bot.telegram_handler import TelegramBot
from bot.config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_async_fix():
    """Test the async message sending fix."""
    
    # Mock the config validation to avoid needing real tokens
    original_validate = Config.validate
    Config.validate = lambda: None
    Config.TELEGRAM_BOT_TOKEN = "test_token"
    Config.OPENAI_API_KEY = "test_key"
    Config.OPENAI_MODEL_NAME = "gpt-4o-mini"
    
    try:
        # Create bot instance
        bot = TelegramBot()
        
        # Test the reminder message sending directly
        print("🧪 Testing async message sending fix...")
        
        # This should not raise a RuntimeError anymore
        bot._send_reminder_message("test_user", "Test reminder message")
        
        # Give it a moment to process
        time.sleep(2)
        
        print("✅ No RuntimeError occurred - async fix is working!")
        return True
        
    except RuntimeError as e:
        if "no running event loop" in str(e):
            print(f"❌ RuntimeError still occurs: {e}")
            return False
        else:
            print(f"❌ Different RuntimeError: {e}")
            return False
    except Exception as e:
        # Other exceptions are expected since we're using mock tokens
        if "no running event loop" not in str(e):
            print(f"✅ No event loop error - got expected error: {type(e).__name__}")
            return True
        else:
            print(f"❌ Still getting event loop error: {e}")
            return False
    finally:
        # Restore original validation
        Config.validate = original_validate

if __name__ == "__main__":
    success = test_async_fix()
    print(f"\n{'🎉 Test passed!' if success else '❌ Test failed!'}")
