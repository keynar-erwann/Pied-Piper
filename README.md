# Pied Piper AI Music Assistant 🎵🤖

**Pied Piper** is a multilingual AI music companion that offers a conversational and immersive music discovery experience. Designed with advanced LLM, STT, TTS, and VAD technologies, it can play songs, interpret lyrics, debate music topics, recommend tracks, and much more — all through natural conversation. 

---

## 🚀 Features

### 🎧 Core Capabilities
- **Natural conversations about music**
- **YouTube music integration** (search/play music via lyrics or queries)
- **Multilingual support**: English, Spanish, French, German, Italian, Hindi
- **Proactive music recommendations** based on mood, season, trends, or events
- **Interactive debates** on music topics
- **Interpretation of song meanings** (literal, metaphorical, psychological, cultural)
- **Personalized music therapy** based on emotional context
- **Prediction of music trends** (genre, production, culture, tech)
- **Soundtracks for life events**

---

## 🧠 Intelligent Tools

- `play_youtube_music(song_query)`
- `search_youtube_songs(query)`
- `play_music_from_lyrics(lyrics_snippet)`
- `find_lyrics(lyrics_snippet)`
- `interpret_song_meaning(song_name, artist_name=None, personal_context=None)`
- `start_music_debate(topic, user_position)`
- `continue_music_debate(user_argument)`
- `music_therapy_session(current_feeling, situation=None, goal=None)`
- `predict_music_trends(timeframe='next_6_months', genre=None)`
- `seasonal_music_recommendations(override_season=None)`
- `life_event_soundtrack(event_type, description=None, emotional_tone=None)`
- Language switching: `switch_to_english`, `switch_to_spanish`, etc.

---

## 🌐 Language Support

Supports dynamic language switching and continued context in:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Hindi (hi)

---

## 🛠️ Dependencies

- Python 3.9+
- `livekit.agents`, `livekit.plugins` (Anthropic, ElevenLabs, Silero, Groq)
- `serpapi`
- `dotenv`, `aiohttp`, `webbrowser`, `logging`


🗣️ Usage

Run in the terminal : pip install -r requirements.txt to install all of the libraries and frameworks

Then run the script using:

python Pied_Piper_local_script.py console

If you want to use your own API Keys, here are the ones I used : 

ANTHROPIC_API_KEY
LIVEKIT_URL
LIVEKIT_API_SECRET
LIVEKIT_API_KEY
GROQ_API_KEY
ELEVEN_API_KEY
SERPAPI_KEY
LIVEKIT_ROOM_NAME
SPOTIFY_CLIENT_SECRET
SPOTIFY_CLIENT_ID
YOUTUBE_API_KEY


Pied Piper will greet you and begin a conversational session about music. Use natural language like:

    "Play 'Bohemian Rhapsody'"

    "What does 'Smells Like Teen Spirit' mean?"

    "I'm feeling anxious, can you help?"

    "Let's debate about 90s music"

    "Recommend music for autumn"

    "Create a soundtrack for my wedding"

💡 Design Philosophy

Pied Piper is built to:

    Be emotionally intelligent and empathetic

    Respond to musical cues naturally

    Preserve context throughout interactions

    Proactively enhance the user’s musical experience

📌 Notes

    Songs are played via YouTube in your default web browser.

    Language switching affects STT and TTS configuration.

    Song information and lyrics are fetched using SerpAPI.

🔒 Disclaimer

Do not use this tool to infringe on music licensing terms or play copyrighted material without proper rights.
