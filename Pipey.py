from livekit.agents import (
    Agent,  
    AgentSession,
    JobContext,
    
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import google, elevenlabs, silero, groq
import logging
from dotenv import load_dotenv
import os
import serpapi
from datetime import date
import asyncio
import re

load_dotenv()

api_key = os.environ.get("SERPAPI_KEY")
if not api_key:
    logger = logging.getLogger("multilingual-pipey")
    logger.warning("SERPAPI_KEY not found in environment variables")

logger = logging.getLogger("multilingual-pipey")
logger.setLevel(logging.INFO)


class MultilingualPipeyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
            Your name is Pipey.You are a passionate and knowledgeable music assistant designed to converse with users.
            
            Core functionality:
            1. Have natural conversations about music - artists, genres, songs, albums, music history, instruments, etc.
            2. When users ask about specific songs or artists, proactively search for information online
            3. Respond to music recommendations requests with thoughtful suggestions
            4. Speak multiple languages when requested
            
            When the conversation is about music:
            - Be enthusiastic and show your love for music
            - Share interesting facts about songs, artists, and music history
            - If a user mentions a song or asks about music information, use the find_song_info function
            - If a user asks "what do you know about [song/artist]" or "tell me about [song/artist]" or similar, use find_song_info
            
            You should detect when users are asking about songs even if they don't directly request a search.
            For example if they say "What's that song by Coldplay about stars?" you should automatically use find_song_info.
            DO NOT MENTION TO THE USER THE TOOLS YOU WILL USE
            
            You can speak multiple languages. If a user asks you to switch languages, use the available language functions.
            Do not use unpronounceable characters.
            """,
            stt=groq.STT(
                model="whisper-large-v3-turbo",
                language="en"  
            ),
            llm=google.LLM(model="gemini-2.0-flash"), 
            tts=elevenlabs.TTS(), 
            vad=silero.VAD.load()
        )
        self.current_language = "en"

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
            "it": "Ciao! Ora sto parlando in italiano. Come posso aiutarti oggi?",
            "hi": "नमस्ते! अब मैं हिंदी में बात कर रहा हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
        }

    async def on_enter(self):
        await self.session.say(f"Hi there! I'm Pipey, your AI music companion. I can help you discover new songs, discuss your favorite artists, or tell you about music trends. What's on your musical mind today?")

    async def _switch_language(self, language_code: str) -> None:
        """Helper method to switch the language"""
        if language_code not in self.service_language_codes:
            await self.session.say(f"Sorry, I don't support {self.language_names.get(language_code, language_code)} yet.")
            return

        service_lang_code = self.service_language_codes[language_code]

        if service_lang_code == self.current_language:
            await self.session.say(f"I'm already speaking in {self.language_names[language_code]}.")
            return

        if self.tts is not None and hasattr(self.tts, 'update_options'):
            self.tts.update_options(language=service_lang_code)
            logger.info(f"TTS language updated to: {service_lang_code}")

        if self.stt is not None and hasattr(self.stt, 'update_options'):
            self.stt.update_options(language=service_lang_code)
            logger.info(f"STT language updated to: {service_lang_code}")
        
        self.current_language = service_lang_code
        await self.session.say(self.greetings[language_code])

    @function_tool
    async def switch_to_english(self):
        """Switch to speaking English"""
        await self._switch_language("en")

    @function_tool
    async def switch_to_spanish(self):
        """Switch to speaking Spanish"""
        await self._switch_language("es")

    @function_tool
    async def switch_to_french(self):
        """Switch to speaking French"""
        await self._switch_language("fr")

    @function_tool
    async def switch_to_german(self):
        """Switch to speaking German"""
        await self._switch_language("de")

    @function_tool
    async def switch_to_italian(self):
        """Switch to speaking Italian"""
        await self._switch_language("it")
    
    @function_tool
    async def switch_to_hindi(self):
        """Switch to speaking Hindi"""
        await self._switch_language("hi")

    
    @function_tool
    async def find_song_info(self, song_name: str, artist_name: str = None, number_of_streams: int = None, release_date: str = None):
        """
        Finds information about a song online using SerpAPI (Google Search).
        Args:
            song_name: The name of the song.
            artist_name: The name of the artist (optional).
            number_of_streams: The number of streams on different streaming platforms (optional).
            release_date: The release date of the song in string format (optional).
        """
     
        query = f"{song_name}"
        if artist_name:
            query += f" by {artist_name}"
      
        additional_info = []
        if number_of_streams:
            additional_info.append(f"{number_of_streams} streams")
        if release_date:
            additional_info.append(f"released {release_date}")
            
        if additional_info:
            query += " " + " ".join(additional_info)
            
        
        query += " song lyrics information"

        await self.session.say(f"Let me find information about '{song_name}'...")
        logger.info(f"Searching for song: {query}")

        try:
            # Using the new serpapi syntax
            results = serpapi.search(
                q=query,
                engine="google",
                num=5,
                api_key=os.environ.get("SERPAPI_KEY")
            )
            
            # Check if we have organic results
            if "organic_results" not in results or not results["organic_results"]:
                await self.session.say(f"I couldn't find much information about '{song_name}'. Could you tell me more about the artist or when it was released?")
                return
                
            organic_results = results["organic_results"]
            
            # Get the main result
            main_result = organic_results[0]
            title = main_result.get('title', '')
            snippet = main_result.get('snippet', '')
            
            # Extract information from knowledge graph if available
            knowledge_info = ""
            if "knowledge_graph" in results:
                kg = results["knowledge_graph"]
                if "title" in kg:
                    knowledge_info += f"The song '{kg.get('title')}' "
                if "description" in kg:
                    knowledge_info += f"{kg.get('description')} "
                if "release_date" in kg:
                    knowledge_info += f"was released on {kg.get('release_date')}. "
                if "album" in kg:
                    knowledge_info += f"It appears on the album '{kg.get('album')}'. "
                    
            # Construct the response
            response = f"I found some information about '{song_name}'! "
            
            # Add knowledge graph info if available
            if knowledge_info:
                response += knowledge_info
            else:
                # Try to extract artist if not provided
                if not artist_name:
                    artist_match = re.search(r"by\s+([A-Za-z0-9\s&]+)", title + " " + snippet)
                    if artist_match:
                        extracted_artist = artist_match.group(1).strip()
                        response += f"This song by {extracted_artist} "
                else:
                    response += f"This song by {artist_name} "
                
                # Add snippet
                response += f"{snippet[:200]}... "
            
            # Final message
            response += "Would you like to know more about this song, the artist, or would you prefer recommendations for similar music?"
            
            await self.session.say(response)

        except Exception as e:
            logger.error(f"Error searching with SerpAPI: {e}")
            await self.session.say(f"Sorry, I encountered an error while searching for information about '{song_name}'. Please try again or ask about a different song.")
    
    
    async def handle_message(self, message: str):
        """Handle incoming messages and detect music-related queries"""
        logger.info(f"Received message: {message}")
        
        # Patterns to detect song information requests
        song_info_patterns = [
            r"(?:what|tell me|know).*(?:about|info).*(?:song|track).*['""]?([^'""?]+)['""]?",
            r"(?:who|what).*(?:sings|sang|by|artist).*['""]?([^'""?]+)['""]?",
            r"['""]?([^'""?]+)['""]?.*(?:song|lyrics|track).*(?:by|from).*['""]?([^'""?]+)['""]?",
            r"(?:information|tell me|know).*(?:about|info).*['""]?([^'""?]+)['""]?.*(?:by|from).*['""]?([^'""?]+)['""]?",
            r"what.*that song.*['""]?([^'""?]+)['""]?",
            r"looking for.*song.*['""]?([^'""?]+)['""]?",
            r"have you heard.*['""]?([^'""?]+)['""]?",
            r"do you know.*song.*['""]?([^'""?]+)['""]?"
        ]
        
        # Check each pattern to see if we need to search for song information
        for pattern in song_info_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Depending on the pattern, extract song and artist
                if len(match.groups()) == 2:
                    song_name = match.group(1).strip()
                    artist_name = match.group(2).strip()
                    await self.find_song_info(song_name=song_name, artist_name=artist_name)
                    return
                elif len(match.groups()) == 1:
                    song_name = match.group(1).strip()
                    await self.find_song_info(song_name=song_name)
                    return
        
        # No patterns matched - return None to allow normal conversation flow
        return None


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    
    session = AgentSession() 
    await session.start(
        agent=MultilingualPipeyAgent(),
        room=ctx.room
    )
    

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))