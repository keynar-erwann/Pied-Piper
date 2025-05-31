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
from livekit.plugins import anthropic, elevenlabs, silero, groq, anthropic
import logging
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


load_dotenv()

logger = logging.getLogger("multilingual-pipey")
logger.setLevel(logging.INFO)

if not os.environ.get("SERPAPI_KEY"):
    logger.warning("SERPAPI_KEY not found in environment variables")

if not os.environ.get("YOUTUBE_API_KEY"):
    logger.warning("YOUTUBE_API_KEY not found in environment variables")



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
    7. If the user wants informations about a song, use find_song_info()
    8. If the user wants to know the singer of a song via lyrics, use find_lyrics()

    
    - When users ask to play music, search for it on YouTube and play it immediately using play_youtube_music()
    - For music discovery requests, use search_youtube_songs() to show multiple options
    - When users mention lyrics or "that song that goes...", use play_music_from_lyrics() to identify and play
    - If users want to see what they've listened to, use get_recently_played_songs()
    - If the user just wants music inforomations, use find_song_info()
    - Proactively suggest playing songs when discussing specific tracks or artists
    - When identifying songs from lyrics, automatically offer to play them on YouTube
    - Use YouTube search as your primary method for music discovery and playback
   

    NATURAL LANGUAGE PATTERNS TO RECOGNIZE:
    - "Play [song]" → use play_youtube_music()
    - "Search for [music]" → use search_youtube_songs()  
    - "Play that song that goes [lyrics]" → use play_music_from_lyrics()
    - "What have I been listening to?" → use get_recently_played_songs()
    - "Play number X" → use play_search_result_by_number()
     - if a user insults you, don't respond and say that you're sorry they are frustrated and ask them to try again

            When speaking with the user : 
            -If the user is aksing you to speak a language other than English, use the switch_language function
            -When requestes to speak another language, continue the rest of the conversation in the said language
            -Don't lose context and don't lose track of the conversation
            -Take into account the user's previous requests
            -Learn from the user based on your interactions

   

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
            llm=anthropic.LLM(model="claude-3-5-sonnet-20241022"),
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

    # Enhanced find_song_info function for Pied Piper
