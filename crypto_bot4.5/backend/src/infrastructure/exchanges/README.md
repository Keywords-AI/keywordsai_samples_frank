# Exchange Infrastructure

This module provides standardized interfaces for cryptocurrency exchange interactions using CCXT as the underlying library.

## Overview

The exchange infrastructure consists of:

- **BaseExchange**: Abstract base class defining the standard interface
- **CoinbaseExchange**: Coinbase-specific implementation
- Configuration files for different environments (sandbox/production)

## Features

### Supported Operations

- ✅ **Market Data**: Tickers, order books, historical candles, trades
- ✅ **Account Management**: Balance, account info, trading fees
- ✅ **Order Management**: Place/cancel orders, order status, order history
- ✅ **Trading**: Market orders, limit orders, stop orders
- ✅ **Transfers**: Deposits, withdrawals, account transfers (where supported)

### Exchange Support

- ✅ **Coinbase Pro** (legacy API)
- ✅ **Coinbase Advanced Trade** (newer API)
- 🔄 **Binance** (placeholder - implement similar to Coinbase)

## Quick Start

### 1. Configuration

Update your API credentials in the configuration file:

```yaml
# backend/src/configs/exchanges/coinbase_sandbox.yaml
api_key: YOUR_API_KEY
api_secret: YOUR_API_SECRET
passphrase: YOUR_PASSPHRASE  # Required for Coinbase Pro API
endpoint: https://api-public.sandbox.exchange.coinbase.com
```

### 2. Basic Usage

```python
import asyncio
from infrastructure.exchanges import create_coinbase_exchange

async def main():
    # Create exchange instance
    exchange = create_coinbase_exchange()
    
    try:
        # Get market data (no auth needed)
        ticker = await exchange.get_ticker('BTC/USD')
        print(f"BTC Price: ${ticker['last']}")
        
        # Get account balance (auth needed)
        balance = await exchange.get_balance()
        print(f"USD Balance: {balance['USD']['free']}")
        
        # Place a limit order
        order = await exchange.place_limit_order(
            symbol='BTC/USD',
            side='buy',
            amount=0.001,
            price=50000.0
        )
        print(f"Order placed: {order['id']}")
        
    finally:
        await exchange.close()

# Run the example
asyncio.run(main())
```

### 3. Using Custom Configuration

```python
from infrastructure.exchanges import CoinbaseExchange

# Use custom config file
exchange = CoinbaseExchange('/path/to/your/config.yaml')
```

## API Reference

### BaseExchange Methods

#### Market Data (Public - No Authentication Required)
- `get_ticker(symbol)` - Get current price and volume data
- `get_orderbook(symbol, limit)` - Get order book depth
- `get_candles(symbol, timeframe, limit)` - Get OHLCV candlestick data
- `get_trades(symbol, limit)` - Get recent public trades
- `get_supported_symbols()` - Get all available trading pairs
- `get_market_info(symbol)` - Get detailed market information

#### Account Management (Private - Authentication Required)
- `get_balance()` - Get account balances for all currencies
- `get_account_info()` - Get detailed account information
- `get_trading_fees(symbol)` - Get trading fee information

#### Order Management (Private - Authentication Required)
- `place_market_order(symbol, side, amount)` - Place market order
- `place_limit_order(symbol, side, amount, price)` - Place limit order
- `cancel_order(order_id, symbol)` - Cancel existing order
- `get_order_status(order_id, symbol)` - Check order status
- `get_open_orders(symbol)` - Get all open orders
- `get_order_history(symbol, limit)` - Get order history
- `get_my_trades(symbol, limit)` - Get user's trade history

#### Advanced Trading (Private - Coinbase Specific)
- `place_stop_order(symbol, side, amount, stop_price, limit_price)` - Place stop orders
- `transfer(currency, amount, from_account, to_account)` - Transfer between accounts
- `get_deposit_address(currency)` - Get deposit address
- `withdraw(currency, amount, address, tag)` - Withdraw funds

## Configuration Files

### Environment Configurations

1. **Sandbox** (`coinbase_sandbox.yaml`)
   - For testing and development
   - Uses Coinbase sandbox environment
   - Safe for testing without real money

2. **Production** (`coinbase_production.yaml`)
   - For live trading
   - Uses real Coinbase exchange
   - ⚠️ **WARNING**: Real money transactions

### Configuration Format

```yaml
api_key: YOUR_API_KEY
api_secret: YOUR_API_SECRET
passphrase: YOUR_PASSPHRASE  # For Coinbase Pro API
endpoint: https://api-public.sandbox.exchange.coinbase.com

# Configuration notes:
# 1. For Coinbase Pro: api_key, api_secret, and passphrase required
# 2. For Advanced Trade: only api_key and api_secret required
# 3. Sandbox/production determined by endpoint URL
```

## Security Best Practices

1. **API Permissions**: Only grant necessary permissions to your API keys
2. **Environment Variables**: Store sensitive credentials as environment variables
3. **Rate Limiting**: The wrapper includes built-in rate limiting
4. **Error Handling**: Always use try-catch blocks for API calls
5. **Connection Management**: Always close connections when done

### Environment Variable Example

```yaml
api_key: ${COINBASE_API_KEY}
api_secret: ${COINBASE_API_SECRET}
passphrase: ${COINBASE_PASSPHRASE}
```

## Error Handling

The exchange wrapper provides detailed error messages:

```python
try:
    balance = await exchange.get_balance()
except Exception as e:
    print(f"Error: {e}")
    # Handle specific error cases
```

Common error scenarios:
- Invalid API credentials
- Insufficient balance
- Invalid trading pair
- Network connectivity issues
- Rate limit exceeded

## Testing

Run the example script to test your configuration:

```bash
cd backend
python examples/coinbase_example.py
```

The example script tests both public endpoints (no auth needed) and private endpoints (auth required).

## Advanced Usage

### Custom Exchange Implementation

To add support for a new exchange:

1. Create a new file (e.g., `binance.py`)
2. Extend `BaseExchange`
3. Implement `_initialize_exchange()` method
4. Add exchange-specific methods as needed

```python
from .base import BaseExchange
import ccxt.async_support as ccxt

class BinanceExchange(BaseExchange):
    def _initialize_exchange(self):
        self.exchange = ccxt.binance({
            'apiKey': self.config['api_key'],
            'secret': self.config['api_secret'],
            'sandbox': self.config.get('sandbox', False)
        })
```

### Async Context Manager

Use the exchange as an async context manager for automatic cleanup:

```python
async with create_coinbase_exchange() as exchange:
    balance = await exchange.get_balance()
    # Connection automatically closed
```

## Dependencies

- **ccxt**: Cryptocurrency exchange library
- **pyyaml**: YAML configuration file support
- **asyncio**: Asynchronous programming support

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API credentials in configuration file
   - Check API key permissions on Coinbase
   - Ensure correct endpoint (sandbox vs production)

2. **Connection Errors**
   - Check internet connectivity
   - Verify endpoint URLs
   - Check for firewall/proxy issues

3. **Rate Limiting**
   - The wrapper includes automatic rate limiting
   - Reduce request frequency if needed
   - Check Coinbase rate limit documentation

### Debug Mode

Enable debug logging to see detailed API interactions:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This exchange infrastructure is part of the crypto trading bot project. 