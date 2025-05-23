#!/usr/bin/env python3
"""
Script to start the Pied Piper LiveKit Agent
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        'LIVEKIT_URL',
        'LIVEKIT_API_KEY', 
        'LIVEKIT_API_SECRET',
        'GROQ_API_KEY',
        'ELEVEN_API_KEY',
        'GOOGLE_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return 1
        
    print("🚀 Starting Pied Piper Agent...")
    print(f"🔗 LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    print(f"🏠 Room: {os.getenv('LIVEKIT_ROOM_NAME', 'pipey-room')}")
    
    try:
        # Run the agent directly
        cmd = [sys.executable, "pied_piper_agent.py"]
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Agent failed to start: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")
        return 0

if __name__ == "__main__":
    exit(main())