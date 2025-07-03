#!/usr/bin/env python3
"""
Tournament Reset Script
Completely resets the tournament and shows the new structure
"""

import os
import glob
from colorama import init, Fore, Style

from tournament_manager import TournamentManager
from tournament_config import PLAYER_CONFIGS, TOURNAMENT_CONFIG

# Initialize colorama
init()

def reset_tournament():
    """Complete tournament reset with new structure information"""
    
    print(f"\n{Fore.RED}🔄 COMPLETE TOURNAMENT RESET")
    print("="*80)
    
    files_removed = []
    
    # Reset tournament manager
    tournament_manager = TournamentManager()
    
    # Remove tournament state
    if os.path.exists(tournament_manager.tournament_file):
        os.remove(tournament_manager.tournament_file)
        files_removed.append(tournament_manager.tournament_file)
        print(f"{Fore.GREEN}✅ Removed: {tournament_manager.tournament_file}")
    
    # Remove old state files
    old_state_files = ["poker_game_state.json", "game_state.json"]
    for state_file in old_state_files:
        if os.path.exists(state_file):
            os.remove(state_file)
            files_removed.append(state_file)
            print(f"{Fore.GREEN}✅ Removed: {state_file}")
    
    # Remove ALL CSV files
    csv_patterns = ["poker_*.csv", "tournament_*.csv", "*tournament*.csv"]
    for pattern in csv_patterns:
        csv_files = glob.glob(pattern)
        for csv_file in csv_files:
            try:
                os.remove(csv_file)
                files_removed.append(csv_file)
                print(f"{Fore.GREEN}✅ Removed: {csv_file}")
            except PermissionError:
                print(f"{Fore.YELLOW}⚠️  Could not remove {csv_file} (file may be open)")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Error removing {csv_file}: {e}")
    
    # Remove log files
    log_files = glob.glob("run_log_*.txt") + glob.glob("*.log")
    for log_file in log_files:
        try:
            os.remove(log_file)
            files_removed.append(log_file)
            print(f"{Fore.GREEN}✅ Removed: {log_file}")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Error removing {log_file}: {e}")
    
    # Remove backup files
    backup_files = glob.glob("*.bak") + glob.glob("*.backup")
    for backup_file in backup_files:
        try:
            os.remove(backup_file)
            files_removed.append(backup_file)
            print(f"{Fore.GREEN}✅ Removed: {backup_file}")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Error removing {backup_file}: {e}")
    
    print(f"\n{Fore.CYAN}🎊 RESET COMPLETE!")
    if files_removed:
        print(f"Removed {len(files_removed)} files total")
    else:
        print(f"No files found to remove - already clean!")
    
    # Show new tournament configuration
    print(f"\n{Fore.YELLOW}🏆 TOURNAMENT CONFIGURATION:")
    print(f"📊 Total Hands: {TOURNAMENT_CONFIG['total_hands']}")
    print(f"💰 Starting Chips: ${TOURNAMENT_CONFIG['starting_chips']:,}")
    
    print(f"\n{Fore.MAGENTA}🎯 TOURNAMENT PHASES:")
    for phase_key, phase_config in TOURNAMENT_CONFIG["phases"].items():
        hand_range = phase_config["hand_range"]
        blinds = f"${phase_config['small_blind']}/${phase_config['big_blind']}"
        print(f"   {phase_config['description']}")
        print(f"      📈 Blinds: {blinds}")
        print(f"      🎲 Hands: {hand_range[0]}-{hand_range[1]}")
        print()
    
    print(f"{Fore.CYAN}🤖 PLAYERS:")
    for i, player in enumerate(PLAYER_CONFIGS, 1):
        print(f"   {i}. {Fore.WHITE}{player['name']}{Style.RESET_ALL}")
        print(f"      🧠 Model: {player['model']}")
        print(f"      💰 Starting: ${player['starting_chips']:,}")
        print(f"      🎭 Style: {Fore.CYAN}{player['personality']}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}🎯 READY FOR NEW TOURNAMENT!")
    print(f"\n{Fore.YELLOW}📋 USAGE:")
    print(f"   {Fore.WHITE}python poker_tournament.py{Style.RESET_ALL}          # Run full tournament")
    print(f"   {Fore.WHITE}python poker_tournament.py --single{Style.RESET_ALL} # Play one hand at a time")
    print(f"   {Fore.WHITE}python poker_tournament.py --reset{Style.RESET_ALL}  # Reset and start new")
    print(f"   {Fore.WHITE}python poker_tournament.py --hands 20{Style.RESET_ALL} # Limit to 20 hands")
    
    print(f"\n{Fore.CYAN}📁 NEW STRUCTURE:")
    print(f"   {Fore.WHITE}core/{Style.RESET_ALL}          # Game models, deck, hand evaluation")
    print(f"   {Fore.WHITE}engine/{Style.RESET_ALL}        # Poker game engine")
    print(f"   {Fore.WHITE}services/{Style.RESET_ALL}      # External services (Keywords AI, CSV logging)")
    print(f"   {Fore.WHITE}tournament_manager.py{Style.RESET_ALL}   # Tournament structure and progression")
    print(f"   {Fore.WHITE}tournament_config.py{Style.RESET_ALL}    # Configuration settings")
    print(f"   {Fore.WHITE}poker_tournament.py{Style.RESET_ALL}     # Main tournament runner")

def main():
    """Main function"""
    try:
        reset_tournament()
    except Exception as e:
        print(f"\n{Fore.RED}💥 Error during reset: {e}")
        raise

if __name__ == "__main__":
    main() 