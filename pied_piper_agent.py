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
from dotenv import load_dotenv
import os
import serpapi
from datetime import date
import asyncio
import re
import aiohttp
from typing import Dict, Any, List, Optional

load_dotenv()

# Initialize logger before checking for SERPAPI_KEY to avoid NameError
logger = logging.getLogger("multilingual-pipey")
logger.setLevel(logging.INFO)

api_key = os.environ.get("SERPAPI_KEY")
if not api_key:
    logger.warning("SERPAPI_KEY not found in environment variables")


class MultilingualPipeyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
            Your name is Pied Piper.You are a passionate and knowledgeable music assistant designed to converse with users.
            
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
        self.music_knowledge_cache = {}  #

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
        await self.session.say(f"Hi there! I'm Pied Piper, your AI music companion. I can help you discover new songs, discuss your favorite artists, or tell you about music trends. What's on your musical mind today?")

    async def _switch_language(self, language_code: str) -> None:
        """Helper method to switch the language"""
        if language_code not in self.service_language_codes:
            await self.session.say(f"Sorry, I don't support {self.language_names.get(language_code, language_code)} yet.")
            return

        service_lang_code = self.service_language_codes[language_code]

        if service_lang_code == self.current_language:
            await self.session.say(f"I'm already speaking in {self.language_names[language_code]}.")
            return

        # Ensure tts and stt are not None before attempting to update options
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
            # Check if API key is available before making the call
            if not os.environ.get("SERPAPI_KEY"):
                await self.session.say("I'm sorry, I cannot perform searches right now as my search functionality is not configured.")
                return

            results = serpapi.search(
                q=query,
                engine="google",
                num=5,
                api_key=os.environ.get("SERPAPI_KEY")
            )
            
            
            if "organic_results" not in results or not results["organic_results"]:
                await self.session.say(f"I couldn't find much information about '{song_name}'. Could you tell me more about the artist or when it was released?")
                return
                
            organic_results = results["organic_results"]
            
            
            main_result = organic_results[0]
            title = main_result.get('title', '')
            snippet = main_result.get('snippet', '')
            
            
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
                    
           
            response = f"I found some information about '{song_name}'! "
            
           
            if knowledge_info:
                response += knowledge_info
            else:
               
                if not artist_name:
                    artist_match = re.search(r"by\s+([A-Za-z0-9\s&]+)", title + " " + snippet)
                    if artist_match:
                        extracted_artist = artist_match.group(1).strip()
                        response += f"This song by {extracted_artist} "
                else:
                    response += f"This song by {artist_name} "
                
               
                response += f"{snippet[:200]}... "
            
          
            response += "Would you like to know more about this song, the artist, or would you prefer recommendations for similar music?"
            
           
            cache_key = f"{song_name.lower()}"
            if artist_name:
                cache_key += f"_{artist_name.lower()}"
            
            self.music_knowledge_cache[cache_key] = {
                "title": song_name,
                "artist": artist_name or "",
                "info": knowledge_info or snippet,
                "full_results": results
            }
            
            await self.session.say(response)

        except Exception as e:
            logger.error(f"Error searching with SerpAPI: {e}")
            await self.session.say(f"Sorry, I encountered an error while searching for information about '{song_name}'. Please try again or ask about a different song.")
    
    async def my_rag_lookup(self, query: str) -> str:
        """
        Performs a RAG lookup based on the user's query to find relevant music information.
        
        Args:
            query: The user's message text
        
        Returns:
            A string containing relevant music information
        """
        logger.info(f"Performing RAG lookup for: {query}")
        
       
        music_entities = self._extract_music_entities(query)
        
        if not music_entities:
            return ""
            
        
        cached_info = []
        for entity in music_entities:
            entity_key = entity.lower()
            if entity_key in self.music_knowledge_cache:
                info = self.music_knowledge_cache[entity_key]
                cached_info.append(f"{info['title']} by {info['artist']}: {info['info'][:150]}...")
        
        if cached_info:
            return "Music context: " + " | ".join(cached_info)
            
       
        try:
            # Check if API key is available before making the call
            if not os.environ.get("SERPAPI_KEY"):
                logger.warning("SERPAPI_KEY not found, skipping RAG lookup.")
                return ""

            results = serpapi.search(
                q=f"{music_entities[0]} music information",
                engine="google",
                num=3,
                api_key=os.environ.get("SERPAPI_KEY")
            )
            
            if "organic_results" not in results or not results["organic_results"]:
                return ""
                
            
            snippets = []
            for result in results["organic_results"][:2]:  
                if "snippet" in result:
                    snippets.append(result["snippet"])
            
            if snippets:
                combined_info = " | ".join(snippets)
                return f"Music context: {combined_info[:300]}..."
                
        except Exception as e:
            logger.error(f"Error in RAG lookup: {e}")
            return ""

    def _extract_music_entities(self, text: str) -> List[str]:
        """
        Extract potential music-related entities from text.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            A list of potential music entities
        """
        # Simple pattern matching for music entities
        # This could be enhanced with NLP libraries in production
        music_patterns = [
            r"song[:\s]+(['\"]?)([^'\"]+?)\1",
            r"track[:\s]+(['\"]?)([^'\"]+?)\1", 
            r"album[:\s]+(['\"]?)([^'\"]+?)\1",
            r"artist[:\s]+(['\"]?)([^'\"]+?)\1",
            r"band[:\s]+(['\"]?)([^'\"]+?)\1",
        ]
        
        entities = []
        for pattern in music_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    entity = match[1].strip()
                else:
                    entity = match.strip()
                if entity and len(entity) > 2:
                    entities.append(entity)
        
        # Also look for quoted strings that might be song/artist names
        quoted_strings = re.findall(r'["\']([^"\']{3,})["\']', text)
        entities.extend(quoted_strings)
        
        return list(set(entities))  # Remove duplicates

    async def on_user_turn_completed(
        self, turn_ctx: ChatContext, new_message: ChatMessage,
    ) -> None:
        """
        Called after a user completes their turn in the conversation.
        Enhances the conversation with relevant music information.
        
        Args:
            turn_ctx: The chat context
            new_message: The user's most recent message
        """
        try:
            # Get RAG information for the user's message
            rag_info = await self.my_rag_lookup(new_message.content)
            
            if rag_info:
                # Add the RAG information to the context
                logger.info(f"Adding RAG context: {rag_info[:100]}...")
                # This context will be available to the LLM in subsequent turns
                
        except Exception as e:
            logger.error(f"Error in on_user_turn_completed: {e}")

    async def handle_message(self, message: str):
        """Handle incoming messages and detect music-related queries"""
        logger.info(f"Handling message: {message}")
        
        # Check if this looks like a music query that needs song info
        music_keywords = ["song", "track", "artist", "album", "music", "singer", "band"]
        contains_music_keywords = any(keyword in message.lower() for keyword in music_keywords)
        
        if contains_music_keywords:
            # Extract potential song/artist names
            entities = self._extract_music_entities(message)
            if entities:
                # Automatically trigger song search for the first entity
                await self.find_song_info(entities[0])


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent"""
    logger.info("Starting Pied Piper Agent")
    
    # Wait for the first participant to connect
    await ctx.wait_for_participant()
    logger.info("Participant connected, starting agent session")
    
    # Create and start the agent
    agent = MultilingualPipeyAgent()
    await agent.start(ctx.room)
    
    logger.info("Pied Piper Agent started successfully")


if __name__ == "__main__":
    # Run the agent using LiveKit CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=None,
        )
    )