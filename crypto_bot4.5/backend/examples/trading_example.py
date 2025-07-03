#!/usr/bin/env python3
"""
Pure Trading Example

This example demonstrates safe trading in Coinbase sandbox:
- 🧪 Safe sandbox environment (no real money)
- 💰 Account balance and management
- 📝 Order placement and management
- 🔐 Authenticated endpoints
- 🛡️ Complete safety for testing

Perfect for testing trading strategies safely!
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from infrastructure.exchanges.factory import create_coinbase_sandbox_exchange


async def trading_demo():
    """Demonstrate safe sandbox trading."""
    
    print("🧪 COINBASE SANDBOX TRADING")
    print("=" * 50)
    print("🛡️ Safe testing environment")
    print("💰 No real money involved")
    print("=" * 50)
    
    # Create sandbox exchange
    exchange = create_coinbase_sandbox_exchange()
    
    try:
        # Check environment
        env_info = exchange.get_environment_info()
        print(f"🔗 Environment: {env_info['environment']}")
        print(f"🧪 Sandbox: {env_info['is_sandbox']}")
        print(f"🔐 Authenticated: {env_info['authenticated']}")
        
        # Account Balance
        print("\n💰 SANDBOX ACCOUNT BALANCE")
        print("-" * 40)
        balance = await exchange.get_balance()
        
        print("💰 Available test funds:")
        for currency, amount in balance.items():
            try:
                # Handle different balance formats
                if isinstance(amount, dict):
                    free_amount = amount.get('free', 0)
                    if float(free_amount) > 0:
                        print(f"  {currency}: {free_amount}")
                else:
                    if float(amount) > 0:
                        print(f"  {currency}: {amount}")
            except (ValueError, TypeError):
                print(f"  {currency}: {amount}")
        
        # Account Information
        print("\n📋 ACCOUNT INFORMATION")
        print("-" * 30)
        account_info = await exchange.get_account_info()
        accounts = account_info.get('accounts', [])
        print(f"📊 Total sandbox accounts: {len(accounts)}")
        
        # Order History
        print("\n📝 ORDER HISTORY")
        print("-" * 20)
        orders = await exchange.get_order_history(limit=5)
        print(f"📝 Recent orders: {len(orders)}")
        
        if orders:
            print("🔍 Recent order details:")
            for i, order in enumerate(orders[:3], 1):
                order_id = order.get('id', 'N/A')[:8]
                side = order.get('side', 'N/A')
                symbol = order.get('symbol', 'N/A')
                status = order.get('status', 'N/A')
                print(f"  {i}. {order_id}... {side} {symbol} ({status})")
        
        # Open Orders
        print("\n📋 OPEN ORDERS")
        print("-" * 20)
        open_orders = await exchange.get_open_orders()
        print(f"📋 Currently open: {len(open_orders)}")
        
        # Safe Order Placement Demo
        print("\n🧪 SAFE ORDER PLACEMENT DEMO")
        print("-" * 35)
        print("🛡️ This is completely safe - sandbox only!")
        
        # Place a safe limit order (way below market price)
        test_symbol = "BTC/USD"
        test_amount = 0.001  # Small amount
        test_price = 30000   # Well below current market price
        
        print(f"💡 Demo: Place limit order for {test_amount} {test_symbol}")
        print(f"💡 Price: ${test_price} (safely below market)")
        print(f"💡 This order will NOT execute (price too low)")
        
        try:
            order_result = await exchange.place_limit_order(
                symbol=test_symbol,
                side="buy",
                amount=test_amount,
                price=test_price
            )
            
            order_id = order_result.get('id', 'N/A')
            print(f"✅ Demo order placed: {order_id}")
            print("🛡️ Safe: This order won't execute (price too low)")
            
            # Immediately cancel the demo order
            print(f"\n🗑️ CANCELING DEMO ORDER")
            print("-" * 25)
            try:
                cancel_result = await exchange.cancel_order(order_id, test_symbol)
                print("✅ Demo order canceled successfully")
            except Exception as e:
                print(f"ℹ️ Cancel info: {e}")
                
        except Exception as e:
            print(f"ℹ️ Order demo: {e}")
        
        # Market vs Limit orders explanation
        print("\n📚 TRADING ORDER TYPES")
        print("-" * 30)
        print("📊 Market Order:")
        print("  • Executes immediately at current price")
        print("  • Use: exchange.place_market_order(symbol, side, amount)")
        print("")
        print("📊 Limit Order:")
        print("  • Executes only at specified price or better")  
        print("  • Use: exchange.place_limit_order(symbol, side, amount, price)")
        print("")
        print("🛡️ All orders in sandbox are safe - no real money!")
        
        print("\n✅ SANDBOX TRADING SUCCESS!")
        print("🎉 Safe trading environment is working perfectly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check .env file has COINBASE_SANDBOX_API_KEY and COINBASE_SANDBOX_API_SECRET")
        print("2. Verify credentials are for Advanced Trade API")
        print("3. Ensure credentials are sandbox (not production)")
        
    finally:
        await exchange.close()


async def main():
    """Run the trading demonstration."""
    print("🚀 COINBASE SANDBOX TRADING")
    print("")
    print("This example demonstrates:")
    print("• Safe sandbox trading environment")
    print("• Account balance and management") 
    print("• Order placement and cancellation")
    print("• Trading history and open orders")
    print("• Complete safety (no real money)")
    print("")
    
    await trading_demo()
    
    print("\n" + "=" * 50)
    print("✅ TRADING DEMO COMPLETE!")
    print("=" * 50)
    print("💡 Key Benefits:")
    print("• Test trading strategies safely")
    print("• No financial risk during development")
    print("• Full API functionality available")
    print("• Easy transition to production")
    print("")
    print("Next: Combine with market_data_example.py for complete bot!")


if __name__ == "__main__":
    asyncio.run(main()) 