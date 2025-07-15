# Keywordsai Samples

This repository contains a collection of AI and automation projects demonstrating various technologies and use cases. Each project showcases different aspects of AI development, from visual workflow builders to trading bots and scheduling systems.

## 📁 Projects Overview

### 🎮 [ai-blocks](./ai-blocks/)
**Visual Workflow Builder for AI Agents**
- **Tech Stack**: Next.js 15, React 19, TypeScript, Tailwind CSS, React Flow
- **Description**: Interactive visual programming platform for designing AI agent workflows
- **Features**: Drag-and-drop interface, tutorial levels, sandbox mode, real-time execution
- **Status**: Active Development

### 💰 [crypto_bot4.5](./crypto_bot4.5/)
**Cryptocurrency Trading Bot**
- **Tech Stack**: Python, Backend API, Frontend Dashboard
- **Description**: Automated cryptocurrency trading system with monitoring dashboard
- **Features**: Trading algorithms, risk management, real-time monitoring
- **Status**: Version 4.5

### 📅 [google_scheduler6.5](./google_scheduler6.5/)
**AI-Powered Google Calendar Scheduler**
- **Tech Stack**: JavaScript, Google Calendar API, Jupyter Notebooks
- **Description**: Intelligent scheduling system that integrates with Google Calendar
- **Features**: 
  - Calendar conflict detection
  - Automated scheduling
  - AI-powered time suggestions
  - Google OAuth integration
- **Components**:
  - `ai_scheduler_workflow.ipynb` - Main scheduling logic
  - `google_auth_setup.ipynb` - Authentication setup
  - `openai_js_tracing/` - Node.js implementation with OpenAI integration
- **Status**: Version 6.5

### 🃏 [poker_fight5.5](./poker_fight5.5/)
**AI Poker Tournament System**
- **Tech Stack**: Python, HTML/CSS/JS, CSV logging
- **Description**: Multi-agent poker tournament with AI players and analytics
- **Features**:
  - Texas Hold'em poker engine
  - AI player strategies
  - Tournament management
  - Performance analytics
  - Web-based visualization
- **Components**:
  - `core/` - Game logic and models
  - `engine/` - Poker game engine
  - `services/` - Logging and AI integration
  - `texas-holdem-master/` - Web interface
- **Status**: Version 5.5

### 📊 [get_start01-03](./get_start01-03/)
**Getting Started Samples**
- **Tech Stack**: Python
- **Description**: Basic examples and tutorials for AI development
- **Features**: Logging, proxy configuration, tracing examples
- **Status**: Tutorial/Examples

### 📝 [Logging04](./Logging04/)
**Logging API Examples**
- **Tech Stack**: Python
- **Description**: API logging implementations and examples
- **Features**: Embedded and full logging solutions
- **Status**: Examples

### 🎨 [mcp_blender](./mcp_blender/)
**Blender Integration**
- **Tech Stack**: Python (Blender Add-on)
- **Description**: Blender add-on for AI-powered 3D modeling workflows
- **Status**: Development

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ (for ai-blocks, google_scheduler)
- **Python** 3.8+ (for crypto_bot, poker_fight, logging examples)
- **Git** for version control

### Running Individual Projects

#### AI Blocks (Visual Workflow Builder)
```bash
cd ai-blocks
npm install
npm run dev
# Open http://localhost:3000