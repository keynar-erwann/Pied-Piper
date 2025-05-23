#!/bin/bash

# Pied Piper FastAPI Backend Startup Script

echo "🎵 Starting Pied Piper FastAPI Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check environment variables
echo "Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please create one with your API keys."
    echo "Required variables:"
    echo "- LIVEKIT_URL"
    echo "- LIVEKIT_API_KEY"
    echo "- LIVEKIT_API_SECRET"
    echo "- GROQ_API_KEY"
    echo "- ELEVEN_API_KEY"
    echo "- GOOGLE_API_KEY"
    echo "- SERPAPI_KEY"
fi

# Start the server
echo "🚀 Starting Pied Piper API server on http://0.0.0.0:8000"
python main.py