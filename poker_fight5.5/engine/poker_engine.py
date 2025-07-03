"""
Poker Engine - Core game logic for Texas Hold'em
Integrated with tournament structure and proper blind management
"""

import re
from typing import List, Tuple, Optional, Callable, Dict, Any
from colorama import Fore, Style, Back

from core.models import Player, Action, Card, GameState
from core.deck import Deck
from core.hand_evaluator import HandEvaluator
from services.keywords_ai import KeywordsAI


class PokerEngine:
    """Core poker game engine with tournament integration"""
    
    def __init__(self, keywords_ai: KeywordsAI):
        self.keywords_ai = keywords_ai
        self.hand_evaluator = HandEvaluator(simplified=False)
        
        # Game state
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.dealer_position = 0
        self.hand_number = 0
        self.action_history = []
        
        # Tournament settings (will be updated by tournament manager)
        self.small_blind = 5
        self.big_blind = 10
        
        # Players will be set externally
        self.players = []
        
        # Callback for logging (set by tournament runner)
        self.log_callback = None
    
    def set_logging_callback(self, callback: Callable):
        """Set callback for logging actions"""
        self.log_callback = callback
    
    def get_game_state(self) -> GameState:
        """Get current game state"""
        return GameState(
            hand_number=self.hand_number,
            pot=self.pot,
            current_bet=self.current_bet,
            community_cards=self.community_cards.copy(),
            players=self.players.copy(),
            dealer_position=self.dealer_position,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            betting_round="unknown",
            action_history=self.action_history.copy()
        )
    
    def reset_for_new_hand(self):
        """Reset game state for a new hand"""
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.action_history = []
        
        for player in self.players:
            player.reset_for_hand()
    
    def post_blinds(self) -> Tuple[str, int, str, int]:
        """Post small and big blinds"""
        active_players = [p for p in self.players if p.chips > 0]
        if len(active_players) < 2:
            return None
        
        # Calculate blind positions
        sb_idx = (self.dealer_position + 1) % len(self.players)
        bb_idx = (self.dealer_position + 2) % len(self.players)
        
        # Ensure we have the right players
        while not self.players[sb_idx].chips > 0:
            sb_idx = (sb_idx + 1) % len(self.players)
        while not self.players[bb_idx].chips > 0:
            bb_idx = (bb_idx + 1) % len(self.players)
        
        sb_player = self.players[sb_idx]
        bb_player = self.players[bb_idx]
        
        # Small blind
        sb_amount = min(self.small_blind, sb_player.chips)
        sb_player.chips -= sb_amount
        sb_player.current_bet = sb_amount
        self.pot += sb_amount
        
        # Log small blind immediately after deduction
        if self.csv_logger:
            self.csv_logger.log_small_blind(self.players, sb_player.name, sb_amount, self.pot)
        
        # Track small blind in action history
        self.action_history.append({
            'round': 'pre-flop',
            'player': sb_player.name,
            'action': 'SMALL_BLIND',
            'amount': sb_amount,
            'reasoning': f'Posted small blind ${sb_amount}'
        })
        
        # Big blind
        bb_amount = min(self.big_blind, bb_player.chips)
        bb_player.chips -= bb_amount
        bb_player.current_bet = bb_amount
        self.pot += bb_amount
        self.current_bet = bb_amount
        
        # Log big blind immediately after deduction
        if self.csv_logger:
            self.csv_logger.log_big_blind(self.players, bb_player.name, bb_amount, self.pot)
        
        # Track big blind in action history
        self.action_history.append({
            'round': 'pre-flop',
            'player': bb_player.name,
            'action': 'BIG_BLIND',
            'amount': bb_amount,
            'reasoning': f'Posted big blind ${bb_amount}'
        })
        
        return (sb_player.name, sb_amount, bb_player.name, bb_amount)
    
    def deal_hole_cards(self):
        """Deal 2 hole cards to each active player"""
        active_players = [p for p in self.players if p.chips > 0]
        
        # Deal 2 cards to each player
        for _ in range(2):
            for player in active_players:
                card = self.deck.deal_one()
                player.hole_cards.append(card)
        
        # Log hole cards to CSV
        if self.csv_logger:
            self.csv_logger.log_hole_cards(self.players, self.pot)
    
    def deal_flop(self):
        """Deal the flop (3 community cards)"""
        self.deck.burn()  # Burn one card
        self.community_cards.extend(self.deck.deal(3))
        
        # Log flop to CSV
        if self.csv_logger:
            self.csv_logger.log_community_cards("flop", self.community_cards, self.players, self.pot)
    
    def deal_turn(self):
        """Deal the turn (1 community card)"""
        self.deck.burn()  # Burn one card
        self.community_cards.append(self.deck.deal_one())
        
        # Log turn to CSV
        if self.csv_logger:
            self.csv_logger.log_community_cards("turn", self.community_cards, self.players, self.pot)
    
    def deal_river(self):
        """Deal the river (1 community card)"""
        self.deck.burn()  # Burn one card
        self.community_cards.append(self.deck.deal_one())
        
        # Log river to CSV
        if self.csv_logger:
            self.csv_logger.log_community_cards("river", self.community_cards, self.players, self.pot)
    
    def create_decision_prompt(self, player: Player, betting_round: str) -> str:
        """Create a decision prompt for a player with tournament context"""
        
        # Determine tournament phase
        if self.hand_number <= 10:
            phase_info = "🟢 EARLY PHASE (Hands 1-10): Blinds $5/$10"
            pressure_level = "🟢 LOW PRESSURE"
        elif self.hand_number <= 30:
            phase_info = "🟡 MID PHASE (Hands 11-30): Blinds $20/$40"
            pressure_level = "🟡 MODERATE PRESSURE"
        else:
            phase_info = "🔴 LATE PHASE (Hands 31-50): Blinds $50/$100"
            pressure_level = "🔴 HIGH PRESSURE"
        
        # Build player information
        all_players_info = []
        for p in self.players:
            status = ""
            if p.is_folded:
                status = "(FOLDED)"
            elif p.is_all_in:
                status = "(ALL-IN)"
            elif p.chips == 0:
                status = "(ELIMINATED)"
                
            player_line = f"- {p.name}: ${p.chips} total (bet: ${p.current_bet} this round) {status}"
            all_players_info.append(player_line)
        
        bet_to_call = max(0, self.current_bet - player.current_bet)
        min_raise = max(self.big_blind, self.current_bet + self.big_blind) if self.current_bet > 0 else self.big_blind
        
        # Define newline for f-string
        newline = '\n'
        
        # Build the prompt
        hole_cards_str = ', '.join(str(card) for card in player.hole_cards)
        community_cards_str = ', '.join(str(card) for card in self.community_cards) if self.community_cards else 'None dealt yet (pre-flop)'
        
        prompt = f"""POKER DECISION REQUIRED
        
TOURNAMENT CONTEXT:
{phase_info}
{pressure_level}
Hand: {self.hand_number}/50

YOUR SITUATION:
- Hand: {hole_cards_str}
- Your chips: ${player.chips}
- Your current bet this round: ${player.current_bet}

GAME STATE:
- Betting round: {betting_round}
- Community cards: {community_cards_str}
- Current pot: ${self.pot}
- Current bet to call: ${bet_to_call}
- Minimum raise: ${min_raise}

ALL PLAYERS:
{newline.join(all_players_info)}

ACTIONS AVAILABLE:
- "fold" - Give up this hand
- "check" - Pass (only if no bet to call)
- "call" - Match the current bet (${bet_to_call})
- "raise X" - Raise by amount X (minimum ${min_raise})

Respond with ONLY your action (e.g., "call", "raise 50", "fold")."""

        return prompt
    
    def build_game_state_for_llm(self, player: Player, round_name: str) -> Dict[str, Any]:
        """Build comprehensive game state for enhanced LLM decision making"""
        # Get player cards
        player_cards = []
        if player.hole_cards and len(player.hole_cards) >= 2:
            player_cards = [card.to_excel_format() for card in player.hole_cards]
        else:
            player_cards = ['xx', 'xx']
        
        # Get community cards
        community_cards = []
        if self.community_cards:
            community_cards = [card.to_excel_format() for card in self.community_cards]
        
        # Get opponents info
        opponents = []
        for p in self.players:
            if p != player:
                opponents.append({
                    'name': p.name,
                    'chips': p.chips,
                    'current_bet': p.current_bet,
                    'folded': p.is_folded
                })
        
        # Get ALL actions in this hand (across all rounds)
        actions_this_hand = []
        for action_record in self.action_history:
            actions_this_hand.append({
                'round': action_record.get('round', ''),
                'player': action_record.get('player', ''),
                'action': action_record.get('action', ''),
                'amount': action_record.get('amount', 0)
            })
        
        # Get actions this round only (for current round context)
        actions_this_round = []
        for action_record in self.action_history:
            if action_record.get('round') == round_name:
                actions_this_round.append({
                    'player': action_record.get('player', ''),
                    'action': action_record.get('action', ''),
                    'amount': action_record.get('amount', 0)
                })
        
        # Calculate amounts
        bet_to_call = max(0, self.current_bet - player.current_bet)
        
        return {
            'hand_number': self.hand_number,
            'total_hands': 50,  # Tournament setting
            'round': round_name,
            'pot': self.pot,
            'current_bet': self.current_bet,
            'to_call': bet_to_call,
            'player_chips': player.chips,
            'player_current_bet': player.current_bet,
            'player_cards': player_cards,
            'community_cards': community_cards,
            'opponents': opponents,
            'actions_this_hand': actions_this_hand,  # ALL actions in this hand
            'actions_this_round': actions_this_round  # Only current round actions
        }

    def parse_enhanced_action(self, action_str: str, player: Player) -> Tuple[Action, int]:
        """Parse enhanced action from LLM JSON response"""
        action_str = action_str.lower().strip()
        
        if action_str == "fold":
            return Action.FOLD, 0
        elif action_str == "check":
            return Action.CHECK, 0
        elif action_str == "call":
            bet_to_call = max(0, self.current_bet - player.current_bet)
            return Action.CALL, bet_to_call
        elif action_str.startswith("raise"):
            # Extract raise amount
            try:
                parts = action_str.split()
                if len(parts) >= 2:
                    raise_amount = int(parts[1])
                    # Return just the raise amount, not total bet
                    return Action.RAISE, raise_amount
                else:
                    # Default raise
                    return Action.RAISE, 20
            except (ValueError, IndexError):
                # Default raise on parse error
                return Action.RAISE, 20
        else:
            # Default to fold on unrecognized action
            return Action.FOLD, 0

    def parse_action(self, decision: str, player: Player) -> Tuple[Action, int, str]:
        """Parse LLM decision into action and amount"""
        decision = decision.strip().lower()
        
        # Extract the actual decision if it's in a code block or has extra formatting
        if '```' in decision:
            lines = decision.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('```'):
                    decision = line
                    break
        
        # Clean up the decision
        decision = re.sub(r'[^\w\s]', ' ', decision).strip()
        
        bet_to_call = max(0, self.current_bet - player.current_bet)
        
        if 'fold' in decision:
            return Action.FOLD, 0, "Folded"
        elif 'check' in decision:
            if bet_to_call > 0:
                # Can't check when there's a bet to call, so call instead
                return Action.CALL, bet_to_call, f"Called ${bet_to_call} (tried to check)"
            return Action.CHECK, 0, "Checked"
        elif 'call' in decision:
            if bet_to_call == 0:
                return Action.CHECK, 0, "Checked (tried to call with no bet)"
            return Action.CALL, bet_to_call, f"Called ${bet_to_call}"
        elif 'raise' in decision or 'bet' in decision:
            # Extract raise amount
            numbers = re.findall(r'\d+', decision)
            if numbers:
                raise_amount = int(numbers[0])
                min_raise = max(self.big_blind, self.current_bet + self.big_blind)
                raise_amount = max(raise_amount, min_raise)
                
                # Check if player has enough chips
                total_needed = bet_to_call + raise_amount
                if total_needed >= player.chips:
                    return Action.ALL_IN, player.chips, f"All-in for ${player.chips}"
                
                return Action.RAISE, raise_amount, f"Raised ${raise_amount}"
            else:
                # Default raise
                min_raise = max(self.big_blind, self.current_bet + self.big_blind)
                if bet_to_call + min_raise >= player.chips:
                    return Action.ALL_IN, player.chips, f"All-in for ${player.chips}"
                return Action.RAISE, min_raise, f"Raised ${min_raise}"
        
        # Default to fold if we can't parse
        return Action.FOLD, 0, "Folded (couldn't parse decision)"
    
    def execute_action(self, player: Player, action: Action, amount: int = 0) -> bool:
        """Execute a player's action"""
        if action == Action.FOLD:
            player.is_folded = True
            print(f"{Fore.RED}❌ {player.name} folds")
            
        elif action == Action.CHECK:
            print(f"{Fore.GREEN}✓ {player.name} checks")
            
        elif action == Action.CALL:
            actual_call = min(amount, player.chips)
            player.chips -= actual_call
            player.current_bet += actual_call
            self.pot += actual_call
            
            if player.chips == 0:
                player.is_all_in = True
                print(f"{Fore.YELLOW}💰 {player.name} calls ${actual_call} and is ALL-IN")
            else:
                print(f"{Fore.GREEN}💰 {player.name} calls ${actual_call}")
                
        elif action == Action.RAISE:
            bet_to_call = max(0, self.current_bet - player.current_bet)
            # amount is the raise amount (additional on top of call)
            total_bet_needed = bet_to_call + amount
            actual_amount = min(total_bet_needed, player.chips)
            
            player.chips -= actual_amount
            player.current_bet += actual_amount
            self.pot += actual_amount
            # Set new current bet to this player's total bet
            self.current_bet = player.current_bet
            
            if player.chips == 0:
                player.is_all_in = True
                print(f"{Fore.YELLOW}💰 {player.name} raises by ${amount} to ${player.current_bet} and is ALL-IN")
            else:
                print(f"{Fore.BLUE}💰 {player.name} raises by ${amount} to ${player.current_bet}")
                
        elif action == Action.ALL_IN:
            all_in_amount = player.chips
            player.chips = 0
            player.current_bet += all_in_amount
            self.pot += all_in_amount
            self.current_bet = max(self.current_bet, player.current_bet)
            player.is_all_in = True
            print(f"{Fore.YELLOW}💰 {player.name} goes ALL-IN for ${all_in_amount}")
        
        return True
    
    def conduct_betting_round(self, round_name: str):
        """Conduct a betting round"""
        # Log betting round start to CSV
        if self.csv_logger:
            self.csv_logger.log_betting_round_start(round_name)
        
        # Reset betting for new round (but NOT for pre-flop since blinds are already posted)
        if round_name != "pre-flop":
            for player in self.players:
                player.current_bet = 0
            self.current_bet = 0
        
        active_players = [p for p in self.players if p.can_act()]
        if len(active_players) <= 1:
            return
        
        # Determine action order
        if round_name == "pre-flop":
            # Pre-flop: start after big blind
            start_idx = (self.dealer_position + 3) % len(self.players)
        else:
            # Post-flop: start after dealer
            start_idx = (self.dealer_position + 1) % len(self.players)
        
        # Betting loop
        last_raiser_idx = None
        current_idx = start_idx
        
        while True:
            player = self.players[current_idx]
            
            if player.can_act():
                bet_to_call = max(0, self.current_bet - player.current_bet)
                
                # Create comprehensive game state for LLM
                game_state = self.build_game_state_for_llm(player, round_name)
                
                try:
                    # Get enhanced decision with full context
                    decision_result = self.keywords_ai.get_poker_decision(
                        player.name, player.model, game_state,
                        customer_id=player.name, group_id=f"hand_{self.hand_number}",
                        personality=player.personality
                    )
                    
                    action, amount = self.parse_enhanced_action(decision_result['action'], player)
                    
                    # Execute action
                    self.execute_action(player, action, amount)
                    
                    # Track action in history for LLM context
                    self.action_history.append({
                        'round': round_name,
                        'player': player.name,
                        'action': action.name,
                        'amount': amount,
                        'reasoning': decision_result['reason']
                    })
                    
                    # Log player action to CSV with full reasoning and context
                    if self.csv_logger:
                        self.csv_logger.log_player_action(
                            player, action.name, amount, 
                            self.players, self.pot, self.community_cards, 
                            decision_result['reason'], decision_result['full_context']
                        )
                    
                    # Track if this was a raise
                    if action == Action.RAISE or action == Action.ALL_IN:
                        last_raiser_idx = current_idx
                    
                except Exception as e:
                    print(f"{Fore.RED}❌ Error getting decision from {player.name}: {e}")
                    # Default to fold
                    player.is_folded = True
                    
                    # Track error fold in history
                    self.action_history.append({
                        'round': round_name,
                        'player': player.name,
                        'action': 'FOLD',
                        'amount': 0,
                        'reasoning': f"Error: {str(e)}"
                    })
                    
                    # Log error fold to CSV
                    if self.csv_logger:
                        self.csv_logger.log_player_action(
                            player, "FOLD", 0, self.players, 
                            self.pot, self.community_cards, 
                            f"Folded due to error: {str(e)}", ""
                        )
            
            # Move to next player
            current_idx = (current_idx + 1) % len(self.players)
            
            # Check if betting round is complete
            active_players = [p for p in self.players if not p.is_folded]
            can_act_players = [p for p in active_players if p.can_act()]
            
            # End round if only one player remains unffolded
            if len(active_players) <= 1:
                break
            
            # End round if no one can act (all folded or all-in)
            if len(can_act_players) == 0:
                break
            
            # Check if all active players have equal bets (betting is complete)
            if len(active_players) >= 2:
                all_bets_equal = True
                first_active_bet = None
                
                for p in active_players:
                    if not p.is_all_in:  # Skip all-in players for bet equality check
                        if first_active_bet is None:
                            first_active_bet = p.current_bet
                        elif p.current_bet != first_active_bet:
                            all_bets_equal = False
                            break
                
                # If all bets are equal and we've had at least one action from each player
                if all_bets_equal:
                    # Check if everyone who can act has had a chance to act
                    players_who_acted = set()
                    for action in self.action_history:
                        if action.get('round') == round_name:
                            players_who_acted.add(action.get('player'))
                    
                    # Check if all non-folded players have acted
                    all_have_acted = True
                    for p in active_players:
                        if p.name not in players_who_acted and p.can_act():
                            all_have_acted = False
                            break
                    
                    if all_have_acted:
                        break
    
    def determine_winners(self) -> List[Player]:
        """Determine hand winners"""
        active_players = [p for p in self.players if not p.is_folded]
        
        if len(active_players) == 1:
            return active_players
        
        # Evaluate hands
        player_scores = []
        for player in active_players:
            hand_cards = player.hole_cards + self.community_cards
            score = self.hand_evaluator.evaluate_hand(hand_cards)
            player_scores.append((player, score))
        
        # Find winners (highest score)
        max_score = max(score for _, score in player_scores)
        winners = [player for player, score in player_scores if score == max_score]
        
        return winners
    
    def award_pot(self, winners: List[Player]):
        """Award pot to winners"""
        if not winners:
            return
            
        pot_share = self.pot // len(winners)
        remainder = self.pot % len(winners)
        
        for i, winner in enumerate(winners):
            share = pot_share + (1 if i < remainder else 0)
            winner.chips += share
            print(f"{Fore.GREEN}💰 {winner.name} wins ${share}")
        
        self.pot = 0
    
    def conduct_showdown(self) -> List[Player]:
        """Conduct showdown and determine winners"""
        active_players = [p for p in self.players if not p.is_folded]
        
        if len(active_players) <= 1:
            return active_players
        
        # Log showdown to CSV
        if self.csv_logger:
            self.csv_logger.log_showdown(self.players, self.pot, self.community_cards)
        
        return self.determine_winners()
    
    def play_hand(self) -> bool:
        """Play one complete hand"""
        # Hand number is set by tournament manager, don't increment here
        # print(f"\n{Fore.GREEN}🃏 HAND {self.hand_number}")  # Removed duplicate print
        
        # Reset for new hand
        self.reset_for_new_hand()
        
        # Check if we have enough players
        active_players = [p for p in self.players if p.chips > 0]
        if len(active_players) < 2:
            print(f"{Fore.RED}❌ Not enough players to continue")
            return False
        
        try:
            # Post blinds
            blind_result = self.post_blinds()
            if not blind_result:
                return False
            
            # Deal hole cards
            self.deal_hole_cards()
            
            # Pre-flop betting
            self.conduct_betting_round("pre-flop")
            
            # Check if hand continues
            active_players = [p for p in self.players if not p.is_folded]
            if len(active_players) > 1:
                # Flop
                self.deal_flop()
                self.conduct_betting_round("flop")
                
                # Turn
                active_players = [p for p in self.players if not p.is_folded]
                if len(active_players) > 1:
                    self.deal_turn()
                    self.conduct_betting_round("turn")
                    
                    # River
                    active_players = [p for p in self.players if not p.is_folded]
                    if len(active_players) > 1:
                        self.deal_river()
                        self.conduct_betting_round("river")
            
            # Showdown
            winners = self.conduct_showdown()
            self.award_pot(winners)
            
            # Store winners for tournament manager access
            self.hand_winners = winners
            
            # Display results
            print(f"\n{Fore.YELLOW}🏆 HAND RESULTS")
            community_str = ', '.join(str(card) for card in self.community_cards)
            print(f"Community: {community_str}")
            
            if len(winners) == 1:
                print(f"Winner: {winners[0].name}")
            else:
                winner_names = ', '.join(w.name for w in winners)
                print(f"Winners: {winner_names}")
            
            # Advance dealer
            self.dealer_position = (self.dealer_position + 1) % len(self.players)
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error in hand {self.hand_number}: {e}")
            return False 