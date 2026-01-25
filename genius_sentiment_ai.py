"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GENIUS SENTIMENT AI v1.0                                   ║
║                    GPT-Powered News Analysis                                  ║
║                                                                              ║
║  Features:                                                                   ║
║  • LLM-based news sentiment analysis                                        ║
║  • Multi-provider support (OpenAI, Anthropic, Ollama)                       ║
║  • Crypto-specific context understanding                                    ║
║  • Real-time news processing                                                ║
║  • Sentiment scoring with confidence levels                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import re

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai not installed. Run: pip install openai")

# Try to import Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Configuration
class SentimentConfig:
    """Sentiment AI Configuration"""
    
    # API Keys (from environment variables)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    
    # Default model settings
    DEFAULT_PROVIDER = 'openai'  # openai, anthropic, ollama
    OPENAI_MODEL = 'gpt-4-turbo-preview'
    ANTHROPIC_MODEL = 'claude-3-sonnet-20240229'
    OLLAMA_MODEL = 'llama2'
    
    # Analysis settings
    MAX_NEWS_ITEMS = 10
    SENTIMENT_THRESHOLD = 0.3  # Minimum absolute sentiment to consider
    CACHE_TTL_MINUTES = 5


class SentimentScore(Enum):
    """Sentiment classification"""
    VERY_BULLISH = 5
    BULLISH = 4
    SLIGHTLY_BULLISH = 3
    NEUTRAL = 2
    SLIGHTLY_BEARISH = 1
    BEARISH = 0
    VERY_BEARISH = -1


@dataclass
class NewsItem:
    """Single news item"""
    title: str
    source: str
    url: str
    published_at: datetime
    content: Optional[str] = None


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    reasoning: str
    key_factors: List[str]
    news_count: int
    timestamp: datetime


