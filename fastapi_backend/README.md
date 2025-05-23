# Pied Piper FastAPI Backend

A FastAPI backend for the Pied Piper AI music companion that provides voice chat, music search, and LiveKit integration.

## Features

- 🎵 **Music Chat API**: Text-based conversations about music
- 🎤 **WebSocket Support**: Real-time chat functionality
- 🔊 **LiveKit Integration**: Voice chat capabilities
- 🔍 **Music Search**: Integration with music databases and search APIs
- 🌍 **Multi-language Support**: Supports multiple languages
- 📱 **CORS Enabled**: Ready for frontend integration

## Quick Start

### Option 1: Using the Start Script
```bash
cd fastapi_backend
./start.sh
```

### Option 2: Manual Setup
```bash
cd fastapi_backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

### Option 3: Using Docker
```bash
cd fastapi_backend

# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t pied-piper-api .
docker run -p 8000:8000 --env-file .env pied-piper-api
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_ROOM_NAME=pipey-room

# AI Service Keys
GROQ_API_KEY=your_groq_api_key
ELEVEN_API_KEY=your_elevenlabs_api_key
GOOGLE_API_KEY=your_google_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Music Search APIs
SERPAPI_KEY=your_serpapi_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
GENIUS_API_KEY=your_genius_api_key

# Server Configuration (optional)
HOST=0.0.0.0
PORT=8000
```

## API Endpoints

### Health Check
- `GET /health` - Check server status and configuration

### Chat
- `POST /chat` - Send a text message to Pied Piper
- `WebSocket /ws` - Real-time chat connection

### LiveKit
- `GET /livekit/config` - Get LiveKit configuration
- `POST /livekit/token` - Generate LiveKit access token

### Music Search
- `POST /search/music` - Search for music information

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Deployment

### Railway
1. Fork this repository
2. Connect to Railway
3. Set environment variables in Railway dashboard
4. Deploy automatically

### Heroku
1. Create a new Heroku app
2. Set environment variables
3. Deploy using Git or GitHub integration

### DigitalOcean/AWS/GCP
1. Use the Dockerfile for containerized deployment
2. Set up environment variables
3. Configure load balancer and domain

## Frontend Integration

The API is designed to work with any frontend. Example usage:

```javascript
// Text chat
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ content: 'Hello Pied Piper!' })
});

// WebSocket chat
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Pied Piper says:', message.content);
};
```

## Development

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
pytest tests/
```

## Troubleshooting

1. **Import Errors**: Make sure all dependencies are installed
2. **API Key Issues**: Check that all required environment variables are set
3. **Port Conflicts**: Change the PORT environment variable if 8000 is in use
4. **CORS Issues**: Adjust CORS settings in main.py for your domain

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details