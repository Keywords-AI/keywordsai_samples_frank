# abstract base exchange

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import ccxt
import asyncio
from datetime import datetime
import yaml
import os
from dotenv import load_dotenv


class BaseExchange(ABC):
    """
    Abstract base class for cryptocurrency exchange wrappers.
    Provides a standardized interface over CCXT exchange implementations.
    """

    def __init__(self, config_path: str):
        """
        Initialize the exchange with configuration.
        
        Args:
            config_path: Path to the exchange configuration file
        """
        # Load .env file if it exists
        self._load_dotenv()
        self.config = self._load_config(config_path)
        self.exchange = None
        self._initialize_exchange()
    
    def _load_dotenv(self) -> None:
        """Load environment variables from .env file."""
        # Look for .env file in backend directory and parent directories
        env_paths = [
            os.path.join(os.getcwd(), '.env'),
            os.path.join(os.path.dirname(os.getcwd()), '.env'),
            os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'),
        ]
        
        for env_path in env_paths:
            if os.path.exists(env_path):
                try:
                    load_dotenv(env_path)
                    print(f"🔑 Loaded environment variables from: {env_path}")
                    break
                except UnicodeDecodeError as e:
                    print(f"⚠️  Warning: Could not load {env_path} due to encoding issue: {e}")
                    print("   Make sure your .env file is saved as UTF-8 text format.")
                except Exception as e:
                    print(f"⚠️  Warning: Could not load {env_path}: {e}")
        else:
            print("ℹ️  No .env file found. Using system environment variables.")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable substitution."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Substitute environment variables
        return self._substitute_env_vars(config)
    
    def _substitute_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitute environment variables in configuration values.
        Supports ${VAR_NAME} syntax.
        """
        if isinstance(config, dict):
            result = {}
            for key, value in config.items():
                result[key] = self._substitute_env_vars(value)
            return result
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Handle ${VAR_NAME} substitution
            if config.startswith('${') and config.endswith('}'):
                env_var = config[2:-1]  # Remove ${ and }
                env_value = os.getenv(env_var)
                if env_value is None:
                    print(f"⚠️  Environment variable {env_var} not found, using original value")
                    return config
                return env_value
            return config
        else:
            return config

    @abstractmethod
    def _initialize_exchange(self) -> None:
        """Initialize the specific exchange instance."""
        pass

    async def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance for all currencies.
        
        Returns:
            Dictionary containing balance information
        """
        try:
            balance = await self.exchange.fetch_balance()
            return balance
        except Exception as e:
            raise Exception(f"Failed to fetch balance: {str(e)}")

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker information for a trading pair.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USD')
            
        Returns:
            Dictionary containing ticker information
        """
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            raise Exception(f"Failed to fetch ticker for {symbol}: {str(e)}")

    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get order book for a trading pair.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of orders to retrieve
            
        Returns:
            Dictionary containing order book data
        """
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit)
            return orderbook
        except Exception as e:
            raise Exception(f"Failed to fetch orderbook for {symbol}: {str(e)}")

    async def place_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Amount to trade
            
        Returns:
            Dictionary containing order information
        """
        try:
            order = await self.exchange.create_market_order(symbol, side, amount)
            return order
        except Exception as e:
            raise Exception(f"Failed to place market order: {str(e)}")

    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Amount to trade
            price: Limit price
            
        Returns:
            Dictionary containing order information
        """
        try:
            order = await self.exchange.create_limit_order(symbol, side, amount, price)
            return order
        except Exception as e:
            raise Exception(f"Failed to place limit order: {str(e)}")

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: ID of the order to cancel
            symbol: Trading pair symbol
            
        Returns:
            Dictionary containing cancellation result
        """
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            return result
        except Exception as e:
            raise Exception(f"Failed to cancel order {order_id}: {str(e)}")

    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Get the status of an order.
        
        Args:
            order_id: ID of the order
            symbol: Trading pair symbol
            
        Returns:
            Dictionary containing order status information
        """
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            raise Exception(f"Failed to fetch order {order_id}: {str(e)}")

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders.
        
        Args:
            symbol: Optional trading pair symbol to filter by
            
        Returns:
            List of dictionaries containing open orders
        """
        try:
            orders = await self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            raise Exception(f"Failed to fetch open orders: {str(e)}")

    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get order history.
        
        Args:
            symbol: Optional trading pair symbol to filter by
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of dictionaries containing order history
        """
        try:
            orders = await self.exchange.fetch_orders(symbol, limit=limit)
            return orders
        except Exception as e:
            raise Exception(f"Failed to fetch order history: {str(e)}")

    async def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get trading fees for the exchange.
        
        Args:
            symbol: Optional trading pair symbol
            
        Returns:
            Dictionary containing fee information
        """
        try:
            fees = await self.exchange.fetch_trading_fees()
            return fees
        except Exception as e:
            raise Exception(f"Failed to fetch trading fees: {str(e)}")

    async def close(self) -> None:
        """Close the exchange connection."""
        if self.exchange:
            await self.exchange.close()

    def __enter__(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
