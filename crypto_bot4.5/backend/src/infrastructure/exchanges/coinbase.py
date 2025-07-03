#!/usr/bin/env python3
"""
Coinbase Advanced Trade API Implementation (Sandbox)
Uses manual HTTP requests to avoid SDK bugs with sandbox endpoints.
"""

import os
import time
import hmac
import hashlib
import base64
import requests
import json
from typing import Dict, Any, List, Optional
from .base import BaseExchange

class CoinbaseExchange(BaseExchange):
    """Coinbase Advanced Trade API implementation for sandbox environment."""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self._initialize_exchange()
    
    def _initialize_exchange(self) -> None:
        """Initialize the Coinbase exchange connection."""
        # Get API credentials
        api_key = self.config.get('api_key')
        api_secret = self.config.get('api_secret')
        
        if not api_key or not api_secret:
            print("🔓 No API credentials provided - public endpoints only")
            self._authenticated = False
            self._api_key = None
            self._api_secret = None
        else:
            print("🔐 API credentials loaded successfully")
            self._authenticated = True
            self._api_key = api_key
            self._api_secret = api_secret
        
        # Use hybrid approach: sandbox for trading, production for market data
        self._base_url = "https://api-sandbox.coinbase.com"
        self._market_data_url = "https://api.coinbase.com"  # Public endpoints work here
        print(f"🧪 Using HYBRID Advanced Trade environment:")
        print(f"   📊 Market data: {self._market_data_url} (public endpoints)")
        print(f"   💰 Trading/accounts: {self._base_url} (sandbox)")
    
    def _make_request(self, method: str, path: str, body: str = "") -> Dict[str, Any]:
        """Make authenticated request to Coinbase Advanced Trade API."""
        timestamp = str(int(time.time()))
        
        # Create signature (only for authenticated requests)
        if self._authenticated:
            message = f"{timestamp}{method.upper()}{path}{body}".encode()
            signature = hmac.new(
                base64.b64decode(self._api_secret), 
                message, 
                hashlib.sha256
            ).digest()
            signature_b64 = base64.b64encode(signature).decode()
            
            headers = {
                "CB-ACCESS-KEY": self._api_key,
                "CB-ACCESS-SIGN": signature_b64,
                "CB-ACCESS-TIMESTAMP": timestamp,
                "Content-Type": "application/json"
            }
        else:
            headers = {
                "Content-Type": "application/json"
            }
        
        url = self._base_url + path
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, data=body, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {str(e)}")

    def _make_public_request(self, path: str) -> Dict[str, Any]:
        """Make public (unauthenticated) request for market data."""
        url = self._market_data_url + path
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Public request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {str(e)}")

    def get_environment_info(self) -> Dict[str, Any]:
        """Get information about the current exchange environment."""
        return {
            'exchange': 'coinbase_sandbox',
            'environment': 'sandbox',
            'is_sandbox': True,
            'is_production': False,
            'api_type': 'coinbase_advanced_trade_manual',
            'endpoint': self._base_url,
            'warning': 'Safe testing environment',
            'authenticated': self._authenticated
        }

    async def get_supported_symbols(self) -> List[str]:
        """Get list of supported trading symbols."""
        try:
            print("📡 Fetching real symbols from production public API...")
            data = self._make_public_request("/api/v3/brokerage/market/products")
            symbols = []
            
            for product in data.get('products', []):
                if product.get('status') == 'online':
                    # Convert from Coinbase format (BTC-USD) to standard format (BTC/USD)
                    symbol = product.get('product_id', '').replace('-', '/')
                    if symbol:
                        symbols.append(symbol)
            
            print(f"✅ Retrieved {len(symbols)} real trading symbols")
            return symbols
        except Exception as e:
            print("⚠️  Failed to fetch real symbols, using fallback list")
            return [
                'BTC/USD', 'ETH/USD', 'ADA/USD', 'SOL/USD', 'DOGE/USD',
                'BTC/USDC', 'ETH/USDC', 'LTC/USD', 'DOT/USD', 'MATIC/USD'
            ]

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information for a symbol."""
        try:
            # Use production market data endpoint (no auth needed)
            product_id = symbol.replace('/', '-')
            data = self._make_public_request(f"/api/v3/brokerage/market/products/{product_id}/ticker")
            
            # Extract useful info from the response
            if 'trades' in data and data['trades']:
                # Get price from most recent trade
                latest_trade = data['trades'][0]
                current_price = float(latest_trade.get('price', 0))
                
                # Calculate volume from recent trades
                total_volume = sum(float(trade.get('size', 0)) for trade in data['trades'])
                
                return {
                    'symbol': symbol,
                    'last': current_price,
                    'bid': data.get('best_bid', current_price * 0.999),
                    'ask': data.get('best_ask', current_price * 1.001),
                    'baseVolume': total_volume,
                    'timestamp': None,
                    'datetime': None,
                }
            else:
                # Fallback to bid/ask if no trades
                bid = float(data.get('best_bid', 0)) if data.get('best_bid') else 0
                ask = float(data.get('best_ask', 0)) if data.get('best_ask') else 0
                price = (bid + ask) / 2 if bid and ask else bid or ask
                
                return {
                    'symbol': symbol,
                    'last': price,
                    'bid': bid,
                    'ask': ask,
                    'baseVolume': 0,
                    'timestamp': None,
                    'datetime': None,
                }
        except Exception as e:
            # Fallback to mock data if production API fails
            print(f"⚠️  Production market data failed for {symbol}, using mock data: {e}")
            import random
            base_price = 105000 if 'BTC' in symbol else 4000 if 'ETH' in symbol else 100
            mock_price = base_price + random.uniform(-1000, 1000)
            
            return {
                'symbol': symbol,
                'last': round(mock_price, 2),
                'bid': round(mock_price * 0.999, 2),
                'ask': round(mock_price * 1.001, 2),
                'baseVolume': round(random.uniform(1, 10), 4),
                'timestamp': None,
                'datetime': None,
            }

    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a symbol."""
        try:
            # Use production market data endpoint (no auth needed)
            product_id = symbol.replace('/', '-')
            params = f"?product_id={product_id}&limit={limit}"
            data = self._make_public_request(f"/api/v3/brokerage/market/product_book{params}")
            
            pricebook = data.get('pricebook', {})
            
            return {
                'symbol': symbol,
                'bids': [[float(bid.get('price', 0)), float(bid.get('size', 0))] 
                        for bid in pricebook.get('bids', [])],
                'asks': [[float(ask.get('price', 0)), float(ask.get('size', 0))] 
                        for ask in pricebook.get('asks', [])],
                'timestamp': None,
                'datetime': None,
            }
        except Exception as e:
            raise Exception(f"Failed to fetch orderbook for {symbol}: {str(e)}")

    async def get_candles(self, symbol: str, timeframe: str = '1d', limit: int = 100) -> List[List]:
        """Get historical candlestick data."""
        try:
            product_id = symbol.replace('/', '-')
            
            # Map timeframes to Coinbase granularity
            granularity_map = {
                '1m': 'ONE_MINUTE',
                '5m': 'FIVE_MINUTE', 
                '15m': 'FIFTEEN_MINUTE',
                '1h': 'ONE_HOUR',
                '6h': 'SIX_HOUR',
                '1d': 'ONE_DAY'
            }
            
            granularity = granularity_map.get(timeframe, 'ONE_DAY')
            
            # Calculate time range (much shorter for high-frequency trading)
            import datetime
            end_time = datetime.datetime.now()
            
            # Use shorter time ranges based on timeframe
            if timeframe in ['1m', '5m']:
                start_time = end_time - datetime.timedelta(hours=3)  # Last 3 hours for minute data
            elif timeframe in ['15m', '1h']:
                start_time = end_time - datetime.timedelta(hours=24)  # Last 24 hours for hourly data
            else:
                start_time = end_time - datetime.timedelta(days=7)   # Last 7 days for daily data
            
            params = (f"?start={int(start_time.timestamp())}"
                     f"&end={int(end_time.timestamp())}"
                     f"&granularity={granularity}")
            
            data = self._make_public_request(f"/api/v3/brokerage/market/products/{product_id}/candles{params}")
            
            # Convert to OHLCV format: [timestamp, open, high, low, close, volume]
            ohlcv_data = []
            for candle in data.get('candles', []):
                ohlcv_data.append([
                    int(candle.get('start', 0)),
                    float(candle.get('open', 0)),
                    float(candle.get('high', 0)),
                    float(candle.get('low', 0)),
                    float(candle.get('close', 0)),
                    float(candle.get('volume', 0))
                ])
            
            return ohlcv_data[:limit]  # Limit results
        except Exception as e:
            raise Exception(f"Failed to fetch candles for {symbol}: {str(e)}")

    async def get_short_term_data(self, symbol: str) -> Dict[str, Any]:
        """Get short-term trading data for high-frequency trading (30min intervals)."""
        try:
            # Get 30-minute candles for the last few hours
            candles_30m = await self.get_candles(symbol, '15m', limit=4)  # Last 1 hour of 15min candles
            candles_5m = await self.get_candles(symbol, '5m', limit=6)    # Last 30min of 5min candles
            
            if not candles_30m or not candles_5m:
                return {
                    'symbol': symbol,
                    'short_term_volume': 0,
                    'recent_change_percent': 0,
                    'momentum': 'neutral',
                    'trend': 'sideways'
                }
            
            # Calculate 30-minute volume (sum of last 6 * 5min candles)
            short_term_volume = sum(candle[5] for candle in candles_5m)  # Volume is index 5
            
            # Calculate recent price change (last 1 hour)
            if len(candles_30m) >= 2:
                recent_open = candles_30m[-1][1]   # Open of oldest candle
                recent_close = candles_30m[0][4]   # Close of newest candle
                recent_change_percent = ((recent_close - recent_open) / recent_open) * 100
            else:
                recent_change_percent = 0
            
            # Determine momentum based on recent price action
            if recent_change_percent > 0.1:
                momentum = 'bullish'
            elif recent_change_percent < -0.1:
                momentum = 'bearish'
            else:
                momentum = 'neutral'
            
            # Determine trend based on multiple timeframes
            if len(candles_5m) >= 3:
                recent_highs = [candle[2] for candle in candles_5m[:3]]  # Last 3 highs
                if recent_highs[0] > recent_highs[1] > recent_highs[2]:
                    trend = 'uptrend'
                elif recent_highs[0] < recent_highs[1] < recent_highs[2]:
                    trend = 'downtrend'
                else:
                    trend = 'sideways'
            else:
                trend = 'sideways'
            
            return {
                'symbol': symbol,
                'short_term_volume': short_term_volume,
                'recent_change_percent': recent_change_percent,
                'momentum': momentum,
                'trend': trend,
                'candles_5m': candles_5m[:3],  # Last 3 candles for reference
                'last_price': candles_5m[0][4] if candles_5m else 0  # Most recent close
            }
            
        except Exception as e:
            raise Exception(f"Failed to fetch short-term data for {symbol}: {str(e)}")

    async def get_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades for a symbol."""
        try:
            product_id = symbol.replace('/', '-')
            params = f"?limit={limit}"
            data = self._make_public_request(f"/api/v3/brokerage/market/products/{product_id}/ticker{params}")
            
            trade_list = []
            for trade in data.get('trades', []):
                # Fix timestamp parsing - handle ISO format datetime
                time_str = trade.get('time', '')
                try:
                    if time_str:
                        # Parse ISO datetime string to timestamp
                        from datetime import datetime
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        timestamp = int(dt.timestamp())
                    else:
                        timestamp = 0
                except (ValueError, AttributeError):
                    timestamp = 0
                
                trade_list.append({
                    'id': trade.get('trade_id'),
                    'timestamp': timestamp,
                    'datetime': time_str,
                    'symbol': symbol,
                    'side': trade.get('side', '').lower(),
                    'amount': float(trade.get('size', 0)),
                    'price': float(trade.get('price', 0)),
                    'cost': float(trade.get('size', 0)) * float(trade.get('price', 0)),
                })
            
            return trade_list
        except Exception as e:
            raise Exception(f"Failed to fetch trades for {symbol}: {str(e)}")

    async def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trades - alias for get_trades method."""
        return await self.get_trades(symbol, limit)

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        if not self._authenticated:
            raise Exception("Authentication required for balance information")
        
        try:
            data = self._make_request("GET", "/api/v3/brokerage/accounts")
            
            balance = {}
            for account in data.get('accounts', []):
                currency = account.get('currency')
                if currency:
                    available = account.get('available_balance', {})
                    hold = account.get('hold', {})
                    total_balance = account.get('balance', {})
                    
                    balance[currency] = {
                        'free': float(available.get('value', 0)),
                        'used': float(hold.get('value', 0)),
                        'total': float(total_balance.get('value', 0)),
                    }
            
            return balance
        except Exception as e:
            raise Exception(f"Failed to fetch balance: {str(e)}")

    async def get_account_info(self) -> Dict[str, Any]:
        """Get detailed account information."""
        if not self._authenticated:
            raise Exception("Authentication required for account information")
        
        try:
            data = self._make_request("GET", "/api/v3/brokerage/accounts")
            return {
                'accounts': data.get('accounts', []),
                'exchange_info': self.get_environment_info()
            }
        except Exception as e:
            raise Exception(f"Failed to fetch account info: {str(e)}")

    async def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        if not self._authenticated:
            raise Exception("Authentication required for order information")
        
        try:
            params = "?order_status=OPEN"
            if symbol:
                product_id = symbol.replace('/', '-')
                params += f"&product_id={product_id}"
            
            data = self._make_request("GET", f"/api/v3/brokerage/orders/historical/batch{params}")
            
            orders = []
            for order in data.get('orders', []):
                orders.append({
                    'id': order.get('order_id'),
                    'symbol': order.get('product_id', '').replace('-', '/'),
                    'side': order.get('side', '').lower(),
                    'amount': float(order.get('order_configuration', {}).get('base_size', 0)),
                    'price': float(order.get('order_configuration', {}).get('limit_price', 0)),
                    'status': order.get('status', '').lower(),
                    'type': order.get('order_type', '').lower(),
                    'timestamp': order.get('created_time'),
                })
            
            return orders
        except Exception as e:
            raise Exception(f"Failed to fetch open orders: {str(e)}")

    async def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history."""
        if not self._authenticated:
            raise Exception("Authentication required for order history")
        
        try:
            params = f"?limit={limit}"
            if symbol:
                product_id = symbol.replace('/', '-')
                params += f"&product_id={product_id}"
            
            data = self._make_request("GET", f"/api/v3/brokerage/orders/historical/batch{params}")
            
            orders = []
            for order in data.get('orders', []):
                orders.append({
                    'id': order.get('order_id'),
                    'symbol': order.get('product_id', '').replace('-', '/'),
                    'side': order.get('side', '').lower(),
                    'amount': float(order.get('order_configuration', {}).get('base_size', 0)),
                    'price': float(order.get('order_configuration', {}).get('limit_price', 0)),
                    'status': order.get('status', '').lower(),
                    'type': order.get('order_type', '').lower(),
                    'timestamp': order.get('created_time'),
                })
            
            return orders
        except Exception as e:
            raise Exception(f"Failed to fetch order history: {str(e)}")

    async def get_trading_fees(self) -> Dict[str, Any]:
        """Get trading fees."""
        if not self._authenticated:
            raise Exception("Authentication required for trading fees")
        
        try:
            data = self._make_request("GET", "/api/v3/brokerage/transaction_summary")
            return data
        except Exception as e:
            raise Exception(f"Failed to fetch trading fees: {str(e)}")

    # Trading methods (require authentication)
    async def place_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        """Place a market order."""
        if not self._authenticated:
            raise Exception("Authentication required for placing orders")
        
        try:
            product_id = symbol.replace('/', '-')
            
            if side.lower() == 'buy':
                order_config = {
                    "market_market_ioc": {
                        "quote_size": str(amount)  # USD amount for buying
                    }
                }
            else:
                order_config = {
                    "market_market_ioc": {
                        "base_size": str(amount)  # Crypto amount for selling
                    }
                }
            
            order_data = {
                "client_order_id": f"{int(time.time() * 1000)}",  # Unique ID
                "product_id": product_id,
                "side": side.upper(),
                "order_configuration": order_config
            }
            
            data = self._make_request("POST", "/api/v3/brokerage/orders", json.dumps(order_data))
            return data
        
        except Exception as e:
            raise Exception(f"Failed to place market order: {str(e)}")

    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """Place a limit order."""
        if not self._authenticated:
            raise Exception("Authentication required for placing orders")
        
        try:
            product_id = symbol.replace('/', '-')
            
            order_config = {
                "limit_limit_gtc": {
                    "base_size": str(amount),
                    "limit_price": str(price)
                }
            }
            
            order_data = {
                "client_order_id": f"{int(time.time() * 1000)}",
                "product_id": product_id,
                "side": side.upper(),
                "order_configuration": order_config
            }
            
            data = self._make_request("POST", "/api/v3/brokerage/orders", json.dumps(order_data))
            return data
        
        except Exception as e:
            raise Exception(f"Failed to place limit order: {str(e)}")

    async def cancel_order(self, order_id: str, symbol: str = None) -> Dict[str, Any]:
        """Cancel an order."""
        if not self._authenticated:
            raise Exception("Authentication required for canceling orders")
        
        try:
            cancel_data = {
                "order_ids": [order_id]
            }
            
            data = self._make_request("POST", "/api/v3/brokerage/orders/batch_cancel", json.dumps(cancel_data))
            return data
        
        except Exception as e:
            raise Exception(f"Failed to cancel order: {str(e)}")

    async def get_order_status(self, order_id: str, symbol: str = None) -> Dict[str, Any]:
        """Get order status."""
        if not self._authenticated:
            raise Exception("Authentication required for order status")
        
        try:
            data = self._make_request("GET", f"/api/v3/brokerage/orders/historical/{order_id}")
            
            order = data.get('order', {})
            return {
                'id': order.get('order_id'),
                'symbol': order.get('product_id', '').replace('-', '/'),
                'side': order.get('side', '').lower(),
                'amount': float(order.get('order_configuration', {}).get('base_size', 0)),
                'price': float(order.get('order_configuration', {}).get('limit_price', 0)),
                'status': order.get('status', '').lower(),
                'type': order.get('order_type', '').lower(),
                'timestamp': order.get('created_time'),
            }
        
        except Exception as e:
            raise Exception(f"Failed to get order status: {str(e)}")

    def get_supported_trading_features(self) -> Dict[str, Any]:
        """Get supported trading features."""
        return {
            'spot_trading': True,
            'margin_trading': False,
            'futures_trading': False,
            'options_trading': False,
            'stop_orders': True,
            'limit_orders': True,
            'market_orders': True,
            'order_types': ['market', 'limit', 'stop'],
            'time_in_force': ['GTC', 'IOC', 'FOK'],
            'sandbox_available': True,
            'websocket_available': True
        }

    async def close(self) -> None:
        """Close exchange connection."""
        print("🔌 Coinbase sandbox connection closed")


def create_coinbase_exchange(config_path: str = None) -> CoinbaseExchange:
    """
    Factory function to create a Coinbase exchange instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        CoinbaseExchange instance
    """
    if config_path is None:
        # Default to sandbox config
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'configs', 'exchanges', 'coinbase_sandbox.yaml'
        )
    
    return CoinbaseExchange(config_path)
