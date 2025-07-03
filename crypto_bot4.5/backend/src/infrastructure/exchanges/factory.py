#!/usr/bin/env python3
"""
Exchange factory for creating different exchange instances.
Supports multiple exchanges and environments.
"""

import os
from enum import Enum
from typing import Optional

from .base import BaseExchange

class ExchangeType(Enum):
    """Supported exchange types."""
    COINBASE_SANDBOX = "coinbase_sandbox"  # Sandbox using manual HTTP
    COINBASE_PRODUCTION = "coinbase_production"  # Production placeholder (not implemented)

class Environment(Enum):
    """Environment types."""
    SANDBOX = "sandbox"
    PRODUCTION = "production"

def create_exchange(exchange_type: ExchangeType, environment: Environment = Environment.SANDBOX, 
                   config_path: Optional[str] = None) -> BaseExchange:
    """
    Create an exchange instance based on type and environment.
    
    Args:
        exchange_type: Type of exchange to create
        environment: Environment (sandbox/production)
        config_path: Optional path to custom config file
        
    Returns:
        Configured exchange instance
        
    Raises:
        ValueError: If unsupported exchange type or environment
        NotImplementedError: If production environment requested
    """
    factory = ExchangeFactory()
    return factory.create_exchange(exchange_type, environment, config_path)

class ExchangeFactory:
    """Factory for creating exchange instances."""
    
    def create_exchange(self, exchange_type: ExchangeType, environment: Environment = Environment.SANDBOX,
                       config_path: Optional[str] = None) -> BaseExchange:
        """
        Create an exchange instance.
        
        Args:
            exchange_type: Type of exchange to create
            environment: Environment (sandbox/production) 
            config_path: Optional path to custom config file
            
        Returns:
            Configured exchange instance
        """
        if exchange_type == ExchangeType.COINBASE_SANDBOX:
            return self._create_coinbase_sandbox(config_path)
        elif exchange_type == ExchangeType.COINBASE_PRODUCTION:
            return self._create_coinbase_production(config_path)
        else:
            raise ValueError(f"Unsupported exchange type: {exchange_type}")
    
    def _create_coinbase_sandbox(self, config_path: Optional[str] = None):
        """Create Coinbase sandbox exchange (manual HTTP implementation)."""
        from .coinbase import create_coinbase_exchange
        
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'configs', 'exchanges', 'coinbase_sandbox.yaml'
            )
        
        print("🧪 Creating Coinbase SANDBOX exchange (manual HTTP)")
        return create_coinbase_exchange(config_path)
    
    def _create_coinbase_production(self, config_path: Optional[str] = None):
        """Create Coinbase production exchange (not implemented)."""
        from .coinbase_official import create_coinbase_official_exchange
        
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'configs', 'exchanges', 'coinbase_production.yaml'
            )
        
        print("⚠️  Production environment not implemented yet")
        return create_coinbase_official_exchange(config_path)

# Convenience functions for common use cases
def create_coinbase_sandbox_exchange(config_path: Optional[str] = None) -> BaseExchange:
    """Create Coinbase sandbox exchange directly."""
    return create_exchange(ExchangeType.COINBASE_SANDBOX, Environment.SANDBOX, config_path)

def create_coinbase_production_exchange(config_path: Optional[str] = None) -> BaseExchange:
    """Create Coinbase production exchange (not implemented)."""
    return create_exchange(ExchangeType.COINBASE_PRODUCTION, Environment.PRODUCTION, config_path)

# Default function - creates sandbox by default for safety
def create_default_exchange(config_path: Optional[str] = None) -> BaseExchange:
    """Create default exchange (Coinbase sandbox for safety)."""
    print("🛡️  Creating default exchange (Coinbase SANDBOX for safety)")
    return create_coinbase_sandbox_exchange(config_path) 