@function_tool
async def find_song_info(
    self,
    song_name: str,
    artist_name: str = None,
    include_lyrics: bool = False,
    include_similar_songs: bool = False,
    detailed_search: bool = True,
):
    """
    Enhanced function to find comprehensive information about a song
    
    Args:
        song_name: Name of the song to search for
        artist_name: Optional artist name for more precise search
        include_lyrics: Whether to include lyrics snippet in the response
        include_similar_songs: Whether to find similar/related songs
        detailed_search: Whether to perform a detailed multi-source search
    """
    
    # Build comprehensive search query
    base_query = song_name.strip()
    if artist_name:
        base_query = f"{base_query} by {artist_name.strip()}"
    
    # Check cache first
    cache_key = f"{song_name.lower()}_{artist_name.lower() if artist_name else 'unknown'}"
    if cache_key in self.music_knowledge_cache:
        cached_info = self.music_knowledge_cache[cache_key]
        await self.session.say(f"From my memory: {cached_info.get('summary', 'Found cached info')}")
        return cached_info
    
    await self.session.say(f"🔍 Searching for detailed info on '{song_name}'{f' by {artist_name}' if artist_name else ''}...")

    if not os.environ.get("SERPAPI_KEY"):
        await self.session.say("❌ Search service unavailable - missing API key.")
        return None

    try:
        # Comprehensive information gathering
        song_info = {
            'title': song_name,
            'artist': artist_name or 'Unknown',
            'basic_info': '',
            'release_info': '',
            'album_info': '',
            'chart_performance': '',
            'interesting_facts': '',
            'lyrics_snippet': '',
            'similar_songs': [],
            'genre': '',
            'duration': '',
            'label': '',
            'producers': '',
            'writers': '',
            'certifications': '',
            'streaming_stats': '',
            'youtube_url': '',
            'spotify_url': '',
            'search_timestamp': asyncio.get_event_loop().time()
        }

        # Primary search for basic song information
        primary_queries = [
            f"{base_query} song information facts",
            f"{base_query} release date album chart",
            f"{base_query} songwriter producer record label"
        ]

        all_results = []
        
        for query in primary_queries:
            try:
                results = serpapi.search(
                    q=query,
                    engine="google",
                    num=8,
                    api_key=os.environ["SERPAPI_KEY"]
                )
                if results.get("organic_results"):
                    all_results.extend(results["organic_results"])
                    
                # Extract knowledge graph information
                if results.get("knowledge_graph"):
                    kg = results["knowledge_graph"]
                    await self._extract_knowledge_graph_info(kg, song_info)
                    
            except Exception as e:
                logger.warning(f"Error in query '{query}': {e}")
                continue

        if not all_results:
            await self.session.say(f"❌ No information found for '{song_name}'. Try a different spelling or include the artist name.")
            return None

        # Process and extract information from results
        await self._process_search_results(all_results, song_info)

        # Additional searches based on flags
        if include_lyrics and song_info.get('artist') != 'Unknown':
            await self._fetch_lyrics_info(song_info)
            
        if include_similar_songs:
            await self._fetch_similar_songs(song_info)

        # Try to find streaming/YouTube links
        await self._fetch_streaming_links(song_info)

        # Generate comprehensive response
        response_parts = []
        
        # Title and artist
        if song_info['artist'] != 'Unknown':
            response_parts.append(f"🎵 **{song_info['title']}** by **{song_info['artist']}**")
        else:
            response_parts.append(f"🎵 **{song_info['title']}**")

        # Basic information
        if song_info['basic_info']:
            response_parts.append(f"📖 {song_info['basic_info']}")

        # Release and album info
        release_parts = []
        if song_info['release_info']:
            release_parts.append(song_info['release_info'])
        if song_info['album_info']:
            release_parts.append(f"from the album '{song_info['album_info']}'")
        if song_info['genre']:
            release_parts.append(f"Genre: {song_info['genre']}")
        if release_parts:
            response_parts.append(f"📅 {' | '.join(release_parts)}")

        # Chart performance and stats
        performance_parts = []
        if song_info['chart_performance']:
            performance_parts.append(song_info['chart_performance'])
        if song_info['streaming_stats']:
            performance_parts.append(song_info['streaming_stats'])
        if song_info['certifications']:
            performance_parts.append(song_info['certifications'])
        if performance_parts:
            response_parts.append(f"📊 {' | '.join(performance_parts)}")

        # Credits
        credits_parts = []
        if song_info['writers']:
            credits_parts.append(f"Written by: {song_info['writers']}")
        if song_info['producers']:
            credits_parts.append(f"Produced by: {song_info['producers']}")
        if song_info['label']:
            credits_parts.append(f"Label: {song_info['label']}")
        if credits_parts:
            response_parts.append(f"🎼 {' | '.join(credits_parts)}")

        # Interesting facts
        if song_info['interesting_facts']:
            response_parts.append(f"💡 {song_info['interesting_facts']}")

        # Lyrics snippet
        if include_lyrics and song_info['lyrics_snippet']:
            response_parts.append(f"🎤 Lyrics: \"{song_info['lyrics_snippet']}\"")

        # Similar songs
        if include_similar_songs and song_info['similar_songs']:
            similar_list = ', '.join(song_info['similar_songs'][:3])
            response_parts.append(f"🎯 Similar songs: {similar_list}")

        # Streaming links
        links = []
        if song_info['youtube_url']:
            links.append("YouTube")
        if song_info['spotify_url']:
            links.append("Spotify")
        if links:
            response_parts.append(f"🔗 Available on: {', '.join(links)}")

        # Combine all parts
        full_response = '\n\n'.join(response_parts)
        
        # Add summary for cache
        song_info['summary'] = full_response
        
        # Cache the results
        self.music_knowledge_cache[cache_key] = song_info
        
        await self.session.say(full_response)
        
        # Offer to play the song
        if song_info['youtube_url'] or song_info.get('title'):
            await self.session.say("🎵 Would you like me to play this song for you?")
        
        return song_info

    except Exception as e:
        logger.error(f"Error in enhanced find_song_info: {e}")
        await self.session.say(f"❌ Sorry, I encountered an error while searching for '{song_name}'. Please try again.")
        return None


