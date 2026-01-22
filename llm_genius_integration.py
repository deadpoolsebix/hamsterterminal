"""
🧠 LLM GENIUS INTEGRATION - AI-Powered Market Analysis
Genius Hamster's brain - powered by GPT for intelligent commentary
Based on QuantMuse LLM architecture
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)


class LLMGeniusIntegration:
    """LLM integration for Genius Hamster commentary"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', '')
        self.use_openai = bool(self.api_key and self.api_key != 'demo')
        self.logger = logging.getLogger(__name__)
        
    def analyze_market_data(self, market_data: Dict[str, Any], 
                           sentiment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate intelligent market commentary
        
        Args:
            market_data: Current market indicators (RSI, MACD, price, volume, etc.)
            sentiment_data: Sentiment analysis results
            
        Returns:
            Dict with commentary, signal, and reasoning
        """
        if self.use_openai:
            return self._analyze_with_openai(market_data, sentiment_data)
        else:
            return self._analyze_with_rules(market_data, sentiment_data)
    
    def _analyze_with_openai(self, market_data: Dict[str, Any], 
                            sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate commentary using OpenAI GPT"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key)
            
            # Build context from market data
            context = self._build_market_context(market_data, sentiment_data)
            
            prompt = f"""
            You are Genius Hamster 🐹, an expert crypto trader with a fun personality.
            Analyze this market data and provide a SHORT, witty trading commentary (max 3 sentences).
            
            Market Context:
            {json.dumps(context, indent=2)}
            
            Provide JSON response:
            {{
                "commentary": "<your witty analysis>",
                "signal": "BUY|SELL|NEUTRAL",
                "confidence": <0-100>,
                "key_factor": "<most important factor>",
                "emoji": "<relevant emoji>"
            }}
            
            Be conversational and use trading slang!
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Genius Hamster, a skilled crypto trader with personality."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                'commentary': result.get('commentary', 'Market analysis in progress...'),
                'signal': result.get('signal', 'NEUTRAL'),
                'confidence': result.get('confidence', 50),
                'reasoning': result.get('key_factor', 'Multiple factors considered'),
                'emoji': result.get('emoji', '🐹'),
                'timestamp': datetime.now().isoformat(),
                'source': 'GPT-Analysis'
            }
            
        except Exception as e:
            self.logger.error(f"OpenAI analysis failed: {e}")
            return self._analyze_with_rules(market_data, sentiment_data)
    
    def _analyze_with_rules(self, market_data: Dict[str, Any], 
                           sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based analysis (fallback)"""
        
        # Extract key indicators
        rsi = market_data.get('rsi', 50)
        macd = market_data.get('macd', 0)
        volume = market_data.get('volume_ratio', 1.0)
        sentiment = sentiment_data.get('weighted_sentiment', 0) if sentiment_data else 0
        
        # Determine signal
        bullish_signals = 0
        bearish_signals = 0
        
        # RSI analysis
        if rsi < 30:
            bullish_signals += 2
            key_factor = "RSI oversold"
        elif rsi > 70:
            bearish_signals += 2
            key_factor = "RSI overbought"
        else:
            key_factor = "RSI neutral"
        
        # MACD analysis
        if macd > 0:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # Volume analysis
        if volume > 1.5:
            bullish_signals += 1
        
        # Sentiment analysis
        if sentiment > 0.2:
            bullish_signals += 2
        elif sentiment < -0.2:
            bearish_signals += 2
        
        # Generate signal
        if bullish_signals > bearish_signals + 1:
            signal = "BUY"
            confidence = min((bullish_signals / 6) * 100, 100)
            commentary = f"🐹 Bullish vibes! {key_factor}. Volume looking good!"
            emoji = "🚀"
        elif bearish_signals > bullish_signals + 1:
            signal = "SELL"
            confidence = min((bearish_signals / 6) * 100, 100)
            commentary = f"🐹 Caution ahead! {key_factor}. Maybe wait for better entry."
            emoji = "⚠️"
        else:
            signal = "NEUTRAL"
            confidence = 50
            commentary = f"🐹 Sideways action. {key_factor}. Patience is key!"
            emoji = "😐"
        
        return {
            'commentary': commentary,
            'signal': signal,
            'confidence': int(confidence),
            'reasoning': key_factor,
            'emoji': emoji,
            'timestamp': datetime.now().isoformat(),
            'source': 'Rule-Based-Analysis'
        }
    
    def _build_market_context(self, market_data: Dict[str, Any], 
                             sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build concise market context for LLM"""
        context = {
            'price': market_data.get('price', 0),
            'rsi': market_data.get('rsi', 50),
            'macd': market_data.get('macd', 0),
            'volume_ratio': market_data.get('volume_ratio', 1.0),
            'trend': market_data.get('trend', 'neutral')
        }
        
        if sentiment_data:
            context['sentiment'] = sentiment_data.get('weighted_sentiment', 0)
            context['sentiment_confidence'] = sentiment_data.get('confidence', 0)
        
        return context
    
    def generate_risk_assessment(self, portfolio_data: Dict[str, Any], 
                                market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk assessment commentary"""
        
        risk_level = "MEDIUM"
        risk_commentary = "🐹 Risk levels looking normal. Stay alert!"
        
        # Analyze volatility
        volatility = market_conditions.get('volatility', 0)
        if volatility > 0.05:
            risk_level = "HIGH"
            risk_commentary = "🐹 High volatility! Reduce position sizes!"
        elif volatility < 0.02:
            risk_level = "LOW"
            risk_commentary = "🐹 Low volatility. Good time for entries!"
        
        # Analyze position exposure
        exposure = portfolio_data.get('exposure', 0)
        if exposure > 0.8:
            risk_commentary += " Position size is heavy!"
        
        return {
            'risk_level': risk_level,
            'commentary': risk_commentary,
            'recommendations': [
                'Monitor key support/resistance levels',
                'Use stop losses',
                'Diversify if overexposed'
            ],
            'timestamp': datetime.now().isoformat()
        }
