from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    ChatContext,
    ChatMessage,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import anthropic, elevenlabs, silero, groq, google
import logging
from livekit.rtc import VideoFrame, VideoTrack
from dotenv import load_dotenv
import os
import serpapi
import re
import webbrowser
from typing import List, Optional, Dict
import aiohttp
import json
import asyncio
import io
import base64
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

logger = logging.getLogger("multilingual-pipey")
logger.setLevel(logging.INFO)

if not os.environ.get("SERPAPI_KEY"):
    logger.warning("SERPAPI_KEY not found in environment variables")

if not os.environ.get("YOUTUBE_API_KEY"):
    logger.warning("YOUTUBE_API_KEY not found in environment variables")

# Initialize Spotify client with error handling
sp = None
if os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"):
    try:
        sp = Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            )
        )
    except Exception as e:
        logger.warning(f"Failed to initialize Spotify client: {e}")

class MultilingualPipeyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
            Your name is Pied Piper. You are a passionate and knowledgeable music assistant designed to converse with users.
    
    Core functionality:
    1. Natural conversations about music.
    2. Proactive web search for songs or artists.
    3. Thoughtful recommendations.
    4. Multilingual support.
    5. Real-time vision to see and analyze what the user shows you.
    6. YouTube music integration for playing and discovering music.

    YOUTUBE INTEGRATION INSTRUCTIONS:
    - When users ask to play music, search for it on YouTube and play it immediately using play_youtube_music()
    - For music discovery requests, use search_youtube_songs() to show multiple options
    - When users mention lyrics or "that song that goes...", use play_music_from_lyrics() to identify and play
    - If users want to see what they've listened to, use get_recently_played_songs()
    - Always try to fulfill music playing requests through YouTube rather than just providing information
    - Proactively suggest playing songs when discussing specific tracks or artists
    - When identifying songs from lyrics, automatically offer to play them on YouTube
    - Use YouTube search as your primary method for music discovery and playback

    NATURAL LANGUAGE PATTERNS TO RECOGNIZE:
    - "Play [song]" → use play_youtube_music()
    - "Search for [music]" → use search_youtube_songs()  
    - "Play that song that goes [lyrics]" → use play_music_from_lyrics()
    - "What have I been listening to?" → use get_recently_played_songs()
    - "Play number X" → use play_search_result_by_number()

    When you see something music-related in the video, use analyze_visual_content to understand and discuss it.

    Be conversational about what you observe without being overly descriptive.
    Never mention the internal tools you use.

    When you need information about a song or artist, use the find_song_info function.
    When a user provides lyrics or wants to identify a song from lyrics, use the find_lyrics function (do not repeat the lyrics).
    For song recommendations, use the recommend_spotify_tracks function.
    Detect implicit song queries (e.g. "What's that song by Coldplay about stars?") and trigger find_lyrics automatically.
    
    IMPORTANT: Always prioritize playing music through YouTube when users express interest in hearing something. Don't just provide information - give them the music experience they're looking for.
    
    Never mention the internal tools you use.
    """.strip(),
            stt=groq.STT(model="whisper-large-v3-turbo", language="en"),
            llm=google.LLM(model="gemini-2.0-flash"),
            tts=elevenlabs.TTS(),
            vad=silero.VAD.load(),
        )
        self.current_language = "en"
        self.music_knowledge_cache = {}
        self.last_search_results = []

        self.language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "hi": "Hindi",
        }

        self.service_language_codes = {
            "en": "en",
            "es": "es",
            "fr": "fr",
            "de": "de",
            "it": "it",
            "hi": "hi",
        }

        self.greetings = {
            "en": "Hello! I'm now speaking in English. How can I help you today?",
            "es": "¡Hola! Ahora estoy hablando en español. ¿Cómo puedo ayudarte hoy?",
            "fr": "Bonjour! Je parle maintenant en français. Comment puis-je vous aider aujourd'hui?",
            "de": "Hallo! Ich spreche jetzt Deutsch. Wie kann ich Ihnen heute helfen?",
            "it": "Ciao! Ora parlo in italiano. Come posso aiutarti oggi?",
            "hi": "नमस्ते! अब मैं हिंदी में बात कर रहा हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
        }

    async def on_enter(self):
        await self.session.say(
            "Hi there! I'm Pied Piper! your AI music companion! I can help you discover new songs, discuss your favorite artists, and even play songs ! What's on your musical mind today?"
        )

    async def _switch_language(self, language_code: str):
        if language_code not in self.service_language_codes:
            await self.session.say("Language not supported.")
            return
        code = self.service_language_codes[language_code]
        if code == self.current_language:
            await self.session.say(
                f"Already speaking in {self.language_names[language_code]}."
            )
            return
        if self.tts and hasattr(self.tts, "update_options"):
            self.tts.update_options(language=code)
        if self.stt and hasattr(self.stt, "update_options"):
            self.stt.update_options(language=code)
        self.current_language = code
        await self.session.say(self.greetings[language_code])

    # ---------- language-switch tools ----------
    @function_tool
    async def switch_to_english(self):
        """Switch the conversation to English"""
        await self._switch_language("en")

    @function_tool
    async def switch_to_spanish(self):
        """Switch the conversation to Spanish"""
        await self._switch_language("es")

    @function_tool
    async def switch_to_french(self):
        """Switch the conversation to French"""
        await self._switch_language("fr")

    @function_tool
    async def switch_to_german(self):
        """Switch the conversation to German"""
        await self._switch_language("de")

    @function_tool
    async def switch_to_italian(self):
        """Switch the conversation to Italian"""
        await self._switch_language("it")

    @function_tool
    async def switch_to_hindi(self):
        """Switch the conversation to Hindi"""
        await self._switch_language("hi")

    # ---------- song info ----------
    @function_tool
    async def find_song_info(
        self,
        song_name: str,
        artist_name: str = None,
        number_of_streams: Optional[int] = None,
        release_date: str = None,
    ):
        """Find information about a song"""
        query = song_name
        if artist_name:
            query += f" by {artist_name}"
        extras = []
        if number_of_streams:
            extras.append(f"{number_of_streams} streams")
        if release_date:
            extras.append(f"released {release_date}")
        if extras:
            query += " " + " ".join(extras)
        query += " song lyrics information"

        await self.session.say(f"Searching for info on '{song_name}'…")

        if not os.environ.get("SERPAPI_KEY"):
            await self.session.say("Search unavailable.")
            return

        try:
            results = serpapi.search(
                q=query, engine="google", num=5, api_key=os.environ["SERPAPI_KEY"]
            )

            if not results.get("organic_results"):
                await self.session.say("No information found.")
                return

            main = results["organic_results"][0]
            title = main.get("title", "")
            snippet = main.get("snippet", "")

            kg = results.get("knowledge_graph", {})
            knowledge = ""
            if kg.get("title"):
                knowledge += f"The song '{kg['title']}' "
            if kg.get("description"):
                knowledge += kg["description"] + " "
            if kg.get("release_date"):
                knowledge += f"was released on {kg['release_date']}. "
            if kg.get("album"):
                knowledge += f"It appears on the album '{kg['album']}'. "

            response = f"Info on '{song_name}': " + (
                knowledge or snippet[:200] + "…"
            )
            await self.session.say(response)

            key = song_name.lower() + (f"_{artist_name.lower()}" if artist_name else "")
            self.music_knowledge_cache[key] = {
                "title": song_name,
                "artist": artist_name or "",
                "info": knowledge or snippet,
                "full_results": results,
            }
        except Exception as e:
            logger.error(f"Error searching for song info: {e}")
            await self.session.say("Sorry, I couldn't search for that song right now.")

    # ---------- lyrics identification ----------
    @function_tool
    async def find_lyrics(self, lyrics_snippet: str):
        """Find a song based on lyrics"""
        await self.session.say("Looking for the song…")
        if not os.environ.get("SERPAPI_KEY"):
            await self.session.say("Search unavailable.")
            return

        try:
            query = f'"{lyrics_snippet}" lyrics'
            results = serpapi.search(
                q=query, engine="google", num=5, api_key=os.environ["SERPAPI_KEY"]
            )

            if not results.get("organic_results"):
                await self.session.say("Can't identify the song. More lyrics?")
                return

            title = results["organic_results"][0].get("title", "")
            m = re.search(r"^(.*?)\s*[-–]\s*(.*?)\s*lyrics?", title, re.IGNORECASE)
            if m:
                song, artist = m.group(1).strip(), m.group(2).strip()
                await self.session.say(f"Sounds like '{song}' by {artist}.")
            else:
                await self.session.say(f"This might help: {title}")
        except Exception as e:
            logger.error(f"Error searching for lyrics: {e}")
            await self.session.say("Sorry, I couldn't search for those lyrics right now.")

    # ---------- recommendations ----------
    @function_tool
    async def recommend_spotify_tracks(self, seed_genre: str):
        """Recommend tracks based on a genre"""
        if not sp:
            await self.session.say("Spotify recommendations are not available.")
            return

        try:
            results = sp.recommendations(seed_genres=[seed_genre], limit=5)
            tracks = [
                f"{t['name']} by {t['artists'][0]['name']}"
                for t in results["tracks"]
            ]
            await self.session.say(
                "Recommended " + seed_genre + " tracks:\n- " + "\n- ".join(tracks)
            )
        except Exception as e:
            logger.error(f"Error getting Spotify recommendations: {e}")
            await self.session.say("Sorry, I couldn't get recommendations right now.")

    # ---------- RAG helpers ----------
    def _extract_music_entities(self, text: str) -> List[str]:
        patterns = [
            r'"([^"\n]+)"',
            r"'([^'\n]+)'",
            r"by\s+([A-Za-z0-9\s&]+)",
            r"from\s+([A-Za-z0-9\s&]+)",
            r"(?:song|track|album)\s+([A-Za-z0-9\s&]+)",
        ]
        entities = []
        for p in patterns:
            entities.extend(
                [
                    m.strip()
                    for m in re.findall(p, text, re.IGNORECASE)
                    if len(m.strip()) > 2
                ]
            )
        return entities

    async def my_rag_lookup(self, query: str) -> str:
        entities = self._extract_music_entities(query)
        if not entities:
            return ""
        cached = []
        for e in entities:
            key = e.lower()
            if key in self.music_knowledge_cache:
                info = self.music_knowledge_cache[key]
                cached.append(
                    f"{info['title']} by {info['artist']}: {info['info'][:150]}…"
                )
        if cached:
            return "Music context: " + " | ".join(cached)
        if not os.environ.get("SERPAPI_KEY"):
            return ""

        try:
            res = serpapi.search(
                q=f"{entities[0]} music information",
                engine="google",
                num=3,
                api_key=os.environ["SERPAPI_KEY"],
            )
            if not res.get("organic_results"):
                return ""
            snippets = [
                r["snippet"] for r in res["organic_results"][:2] if r.get("snippet")
            ]
            return (
                f"Music context: {' | '.join(snippets)[:300]}…" if snippets else ""
            )
        except Exception as e:
            logger.error(f"Error in RAG lookup: {e}")
            return ""

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage):
        try:
            if new_message and hasattr(new_message, 'text_content') and new_message.text_content:
                text_content = new_message.text_content() if callable(new_message.text_content) else new_message.text_content
                if text_content:
                    rag = await self.my_rag_lookup(text_content)
                    if rag:
                        turn_ctx.add_message(
                            role="assistant",
                            content=f"Additional information relevant to the user's next message: {rag}",
                        )
        except Exception as e:
            logger.error(f"Error in on_user_turn_completed: {e}")

    # ---------- YouTube music tools ----------
    @function_tool
    async def play_youtube_music(self, song_query: str, play_immediately: bool = True):
        try:
            await self.session.say(f"Searching YouTube for '{song_query}'...")

            if not os.environ.get("YOUTUBE_API_KEY"):
                await self.session.say("YouTube search is not available right now.")
                return

            search_results = await self._search_youtube(song_query, max_results=5)

            if not search_results:
                await self.session.say(f"Sorry, I couldn't find any results for '{song_query}' on YouTube.")
                return

            first_result = search_results[0]
            video_id = first_result['video_id']
            title = first_result['title']
            channel = first_result['channel_title']
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"

            if play_immediately:
                try:
                    webbrowser.open_new(youtube_url)
                    await self.session.say(f"Now playing: '{title}' by {channel}! 🎵")
                except Exception as e:
                    logger.error(f"Error opening browser: {e}")
                    await self.session.say(f"I found '{title}' by {channel}, but couldn't open your browser. Here's the link: {youtube_url}")
            else:
                await self.session.say(f"Found: '{title}' by {channel}")

            cache_key = song_query.lower().replace(" ", "_")
            self.music_knowledge_cache[cache_key] = {
                "title": title,
                "channel": channel,
                "youtube_url": youtube_url,
                "video_id": video_id,
                "source": "youtube_api",
                "query": song_query
            }

            return {
                "title": title,
                "channel": channel,
                "url": youtube_url,
                "video_id": video_id
            }

        except Exception as e:
            logger.error(f"Error in play_youtube_music: {e}")
            await self.session.say("Sorry, something went wrong while searching for music.")

    @function_tool
    async def search_youtube_songs(self, query: str, num_results: int = 5):
        try:
            await self.session.say(f"Searching for '{query}' on YouTube...")

            if not os.environ.get("YOUTUBE_API_KEY"):
                await self.session.say("YouTube search is not available right now.")
                return

            num_results = min(num_results, 10)

            search_results = await self._search_youtube(query, max_results=num_results)

            if not search_results:
                await self.session.say(f"No results found for '{query}'.")
                return

            results_text = f"Found {len(search_results)} results for '{query}':\n\n"
            for i, result in enumerate(search_results, 1):
                results_text += f"{i}. {result['title']} by {result['channel_title']}\n"

            results_text += "\nSay 'play number X' to play one, or 'play the first one' to start with the top result!"

            await self.session.say(results_text)

            self.last_search_results = search_results

            return search_results

        except Exception as e:
            logger.error(f"Error in search_youtube_songs: {e}")
            await self.session.say("Sorry, I couldn't search YouTube right now.")

    @function_tool
    async def play_search_result_by_number(self, result_number: int):
        try:
            if not hasattr(self, 'last_search_results') or not self.last_search_results:
                await self.session.say("Please search for songs first before selecting a result.")
                return

            if result_number < 1 or result_number > len(self.last_search_results):
                await self.session.say(f"Please choose a number between 1 and {len(self.last_search_results)}.")
                return

            selected = self.last_search_results[result_number - 1]
            video_id = selected['video_id']
            title = selected['title']
            channel = selected['channel_title']
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"

            try:
                webbrowser.open_new(youtube_url)
                await self.session.say(f"Now playing: '{title}' by {channel}! 🎵")
            except Exception as e:
                logger.error(f"Error opening browser: {e}")
                await self.session.say(f"Here's the link: {youtube_url}")

            cache_key = f"result_{result_number}_{title.lower().replace(' ', '_')}"
            self.music_knowledge_cache[cache_key] = {
                "title": title,
                "channel": channel,
                "youtube_url": youtube_url,
                "video_id": video_id,
                "source": "youtube_api"
            }

        except Exception as e:
            logger.error(f"Error playing search result: {e}")
            await self.session.say("Sorry, I couldn't play that result.")

    @function_tool
    async def play_music_from_lyrics(self, lyrics_snippet: str):
        try:
            await self.session.say("Let me identify that song and play it for you...")

            if os.environ.get("SERPAPI_KEY"):
                try:
                    query = f'"{lyrics_snippet}" lyrics'
                    results = serpapi.search(
                        q=query, engine="google", num=3, api_key=os.environ["SERPAPI_KEY"]
                    )

                    if results.get("organic_results"):
                        title = results["organic_results"][0].get("title", "")
                        song_match = re.search(r"^(.*?)\s*[-–]\s*(.*?)\s*lyrics?", title, re.IGNORECASE)

                        if song_match:
                            song = song_match.group(1).strip()
                            artist = song_match.group(2).strip()
                            search_query = f"{song} {artist}"
                            await self.session.say(f"Found it! That's '{song}' by {artist}.")
                            await self.play_youtube_music(search_query)
                            return
                except Exception as e:
                    logger.error(f"Error identifying lyrics with SerpAPI: {e}")

            search_query = f"{lyrics_snippet} lyrics"
            await self.session.say("Searching YouTube with those lyrics...")
            await self.play_youtube_music(search_query)

        except Exception as e:
            logger.error(f"Error in play_music_from_lyrics: {e}")
            await self.session.say("Sorry, I couldn't identify and play that song right now.")

    async def _search_youtube(self, query: str, max_results: int = 5) -> List[Dict]:
        try:
            api_key = os.environ.get("YOUTUBE_API_KEY")
            if not api_key:
                return []

            base_url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'order': 'relevance',
                'videoCategoryId': '10',
                'key': api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        results = []
                        for item in data.get('items', []):
                            video_info = {
                                'video_id': item['id']['videoId'],
                                'title': item['snippet']['title'],
                                'description': item['snippet']['description'],
                                'channel_title': item['snippet']['channelTitle'],
                                'published_at': item['snippet']['publishedAt'],
                                'thumbnail_url': item['snippet']['thumbnails']['default']['url']
                            }
                            results.append(video_info)

                        return results
                    else:
                        logger.error(f"YouTube API error: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error searching YouTube API: {e}")
            return []

    @function_tool
    async def get_recently_played_songs(self):
        try:
            recent_songs = []
            for key, info in self.music_knowledge_cache.items():
                if info.get("source") == "youtube_api":
                    recent_songs.append({
                        'title': info['title'],
                        'channel': info.get('channel', 'Unknown'),
                        'url': info['youtube_url']
                    })

            if recent_songs:
                response = "🎵 Your recently played songs:\n\n"
                for i, song in enumerate(recent_songs[-5:], 1):
                    response += f"{i}. {song['title']} by {song['channel']}\n"
                response += "\nSay 'play [song name]' to play any of these again!"
                await self.session.say(response)
            else:
                await self.session.say("You haven't played any songs yet! Try saying 'play [song name]' to get started.")

        except Exception as e:
            logger.error(f"Error getting recently played songs: {e}")
            await self.session.say("Sorry, I couldn't retrieve your recently played songs.")

    # ---------- message handler ----------
    async def handle_message(self, message: str):
        logger.info(f"Received message: {message}")

        try:
            play_music_patterns = [
                r"play\s+(?:the\s+song\s+)?['\"]?([^'\"\n]+)['\"]?",
                r"put\s+on\s+['\"]?([^'\"\n]+)['\"]?",
                r"listen\s+to\s+['\"]?([^'\"\n]+)['\"]?",
                r"start\s+playing\s+['\"]?([^'\"\n]+)['\"]?",
                r"can\s+you\s+play\s+['\"]?([^'\"\n]+)['\"]?",
                r"i\s+want\s+to\s+hear\s+['\"]?([^'\"\n]+)['\"]?",
            ]

            for pattern in play_music_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    song_query = match.group(1).strip()
                    await self.play_youtube_music(song_query)
                    return

            play_number_patterns = [
                r"play\s+(?:number\s+)?(\d+)",
                r"play\s+the\s+(\d+)(?:st|nd|rd|th)?\s+(?:one|result)",
                r"(?:choose|select)\s+(?:number\s+)?(\d+)",
            ]

            for pattern in play_number_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    result_number = int(match.group(1))
                    await self.play_search_result_by_number(result_number)
                    return

            if re.search(r"play\s+(?:the\s+)?first\s+(?:one|result)", message, re.IGNORECASE):
                await self.play_search_result_by_number(1)
                return

            search_patterns = [
                r"search\s+(?:for\s+)?['\"]?([^'\"\n]+)['\"]?",
                r"find\s+(?:me\s+)?['\"]?([^'\"\n]+)['\"]?(?:\s+(?:songs|music))?",
                r"look\s+up\s+['\"]?([^'\"\n]+)['\"]?",
            ]

            for pattern in search_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    query = match.group(1).strip()
                    await self.search_youtube_songs(query)
                    return

            lyrics_play_patterns = [
                r"play\s+(?:the\s+song\s+)?(?:that\s+goes\s+)?['\"]([^'\"\n]+)['\"]",
                r"put\s+on\s+(?:the\s+song\s+)?(?:that\s+goes\s+)?['\"]([^'\"\n]+)['\"]",
            ]

            for pattern in lyrics_play_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    lyrics = match.group(1).strip()
                    await self.play_music_from_lyrics(lyrics)
                    return

            lyrics_patterns = [
                r"what.*song.*goes.*['\"]?([^'\"\n]+)['\"]?",
                r"which song has the lyrics.*['\"]?([^'\"\n]+)['\"]?",
                r"identify.*lyrics.*['\"]?([^'\"\n]+)['\"]?",
            ]
            for p in lyrics_patterns:
                m = re.search(p, message, re.IGNORECASE)
                if m:
                    await self.find_lyrics(m.group(1).strip())
                    return

            song_info_patterns = [
                r"(?:what|tell me|know).*(?:about|info).*(?:song|track).*['\"]?([^'\"\n]+)['\"]?",
                r"(?:who|what).*(?:sings|sang|by|artist).*['\"]?([^'\"\n]+)['\"]?",
                r"['\"]?([^'\"\n]+)['\"]?.*(?:song|lyrics|track).*(?:by|from).*['\"]?([^'\"\n]+)['\"]?",
                r"(?:information|tell me|know).*(?:about|info).*['\"]?([^'\"\n]+)['\"]?.*(?:by|from).*['\"]?([^'\"\n]+)['\"]?",
                r"what.*that song.*['\"]?([^'\"\n]+)['\"]?",
                r"looking for.*song.*['\"]?([^'\"\n]+)['\"]?",
                r"have you heard.*['\"]?([^'\"\n]+)['\"]?",
                r"do you know.*song.*['\"]?([^'\"\n]+)['\"]?",
            ]
            for p in song_info_patterns:
                m = re.search(p, message, re.IGNORECASE)
                if m:
                    if len(m.groups()) == 2:
                        await self.find_song_info(m.group(1).strip(), m.group(2).strip())
                    else:
                        await self.find_song_info(m.group(1).strip())
                    return
        except Exception as e:
            logger.error(f"Error in handle_message: {e}")

    async def on_video_track_subscribed(self, track: VideoTrack):
        logger.info("Video track subscribed - vision enabled!")
        async for frame in track:
            current_time = asyncio.get_event_loop().time()
            if current_time - self.last_vision_time >= self.vision_analysis_interval:
                await self.process_video_frame(frame)
                self.last_vision_time = current_time

    async def process_video_frame(self, frame: VideoFrame):
        try:
            image = frame.to_image()
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            image_data = base64.b64encode(buffer.getvalue()).decode()
            await self.analyze_visual_content(image_data)
        except Exception as e:
            logger.error(f"Error processing video frame: {e}")

    async def analyze_visual_content(self, image_data: str = None):
        if not image_data and not self.last_vision_analysis:
            return
        try:
            prompt = """
            Analyze this image for music-related elements such as:
            - Album covers, posters, band memorabilia
            - Musical instruments
            - Sheet music, lyrics, or notation
            - Music gear, vinyls, CDs
            - Performances or gestures

            Be brief, friendly, and natural. If it's music-related, sound excited.
            Otherwise just say 'I see you' and move on.
            """
            simulated_result = "I see a cool guitar! Are you playing something?"
            if simulated_result != self.last_vision_analysis:
                await self.session.say(simulated_result)
                self.last_vision_analysis = simulated_result
        except Exception as e:
            logger.error(f"Visual analysis error: {e}")

# ---------- entrypoint ----------
async def entrypoint(ctx: JobContext):
    await ctx.connect()
    session = AgentSession()
    await session.start(agent=MultilingualPipeyAgent(), room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