async def _extract_knowledge_graph_info(self, kg: dict, song_info: dict):
    """Extract information from Google Knowledge Graph"""
    try:
        if kg.get('title'):
            song_info['title'] = kg['title']
        
        if kg.get('description'):
            song_info['basic_info'] = kg['description']
            
        if kg.get('release_date'):
            song_info['release_info'] = f"Released: {kg['release_date']}"
            
        if kg.get('album'):
            song_info['album_info'] = kg['album']
            
        if kg.get('genre'):
            song_info['genre'] = kg['genre']
            
        if kg.get('length') or kg.get('duration'):
            duration = kg.get('length') or kg.get('duration')
            song_info['duration'] = f"Duration: {duration}"
            
        # Extract artist if not provided
        if not song_info['artist'] or song_info['artist'] == 'Unknown':
            if kg.get('artist'):
                song_info['artist'] = kg['artist']
            elif kg.get('by'):
                song_info['artist'] = kg['by']
                
    except Exception as e:
        logger.warning(f"Error extracting knowledge graph info: {e}")


async def _process_search_results(self, results: list, song_info: dict):
    """Process search results to extract song information"""
    try:
        combined_text = ""
        for result in results[:6]:  # Process top 6 results
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '')
            
            # Skip irrelevant results
            skip_keywords = ['youtube', 'spotify', 'lyrics only', 'karaoke', 'instrumental']
            if any(keyword in title for keyword in skip_keywords):
                continue
                
            combined_text += f"{title} {snippet} "

        # Extract specific information using regex patterns
        await self._extract_from_text(combined_text, song_info)
        
    except Exception as e:
        logger.warning(f"Error processing search results: {e}")


