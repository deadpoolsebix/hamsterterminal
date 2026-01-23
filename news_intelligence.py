"""
News Intelligence System
Aggregate and analyze news from multiple sources with AI sentiment
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import time
from collections import Counter

logger = logging.getLogger(__name__)


class NewsIntelligence:
    """Intelligent news aggregation and analysis"""
    
    def __init__(self):
        self.news_cache = []
        self.cache_timestamp = 0
        self.cache_duration = 300  # 5 minutes
        
        # News sources
        self.sources = {
            'coingecko': 'https://api.coingecko.com/api/v3/news',
            'cryptopanic': 'https://cryptopanic.com/api/v1/posts/',
        }
    
    def get_latest_news(self, limit: int = 20, force_refresh: bool = False) -> List[Dict]:
        """Get latest crypto news from multiple sources"""
        
        # Check cache
        if not force_refresh and self.news_cache:
            if time.time() - self.cache_timestamp < self.cache_duration:
                return self.news_cache[:limit]
        
        all_news = []
        
        # Fetch from CoinGecko
        try:
            cg_news = self._fetch_coingecko_news()
            all_news.extend(cg_news)
        except Exception as e:
            logger.warning(f"CoinGecko news fetch failed: {e}")
        
        # Fetch from demo sources if APIs fail
        if not all_news:
            all_news = self._get_demo_news()
        
        # Analyze sentiment
        for news_item in all_news:
            news_item['sentiment'] = self._analyze_sentiment(news_item.get('title', ''))
        
        # Sort by date
        all_news.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Update cache
        self.news_cache = all_news
        self.cache_timestamp = time.time()
        
        return all_news[:limit]
    
    def _fetch_coingecko_news(self) -> List[Dict]:
        """Fetch news from CoinGecko"""
        try:
            url = "https://api.coingecko.com/api/v3/news"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_list = []
            
            for item in data.get('data', [])[:15]:
                news_list.append({
                    'title': item.get('title', 'No title'),
                    'description': item.get('description', '')[:200],
                    'url': item.get('url', ''),
                    'source': item.get('source', {}).get('name', 'CoinGecko'),
                    'timestamp': item.get('published_at', datetime.now().isoformat()),
                    'image': item.get('thumb_2x', '')
                })
            
            return news_list
            
        except Exception as e:
            logger.error(f"CoinGecko news error: {e}")
            return []
    
    def _get_demo_news(self) -> List[Dict]:
        """Demo news when APIs are unavailable"""
        demo_news = [
            {
                'title': 'Bitcoin Tests Key Resistance at $96,000',
                'description': 'BTC showing strong momentum with increasing volume',
                'url': '#',
                'source': 'Crypto Daily',
                'timestamp': datetime.now().isoformat(),
                'sentiment': 'bullish'
            },
            {
                'title': 'Ethereum 2.0 Staking Hits New Record',
                'description': 'ETH staking participation reaches all-time high',
                'url': '#',
                'source': 'DeFi News',
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'sentiment': 'bullish'
            },
            {
                'title': 'SEC Delays Decision on Spot ETF Applications',
                'description': 'Regulatory uncertainty continues in crypto markets',
                'url': '#',
                'source': 'Bloomberg Crypto',
                'timestamp': (datetime.now() - timedelta(hours=4)).isoformat(),
                'sentiment': 'neutral'
            }
        ]
        return demo_news
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of news headline"""
        text_lower = text.lower()
        
        # Bullish keywords
        bullish_words = ['pump', 'rally', 'surge', 'breakout', 'bullish', 'gains', 'record', 'high', 'moon', 'adoption']
        # Bearish keywords
        bearish_words = ['dump', 'crash', 'drop', 'bearish', 'losses', 'low', 'fear', 'sell', 'decline', 'fall']
        
        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'
    
    def get_sentiment_summary(self, timeframe: str = '24h') -> Dict:
        """Get overall market sentiment from news"""
        news = self.get_latest_news(limit=50)
        
        sentiments = [item.get('sentiment', 'neutral') for item in news]
        sentiment_counts = Counter(sentiments)
        
        total = len(sentiments)
        if total == 0:
            return {
                'overall': 'neutral',
                'bullish_pct': 33.3,
                'bearish_pct': 33.3,
                'neutral_pct': 33.4
            }
        
        bullish_pct = (sentiment_counts.get('bullish', 0) / total) * 100
        bearish_pct = (sentiment_counts.get('bearish', 0) / total) * 100
        neutral_pct = (sentiment_counts.get('neutral', 0) / total) * 100
        
        # Determine overall sentiment
        if bullish_pct > 50:
            overall = 'bullish'
        elif bearish_pct > 50:
            overall = 'bearish'
        else:
            overall = 'neutral'
        
        return {
            'overall': overall,
            'bullish_pct': round(bullish_pct, 1),
            'bearish_pct': round(bearish_pct, 1),
            'neutral_pct': round(neutral_pct, 1),
            'total_articles': total,
            'timeframe': timeframe
        }
    
    def get_top_stories(self, limit: int = 3) -> List[Dict]:
        """Get top stories with Genius AI summary"""
        news = self.get_latest_news(limit=10)
        
        # Filter for most important (high impact keywords)
        impact_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'sec', 'fed', 'regulation', 'etf', 'hack', 'adoption']
        
        scored_news = []
        for item in news:
            title_lower = item['title'].lower()
            impact_score = sum(1 for keyword in impact_keywords if keyword in title_lower)
            item['impact_score'] = impact_score
            scored_news.append(item)
        
        # Sort by impact score
        scored_news.sort(key=lambda x: x['impact_score'], reverse=True)
        
        # Add Genius commentary
        for item in scored_news[:limit]:
            item['genius_take'] = self._generate_genius_take(item)
        
        return scored_news[:limit]
    
    def _generate_genius_take(self, news_item: Dict) -> str:
        """Generate Genius AI take on news item"""
        sentiment = news_item.get('sentiment', 'neutral')
        title = news_item.get('title', '')
        
        if sentiment == 'bullish':
            takes = [
                "💡 Bullish signal for the market. Could see continued momentum.",
                "🚀 This could be the catalyst for next leg up. Watch volume.",
                "📈 Positive development. Short-term traders might benefit."
            ]
        elif sentiment == 'bearish':
            takes = [
                "⚠️ Bearish pressure. Consider tightening stops.",
                "📉 Negative news flow. Wait for stabilization before entering.",
                "🛑 Risk-off sentiment. Preserve capital."
            ]
        else:
            takes = [
                "📊 Mixed signals. Monitor for direction confirmation.",
                "⏳ Wait-and-see mode. No clear catalyst yet.",
                "🔍 Neutral impact. Focus on technicals."
            ]
        
        import random
        return random.choice(takes)
    
    def search_news(self, query: str, limit: int = 10) -> List[Dict]:
        """Search news by keyword"""
        all_news = self.get_latest_news(limit=100)
        
        query_lower = query.lower()
        matches = []
        
        for item in all_news:
            title_lower = item['title'].lower()
            desc_lower = item.get('description', '').lower()
            
            if query_lower in title_lower or query_lower in desc_lower:
                matches.append(item)
        
        return matches[:limit]


# Singleton instance
_news_intel = None

def get_news_intelligence() -> NewsIntelligence:
    """Get or create News Intelligence instance"""
    global _news_intel
    if _news_intel is None:
        _news_intel = NewsIntelligence()
    return _news_intel
