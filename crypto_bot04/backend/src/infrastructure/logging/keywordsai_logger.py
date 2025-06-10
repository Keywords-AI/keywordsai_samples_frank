"""
KeywordsAI Request Logger

Logs all LLM requests to the KeywordsAI platform for analytics and monitoring.
"""

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import aiohttp
import yaml


class KeywordsAILogger:
    """Logger for sending LLM requests to KeywordsAI platform."""
    
    def __init__(self, config_path: str = None):
        """Initialize the KeywordsAI logger."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'configs', 'llm.yaml')
        
        self.config = self._load_config(config_path)
        self.enabled = self.config.get('keywordsai', {}).get('enabled', False)
        self.api_key = self._resolve_api_key(self.config.get('keywordsai', {}).get('api_key'))
        self.endpoint = self.config.get('keywordsai', {}).get('endpoint', 'https://api.keywordsai.co/api/request-logs/create/')
        self.customer_identifier = self.config.get('keywordsai', {}).get('customer_identifier', 'crypto_trading_bot')
        
        if self.enabled and not self.api_key:
            print("⚠️  KeywordsAI logging enabled but no API key found. Disabling logging.")
            self.enabled = False
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"⚠️  Failed to load LLM config: {e}")
            return {}
    
    def _resolve_api_key(self, api_key_config: Optional[str]) -> Optional[str]:
        """Resolve API key from environment variable or direct value."""
        if not api_key_config:
            return None
            
        if api_key_config.startswith('${') and api_key_config.endswith('}'):
            env_var_name = api_key_config[2:-1]  # Remove ${ and }
            resolved_key = os.environ.get(env_var_name)
            if not resolved_key:
                print(f"⚠️  Environment variable {env_var_name} not found")
            return resolved_key
        else:
            # It's a direct API key value
            return api_key_config
    
    async def log_llm_request(
        self,
        model: str,
        prompt_messages: List[Dict[str, str]],
        completion_message: Dict[str, str],
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        latency: float,
        ttft: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
        error_message: str = "",
        warnings: str = ""
    ) -> bool:
        """
        Log an LLM request to KeywordsAI platform.
        
        Args:
            model: Model used (e.g., 'gpt-4o')
            prompt_messages: List of prompt messages
            completion_message: Completion response
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cost: Cost of the inference in USD
            latency: Total generation time in seconds
            ttft: Time to first token in seconds
            metadata: Additional metadata
            status_code: HTTP status code
            error_message: Error message if failed
            warnings: Warning messages
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        
        if not self.enabled:
            return False
        
        try:
            # Prepare payload according to KeywordsAI API spec
            payload = {
                "model": model,
                "prompt_messages": prompt_messages,
                "completion_message": completion_message,
                "customer_params": {
                    "customer_identifier": self.customer_identifier,
                    "name": "Crypto Trading Bot"
                },
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost": cost,
                "latency": latency,  # Total generation time
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "time_to_first_token": ttft,
                "metadata": metadata or {},
                "stream": False,
                "status_code": status_code,
                "warnings": warnings,
                "error_message": error_message,
                "type": "text"
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Send request to KeywordsAI
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status in [200, 201]:
                        print(f"✅ KeywordsAI: Logged LLM request ({model}, {completion_tokens} tokens)")
                        return True
                    else:
                        response_text = await response.text()
                        print(f"⚠️  KeywordsAI logging failed: {response.status} - {response_text}")
                        return False
                        
        except Exception as e:
            print(f"⚠️  KeywordsAI logging error: {e}")
            return False
    
    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost based on model and token usage.
        
        OpenAI GPT-4o pricing (as of 2024):
        - Input: $0.0025 per 1K tokens
        - Output: $0.01 per 1K tokens
        """
        
        if model.startswith('gpt-4'):
            input_cost = (prompt_tokens / 1000) * 0.0025
            output_cost = (completion_tokens / 1000) * 0.01
            return input_cost + output_cost
        elif model.startswith('gpt-3.5'):
            input_cost = (prompt_tokens / 1000) * 0.0005
            output_cost = (completion_tokens / 1000) * 0.0015
            return input_cost + output_cost
        else:
            # Default estimate
            return (prompt_tokens + completion_tokens) / 1000 * 0.002


# Global logger instance
_logger_instance = None

def get_keywordsai_logger() -> KeywordsAILogger:
    """Get or create the global KeywordsAI logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = KeywordsAILogger()
    return _logger_instance 