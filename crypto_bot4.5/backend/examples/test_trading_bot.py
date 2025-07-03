#!/usr/bin/env python3
"""
Trading Bot Test Script
======================

Test script to debug the TradingBot class before running the full bot.
Tests each component individually to ensure everything works.
"""

import asyncio
import sys
import os
import traceback

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test imports first
print("🧪 Testing imports...")
try:
    from bot.trading_bot import TradingBot
    print("✅ TradingBot import successful")
except Exception as e:
    print(f"❌ TradingBot import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from keywordsai_tracing.main import KeywordsAITelemetry
    print("✅ KeywordsAI import successful")
except Exception as e:
    print(f"❌ KeywordsAI import failed: {e}")
    traceback.print_exc()

async def test_bot_initialization():
    """Test bot initialization without running the loop."""
    print("\n🧪 Testing bot initialization...")
    
    try:
        # Test with default config (hardcoded)
        bot = TradingBot()
        print("✅ Bot initialized with default config")
        print(f"   Interval: {bot.interval_minutes} minutes")
        print(f"   Min confidence: {bot.min_confidence}")
        print(f"   Max trade size: ${bot.max_trade_size}")
        print(f"   Supported symbols: {bot.supported_symbols}")
        
        # Test components
        if bot.exchange:
            print("✅ Exchange component initialized")
        else:
            print("❌ Exchange component failed")
            
        if bot.strategy:
            print("✅ Strategy component initialized")
        else:
            print("❌ Strategy component failed")
            
        return bot
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        traceback.print_exc()
        return None

async def test_market_data_collection(bot):
    """Test market data collection."""
    print("\n🧪 Testing market data collection...")
    
    try:
        market_data = await bot.get_comprehensive_market_data()
        print("✅ Market data collection successful")
        print(f"   Symbols: {list(market_data.prices.keys())}")
        print(f"   Prices: {market_data.prices}")
        print(f"   Has volumes: {bool(market_data.volumes)}")
        print(f"   Has momentum: {bool(market_data.momentum)}")
        return market_data
        
    except Exception as e:
        print(f"❌ Market data collection failed: {e}")
        traceback.print_exc()
        return None

async def test_portfolio_data(bot):
    """Test portfolio data collection."""
    print("\n🧪 Testing portfolio data collection...")
    
    try:
        portfolio_data = await bot.get_portfolio_data()
        print("✅ Portfolio data collection successful")
        print(f"   Balances: {portfolio_data.balances}")
        print(f"   Total value: ${portfolio_data.total_value_usd:.2f}")
        return portfolio_data
        
    except Exception as e:
        print(f"❌ Portfolio data collection failed: {e}")
        traceback.print_exc()
        return None

async def test_ai_decisions(bot, market_data, portfolio_data):
    """Test AI decision making."""
    print("\n🧪 Testing AI decision making...")
    
    if not market_data or not portfolio_data:
        print("⏸️  Skipping AI test - missing market or portfolio data")
        return None
    
    try:
        decisions = await bot.make_ai_decisions(market_data, portfolio_data)
        print("✅ AI decision making successful")
        print(f"   Overall confidence: {decisions.overall_confidence:.2f}")
        print(f"   Number of decisions: {len(decisions.decisions)}")
        
        for i, decision in enumerate(decisions.decisions):
            print(f"   Decision {i+1}: {decision.action} ${decision.amount_usd} {decision.asset}")
            print(f"      Confidence: {decision.confidence:.2f}")
            print(f"      Reasoning: {decision.reasoning}")
        
        return decisions
        
    except Exception as e:
        print(f"❌ AI decision making failed: {e}")
        traceback.print_exc()
        return None

async def test_single_cycle(bot):
    """Test a single trading cycle using the proper workflow."""
    print("\n🧪 Testing single trading cycle (using workflow)...")
    
    try:
        # Call the complete workflow - this will group all tasks under one trace
        cycle_result = await bot.execute_trading_cycle()
        
        print("✅ Trading cycle workflow completed successfully!")
        print(f"   Cycle number: {cycle_result['cycle_number']}")
        print(f"   Status: {cycle_result['status']}")
        
        # Display results from the workflow
        if cycle_result['market_data']:
            market_data = cycle_result['market_data']
            print(f"   Market data: {list(market_data.prices.keys())}")
            print(f"   Prices: {market_data.prices}")
        
        if cycle_result['portfolio_data']:
            portfolio_data = cycle_result['portfolio_data']
            print(f"   Portfolio: {portfolio_data.balances}")
            print(f"   Total value: ${portfolio_data.total_value_usd:.2f}")
        
        if cycle_result['decisions']:
            decisions = cycle_result['decisions']
            print(f"   AI confidence: {decisions.overall_confidence:.2f}")
            print(f"   Number of decisions: {len(decisions.decisions)}")
            for i, decision in enumerate(decisions.decisions):
                print(f"   Decision {i+1}: {decision.action} ${decision.amount_usd} {decision.asset}")
        
        if cycle_result['executed_trades']:
            print(f"   Trades executed: {len(cycle_result['executed_trades'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Trading cycle workflow failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Trading Bot Test Suite")
    print("=" * 50)
    
    # Test 1: Bot initialization
    bot = await test_bot_initialization()
    if not bot:
        print("\n❌ Tests failed at initialization")
        return
    
    # Test 2: Individual components
    print("\n📊 Testing individual components...")
    
    # Test 3: Single cycle
    success = await test_single_cycle(bot)
    
    # Cleanup
    await bot.cleanup()
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Bot is ready to run.")
        print("\n🚀 You can now run the bot with:")
        print("   python run_bot.py")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("\n📊 Next: Monitor your bot on KeywordsAI platform")
    print("   Make sure to set environment variables:")
    print("   - OPENAI_API_KEY")
    print("   - KEYWORDSAI_API_KEY")

if __name__ == "__main__":
    asyncio.run(main()) 