"""
Configuration for Poker Tournament with 3-Phase Structure
"""

# Tournament Configuration
TOURNAMENT_CONFIG = {
    "total_hands": 50,
    "starting_chips": 1500,
    
    # Tournament phases with specific blind structure
    "phases": {
        "early": {
            "name": "Early Phase",
            "hand_range": (1, 10),
            "small_blind": 5,
            "big_blind": 10,
            "description": "🟢 EARLY PHASE (Hands 1-10): Blinds $5/$10"
        },
        "mid": {
            "name": "Mid Phase", 
            "hand_range": (11, 30),
            "small_blind": 20,
            "big_blind": 40,
            "description": "🟡 MID PHASE (Hands 11-30): Blinds $20/$40"
        },
        "late": {
            "name": "Late Phase",
            "hand_range": (31, 50),
            "small_blind": 50,
            "big_blind": 100,
            "description": "🔴 LATE PHASE (Hands 31-50): Blinds $50/$100"
        }
    }
}

# Player Configurations
PLAYER_CONFIGS = [
    {
        'name': 'GPT-4o',
        'model': 'gpt-4o',
        'starting_chips': 1500,
        'personality': 'professional but creative poker player who makes balanced decisions based on pot odds, position, and opponent behavior while maintaining proper bankroll management'
    },
    {
        'name': 'Claude',
        'model': 'claude-3-5-sonnet-20241022',
        'starting_chips': 1500,
        'personality': 'professional but creative poker player who makes balanced decisions based on pot odds, position, and opponent behavior while maintaining proper bankroll management'
    },
    {
        'name': 'Grok',
        'model': 'xai/grok-2-1212',
        'starting_chips': 1500,
        'personality': 'professional but creative poker player who makes balanced decisions based on pot odds, position, and opponent behavior while maintaining proper bankroll management'
    }
]

# Keywords AI Configuration
KEYWORDS_AI_CONFIG = {
    "base_url": "https://api.keywordsai.co/api/generate/",
    "timeout": 30,
    "max_retries": 3
}

# File Settings
FILE_SETTINGS = {
    "tournament_state_file": "tournament_state.json",
    "csv_log_prefix": "poker_tournament",
    "backup_directory": "backups"
}

# Logging Configuration
LOGGING_CONFIG = {
    "enable_detailed_logging": True,
    "console_colors": True,
    "csv_logging": True
} 