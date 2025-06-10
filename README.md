# KeywordsAI Samples

This repository contains sample applications demonstrating various integrations with KeywordsAI and OpenAI APIs.

## Project Structure

```
keywordsai_samples/
├── get_start01-03/          # Getting started samples
│   ├── logging_sample.py    # Keywords AI logging example
│   ├── proxy_sample.py      # Keywords AI proxy example
│   ├── tracing_sample.py    # Keywords AI tracing example
│   ├── requirements.txt     # Python dependencies
│   └── env.example          # Environment variables template
└── crypto_bot04/            # AI Crypto Trading Bot
    ├── backend/
    │   ├── src/
    │   │   ├── api/         # API endpoints and routes
    │   │   ├── config/      # Configuration files
    │   │   ├── models/      # Data models
    │   │   ├── services/    # Business logic
    │   │   └── utils/       # Utility functions
    │   ├── tests/           # Backend tests
    │   └── requirements.txt # Python dependencies
    ├── frontend/            # Frontend application
    ├── start_backend.py     # Backend startup script
    └── env.example          # Environment variables template
```

## Getting Started Samples

The `get_start01-03/` folder contains three basic examples of integrating with KeywordsAI:

### Setup for Get Started Samples

1. Navigate to the get_start directory:
   ```bash
   cd get_start01-03
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your actual API keys
   ```

4. Run any of the samples:
   ```bash
   python logging_sample.py    # Keywords AI logging
   python proxy_sample.py      # Keywords AI proxy
   python tracing_sample.py    # Keywords AI tracing with OpenAI
   ```

### Sample Descriptions

- **logging_sample.py**: Demonstrates how to log requests to Keywords AI
- **proxy_sample.py**: Shows how to use Keywords AI as a proxy for OpenAI API calls
- **tracing_sample.py**: Implements distributed tracing for LLM workflows

## Crypto Trading Bot

The `crypto_bot04/` folder contains an advanced AI-powered cryptocurrency trading bot.

### Features

- Integration with Coinbase Sandbox API
- LLM-based trading decisions using Keywords AI
- Multiple trading strategies
- Real-time market data processing
- Risk management
- Performance analytics
- Web interface

### Setup for Crypto Bot

1. Navigate to the crypto bot directory:
   ```bash
   cd crypto_bot04
   ```

2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

4. Run the backend:
   ```bash
   python start_backend.py
   ```

## Environment Variables

Both samples require API keys configured in `.env` files:

### For Get Started Samples
- `OPENAI_API_KEY`: Your OpenAI API key (required for tracing_sample.py)
- `KEYWORDSAI_API_KEY`: Your Keywords AI API key (required for all samples)

### For Crypto Bot
- `OPENAI_API_KEY`: Your OpenAI API key for LLM integration
- `KEYWORDSAI_API_KEY`: Your Keywords AI API key for logging
- `COINBASE_SANDBOX_API_KEY`: Your Coinbase sandbox API key
- `COINBASE_SANDBOX_API_SECRET`: Your Coinbase sandbox API secret

## Security Notes

- Never commit `.env` files to version control
- Use the provided `env.example` files as templates
- Keep your API keys secure and regenerate them if compromised

## Requirements

- Python 3.8+
- OpenAI API access
- Keywords AI API access
- Coinbase API access (for crypto bot only)

## License

MIT 