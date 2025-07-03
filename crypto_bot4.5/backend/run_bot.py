#!/usr/bin/env python3
"""
Trading Bot Startup Script
==========================

Simple script to start the 30-minute autonomous trading bot.
Run this from the backend directory.
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bot.trading_bot import TradingBot

async def main():
    """Start the trading bot."""
    print("🚀 Starting 30-Minute Autonomous Crypto Trading Bot")
    print("="*50)
    print("📊 Features:")
    print("   • AI-powered trading decisions (GPT-4o)")
    print("   • KeywordsAI tracing and monitoring")
    print("   • 30-minute automated cycles")
    print("   • Comprehensive market analysis")
    print("   • Safe sandbox environment")
    print()
    print("⏸️  Press Ctrl+C to stop gracefully")
    print("="*50)
    
    # Create and run the bot
    bot = TradingBot()
    
    try:
        await bot.run_30min_loop()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
    finally:
        await bot.cleanup()
        print("✅ Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main()) 