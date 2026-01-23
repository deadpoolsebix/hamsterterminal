"""
Genius AI Live Chat System
Multi-language AI assistant with voice synthesis and market analysis
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# Try importing AI libraries with fallbacks
try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not available - using fallback")
    LANGCHAIN_AVAILABLE = False

try:
    from gtts import gTTS
    import io
    TTS_AVAILABLE = True
except ImportError:
    logger.warning("gTTS not available - voice disabled")
    TTS_AVAILABLE = False


class GeniusAIChat:
    """Live AI chat with market context and voice synthesis"""
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'pl': 'Polish',
        'es': 'Spanish',
        'de': 'German',
        'fr': 'French',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ja': 'Japanese'
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.chat_history: Dict[str, List] = {}  # user_id -> messages
        self.market_context: Dict = {}
        
        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                self.llm = ChatOpenAI(
                    api_key=self.api_key,
                    model="gpt-4",
                    temperature=0.7
                )
                self.ai_ready = True
                logger.info("✅ Genius AI Chat initialized with GPT-4")
            except Exception as e:
                logger.warning(f"⚠️ GPT-4 init failed: {e}")
                self.ai_ready = False
        else:
            self.ai_ready = False
            logger.info("ℹ️ Genius AI Chat in demo mode (no API key)")
    
    def get_system_prompt(self, language: str = 'en') -> str:
        """Get system prompt for Genius AI in specified language"""
        prompts = {
            'en': """You are Hamster Genius AI, a professional crypto and stock market analyst.
You provide clear, actionable insights with data-driven analysis.
Keep responses concise but informative. Use emojis sparingly for key points.
Always include risk warnings when giving market opinions.""",
            
            'pl': """Jesteś Hamster Genius AI, profesjonalnym analitykiem krypto i giełdy.
Dostarczasz jasne, konkretne wskazówki oparte na danych.
Odpowiedzi zwięzłe ale informacyjne. Używaj emoji oszczędnie dla kluczowych punktów.
Zawsze dodawaj ostrzeżenia o ryzyku przy opiniach rynkowych.""",
            
            'es': """Eres Hamster Genius AI, analista profesional de cripto y mercados.
