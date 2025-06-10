#!/usr/bin/env python3
"""
Pure Market Data Example

This example demonstrates accessing real market data from Coinbase:
- 🌍 Real-time prices and order books
- 📊 Historical candles and trading volume  
- 📋 700+ trading pairs available
- 🔓 NO authentication needed
- 💰 NO sandbox required

Perfect for market analysis and price monitoring!
"""

import asyncio
import aiohttp
import json
from datetime import datetime


class CoinbaseMarketData:
    """Simple class for accessing Coinbase public market data."""
    
    def __init__(self):
        self.base_url = "https://api.coinbase.com"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_products(self):
        """Get all available trading products."""
        url = f"{self.base_url}/api/v3/brokerage/market/products"
        async with self.session.get(url) as response:
            data = await response.json()
            return data.get('products', [])
    
    async def get_ticker(self, product_id):
        """Get current price for a product."""
        url = f"{self.base_url}/api/v3/brokerage/market/products/{product_id}/ticker"
        async with self.session.get(url) as response:
            data = await response.json()
            
            # Extract useful info from the response
            if 'trades' in data and data['trades']:
                # Get price from most recent trade
                latest_trade = data['trades'][0]
                current_price = latest_trade.get('price', 'N/A')
                
                # Calculate volume from recent trades
                total_volume = sum(float(trade.get('size', 0)) for trade in data['trades'])
                
                return {
                    'price': current_price,
                    'volume_24h': f"{total_volume:.4f}",
                    'best_bid': data.get('best_bid', 'N/A'),
                    'best_ask': data.get('best_ask', 'N/A'),
                    'trades_count': len(data['trades'])
                }
            else:
                return {
                    'price': data.get('best_bid', 'N/A'),
                    'volume_24h': 'N/A',
                    'best_bid': data.get('best_bid', 'N/A'),
                    'best_ask': data.get('best_ask', 'N/A'),
                    'trades_count': 0
                }
    
    async def get_order_book(self, product_id, limit=10):
        """Get order book for a product."""
        url = f"{self.base_url}/api/v3/brokerage/market/product_book"
        params = {"product_id": product_id, "limit": limit}
        async with self.session.get(url, params=params) as response:
            return await response.json()
    
    async def get_candles(self, product_id, granularity="ONE_HOUR", limit=10):
        """Get historical candles."""
        url = f"{self.base_url}/api/v3/brokerage/market/products/{product_id}/candles"
        params = {
            "granularity": granularity,
            "limit": limit
        }
        async with self.session.get(url, params=params) as response:
            return await response.json()


async def market_data_demo():
    """Demonstrate real market data access."""
    
    print("📊 COINBASE REAL MARKET DATA")
    print("=" * 50)
    print("🌍 Accessing live production data")
    print("🔓 No authentication required")
    print("=" * 50)
    
    async with CoinbaseMarketData() as market:
        
        # Get all available products
        print("\n📋 AVAILABLE TRADING PAIRS")
        print("-" * 30)
        products = await market.get_products()
        
        # Filter for active products
        active_products = [p for p in products if p.get('status') == 'online']
        print(f"📊 Total active products: {len(active_products)}")
        
        # Show some popular pairs
        popular_pairs = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD']
        available_popular = [p for p in active_products if p.get('product_id') in popular_pairs]
        
        print("🔥 Popular pairs available:")
        for product in available_popular[:5]:
            print(f"  • {product['product_id']}: {product.get('display_name', 'N/A')}")
        
        # Get real-time price for BTC
        print(f"\n💰 REAL-TIME BITCOIN PRICE")
        print("-" * 30)
        btc_ticker = await market.get_ticker("BTC-USD")
        btc_price = btc_ticker.get('price', 'N/A')
        volume_recent = btc_ticker.get('volume_24h', 'N/A')
        best_bid = btc_ticker.get('best_bid', 'N/A')
        best_ask = btc_ticker.get('best_ask', 'N/A')
        trades_count = btc_ticker.get('trades_count', 0)
        
        print(f"💰 BTC/USD Price: ${btc_price}")
        print(f"📈 Best Bid: ${best_bid}")
        print(f"📉 Best Ask: ${best_ask}")
        print(f"📊 Recent Volume: {volume_recent} BTC ({trades_count} trades)")
        print(f"⏰ Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        # Get order book
        print(f"\n📈 LIVE ORDER BOOK (BTC/USD)")
        print("-" * 30)
        order_book = await market.get_order_book("BTC-USD", limit=5)
        
        bids = order_book.get('pricebook', {}).get('bids', [])
        asks = order_book.get('pricebook', {}).get('asks', [])
        
        print("📈 Top 5 Bids (buyers):")
        for i, bid in enumerate(bids[:5], 1):
            print(f"  {i}. ${bid['price']} (size: {bid['size']})")
        
        print("📉 Top 5 Asks (sellers):")
        for i, ask in enumerate(asks[:5], 1):
            print(f"  {i}. ${ask['price']} (size: {ask['size']})")
        
        # Get historical data
        print(f"\n📊 HISTORICAL CANDLES (BTC/USD)")
        print("-" * 30)
        candles = await market.get_candles("BTC-USD", granularity="ONE_HOUR", limit=5)
        
        if 'candles' in candles:
            print("🕐 Last 5 hourly candles (High/Low/Close):")
            for i, candle in enumerate(candles['candles'][:5], 1):
                high = candle['high']
                low = candle['low']
                close = candle['close']
                timestamp = datetime.fromtimestamp(int(candle['start']))
                print(f"  {i}. {timestamp.strftime('%H:%M')} - H:${high} L:${low} C:${close}")
        
        # Test other popular coins
        print(f"\n🔥 OTHER POPULAR CRYPTOCURRENCIES")
        print("-" * 40)
        other_coins = ['ETH-USD', 'SOL-USD', 'XRP-USD']
        
        for coin in other_coins:
            try:
                ticker = await market.get_ticker(coin)
                price = ticker.get('price', 'N/A')
                bid = ticker.get('best_bid', 'N/A')
                ask = ticker.get('best_ask', 'N/A')
                print(f"💰 {coin}: ${price} (Bid: ${bid}, Ask: ${ask})")
            except Exception as e:
                print(f"❌ {coin}: Error - {e}")
        
        print("\n✅ REAL MARKET DATA SUCCESS!")
        print("🎉 You now have access to live crypto market data!")


async def main():
    """Run the market data demonstration."""
    print("🚀 COINBASE MARKET DATA ACCESS")
    print("")
    print("This example demonstrates:")
    print("• Real-time cryptocurrency prices")
    print("• Live order books and trading data")
    print("• Historical price charts")
    print("• 700+ trading pairs available")
    print("• NO authentication required!")
    print("")
    
    await market_data_demo()
    
    print("\n" + "=" * 50)
    print("✅ MARKET DATA DEMO COMPLETE!")
    print("=" * 50)
    print("💡 Key Benefits:")
    print("• Real-time data for trading decisions")
    print("• No API keys needed for market data")
    print("• Perfect for price monitoring bots")
    print("• Ready for technical analysis!")
    print("")
    print("Next: Try trading_example.py for safe sandbox trading!")


if __name__ == "__main__":
    asyncio.run(main()) 