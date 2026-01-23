"""
🐹 SENTIMENT ANALYZER - Genius Hamster AI Enhancement
Analyzes market sentiment from news and social media using LLM
Based on QuantMuse architecture
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class SentimentData:
    """Sentiment analysis result"""
    timestamp: datetime
    symbol: str
    sentiment_score: float  # -1 to 1
    confidence: float  # 0 to 1
    source: str
    text: str
    keywords: List[str]
    market_impact: str = ""


class SentimentAnalyzer:
    """Market sentiment analyzer using LLM and traditional NLP"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY', '')
        self.use_openai = bool(self.openai_api_key and self.openai_api_key != 'demo')
        self.logger = logging.getLogger(__name__)
        self.vader = None

        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader = SentimentIntensityAnalyzer()
            self.logger.info("VADER sentiment available; using as primary fallback.")
        except Exception:
            # Keep silent when VADER is missing to avoid log spam on every call.
            self.vader = None
        
    def analyze_text_sentiment(self, text: str, symbol: str = None) -> SentimentData:
        """
        Analyze sentiment of financial text
        
        Args:
            text: News headline or social media post
            symbol: Trading symbol (BTC, ETH, etc.)
            
        Returns:
            SentimentData with score and confidence
        """
        if self.use_openai:
            result = self._analyze_with_openai(text, symbol)
            if result:
                return result

        if self.vader:
            result = self._analyze_with_vader(text, symbol)
            if result:
                return result

        result = self._analyze_with_textblob(text, symbol)
        if result:
            return result

        return self._create_default_sentiment(text, symbol)
    
    def _analyze_with_openai(self, text: str, symbol: str) -> SentimentData:
        """Analyze sentiment using OpenAI GPT"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            prompt = f"""
            Analyze the sentiment of this financial news for {symbol if symbol else 'the market'}.
            Consider market impact and potential price movement.
            
            Text: {text}
            
            Respond with JSON:
            {{
                "sentiment_score": <float -1 to 1>,
                "confidence": <float 0 to 1>,
                "keywords": [<list of key financial terms>],
                "market_impact": "<brief analysis>"
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial sentiment analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return SentimentData(
                timestamp=datetime.now(),
                symbol=symbol or "GENERAL",
                sentiment_score=result.get('sentiment_score', 0),
                confidence=result.get('confidence', 0.5),
                source="OpenAI",
                text=text,
                keywords=result.get('keywords', []),
                market_impact=result.get('market_impact', '')
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI sentiment analysis failed: {e}")
            return None

    def _analyze_with_vader(self, text: str, symbol: str) -> Optional[SentimentData]:
        """Fallback sentiment using VADER (no extra corpora required)."""
        try:
            if not self.vader:
                return None

            scores = self.vader.polarity_scores(text)
            compound = scores.get('compound', 0.0)
            # Confidence scaled by non-neutrality and magnitude of sentiment
            confidence = min(1.0, abs(compound) + 0.5)

            keywords = [word for word in text.lower().split() if len(word) > 4][:5]
            market_impact = "bullish" if compound > 0.2 else "bearish" if compound < -0.2 else "neutral"

            return SentimentData(
                timestamp=datetime.now(),
                symbol=symbol or "GENERAL",
                sentiment_score=compound,
                confidence=confidence,
                source="VADER",
                text=text,
                keywords=keywords,
                market_impact=market_impact
            )
        except Exception as e:
            self.logger.error(f"VADER sentiment analysis failed: {e}")
            return None
    
    def _analyze_with_textblob(self, text: str, symbol: str) -> SentimentData:
        """Fallback sentiment analysis using TextBlob"""
        try:
            from textblob import TextBlob
            
            blob = TextBlob(text.lower())
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Extract keywords
            keywords = [word for word in blob.words if len(word) > 4][:5]
            
            # Simple market impact assessment
            impact_words = {
                'bullish': ['surge', 'rally', 'breakout', 'moon', 'pump', 'bullish'],
                'bearish': ['crash', 'dump', 'collapse', 'bearish', 'decline', 'fall']
            }
            
            market_impact = "neutral"
            text_lower = text.lower()
            if any(word in text_lower for word in impact_words['bullish']):
                market_impact = "bullish"
            elif any(word in text_lower for word in impact_words['bearish']):
                market_impact = "bearish"
            
            return SentimentData(
                timestamp=datetime.now(),
                symbol=symbol or "GENERAL",
                sentiment_score=polarity,
                confidence=1.0 - subjectivity,  # More objective = more confident
                source="TextBlob",
                text=text,
                keywords=keywords,
                market_impact=market_impact
            )
            
        except Exception as e:
            # Downgrade to warning to avoid noisy logs when corpora are missing.
            self.logger.warning(f"TextBlob sentiment analysis unavailable: {e}")
            return None
    
    def _create_default_sentiment(self, text: str, symbol: str) -> SentimentData:
        """Create default neutral sentiment"""
        return SentimentData(
            timestamp=datetime.now(),
            symbol=symbol or "GENERAL",
            sentiment_score=0.0,
            confidence=0.0,
            source="Default",
            text=text,
            keywords=[]
        )
    
    def analyze_news_batch(self, news_items: List[Dict[str, Any]]) -> List[SentimentData]:
        """Analyze sentiment for multiple news items"""
        results = []
        for item in news_items:
            text = f"{item.get('title', '')} {item.get('description', '')}"
            symbol = item.get('symbol', 'GENERAL')
            sentiment = self.analyze_text_sentiment(text, symbol)
            results.append(sentiment)
        return results
    
    def calculate_market_sentiment(self, sentiment_data: List[SentimentData], 
                                  symbol: str = None) -> Dict[str, float]:
        """Calculate aggregate market sentiment metrics"""
        if not sentiment_data:
            return {
                'weighted_sentiment': 0.0,
                'confidence': 0.0,
                'sample_size': 0
            }
        
        # Filter by symbol if provided
        if symbol:
            sentiment_data = [s for s in sentiment_data if s.symbol == symbol]
        
        if not sentiment_data:
            return {'weighted_sentiment': 0.0, 'confidence': 0.0, 'sample_size': 0}
        
        # Calculate weighted sentiment
        total_weight = sum(s.confidence for s in sentiment_data)
        if total_weight > 0:
            weighted_sentiment = sum(
                s.sentiment_score * s.confidence for s in sentiment_data
            ) / total_weight
        else:
            weighted_sentiment = 0.0
        
        # Average confidence
        avg_confidence = sum(s.confidence for s in sentiment_data) / len(sentiment_data)
        
        return {
            'weighted_sentiment': weighted_sentiment,
            'confidence': avg_confidence,
            'sample_size': len(sentiment_data)
        }
    
    def generate_sentiment_signal(self, sentiment_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Generate trading signal based on sentiment"""
        sentiment = sentiment_metrics.get('weighted_sentiment', 0)
        confidence = sentiment_metrics.get('confidence', 0)
        
        # Define thresholds
        strong_bullish = sentiment > 0.3 and confidence > 0.7
        bullish = sentiment > 0.1 and confidence > 0.5
        strong_bearish = sentiment < -0.3 and confidence > 0.7
        bearish = sentiment < -0.1 and confidence > 0.5
        
        signal_strength = min(abs(sentiment) + confidence, 1.0)
        
        if strong_bullish:
            signal = 'STRONG_BUY'
        elif bullish:
            signal = 'BUY'
        elif strong_bearish:
            signal = 'STRONG_SELL'
        elif bearish:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        return {
            'signal': signal,
            'strength': signal_strength,
            'sentiment_score': sentiment,
            'confidence': confidence,
            'timestamp': datetime.now()
        }
