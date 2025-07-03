#!/bin/bash

echo "🎨 Starting AI Crypto Trading Bot Frontend..."
echo
echo "Make sure the backend is running first:"
echo "  python start_backend.py"
echo
echo "Opening frontend in your default browser..."

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FRONTEND_PATH="$DIR/frontend/index.html"

echo "Frontend URL: file://$FRONTEND_PATH"
echo

# Try to open in browser (works on macOS and most Linux distributions)
if command -v open &> /dev/null; then
    # macOS
    open "$FRONTEND_PATH"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "$FRONTEND_PATH"
else
    echo "❌ Could not automatically open browser."
    echo "Please manually open: $FRONTEND_PATH"
    exit 1
fi

echo "✅ Frontend opened!"
echo "If it doesn't work, manually open: frontend/index.html" 