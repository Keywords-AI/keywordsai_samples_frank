"""
Enhanced data models and enums for the poker simulation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank(Enum):
    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("T", 10)
    JACK = ("J", 11)
    QUEEN = ("Q", 12)
    KING = ("K", 13)
    ACE = ("A", 14)
    
    @property
    def symbol(self):
        return self.value[0]
    
    @property  
    def numeric_value(self):
        return self.value[1]


@dataclass
class Card:
    rank: Rank
    suit: Suit
    
    def __str__(self):
        return f"{self.rank.symbol}{self.suit.value}"
    
    def __repr__(self):
        return self.__str__()
    
    def to_excel_format(self) -> str:
        """Convert card to Excel-friendly format (e.g., 'AC' instead of 'A♣')"""
        suit_map = {"♥": "H", "♦": "D", "♣": "C", "♠": "S"}
        return f"{self.rank.symbol}{suit_map[self.suit.value]}"


class Action(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass
class Player:
    name: str
    model: str
    chips: int = 1500
    hole_cards: List[Card] = field(default_factory=list)
    current_bet: int = 0
    is_folded: bool = False
    is_all_in: bool = False
    personality: str = "professional and analytical"
    
    def reset_for_hand(self):
        """Reset player state for a new hand"""
        self.hole_cards = []
        self.current_bet = 0
        self.is_folded = False
        self.is_all_in = False
    
    def can_act(self) -> bool:
        """Check if player can take action"""
        return not self.is_folded and not self.is_all_in and self.chips > 0
    
    def get_hole_cards_string(self, hidden: bool = False) -> str:
        """Get hole cards as string, optionally hidden"""
        if hidden or not self.hole_cards:
            return "xx, xx"
        if len(self.hole_cards) >= 2:
            return f"{self.hole_cards[0].to_excel_format()}, {self.hole_cards[1].to_excel_format()}"
        return "xx, xx"


@dataclass
class GameState:
    """Represents the current state of the poker game"""
    hand_number: int
    pot: int
    current_bet: int
    community_cards: List[Card]
    players: List[Player]
    dealer_position: int
    small_blind: int
    big_blind: int
    betting_round: str
    action_history: List[str]
    phase: str = "early"
    
    def get_active_players(self) -> List[Player]:
        """Get list of players who can still act"""
        return [p for p in self.players if p.can_act()]
    
    def get_community_cards_string(self) -> List[str]:
        """Get community cards as list of Excel-friendly strings"""
        cards = [""] * 5
        for i, card in enumerate(self.community_cards[:5]):
            cards[i] = card.to_excel_format()
        return cards


@dataclass
class HandResult:
    """Result of a poker hand"""
    hand_number: int
    winners: List[str]
    pot_amount: int
    community_cards: List[Card]
    player_hands: Dict[str, List[Card]]
    hand_descriptions: Dict[str, str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_winner_names(self) -> str:
        """Get comma-separated winner names"""
        return ", ".join(self.winners)


@dataclass
class TournamentResult:
    """Final tournament result"""
    tournament_id: str
    winner: str
    final_standings: List[Tuple[str, int]]  # (player_name, final_chips)
    total_hands: int
    duration_minutes: float
    timestamp: datetime = field(default_factory=datetime.now) 