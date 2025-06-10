"""
Base Strategy Class

All trading strategies inherit from this base class.
Defines the interface that all strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio


@dataclass
class TradingDecision:
    """Represents a trading decision made by a strategy."""
    
    action: str  # 'buy', 'sell', 'hold'
    symbol: str  # 'BTC/USD', 'ETH/USD', etc.
    amount: float  # Amount to trade
    order_type: str  # 'market', 'limit'
    price: Optional[float] = None  # Price for limit orders
    reasoning: str = ""  # Why this decision was made
    confidence: float = 0.0  # Confidence level (0.0 to 1.0)
    strategy_used: str = ""  # Which strategy made this decision
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MarketData:
    """Current market data for strategy analysis."""
    
    prices: Dict[str, float]  # {'BTC/USD': 105000, 'ETH/USD': 2600}
    order_books: Dict[str, Dict] = None  # Order book data
    volumes: Dict[str, float] = None  # Trading volumes
    candles: Dict[str, list] = None  # Historical candles
    trades: Dict[str, list] = None  # Recent trades
    trades_history: Dict[str, Dict] = None  # Trade analysis (buy/sell ratios, avg sizes)
    momentum: Dict[str, Dict] = None  # Price momentum and technical indicators
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PortfolioData:
    """Current portfolio/account data."""
    
    balances: Dict[str, float]  # {'BTC': 0.5, 'USDC': 100}
    open_orders: list = None  # Current open orders
    recent_trades: list = None  # Recent trade history
    total_value_usd: float = 0.0  # Total portfolio value
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AssetDecision:
    """Decision for a specific asset."""
    asset: str  # 'BTC', 'ETH', 'USDT'
    action: str  # 'buy', 'sell', 'hold'
    target_symbol: str  # what to trade against (e.g., 'BTC/USDT')
    amount_usd: float  # USD amount to trade
    confidence: float  # 0.0 to 1.0
    reasoning: str


@dataclass
class MultiAssetTradingDecision:
    """Multi-asset trading decision."""
    decisions: List[AssetDecision]
    overall_strategy: str
    overall_confidence: float
    timestamp: str


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    
    All strategies must inherit from this class and implement:
    - analyze() method for making trading decisions
    - get_strategy_info() method for strategy description
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize the strategy.
        
        Args:
            name: Strategy name
            config: Strategy configuration parameters
        """
        self.name = name
        self.config = config or {}
        self.is_active = True
        self.last_decision = None
        self.decision_history = []
        
    @abstractmethod
    async def analyze(self, market_data: MarketData, portfolio_data: PortfolioData) -> TradingDecision:
        """
        Analyze market and portfolio data to make a trading decision.
        
        Args:
            market_data: Current market conditions
            portfolio_data: Current portfolio state
            
        Returns:
            TradingDecision: The trading decision
        """
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about this strategy.
        
        Returns:
            Dict containing strategy description, parameters, etc.
        """
        pass
    
    def record_decision(self, decision: TradingDecision):
        """Record a trading decision for history tracking."""
        self.last_decision = decision
        self.decision_history.append(decision)
        
        # Keep only last 100 decisions to avoid memory issues
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration parameter."""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set a configuration parameter."""
        self.config[key] = value
    
    def activate(self):
        """Activate this strategy."""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate this strategy."""
        self.is_active = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current strategy status."""
        return {
            'name': self.name,
            'active': self.is_active,
            'last_decision': self.last_decision.action if self.last_decision else None,
            'last_decision_time': self.last_decision.timestamp if self.last_decision else None,
            'total_decisions': len(self.decision_history),
            'config': self.config
        } 