#!/usr/bin/env python3
"""
Main entry point for the LangGraph Telegram Bot.
"""

import sys
import signal
import asyncio
from bot.config import Config
from bot.telegram_handler import TelegramBot

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\nShutting down bot...")
    sys.exit(0)

async def main():
    """Main function to run the bot."""
    try:
        # Validate configuration
        Config.validate()
        print("✅ Configuration validated successfully")
        
        # Create and start the bot
        bot = TelegramBot()
        print("🤖 Bot initialized successfully")
        print("🚀 Starting bot... (Press Ctrl+C to stop)")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the bot
        bot.run()
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease make sure to:")
        print("1. Copy env.example to .env")
        print("2. Set your OpenAI API key in .env")
        print("3. Set your Telegram bot token in .env")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
