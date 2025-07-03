"""
Deck management for poker simulation
"""

import random
from typing import List
from .models import Card, Suit, Rank


class Deck:
    def __init__(self):
        self.cards = []
        self.reset()
    
    def reset(self):
        """Create a fresh 52-card deck"""
        self.cards = []
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(rank, suit))
        self.shuffle()
    
    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)
    
    def deal(self, count: int = 1) -> List[Card]:
        """
        Deal cards from the deck
        
        Args:
            count: Number of cards to deal
            
        Returns:
            List of dealt cards
            
        Raises:
            ValueError: If not enough cards in deck
        """
        if len(self.cards) < count:
            raise ValueError(f"Not enough cards in deck. Requested: {count}, Available: {len(self.cards)}")
        
        dealt_cards = []
        for _ in range(count):
            dealt_cards.append(self.cards.pop())
        
        return dealt_cards
    
    def deal_one(self) -> Card:
        """Deal a single card"""
        return self.deal(1)[0]
    
    def burn(self) -> Card:
        """Burn (discard) the top card"""
        if len(self.cards) == 0:
            raise ValueError("Cannot burn card from empty deck")
        return self.cards.pop()
    
    def cards_remaining(self) -> int:
        """Get the number of cards remaining in the deck"""
        return len(self.cards)
    
    def is_empty(self) -> bool:
        """Check if the deck is empty"""
        return len(self.cards) == 0
    
    def peek(self, count: int = 1) -> List[Card]:
        """
        Peek at the top cards without removing them
        
        Args:
            count: Number of cards to peek at
            
        Returns:
            List of top cards (without removing them)
        """
        if len(self.cards) < count:
            raise ValueError(f"Not enough cards to peek. Requested: {count}, Available: {len(self.cards)}")
        
        return self.cards[-count:]
    
    def __len__(self):
        """Return the number of cards in the deck"""
        return len(self.cards)
    
    def __str__(self):
        """String representation of the deck"""
        return f"Deck with {len(self.cards)} cards" 