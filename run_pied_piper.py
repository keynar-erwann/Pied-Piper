#!/usr/bin/env python3
"""
Simple script to run the Pied Piper agent directly
"""

import asyncio
from pied_piper_agent import entrypoint
from livekit.agents import JobContext

async def main():
    print("🎵 Starting Pied Piper Agent...")
    
    # Create a mock job context for testing
    # In production, this would come from LiveKit
    class MockJobContext:
        def __init__(self):
            self.room = None
        
        async def wait_for_participant(self):
            print("Waiting for participant to connect...")
            # For now, we'll just wait a bit
            await asyncio.sleep(1)
            print("Participant connected!")
    
    ctx = MockJobContext()
    
    try:
        await entrypoint(ctx)
    except Exception as e:
        print(f"Error running agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())