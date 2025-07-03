# Poker Fight 05 - Reorganized LLM Texas Hold'em Tournament

A well-structured Python poker tournament system where Large Language Models (GPT-4o, Claude, and Grok) compete in Texas Hold'em with a proper 3-phase blind structure.

## 🏆 Tournament Structure

The tournament follows a proper escalating blind structure:

- **🟢 Early Phase (Hands 1-10)**: Blinds $5/$10 - Low pressure, conservative play
- **🟡 Mid Phase (Hands 11-30)**: Blinds $20/$40 - Moderate pressure, strategic decisions
- **🔴 Late Phase (Hands 31-50)**: Blinds $50/$100 - High pressure, aggressive play

Each player starts with **$1,500** in chips. The tournament continues until only one player remains or 50 hands are completed.

## 📁 Project Structure

```
poker_fight05/
├── core/                          # Core game components
│   ├── __init__.py
│   ├── models.py                  # Data models (Player, Card, GameState, etc.)
│   ├── deck.py                    # Deck management and card dealing
│   └── hand_evaluator.py          # Poker hand evaluation logic
├── engine/                        # Game engine
│   ├── __init__.py
│   └── poker_engine.py            # Core poker game logic with tournament integration
├── services/                      # External services
│   ├── __init__.py
│   ├── keywords_ai.py             # Keywords AI API interface
│   └── csv_logger.py              # CSV logging and data export
├── tournament_manager.py          # Tournament structure and progression management
├── tournament_config.py           # Configuration settings
├── poker_tournament.py            # Main tournament runner
├── reset_tournament.py            # Tournament reset utility
└── README.md                      # This file
```

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up your Keywords AI API key
# Create a .env file with:
# KEYWORDS_AI_API_KEY=your_api_key_here
```

### 2. Run Tournament

**Full Tournament (Recommended)**
```bash
python poker_tournament.py
```

**Single Hand Mode (Step-by-step)**
```bash
python poker_tournament.py --single
```

**Reset and Start Fresh**
```bash
python poker_tournament.py --reset
```

**Custom Hand Limit**
```bash
python poker_tournament.py --hands 20
```

### 3. Reset Tournament

```bash
python reset_tournament.py
```

## 🎮 Usage Examples

### Run Complete Tournament
```bash
python poker_tournament.py
```
Runs the full 50-hand tournament with automatic phase transitions.

### Play One Hand at a Time
```bash
python poker_tournament.py --single
```
Perfect for watching each hand carefully. Run repeatedly to advance through the tournament.

### Reset Everything
```bash
python reset_tournament.py
```
Cleans all tournament files and shows the configuration.

## 🤖 Players

- **GPT-4o**: Professional and analytical approach using `gpt-4o` model
- **Claude**: Strategic decision-making with `claude-3-5-sonnet-20241022` model  
- **Grok**: Dynamic play style using `xai/grok-2-1212` model

## 📊 Output Files

- **`tournament_state.json`**: Current tournament state and progress
- **`poker_tournament_YYYYMMDD_HHMMSS.csv`**: Complete game log with all actions
- **Console output**: Real-time game progress with colorful formatting

## 🏗️ Architecture Features

### Modular Design
- **Core**: Game logic separated from tournament management
- **Engine**: Clean poker engine with proper betting rounds
- **Services**: External dependencies isolated for easy testing
- **Tournament Manager**: Centralized tournament structure handling

### Tournament Management
- **Automatic phase transitions** at hands 11 and 31
- **Proper blind escalation** according to tournament rules
- **State persistence** for resuming tournaments
- **Comprehensive logging** for analysis

### Robust Error Handling
- **API timeout handling** with fallback decisions
- **State recovery** if tournament is interrupted
- **Clean reset functionality** for fresh starts

## 📈 Tournament Phases

### Early Phase (Hands 1-10)
- **Blinds**: $5/$10
- **Strategy**: Conservative play, building chip stacks
- **Pressure Level**: Low

### Mid Phase (Hands 11-30)  
- **Blinds**: $20/$40
- **Strategy**: More aggressive, strategic positioning
- **Pressure Level**: Moderate

### Late Phase (Hands 31-50)
- **Blinds**: $50/$100
- **Strategy**: High-pressure decisions, all-in scenarios
- **Pressure Level**: High

## 🔧 Configuration

Edit `tournament_config.py` to customize:

- **Starting chips** amount
- **Blind structure** and timing
- **Player models** and personalities
- **Tournament length**
- **API settings**

## 📋 CSV Log Format

The CSV log contains complete tournament data:

```csv
hand,round,action,player,amount,llm1_chips,llm2_chips,llm3_chips,pot,llm1_cards,llm2_cards,llm3_cards,community_1,community_2,community_3,community_4,community_5,timestamp,llm_action,reasoning,winner,hand_result
```

## 🛠️ Development

### Adding New Players
1. Edit `tournament_config.py`
2. Add player configuration to `PLAYER_CONFIGS`
3. Restart tournament

### Modifying Tournament Structure
1. Edit phases in `tournament_config.py`
2. Update `TournamentManager` if needed
3. Reset tournament to apply changes

### Testing Components
```bash
python -m pytest tests/  # When tests are added
```

## 🏆 Tournament Results

The system tracks:
- **Final standings** with profit/loss
- **Hand-by-hand results** in CSV format
- **Tournament winner** determination
- **Complete game history** for analysis

## 📞 Support

For issues or questions:
1. Check the console output for error messages
2. Review the CSV log for hand details
3. Use `reset_tournament.py` to start fresh
4. Ensure your Keywords AI API key is valid

## 🎯 Future Enhancements

- [ ] Multi-table tournament support
- [ ] Advanced hand evaluation algorithms
- [ ] Real-time web dashboard
- [ ] Statistical analysis tools
- [ ] Player strategy customization
- [ ] Tournament replay functionality

---

**Ready to watch LLMs battle it out at the poker table!** 🃏🤖 