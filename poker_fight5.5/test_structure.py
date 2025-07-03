#!/usr/bin/env python3
"""
Quick test script to verify the reorganized structure works correctly
"""

import sys
import os
from colorama import init, Fore, Style

# Initialize colorama
init()

def test_imports():
    """Test that all modules can be imported correctly"""
    print(f"{Fore.CYAN}🧪 Testing Module Imports...")
    
    try:
        # Test core imports
        print(f"{Fore.YELLOW}   Testing core modules...")
        from core.models import Player, Card, Suit, Rank, Action, GameState
        from core.deck import Deck
        from core.hand_evaluator import HandEvaluator
        print(f"{Fore.GREEN}   ✅ Core modules imported successfully")
        
        # Test services imports
        print(f"{Fore.YELLOW}   Testing services...")
        from services.keywords_ai import KeywordsAI
        from services.csv_logger import CSVLogger
        print(f"{Fore.GREEN}   ✅ Services imported successfully")
        
        # Test engine imports
        print(f"{Fore.YELLOW}   Testing engine...")
        from engine.poker_engine import PokerEngine
        print(f"{Fore.GREEN}   ✅ Engine imported successfully")
        
        # Test tournament components
        print(f"{Fore.YELLOW}   Testing tournament components...")
        from tournament_manager import TournamentManager
        from tournament_config import PLAYER_CONFIGS, TOURNAMENT_CONFIG
        print(f"{Fore.GREEN}   ✅ Tournament components imported successfully")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}   ❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of key components"""
    print(f"\n{Fore.CYAN}🔧 Testing Basic Functionality...")
    
    try:
        # Test core components
        print(f"{Fore.YELLOW}   Testing deck creation...")
        from core.deck import Deck
        deck = Deck()
        card = deck.deal_one()
        print(f"{Fore.GREEN}   ✅ Dealt card: {card}")
        
        # Test player creation
        print(f"{Fore.YELLOW}   Testing player creation...")
        from core.models import Player
        player = Player(name="Test", model="test-model", chips=1500)
        print(f"{Fore.GREEN}   ✅ Created player: {player.name} with ${player.chips}")
        
        # Test tournament manager
        print(f"{Fore.YELLOW}   Testing tournament manager...")
        from tournament_manager import TournamentManager
        tm = TournamentManager()
        phase_info = tm.get_phase_info(15)  # Mid phase
        print(f"{Fore.GREEN}   ✅ Phase 15: {phase_info['description']}")
        
        # Test configuration
        print(f"{Fore.YELLOW}   Testing configuration...")
        from tournament_config import TOURNAMENT_CONFIG
        print(f"{Fore.GREEN}   ✅ Tournament config loaded: {TOURNAMENT_CONFIG['total_hands']} hands")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}   ❌ Functionality error: {e}")
        return False

def test_tournament_phases():
    """Test tournament phase configuration"""
    print(f"\n{Fore.CYAN}🏆 Testing Tournament Phase Structure...")
    
    try:
        from tournament_manager import TournamentManager
        tm = TournamentManager()
        
        # Test each phase
        test_hands = [5, 15, 35]
        expected_phases = ["early", "mid", "late"]
        expected_blinds = [(5, 10), (20, 40), (50, 100)]
        
        for i, hand_num in enumerate(test_hands):
            phase_info = tm.get_phase_info(hand_num)
            small_blind, big_blind = tm.get_current_blinds(hand_num)
            
            print(f"{Fore.YELLOW}   Hand {hand_num}: {phase_info['description']}")
            print(f"      Blinds: ${small_blind}/${big_blind}")
            
            # Verify phase key and blinds
            assert phase_info['phase_key'] == expected_phases[i], f"Wrong phase for hand {hand_num}"
            assert (small_blind, big_blind) == expected_blinds[i], f"Wrong blinds for hand {hand_num}"
            
        print(f"{Fore.GREEN}   ✅ All tournament phases configured correctly")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}   ❌ Tournament phase error: {e}")
        return False

def main():
    """Run all tests"""
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}🔬 POKER FIGHT 05 - STRUCTURE TEST")
    print(f"{'='*60}")
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_basic_functionality()
    all_passed &= test_tournament_phases()
    
    # Final result
    print(f"\n{Fore.MAGENTA}{'='*60}")
    if all_passed:
        print(f"{Fore.GREEN}🎉 ALL TESTS PASSED!")
        print(f"{Fore.CYAN}✅ The reorganized structure is working correctly")
        print(f"\n{Fore.YELLOW}📋 Ready to run:")
        print(f"   {Fore.WHITE}python poker_tournament.py{Style.RESET_ALL}          # Full tournament")
        print(f"   {Fore.WHITE}python poker_tournament.py --single{Style.RESET_ALL} # Single hand mode")
        print(f"   {Fore.WHITE}python reset_tournament.py{Style.RESET_ALL}          # Reset tournament")
    else:
        print(f"{Fore.RED}❌ SOME TESTS FAILED")
        print(f"{Fore.YELLOW}⚠️  Check the errors above and fix any import issues")
    
    print(f"{Fore.MAGENTA}{'='*60}")

if __name__ == "__main__":
    main() 