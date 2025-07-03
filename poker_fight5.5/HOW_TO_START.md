# 🎰 How to Start the Poker Animation

## 🚀 **Quick Start Guide**

### **Step 1: Open the Animation**
1. Double-click on `poker_animation.html` in your file explorer
2. **OR** Right-click → "Open with" → Choose your web browser (Chrome, Firefox, Edge, Safari)
3. **OR** Run this command in PowerShell:
   ```
   start poker_animation.html
   ```

### **Step 2: Load Your CSV Data**
1. Click the **"Choose File"** button in the "📁 Load Tournament CSV" section
2. Select your CSV file: `poker_tournament_20250616_203931.csv`
3. The game interface will appear automatically!

### **Step 3: Control the Animation**
- **▶ Play**: Auto-play through all actions
- **⏸ Pause**: Stop auto-play
- **⏮ Previous**: Go back one step
- **⏭ Next**: Go forward one step  
- **Speed**: Change animation speed (0.5x, 1x, 2x, 4x)

## 🎯 **What You'll See:**

### **🃏 Game Flow:**
1. **Hand Start** → Empty table
2. **Small/Big Blind** → Players post blinds
3. **Deal Hole Cards** → Cards flip to show player hands
4. **Betting Round** → Players FOLD/CALL/RAISE/CHECK
5. **Deal Flop** → 3 community cards flip
6. **Betting Round** → More player actions
7. **Deal Turn** → 4th community card flips
8. **Betting Round** → Final decisions
9. **Deal River** → 5th community card flips
10. **Showdown** → Winner revealed, chips distributed

### **🎨 Visual Features:**
- **Grey background** with **black edges** (as requested!)
- **Card flip animations** using your texas-holdem-master images
- **Player highlighting** (golden glow for active player)
- **Winner celebration** (green pulsing effect)
- **Real-time chip updates**
- **Action log** with LLM reasoning

## 🔧 **Troubleshooting:**

### **Cards not showing?**
- Make sure the `texas-holdem-master/images/` folder is in the same directory
- Check browser console for image loading errors

### **CSV not loading?**
- Make sure your CSV file has the correct format with headers
- Try refreshing the page and loading again

### **Animation too fast/slow?**
- Use the **Speed** button to adjust (0.5x = slower, 4x = faster)

## 📁 **File Structure:**
```
poker_fight05/
├── poker_animation.html          ← Main animation file
├── poker_tournament_20250616_203931.csv  ← Your tournament data
├── texas-holdem-master/
│   └── images/                   ← Card images (AS.svg, KH.svg, etc.)
└── HOW_TO_START.md              ← This guide
```

## 🎮 **Ready to Play!**
Just open `poker_animation.html` in your browser and load the CSV file! 🚀🎰 