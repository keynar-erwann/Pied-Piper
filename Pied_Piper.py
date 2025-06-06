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
from livekit.plugins import anthropic, elevenlabs, silero, groq
import logging
from dotenv import load_dotenv
import os
import serpapi
import re
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
2. YouTube music integration for embedding and discovering music.
3. Song identification from lyrics using find_lyrics()
4. Music information lookup using find_song_info()
5. Multilingual support.
- When users ask to play music, search for it on YouTube and embed it in their interface using play_youtube_music()
- For music discovery requests, use search_youtube_songs() to show multiple options
- When users mention lyrics or "that song that goes...", use play_music_from_lyrics() to identify and play
- If users want to see what they've listened to, use get_recently_played_songs()
- If the user just wants music information, use find_song_info()
IMPORTANT: You embed YouTube videos directly in the user's interface, not open them in new tabs.
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
        self.recently_played = []  # ✅ ADDED: Track recently played songs
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
        try:
            await self.session.say(
                "Hi there! I'm Pied Piper, your AI music companion! I can help you discover new songs, discuss your favorite artists, and embed music videos right here in your interface! What's on your musical mind today?"
            )
        except Exception as e:
            logger.error(f"Error in on_enter: {e}")
            await self.session.say("Hello! I encountered an error during startup but I'm ready to help you with music!")
    async def _send_youtube_embed(self, video_id: str, title: str, channel: str) -> bool:
        """Send YouTube video ID to frontend for embedding"""
        if not all([video_id, title, channel]):
            logger.error("Missing required parameters for YouTube embed")
            return False
        try:
            if not (hasattr(self, 'session') and hasattr(self.session, 'room')):
                logger.error("No session or room available to send data")
                return False
            message_data = {
                'type': 'youtube_embed',
                'videoId': video_id,
                'title': title,
                'channel': channel,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            await self.session.room.local_participant.publish_data(
                json.dumps(message_data).encode(),
                reliable=True
            )
            
            logger.info(f"✅ Sent YouTube embed data: {video_id} - {title}")
            return True
        except (AttributeError, json.JSONEncodeError) as e:
            logger.error(f"Data formatting error in _send_youtube_embed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in _send_youtube_embed: {e}")
            return False
    async def _switch_language(self, language_code: str):
        try:
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
        except KeyError as e:
            logger.error(f"Invalid language code or missing greeting: {e}")
            await self.session.say("Sorry, there was an error switching languages.")
        except Exception as e:
            logger.error(f"Error in _switch_language: {e}")
            await self.session.say("Sorry, I couldn't switch languages right now.")
    @function_tool
    async def switch_to_english(self):
        """Switch the conversation to English"""
        try:
            await self._switch_language("en")
        except Exception as e:
            logger.error(f"Error switching to English: {e}")
            await self.session.say("Sorry, I couldn't switch to English.")
    @function_tool
    async def switch_to_spanish(self):
        """Switch the conversation to Spanish"""