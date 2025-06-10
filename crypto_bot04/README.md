# 🤖 AI Crypto Trading Bot (Please Read)

A sophisticated crypto trading bot powered by GPT-4o with real-time monitoring and Keywords AI logging integration. Only test for Coinbase Sandbox now!!!!!!!

## ✨ Features

- **AI-Powered Trading**: Uses GPT-4o to analyze market conditions and make autonomous trading decisions
- **Real-time Dashboard**: Beautiful web interface showing live balance, P&L, and trading activity
- **Keywords AI Integration**: All LLM requests are logged to Keywords AI for analytics and monitoring
- **Coinbase Integration**: Supports both sandbox and production trading via Coinbase Advanced Trade API
- **Multiple Trading Strategies**: LLM dynamically chooses between momentum, mean reversion, DCA, and other strategies
- **Demo Mode**: Simulate trades and activity for demonstrations without real money

## 🏗️ Architecture

```
crypto_bot04/
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── api/         # REST API endpoints
│   │   │   ├── strategies/  # Trading strategies (LLM-based)
│   │   │   ├── infrastructure/
│   │   │   │   ├── exchanges/   # Exchange integrations (Coinbase, CCXT)
│   │   │   │   └── logging/     # Keywords AI logging
│   │   │   └── configs/     # Configuration files
│   │   └── requirements.txt
│   └── frontend/            # Simple HTML/CSS/JS dashboard
│       └── index.html       # Trading bot dashboard
```

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the `backend` directory:

```env
# OpenAI API Key (required for LLM strategy)
OPENAI_API_KEY=your_openai_api_key_here

# Keywords AI API Key (for logging)
KEYWORDSAI_API_KEY=your_keywordsai_api_key_here

# Coinbase API Credentials (for live trading)
COINBASE_SANDBOX_API_KEY=your_coinbase_api_key
COINBASE_SANDBOX_API_SECRET=your_coinbase_api_secret
```

### 3. Start the Backend

```bash
# From the backend directory
cd src
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. Open the Frontend

Simply open `frontend/index.html` in your web browser, or serve it locally:

```bash
# Option 1: Direct file opening
# Open frontend/index.html in your browser

# Option 2: Simple HTTP server (Python)
cd frontend
python -m http.server 3000
# Then visit http://localhost:3000

# Option 3: Simple HTTP server (Node.js)
cd frontend
npx serve .
```

## 🔧 API Endpoints

### Strategy Endpoints (`/v1/strategy/`)
- `GET /balance` - Get current portfolio balance
- `GET /status` - Get bot status and activity
- `GET /positions` - Get current trading positions
- `GET /trades` - Get recent trade history
- `POST /start` - Start the trading bot
- `POST /stop` - Stop the trading bot
- `POST /simulate-trade` - Simulate a trade for demo
- `POST /reset-demo` - Reset demo data

### LLM Endpoints (`/v1/llm/`)
- `GET /activity` - Get LLM activity and Keywords AI logs
- `GET /config` - Get LLM configuration
- `POST /log-demo-request` - Send demo log to Keywords AI

## ⚙️ Configuration

### LLM Strategy (`backend/src/configs/llm.yaml`)
```yaml
model: "gpt-4o"
temperature: 0.1
max_tokens: 500
max_trade_size_usd: 50
supported_symbols: ["BTC/USD", "ETH/USD"]

keywordsai:
  enabled: true
  api_key: "${KEYWORDSAI_API_KEY}"
  customer_identifier: "crypto_trading_bot"
```

### Exchange Configuration
- Supports Coinbase Advanced Trade API
- Sandbox mode for safe testing
- CCXT integration for multiple exchanges

## 🛡️ Safety Features

- **Sandbox Mode**: Test with fake money
- **Position Limits**: Maximum position sizes
- **Error Handling**: Graceful fallbacks when LLM fails
- **Demo Mode**: Simulate everything without real trades

## 🤝 Contributing

This is a demonstration project. Feel free to fork and modify for your own use cases!

## ⚠️ Disclaimer

Do not use with real money without thorough testing and understanding of the risks involved in cryptocurrency trading.

## 📝 License

MIT License - feel free to use for educational purposes. 