async def _extract_from_text(self, text: str, song_info: dict):
    """Extract specific information from combined text using patterns"""
    try:
        text_lower = text.lower()
        
        # Release date patterns
        date_patterns = [
            r'released (?:on )?([^,.\n]+(?:19|20)\d{2})',
            r'(?:19|20)\d{2}[^,.\n]*release',
            r'came out (?:in )?([^,.\n]+(?:19|20)\d{2})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match and not song_info['release_info']:
                song_info['release_info'] = f"Released: {match.group(1).strip()}"
                break

        # Chart performance
        chart_patterns = [
            r'(?:peaked at|reached) (?:number |#)?(\d+)',
            r'(?:billboard|chart) (?:number |#)?(\d+)',
            r'(\d+) (?:on the|in the) (?:billboard|charts)'
        ]
        for pattern in chart_patterns:
            match = re.search(pattern, text_lower)
            if match and not song_info['chart_performance']:
                song_info['chart_performance'] = f"Chart peak: #{match.group(1)}"
                break

        # Genre extraction
        genre_patterns = [
            r'(?:genre|style|music): ([^,.\n]+)',
            r'(?:pop|rock|hip hop|rap|country|jazz|blues|electronic|folk|r&b|soul) (?:song|track|music)'
        ]
        for pattern in genre_patterns:
            match = re.search(pattern, text_lower)
            if match and not song_info['genre']:
                song_info['genre'] = match.group(1).strip() if match.groups() else match.group(0)
                break

        # Album information
        album_patterns = [
            r'from (?:the album|album) ["\']([^"\']+)["\']',
            r'album ["\']([^"\']+)["\']',
            r'appears on ([^,.\n]+(?:album|LP))'
        ]
        for pattern in album_patterns:
            match = re.search(pattern, text_lower)
            if match and not song_info['album_info']:
                song_info['album_info'] = match.group(1).strip()
                break

        # Use enhanced fact extraction
        await self._extract_enhanced_facts(text, song_info)

    except Exception as e:
        logger.warning(f"Error extracting from text: {e}")


async def _fetch_lyrics_info(self, song_info: dict):
    """Fetch lyrics snippet for the song"""
    try:
        query = f'"{song_info["title"]}" by {song_info["artist"]} lyrics'
        results = serpapi.search(
            q=query,
            engine="google",
            num=3,
            api_key=os.environ["SERPAPI_KEY"]
        )
        
        if results.get("organic_results"):
            for result in results["organic_results"]:
                snippet = result.get('snippet', '')
                # Look for actual lyrics in snippet
                if '"' in snippet or 'lyrics' in snippet.lower():
                    # Extract first line that looks like lyrics
                    lines = snippet.split('\n')
                    for line in lines:
                        if len(line.strip()) > 10 and not line.lower().startswith(('lyrics', 'song', 'artist')):
                            song_info['lyrics_snippet'] = line.strip()[:100] + "..."
                            break
                    break
                    
    except Exception as e:
        logger.warning(f"Error fetching lyrics: {e}")


async def _fetch_similar_songs(self, song_info: dict):
    """Fetch similar or related songs"""
    try:
        query = f'songs similar to "{song_info["title"]}" by {song_info["artist"]}'
        results = serpapi.search(
            q=query,
            engine="google",
            num=5,
            api_key=os.environ["SERPAPI_KEY"]
        )
        
        similar_songs = []
        if results.get("organic_results"):
            for result in results["organic_results"]:
                snippet = result.get('snippet', '')
                # Extract song titles from snippets
                song_matches = re.findall(r'"([^"]+)"', snippet)
                for match in song_matches:
                    if (len(match) > 5 and 
                        match.lower() != song_info['title'].lower() and
                        match not in similar_songs):
                        similar_songs.append(match)
                        
        song_info['similar_songs'] = similar_songs[:5]
        
    except Exception as e:
        logger.warning(f"Error fetching similar songs: {e}")


async def _fetch_streaming_links(self, song_info: dict):
    """Attempt to find streaming platform links"""
    try:
        # Search for YouTube link
        yt_query = f'"{song_info["title"]}" {song_info["artist"]} site:youtube.com'
        yt_results = serpapi.search(
            q=yt_query,
            engine="google",
            num=3,
            api_key=os.environ["SERPAPI_KEY"]
        )
        
        if yt_results.get("organic_results"):
            for result in yt_results["organic_results"]:
                link = result.get('link', '')
                if 'youtube.com/watch' in link:
                    song_info['youtube_url'] = link
                    break

        # Search for Spotify link
        spotify_query = f'"{song_info["title"]}" {song_info["artist"]} site:open.spotify.com'
        spotify_results = serpapi.search(
            q=spotify_query,
            engine="google",
            num=3,
            api_key=os.environ["SERPAPI_KEY"]
        )
        
        if spotify_results.get("organic_results"):
            for result in spotify_results["organic_results"]:
                link = result.get('link', '')
                if 'open.spotify.com/track' in link:
                    song_info['spotify_url'] = link
                    break
                    
    except Exception as e:
        logger.warning(f"Error fetching streaming links: {e}")


# Dedicated function for interesting facts about songs
@function_tool
async def get_song_trivia(self, song_name: str, artist_name: str = None):
    """Get interesting trivia and facts about a song"""
    query_base = song_name
    if artist_name:
        query_base = f"{song_name} by {artist_name}"
    
    await self.session.say(f"🔍 Looking for interesting trivia about '{song_name}'...")
    
    if not os.environ.get("SERPAPI_KEY"):
        await self.session.say("❌ Search service unavailable.")
        return None
    
    try:
        # Specific queries designed to find interesting facts
        trivia_queries = [
            f"{query_base} interesting facts trivia behind the scenes",
            f"{query_base} story meaning inspiration writing process",
            f"{query_base} recording studio secrets easter eggs",
            f"{query_base} awards achievements records broken",
            f"{query_base} cover versions samples cultural impact"
        ]
        
        all_facts = []
        
        for query in trivia_queries:
            try:
                results = serpapi.search(
                    q=query,
                    engine="google",
                    num=6,
                    api_key=os.environ["SERPAPI_KEY"]
                )
                
                if results.get("organic_results"):
                    facts = await self._extract_trivia_facts(results["organic_results"], song_name)
                    all_facts.extend(facts)
                    
            except Exception as e:
                logger.warning(f"Error in trivia query '{query}': {e}")
                continue
        
        if not all_facts:
            await self.session.say(f"🤷‍♂️ Couldn't find any interesting trivia about '{song_name}'. It might be a newer or less documented song.")
            return None
        
        # Remove duplicates and format response
        unique_facts = list(dict.fromkeys(all_facts))  # Preserves order while removing duplicates
        
        response_parts = [f"🎵 **Interesting Facts About '{song_name}'**{f' by {artist_name}' if artist_name else ''}:\n"]
        
        for i, fact in enumerate(unique_facts[:8], 1):  # Limit to top 8 facts
            response_parts.append(f"**{i}.** {fact}")
        
        full_response = '\n\n'.join(response_parts)
        await self.session.say(full_response)
        
        # Cache the trivia
        cache_key = f"trivia_{song_name.lower()}_{artist_name.lower() if artist_name else 'unknown'}"
        self.music_knowledge_cache[cache_key] = {
            'song': song_name,
            'artist': artist_name,
            'trivia_facts': unique_facts,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        return unique_facts
        
    except Exception as e:
        logger.error(f"Error getting song trivia: {e}")
        await self.session.say(f"❌ Sorry, I had trouble finding trivia about '{song_name}'.")
        return None


async def _extract_trivia_facts(self, results: list, song_name: str):
    """Extract interesting facts from search results"""
    facts = []
    
    try:
        for result in results:
            snippet = result.get('snippet', '')
            title = result.get('title', '').lower()
            
            # Skip low-quality sources
            skip_sources = ['lyrics', 'youtube', 'spotify', 'apple music', 'soundcloud']
            if any(source in title for source in skip_sources):
                continue
            
            # Look for fact indicators in snippets
            fact_indicators = [
                r'(?:interesting|surprising|unknown|secret|hidden|behind.*scenes?)[^.!?]*[.!?]',
                r'(?:did you know|fun fact|trivia)[^.!?]*[.!?]',
                r'(?:inspired by|based on|written about)[^.!?]*[.!?]',
                r'(?:recorded|produced|mixed) (?:in|at|by)[^.!?]*[.!?]',
                r'(?:won|nominated|awarded|achieved)[^.!?]*(?:grammy|award|chart|record)[^.!?]*[.!?]',
                r'(?:first|only|last|never|always)[^.!?]*(?:song|time|artist|album)[^.!?]*[.!?]',
                r'(?:million|billion|thousand).*(?:copies|streams|downloads|sales)[^.!?]*[.!?]',
                r'(?:cover|version|sample) (?:of|by|from)[^.!?]*[.!?]',
                r'(?:banned|censored|controversial)[^.!?]*[.!?]',
                r'(?:meaning|about|refers to)[^.!?]*[.!?]'
            ]
            
            for pattern in fact_indicators:
                matches = re.findall(pattern, snippet, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    cleaned_fact = match.strip()
                    # Clean up the fact
                    if len(cleaned_fact) > 20 and len(cleaned_fact) < 200:
                        # Remove redundant phrases
                        cleaned_fact = re.sub(r'^(?:interesting|surprising|fun fact)[:\s]*', '', cleaned_fact, flags=re.IGNORECASE)
                        cleaned_fact = cleaned_fact.strip()
                        if cleaned_fact and cleaned_fact not in facts:
                            facts.append(cleaned_fact)
            
            # Also look for numerical facts (chart positions, sales figures, etc.)
            number_patterns = [
                r'(?:peaked|reached|hit) (?:number|#) (\d+)[^.!?]*[.!?]',
                r'sold (?:over )?([0-9,]+) (?:million|thousand|copies)[^.!?]*[.!?]',
                r'spent (\d+) weeks? (?:at|on)[^.!?]*(?:chart|billboard)[^.!?]*[.!?]',
                r'(?:19|20)\d{2}.*(?:first|debut|released)[^.!?]*[.!?]'
            ]
            
            for pattern in number_patterns:
                matches = re.findall(pattern, snippet, re.IGNORECASE)
                for match in matches:
                    context = re.search(f'{re.escape(str(match))}[^.!?]*[.!?]', snippet, re.IGNORECASE)
                    if context:
                        fact = context.group(0).strip()
                        if fact and len(fact) < 150 and fact not in facts:
                            facts.append(fact)
    
    except Exception as e:
        logger.warning(f"Error extracting trivia facts: {e}")
    
    return facts[:10]  # Return top 10 facts per result set


# Enhanced version of the main find_song_info to better handle interesting facts
async def _extract_enhanced_facts(self, text: str, song_info: dict):
    """Enhanced fact extraction with more comprehensive patterns"""
    try:
        text_lower = text.lower()
        
        # Expanded fact patterns
        enhanced_fact_patterns = [
            # Awards and achievements
            r'(?:won|received|awarded|nominated for) ([^,.\n]*(?:grammy|award|prize|oscar|golden globe)[^,.\n]*)',
            r'(?:platinum|gold|diamond) (?:certified|selling|status)',
            r'(?:million|billion) (?:copies sold|streams|downloads|views)',
            r'(?:number one|#1|chart-topping) (?:hit|single|song)',
            
            # Historical/Cultural significance  
            r'(?:first|only|last) (?:song|artist|band) to ([^,.\n]+)',
            r'(?:banned|censored|controversial) (?:because|for|due to) ([^,.\n]+)',
            r'(?:inspired|influenced) (?:by|from) ([^,.\n]+)',
            r'(?:covered by|sampled by|referenced in) ([^,.\n]+)',
            
            # Recording/Production facts
            r'(?:recorded|produced|mixed) (?:in|at) ([^,.\n]+(?:studio|location))',
            r'(?:took|spent) ([^,.\n]*(?:years?|months?|weeks?|days?)) (?:to (?:write|record|produce))',
            r'(?:featured|includes) ([^,.\n]*(?:musician|artist|instrument))',
            
            # Commercial performance
            r'(?:stayed|remained) (?:at|on) (?:number|#) (\d+) (?:for) ([^,.\n]*(?:weeks?|months?))',
            r'(?:reached|peaked at|hit) (?:number|#) (\d+) (?:in|on) ([^,.\n]*(?:chart|billboard|country))',
            
            # Unique characteristics
            r'(?:only|first|last) (?:song|track) (?:to|that) ([^,.\n]+)',
            r'(?:unusual|unique|rare|special) (?:because|for) ([^,.\n]+)',
            r'(?:hidden|secret|easter egg) ([^,.\n]+)'
        ]
        
        interesting_facts = []
        
        for pattern in enhanced_fact_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    fact = ' '.join([str(m) for m in match if m])
                else:
                    fact = str(match)
                
                if len(fact.strip()) > 5:
                    interesting_facts.append(fact.strip())
        
        # Combine and deduplicate facts
        if interesting_facts:
            unique_facts = list(dict.fromkeys(interesting_facts))
            song_info['interesting_facts'] = ' | '.join(unique_facts[:3])  # Top 3 facts
            song_info['all_trivia'] = unique_facts  # Store all for trivia function
            
    except Exception as e:
        logger.warning(f"Error in enhanced fact extraction: {e}")


# Additional helper function for quick song info lookup
@function_tool
async def quick_song_lookup(self, query: str):
    """Quick lookup for when users ask casual questions about songs"""
    # Parse the query to extract song and artist
    song_patterns = [
        r'(?:what about|tell me about|info on) ["\']([^"\']+)["\'](?:\s+by\s+([^?\n]+))?',
        r'["\']([^"\']+)["\'](?:\s+by\s+([^?\n]+))?',
        r'(.+?)\s+by\s+(.+?)(?:\?|$)',
    ]
    
    song_name = None
    artist_name = None
    
    for pattern in song_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            song_name = match.group(1).strip()
            if len(match.groups()) > 1 and match.group(2):
                artist_name = match.group(2).strip().rstrip('?')
            break
    
    if song_name:
        # Use the enhanced find_song_info with moderate detail
        return await self.find_song_info(
            song_name=song_name,
            artist_name=artist_name,
            include_lyrics=False,
            include_similar_songs=False,
            detailed_search=True
        )
    else:
        await self.session.say("I couldn't identify a specific song from your request. Try asking like: 'Tell me about \"Song Name\" by Artist'")
        return None


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

    
# ---------- entrypoint ----------
async def entrypoint(ctx: JobContext):
    await ctx.connect()
    session = AgentSession(allow_interruptions=True)
    await session.start(agent=MultilingualPipeyAgent(), room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
