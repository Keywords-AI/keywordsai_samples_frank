#!/usr/bin/env python3
"""
Simple Trading Example
=====================

Just 4 steps:
1. Get market data
2. Get balance  
3. Send to LLM
4. Get response

No fancy formatting - just accurate functionality.
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from infrastructure.exchanges.factory import ExchangeFactory, ExchangeType, Environment
from strategies.llm_strategy import LLMStrategy
from strategies.base import MarketData, PortfolioData


async def main():
    """Simple 4-step trading pipeline"""
    
    # Initialize exchange
    factory = ExchangeFactory()
    exchange = factory.create_exchange(ExchangeType.COINBASE_SANDBOX, Environment.SANDBOX)
    
    try:
        # Step 1: Get ALL market data needed for trading decisions
        print("1. Getting complete market data...")
        
        symbols = ['BTC/USD', 'ETH/USD']
        prices = {}
        volumes = {}
        order_books = {}
        trades_history = {}
        momentum = {}
        
        for symbol in symbols:
            print(f"   Getting {symbol} data...")
            
            # Get price and 24h volume
            ticker = await exchange.get_ticker(symbol)
            price = float(ticker['last'])
            volume_24h = float(ticker.get('baseVolume', 0))
            volume_30min = volume_24h / 48  # Estimate 30-min volume
            
            # Get short-term price momentum from candles
            try:
                # Get 15min candles for short-term momentum
                candles_15m = await exchange.get_candles(symbol, timeframe='15m', limit=3)  # Last 3 candles = 45min
                candles_30m = await exchange.get_candles(symbol, timeframe='30m', limit=2)  # Last 2 candles = 60min
                
                if candles_15m and len(candles_15m) >= 2:
                    # Calculate 15min change (current vs 15min ago)
                    price_15m_ago = float(candles_15m[-2][4])  # Close price of previous 15min candle
                    price_change_15m = price - price_15m_ago
                    price_change_pct_15m = (price_change_15m / price_15m_ago) * 100 if price_15m_ago > 0 else 0
                else:
                    price_change_pct_15m = 0
                
                if candles_30m and len(candles_30m) >= 2:
                    # Calculate 30min change (current vs 30min ago)  
                    price_30m_ago = float(candles_30m[-2][4])  # Close price of previous 30min candle
                    price_change_30m = price - price_30m_ago
                    price_change_pct_30m = (price_change_30m / price_30m_ago) * 100 if price_30m_ago > 0 else 0
                else:
                    price_change_pct_30m = 0
                    
            except Exception as e:
                print(f"      ⚠️ Could not get candle data for momentum: {e}")
                price_change_pct_15m = 0
                price_change_pct_30m = 0
            
            # Get 24h price momentum from ticker data
            price_24h_ago = float(ticker.get('open', price))
            price_change_24h = price - price_24h_ago
            price_change_pct_24h = (price_change_24h / price_24h_ago) * 100 if price_24h_ago > 0 else 0
            
            # Get order book for spreads and market depth
            order_book = await exchange.get_orderbook(symbol, limit=10)
            
            # Get recent trades for volume analysis
            try:
                recent_trades = await exchange.get_recent_trades(symbol, limit=50)
                
                # Analyze recent trades
                if recent_trades:
                    recent_volumes = [float(trade['amount']) for trade in recent_trades[-10:]]  # Last 10 trades
                    avg_trade_size = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
                    
                    # Calculate buy/sell pressure from recent trades
                    buy_volume = sum([float(trade['amount']) for trade in recent_trades[-20:] if trade.get('side') == 'buy'])
                    sell_volume = sum([float(trade['amount']) for trade in recent_trades[-20:] if trade.get('side') == 'sell'])
                    buy_sell_ratio = buy_volume / sell_volume if sell_volume > 0 else 1
                    
                    trades_history[symbol] = {
                        'avg_trade_size': avg_trade_size,
                        'buy_volume': buy_volume,
                        'sell_volume': sell_volume,
                        'buy_sell_ratio': buy_sell_ratio,
                        'total_recent_trades': len(recent_trades)
                    }
                else:
                    trades_history[symbol] = {'avg_trade_size': 0, 'buy_sell_ratio': 1}
            except Exception as e:
                print(f"      ⚠️ Could not get trades history: {e}")
                trades_history[symbol] = {'avg_trade_size': 0, 'buy_sell_ratio': 1}
            
            # Calculate spread
            if order_book['bids'] and order_book['asks']:
                bid_price = order_book['bids'][0][0]
                ask_price = order_book['asks'][0][0]
                spread = ask_price - bid_price
                spread_pct = (spread / price) * 100
                
                # Calculate market depth
                bid_volume = sum([bid[1] for bid in order_book['bids'][:5]])  # Top 5 bids
                ask_volume = sum([ask[1] for ask in order_book['asks'][:5]])  # Top 5 asks
                
                # Calculate technical indicators
                volatility = abs(price_change_pct_24h)  # Simple volatility measure
                
                # Market sentiment from order book imbalance
                market_sentiment = "BULLISH" if bid_volume > ask_volume * 1.2 else "BEARISH" if ask_volume > bid_volume * 1.2 else "NEUTRAL"
                
                # Trading activity level
                trade_data = trades_history.get(symbol, {})
                activity_level = "HIGH" if trade_data.get('total_recent_trades', 0) > 30 else "MEDIUM" if trade_data.get('total_recent_trades', 0) > 15 else "LOW"
                
                print(f"      Price: ${price:,.2f} ({price_change_pct_15m:+.2f}% 15m, {price_change_pct_30m:+.2f}% 30m, {price_change_pct_24h:+.2f}% 24h)")
                print(f"      Volume: {volume_30min:.4f} (30min est)")
                print(f"      Spread: ${spread:.2f} ({spread_pct:.3f}%)")
                print(f"      Market Depth: Bids {bid_volume:.2f}, Asks {ask_volume:.2f}")
                print(f"      Sentiment: {market_sentiment} | Activity: {activity_level}")
                print(f"      Buy/Sell Ratio: {trade_data.get('buy_sell_ratio', 1):.2f}")
                print(f"      Volatility: {volatility:.2f}%")
                
                # Store momentum data
                momentum[symbol] = {
                    'price_change_15m': price_change_pct_15m,
                    'price_change_30m': price_change_pct_30m,
                    'price_change_24h': price_change_24h,
                    'price_change_pct_24h': price_change_pct_24h,
                    'volatility': volatility,
                    'market_sentiment': market_sentiment,
                    'activity_level': activity_level
                }
                
                # Store all data
                prices[symbol] = price
                volumes[symbol] = volume_30min
                order_books[symbol] = {
                    'bids': order_book['bids'],
                    'asks': order_book['asks'],
                    'spread': spread,
                    'spread_pct': spread_pct,
                    'bid_volume': bid_volume,
                    'ask_volume': ask_volume,
                    'market_depth_ratio': bid_volume / ask_volume if ask_volume > 0 else 1
                }
            else:
                prices[symbol] = price
                volumes[symbol] = volume_30min
                order_books[symbol] = {'spread': 0, 'spread_pct': 0}
                momentum[symbol] = {'price_change_pct_24h': 0, 'volatility': 0}
        
        market_data = MarketData(
            prices=prices, 
            volumes=volumes, 
            order_books=order_books,
            trades_history=trades_history,
            momentum=momentum
        )
        
        # Step 2: Get balance
        print("2. Getting balance...")
        
        balances_raw = await exchange.get_balance()
        portfolio_balances = {}
        
        for currency, balance_info in balances_raw.items():
            if isinstance(balance_info, dict):
                available = float(balance_info.get('free', 0))
            else:
                available = float(balance_info)
            
            if available > 0:
                portfolio_balances[currency] = available
                print(f"   {currency}: {available:.4f}")
        
        portfolio_data = PortfolioData(balances=portfolio_balances, total_value_usd=0)
        
        # Step 3: Send to LLM
        print("3. Sending to LLM...")
        
        strategy = LLMStrategy()
        decisions = await strategy.analyze_multi_asset(market_data, portfolio_data)
        
        # Step 4: Get response
        print("4. LLM Response:")
        print(f"   Confidence: {decisions.overall_confidence:.2f}")
        
        for decision in decisions.decisions:
            print(f"   {decision.asset}: {decision.action} ${decision.amount_usd:.0f}")
            print(f"      Strategy: {decision.reasoning}")
    
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main()) 