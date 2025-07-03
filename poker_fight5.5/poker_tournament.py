#!/usr/bin/env python3
"""
Main Poker Tournament Runner
Orchestrates the entire tournament with proper 3-phase structure
"""

import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional
from colorama import init, Fore, Style

from tournament_manager import TournamentManager
from tournament_config import PLAYER_CONFIGS, TOURNAMENT_CONFIG
from core.models import Player
from engine.poker_engine import PokerEngine
from services.keywords_ai import KeywordsAI
from services.csv_logger import CSVLogger

# Initialize colorama
init()

class PokerTournament:
    """Main tournament orchestrator"""
    
    def __init__(self):
        self.tournament_manager = TournamentManager()
        self.keywords_ai = KeywordsAI()
        self.tournament_state = None
        self.csv_logger = None
        self.poker_engine = None
        
    def initialize_tournament(self, reset: bool = False) -> bool:
        """Initialize or load tournament state"""
        if reset:
            self.reset_tournament()
            
        # Load or create tournament state
        self.tournament_state = self.tournament_manager.load_tournament_state()
        
        if not self.tournament_state.get("tournament_started", False):
            print(f"{Fore.YELLOW}🆕 Creating new tournament...")
            self.tournament_state = self.tournament_manager.create_new_tournament(PLAYER_CONFIGS)
            
        # Initialize CSV logger
        csv_filename = f"poker_tournament_{self.tournament_state['tournament_id']}.csv"
        self.csv_logger = CSVLogger(csv_filename)
        
        # Create players from state
        self.players = self._create_players_from_state()
        
        # Initialize poker engine
        self.poker_engine = PokerEngine(self.keywords_ai)
        self.poker_engine.players = self.players
        
        return True
    
    def _create_players_from_state(self) -> List[Player]:
        """Create Player objects from tournament state"""
        players = []
        for player_name, player_data in self.tournament_state["players"].items():
            if not player_data["eliminated"]:
                # Find matching config
                config = next((c for c in PLAYER_CONFIGS if c["name"] == player_name), None)
                if config:
                    player = Player(
                        name=player_name,
                        model=config["model"],
                        chips=player_data["chips"],
                        personality=config["personality"]
                    )
                    players.append(player)
        return players
    
    def run_tournament(self, max_hands: Optional[int] = None) -> bool:
        """Run the complete tournament"""
        if not self.tournament_state:
            print(f"{Fore.RED}❌ Tournament not initialized")
            return False
            
        print(f"{Fore.CYAN}🏆 STARTING POKER TOURNAMENT")
        print(f"{'='*80}")
        
        hands_played = 0
        max_hands = max_hands or TOURNAMENT_CONFIG["total_hands"]
        
        while (self.tournament_state["current_hand"] <= max_hands and 
               not self.tournament_manager.is_tournament_complete(self.tournament_state)):
            
            current_hand = self.tournament_state["current_hand"]
            
            # Display tournament info
            self.tournament_manager.display_tournament_info(self.tournament_state)
            
            # Set environment variables for current phase
            self.tournament_manager.set_environment_variables(current_hand)
            
            # Check if entering new phase
            phase_info = self.tournament_manager.get_phase_info(current_hand)
            if current_hand in [1, 11, 31]:
                print(f"\n{Fore.MAGENTA}🚀 ENTERING {phase_info['phase_name'].upper()}")
                print(f"{phase_info['description']}")
                print(f"{'='*80}")
            
            # Play hand
            if self._play_hand(current_hand):
                hands_played += 1
                
                # Update tournament state with chip counts
                player_chips = {p.name: p.chips for p in self.players}
                self.tournament_state = self.tournament_manager.update_player_chips(
                    self.tournament_state, player_chips
                )
                
                # Refresh players list to exclude eliminated players
                self.players = self._create_players_from_state()
                self.poker_engine.players = self.players
                
                # Advance to next hand ONLY if tournament continues
                if not self.tournament_manager.is_tournament_complete(self.tournament_state):
                    self.tournament_state = self.tournament_manager.advance_hand(self.tournament_state)
            else:
                print(f"{Fore.RED}❌ Hand {current_hand} failed")
                break
                
        # Tournament completed
        self._display_final_results()
        return True
    
    def _play_hand(self, hand_number: int) -> bool:
        """Play a single hand"""
        try:
            print(f"\n{Fore.GREEN}🃏 HAND {hand_number}")
            
            # Get current phase info for blind levels
            phase_info = self.tournament_manager.get_phase_info(hand_number)
            small_blind = phase_info["small_blind"]
            big_blind = phase_info["big_blind"]
            
            # Update engine blinds
            self.poker_engine.small_blind = small_blind
            self.poker_engine.big_blind = big_blind
            self.poker_engine.hand_number = hand_number
            
            # Set CSV logger in engine
            self.poker_engine.csv_logger = self.csv_logger
            
            # Log hand start
            self.csv_logger.log_hand_start(hand_number, self.players)
            
            # Play the hand
            success = self.poker_engine.play_hand()
            
            if success:
                # Get the actual winners from the poker engine
                winners = getattr(self.poker_engine, 'hand_winners', [])
                
                # Create hand descriptions
                hand_descriptions = {}
                for player in self.players:
                    if player.is_folded:
                        hand_descriptions[player.name] = "FOLDED"
                    else:
                        # Get hand description from hand evaluator
                        hand_cards = player.hole_cards + self.poker_engine.community_cards
                        hand_name = self.poker_engine.hand_evaluator.get_hand_name(hand_cards)
                        hand_descriptions[player.name] = hand_name
                
                # Log hand end with details
                self.csv_logger.log_hand_end(
                    self.players, winners, self.poker_engine.pot,
                    self.poker_engine.community_cards, hand_descriptions
                )
                
                print(f"{Fore.GREEN}✅ Hand {hand_number} completed")
                
                # Display current standings
                self._display_current_standings()
                
            return success
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error in hand {hand_number}: {e}")
            return False
    
    def _display_current_standings(self):
        """Display current chip standings"""
        standings = sorted(self.players, key=lambda p: p.chips, reverse=True)
        
        print(f"\n{Fore.YELLOW}💰 CURRENT STANDINGS:")
        for i, player in enumerate(standings, 1):
            profit_loss = player.chips - 1500
            pl_color = Fore.GREEN if profit_loss >= 0 else Fore.RED
            pl_sign = "+" if profit_loss >= 0 else ""
            status = "❌ ELIMINATED" if player.chips == 0 else "✅ Active"
            
            print(f"   {i}. {player.name}: ${player.chips:,} ({pl_color}{pl_sign}{profit_loss}{Fore.RESET}) - {status}")
    
    def _display_final_results(self):
        """Display final tournament results"""
        print(f"\n{Fore.MAGENTA}🏆 TOURNAMENT COMPLETE!")
        print(f"{'='*80}")
        
        standings = self.tournament_manager.get_standings(self.tournament_state)
        
        if self.tournament_state.get("winner"):
            print(f"{Fore.YELLOW}🥇 TOURNAMENT WINNER: {self.tournament_state['winner']}")
        
        print(f"\n{Fore.CYAN}📊 FINAL STANDINGS:")
        for i, (name, chips, eliminated) in enumerate(standings, 1):
            profit_loss = chips - 1500
            pl_color = Fore.GREEN if profit_loss >= 0 else Fore.RED
            pl_sign = "+" if profit_loss >= 0 else ""
            
            if i == 1 and not eliminated:
                print(f"   🥇 {name}: ${chips:,} ({pl_color}{pl_sign}{profit_loss}{Fore.RESET})")
            elif i == 2 and not eliminated:
                print(f"   🥈 {name}: ${chips:,} ({pl_color}{pl_sign}{profit_loss}{Fore.RESET})")
            elif i == 3 and not eliminated:
                print(f"   🥉 {name}: ${chips:,} ({pl_color}{pl_sign}{profit_loss}{Fore.RESET})")
            else:
                status = "ELIMINATED" if eliminated else "Active"
                print(f"   {i}. {name}: ${chips:,} ({pl_color}{pl_sign}{profit_loss}{Fore.RESET}) - {status}")
        
        # Log tournament end
        self.csv_logger.log_tournament_end(self.players)
        
        csv_file = f"poker_tournament_{self.tournament_state['tournament_id']}.csv"
        print(f"\n{Fore.GREEN}📊 Full game data saved to: {csv_file}")
        print(f"{Fore.GREEN}💾 Tournament state: {self.tournament_manager.tournament_file}")
    
    def run_single_hand(self) -> bool:
        """Run just one hand (for step-by-step play)"""
        if not self.tournament_state:
            print(f"{Fore.RED}❌ Tournament not initialized")
            return False
            
        current_hand = self.tournament_state["current_hand"]
        
        if self.tournament_manager.is_tournament_complete(self.tournament_state):
            print(f"{Fore.YELLOW}🏁 Tournament already complete!")
            self._display_final_results()
            return False
            
        # Display info and play hand
        self.tournament_manager.display_tournament_info(self.tournament_state)
        
        success = self._play_hand(current_hand)
        
        if success:
            # Update state with chip counts
            player_chips = {p.name: p.chips for p in self.players}
            self.tournament_state = self.tournament_manager.update_player_chips(
                self.tournament_state, player_chips
            )
            
            # Refresh players list to exclude eliminated players
            self.players = self._create_players_from_state()
            self.poker_engine.players = self.players
            
            # Check if tournament is complete BEFORE advancing
            if not self.tournament_manager.is_tournament_complete(self.tournament_state):
                self.tournament_state = self.tournament_manager.advance_hand(self.tournament_state)
                print(f"\n{Fore.CYAN}➡️  Run again to play Hand {self.tournament_state['current_hand']}")
            else:
                self._display_final_results()
                
        return success
    
    def reset_tournament(self):
        """Reset tournament completely"""
        print(f"{Fore.YELLOW}🔄 RESETTING TOURNAMENT...")
        
        # Reset tournament manager
        self.tournament_manager.reset_tournament()
        
        # Remove CSV files
        import glob
        csv_files = glob.glob("poker_tournament_*.csv")
        for csv_file in csv_files:
            try:
                os.remove(csv_file)
                print(f"{Fore.GREEN}✅ Removed: {csv_file}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Could not remove {csv_file}: {e}")
        
        print(f"{Fore.GREEN}✅ Tournament reset complete!")
        print(f"{Fore.CYAN}🎯 Ready for new tournament")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Poker Tournament with 3-Phase Structure')
    parser.add_argument('--reset', action='store_true', help='Reset tournament before starting')
    parser.add_argument('--single', action='store_true', help='Play only one hand')
    parser.add_argument('--hands', type=int, help='Maximum number of hands to play')
    parser.add_argument('--reset-only', action='store_true', help='Only reset tournament, don\'t play')
    
    args = parser.parse_args()
    
    try:
        tournament = PokerTournament()
        
        if args.reset_only:
            tournament.reset_tournament()
            return
            
        if not tournament.initialize_tournament(reset=args.reset):
            print(f"{Fore.RED}❌ Failed to initialize tournament")
            return
            
        if args.single:
            tournament.run_single_hand()
        else:
            tournament.run_tournament(max_hands=args.hands)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⏸️  Tournament interrupted by user")
    except Exception as e:
        print(f"\n{Fore.RED}💥 Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main() 