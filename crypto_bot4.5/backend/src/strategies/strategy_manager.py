"""
Strategy Manager

Orchestrates strategy execution, manages multiple strategies,
and handles the trading loop with configurable intervals.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import yaml

from .base import BaseStrategy, TradingDecision, MarketData, PortfolioData
from .llm_strategy import LLMStrategy


class StrategyManager:
    """
    Manages strategy execution and trading loops.
    
    Features:
    - Multiple strategy support
    - Configurable execution intervals
    - Strategy performance tracking
    - Automatic error handling and recovery
    """
    
    def __init__(self, config_path: str = None, config_dict: Dict[str, Any] = None):
        """
        Initialize the strategy manager.
        
        Args:
            config_path: Path to strategy configuration file
            config_dict: Configuration dictionary (alternative to file)
        """
        self.strategies: Dict[str, BaseStrategy] = {}
        self.is_running = False
        self.execution_task = None
        
        # Load configuration
        if config_path:
            self.config = self._load_config_file(config_path)
        elif config_dict:
            self.config = config_dict
        else:
            self.config = self._get_default_config()
        
        # Configuration parameters
        self.interval_minutes = self.config.get('interval_minutes', 30)
        self.active_strategies = self.config.get('active_strategies', ['LLM_Strategy'])
        
        # Initialize strategies
        self._initialize_strategies()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'interval_minutes': 30,
            'active_strategies': ['LLM_Strategy'],
            'strategies': {
                'LLM_Strategy': {
                    'model': 'gpt-4o',
                    'temperature': 0.1,
                    'max_tokens': 500,
                    'max_trade_size_usd': 50,
                    'max_positions': 3,
                    'supported_symbols': ['BTC/USD', 'ETH/USD']
                }
            }
        }
    
    def _initialize_strategies(self):
        """Initialize configured strategies."""
        strategy_configs = self.config.get('strategies', {})
        
        for strategy_name in self.active_strategies:
            try:
                if strategy_name == 'LLM_Strategy':
                    config = strategy_configs.get(strategy_name, {})
                    strategy = LLMStrategy(config)
                    self.strategies[strategy_name] = strategy
                    self.logger.info(f"Initialized strategy: {strategy_name}")
                else:
                    self.logger.warning(f"Unknown strategy: {strategy_name}")
                    
            except Exception as e:
                self.logger.error(f"Failed to initialize strategy {strategy_name}: {e}")
    
    def add_strategy(self, strategy: BaseStrategy):
        """Add a strategy to the manager."""
        self.strategies[strategy.name] = strategy
        self.logger.info(f"Added strategy: {strategy.name}")
    
    def remove_strategy(self, strategy_name: str):
        """Remove a strategy from the manager."""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            self.logger.info(f"Removed strategy: {strategy_name}")
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """Get a strategy by name."""
        return self.strategies.get(strategy_name)
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """List all strategies and their status."""
        return [strategy.get_status() for strategy in self.strategies.values()]
    
    async def execute_strategies(self, market_data: MarketData, portfolio_data: PortfolioData) -> List[TradingDecision]:
        """
        Execute all active strategies and collect their decisions.
        
        Args:
            market_data: Current market data
            portfolio_data: Current portfolio data
            
        Returns:
            List of trading decisions from all strategies
        """
        decisions = []
        
        for strategy_name, strategy in self.strategies.items():
            if not strategy.is_active:
                continue
                
            try:
                self.logger.info(f"Executing strategy: {strategy_name}")
                decision = await strategy.analyze(market_data, portfolio_data)
                decisions.append(decision)
                
                self.logger.info(
                    f"Strategy {strategy_name} decision: "
                    f"{decision.action} {decision.amount} {decision.symbol} "
                    f"(confidence: {decision.confidence:.2f})"
                )
                
            except Exception as e:
                self.logger.error(f"Strategy {strategy_name} failed: {e}")
                # Continue with other strategies
                continue
        
        return decisions
    
    async def start_trading_loop(self, data_provider_func, execution_func):
        """
        Start the main trading loop.
        
        Args:
            data_provider_func: Async function that returns (market_data, portfolio_data)
            execution_func: Async function that executes trading decisions
        """
        if self.is_running:
            self.logger.warning("Trading loop is already running")
            return
        
        self.is_running = True
        self.logger.info(f"Starting trading loop (interval: {self.interval_minutes} minutes)")
        
        self.execution_task = asyncio.create_task(
            self._trading_loop(data_provider_func, execution_func)
        )
        
        try:
            await self.execution_task
        except asyncio.CancelledError:
            self.logger.info("Trading loop cancelled")
        except Exception as e:
            self.logger.error(f"Trading loop error: {e}")
        finally:
            self.is_running = False
    
    async def _trading_loop(self, data_provider_func, execution_func):
        """Main trading loop implementation."""
        
        while self.is_running:
            try:
                loop_start = datetime.now()
                self.logger.info(f"Trading loop iteration started at {loop_start}")
                
                # Get current market and portfolio data
                market_data, portfolio_data = await data_provider_func()
                
                # Execute all strategies
                decisions = await self.execute_strategies(market_data, portfolio_data)
                
                # Execute trading decisions
                if decisions:
                    await execution_func(decisions)
                else:
                    self.logger.info("No trading decisions made this iteration")
                
                # Calculate next execution time
                next_execution = loop_start + timedelta(minutes=self.interval_minutes)
                sleep_seconds = (next_execution - datetime.now()).total_seconds()
                
                if sleep_seconds > 0:
                    self.logger.info(f"Next execution in {sleep_seconds/60:.1f} minutes")
                    await asyncio.sleep(sleep_seconds)
                else:
                    self.logger.warning("Trading loop is running behind schedule")
                    
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                # Sleep before retrying
                await asyncio.sleep(60)  # 1 minute before retry
    
    def stop_trading_loop(self):
        """Stop the trading loop."""
        if self.execution_task:
            self.execution_task.cancel()
        self.is_running = False
        self.logger.info("Trading loop stop requested")
    
    def update_interval(self, minutes: int):
        """Update the execution interval."""
        self.interval_minutes = minutes
        self.logger.info(f"Updated execution interval to {minutes} minutes")
    
    def get_status(self) -> Dict[str, Any]:
        """Get manager status."""
        return {
            'is_running': self.is_running,
            'interval_minutes': self.interval_minutes,
            'active_strategies': [name for name, strategy in self.strategies.items() if strategy.is_active],
            'total_strategies': len(self.strategies),
            'strategies': self.list_strategies()
        } 