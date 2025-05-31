# 🎵 Pied Piper - AI Music Assistant

Pied Piper is an intelligent, multilingual AI voice music companion that combines real-time conversation, music discovery, and YouTube integration to create an immersive musical experience. Built with LiveKit and powered by advanced AI models, Pied Piper can see, hear, and interact with you naturally while helping you discover and play music.

## ✨ Features

### 🎶 Music Discovery & Playback
- **YouTube Integration**: Search and play music directly from YouTube
- **Lyrics Identification**: Identify songs from partial lyrics ("Play that song that goes...")
- **Song Information**: Get detailed information about tracks, artists, and albums
- **Music Recommendations**: Spotify-powered recommendations based on genres
- **Recently Played**: Track and replay your music history

### 🌍 Multilingual Support
- **6 Languages**: English, Spanish, French, German, Italian, and Hindi
- **Dynamic Language Switching**: Change languages mid-conversation
- **Localized Responses**: Native greetings and responses in each language

### 👁️ Real-Time Vision
- **Visual Music Recognition**: Identify album covers, instruments, and music-related content
- **Live Video Analysis**: Process video streams in real-time
- **Smart Context Awareness**: Understands what you're showing and responds accordingly

### 🧠 Intelligent Conversation
- **Natural Language Processing**: Understands casual music requests
- **Context Memory**: Remembers previous searches and conversations
- **Proactive Suggestions**: Automatically suggests playing songs during discussions

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required API keys (see Configuration section)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pied-piper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application**
   ```bash
   python Pied_Piper.py
   ```

## ⚙️ Configuration

Create a `.env` file with the following API keys:

```env
# Required for web search and song identification
SERPAPI_KEY=your_serpapi_key_here

# Required for YouTube music playback
YOUTUBE_API_KEY=your_youtube_api_key_here

# Optional: For Spotify recommendations
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# LiveKit configuration (if needed)
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

### Getting API Keys

1. **SerpAPI**: Sign up at [serpapi.com](https://serpapi.com) for web search capabilities
2. **YouTube Data API**: Enable YouTube Data API v3 in [Google Cloud Console](https://console.cloud.google.com)
3. **Spotify API**: Create an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## 🎯 Usage Examples

### Playing Music
```
"Play Bohemian Rhapsody"
"Put on some Beatles"
"I want to hear Shape of You"
```

### Music Discovery
```
"Search for jazz songs"
"Find me some rock music"
"Look up Taylor Swift songs"
```

### Lyrics Identification
```
"Play that song that goes 'Is this the real life'"
"What song has the lyrics 'Hello darkness my old friend'"
"Play the song that goes 'I see trees of green'"
```

### Language Switching
```
"Switch to Spanish"
"Habla en español"
"Change language to French"
```

### Getting Information
```
"Tell me about Hotel California"
"What do you know about The Beatles?"
"Give me info on Billie Eilish"
```

## 🏗️ Architecture

### Core Components

- **MultilingualPipeyAgent**: Main agent class handling all interactions
- **Music Tools**: YouTube integration, Spotify recommendations, song identification
- **Language Tools**: Dynamic language switching with localized responses
- **Vision System**: Real-time video analysis for music-related content
- **RAG System**: Retrieval-augmented generation for enhanced music knowledge

### AI Models Used

- **LLM**: Google Gemini 2.0 Flash for natural language understanding
- **STT**: Groq Whisper Large v3 Turbo for speech recognition
- **TTS**: ElevenLabs for natural voice synthesis
- **VAD**: Silero for voice activity detection

## 🛠️ Development

### Project Structure
```
pied-piper/
├── Pied_Piper.py          # Main application file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
└── docs/                 # Additional documentation
```

### Key Dependencies
- `livekit-agents`: Real-time communication framework
- `serpapi`: Web search integration
- `spotipy`: Spotify API wrapper
- `aiohttp`: Async HTTP client
- `python-dotenv`: Environment variable management

### Adding New Features

1. **New Music Sources**: Extend the music tools section with additional APIs
2. **More Languages**: Add new language codes and greetings to the language system
3. **Enhanced Vision**: Improve visual recognition with additional AI models
4. **Custom Commands**: Add new function tools for specific music operations

## 🔧 Troubleshooting

### Common Issues

**"Search unavailable" messages**
- Check that SERPAPI_KEY is properly set in your .env file
- Verify your SerpAPI account has remaining credits

**YouTube playback not working**
- Ensure YOUTUBE_API_KEY is valid and active
- Check that YouTube Data API v3 is enabled in Google Cloud Console
- Verify your browser allows automated URL opening

**Language switching not working**
- Confirm all required AI model APIs are properly configured
- Check that the language code is supported (en, es, fr, de, it, hi)

**Vision features not responding**
- Ensure camera permissions are granted
- Check that video track subscription is working in LiveKit

### Performance Optimization

- Adjust `vision_analysis_interval` for better performance vs. responsiveness balance
- Cache frequently requested song information to reduce API calls
- Monitor API rate limits across all services

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🆘 Support

For support, please:
1. Check the troubleshooting section above
2. Search existing issues on GitHub
3. Create a new issue with detailed information about your problem

## 🎵 Let's Make Music!

Pied Piper is more than just a music assistant - it's your AI companion for musical discovery and enjoyment. Whether you're looking to identify that song stuck in your head, discover new artists, or just have a chat about music, Pied Piper is here to help!

Start the conversation and let the music play! 🎶
