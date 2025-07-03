#!/usr/bin/env python3
"""
30-Minute Autonomous Trading Bot (Simplified Version)
====================================================

Simplified trading bot that runs every 30 minutes with:
- Comprehensive market data collection
- AI-powered decision making  
- Automated trade execution
- Basic KeywordsAI tracing (compatible with v0.0.32)
"""

import asyncio
import signal
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from keywordsai_tracing.main import get_client

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# KeywordsAI tracing imports (simple version like working sample)
from keywordsai_tracing.decorators import workflow, task
from keywordsai_tracing.main import KeywordsAITelemetry
from dotenv import load_dotenv

# Bot imports
from infrastructure.exchanges.factory import ExchangeFactory, ExchangeType, Environment
from strategies.llm_strategy import LLMStrategy
from strategies.base import MarketData, PortfolioData, TradingDecision

# Load environment variables (like your working sample)
load_dotenv()

# Initialize KeywordsAI tracing (simple like your working sample)
k_tl = KeywordsAITelemetry(block_instruments={"requests"})


class TradingBot:
    """
    30-Minute Autonomous Trading Bot (Simplified)
    
    Features:
    - Runs every 30 minutes automatically
    - Comprehensive market data analysis
    - AI-powered trading decisions
    - Real trade execution
    - Basic KeywordsAI tracing
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the trading bot."""
        self.config = config or self._get_default_config()
        
        # Bot state
        self.is_running = False
        self.cycle_count = 0
        self.start_time = None
        
        # Trading components
        self.exchange = None
        self.strategy = None
        
        # Configuration
        self.interval_minutes = self.config.get('interval_minutes', 30)
        self.min_confidence = self.config.get('min_confidence_threshold', 0.6)
        self.max_trade_size = self.config.get('max_trade_size_usd', 1000)
        self.supported_symbols = self.config.get('supported_symbols', ['BTC/USD', 'ETH/USD'])
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize components
        self._initialize_components()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'interval_minutes': 30,
            'min_confidence_threshold': 0.6,
            'max_trade_size_usd': 1000,
            'max_daily_trades': 20,
            'supported_symbols': ['BTC/USD', 'ETH/USD'],
            'environment': 'sandbox',
            'customer_identifier': 'crypto_trading_bot_v1'
        }
    
    def _initialize_components(self):
        """Initialize exchange and strategy components."""
        try:
            # Initialize exchange
            factory = ExchangeFactory()
            self.exchange = factory.create_exchange(
                ExchangeType.COINBASE_SANDBOX, 
                Environment.SANDBOX
            )
            
            # Initialize AI strategy
            self.strategy = LLMStrategy()
            
            self.logger.info("✅ Bot components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize bot components: {e}")
            raise
    
    async def run_30min_loop(self):
        """
        Main 30-minute trading loop.
        Each trading cycle is a separate workflow for proper tracing.
        """
        self.is_running = True
        self.start_time = datetime.now()
        
        self.logger.info(f"🚀 Starting 30-minute trading bot loop")
        self.logger.info(f"📊 KeywordsAI tracing: {'enabled' if k_tl else 'disabled'}")
        self.logger.info(f"⚙️  Configuration: {self.interval_minutes}min interval, "
                        f"min confidence {self.min_confidence}, max trade ${self.max_trade_size}")
        
        while self.is_running:
            try:
                cycle_start = datetime.now()
                self.cycle_count += 1
                
                self.logger.info(f"🔄 Trading cycle #{self.cycle_count} started at {cycle_start}")
                
                # Execute the complete trading cycle as a workflow
                cycle_result = await self.execute_trading_cycle()
                
                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                self.logger.info(f"✅ Cycle #{self.cycle_count} completed in {cycle_duration:.1f}s")
                
                # Wait for next cycle
                if self.is_running:  # Check if still running before waiting
                    self.logger.info(f"⏰ Waiting {self.interval_minutes} minutes for next cycle...")
                    await asyncio.sleep(self.interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"❌ Trading cycle #{self.cycle_count} error: {e}")
                # Wait 1 minute before retry on error
                if self.is_running:
                    await asyncio.sleep(60)
    
    @workflow(name="trading_cycle")
    async def execute_trading_cycle(self) -> Dict[str, Any]:
        """
        Execute the complete 4-step trading pipeline as a KeywordsAI workflow:
        1. Get comprehensive market data (task)
        2. Get current portfolio data (task)
        3. AI decision making (task)
        4. Execute trades (task)
        """
        cycle_data = {
            'cycle_number': self.cycle_count,
            'timestamp': datetime.now().isoformat(),
            'market_data': None,
            'portfolio_data': None,
            'decisions': None,
            'executed_trades': None,
            'status': 'started'
        }
        
        try:
            # Step 1: Get comprehensive market data (task)
            self.logger.info("📊 Step 1: Getting comprehensive market data...")
            cycle_data['market_data'] = await self.get_comprehensive_market_data()
            
            # Step 2: Get current portfolio data (task)
            self.logger.info("💰 Step 2: Getting portfolio data...")
            cycle_data['portfolio_data'] = await self.get_portfolio_data()
            
            # Step 3: AI decision making (task)
            self.logger.info("🤖 Step 3: AI decision making...")
            cycle_data['decisions'] = await self.make_ai_decisions(
                cycle_data['market_data'], 
                cycle_data['portfolio_data']
            )
            
            # Step 4: Execute trades (task - mock for now)
            self.logger.info("⚡ Step 4: Mock executing trades...")
            cycle_data['executed_trades'] = await self.mock_execute_decisions(cycle_data['decisions'])
            
            cycle_data['status'] = 'completed'
            
            # Log cycle summary
            self._log_cycle_summary(cycle_data)
            
            return cycle_data
            
        except Exception as e:
            cycle_data['status'] = 'failed'
            cycle_data['error'] = str(e)
            self.logger.error(f"❌ Trading cycle failed: {e}")
            raise
    
    @task(name="get_market_data")
    async def get_comprehensive_market_data(self) -> MarketData:
        """
        Step 1: Get comprehensive market data with KeywordsAI tracing.
        Collects prices, volumes, order books, trades, and momentum data.
        """
        self.logger.info(f"   Collecting data for symbols: {self.supported_symbols}")
        kai_client = get_client()
        kai_client.update_current_span(
            keywordsai_params={
                "metadata":{
                    "test":"test_market_data"
                }
            }
        )
        
        
        symbols = self.supported_symbols
        prices = {}
        volumes = {}
        order_books = {}
        trades_history = {}
        momentum = {}
        
        for symbol in symbols:
            try:
                self.logger.info(f"   Getting {symbol} data...")
                
                # Get price and 24h volume
                ticker = await self.exchange.get_ticker(symbol)
                price = float(ticker['last'])
                volume_24h = float(ticker.get('baseVolume', 0))
                volume_30min = volume_24h / 48  # Estimate 30-min volume
                
                # Get 24h momentum from ticker
                price_24h_ago = float(ticker.get('open', price))
                price_change_pct_24h = ((price - price_24h_ago) / price_24h_ago) * 100 if price_24h_ago > 0 else 0
                
                # Get order book
                order_book = await self.exchange.get_orderbook(symbol, limit=10)
                
                # Calculate spread and market depth
                spread = 0
                spread_pct = 0
                bid_volume = 0
                ask_volume = 0
                market_sentiment = "NEUTRAL"
                
                if order_book['bids'] and order_book['asks']:
                    bid_price = order_book['bids'][0][0]
                    ask_price = order_book['asks'][0][0]
                    spread = ask_price - bid_price
                    spread_pct = (spread / price) * 100
                    
                    # Market depth
                    bid_volume = sum([bid[1] for bid in order_book['bids'][:5]])
                    ask_volume = sum([ask[1] for ask in order_book['asks'][:5]])
                    
                    # Market sentiment from order book imbalance
                    if bid_volume > ask_volume * 1.2:
                        market_sentiment = "BULLISH"
                    elif ask_volume > bid_volume * 1.2:
                        market_sentiment = "BEARISH"
                
                # Store basic trade history (simplified)
                trades_history[symbol] = {'buy_sell_ratio': 1.0, 'avg_trade_size': 0}
                
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
                
                momentum[symbol] = {
                    'price_change_24h': price_change_pct_24h,
                    'price_change_pct_24h': price_change_pct_24h,
                    'volatility': abs(price_change_pct_24h),
                    'market_sentiment': market_sentiment,
                    'activity_level': "MEDIUM"
                }
                
                # Log market data summary
                self.logger.info(f"      Price: ${price:,.2f} ({price_change_pct_24h:+.2f}% 24h)")
                self.logger.info(f"      Sentiment: {market_sentiment} | Spread: {spread_pct:.3f}%")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to get data for {symbol}: {e}")
                # Add fallback data
                prices[symbol] = 0
                volumes[symbol] = 0
                order_books[symbol] = {'spread': 0, 'spread_pct': 0}
                momentum[symbol] = {'price_change_pct_24h': 0, 'volatility': 0, 'market_sentiment': 'NEUTRAL'}
                trades_history[symbol] = {'buy_sell_ratio': 1}
        
        market_data = MarketData(
            prices=prices,
            volumes=volumes,
            order_books=order_books,
            trades_history=trades_history,
            momentum=momentum
        )
        
        return market_data
    
    @task(name="get_portfolio_data")
    async def get_portfolio_data(self) -> PortfolioData:
        """
        Step 2: Get current portfolio data with KeywordsAI tracing.
        """
        try:
            # Get balance from exchange
            balances_raw = await self.exchange.get_balance()
            portfolio_balances = {}
            total_value_usd = 0
            
            # Process balance data
            for currency, balance_info in balances_raw.items():
                if isinstance(balance_info, dict):
                    available = float(balance_info.get('free', 0))
                else:
                    available = float(balance_info)
                
                if available > 0:
                    portfolio_balances[currency] = available
                    self.logger.info(f"   {currency}: {available:.6f}")
            
            # Calculate total USD value (simplified)
            for currency, amount in portfolio_balances.items():
                if currency in ['USD', 'USDC', 'USDT']:
                    total_value_usd += amount
                # Add BTC/ETH value calculation if needed
            
            portfolio_data = PortfolioData(
                balances=portfolio_balances,
                total_value_usd=total_value_usd
            )
            
            return portfolio_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get portfolio data: {e}")
            # Return empty portfolio on error
            return PortfolioData(balances={}, total_value_usd=0)
    
    @task(name="ai_decision_making")
    async def make_ai_decisions(self, market_data: MarketData, portfolio_data: PortfolioData):
        """
        Step 3: AI decision making with KeywordsAI tracing.
        Uses LLM strategy to analyze market and make trading decisions.
        """
        try:
            # Execute AI decision making
            decisions = await self.strategy.analyze_multi_asset(market_data, portfolio_data)
            
            self.logger.info(f"   AI Confidence: {decisions.overall_confidence:.2f}")
            self.logger.info(f"   Decisions: {len(decisions.decisions)}")
            
            for decision in decisions.decisions:
                self.logger.info(f"   {decision.asset}: {decision.action} ${decision.amount_usd:.0f} "
                               f"(confidence: {decision.confidence:.2f}) - {decision.reasoning}")
            
            return decisions
            
        except Exception as e:
            self.logger.error(f"❌ AI decision making failed: {e}")
            # Return empty decisions on error
            from strategies.base import MultiAssetTradingDecision, AssetDecision
            return MultiAssetTradingDecision(
                decisions=[],
                overall_strategy="error_fallback",
                overall_confidence=0.0,
                timestamp=datetime.now().isoformat()
            )
    
    @task(name="mock_execute_trades")
    async def mock_execute_decisions(self, decisions):
        """
        Step 4: Mock trade execution (doesn't actually place orders - for testing).
        """
        executed_trades = []
        
        if decisions.overall_confidence <= self.min_confidence:
            self.logger.info(f"   ⏸️  Confidence {decisions.overall_confidence:.2f} below threshold {self.min_confidence}. No trades would be executed.")
            return executed_trades
        
        # Mock execute trades
        for decision in decisions.decisions:
            if decision.action in ['buy', 'sell'] and decision.amount_usd > 0:
                self.logger.info(f"   🔄 MOCK: Would {decision.action} ${decision.amount_usd} {decision.asset}")
                
                trade_result = {
                    'decision': decision,
                    'status': 'mock_success',
                    'usd_amount': decision.amount_usd,
                    'executed_at': datetime.now().isoformat(),
                    'note': 'Mock execution - no real trade placed'
                }
                
                executed_trades.append(trade_result)
                self.logger.info(f"   ✅ MOCK: Would execute {decision.action} {decision.asset} for ${decision.amount_usd}")
        
        return executed_trades
    
    def _log_cycle_summary(self, cycle_data: Dict[str, Any]):
        """Log summary of completed trading cycle."""
        self.logger.info("📊 Cycle Summary:")
        self.logger.info(f"   Market data: {len(cycle_data['market_data'].prices)} symbols")
        self.logger.info(f"   Portfolio value: ${cycle_data['portfolio_data'].total_value_usd:.2f}")
        self.logger.info(f"   AI confidence: {cycle_data['decisions'].overall_confidence:.2f}")
        self.logger.info(f"   Mock trades: {len(cycle_data['executed_trades'])}")
        self.logger.info(f"   Status: {cycle_data['status']}")
    
    def stop(self):
        """Stop the trading bot gracefully."""
        self.logger.info("🛑 Stopping trading bot...")
        self.is_running = False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.exchange:
            await self.exchange.close()
        self.logger.info("✅ Bot cleanup completed")


async def main():
    """Main function to run the trading bot."""
    # Setup graceful shutdown
    bot = None
    
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}. Shutting down bot...")
        if bot:
            bot.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and start bot
        bot = TradingBot()
        
        print("🚀 Starting 30-minute autonomous trading bot (simplified)...")
        print("📊 KeywordsAI basic tracing enabled")
        print("🛡️  Running in SANDBOX mode with MOCK trading")
        print("⏸️  Press Ctrl+C to stop gracefully")
        
        await bot.run_30min_loop()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
    finally:
        if bot:
            await bot.cleanup()
        print("✅ Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main()) 