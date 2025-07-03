"""
Tournament Manager for Poker Fight 05
Handles tournament structure, blind levels, and progression
"""

import os
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from colorama import Fore, Style

@dataclass
class TournamentPhase:
    """Tournament phase configuration"""
    name: str
    hand_range: Tuple[int, int]  # (start_hand, end_hand)
    small_blind: int
    big_blind: int
    description: str

class TournamentManager:
    """Manages tournament structure and progression"""
    
    def __init__(self, tournament_file: str = "tournament_state.json"):
        self.tournament_file = tournament_file
        
        # Tournament Structure as specified
        self.phases = {
            "early": TournamentPhase(
                name="Early Phase",
                hand_range=(1, 10),
                small_blind=5,
                big_blind=10,
                description="🟢 EARLY PHASE (Hands 1-10): Blinds $5/$10"
            ),
            "mid": TournamentPhase(
                name="Mid Phase", 
                hand_range=(11, 30),
                small_blind=20,
                big_blind=40,
                description="🟡 MID PHASE (Hands 11-30): Blinds $20/$40"
            ),
            "late": TournamentPhase(
                name="Late Phase",
                hand_range=(31, 50),
                small_blind=50,
                big_blind=100,
                description="🔴 LATE PHASE (Hands 31-50): Blinds $50/$100"
            )
        }
        
        # Default tournament state
        self.default_state = {
            "tournament_id": None,
            "current_hand": 1,
            "current_phase": "early",
            "dealer_position": 0,
            "players": {},
            "tournament_started": False,
            "tournament_completed": False,
            "winner": None,
            "created_at": None,
            "last_updated": None
        }
    
    def get_phase_for_hand(self, hand_number: int) -> TournamentPhase:
        """Get the tournament phase for a given hand number"""
        for phase in self.phases.values():
            start, end = phase.hand_range
            if start <= hand_number <= end:
                return phase
        
        # After hand 50, use late phase blinds
        return self.phases["late"]
    
    def get_current_blinds(self, hand_number: int) -> Tuple[int, int]:
        """Get current small and big blind amounts"""
        phase = self.get_phase_for_hand(hand_number)
        return phase.small_blind, phase.big_blind
    
    def get_phase_info(self, hand_number: int) -> Dict:
        """Get comprehensive phase information"""
        phase = self.get_phase_for_hand(hand_number)
        
        return {
            "phase_name": phase.name,
            "phase_key": self._get_phase_key(hand_number),
            "small_blind": phase.small_blind,
            "big_blind": phase.big_blind,
            "description": phase.description,
            "hand_range": phase.hand_range,
            "hands_remaining_in_phase": max(0, phase.hand_range[1] - hand_number + 1)
        }
    
    def _get_phase_key(self, hand_number: int) -> str:
        """Get phase key (early/mid/late) for hand number"""
        for key, phase in self.phases.items():
            start, end = phase.hand_range
            if start <= hand_number <= end:
                return key
        return "late"  # Default for hands beyond 50
    
    def load_tournament_state(self) -> Dict:
        """Load tournament state from file"""
        if not os.path.exists(self.tournament_file):
            return self.default_state.copy()
        
        try:
            with open(self.tournament_file, 'r') as f:
                state = json.load(f)
            return state
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading tournament state: {e}")
            return self.default_state.copy()
    
    def save_tournament_state(self, state: Dict):
        """Save tournament state to file"""
        state["last_updated"] = datetime.now().isoformat()
        
        try:
            with open(self.tournament_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving tournament state: {e}")
    
    def create_new_tournament(self, player_configs: List[Dict]) -> Dict:
        """Create a new tournament with given player configurations"""
        tournament_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        state = self.default_state.copy()
        state.update({
            "tournament_id": tournament_id,
            "players": {
                config["name"]: {
                    "chips": config.get("starting_chips", 1500),
                    "eliminated": False,
                    "model": config["model"]
                }
                for config in player_configs
            },
            "tournament_started": True,
            "created_at": datetime.now().isoformat()
        })
        
        self.save_tournament_state(state)
        return state
    
    def advance_hand(self, state: Dict) -> Dict:
        """Advance to next hand and update tournament state"""
        new_state = state.copy()
        new_state["current_hand"] += 1
        new_state["current_phase"] = self._get_phase_key(new_state["current_hand"])
        
        # Rotate dealer
        active_players = [name for name, data in state["players"].items() 
                         if not data["eliminated"]]
        if active_players:
            new_state["dealer_position"] = (state["dealer_position"] + 1) % len(active_players)
        
        self.save_tournament_state(new_state)
        return new_state
    
    def update_player_chips(self, state: Dict, player_chips: Dict[str, int]) -> Dict:
        """Update player chip counts and check for eliminations"""
        new_state = state.copy()
        
        for player_name, chips in player_chips.items():
            if player_name in new_state["players"]:
                new_state["players"][player_name]["chips"] = chips
                new_state["players"][player_name]["eliminated"] = chips <= 0
        
        # Check for tournament completion
        active_players = [name for name, data in new_state["players"].items() 
                         if not data["eliminated"]]
        
        if len(active_players) == 1:
            new_state["tournament_completed"] = True
            new_state["winner"] = active_players[0]
        elif len(active_players) == 0:
            new_state["tournament_completed"] = True
            new_state["winner"] = "No Winner"
        
        self.save_tournament_state(new_state)
        return new_state
    
    def is_tournament_complete(self, state: Dict) -> bool:
        """Check if tournament is complete"""
        active_players = [name for name, data in state["players"].items() 
                         if not data["eliminated"]]
        return len(active_players) <= 1
    
    def get_standings(self, state: Dict) -> List[Tuple[str, int, bool]]:
        """Get current tournament standings (name, chips, eliminated)"""
        standings = []
        for name, data in state["players"].items():
            standings.append((name, data["chips"], data["eliminated"]))
        
        # Sort by chips (eliminated players at bottom)
        standings.sort(key=lambda x: (x[2], -x[1]))  # Sort by eliminated, then by chips desc
        return standings
    
    def display_tournament_info(self, state: Dict):
        """Display current tournament information"""
        hand_number = state["current_hand"]
        phase_info = self.get_phase_info(hand_number)
        
        print(f"\n{Fore.CYAN}🏆 TOURNAMENT STATUS")
        print(f"{'='*60}")
        print(f"🎯 Current Hand: {hand_number}")
        print(f"📊 {phase_info['description']}")
        
        if phase_info['hands_remaining_in_phase'] > 0:
            print(f"⏳ Hands remaining in phase: {phase_info['hands_remaining_in_phase']}")
        
        # Show standings
        standings = self.get_standings(state)
        print(f"\n💰 Current Standings:")
        for i, (name, chips, eliminated) in enumerate(standings, 1):
            status = "❌ ELIMINATED" if eliminated else "✅ Active"
            profit_loss = chips - 1500  # Assuming 1500 starting chips
            pl_color = Fore.GREEN if profit_loss >= 0 else Fore.RED
            pl_sign = "+" if profit_loss >= 0 else ""
            
            print(f"   {i}. {name}: ${chips:,} ({pl_color}{pl_sign}{profit_loss}{Fore.RESET}) - {status}")
    
    def reset_tournament(self):
        """Reset tournament state"""
        if os.path.exists(self.tournament_file):
            try:
                os.remove(self.tournament_file)
                print(f"{Fore.GREEN}✅ Tournament state reset")
            except Exception as e:
                print(f"{Fore.RED}❌ Error resetting tournament: {e}")
        else:
            print(f"{Fore.YELLOW}⚠️ No tournament state to reset")
    
    def set_environment_variables(self, hand_number: int):
        """Set environment variables for current hand/phase"""
        small_blind, big_blind = self.get_current_blinds(hand_number)
        phase_info = self.get_phase_info(hand_number)
        
        os.environ['POKER_SMALL_BLIND'] = str(small_blind)
        os.environ['POKER_BIG_BLIND'] = str(big_blind)
        os.environ['POKER_HAND_NUMBER'] = str(hand_number)
        os.environ['POKER_PHASE'] = phase_info['phase_key'] 