Proporcionas información clara y accionable basada en datos.
Respuestas concisas pero informativas. Usa emojis con moderación.
Siempre incluye advertencias de riesgo en opiniones de mercado."""
        }
        return prompts.get(language, prompts['en'])
    
    def update_market_context(self, data: Dict):
        """Update current market data for context-aware responses"""
        self.market_context = {
            'timestamp': datetime.now().isoformat(),
            'btc_price': data.get('btc_price'),
            'eth_price': data.get('eth_price'),
            'market_sentiment': data.get('sentiment'),
            'trending': data.get('trending', []),
            'fear_greed': data.get('fear_greed')
        }
    
    def get_demo_response(self, message: str, language: str = 'en') -> Dict:
        """Demo response when AI is not available"""
        responses = {
            'en': {
                'market': "📊 Current market shows mixed signals. BTC consolidating around support. Monitor key levels.",
                'analysis': "🔍 Technical indicators suggest caution. Wait for clear breakout confirmation.",
                'help': "👋 I'm Hamster Genius AI! Ask me about market analysis, crypto trends, or trading strategies.",
                'default': "🤖 AI analysis available with OpenAI API key. Currently in demo mode."
            },
            'pl': {
                'market': "📊 Obecny rynek pokazuje mieszane sygnały. BTC konsoliduje wokół wsparcia.",
                'analysis': "🔍 Wskaźniki techniczne sugerują ostrożność. Czekaj na potwierdzenie wybicia.",
                'help': "👋 Jestem Hamster Genius AI! Pytaj o analizę rynku, trendy crypto, strategie.",
                'default': "🤖 Analiza AI dostępna z kluczem OpenAI API. Obecnie tryb demo."
            }
        }
        
        msg_lower = message.lower()
        lang_responses = responses.get(language, responses['en'])
        
        if any(word in msg_lower for word in ['market', 'rynek', 'price', 'cena']):
            text = lang_responses['market']
        elif any(word in msg_lower for word in ['analysis', 'analiza', 'trend']):
            text = lang_responses['analysis']
        elif any(word in msg_lower for word in ['help', 'pomoc', 'hello', 'cześć']):
            text = lang_responses['help']
        else:
            text = lang_responses['default']
        
        return {
            'response': text,
            'timestamp': datetime.now().isoformat(),
            'mode': 'demo'
        }
    
    async def chat(
        self,
        user_id: str,
        message: str,
        language: str = 'en',
        include_voice: bool = False
    ) -> Dict:
        """
        Process chat message and return AI response
        
        Args:
            user_id: Unique user identifier
            message: User's message
            language: Response language code
            include_voice: Generate voice audio
            
        Returns:
            Dict with response, voice data, and metadata
        """
        
        # Initialize chat history for new users
        if user_id not in self.chat_history:
            self.chat_history[user_id] = []
        
        # Add market context to message
        context = ""
        if self.market_context:
            context = f"\nCurrent market: BTC ${self.market_context.get('btc_price', 'N/A')}, "
            context += f"Sentiment: {self.market_context.get('market_sentiment', 'neutral')}"
        
        # Get AI response
        if self.ai_ready:
            try:
                messages = [
                    SystemMessage(content=self.get_system_prompt(language))
                ]
                
                # Add chat history (last 5 messages for context)
                for msg in self.chat_history[user_id][-5:]:
                    if msg['role'] == 'user':
                        messages.append(HumanMessage(content=msg['content']))
                    else:
                        messages.append(AIMessage(content=msg['content']))
                
                # Add current message with context
                messages.append(HumanMessage(content=message + context))
                
                # Get AI response
                response = self.llm.invoke(messages)
                response_text = response.content
                
                # Update history
                self.chat_history[user_id].append({
                    'role': 'user',
                    'content': message,
                    'timestamp': datetime.now().isoformat()
                })
                self.chat_history[user_id].append({
                    'role': 'assistant',
                    'content': response_text,
                    'timestamp': datetime.now().isoformat()
                })
                
                result = {
                    'response': response_text,
                    'timestamp': datetime.now().isoformat(),
                    'mode': 'ai',
                    'language': language
                }
                
            except Exception as e:
                logger.error(f"AI response error: {e}")
                result = self.get_demo_response(message, language)
        else:
            result = self.get_demo_response(message, language)
        
        # Generate voice if requested
        if include_voice and TTS_AVAILABLE:
            try:
                voice_data = self.generate_voice(result['response'], language)
                result['voice'] = voice_data
            except Exception as e:
                logger.warning(f"Voice generation failed: {e}")
        
        return result
    
    def generate_voice(self, text: str, language: str = 'en') -> Optional[str]:
        """Generate voice audio from text using gTTS"""
        if not TTS_AVAILABLE:
            return None
        
        try:
            # Clean text for better TTS
            clean_text = text.replace('📊', '').replace('🔍', '').replace('💡', '')
            clean_text = clean_text.replace('🚀', '').replace('⚠️', '')
            
            # Generate audio
            tts = gTTS(text=clean_text, lang=language, slow=False)
            
            # Convert to base64 for easy transport
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            import base64
            audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
            
            return audio_base64
            
        except Exception as e:
            logger.error(f"Voice generation error: {e}")
            return None
    
    def clear_history(self, user_id: str):
        """Clear chat history for user"""
        if user_id in self.chat_history:
            del self.chat_history[user_id]
    
    def get_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get chat history for user"""
        history = self.chat_history.get(user_id, [])
        return history[-limit:]


# Singleton instance
_genius_chat_instance = None

def get_genius_chat() -> GeniusAIChat:
    """Get or create Genius AI Chat instance"""
    global _genius_chat_instance
    if _genius_chat_instance is None:
        _genius_chat_instance = GeniusAIChat()
    return _genius_chat_instance
