"""
Keywords AI API interface for poker LLM decisions
"""

import requests
import json
import random
import os
from typing import Dict, Any, Optional
from colorama import Fore
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class KeywordsAI:
    def __init__(self, api_key: str = None):
        """Initialize Keywords AI client"""
        self.api_key = api_key or os.getenv('KEYWORDSAI_API_KEY')
        
        if not self.api_key or self.api_key == 'YOUR_API_KEY_HERE':
            print(f"{Fore.RED}⚠ WARNING: No valid API key found!")
            print(f"{Fore.YELLOW}Please set KEYWORDSAI_API_KEY in your .env file")
            print(f"{Fore.CYAN}Get your API key from: https://keywordsai.co/")
        
        self.base_url = os.getenv('KEYWORDSAI_BASE_URL', 'https://api.keywordsai.co/api') + '/chat/completions'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
    
    def test_connection(self) -> bool:
        """Test the API connection"""
        if not self.api_key or self.api_key == 'YOUR_API_KEY_HERE':
            return False
            
        try:
            response = self.get_decision("gpt-4o-mini", "Say 'test' if you can hear me")
            return "test" in response.lower()
        except Exception as e:
            print(f"{Fore.RED}API test failed: {e}")
            return False
    
    def get_poker_decision(self, player_name: str, model: str, game_state: Dict[str, Any], 
                          customer_id: str = None, group_id: str = None, personality: str = None) -> Dict[str, str]:
        """
        Get a detailed poker decision with full tournament context
        
        Args:
            player_name: Name of the player (e.g. "GPT-4o", "Claude", "Grok")
            model: The model to use 
            game_state: Complete game state with all context
            customer_id: Customer identifier for tracking
            group_id: Group identifier for hand tracking
            
        Returns:
            Dictionary with 'action', 'reason', and 'full_context'
        """
        if not self.api_key or self.api_key == 'YOUR_API_KEY_HERE':
            return self._random_fallback_poker()
        
        # Build comprehensive poker prompt
        prompt = self._build_poker_prompt(player_name, game_state)
        system_prompt = self._build_system_prompt(player_name, personality)
        
        # Get LLM response
        response = self.get_decision(model, prompt, customer_id, group_id, system_prompt)
        
        # Clean response of markdown formatting
        cleaned_response = response.strip()
        
        # Remove markdown code blocks if present
        if '```json' in cleaned_response:
            start = cleaned_response.find('```json') + 7
            end = cleaned_response.find('```', start)
            if end != -1:
                cleaned_response = cleaned_response[start:end].strip()
        elif '```' in cleaned_response:
            start = cleaned_response.find('```') + 3
            end = cleaned_response.find('```', start)
            if end != -1:
                cleaned_response = cleaned_response[start:end].strip()
        
        # Parse JSON response
        try:
            parsed = json.loads(cleaned_response)
            return {
                'action': parsed.get('action', 'fold'),
                'reason': parsed.get('reason', 'No reasoning provided'),
                'full_context': prompt
            }
        except json.JSONDecodeError:
            # Try to extract action and reason from text response
            return self._parse_text_response(response, prompt)

    def _build_poker_prompt(self, player_name: str, game_state: Dict[str, Any]) -> str:
        """Build detailed poker decision prompt like the example"""
        hand_num = game_state.get('hand_number', 1)
        total_hands = game_state.get('total_hands', 50)
        round_name = game_state.get('round', 'pre-flop')
        pot = game_state.get('pot', 0)
        current_bet = game_state.get('current_bet', 0)
        to_call = game_state.get('to_call', 0)
        player_chips = game_state.get('player_chips', 1500)
        player_cards = game_state.get('player_cards', ['xx', 'xx'])
        community_cards = game_state.get('community_cards', [])
        opponents = game_state.get('opponents', [])
        actions_this_round = game_state.get('actions_this_round', [])
        actions_this_hand = game_state.get('actions_this_hand', [])
        
        # Phase determination
        if hand_num <= 10:
            phase = "🟢 EARLY PHASE (Hands 1-10): Blinds $5/$10"
            pressure = "🟢 LOW PRESSURE"
        elif hand_num <= 30:
            phase = "🟡 MID PHASE (Hands 11-30): Blinds $10/$20"
            pressure = "🟡 MEDIUM PRESSURE"
        else:
            phase = "🔴 LATE PHASE (Hands 31-50): Blinds $20/$40"
            pressure = "🔴 HIGH PRESSURE"
        
        # Format cards
        hole_cards = f"{player_cards[0]}, {player_cards[1]}" if len(player_cards) >= 2 else "xx, xx"
        community = ", ".join(community_cards) if community_cards else "None dealt yet"
        
        # Format opponents
        opponent_info = []
        for opp in opponents:
            status = " (FOLDED)" if opp.get('folded', False) else ""
            opponent_info.append(f"- {opp['name']}: ${opp['chips']} total (bet: ${opp['current_bet']} this round){status}")
        
        # Format ALL actions in this hand (across all rounds)
        hand_action_history = []
        if actions_this_hand:
            current_round_actions = ""
            last_round = ""
            for action in actions_this_hand:
                action_round = action.get('round', '')
                action_player = action.get('player', '')
                action_type = action.get('action', '')
                action_amount = action.get('amount', 0)
                
                # Group by rounds
                if action_round != last_round:
                    if current_round_actions:
                        hand_action_history.append(current_round_actions)
                    current_round_actions = f"{action_round.upper()}: "
                    last_round = action_round
                
                # Format action with amount if relevant
                if action_amount > 0:
                    current_round_actions += f"{action_player} {action_type} ${action_amount}, "
                else:
                    current_round_actions += f"{action_player} {action_type}, "
            
            # Add final round
            if current_round_actions:
                hand_action_history.append(current_round_actions.rstrip(', '))
        
        # Actions this round only
        current_round_actions = []
        for action in actions_this_round:
            if action.get('amount', 0) > 0:
                current_round_actions.append(f"{action['player']} {action['action']} ${action['amount']}")
            else:
                current_round_actions.append(f"{action['player']} {action['action']}")
        
        # Available actions
        actions_available = []
        if to_call > 0:
            actions_available.extend([
                f'- "fold" - Give up this hand',
                f'- "call" - Match the current bet (${to_call})',
                f'- "raise X" - Raise by amount X (minimum ${current_bet + 10})'
            ])
        else:
            actions_available.extend([
                f'- "fold" - Give up this hand',
                f'- "check" - Pass (only if no bet to call)',
                f'- "raise X" - Raise by amount X (minimum $10)'
            ])
            
        # Define newline for f-string and safely extract values
        newline = '\n'
        player_current_bet = game_state.get('player_current_bet', 0)
        round_name_upper = round_name.upper()
        min_raise_amount = current_bet + 10
        
        # Safely join lists
        all_players_text = newline.join(opponent_info)
        hand_history_text = newline.join(hand_action_history) if hand_action_history else "No actions yet in this hand"
        current_round_text = newline.join(current_round_actions) if current_round_actions else "No actions yet this round"
        actions_text = newline.join(actions_available)

        prompt = f"""POKER DECISION REQUIRED
        
TOURNAMENT CONTEXT:
{phase}
{pressure}
Hand: {hand_num}/{total_hands}

YOUR SITUATION:
- Hand: {hole_cards}
- Your chips: ${player_chips}
- Your current bet this round: ${player_current_bet}

GAME STATE:
- Betting round: {round_name}
- Community cards: {community}
- Current pot: ${pot}
- Current bet to call: ${to_call}
- Minimum raise: ${min_raise_amount}

ALL PLAYERS:
{all_players_text}

FULL HAND HISTORY:
{hand_history_text}

CURRENT ROUND ({round_name_upper}):
{current_round_text}

ACTIONS AVAILABLE:
{actions_text}

🎲 RESPOND WITH ONLY VALID JSON - NO MARKDOWN, NO CODE BLOCKS, NO EXTRA TEXT:

You must respond with EXACTLY this format:
{{"action": "your_action", "reason": "your_reasoning"}}

Valid actions: "fold", "check", "call", "raise X" (where X is amount)
Keep reasoning to 2-3 sentences maximum.

Examples:
{{"action": "fold", "reason": "Weak hole cards and facing a large bet. Not worth the risk with limited chips."}}
{{"action": "call", "reason": "Good pot odds with a decent hand. Want to see the flop before committing more."}}
{{"action": "raise 60", "reason": "With a pair on the flop and a potential flush draw, I want to take control and build the pot."}}

IMPORTANT: Do NOT use markdown, do NOT use ```json```, respond with pure JSON only."""

        return prompt

    def _build_system_prompt(self, player_name: str, personality: str = None) -> str:
        """Build system prompt for player identity using actual personality from config"""
        # Use provided personality from tournament config, or fallback to hardcoded styles
        if personality:
            style = f"Your personality is {personality}. Play poker accordingly."
        else:
            # Fallback to hardcoded styles if no personality provided
            styles = {
                "GPT-4o": "Play strategic poker with calculated aggression when you have strong hands and conservative play with weak hands.",
                "Claude": "Play tight-aggressive poker, focusing on position and pot odds. Make disciplined decisions.",
                "Grok": "Play loose-aggressive poker with creative bluffs and unexpected moves. Take calculated risks."
            }
            style = styles.get(player_name, "Play balanced poker with good fundamentals.")
        
        return f"""You are playing Texas Hold'em poker as {player_name}.

🎭 YOUR PLAYING STYLE: {style}

CRITICAL: You must respond with ONLY pure JSON. No markdown, no code blocks, no extra text.
Format: {{"action": "your_action", "reason": "your_reasoning"}}

Never use ```json``` or any markdown formatting. Only pure JSON."""

    def _parse_text_response(self, response: str, context: str) -> Dict[str, str]:
        """Parse non-JSON text response to extract action and reason"""
        response_lower = response.lower()
        
        # Try to extract action
        action = "fold"  # default
        if "raise" in response_lower:
            # Try to extract raise amount
            import re
            match = re.search(r'raise\s+(\d+)', response_lower)
            if match:
                action = f"raise {match.group(1)}"
            else:
                action = "raise 20"
        elif "call" in response_lower:
            action = "call"
        elif "check" in response_lower:
            action = "check"
        elif "fold" in response_lower:
            action = "fold"
        
        return {
            'action': action,
            'reason': response[:200],  # First 200 chars as reason
            'full_context': context
        }

    def _random_fallback_poker(self) -> Dict[str, str]:
        """Fallback poker decision when API unavailable"""
        actions = [
            {"action": "fold", "reason": "API unavailable - random fallback decision"},
            {"action": "check", "reason": "API unavailable - random fallback decision"}, 
            {"action": "call", "reason": "API unavailable - random fallback decision"},
            {"action": "raise 20", "reason": "API unavailable - random fallback decision"}
        ]
        choice = random.choice(actions)
        return {
            'action': choice['action'],
            'reason': choice['reason'],
            'full_context': 'API unavailable'
        }

    def get_decision(self, model: str, prompt: str, customer_id: str = None, 
                    group_id: str = None, system_prompt: str = None) -> str:
        """
        Get a decision from the specified LLM model with customer and group tracking
        
        Args:
            model: The model to use (e.g. "gpt-4o-mini", "claude-3-5-sonnet-20240620")
            prompt: The decision prompt to send
            customer_id: Customer identifier for player tracking (e.g., "GPT-4", "Claude", "Grok")
            group_id: Group identifier for hand tracking (e.g., "hand_1", "hand_2")
            system_prompt: System message with player identity and playing style
            
        Returns:
            The LLM's response as a string
        """
        if not self.api_key or self.api_key == 'YOUR_API_KEY_HERE':
            # Fallback to random decision if no API key
            return self._random_fallback()
        
        # Build messages array with optional system prompt
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        # Build payload with customer and group tracking
        payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 500
        }
        
        # Add customer and group tracking parameters
        if customer_id:
            payload['customer_identifier'] = customer_id
        if group_id:
            payload['group_identifier'] = group_id
        
        try:
            response = requests.post(
                self.base_url, 
                headers=self.headers, 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    return content.strip()
                else:
                    print(f"{Fore.RED}Unexpected API response format")
                    return self._random_fallback()
            else:
                print(f"{Fore.RED}API Error {response.status_code}: {response.text}")
                return self._random_fallback()
                
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}API request timed out")
            return self._random_fallback()
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}API connection failed")
            return self._random_fallback()
        except Exception as e:
            print(f"{Fore.RED}API request failed: {e}")
            return self._random_fallback()
    
    def _random_fallback(self) -> str:
        """Fallback to random poker decisions when API is unavailable"""
        actions = [
            '{"action": "fold", "reason": "Random fallback decision"}',
            '{"action": "check", "reason": "Random fallback decision"}', 
            '{"action": "call", "reason": "Random fallback decision"}',
            '{"action": "raise 20", "reason": "Random fallback decision"}',
            '{"action": "raise 50", "reason": "Random fallback decision"}'
        ]
        return random.choice(actions) 