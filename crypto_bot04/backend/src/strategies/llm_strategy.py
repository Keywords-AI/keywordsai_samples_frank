"""
LLM-Based Trading Strategy

Uses GPT-4o to analyze market conditions and make autonomous trading decisions.
The LLM acts as the strategy brain, choosing tactics and making trade decisions.
"""

import json
import asyncio
import time
from typing import Dict, Any
from datetime import datetime

from .base import BaseStrategy, TradingDecision, MarketData, PortfolioData, MultiAssetTradingDecision, AssetDecision
# KeywordsAI import will be done dynamically to avoid import issues

try:
    import openai
except ImportError:
    openai = None


class LLMStrategy(BaseStrategy):
    """
    LLM-powered autonomous trading strategy.
    
    Uses GPT-4o to:
    1. Analyze current market conditions
    2. Choose the best trading strategy for current conditions
    3. Make specific trading decisions
    4. Provide reasoning for decisions
    """
    
    def _load_llm_config(self) -> Dict[str, Any]:
        """Load LLM configuration from YAML file."""
        import yaml
        import os
        
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'configs', 'llm.yaml'
        )
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config or {}
        except FileNotFoundError:
            print(f"⚠️  LLM config file not found: {config_path}")
            return {}
        except Exception as e:
            print(f"⚠️  Error loading LLM config: {e}")
            return {}
    
    def _resolve_api_key(self, api_key_config: str) -> str:
        """Resolve API key from environment variable if needed."""
        import os
        
        if not api_key_config:
            return None
            
        # Check if it's an environment variable reference
        if api_key_config.startswith('${') and api_key_config.endswith('}'):
            env_var_name = api_key_config[2:-1]  # Remove ${ and }
            resolved_key = os.environ.get(env_var_name)
            if not resolved_key:
                print(f"⚠️  Environment variable {env_var_name} not found")
            return resolved_key
        else:
            # It's a direct API key value
            return api_key_config
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the LLM strategy."""
        # Load config from YAML file if no config provided
        if config is None:
            config = self._load_llm_config()
            
        super().__init__("LLM_Strategy", config)
        
        # LLM Configuration
        self.model = self.get_config('model', 'gpt-4o')
        self.api_key = self._resolve_api_key(self.get_config('api_key', None))
        self.temperature = self.get_config('temperature', 0.1)
        self.max_tokens = self.get_config('max_tokens', 500)
        
        # Trading Configuration
        self.max_trade_size_usd = self.get_config('max_trade_size_usd', 50)
        self.max_positions = self.get_config('max_positions', 3)
        self.supported_symbols = self.get_config('supported_symbols', ['BTC/USD', 'ETH/USD'])
        
        # Initialize OpenAI client
        if openai and self.api_key:
            # For OpenAI v1.0+, we use the OpenAI class constructor
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        elif not openai:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        elif not self.api_key:
            raise ValueError("OpenAI API key not provided in config")
        
        # Initialize KeywordsAI logger
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from src.infrastructure.logging.keywordsai_logger import get_keywordsai_logger
            self.keywordsai_logger = get_keywordsai_logger()
            print(f"📊 KeywordsAI logging: {'enabled' if self.keywordsai_logger.enabled else 'disabled'}")
        except ImportError as e:
            print(f"⚠️  KeywordsAI logger not available: {e}")
            self.keywordsai_logger = None
    
    async def analyze(self, market_data: MarketData, portfolio_data: PortfolioData) -> TradingDecision:
        """
        Use LLM to analyze market data and make a trading decision.
        
        Args:
            market_data: Current market conditions
            portfolio_data: Current portfolio state
            
        Returns:
            TradingDecision: The LLM's trading decision
        """
        try:
            # Build the prompt with current data
            prompt = self._build_analysis_prompt(market_data, portfolio_data)
            
            # Get LLM decision
            llm_response = await self._get_llm_decision(prompt)
            
            # Parse and validate the decision
            decision = self._parse_llm_response(llm_response)
            
            # Record the decision
            self.record_decision(decision)
            
            return decision
            
        except Exception as e:
            # Fallback to safe 'hold' decision if LLM fails
            fallback_decision = TradingDecision(
                action='hold',
                symbol='BTC/USD',
                amount=0.0,
                order_type='market',
                reasoning=f"LLM analysis failed: {str(e)}. Defaulting to hold.",
                confidence=0.0,
                strategy_used=self.name
            )
            self.record_decision(fallback_decision)
            return fallback_decision
    
    def _build_analysis_prompt(self, market_data: MarketData, portfolio_data: PortfolioData) -> str:
        """Build the prompt for LLM analysis."""
        
        # Format market data
        market_summary = []
        for symbol, price in market_data.prices.items():
            if symbol in self.supported_symbols:
                market_summary.append(f"{symbol}: ${price:,.2f}")
        
        # Format portfolio data
        portfolio_summary = []
        total_value = 0
        for asset, balance in portfolio_data.balances.items():
            if balance > 0:
                # Estimate USD value
                if asset == 'USD' or asset == 'USDC':
                    usd_value = balance
                elif f"{asset}/USD" in market_data.prices:
                    usd_value = balance * market_data.prices[f"{asset}/USD"]
                else:
                    usd_value = 0
                
                total_value += usd_value
                portfolio_summary.append(f"{asset}: {balance:.4f} (~${usd_value:.2f})")
        
        prompt = f"""You are an autonomous crypto trading AI. Analyze the current market and portfolio state, then make ONE trading decision.

