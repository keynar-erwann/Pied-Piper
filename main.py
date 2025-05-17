from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from Pipey import MultilingualPipeyAgent, AgentSession
import asyncio
import json

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000/"],  # In production, replace with your v0 frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Create Pipey agent instance
    agent = MultilingualPipeyAgent()
    session = AgentSession()
    
    try:
        # Start agent session
        await session.start(agent=agent)
        
        # Handle messages
        while True:
            # Receive message from v0 frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message through agent
            response = await agent.handle_message(message['text'])
            
            # If no specific response from handle_message, get general response
            if response is None:
                # The response will be handled by the agent's LLM
                continue
                
            # Send response back to frontend
            await websocket.send_text(json.dumps({
                "type": "response",
                "text": response
            }))
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=3001)