class GeniusSentimentAI:
    """
    GPT-Powered Sentiment Analysis for Trading
    
    Uses LLMs to analyze news and social media for trading signals.
    """
    
    def __init__(
        self,
        provider: str = None,
        api_key: str = None,
        model: str = None
    ):
        self.provider = provider or SentimentConfig.DEFAULT_PROVIDER
        self.api_key = api_key
        self.model = model
        
        # Set up provider-specific settings
        self._setup_provider()
        
        # Cache for recent analyses
        self.cache: Dict[str, SentimentResult] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Logger
        self.logger = logging.getLogger('GeniusSentimentAI')
        
        # Analysis history
        self.analysis_history: List[SentimentResult] = []
    
    def _setup_provider(self):
        """Setup the LLM provider"""
        
        if self.provider == 'openai':
            self.api_key = self.api_key or SentimentConfig.OPENAI_API_KEY
            self.model = self.model or SentimentConfig.OPENAI_MODEL
            if OPENAI_AVAILABLE and self.api_key:
                openai.api_key = self.api_key
        
        elif self.provider == 'anthropic':
            self.api_key = self.api_key or SentimentConfig.ANTHROPIC_API_KEY
            self.model = self.model or SentimentConfig.ANTHROPIC_MODEL
            if ANTHROPIC_AVAILABLE and self.api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=self.api_key)
        
        elif self.provider == 'ollama':
            self.ollama_url = SentimentConfig.OLLAMA_URL
            self.model = self.model or SentimentConfig.OLLAMA_MODEL
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROMPT ENGINEERING
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_analysis_prompt(self, symbol: str, news_items: List[NewsItem]) -> str:
        """Generate the analysis prompt for the LLM"""
        
        news_text = "\n".join([
            f"- [{item.source}] {item.title}"
            for item in news_items[:SentimentConfig.MAX_NEWS_ITEMS]
        ])
        
        prompt = f"""You are an expert cryptocurrency and financial market analyst. Analyze the following news headlines for {symbol} and provide a trading sentiment assessment.

NEWS HEADLINES:
{news_text}

Provide your analysis in the following JSON format:
{{
    "sentiment_score": <float from -1.0 (extremely bearish) to 1.0 (extremely bullish)>,
    "confidence": <float from 0.0 to 1.0 indicating how confident you are>,
    "sentiment_label": "<VERY_BULLISH|BULLISH|SLIGHTLY_BULLISH|NEUTRAL|SLIGHTLY_BEARISH|BEARISH|VERY_BEARISH>",
    "reasoning": "<2-3 sentence explanation of your analysis>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"],
    "market_impact": "<SHORT_TERM|MEDIUM_TERM|LONG_TERM>",
    "risk_level": "<LOW|MEDIUM|HIGH>"
}}

Consider the following in your analysis:
1. Direct price impact of news
2. Market sentiment and fear/greed
3. Regulatory implications
4. Institutional interest signals
5. Technical and fundamental factors mentioned
6. Social media and community sentiment indicators

Respond ONLY with the JSON object, no additional text."""

        return prompt
    
    def get_quick_sentiment_prompt(self, text: str) -> str:
        """Generate a quick sentiment analysis prompt"""
        
        return f"""Analyze the sentiment of this cryptocurrency news headline and respond with ONLY a JSON object:

TEXT: "{text}"

Format:
{{"score": <-1.0 to 1.0>, "sentiment": "<BULLISH|BEARISH|NEUTRAL>", "reason": "<one sentence>"}}"""

    # ═══════════════════════════════════════════════════════════════════════
    # LLM API CALLS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        
        if not OPENAI_AVAILABLE or not self.api_key:
            raise ValueError("OpenAI not available or API key not set")
        
        try:
            client = openai.AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional cryptocurrency market analyst specializing in sentiment analysis."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise
    
    async def call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        
        if not ANTHROPIC_AVAILABLE or not self.api_key:
            raise ValueError("Anthropic not available or API key not set")
        
        try:
            message = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise
    
    async def call_ollama(self, prompt: str) -> str:
        """Call local Ollama instance"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('response', '')
                    else:
                        raise ValueError(f"Ollama returned status {response.status}")
        except Exception as e:
            self.logger.error(f"Ollama API error: {e}")
            raise
    
    async def call_llm(self, prompt: str) -> str:
        """Call the configured LLM provider"""
        
        if self.provider == 'openai':
            return await self.call_openai(prompt)
        elif self.provider == 'anthropic':
            return await self.call_anthropic(prompt)
        elif self.provider == 'ollama':
            return await self.call_ollama(prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # ANALYSIS METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from LLM"""
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback parsing
        self.logger.warning("Could not parse LLM response as JSON, using fallback")
        
        return {
            'sentiment_score': 0.0,
            'confidence': 0.5,
            'sentiment_label': 'NEUTRAL',
            'reasoning': 'Could not parse LLM response',
            'key_factors': [],
            'market_impact': 'UNKNOWN',
            'risk_level': 'MEDIUM'
        }
    
    async def analyze_news(
        self,
        symbol: str,
        news_items: List[NewsItem]
    ) -> SentimentResult:
        """
        Analyze news items for a symbol using LLM
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            news_items: List of news items to analyze
            
        Returns:
            SentimentResult with analysis
        """
        
        # Check cache
        cache_key = f"{symbol}_{len(news_items)}"
        if cache_key in self.cache:
            cache_time = self.cache_timestamps.get(cache_key, datetime.min)
            if datetime.now() - cache_time < timedelta(minutes=SentimentConfig.CACHE_TTL_MINUTES):
                self.logger.info(f"Using cached sentiment for {symbol}")
                return self.cache[cache_key]
        
        # Generate prompt
        prompt = self.get_analysis_prompt(symbol, news_items)
        
        try:
            # Call LLM
            response = await self.call_llm(prompt)
            
            # Parse response
            analysis = self.parse_llm_response(response)
            
            # Create result
            result = SentimentResult(
                score=float(analysis.get('sentiment_score', 0.0)),
                confidence=float(analysis.get('confidence', 0.5)),
                sentiment=analysis.get('sentiment_label', 'NEUTRAL'),
                reasoning=analysis.get('reasoning', ''),
                key_factors=analysis.get('key_factors', []),
                news_count=len(news_items),
                timestamp=datetime.now()
            )
            
            # Cache result
            self.cache[cache_key] = result
            self.cache_timestamps[cache_key] = datetime.now()
            
            # Add to history
            self.analysis_history.append(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing news: {e}")
            # Return neutral result on error
            return SentimentResult(
                score=0.0,
                confidence=0.0,
                sentiment='NEUTRAL',
                reasoning=f'Analysis failed: {str(e)}',
                key_factors=[],
                news_count=len(news_items),
                timestamp=datetime.now()
            )
    
    async def quick_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Quick sentiment analysis of a single text
        
        Returns:
            Tuple of (score, sentiment_label)
        """
        
        prompt = self.get_quick_sentiment_prompt(text)
        
        try:
            response = await self.call_llm(prompt)
            analysis = self.parse_llm_response(response)
            return (
                float(analysis.get('score', 0.0)),
                analysis.get('sentiment', 'NEUTRAL')
            )
        except Exception as e:
            self.logger.error(f"Quick sentiment error: {e}")
            return (0.0, 'NEUTRAL')
    
    # ═══════════════════════════════════════════════════════════════════════
    # FALLBACK ANALYSIS (Without LLM)
    # ═══════════════════════════════════════════════════════════════════════
    
    def analyze_sentiment_keywords(self, text: str) -> Tuple[float, float]:
        """
        Keyword-based sentiment analysis (fallback when no LLM available)
        
        Returns:
            Tuple of (score, confidence)
        """
        
        text_lower = text.lower()
        
        # Bullish keywords with weights
        bullish_keywords = {
            'surge': 0.8, 'rally': 0.7, 'bullish': 0.9, 'breakout': 0.7,
            'all-time high': 0.9, 'ath': 0.8, 'pump': 0.6, 'moon': 0.5,
            'adoption': 0.6, 'institutional': 0.5, 'etf approved': 0.9,
            'partnership': 0.4, 'upgrade': 0.5, 'halving': 0.6,
            'accumulation': 0.5, 'buy signal': 0.7, 'support': 0.3,
            'recovery': 0.5, 'growth': 0.4, 'milestone': 0.4,
            'breakthrough': 0.6, 'positive': 0.4, 'gain': 0.5
        }
        
        # Bearish keywords with weights
        bearish_keywords = {
            'crash': -0.9, 'dump': -0.7, 'bearish': -0.9, 'breakdown': -0.7,
            'all-time low': -0.8, 'sell-off': -0.8, 'plunge': -0.8,
            'regulation': -0.4, 'ban': -0.8, 'hack': -0.9, 'exploit': -0.8,
            'fud': -0.5, 'fear': -0.6, 'panic': -0.7, 'liquidation': -0.7,
            'resistance': -0.3, 'rejection': -0.5, 'decline': -0.5,
            'warning': -0.4, 'risk': -0.3, 'negative': -0.4, 'loss': -0.5,
            'fraud': -0.9, 'scam': -0.9, 'lawsuit': -0.6
        }
        
        bullish_score = 0.0
        bearish_score = 0.0
        matches = 0
        
        for keyword, weight in bullish_keywords.items():
            if keyword in text_lower:
                bullish_score += weight
                matches += 1
        
        for keyword, weight in bearish_keywords.items():
            if keyword in text_lower:
                bearish_score += weight
                matches += 1
        
        # Calculate final score
        if matches == 0:
            return (0.0, 0.3)  # Neutral with low confidence
        
        total_score = bullish_score + bearish_score
        normalized_score = max(-1.0, min(1.0, total_score / max(matches, 1)))
        
        # Confidence based on number of matches
        confidence = min(1.0, matches * 0.15 + 0.3)
        
        return (normalized_score, confidence)
    
    def analyze_without_llm(self, news_items: List[NewsItem]) -> SentimentResult:
        """
        Analyze news without LLM using keyword analysis
        
        Use this as a fallback when API keys are not available
        """
        
        if not news_items:
            return SentimentResult(
                score=0.0,
                confidence=0.0,
                sentiment='NEUTRAL',
                reasoning='No news items to analyze',
                key_factors=[],
                news_count=0,
                timestamp=datetime.now()
            )
        
        # Analyze each headline
        scores = []
        confidences = []
        
        for item in news_items:
            score, confidence = self.analyze_sentiment_keywords(item.title)
            scores.append(score)
            confidences.append(confidence)
        
        # Weighted average
        if confidences:
            total_confidence = sum(confidences)
            if total_confidence > 0:
                avg_score = sum(s * c for s, c in zip(scores, confidences)) / total_confidence
            else:
                avg_score = 0.0
            avg_confidence = sum(confidences) / len(confidences)
        else:
            avg_score = 0.0
            avg_confidence = 0.0
        
        # Determine sentiment label
        if avg_score >= 0.6:
            sentiment = 'VERY_BULLISH'
        elif avg_score >= 0.3:
            sentiment = 'BULLISH'
        elif avg_score >= 0.1:
            sentiment = 'SLIGHTLY_BULLISH'
        elif avg_score <= -0.6:
            sentiment = 'VERY_BEARISH'
        elif avg_score <= -0.3:
            sentiment = 'BEARISH'
        elif avg_score <= -0.1:
            sentiment = 'SLIGHTLY_BEARISH'
        else:
            sentiment = 'NEUTRAL'
        
        return SentimentResult(
            score=avg_score,
            confidence=avg_confidence,
            sentiment=sentiment,
            reasoning='Keyword-based analysis (LLM not available)',
            key_factors=['Keyword matching', f'{len(news_items)} headlines analyzed'],
            news_count=len(news_items),
            timestamp=datetime.now()
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # TRADING SIGNAL INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_trading_signal(self, result: SentimentResult) -> Dict[str, Any]:
        """
        Convert sentiment result to trading signal contribution
        
        Returns:
            Dict with signal information for Genius Engine
        """
        
        # Minimum confidence threshold
        if result.confidence < 0.4:
            return {
                'active': False,
                'points': 0,
                'direction': 'NEUTRAL',
                'reason': 'Low confidence'
            }
        
        # Minimum sentiment threshold
        if abs(result.score) < SentimentConfig.SENTIMENT_THRESHOLD:
            return {
                'active': False,
                'points': 0,
                'direction': 'NEUTRAL',
                'reason': 'Sentiment too weak'
            }
        
        # Calculate points (max 15 for sentiment)
        base_points = 15
        points = int(base_points * abs(result.score) * result.confidence)
        
        # Direction
        if result.score > 0:
            direction = 'LONG'
        else:
            direction = 'SHORT'
        
        return {
            'active': True,
            'points': points,
            'direction': direction,
            'score': result.score,
            'confidence': result.confidence,
            'sentiment': result.sentiment,
            'reasoning': result.reasoning,
            'key_factors': result.key_factors
        }


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS FETCHER (Integration with existing news sources)
# ═══════════════════════════════════════════════════════════════════════════════

class NewsFetcher:
    """Fetch news from various sources"""
    
    def __init__(self):
        self.cryptopanic_api_key = os.environ.get('CRYPTOPANIC_API_KEY', '')
    
    async def fetch_cryptopanic_news(self, symbol: str = 'BTC') -> List[NewsItem]:
        """Fetch news from CryptoPanic API"""
        
        # Extract base symbol
        base_symbol = symbol.split('/')[0].upper()
        
        url = f"https://cryptopanic.com/api/v1/posts/"
        params = {
            'auth_token': self.cryptopanic_api_key,
            'currencies': base_symbol,
            'filter': 'hot',
            'public': 'true'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        
                        news_items = []
                        for item in results[:SentimentConfig.MAX_NEWS_ITEMS]:
                            news_items.append(NewsItem(
                                title=item.get('title', ''),
                                source=item.get('source', {}).get('title', 'Unknown'),
                                url=item.get('url', ''),
                                published_at=datetime.fromisoformat(
                                    item.get('published_at', datetime.now().isoformat()).replace('Z', '+00:00')
                                )
                            ))
                        
                        return news_items
                    else:
                        return []
        except Exception as e:
            logging.error(f"CryptoPanic fetch error: {e}")
            return []
    
    async def fetch_demo_news(self, symbol: str = 'BTC') -> List[NewsItem]:
        """Generate demo news for testing"""
        
        demo_headlines = [
            ("Bitcoin ETF inflows reach $500M as institutional adoption accelerates", "Bloomberg"),
            ("Major bank announces crypto custody services for institutional clients", "Reuters"),
            ("BTC breaks key resistance level, analysts predict further upside", "CoinDesk"),
            ("Regulatory clarity improves as SEC provides guidance on crypto", "The Block"),
            ("On-chain metrics show accumulation by long-term holders", "Glassnode"),
        ]
        
        return [
            NewsItem(
                title=title,
                source=source,
                url="https://example.com",
                published_at=datetime.now() - timedelta(hours=i)
            )
            for i, (title, source) in enumerate(demo_headlines)
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════════════════

async def demo_async():
    """Async demo of sentiment analysis"""
    
    print("=" * 70)
    print("🧠 GENIUS SENTIMENT AI v1.0 - DEMO")
    print("=" * 70)
    
    # Create analyzer
    analyzer = GeniusSentimentAI()
    
    # Fetch demo news
    fetcher = NewsFetcher()
    news_items = await fetcher.fetch_demo_news('BTC')
    
    print(f"\n📰 Fetched {len(news_items)} news items:")
    for item in news_items:
        print(f"   • [{item.source}] {item.title[:50]}...")
    
    # Analyze without LLM (fallback)
    print("\n🔍 Analyzing sentiment (keyword-based fallback)...")
    result = analyzer.analyze_without_llm(news_items)
    
    print(f"\n📊 SENTIMENT ANALYSIS RESULT:")
    print(f"   Score:      {result.score:+.2f}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Sentiment:  {result.sentiment}")
    print(f"   Reasoning:  {result.reasoning}")
    print(f"   Factors:    {', '.join(result.key_factors)}")
    
    # Get trading signal
    signal = analyzer.get_trading_signal(result)
    print(f"\n🎯 TRADING SIGNAL:")
    print(f"   Active:     {signal['active']}")
    print(f"   Direction:  {signal.get('direction', 'N/A')}")
    print(f"   Points:     {signal['points']}")
    
    # Test individual headline sentiment
    print("\n📰 INDIVIDUAL HEADLINE ANALYSIS:")
    test_headlines = [
        "Bitcoin crashes 15% amid market panic",
        "BTC rallies to new all-time high of $100,000",
        "Cryptocurrency market sees mixed trading"
    ]
    
    for headline in test_headlines:
        score, confidence = analyzer.analyze_sentiment_keywords(headline)
        emoji = "🟢" if score > 0.1 else "🔴" if score < -0.1 else "⚪"
        print(f"   {emoji} {score:+.2f} | {headline[:45]}...")
    
    print("\n" + "=" * 70)
    print("✅ Sentiment AI ready!")
    print("   To enable GPT: Set OPENAI_API_KEY environment variable")
    print("=" * 70)
    
    return True


def demo():
    """Synchronous demo wrapper"""
    return asyncio.run(demo_async())


if __name__ == "__main__":
    demo()