CURRENT MARKET DATA:
{chr(10).join(market_summary)}

CURRENT PORTFOLIO:
{chr(10).join(portfolio_summary)}
Total Portfolio Value: ~${total_value:.2f}

TRADING CONSTRAINTS:
- Max trade size: ${self.max_trade_size_usd}
- Supported symbols: {', '.join(self.supported_symbols)}
- You can only make ONE trade decision
- Available actions: buy, sell, hold

TASK:
1. Analyze current market conditions
2. Choose the best trading strategy for this moment (momentum, mean reversion, DCA, etc.)
3. Make ONE specific trading decision
4. Give ONLY the strategy name as reasoning (no explanations)

Respond ONLY with a JSON object in this exact format:
{{
    "strategy_chosen": "momentum_trading|mean_reversion|dca|arbitrage|hold",
    "action": "buy|sell|hold",
    "symbol": "BTC/USD|ETH/USD",
    "amount": 0.001,
    "order_type": "market|limit",
    "price": null,
    "reasoning": "Momentum Trading",
    "confidence": 0.85
}}

Important: 
- Only trade if you see a clear opportunity
- Consider your current portfolio balance
- For "reasoning" field, use ONLY strategy names like: "Momentum Trading", "Mean Reversion", "Market Making", "Scalping", "Hold Strategy"
- Set confidence between 0.0 and 1.0"""

        return prompt
    
    async def _get_llm_decision(self, prompt: str) -> str:
        """Get decision from LLM."""
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": self.get_config('system_prompt', 'You are a professional crypto trading AI.')
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")

    async def _get_llm_multi_asset_decision(self, prompt: str) -> str:
        """Get multi-asset decision from LLM using function calls for structured output."""
        try:
            # Define the function schema for multi-asset trading decisions
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "make_trading_decisions",
                        "description": "Make trading decisions for multiple crypto assets",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "decisions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "symbol": {
                                                "type": "string",
                                                "description": "Trading symbol like BTC/USD or ETH/USD"
                                            },
                                            "action": {
                                                "type": "string",
                                                "enum": ["buy", "sell", "hold"],
                                                "description": "Trading action to take"
                                            },
                                            "amount_usd": {
                                                "type": "number",
                                                "minimum": 0,
                                                "maximum": 5000,
                                                "description": "Amount in USD to trade (0 for hold, max $5000)"
                                            },
                                            "confidence": {
                                                "type": "number",
                                                "minimum": 0.0,
                                                "maximum": 1.0,
                                                "description": "Confidence level for this decision"
                                            }
                                        },
                                        "required": ["symbol", "action", "amount_usd", "confidence"]
                                    }
                                },
                                "overall_strategy": {
                                    "type": "string",
                                    "description": "Overall trading strategy being employed"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "Strategy name only (e.g. 'Momentum Trading', 'Market Making')"
                                }
                            },
                            "required": ["decisions", "overall_strategy", "reasoning"]
                        }
                    }
                }
            ]
            
            # Track timing for logging
            start_time = time.time()
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self.get_config('system_prompt', 'You are a professional crypto trading AI.')
                        },
                        {"role": "user", "content": prompt}
                    ],
                    tools=tools,
                    tool_choice={"type": "function", "function": {"name": "make_trading_decisions"}},
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            )
            
            # Calculate timing
            end_time = time.time()
            latency = end_time - start_time
            
            # Extract function call result
            tool_call = response.choices[0].message.tool_calls[0]
            function_args = tool_call.function.arguments
            
            # Log to KeywordsAI if enabled
            if self.keywordsai_logger and self.keywordsai_logger.enabled:
                try:
                    # Prepare messages for logging
                    prompt_messages = [
                        {
                            "role": "system",
                            "content": self.get_config('system_prompt', 'You are a professional crypto trading AI.')
                        },
                        {"role": "user", "content": prompt}
                    ]
                    
                    completion_message = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": function_args
                                }
                            }
                        ]
                    }
                    
                    # Estimate token counts (rough approximation)
                    prompt_tokens = len(prompt.split()) * 1.3  # Rough token estimation
                    completion_tokens = len(function_args.split()) * 1.3
                    
                    # Estimate cost
                    cost = self.keywordsai_logger.estimate_cost(self.model, int(prompt_tokens), int(completion_tokens))
                    
                    # Log the request
                    await self.keywordsai_logger.log_llm_request(
                        model=self.model,
                        prompt_messages=prompt_messages,
                        completion_message=completion_message,
                        prompt_tokens=int(prompt_tokens),
                        completion_tokens=int(completion_tokens),
                        cost=cost,
                        latency=latency,
                        metadata={
                            "strategy": "multi_asset_trading",
                            "trading_bot": "crypto_bot04",
                            "function_call": "make_trading_decisions"
                        }
                    )
                except Exception as e:
                    print(f"⚠️  Failed to log to KeywordsAI: {e}")
            
            return function_args  # This will be JSON string
            
        except Exception as e:
            raise Exception(f"LLM function call failed: {str(e)}")
    
    def _parse_llm_response(self, response: str) -> TradingDecision:
        """Parse LLM response into a TradingDecision."""
        
        try:
            # Try to extract JSON from response
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            data = json.loads(response_clean)
            
            # Validate required fields
            required_fields = ['action', 'symbol', 'amount', 'order_type', 'reasoning']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate action
            if data['action'] not in ['buy', 'sell', 'hold']:
                raise ValueError(f"Invalid action: {data['action']}")
            
            # Validate symbol
            if data['symbol'] not in self.supported_symbols:
                raise ValueError(f"Unsupported symbol: {data['symbol']}")
            
            # Validate amount
            amount = float(data['amount'])
            if amount < 0:
                raise ValueError("Amount cannot be negative")
            
            # Create TradingDecision
            decision = TradingDecision(
                action=data['action'],
                symbol=data['symbol'],
                amount=amount,
                order_type=data['order_type'],
                price=data.get('price'),
                reasoning=data['reasoning'],
                confidence=float(data.get('confidence', 0.5)),
                strategy_used=f"{self.name} ({data.get('strategy_chosen', 'unknown')})"
            )
            
            return decision
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this strategy."""
        return {
            'name': self.name,
            'type': 'LLM-powered',
            'model': self.model,
            'description': 'Autonomous trading using GPT-4o AI',
            'features': [
                'Market condition analysis',
                'Autonomous strategy selection',
                'Reasoning for decisions',
                'Adaptive to market changes'
            ],
            'supported_symbols': self.supported_symbols,
            'max_trade_size_usd': self.max_trade_size_usd,
            'parameters': {
                'temperature': self.temperature,
                'max_tokens': self.max_tokens,
                'max_positions': self.max_positions
            }
        }

    async def analyze_multi_asset(self, market_data: MarketData, portfolio_data: PortfolioData) -> MultiAssetTradingDecision:
        """
        Use LLM to analyze market data and make multi-asset trading decisions.
        
        Args:
            market_data: Current market conditions
            portfolio_data: Current portfolio state
            
        Returns:
            MultiAssetTradingDecision: Decisions for each asset
        """
        try:
            # Build the multi-asset prompt
            prompt = self._build_multi_asset_prompt(market_data, portfolio_data)
            
            # Get LLM decision using function calls
            llm_response = await self._get_llm_multi_asset_decision(prompt)
            
            # Parse multi-asset response (now it's structured JSON)
            decision = self._parse_multi_asset_function_response(llm_response)
            
            return decision
            
        except Exception as e:
            # Fallback to safe 'hold' decisions for all assets
            fallback_decisions = []
            
            for asset in ['BTC', 'ETH', 'USDT']:
                if asset in portfolio_data.balances and portfolio_data.balances[asset] > 0:
                    fallback_decisions.append(AssetDecision(
                        asset=asset,
                        action='hold',
                        target_symbol=f"{asset}/USD",
                        amount_usd=0.0,
                        confidence=0.0,
                        reasoning=f"LLM analysis failed: {str(e)}. Defaulting to hold."
                    ))
            
            return MultiAssetTradingDecision(
                decisions=fallback_decisions,
                overall_strategy="emergency_hold",
                overall_confidence=0.0,
                timestamp=datetime.now().isoformat()
            )

    def _build_multi_asset_prompt(self, market_data: MarketData, portfolio_data: PortfolioData) -> str:
        """Build the multi-asset analysis prompt using system prompt from config."""
        
        # Get system prompt from config
        system_prompt = self.get_config('system_prompt', '')
        
        # Get current prices and format market data
        btc_price = market_data.prices.get('BTC/USD', 0)
        eth_price = market_data.prices.get('ETH/USD', 0)
        btc_volume = market_data.volumes.get('BTC/USD', 0)
        eth_volume = market_data.volumes.get('ETH/USD', 0)
        
        # Format portfolio data with USD values
        portfolio_details = []
        total_usd_value = 0
        for asset, balance in portfolio_data.balances.items():
            if balance > 0:
                if asset == 'USD' or asset == 'USDT' or asset == 'USDC':
                    usd_value = balance
                elif asset == 'BTC':
                    usd_value = balance * btc_price
                elif asset == 'ETH':
                    usd_value = balance * eth_price
                else:
                    usd_value = 0
                
                total_usd_value += usd_value
                portfolio_details.append(f"{asset}: {balance:.4f} (~${usd_value:.2f})")

        # Build COMPREHENSIVE HIGH-FREQUENCY market data section
        market_data_text = f"""HIGH-FREQUENCY MARKET DATA:
BTC/USD: ${btc_price:,.2f} (30-min Volume: {btc_volume:.4f})
ETH/USD: ${eth_price:,.2f} (30-min Volume: {eth_volume:.4f})"""

        # Add comprehensive market analysis data
        for symbol in ['BTC/USD', 'ETH/USD']:
            if symbol in market_data.prices:
                # Add spread data
                if market_data.order_books and symbol in market_data.order_books:
                    order_book = market_data.order_books[symbol]
                    if order_book.get('spread') is not None:
                        spread = order_book.get('spread', 0)
                        spread_pct = order_book.get('spread_pct', 0)
                        market_data_text += f"\n{symbol} Spread: ${spread:.2f} ({spread_pct:.3f}%)"
                        
                        # Add market depth and sentiment
                        bid_volume = order_book.get('bid_volume', 0)
                        ask_volume = order_book.get('ask_volume', 0)
                        market_data_text += f"\n{symbol} Market Depth: Bids {bid_volume:.2f}, Asks {ask_volume:.2f}"
                
                # Add momentum data (15min, 30min, 24h changes)
                if market_data.momentum and symbol in market_data.momentum:
                    momentum = market_data.momentum[symbol]
                    change_15m = momentum.get('price_change_15m', 0)
                    change_30m = momentum.get('price_change_30m', 0)
                    change_24h = momentum.get('price_change_pct_24h', 0)
                    volatility = momentum.get('volatility', 0)
                    sentiment = momentum.get('market_sentiment', 'NEUTRAL')
                    activity = momentum.get('activity_level', 'MEDIUM')
                    
                    market_data_text += f"\n{symbol} Momentum: {change_15m:+.2f}% (15m), {change_30m:+.2f}% (30m), {change_24h:+.2f}% (24h)"
                    market_data_text += f"\n{symbol} Market: {sentiment} sentiment, {activity} activity, {volatility:.2f}% volatility"
                
                # Add trading activity data
                if market_data.trades_history and symbol in market_data.trades_history:
                    trades = market_data.trades_history[symbol]
                    buy_sell_ratio = trades.get('buy_sell_ratio', 1)
                    avg_trade_size = trades.get('avg_trade_size', 0)
                    total_trades = trades.get('total_recent_trades', 0)
                    
                    market_data_text += f"\n{symbol} Trading: Buy/Sell ratio {buy_sell_ratio:.2f}, Avg size {avg_trade_size:.4f}, {total_trades} recent trades"

        portfolio_text = f"""CURRENT PORTFOLIO:
{chr(10).join(portfolio_details)}
Total Value: ~${total_usd_value:.2f}"""

        # Build the user prompt with market and portfolio data only
        # System prompt is handled separately in the API call
        prompt = f"""{market_data_text}

{portfolio_text}"""

        # Debug: Show what's being sent to LLM
        print("🔍 DEBUG: Prompt being sent to LLM:")
        print("=" * 60)
        print(prompt)
        print("=" * 60)

        return prompt

    def _parse_multi_asset_function_response(self, response: str) -> MultiAssetTradingDecision:
        """Parse the LLM function call response into MultiAssetTradingDecision."""
        try:
            # Parse the JSON from function call
            data = json.loads(response)
            
            # Extract decisions
            decisions = []
            for decision_data in data.get('decisions', []):
                asset = decision_data['symbol'].split('/')[0]  # BTC from BTC/USD
                
                # Enforce max trade size limit
                amount_usd = float(decision_data['amount_usd'])
                if amount_usd > self.max_trade_size_usd:
                    print(f"⚠️  Limiting {asset} trade from ${amount_usd:.0f} to ${self.max_trade_size_usd}")
                    amount_usd = self.max_trade_size_usd
                
                decisions.append(AssetDecision(
                    asset=asset,
                    action=decision_data['action'],
                    target_symbol=decision_data['symbol'],
                    amount_usd=amount_usd,
                    confidence=float(decision_data['confidence']),
                    reasoning=data.get('reasoning', f"{decision_data['action']} {decision_data['symbol']}")
                ))
            
            from datetime import datetime
            return MultiAssetTradingDecision(
                decisions=decisions,
                overall_strategy=data.get('overall_strategy', 'multi_asset_analysis'),
                overall_confidence=sum(d.confidence for d in decisions) / len(decisions) if decisions else 0.0,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse LLM function response: {e}\nResponse was: {response}")

    def _parse_multi_asset_response(self, response: str) -> MultiAssetTradingDecision:
        """Parse the LLM multi-asset response - handles simple format from config."""
        try:
            print(f"🔍 DEBUG: Raw LLM response:\n{response}")
            
            # Parse the simple format from llm.yaml system_prompt:
            # BTC/USD: [buy/sell/hold], $[amount]
            # ETH/USD: [buy/sell/hold], $[amount]
            # Reasoning: [explanation]
            
            lines = response.strip().split('\n')
            decisions = []
            reasoning = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                print(f"🔍 DEBUG: Processing line: '{line}'")
                    
                # Parse asset decisions: "BTC/USD: buy, $500" or "BTC/USD: hold, $0"
                if ':' in line and ('BTC/USD' in line or 'ETH/USD' in line):
                    parts = line.split(':', 1)
                    symbol = parts[0].strip()
                    decision_text = parts[1].strip()
                    
                    print(f"  🎯 Found symbol decision: {symbol} -> {decision_text}")
                    
                    # Extract action and amount
                    if ',' in decision_text:
                        action_part, amount_part = decision_text.split(',', 1)
                        action = action_part.strip()
                        
                        # Extract amount (remove $ and parse)
                        amount_str = amount_part.strip().replace('$', '').replace(',', '')
                        try:
                            amount = float(amount_str)
                        except ValueError:
                            amount = 0.0
                    else:
                        action = decision_text.strip()
                        amount = 0.0
                    
                    print(f"    ➤ Action: {action}, Amount: ${amount}")
                    
                    # Create asset decision
                    asset = symbol.split('/')[0]  # BTC from BTC/USD
                    decisions.append(AssetDecision(
                        asset=asset,
                        action=action,
                        target_symbol=symbol,
                        amount_usd=amount,
                        confidence=0.8,  # Default confidence
                        reasoning=f"{action} {symbol}"
                    ))
                
                # Parse reasoning: "Reasoning: Market shows momentum..."
                elif line.lower().startswith('reasoning:'):
                    reasoning = line[10:].strip()  # Remove "Reasoning: "
                    print(f"  📝 Found reasoning: {reasoning}")
            
            print(f"🎯 Parsed {len(decisions)} decisions with reasoning: '{reasoning}'")
            
            # Update reasoning for all decisions if we found a global reasoning
            if reasoning:
                for decision in decisions:
                    decision.reasoning = reasoning
            
            # Create multi-asset decision
            from datetime import datetime
            return MultiAssetTradingDecision(
                decisions=decisions,
                overall_strategy="multi_asset_analysis",
                overall_confidence=0.8,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse LLM multi-asset response: {e}\nResponse was: {response}") 