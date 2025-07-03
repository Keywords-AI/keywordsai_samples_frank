# Coinbase Exchange Examples

**Clean, focused examples for crypto trading bot development.**

## 🎯 **Three Essential Examples**

### 📊 **Market Data** = Real production data, no authentication needed
### 🧪 **Trading** = Safe sandbox, authentication required  
### 🤖 **LLM Strategy** = AI-powered trading decisions with GPT-4o

---

## 📊 **Market Data Example** (No Auth Needed)

### `market_data_example.py` 🌟 
- **Real-time cryptocurrency prices** (700+ trading pairs)
- **Live order books** with bid/ask spreads
- **Historical candles** and volume data
- **Zero setup** - no API keys needed!

**Run it:**
```bash
python examples/market_data_example.py
```

**Perfect for:** Price monitoring, market analysis, technical analysis, portfolio tracking

---

## 🧪 **Trading Example** (Auth Required)

### `trading_example.py` 🛡️
- **Safe sandbox trading** with test funds
- **Account balance management**
- **Order placement and cancellation**  
- **Complete safety** - no real money involved

**Run it:**
```bash
python examples/trading_example.py
```

**Perfect for:** Testing trading strategies, learning order management, bot development

---

## 🤖 **LLM Strategy Pipeline** (OpenAI + Coinbase)

### `llm_strategy_pipeline_example.py` 🧠
- **GPT-4o powered trading decisions** with real market analysis
- **Complete pipeline**: Market data → Portfolio → LLM → Trading decision
- **Real market data** + safe sandbox trading
- **Intelligent reasoning** with confidence scores

**Setup:**
```bash
# 1. Add OpenAI API key to .env:
echo "OPENAI_API_KEY=your_openai_key" >> .env

# 2. Run the pipeline:
python examples/llm_strategy_pipeline_example.py
```

**What it does:**
1. Collects real market data (BTC ~$105K, live prices)
2. Gets sandbox account balance  
3. Feeds data to GPT-4o: "Using momentum strategy, what should I do?"
4. Returns structured trading decision with reasoning

**Perfect for:** AI trading bots, strategy backtesting, autonomous trading systems

---

## 🚀 **Quick Start**

### **Step 1: Market Data** (No setup needed)
```bash
python examples/market_data_example.py
```
✅ **See live crypto prices instantly!**

### **Step 2: Trading Setup** (One-time)
1. Get Coinbase Advanced Trade sandbox API credentials
2. Create `.env` file:
   ```
   COINBASE_SANDBOX_API_KEY=your_key
   COINBASE_SANDBOX_API_SECRET=your_secret
   ```
3. Test trading:
   ```bash
   python examples/trading_example.py
   ```
✅ **Practice trading safely!**

### **Step 3: AI Trading** (Optional)
1. Add OpenAI API key to `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   ```
2. Run AI pipeline:
   ```bash
   python examples/llm_strategy_pipeline_example.py
   ```
✅ **See AI make trading decisions!**

---

## 📊 **What You'll See**

### Market Data:
- **Real BTC price**: ~$105,000
- **Live order book**: Real bids/asks with trading sizes
- **Historical data**: Hourly candles with High/Low/Close
- **700+ pairs**: All major cryptocurrencies

### Trading:
- **Sandbox balance**: Test funds (BTC: 0.5, USDC: 100, etc.)
- **Safe orders**: Demo placement with automatic cancellation
- **Full API access**: All trading functions work safely

### LLM Strategy:
- **Real market analysis**: "BTC price is exceptionally high at $104K+"
- **Smart decisions**: GPT-4o chooses hold/buy/sell with reasoning
- **High confidence**: 0.90+ confidence scores on clear decisions
- **Risk awareness**: Won't trade with $0 balance or overvalued assets

---

## 🎯 **Perfect Foundation For:**

- **📊 Price monitoring bots** (market_data_example.py)
- **🧪 Trading strategy testers** (trading_example.py)  
- **🤖 AI trading systems** (llm_strategy_pipeline_example.py)
- **📈 Portfolio trackers** (market_data_example.py)
- **🤖 Arbitrage bots** (combine examples)
- **📊 Technical analysis tools** (market_data_example.py)

---

## 🛡️ **Safety**

- **Market data**: Public endpoints, no authentication, zero risk
- **Trading**: Sandbox only, test funds, zero financial risk
- **LLM decisions**: Analysis only, safe sandbox execution
- **Clean separation**: Market data and trading are completely independent

---

## 🔧 **Dependencies**

```bash
pip install aiohttp python-dotenv pyyaml openai
```

---

**🎉 Clean, focused, and ready for crypto bot development!**

- **📊 Market data**: `market_data_example.py` - real-time, no auth
- **🧪 Trading**: `trading_example.py` - safe sandbox, auth required
- **🤖 AI Strategy**: `llm_strategy_pipeline_example.py` - GPT-4o trading decisions

**That's it! Everything you need for modern crypto trading bots. 🚀** 