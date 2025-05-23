from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from dotenv import load_dotenv
import asyncio
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pied Piper API", description="AI Music Companion Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    content: str
    sender: str = "user"
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    content: str
    sender: str = "ai"
    timestamp: datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Import the Pied Piper agent functionality
try:
    from pied_piper_agent import MultilingualPipeyAgent
    AGENT_AVAILABLE = True
    logger.info("Pied Piper agent loaded successfully")
except ImportError as e:
    AGENT_AVAILABLE = False
    logger.warning(f"Pied Piper agent not available: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_available": AGENT_AVAILABLE,
        "environment": {
            "livekit_url": os.getenv("LIVEKIT_URL", "Not configured"),
            "has_api_keys": {
                "groq": bool(os.getenv("GROQ_API_KEY")),
                "eleven": bool(os.getenv("ELEVEN_API_KEY")),
                "google": bool(os.getenv("GOOGLE_API_KEY")),
                "serpapi": bool(os.getenv("SERPAPI_KEY"))
            }
        }
    }

# Chat endpoint for simple text interactions
@app.post("/chat", response_model=ChatResponse)
async def chat_with_pied_piper(message: ChatMessage):
    """
    Simple chat endpoint for text-based interactions with Pied Piper
    """
    try:
        # Generate response based on message content
        response_content = generate_music_response(message.content)
        
        return ChatResponse(
            content=response_content,
            sender="ai",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def generate_music_response(user_message: str) -> str:
    """
    Generate a music-focused response to user input
    """
    message_lower = user_message.lower()
    
    # Music-related keywords and responses
    if any(keyword in message_lower for keyword in ['song', 'music', 'artist', 'band', 'album']):
        if 'recommend' in message_lower or 'suggest' in message_lower:
            return "I'd love to recommend some music for you! What genre or mood are you in the mood for? I can suggest artists like Taylor Swift for pop, Pink Floyd for classic rock, or maybe some lo-fi beats for studying?"
        elif 'lyrics' in message_lower:
            return "I can help you find lyrics! What song are you looking for? I can search for lyrics and even tell you about the meaning behind the songs."
        elif 'search' in message_lower or 'find' in message_lower:
            return "Let me help you search for that! I can find information about songs, artists, albums, and more. What specifically are you looking for?"
        else:
            return "That's a great music question! I'm passionate about all things music - from discovering new artists to exploring the stories behind classic songs. What would you like to know more about?"
    
    elif 'hello' in message_lower or 'hi' in message_lower or 'hey' in message_lower:
        return "Hello there! I'm Pied Piper, your AI music companion. I'm here to help you discover new music, find lyrics, learn about artists, and explore the wonderful world of sound. What's on your musical mind today?"
    
    elif 'language' in message_lower:
        return "I can communicate in multiple languages including English, Spanish, French, German, Italian, and Hindi! I love helping people discover music from all around the world. What language would you prefer to chat in?"
    
    elif 'help' in message_lower:
        return "I'm here to help with all your music needs! I can search for song information, find lyrics, recommend music based on your taste, tell you about artists and albums, and even help you discover new genres. Just ask me anything about music!"
    
    else:
        return "That's interesting! As your AI music companion, I'm always excited to chat about music, artists, songs, and the power of sound. Is there anything musical you'd like to explore together?"

# WebSocket endpoint for real-time chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send welcome message
    welcome_message = {
        "type": "message",
        "content": "Hi there! I'm Pied Piper, your AI music companion. I can help you discover new songs, discuss your favorite artists, or tell you about music trends. What's on your musical mind today?",
        "sender": "ai",
        "timestamp": datetime.now().isoformat()
    }
    await websocket.send_text(json.dumps(welcome_message))
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_content = message_data.get("content", "")
            logger.info(f"Received message: {user_content}")
            
            # Generate response
            response_content = generate_music_response(user_content)
            
            # Send response back
            response_message = {
                "type": "message",
                "content": response_content,
                "sender": "ai",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_text(json.dumps(response_message))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# LiveKit integration endpoints
@app.get("/livekit/config")
async def get_livekit_config():
    """Get LiveKit configuration"""
    return {
        "url": os.getenv("LIVEKIT_URL", "wss://pied-piper-93l7cg2j.livekit.cloud"),
        "room_name": os.getenv("LIVEKIT_ROOM_NAME", "pipey-room")
    }

@app.post("/livekit/token")
async def generate_livekit_token():
    """Generate LiveKit access token"""
    try:
        from livekit import AccessToken, VideoGrants
        
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        room_name = os.getenv("LIVEKIT_ROOM_NAME", "pipey-room")
        
        if not api_key or not api_secret:
            raise HTTPException(status_code=500, detail="LiveKit credentials not configured")
        
        # Generate unique participant identity
        participant_identity = f"user_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}"
        
        # Create access token
        token = AccessToken(api_key, api_secret)
        token.with_identity(participant_identity)
        token.with_name(f"User {participant_identity[-8:]}")
        token.with_grants(VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        ))
        
        return {
            "token": token.to_jwt(),
            "identity": participant_identity,
            "room_name": room_name
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="LiveKit SDK not available")
    except Exception as e:
        logger.error(f"Error generating LiveKit token: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate access token")

# Music search endpoint
@app.post("/search/music")
async def search_music(query: dict):
    """Search for music information"""
    try:
        search_query = query.get("query", "")
        
        if not search_query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # This would integrate with your actual music search logic
        # For now, return a structured response
        return {
            "query": search_query,
            "results": [
                {
                    "title": f"Search results for: {search_query}",
                    "description": "I can help you find detailed information about this. Let me search for lyrics, artist info, and more details.",
                    "type": "music_search"
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in music search: {e}")
        raise HTTPException(status_code=500, detail="Music search failed")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )