"""
Hand evaluation logic for poker hands
"""

import random
from typing import List, Tuple, Dict
from collections import Counter
from .models import Card, Player, Rank


class HandEvaluator:
    
    HAND_RANKINGS = {
        "Royal Flush": 1000,
        "Straight Flush": 900,
        "Four of a Kind": 800,
        "Full House": 700,
        "Flush": 600,
        "Straight": 500,
        "Three of a Kind": 400,
        "Two Pair": 300,
        "Pair": 200,
        "High Card": 100
    }
    
    def __init__(self, simplified: bool = True):
        """
        Initialize hand evaluator
        
        Args:
            simplified: If True, use simplified random evaluation for simulation speed
        """
        self.simplified = simplified
    
    def evaluate_hand(self, player: Player, community_cards: List[Card]) -> Tuple[int, str]:
        """
        Evaluate a player's hand strength
        
        Args:
            player: The player whose hand to evaluate
            community_cards: The community cards on the board
            
        Returns:
            Tuple of (hand_strength, hand_description)
        """
        if player.is_folded:
            return 0, "Folded"
        
        all_cards = player.hole_cards + community_cards
        
        if len(all_cards) < 5:
            return self._evaluate_preflop(player.hole_cards)
        
        if self.simplified:
            return self._simplified_evaluation(all_cards)
        else:
            return self._full_evaluation(all_cards)
    
    def _evaluate_preflop(self, hole_cards: List[Card]) -> Tuple[int, str]:
        """Evaluate hole cards pre-flop"""
        if len(hole_cards) != 2:
            return 1, "Incomplete Hand"
        
        card1, card2 = hole_cards
        
        # Pocket pairs
        if card1.rank == card2.rank:
            strength = 50 + card1.rank.numeric_value * 3
            return strength, f"Pocket {card1.rank.symbol}s"
        
        # Suited cards
        if card1.suit == card2.suit:
            high_card = max(card1.rank.numeric_value, card2.rank.numeric_value)
            strength = 20 + high_card * 2
            return strength, f"{card1.rank.symbol}{card2.rank.symbol} suited"
        
        # Offsuit cards
        high_card = max(card1.rank.numeric_value, card2.rank.numeric_value)
        low_card = min(card1.rank.numeric_value, card2.rank.numeric_value)
        strength = 10 + high_card + low_card
        return strength, f"{card1.rank.symbol}{card2.rank.symbol} offsuit"
    
    def _simplified_evaluation(self, all_cards: List[Card]) -> Tuple[int, str]:
        """Simplified random-based evaluation for simulation speed"""
        hand_types = [
            (10, "High Card"),
            (25, "Pair"), 
            (40, "Two Pair"),
            (60, "Three of a Kind"),
            (75, "Straight"),
            (85, "Flush"),
            (95, "Full House"),
            (98, "Four of a Kind"),
            (99, "Straight Flush"),
            (100, "Royal Flush")
        ]
        
        # Get random strength, but bias towards lower hands
        rand_val = random.randint(1, 100)
        
        for threshold, hand_name in hand_types:
            if rand_val <= threshold:
                # Add some card-based variance
                high_card_bonus = max(card.rank.numeric_value for card in all_cards) * 2
                strength = threshold + high_card_bonus + random.randint(-10, 10)
                return max(1, strength), hand_name
        
        return 100, "Royal Flush"
    
    def _full_evaluation(self, all_cards: List[Card]) -> Tuple[int, str]:
        """Full poker hand evaluation (more complex, but accurate)"""
        if len(all_cards) < 5:
            return 1, "Incomplete Hand"
        
        # Get the best 5-card hand from available cards
        best_hand = self._get_best_five_card_hand(all_cards)
        
        # Evaluate the hand
        return self._evaluate_five_card_hand(best_hand)
    
    def _get_best_five_card_hand(self, cards: List[Card]) -> List[Card]:
        """Get the best 5-card hand from available cards"""
        from itertools import combinations
        
        if len(cards) == 5:
            return cards
        
        best_hand = None
        best_strength = 0
        
        # Try all combinations of 5 cards
        for combo in combinations(cards, 5):
            strength, _ = self._evaluate_five_card_hand(list(combo))
            if strength > best_strength:
                best_strength = strength
                best_hand = list(combo)
        
        return best_hand or cards[:5]
    
    def _evaluate_five_card_hand(self, cards: List[Card]) -> Tuple[int, str]:
        """Evaluate a 5-card poker hand"""
        if len(cards) != 5:
            return 1, "Invalid Hand"
        
        # Sort cards by rank value
        sorted_cards = sorted(cards, key=lambda x: x.rank.numeric_value, reverse=True)
        ranks = [card.rank.numeric_value for card in sorted_cards]
        suits = [card.suit for card in sorted_cards]
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight = self._is_straight(ranks)
        
        # Count rank occurrences
        rank_counts = Counter(ranks)
        counts = sorted(rank_counts.values(), reverse=True)
        
        # Determine hand type
        if is_straight and is_flush:
            if ranks == [14, 13, 12, 11, 10]:  # Royal flush
                return 1000, "Royal Flush"
            else:
                return 900 + max(ranks), "Straight Flush"
        
        if counts == [4, 1]:  # Four of a kind
            four_kind = [rank for rank, count in rank_counts.items() if count == 4][0]
            return 800 + four_kind, "Four of a Kind"
        
        if counts == [3, 2]:  # Full house
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            return 700 + three_kind, "Full House"
        
        if is_flush:
            return 600 + max(ranks), "Flush"
        
        if is_straight:
            return 500 + max(ranks), "Straight"
        
        if counts == [3, 1, 1]:  # Three of a kind
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            kicker_score = kickers[0] * 10 + kickers[1] * 1
            return 400 + three_kind * 100 + kicker_score, "Three of a Kind"
        
        if counts == [2, 2, 1]:  # Two pair
            pairs = sorted([rank for rank, count in rank_counts.items() if count == 2], reverse=True)
            kicker = [rank for rank, count in rank_counts.items() if count == 1][0]
            return 300 + pairs[0] * 100 + pairs[1] * 10 + kicker, "Two Pair"
        
        if counts == [2, 1, 1, 1]:  # One pair
            pair = [rank for rank, count in rank_counts.items() if count == 2][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            # Score: 200 + pair*100 + kicker1*10 + kicker2*1 + kicker3*0.1
            kicker_score = kickers[0] * 10 + kickers[1] * 1 + kickers[2] * 0.1
            return 200 + pair * 100 + kicker_score, "Pair"
        
        # High card
        # Sort all ranks in descending order for kicker comparison
        sorted_ranks = sorted(ranks, reverse=True)
        # Use much smaller multipliers to keep high card scores below pair scores
        high_card_score = (sorted_ranks[0] * 10 + sorted_ranks[1] * 1 + 
                          sorted_ranks[2] * 0.1 + sorted_ranks[3] * 0.01 + sorted_ranks[4] * 0.001)
        return 100 + high_card_score, "High Card"
    
    def _is_straight(self, ranks: List[int]) -> bool:
        """Check if ranks form a straight"""
        unique_ranks = sorted(set(ranks))
        
        if len(unique_ranks) != 5:
            return False
        
        # Check for regular straight
        if unique_ranks[-1] - unique_ranks[0] == 4:
            return True
        
        # Check for A-2-3-4-5 straight (wheel)
        if unique_ranks == [2, 3, 4, 5, 14]:
            return True
        
        return False
    
    def get_hand_name(self, all_cards: List[Card]) -> str:
        """Get human-readable hand name from cards"""
        if not all_cards or len(all_cards) < 5:
            return "High Card"
        
        if self.simplified:
            _, hand_name = self._simplified_evaluation(all_cards)
        else:
            _, hand_name = self._full_evaluation(all_cards)
        
        return hand_name
    
    def evaluate_hand(self, all_cards: List[Card]) -> int:
        """Evaluate hand and return numeric score"""
        if not all_cards or len(all_cards) < 5:
            return 1
        
        if self.simplified:
            score, _ = self._simplified_evaluation(all_cards)
        else:
            score, _ = self._full_evaluation(all_cards)
        
        return score

    def compare_hands(self, player1: Player, player2: Player, community_cards: List[Card]) -> int:
        """
        Compare two hands and return the winner
        
        Returns:
            1 if player1 wins, -1 if player2 wins, 0 if tie
        """
        strength1, _ = self.evaluate_hand(player1, community_cards)
        strength2, _ = self.evaluate_hand(player2, community_cards)
        
        if strength1 > strength2:
            return 1
        elif strength2 > strength1:
            return -1
        else:
            return 0 