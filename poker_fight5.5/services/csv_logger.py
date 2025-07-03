"""
Enhanced CSV Logger for Poker Tournament
Matches the exact original format with detailed action logging
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from colorama import Fore, Style

from core.models import Player, Card


class CSVLogger:
    """Enhanced CSV logger matching original detailed format"""
    
    def __init__(self, csv_file: str = None):
        self.current_hand = 1
        self.current_round = "start"
        
        # Generate filename if not provided
        if csv_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.csv_file = f"poker_tournament_{timestamp}.csv"
        else:
            self.csv_file = csv_file
            
        # Headers matching original format exactly plus full context
        self.headers = [
            "hand", "round", "action", "player", "amount",
            "llm1_chips", "llm2_chips", "llm3_chips", "pot",
            "llm1_cards", "llm2_cards", "llm3_cards",
            "community_1", "community_2", "community_3", "community_4", "community_5",
            "timestamp", "llm_action", "reasoning", "winner", "hand_result", "full_context"
        ]
        
        self.rows = []
        self._write_headers()
        
        print(f"{Fore.GREEN}📊 CSV Logger initialized: {self.csv_file}")

    def _write_headers(self):
        """Write CSV headers"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def _get_player_cards_string(self, player: Player, hidden: bool = False) -> str:
        """Get player cards as string, matching original format"""
        if hidden or not player.hole_cards or len(player.hole_cards) < 2:
            return '"xx, xx"'
        return f'"{player.hole_cards[0].to_excel_format()}, {player.hole_cards[1].to_excel_format()}"'

    def _get_community_cards(self, community_cards: List[Card]) -> List[str]:
        """Get community cards as list of strings"""
        cards = [""] * 5
        for i, card in enumerate(community_cards[:5]):
            cards[i] = card.to_excel_format()
        return cards

    def _clean_llm_response(self, response: str) -> str:
        """Clean LLM response for CSV storage"""
        if not response:
            return ""
        # Remove excessive whitespace and normalize
        cleaned = " ".join(response.strip().split())
        # Remove quotes to avoid CSV issues
        cleaned = cleaned.replace('"', "'").replace('\n', ' ').replace('\r', '')
        return cleaned[:500]  # Truncate if too long

    def _get_timestamp(self) -> str:
        """Get current timestamp in HH:MM:SS format"""
        return datetime.now().strftime("%H:%M:%S")

    def _add_row(self, action: str, player: str = "", amount: int = 0,
                 players: List[Player] = None, pot: int = 0,
                 community_cards: List[Card] = None, llm_action: str = "",
                 reasoning: str = "", winner: str = "", hand_result: str = "",
                 full_context: str = ""):
        """Add a row to the CSV with all details"""
        
        # Get player chips and cards
        if players and len(players) >= 3:
            llm1_chips = players[0].chips
            llm2_chips = players[1].chips
            llm3_chips = players[2].chips
            llm1_cards = self._get_player_cards_string(players[0])
            llm2_cards = self._get_player_cards_string(players[1])
            llm3_cards = self._get_player_cards_string(players[2])
        else:
            llm1_chips = llm2_chips = llm3_chips = 0
            llm1_cards = llm2_cards = llm3_cards = '"xx, xx"'

        # Get community cards
        if community_cards:
            community = self._get_community_cards(community_cards)
        else:
            community = [""] * 5

        # Clean reasoning and context
        clean_reasoning = self._clean_llm_response(reasoning)
        clean_context = self._clean_llm_response(full_context)

        # Create row
        row = [
            self.current_hand,
            self.current_round,
            action,
            player,
            amount,
            llm1_chips,
            llm2_chips, 
            llm3_chips,
            pot,
            llm1_cards,
            llm2_cards,
            llm3_cards,
            community[0],
            community[1],
            community[2],
            community[3],
            community[4],
            self._get_timestamp(),
            llm_action,
            clean_reasoning,
            winner,
            hand_result,
            clean_context
        ]

        self.rows.append(row)
        self._save_row(row)

    def _save_row(self, row):
        """Save single row to CSV file"""
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def log_hand_start(self, hand_number: int, players: List[Player]):
        """Log hand start with initial state"""
        self.current_hand = hand_number
        self.current_round = "start"
        
        # Reset cards to hidden for start
        for player in players:
            player.hole_cards = []
        
        self._add_row(
            action="HAND_START",
            players=players,
            pot=0
        )
        
        print(f"\n{Fore.GREEN}🃏 HAND {hand_number} START")
        for i, player in enumerate(players, 1):
            print(f"LLM{i} ({player.name}): ${player.chips}")

    def log_small_blind(self, players: List[Player], sb_player: str, sb_amount: int, pot: int):
        """Log small blind posting with correct chip state"""
        self._add_row(
            action="SMALL_BLIND",
            player=sb_player,
            amount=sb_amount,
            players=players,
            pot=pot
        )
        
        print(f"{Fore.YELLOW}💰 {sb_player} posts small blind: ${sb_amount}")

    def log_big_blind(self, players: List[Player], bb_player: str, bb_amount: int, pot: int):
        """Log big blind posting with correct chip state"""
        self._add_row(
            action="BIG_BLIND",
            player=bb_player,
            amount=bb_amount,
            players=players,
            pot=pot
        )
        
        print(f"{Fore.YELLOW}💰 {bb_player} posts big blind: ${bb_amount}")

    def log_hole_cards(self, players: List[Player], pot: int = 0):
        """Log hole cards dealt with actual cards revealed"""
        self._add_row(
            action="DEAL_HOLE_CARDS",
            players=players,
            pot=pot
        )
        
        print(f"\n{Fore.CYAN}🎴 HOLE CARDS DEALT")

    def log_community_cards(self, round_name: str, community_cards: List[Card],
                           players: List[Player], pot: int):
        """Log community cards being dealt"""
        action_name = f"DEAL_{round_name.upper()}"
        self.current_round = round_name
        
        self._add_row(
            action=action_name,
            players=players,
            pot=pot,
            community_cards=community_cards
        )
        
        cards_str = ", ".join(str(card) for card in community_cards)
        print(f"\n{Fore.CYAN}🃏 {round_name.upper()}: {cards_str}")

    def log_player_action(self, player: Player, action: str, amount: int,
                         players: List[Player], pot: int, community_cards: List[Card],
                         reasoning: str = "", full_context: str = ""):
        """Log individual player action with reasoning and full context"""
        
        self._add_row(
            action=action.upper(),
            player=player.name,
            amount=amount,
            players=players,
            pot=pot,
            community_cards=community_cards,
            reasoning=reasoning,
            full_context=full_context
        )
        
        # Display action
        if action.upper() == "FOLD":
            print(f"{Fore.RED}❌ {player.name} folds")
        elif action.upper() == "CHECK":
            print(f"{Fore.CYAN}✓ {player.name} checks")
        elif action.upper() == "CALL":
            print(f"{Fore.YELLOW}💰 {player.name} calls ${amount}")
        elif action.upper() == "RAISE":
            print(f"{Fore.GREEN}💰 {player.name} raises to ${amount}")
        elif action.upper() == "BET":
            print(f"{Fore.GREEN}💰 {player.name} bets ${amount}")

    def log_showdown(self, players: List[Player], pot: int, community_cards: List[Card]):
        """Log showdown"""
        self._add_row(
            action="SHOWDOWN",
            players=players,
            pot=pot,
            community_cards=community_cards
        )
        
        print(f"\n{Fore.CYAN}🃏 SHOWDOWN")

    def log_hand_end(self, players: List[Player], winners: List[Player],
                     pot_amount: int, community_cards: List[Card],
                     hand_descriptions: Dict[str, str]):
        """Log hand completion exactly like original"""
        
        winner_names = ", ".join(w.name for w in winners)
        
        # Create hand result string exactly like original
        result_parts = []
        for player in players:
            if player.name in hand_descriptions:
                result_parts.append(f"{player.name}: {hand_descriptions[player.name]}")
            elif any(p.name == player.name and p.is_folded for p in players):
                result_parts.append(f"{player.name}: FOLDED")
        
        result_summary = " | ".join(result_parts)
        
        self._add_row(
            action="HAND_END",
            players=players,
            pot=0,  # Pot is 0 after being awarded
            community_cards=community_cards,
            winner=winner_names,
            hand_result=result_summary
        )
        
        print(f"\n{Fore.GREEN}🏆 HAND RESULTS")
        community_str = ', '.join(str(card) for card in community_cards) if community_cards else ""
        print(f"Community: {community_str}")
        print(f"Winner: {winner_names}")

    def log_tournament_end(self, players: List[Player]):
        """Log tournament completion"""
        standings = sorted(players, key=lambda p: p.chips, reverse=True)
        
        self._add_row(
            action="TOURNAMENT_END",
            players=players,
            winner=standings[0].name,
            hand_result=f"Final Winner: {standings[0].name} with ${standings[0].chips}"
        )
        
        print(f"\n{Fore.GREEN}📊 Tournament complete - data saved to: {self.csv_file}")

    def log_betting_round_start(self, round_name: str):
        """Start a new betting round"""
        self.current_round = round_name
        print(f"\n{Fore.MAGENTA}🎯 {round_name.upper()} BETTING")

    def display_current_table(self, num_recent_rows: int = 10):
        """Display recent rows in a formatted table"""
        if not self.rows:
            print("No data to display yet.")
            return
        
        print(f"\n{Fore.CYAN}📊 RECENT GAME DATA (Last {num_recent_rows} actions):")
        print("-" * 120)
        
        # Show headers
        header_display = f"{'Hand':<4} {'Round':<8} {'Action':<12} {'Player':<8} {'Amt':<6} {'LLM1':<6} {'LLM2':<6} {'LLM3':<6} {'Pot':<6} {'Community':<25}"
        print(header_display)
        print("-" * 120)
        
        # Show recent rows
        recent_rows = self.rows[-num_recent_rows:] if len(self.rows) > num_recent_rows else self.rows
        
        for row in recent_rows:
            hand, round_name, action, player, amount = row[0:5]
            llm1_chips, llm2_chips, llm3_chips, pot = row[5:9]
            community = [row[12], row[13], row[14], row[15], row[16]]
            community_str = ", ".join(c for c in community if c)
            
            row_display = f"{hand:<4} {round_name:<8} {action:<12} {player:<8} {amount:<6} {llm1_chips:<6} {llm2_chips:<6} {llm3_chips:<6} {pot:<6} {community_str:<25}"
            print(row_display)
        
        print("-" * 120) 