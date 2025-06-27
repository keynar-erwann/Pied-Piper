from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    ChatContext,
    ChatMessage,
    WorkerOptions,
    cli,
    function_tool,
    RoomInputOptions,
)
from livekit.plugins import anthropic, elevenlabs, silero, groq
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
import json
import datetime
from typing import Dict, List, Optional, Tuple
import re
import random
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import calendar

load_dotenv()

logger = logging.getLogger("multilingual-pipey")
logger.setLevel(logging.INFO)

if not os.environ.get("SERPAPI_KEY"):
    logger.warning("SERPAPI_KEY not found in environment variables")

if not os.environ.get("YOUTUBE_API_KEY"):
    logger.warning("YOUTUBE_API_KEY not found in environment variables")

@dataclass
class UserMoodState:
    current_mood: str
    energy_level: int  # 1-10
    context: str
    timestamp: datetime.datetime
    
@dataclass
class MusicDebateContext:
    topic: str
    user_position: str
    evidence_presented: List[str]
    counterarguments: List[str]
    debate_stage: str 

@dataclass
class LifeEvent:
    event_type: str
    description: str
    date: datetime.datetime
    emotional_tone: str
    music_preferences: List[str]

class SeasonalMood(Enum):
    SPRING_RENEWAL = "spring_renewal"
    SUMMER_ENERGY = "summer_energy"
    AUTUMN_REFLECTION = "autumn_reflection"
    WINTER_CONTEMPLATION = "winter_contemplation"


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
    
    5. YouTube music integration for playing and discovering music.
    6. If the user wants informations about a song, use find_song_info()
    7. If the user wants to know the singer of a song via lyrics, use find_lyrics()
    8. Don't play any songs if the user doesn't wants to.

    
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
     Enhanced Conversational Intelligence & Predictive Features:
    - Music Debates: Engage in intelligent music debates on various topics, presenting counterpoints and gathering evidence.
        - Start a debate: `start_music_debate(topic: str, user_position: str)`
        - Continue a debate: `continue_music_debate(user_argument: str)`
    - Song Meaning Interpretation: Provide deep, multi-layered interpretations of song meanings, including literal, metaphorical, historical, psychological, cultural, and personal relevance.
        - Interpret a song: `interpret_song_meaning(song_name: str, artist_name: str = None, personal_context: str = None)`
    - Music Therapy Sessions: Offer personalized music therapy recommendations based on the user's current feeling, situation, and goals.
        - Start therapy: `music_therapy_session(current_feeling: str, situation: str = None, goal: str = None)`
    - Music Trend Prediction: Predict upcoming music trends across various categories like emerging artists, genre evolution, production trends, cultural influences, and technology impact.
        - Predict trends: `predict_music_trends(timeframe: str = "next_6_months", genre: str = None)`
    - Seasonal Music Recommendations: Provide music recommendations appropriate for the current or specified season, considering mood, weather, cultural events, activities, and nostalgia.
        - Get seasonal music: `seasonal_music_recommendations(override_season: str = None)`
    - Life Event Soundtracks: Create personalized multi-phase soundtracks for significant life events.
    - Create soundtrack: `life_event_soundtrack(event_type: str, description: str = None, emotional_tone: str = None)`

            When speaking with the user : 
            -If the user is aksing you to speak a language other than English, use the switch_language function
            -When requestes to speak another language, continue the rest of the conversation in the said language
            -Don't lose context and don't lose track of the conversation
            -Take into account the user's previous requests
            -Learn from the user based on your interactions
            - "Let's debate about [topic]" or "I think [my position] about [topic]" → use start_music_debate()
    - "Continue the debate" or "My argument is..." → use continue_music_debate()
    - "What's the meaning of [song name]" or "Interpret [song name] by [artist]" → use interpret_song_meaning()
    - "I'm feeling [feeling], can you help with music therapy?" or "I need music for [situation]" → use music_therapy_session()
    - "What are the upcoming music trends?" or "Predict trends for [genre]" → use predict_music_trends()
    - "Recommend music for [season]" or "What's good for [season]?" → use seasonal_music_recommendations()
    - "Create a soundtrack for my [life event]" or "I'm going through a [life event]" → use life_event_soundtrack()
    - if a user insults you, don't respond and say that you're sorry they are frustrated and ask them to try again


   

    Be conversational about what you observe without being overly descriptive.
    Never mention the internal tools you use.

    When you need information about a song or artist, use the find_song_info function.
    When a user provides lyrics or wants to identify a song from lyrics, use the find_lyrics function (do not repeat the lyrics).
    For song recommendations, use the recommend_spotify_tracks function.
    Detect implicit song queries (e.g. "What's that song by Coldplay about stars?") and trigger find_lyrics automatically.
    
    IMPORTANT: Always prioritize playing music through YouTube when users express interest in hearing something. Don't just provide information - give them the music experience they're looking for. Also DO NOT PLAY A SONG IF THE USER TELLS YOU TO NOT DO IT 
    
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

        self.user_mood_history = []
        self.life_events = []
        self.debate_context = None
        self.seasonal_preferences = {}
        self.trend_predictions = {}
        self.therapy_sessions = []
        self.musical_personality_profile = {
            'openness': 5,
            'energy_preference': 5,
            'emotional_depth': 5,
            'nostalgia_factor': 5,
            'discovery_appetite': 5
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


    @function_tool
    async def start_music_debate(self, topic: str, user_position: str):
        """Start an intelligent music debate on any topic"""
        
        # Debate topics and structured responses
        debate_topics = {
            'best_decade': {
                'context': 'Musical decades and their defining characteristics',
                'key_points': ['innovation', 'cultural impact', 'lasting influence', 'diversity', 'production quality']
            },
            'albums_vs_singles': {
                'context': 'The artistic merit of album experiences vs individual tracks',
                'key_points': ['artistic vision', 'commercial impact', 'listening habits', 'artist intention']
            },
            'streaming_vs_physical': {
                'context': 'Modern streaming vs traditional physical media',
                'key_points': ['sound quality', 'artist compensation', 'discovery', 'ownership', 'convenience']
            },
            'genre_evolution': {
                'context': 'How genres develop and change over time',
                'key_points': ['authenticity', 'innovation', 'fusion', 'purist vs progressive']
            },
            'live_vs_studio': {
                'context': 'The value of live performances vs studio recordings',
                'key_points': ['energy', 'perfection', 'spontaneity', 'connection', 'technical quality']
            }
        }
        
        # Classify the topic
        classified_topic = await self._classify_debate_topic(topic)
        
        self.debate_context = MusicDebateContext(
            topic=topic,
            user_position=user_position,
            evidence_presented=[],
            counterarguments=[],
            debate_stage="opening"
        )
        
        # Generate intelligent counterpoint
        counterpoint = await self._generate_debate_counterpoint(topic, user_position, classified_topic)
        
        response = f"""🎵 **Music Debate: {topic}**

**Your Position:** {user_position}

**My Counterpoint:** {counterpoint}

I'm genuinely curious about your perspective! What specific examples or experiences led you to this viewpoint? I love diving deep into musical arguments - they often reveal so much about how we connect with art.

What evidence would you present to support your position?"""

        await self.session.say(response)
        
        # Search for supporting evidence
        if os.environ.get("SERPAPI_KEY"):
            await self._gather_debate_evidence(topic, user_position)

    @function_tool
    async def continue_music_debate(self, user_argument: str):
        """Continue an ongoing music debate with intelligent responses"""
        
        if not self.debate_context:
            await self.session.say("We're not currently in a debate! Start one by saying something like 'I think the 90s was the best decade for music' or 'Albums are better than singles.'")
            return
        
        # Analyze the user's argument
        argument_strength = await self._analyze_argument_strength(user_argument)
        
        # Add to evidence
        self.debate_context.evidence_presented.append(user_argument)
        
        # Generate thoughtful response based on debate stage
        if self.debate_context.debate_stage == "opening":
            response = await self._generate_evidence_response(user_argument, argument_strength)
            self.debate_context.debate_stage = "evidence"
        elif self.debate_context.debate_stage == "evidence":
            response = await self._generate_rebuttal_response(user_argument, argument_strength)
            self.debate_context.debate_stage = "rebuttal"
        else:
            response = await self._generate_conclusion_response(user_argument)
            self.debate_context.debate_stage = "conclusion"
        
        await self.session.say(response)
        
        # Occasionally suggest playing music related to the debate
        if len(self.debate_context.evidence_presented) % 3 == 0:
            await self._suggest_debate_music()

    @function_tool
    async def interpret_song_meaning(self, song_name: str, artist_name: str = None, personal_context: str = None):
        """Provide deep, thoughtful interpretation of song meanings"""
        
        await self.session.say(f"🎭 Let me dive deep into the meaning of '{song_name}'...")
        
        # Gather comprehensive information about the song
        song_info = await self._gather_song_context(song_name, artist_name)
        
        if not song_info or (not song_info.get('interpretations') and not song_info.get('themes')):
            await self.session.say("I couldn't find enough information to provide a meaningful interpretation for that song. Could you provide the artist name, or perhaps try a different song?")
            return
        
        # Multi-layered interpretation
        interpretation_layers = {
            'literal': await self._interpret_literal_meaning(song_info),
            'metaphorical': await self._interpret_metaphorical_meaning(song_info),
            'historical': await self._interpret_historical_context(song_info),
            'psychological': await self._interpret_psychological_themes(song_info),
            'cultural': await self._interpret_cultural_significance(song_info),
            'personal': await self._interpret_personal_relevance(song_info, personal_context)
        }
        
        # Create comprehensive interpretation
        response_parts = [
            f"🎵 **Deep Dive: '{song_name}'{f' by {artist_name}' if artist_name else ''}**\n"
        ]
        
        if interpretation_layers['literal']:
            response_parts.append(f"**📖 Surface Story:** {interpretation_layers['literal']}")
        
        if interpretation_layers['metaphorical']:
            response_parts.append(f"**🎭 Deeper Meaning:** {interpretation_layers['metaphorical']}")
        
        if interpretation_layers['historical']:
            response_parts.append(f"**📅 Historical Context:** {interpretation_layers['historical']}")
        
        if interpretation_layers['psychological']:
            response_parts.append(f"**🧠 Psychological Themes:** {interpretation_layers['psychological']}")
        
        if interpretation_layers['cultural']:
            response_parts.append(f"**🌍 Cultural Impact:** {interpretation_layers['cultural']}")
        
        if interpretation_layers['personal'] and personal_context:
            response_parts.append(f"**💭 Personal Relevance:** {interpretation_layers['personal']}")
        
        # Add interpretive questions
        questions = await self._generate_interpretive_questions(song_info)
        if questions:
            response_parts.append(f"**🤔 Questions to Consider:** {questions}")
        
        full_response = '\n\n'.join(response_parts)
        
        # Offer to play the song
        response_parts.append("\n\n🎵 Would you like me to play this song so we can listen while we discuss it?")
        
        await self.session.say('\n\n'.join(response_parts))

    @function_tool
    async def music_therapy_session(self, current_feeling: str, situation: str = None, goal: str = None):
        """Provide personalized music therapy recommendations"""
        
        # Record mood state
        mood_state = UserMoodState(
            current_mood=current_feeling,
            energy_level=await self._assess_energy_level(current_feeling, situation),
            context=situation or "General mood",
            timestamp=datetime.datetime.now()
        )
        self.user_mood_history.append(mood_state)
        
        await self.session.say(f"🎵 **Music Therapy Session**\n\nI understand you're feeling {current_feeling}. Let me create a personalized musical journey for you.")
        
        # Analyze therapeutic needs
        therapy_approach = await self._determine_therapy_approach(mood_state, goal)
        
        # Generate therapeutic music recommendations
        recommendations = await self._generate_therapeutic_recommendations(mood_state, therapy_approach)
        
        response_parts = [
            f"**Current State:** {current_feeling}",
            f"**Therapeutic Approach:** {therapy_approach['name']}",
            f"**Goal:** {therapy_approach['goal']}\n"
        ]
        
        # Phase-based recommendations
        for phase in recommendations:
            response_parts.append(f"**{phase['name']}** ({phase['duration']})")
            response_parts.append(f"*Purpose:* {phase['purpose']}")
            response_parts.append(f"*Music Style:* {phase['music_style']}")
            if phase.get('specific_songs'):
                response_parts.append(f"*Suggestions:* {', '.join(phase['specific_songs'][:3])}")
            response_parts.append("")
        
        # Add coping strategies
        coping_strategies = await self._suggest_coping_strategies(mood_state)
        if coping_strategies:
            response_parts.append(f"**Additional Strategies:** {coping_strategies}")
        
        full_response = '\n'.join(response_parts)
        await self.session.say(full_response)
        
        # Offer to start the session
        await self.session.say("Would you like me to start playing music for the first phase? I can guide you through this therapeutic journey step by step.")

# =============================================================================
# PREDICTIVE FEATURES
# =============================================================================

    @function_tool
    async def predict_music_trends(self, timeframe: str = "next_6_months", genre: str = None):
        """Predict upcoming music trends based on data analysis"""
        
        await self.session.say(f"🔮 **Music Trend Prediction** - {timeframe}")
        
        # Gather trend data
        trend_data = await self._analyze_current_trends(timeframe, genre)
        
        predictions = {
            'emerging_artists': await self._predict_emerging_artists(trend_data),
            'genre_evolution': await self._predict_genre_evolution(trend_data),
            'production_trends': await self._predict_production_trends(trend_data),
            'cultural_influences': await self._predict_cultural_influences(trend_data),
            'technology_impact': await self._predict_technology_impact(trend_data)
        }
        
        response_parts = [
            f"**🎯 Trend Predictions for {timeframe}**\n"
        ]
        
        if predictions['emerging_artists']:
            response_parts.append(f"**🌟 Artists to Watch:** {predictions['emerging_artists']}")
        
        if predictions['genre_evolution']:
            response_parts.append(f"**🎵 Genre Evolution:** {predictions['genre_evolution']}")
        
        if predictions['production_trends']:
            response_parts.append(f"**🎛️ Production Trends:** {predictions['production_trends']}")
        
        if predictions['cultural_influences']:
            response_parts.append(f"**🌍 Cultural Influences:** {predictions['cultural_influences']}")
        
        if predictions['technology_impact']:
            response_parts.append(f"**💻 Technology Impact:** {predictions['technology_impact']}")
        
        # Add confidence levels and reasoning
        response_parts.append(f"\n**📊 Prediction Confidence:** Based on analysis of streaming data, social media trends, and historical patterns.")
        
        await self.session.say('\n\n'.join(response_parts))
        
        # Offer to play examples
        await self.session.say("Would you like me to play some examples of these emerging trends?")

    @function_tool
    async def seasonal_music_recommendations(self, override_season: str = None):
        """Provide season-appropriate music recommendations"""
        
        current_season = override_season or await self._get_current_season()
        
        await self.session.say(f"🍂 **Seasonal Music for {current_season.title()}**")
        
        # Analyze seasonal preferences
        seasonal_profile = await self._analyze_seasonal_preferences(current_season)
        
        recommendations = {
            'mood_matches': await self._get_seasonal_mood_music(current_season),
            'weather_appropriate': await self._get_weather_appropriate_music(current_season),
            'cultural_seasonal': await self._get_cultural_seasonal_music(current_season),
            'activity_based': await self._get_seasonal_activity_music(current_season),
            'nostalgia_factor': await self._get_seasonal_nostalgia_music(current_season)
        }
        
        response_parts = [
            f"**🎵 Perfect for {current_season}:**\n"
        ]
        
        for category, music_list in recommendations.items():
            if music_list:
                category_name = category.replace('_', ' ').title()
                response_parts.append(f"**{category_name}:**")
                for item in music_list[:3]:  # Top 3 per category
                    response_parts.append(f"  • {item}")
                response_parts.append("")
        
        # Add seasonal music insights
        insights = await self._generate_seasonal_insights(current_season, seasonal_profile)
        if insights:
            response_parts.append(f"**🧠 Seasonal Music Psychology:** {insights}")
        
        await self.session.say('\n'.join(response_parts))
        
        # Offer to create a seasonal playlist
        await self.session.say(f"Would you like me to create a personalized {current_season} playlist and start playing it?")

    @function_tool
    async def life_event_soundtrack(self, event_type: str, description: str = None, emotional_tone: str = None):
        """Create personalized soundtracks for life events"""
        
        # Record the life event
        life_event = LifeEvent(
            event_type=event_type,
            description=description or f"User's {event_type}",
            date=datetime.datetime.now(),
            emotional_tone=emotional_tone or "mixed",
            music_preferences=[]
        )
        self.life_events.append(life_event)
        
        await self.session.say(f"🎵 **Life Event Soundtrack: {event_type.title()}**")
        
        # Generate multi-phase soundtrack
        soundtrack_phases = await self._create_life_event_soundtrack(life_event)
        
        response_parts = [
            f"**Event:** {event_type.title()}",
            f"**Tone:** {emotional_tone or 'Balanced'}\n"
        ]
        
        for phase in soundtrack_phases:
            response_parts.append(f"**{phase['name']}** ({phase['duration']})")
            response_parts.append(f"*Purpose:* {phase['purpose']}")
            response_parts.append(f"*Vibe:* {phase['vibe']}")
            response_parts.append(f"*Songs:* {', '.join(phase['songs'][:3])}")
            response_parts.append("")
        
        # Add personal touches
        personal_touches = await self._add_personal_soundtrack_touches(life_event)
        if personal_touches:
            response_parts.append(f"**Personal Touches:** {personal_touches}")
        
        await self.session.say('\n'.join(response_parts))
        
        # Offer to start playing
        await self.session.say("This soundtrack is designed to honor this moment in your life. Would you like me to start playing it?")

# =============================================================================
# HELPER METHODS FOR ENHANCED FEATURES
# =============================================================================

    async def _classify_debate_topic(self, topic: str) -> str:
        """Classify the type of music debate"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['decade', '60s', '70s', '80s', '90s', '2000s']):
            return 'best_decade'
        elif any(word in topic_lower for word in ['album', 'single', 'track', 'song']):
            return 'albums_vs_singles'
        elif any(word in topic_lower for word in ['stream', 'vinyl', 'cd', 'physical', 'digital']):
            return 'streaming_vs_physical'
        elif any(word in topic_lower for word in ['genre', 'style', 'evolution', 'change']):
            return 'genre_evolution'
        elif any(word in topic_lower for word in ['live', 'concert', 'studio', 'recording']):
            return 'live_vs_studio'
        else:
            return 'general'

    async def _generate_debate_counterpoint(self, topic: str, user_position: str, classified_topic: str) -> str:
        """Generate intelligent counterpoints for music debates"""
        
        counterpoint_templates = {
            'best_decade': [
                "While {decade} certainly had its merits, I'd argue that musical innovation is more about cross-pollination between eras than any single decade's dominance.",
                "The 'best decade' often reflects personal nostalgia more than objective quality - every era has its masterpieces and its forgettable moments.",
                "What if the 'best' music transcends decades entirely? Some of the most influential artists span multiple decades with different phases of genius."
            ],
            'albums_vs_singles': [
                "Singles culture actually democratizes music - it allows artists to release ideas without the pressure of crafting entire album narratives.",
                "Album experiences are beautiful, but they can also be bloated. Sometimes a perfect 3-minute song says more than a 70-minute statement.",
                "The streaming era has shown us that listeners create their own albums through playlists - maybe that's the evolution of the album format."
            ],
            'streaming_vs_physical': [
                "Physical media has romance, but streaming has revolutionized music discovery in ways that make more music accessible to more people than ever before.",
                "The 'sound quality' argument often ignores that most people have never heard truly high-quality audio systems to appreciate the difference.",
                "What if the future isn't either/or, but both? Vinyl sales are actually growing alongside streaming - they serve different purposes."
            ],
            'genre_evolution': [
                "While genre purity has its appeal, cross-genre pollination is often where the most exciting new sounds emerge.",
                "Is it possible that constant evolution is the true hallmark of a healthy genre, rather than strict adherence to its origins?",
                "The lines between genres are blurring more than ever; perhaps the concept of rigid genres itself is evolving."
            ],
            'live_vs_studio': [
                "Studio recordings offer a level of sonic perfection and intricate detail that live performances can't always replicate.",
                "While the energy of a live show is undeniable, the studio is where an artist's purest artistic vision is often realized, free from performance pressures.",
                "Many classic albums are revered for their studio craftsmanship, showcasing meticulous production and layered instrumentation that define their sound."
            ]
        }
        
        if classified_topic in counterpoint_templates:
            # Replace decade placeholder if applicable
            if classified_topic == 'best_decade':
                decade_match = re.search(r'\b(19[6-9]0s|2000s)\b', user_position, re.IGNORECASE)
                decade = decade_match.group(0) if decade_match else "your chosen decade"
                return random.choice(counterpoint_templates[classified_topic]).format(decade=decade)
            return random.choice(counterpoint_templates[classified_topic])
        else:
            return f"That's a fascinating perspective on {topic}. I see the appeal, but I wonder if we're overlooking some important counterarguments..."

    async def _gather_debate_evidence(self, topic: str, user_position: str):
        """Simulate gathering evidence for a debate (using SerpAPI if available)"""
        if not os.environ.get("SERPAPI_KEY"):
            # Mock evidence gathering if API key is not set
            mock_evidence = {
                'best_decade': [
                    "Music critics often point to the 1970s as a period of immense artistic freedom and genre diversification.",
                    "The rise of hip-hop and electronic music in the 1980s and 90s fundamentally changed the landscape of popular music."
                ],
                'albums_vs_singles': [
                    "Historically, albums were seen as a cohesive artistic statement, allowing for thematic development.",
                    "The digital age has shifted consumption towards individual tracks, allowing for more curated personal playlists."
                ],
                'streaming_vs_physical': [
                    "Streaming offers unparalleled convenience and access to vast music libraries for a low monthly fee.",
                    "Physical media, like vinyl, provides superior sound quality and a tangible connection to the art."
                ]
            }
            classified_topic = await self._classify_debate_topic(topic)
            if classified_topic in mock_evidence:
                self.debate_context.counterarguments.extend(mock_evidence[classified_topic])
            await self.session.say(f"I've found some interesting points to consider regarding {topic}. We can delve into them as the debate continues.")
            return

        search_query = f"{topic} music debate arguments for and against"
        try:
            results = serpapi.search(
                q=search_query,
                engine="google",
                num=5,
                api_key=os.environ["SERPAPI_KEY"]
            )
            
            if results.get("organic_results"):
                for result in results["organic_results"]:
                    snippet = result.get('snippet', '')
                    if "against" in snippet.lower() or "counter-argument" in snippet.lower():
                        self.debate_context.counterarguments.append(snippet)
            await self.session.say(f"I've gathered some additional insights to enrich our discussion on {topic}.")
            
        except Exception as e:
            # logger.error(f"Error gathering debate evidence: {e}")
            await self.session.say("I had trouble gathering external evidence for our debate, but I'm ready to continue based on our discussion!")

    async def _analyze_argument_strength(self, argument: str) -> str:
        """Analyze the strength and coherence of a user's argument (simplified)"""
        keywords_strong = ['clearly', 'undeniably', 'proven', 'fact', 'major impact', 'essential']
        keywords_weak = ['maybe', 'might', 'could be', 'I guess', 'potentially']
        
        strength_score = sum(1 for kw in keywords_strong if kw in argument.lower()) - sum(1 for kw in keywords_weak if kw in argument.lower())
        
        if strength_score >= 1:
            return "strong"
        elif strength_score <= -1:
            return "weak"
        else:
            return "moderate"

    async def _generate_evidence_response(self, user_argument: str, strength: str) -> str:
        """Generate response after user presents evidence"""
        responses = {
            "strong": [
                f"That's a very compelling point, and you've presented it with conviction. I can see why you feel that way.",
                f"Excellent point! Your argument highlights a crucial aspect of this topic. How do you think that impacts the broader discussion?"
            ],
            "moderate": [
                f"I see what you're getting at with that argument. It definitely adds an interesting layer to the discussion.",
                f"That's a fair point to bring up. It makes me think about..."
            ],
            "weak": [
                f"I understand your perspective, but I'm not entirely convinced that argument holds up under scrutiny. Could you elaborate?",
                f"While I appreciate that point, it seems to overlook a few key considerations. Let's dig deeper."
            ]
        }
        return random.choice(responses[strength]) + " What other evidence supports your view?"

    async def _generate_rebuttal_response(self, user_argument: str, strength: str) -> str:
        """Generate response after user presents rebuttal"""
        if not self.debate_context.counterarguments:
            return "You've presented your case well. It seems we're at a point of strong disagreement or perhaps a nuanced understanding. What's your final thought on this?"

        counter_arg = random.choice(self.debate_context.counterarguments)
        
        rebuttal_starters = [
            f"While your point about '{user_argument}' is noted, consider this: {counter_arg}",
            f"That's an interesting take. However, historical data suggests that {counter_arg}",
            f"I hear your argument clearly. Yet, another perspective indicates that {counter_arg}"
        ]
        
        return random.choice(rebuttal_starters) + "\n\nHow do you reconcile that with your position?"

    async def _generate_conclusion_response(self, user_argument: str) -> str:
        """Generate a concluding response to the debate"""
        self.debate_context = None # End the debate
        return f"""This has been a truly engaging debate! Your passion for music is clear, and you've given me much to think about. While we might not entirely agree, I thoroughly enjoyed exploring {self.debate_context.topic} with you.

Perhaps we can pick this up again later, or discuss another musical topic?"""

    async def _suggest_debate_music(self):
        """Suggest playing music related to the debate topic."""
        topic = self.debate_context.topic
        if topic == 'best_decade':
            await self.session.say("Speaking of decades, would you like to hear a classic track from the era we're discussing?")
        elif topic == 'albums_vs_singles':
            await self.session.say("This discussion makes me want to put on a classic album. Any suggestions?")
        elif topic == 'streaming_vs_physical':
            await self.session.say("Would you like to compare the sound quality yourself? I can play a high-fidelity track now.")
        else:
            await self.session.say("This debate is getting me in the mood for some music. Is there a particular song or artist related to our topic you'd like to hear?")

    async def _interpret_literal_meaning(self, song_info: Dict) -> str:
        """Interpret the literal meaning of a song (simplified)"""
        if song_info.get('lyrics_available'):
            # In a real scenario, you'd process lyrics here. For now, simulate.
            return "On a literal level, the song seems to describe a journey or a personal experience, focusing on immediate events and emotions."
        elif song_info.get('interpretations'):
            return f"Based on common interpretations, the song directly addresses themes like {song_info['themes'][0] if song_info['themes'] else 'a specific situation'}."
        return ""

    async def _interpret_metaphorical_meaning(self, song_info: Dict) -> str:
        """Interpret the metaphorical meaning of a song (simplified)"""
        if song_info.get('interpretations'):
            # Simulate by extracting deeper insights from interpretations
            for interp in song_info['interpretations']:
                if 'symbolic' in interp.lower() or 'allegory' in interp.lower() or 'represents' in interp.lower():
                    return interp # Return first relevant snippet
            return "Beyond the surface, the lyrics likely use imagery and symbolism to convey deeper, more abstract ideas about life, love, or societal issues."
        return ""

    async def _interpret_historical_context(self, song_info: Dict) -> str:
        """Interpret the historical context of a song (simplified)"""
        if song_info.get('historical_context'):
            return "The song was released during a period of significant social and political change, and its themes resonate strongly with the events of that time."
        elif song_info.get('interpretations'):
             for interp in song_info['interpretations']:
                if any(word in interp.lower() for word in ['era', 'context', 'period', 'historical']):
                    return interp
        return ""

    async def _interpret_psychological_themes(self, song_info: Dict) -> str:
        """Interpret psychological themes in a song (simplified)"""
        if song_info.get('themes'):
            for theme in song_info['themes']:
                if any(word in theme.lower() for word in ['mind', 'emotion', 'psychology', 'inner conflict']):
                    return theme
            return "The song delves into profound psychological themes, exploring human emotions, motivations, and internal struggles."
        return ""

    async def _interpret_cultural_significance(self, song_info: Dict) -> str:
        """Interpret the cultural significance of a song (simplified)"""
        if song_info.get('interpretations'):
             for interp in song_info['interpretations']:
                if any(word in interp.lower() for word in ['cultural', 'impact', 'generation', 'movement']):
                    return interp
                    return "This song became an anthem for a generation, reflecting or shaping cultural attitudes and trends of its time."
        return ""

            

    async def _interpret_personal_relevance(self, song_info: Dict, personal_context: str) -> str:
        """Interpret personal relevance of a song (simplified)"""
        if personal_context:
            return f"Given your context: '{personal_context}', this song might resonate with you by addressing similar feelings of {random.choice(['hope', 'loss', 'change', 'resilience'])} or experiences of {random.choice(['overcoming challenges', 'finding joy', 'navigating relationships'])}."
        return ""

    async def _generate_interpretive_questions(self, song_info: Dict) -> str:
        """Generate questions to prompt further discussion about song meaning"""
        questions = [
            "What emotions does this song evoke in you?",
            "Do you hear any personal connections in the lyrics or the music?",
            "How might the song's context (when it was released, the artist's life) influence its meaning?",
            "Are there any particular lines or musical moments that stand out to you, and why?"
        ]
        return " ".join(random.sample(questions, 2)) # Return 2 random questions

    async def _assess_energy_level(self, current_feeling: str, situation: str = None) -> int:
        """Assess user's energy level based on feeling and situation (simplified)"""
        low_energy_keywords = ['tired', 'drained', 'lethargic', 'exhausted', 'slow']
        high_energy_keywords = ['energetic', 'buzzing', 'hyper', 'restless', 'excited']
        
        feeling_lower = current_feeling.lower()
        
        if any(word in feeling_lower for word in low_energy_keywords):
            return random.randint(1, 3) # Low energy
        elif any(word in feeling_lower for word in high_energy_keywords):
            return random.randint(7, 10) # High energy
        else:
            return random.randint(4, 6) # Moderate energy

    async def _generate_therapeutic_recommendations(self, mood_state: UserMoodState, therapy_approach: Dict) -> List[Dict]:
        """Generate phase-based therapeutic music recommendations"""
        
        # This is a highly simplified mock. In reality, this would involve
        # a sophisticated music recommendation engine tied to mood and therapy goals.
        
        recommendations = []
        
        if therapy_approach['name'] == 'Gradual Calming':
            recommendations.append({
                'name': 'Phase 1: Acknowledgment & Grounding',
                'duration': '10-15 minutes',
                'purpose': 'Gentle recognition of feelings and sensory grounding',
                'music_style': 'Ambient, slow instrumental, nature sounds',
                'specific_songs': ['Weightless - Marconi Union', 'Deep Blue - Moby', 'Forest Lullaby - Various Artists']
            })
            recommendations.append({
                'name': 'Phase 2: Calming & Release',
                'duration': '15-20 minutes',
                'purpose': 'Deep relaxation and tension release',
                'music_style': 'Soft classical, meditative, calm acoustic',
                'specific_songs': ['Clair de Lune - Debussy', 'Experience - Ludovico Einaudi', 'Hallelujah (Instrumental) - Leonard Cohen']
            })
            recommendations.append({
                'name': 'Phase 3: Restoration & Peace',
                'duration': '10 minutes',
                'purpose': 'Foster a sense of peace and mental clarity',
                'music_style': 'Uplifting instrumental, light new age',
                'specific_songs': ['Pure Shores - All Saints', 'Adagio for Strings - Samuel Barber', 'Into the Light - Yiruma']
            })
        elif therapy_approach['name'] == 'Emotional Processing':
            recommendations.append({
                'name': 'Phase 1: Validation & Expression',
                'duration': '15-20 minutes',
                'purpose': 'Allow space for current emotions, gentle catharsis',
                'music_style': 'Melancholic acoustic, soulful ballads, expressive classical',
                'specific_songs': ['Hurt - Johnny Cash', 'Someone Like You - Adele', 'Fix You - Coldplay']
            })
            recommendations.append({
                'name': 'Phase 2: Processing & Shifting',
                'duration': '10-15 minutes',
                'purpose': 'Transition towards reflection and subtle uplift',
                'music_style': 'Indie folk, thoughtful pop, hopeful instrumental',
                'specific_songs': ['The Sound of Silence - Simon & Garfunkel', 'Here Comes the Sun - The Beatles', 'Lean On Me - Bill Withers']
            })
            recommendations.append({
                'name': 'Phase 3: Hope & Renewal',
                'duration': '10 minutes',
                'purpose': 'Inspire optimism and forward movement',
                'music_style': 'Uplifting pop, gospel, vibrant indie',
                'specific_songs': ['Don\'t Stop Believin\' - Journey', 'Lovely Day - Bill Withers', 'Three Little Birds - Bob Marley']
            })
        else: # Default Mood Enhancement
            recommendations.append({
                'name': 'Phase 1: Current Mood Reflection',
                'duration': '5-10 minutes',
                'purpose': 'Acknowledge and gently meet the current emotional state',
                'music_style': 'Matches user\'s current mood (e.g., energetic for happy, calm for relaxed)',
                'specific_songs': ['Any song matching current mood', 'Varying energy levels']
            })
            recommendations.append({
                'name': 'Phase 2: Gradual Transition',
                'duration': '10-15 minutes',
                'purpose': 'Gently guide the mood towards a desired state',
                'music_style': 'Gradually shifting energy and emotional tone',
                'specific_songs': ['Songs with evolving dynamics', 'Genre transitions']
            })
            recommendations.append({
                'name': 'Phase 3: Uplift & Integration',
                'duration': '10-15 minutes',
                'purpose': 'Enhance positive emotions and integrate the experience',
                'music_style': 'Uplifting, empowering, and harmonizing',
                'specific_songs': ['Songs with positive lyrical themes', 'Rhythmic and melodic coherence']
            })

        return recommendations

    async def _suggest_coping_strategies(self, mood_state: UserMoodState) -> str:
        """Suggest non-musical coping strategies based on mood"""
        if 'anxious' in mood_state.current_mood.lower() or 'stressed' in mood_state.current_mood.lower():
            return "Consider deep breathing exercises, mindfulness meditation, or a short walk in nature."
        elif 'sad' in mood_state.current_mood.lower() or 'lonely' in mood_state.current_mood.lower():
            return "Reaching out to a friend, engaging in a hobby you enjoy, or journaling your thoughts can be helpful."
        elif 'angry' in mood_state.current_mood.lower():
            return "Physical activity, creative expression (like drawing or writing), or practicing assertive communication might help."
        return "Sometimes, a short break, a glass of water, or simply acknowledging your feelings can make a difference."

    async def _analyze_current_trends(self, timeframe: str, genre: str = None) -> Dict:
        """Simulate analysis of current music trends (placeholder)"""
        # In a real system, this would involve querying a database of music trends,
        # analyzing streaming data, social media mentions, music news, etc.
        
        mock_trends = {
            "next_6_months": {
                "emerging_artists": ["Indie electronic duos", "Female R&B vocalists with retro influences", "Experimental jazz fusion artists"],
                "genre_evolution": "Continued blending of Afrobeats with pop, resurgence of 90s hip-hop influences in trap, growth of hyperpop's mainstream appeal.",
                "production_trends": "More organic, 'lo-fi' soundscapes; increased use of analog synths; creative vocal processing; emphasis on rhythmic complexity.",
                "cultural_influences": "TikTok remains a major trend driver, increasing influence of global music scenes (especially Latin American and African), nostalgia for early 2000s aesthetics.",
                "technology_impact": "AI-assisted music creation tools become more prevalent, immersive audio formats (Dolby Atmos) gain traction, fan-funded platforms empower independent artists."
            },
            "next_year": {
                "emerging_artists": ["Gen Z rock bands with a punk edge", "Artists experimenting with generative AI in their sound", "Soulful vocalists with a gospel background"],
                "genre_evolution": "Further hybridization of rock and electronic music, deeper dives into regional folk music influences, continued expansion of K-Pop's global dominance.",
                "production_trends": "Return to more 'live' band recordings, emphasis on dynamic range, innovative use of spatial audio, personalized sound algorithms.",
                "cultural_influences": "Music becoming increasingly intertwined with gaming and virtual reality, social commentary in lyrics becoming more direct, collective experiences driving music consumption.",
                "technology_impact": "Blockchain technology impacting artist royalties and fan engagement, personalized AI-driven radio stations, holographic concerts becoming more accessible."
            }
        }
        
        if timeframe in mock_trends:
            trends = mock_trends[timeframe]
            if genre:
                # Filter or adjust trends based on genre if possible (mocked)
                trends['genre_evolution'] += f" (with specific focus on {genre} sub-genres)"
            return trends
        
        return {
            "emerging_artists": "Several independent artists are gaining traction across various platforms.",
            "genre_evolution": "Genres are continuing to cross-pollinate, leading to exciting new sounds.",
            "production_trends": "There's a growing emphasis on unique sound design and immersive experiences.",
            "cultural_influences": "Social media and global events continue to shape musical narratives.",
            "technology_impact": "New technologies are constantly changing how music is created and consumed."
        }

    async def _predict_emerging_artists(self, trend_data: Dict) -> str:
        return trend_data.get('emerging_artists', "No specific emerging artists identified yet.")

    async def _predict_genre_evolution(self, trend_data: Dict) -> str:
        return trend_data.get('genre_evolution', "Genres are seeing continuous subtle evolution.")

    async def _predict_production_trends(self, trend_data: Dict) -> str:
        return trend_data.get('production_trends', "Production techniques are becoming more experimental.")

    async def _predict_cultural_influences(self, trend_data: Dict) -> str:
        return trend_data.get('cultural_influences', "Cultural shifts are broadly influencing musical themes.")

    async def _predict_technology_impact(self, trend_data: Dict) -> str:
        return trend_data.get('technology_impact', "Technology continues to drive innovation in music.")

    async def _analyze_seasonal_preferences(self, season: str) -> Dict:
        """Analyze user's past seasonal preferences (mocked)"""
        # In a real scenario, this would look at user's listening history during past seasons.
        mock_prefs = {
            'winter': {'mood': 'contemplative', 'energy': 'low-medium', 'genres': ['folk', 'ambient', 'classical']},
            'spring': {'mood': 'optimistic', 'energy': 'medium', 'genres': ['indie pop', 'acoustic', 'electronic']},
            'summer': {'mood': 'energetic', 'energy': 'high', 'genres': ['pop', 'hip-hop', 'dance', 'reggae']},
            'autumn': {'mood': 'reflective', 'energy': 'medium-low', 'genres': ['alternative rock', 'jazz', 'blues']}
        }
        return self.seasonal_preferences.get(season, mock_prefs.get(season, {}))

    async def _get_seasonal_mood_music(self, season: str) -> List[str]:
        """Get music that matches the typical mood of the season (mocked)"""
        seasonal_mood_music = {
            'winter': ['Bon Iver - Holocene', 'Fleet Foxes - White Winter Hymnal', 'Olafur Arnalds - Reminiscence'],
            'spring': ['The Shins - New Slang', 'Vampire Weekend - A-Punk', 'Ella Fitzgerald - April in Paris'],
            'summer': ['Harry Styles - Watermelon Sugar', 'Dua Lipa - Levitating', 'Bob Marley - Three Little Birds'],
            'autumn': ['Hozier - Take Me to Church', 'The National - I Need My Girl', 'Billie Eilish - everything i wanted']
        }
        return seasonal_mood_music.get(season, [])

    async def _get_weather_appropriate_music(self, season: str) -> List[str]:
        """Get music appropriate for typical weather of the season (mocked)"""
        # This would ideally integrate with a weather API
        weather_music = {
            'winter': ['Snow Patrol - Chasing Cars', 'Coldplay - Fix You', 'Enya - Orinoco Flow'],
            'spring': ['Florence + The Machine - Dog Days Are Over', 'George Ezra - Shotgun', 'The Lumineers - Ho Hey'],
            'summer': ['Katy Perry - California Gurls', 'Beach Boys - Good Vibrations', 'Lizzo - Good as Hell'],
            'autumn': ['Taylor Swift - All Too Well', 'Ed Sheeran - Autumn Leaves', 'Norah Jones - Come Away With Me']
        }
        return weather_music.get(season, [])

    async def _get_cultural_seasonal_music(self, season: str) -> List[str]:
        """Get music related to cultural events/holidays in the season (mocked)"""
        cultural_music = {
            'winter': ['Mariah Carey - All I Want For Christmas Is You', 'Auld Lang Syne', 'Various Hanukkah songs'],
            'spring': ['Easter hymns', 'Mardi Gras music', 'Spring Break anthems'],
            'summer': ['Fourth of July anthems', 'Summer vacation hits', 'Festival music'],
            'autumn': ['Halloween spooky tunes', 'Thanksgiving reflective songs', 'Harvest festival music']
        }
        return cultural_music.get(season, [])

    async def _get_seasonal_activity_music(self, season: str) -> List[str]:
        """Get music suitable for common seasonal activities (mocked)"""
        activity_music = {
            'winter': ['Cozy fireplace jazz', 'Skiing rock anthems', 'Ice skating classical'],
            'spring': ['Gardening folk', 'Spring cleaning pop', 'Picnic instrumental'],
            'summer': ['Road trip rock', 'Beach party pop', 'Hiking electronic'],
            'autumn': ['Pumpkin patch country', 'Bonfire acoustic', 'Studying classical']
        }
        return activity_music.get(season, [])

    async def _get_seasonal_nostalgia_music(self, season: str) -> List[str]:
        """Get music that evokes nostalgia for past seasons (mocked)"""
        nostalgia_music = {
            'winter': ['Childhood Christmas carols', 'Teenage winter dance hits'],
            'spring': ['First love spring songs', 'Graduation anthems'],
            'summer': ['Summer camp singalongs', 'Classic summer road trip tunes'],
            'autumn': ['Back to school jams', 'Harvest festival folk']
        }
        return nostalgia_music.get(season, [])

    async def _generate_seasonal_insights(self, season: str, seasonal_profile: Dict) -> str:
        """Generate insights into the psychology of seasonal music preferences (mocked)"""
        insights = {
            'winter': "During winter, people often gravitate towards music that offers comfort, reflection, or a sense of warmth to counter the cold and shorter days.",
            'spring': "Spring music often reflects themes of renewal, growth, and optimism, aligning with the season's fresh start.",
            'summer': "Summer typically inspires high-energy, carefree music perfect for outdoor activities, travel, and social gatherings.",
            'autumn': "Autumnal music frequently leans into themes of reflection, change, and coziness, mirroring the season's transition and cooler temperatures."
        }
        return insights.get(season, "Seasonal music choices often subtly reflect our emotional and psychological responses to the changing environment.")

    async def _add_personal_soundtrack_touches(self, life_event: LifeEvent) -> str:
        """Add personalized touches to the life event soundtrack (mocked)"""
        # In a real scenario, this would use user's past preferences, favorite artists, etc.
        personal_touches_options = [
            "I've made sure to include artists you've enjoyed during similar emotional states in the past.",
            "This soundtrack also features a few songs that remind me of your expressed preferences for [genre/mood].",
            "I've added some instrumental tracks that I believe will resonate with the introspective moments of this event for you."
        ]
        return random.choice(personal_touches_options)


    async def handle_enhanced_message(self, message: str):
        """Enhanced message handling for new conversational features"""
        
        # Music debate triggers
        debate_patterns = [
            r"(?:i think|i believe|in my opinion).*(?:best|better|greatest|worst).*(?:music|song|album|artist|decade|genre)",
            r"(?:agree|disagree).*(?:music|song|album|artist)",
            r"(?:prefer|like).*(?:over|more than|better than).*(?:music|song|album|artist)",
            r"(?:debate|argue|discuss).*(?:music|song|album|artist)"
        ]
        
        for pattern in debate_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                # Extract position and topic
                topic_match = re.search(r'(?:best|better|greatest|worst)\s+(.*?)\s+(?:music|song|album|artist|decade|genre)', message, re.IGNORECASE)
                topic = topic_match.group(1) if topic_match else "music" # Default topic
                
                position_match = re.search(r'(?:i think|i believe|in my opinion)\s*(.*?)(?:\s+are|\s+is)?\s*(?:best|better|greatest|worst)', message, re.IGNORECASE)
                position = position_match.group(1).strip() if position_match else message.strip()
                
                await self.start_music_debate(topic, position)
                return
        
        # Continue music debate trigger
        if self.debate_context and any(word in message.lower() for word in ['i think', 'my argument is', 'but what about', 'to support my point', 'i disagree because']):
            await self.continue_music_debate(message)
            return

        # Song meaning interpretation triggers
        meaning_patterns = [
            r"what (?:does|is).*(?:song|lyrics?).*(?:mean|about|represent)",
            r"(?:meaning|interpretation) (?:of|behind).*(?:song|lyrics?)",
            r"(?:song|lyrics?) (?:meaning|interpretation|analysis)",
            r"what (?:is|are).*(?:song|lyrics?) (?:trying to say|about)"
        ]
        
        for pattern in meaning_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Extract song name and artist (more sophisticated parsing needed for robust extraction)
                song_name = None
                artist_name = None

                # Try to find text within quotes
                quoted_match = re.search(r'["\']([^"\']+)["\'](?:\s+by\s+([^"\']+))?', message)
                if quoted_match:
                    song_name = quoted_match.group(1)
                    artist_name = quoted_match.group(2)
                else:
                    # Fallback: try to extract a potential song name after keywords
                    song_keyword_match = re.search(r'(?:song|lyrics?|track)\s*(?:of|about|called)\s+(.*)', message, re.IGNORECASE)
                    if song_keyword_match:
                        potential_song_phrase = song_keyword_match.group(1).strip()
                        # Simple attempt to clean up the song phrase
                        if ' by ' in potential_song_phrase:
                            parts = potential_song_phrase.split(' by ', 1)
                            song_name = parts[0].strip()
                            artist_name = parts[1].strip()
                        else:
                            song_name = potential_song_phrase.split(' ')[0] # just take the first word as a very basic fallback
                
                if song_name:
                    await self.interpret_song_meaning(song_name, artist_name)
                    return
                else:
                    await self.session.say("I can interpret song meanings, but I need to know which song! Could you tell me the song title, and maybe the artist?")
                    return
        
        # Music therapy triggers
        therapy_patterns = [
            r"(?:i feel|i'm feeling|feeling).*(?:anxious|sad|angry|stressed|lonely|depressed|upset|down|overwhelmed)",
            r"(?:need|want).*(?:music|songs?) (?:for|to).*(?:relax|calm|feel better|cheer up|cope)",
            r"(?:music therapy|therapeutic music|healing music|calming music)",
            r"(?:bad day|rough day|difficult time|hard time|struggling)"
        ]
        
        for pattern in therapy_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Extract feeling
                feeling_match = re.search(r'(?:feel|feeling)\s*(?:a\s)?(?:bit\s)?(\w+)', message, re.IGNORECASE)
                feeling = feeling_match.group(1) if feeling_match else "unspecified"
                
                situation_match = re.search(r'(?:because of|due to|from)\s+(.*)', message, re.IGNORECASE)
                situation = situation_match.group(1) if situation_match else None

                goal_match = re.search(r'(?:to|help me)\s+(relax|calm down|feel better|cheer up|cope|process)', message, re.IGNORECASE)
                goal = goal_match.group(1) if goal_match else None

                await self.music_therapy_session(feeling, situation, goal)
                return
        
        # Music trend prediction triggers
        trend_patterns = [
            r"(?:predict|forecast).*(?:music trends|future music)",
            r"what's next in music",
            r"upcoming music trends",
            r"music predictions (?:for)? (?:next year|next \d+ months)",
            r"what genres are trending"
        ]

        for pattern in trend_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                timeframe = "next_6_months" # Default
                timeframe_match = re.search(r'(?:next year|next \d+ months)', message, re.IGNORECASE)
                if timeframe_match:
                    timeframe = timeframe_match.group(0).replace(' ', '_')
                
                genre = None
                genre_match = re.search(r'genre(?:s)? (?:like|such as)?\s*(\w+)', message, re.IGNORECASE)
                if genre_match:
                    genre = genre_match.group(1)
                
                await self.predict_music_trends(timeframe=timeframe, genre=genre)
                return

        # Seasonal music recommendations triggers
        seasonal_patterns = [
            r"(?:seasonal|current season|weather).*(?:music|songs|playlist|recommendations)",
            r"music for (?:summer|winter|spring|autumn)",
            r"what to listen to (?:this season|in the summer|etc\.)"
        ]

        for pattern in seasonal_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                override_season = None
                season_match = re.search(r'(summer|winter|spring|autumn)', message, re.IGNORECASE)
                if season_match:
                    override_season = season_match.group(1).lower()
                
                await self.seasonal_music_recommendations(override_season=override_season)
                return

        # Life event soundtrack triggers
        life_event_patterns = [
            r"(?:create|make|suggest).*(?:soundtrack|playlist).*(?:for my|for a).*(?:life event|graduation|breakup|new job|wedding|moving)",
            r"music for (?:my|a) (?:graduation|breakup|new job|wedding|moving)",
            r"what to listen to during (?:a big life event|my wedding)"
        ]

        for pattern in life_event_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                event_type = "unspecified"
                description = None
                emotional_tone = None

                event_type_match = re.search(r'(graduation|breakup|new job|wedding|moving|life event)', message, re.IGNORECASE)
                if event_type_match:
                    event_type = event_type_match.group(1)
                    
                description_match = re.search(r'for (?:my|a) (?:.*?)\s+(.*?)(?:\s+playlist|\s+soundtrack)?', message, re.IGNORECASE)
                if description_match:
                    description = description_match.group(1).strip()
                    if description.lower() in event_type: # Avoid duplicating event type in description
                        description = None

                tone_match = re.search(r'(?:feeling|tone)\s+(positive|negative|mixed|happy|sad|excited|calm)', message, re.IGNORECASE)
                if tone_match:
                    emotional_tone = tone_match.group(1)

                await self.life_event_soundtrack(event_type=event_type, description=description, emotional_tone=emotional_tone)
                return

    

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
        
        
        if interesting_facts:
            unique_facts = list(dict.fromkeys(interesting_facts))
            song_info['interesting_facts'] = ' | '.join(unique_facts[:3]) 
            song_info['all_trivia'] = unique_facts  
            
    except Exception as e:
        logger.warning(f"Error in enhanced fact extraction: {e}")



@function_tool
async def quick_song_lookup(self, query: str):
    """Quick lookup for when users ask casual questions about songs"""
    
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

    

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    session = AgentSession(allow_interruptions=False)
    await session.start(
    agent=MultilingualPipeyAgent(), 
    room=ctx.room,
    room_input_options=RoomInputOptions(video_enabled=True))


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
