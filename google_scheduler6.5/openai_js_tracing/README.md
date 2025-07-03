# OpenAI Agents Scheduling Demo

A simple demonstration of using OpenAI Agents SDK with Google Calendar integration for automated scheduling.

## ⚠️ Windows Compatibility Issue

**Note: This project is currently not working on Windows systems.**

The implementation relies on certain Unix-specific features and dependencies that are not compatible with the Windows environment. Windows users may experience issues with:

- Node.js dependencies installation
- File path handling
- Process management
- Authentication flow

### Alternatives for Windows Users

If you're using Windows, consider:
- Using WSL (Windows Subsystem for Linux)
- Running the project in a Docker container
- Using a macOS or Linux virtual machine

## Overview

This demo showcases a complete scheduling workflow using multiple AI agents:

1. **Date Extractor Agent** - Parses user input to identify scheduling requests and extract date/time information
2. **Schedule Planner Agent** - Analyzes calendar availability and suggests optimal time slots
3. **Response Generator Agent** - Creates user-friendly responses about scheduled events
4. **Calendar Integration** - Checks availability and schedules events (mock implementation)

## Workflow

```
User Input → Date Extraction → Calendar Check → Schedule Planning → Event Creation → Response Generation
```

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Configuration

Copy `env.example` to `.env` and fill in your credentials:

```bash
cp env.example .env
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `GOOGLE_CLIENT_ID` - Google OAuth2 client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth2 client secret
- `GOOGLE_REDIRECT_URI` - OAuth2 redirect URI
- `CALENDAR_ID` - Your Google Calendar ID (usually your email)

### 3. Google Calendar API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Create OAuth2 credentials
5. Download the credentials and update your `.env` file

## Usage

### Option 1: Web Server (Recommended)

Start the web server with frontend interface:

```bash
npm run server
```

Then open your browser to `http://localhost:3000` to use the web interface.

### Option 2: CLI Demo

Run the demo through the command line:

```bash
npm start
```

The demo will run through several example scheduling requests and show the complete workflow.

### Example Inputs

- "Schedule a team meeting for tomorrow at 2pm"
- "Book a doctor appointment for next Monday"
- "Set up a call with John for Friday at 10am"

## File Structure

```
├── server.js               # Express server with API endpoints and frontend
├── index.html              # Frontend web interface
├── main.js                 # Main orchestration file (for CLI demo)
├── index.js                # Entry point for CLI demo
├── dateExtractor.js        # Agent for extracting date/time from user input
├── calendarChecker.js      # Module for checking Google Calendar availability
├── schedulePlanner.js      # Agent for planning optimal schedule
├── calendarScheduler.js    # Module for creating calendar events
├── responseGenerator.js    # Agent for generating user responses
├── googleAuth.js           # Google OAuth2 authentication module
├── setup-google-auth.js    # Google Auth setup script
├── check-auth.js           # Auth verification utility
├── package.json            # Dependencies and scripts
├── env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Features

- **Multi-Agent Workflow**: Uses different specialized agents for each step
- **Natural Language Processing**: Understands various date/time formats
- **Calendar Integration**: Checks availability and schedules events
- **Error Handling**: Graceful error handling throughout the workflow
- **Mock Implementation**: Includes mock calendar data for demo purposes

## Customization

### Adding Real Google Calendar Integration

To use real Google Calendar API instead of mock data:

1. Uncomment the Google Calendar API calls in `calendarChecker.js` and `calendarScheduler.js`
2. Implement proper OAuth2 flow for authentication
3. Handle token refresh and error cases

### Extending Agents

Each agent can be customized by modifying their instructions in the respective files:

- `dateExtractor.js` - Modify date parsing logic
- `schedulePlanner.js` - Adjust scheduling preferences
- `responseGenerator.js` - Customize response style

## Notes

- This is a demo implementation with mock calendar data
- Real Google Calendar integration requires proper OAuth2 setup
- The agents use structured JSON responses for reliable parsing
- Error handling is included for robustness

## Troubleshooting

1. **OpenAI API Key**: Ensure your API key is valid and has sufficient credits
2. **Environment Variables**: Check that all required variables are set in `.env`
3. **Dependencies**: Run `npm install` to ensure all packages are installed
4. **Google Calendar**: For real integration, ensure OAuth2 is properly configured

## License

ISC 