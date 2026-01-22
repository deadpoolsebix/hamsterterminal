"""
📰 NEWS PROCESSOR - Genius Hamster News Feed
Fetches real-time news from multiple sources
Based on QuantMuse architecture
"""

import logging
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """News article data structure"""
    title: str
    description: str
    url: str
    source: str
    published_at: datetime
    symbol: str
    sentiment: float = 0.0


class NewsProcessor:
    """Fetch and process financial news"""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.newsapi_key = os.getenv('NEWSAPI_KEY', '')
        self.logger = logging.getLogger(__name__)
        
    def fetch_crypto_news(self, symbols: List[str] = None, days_back: int = 1) -> List[NewsItem]:
        """Fetch cryptocurrency news"""
        if symbols is None:
            symbols = ['BTC', 'ETH', 'CRYPTO']
        
        news_items = []
        
        # Try NewsAPI if available
        if self.newsapi_key:
            news_items.extend(self._fetch_from_newsapi(symbols, days_back))
        
        # Try Alpha Vantage
        news_items.extend(self._fetch_from_alpha_vantage(symbols))
        
        # Fallback to dummy data if no API keys
        if not news_items:
            news_items = self._generate_fallback_news(symbols)
        
        return news_items
    
    def _fetch_from_newsapi(self, symbols: List[str], days_back: int) -> List[NewsItem]:
        """Fetch news from NewsAPI.org"""
        news_items = []
        
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            for symbol in symbols:
                query = f"{symbol} cryptocurrency" if symbol in ['BTC', 'ETH'] else symbol
                
                url = f"https://newsapi.org/v2/everything"
                params = {
                    'q': query,
                    'from': from_date,
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'apiKey': self.newsapi_key,
                    'pageSize': 5
                }
                
                response = requests.get(url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', [])[:5]:
                        news_items.append(NewsItem(
                            title=article.get('title', ''),
                            description=article.get('description', ''),
                            url=article.get('url', ''),
                            source=article.get('source', {}).get('name', 'NewsAPI'),
                            published_at=datetime.fromisoformat(
                                article.get('publishedAt', '').replace('Z', '+00:00')
                            ),
                            symbol=symbol
                        ))
                        
        except Exception as e:
            self.logger.error(f"NewsAPI fetch failed: {e}")
        
        return news_items
    
    def _fetch_from_alpha_vantage(self, symbols: List[str]) -> List[NewsItem]:
        """Fetch news from Alpha Vantage"""
        news_items = []
        
        if self.alpha_vantage_key == 'demo':
            return news_items
        
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': 'CRYPTO:BTC',
                'apikey': self.alpha_vantage_key,
                'limit': 10
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('feed', [])[:5]:
                    news_items.append(NewsItem(
                        title=item.get('title', ''),
                        description=item.get('summary', ''),
                        url=item.get('url', ''),
                        source=item.get('source', 'Alpha Vantage'),
                        published_at=datetime.strptime(
                            item.get('time_published', '20260122T000000'),
                            '%Y%m%dT%H%M%S'
                        ),
                        symbol='BTC',
                        sentiment=float(item.get('overall_sentiment_score', 0))
                    ))
                    
        except Exception as e:
            self.logger.error(f"Alpha Vantage fetch failed: {e}")
        
        return news_items
    
    def _generate_fallback_news(self, symbols: List[str]) -> List[NewsItem]:
        """Generate sample news when APIs are unavailable"""
        fallback_headlines = [
            {
                'title': 'Bitcoin Surges Past $95,000 as Institutional Interest Grows',
                'description': 'Major institutions continue accumulating BTC amid regulatory clarity.',
                'sentiment': 0.65
            },
            {
                'title': 'Ethereum Network Upgrade Shows Strong Performance',
                'description': 'Latest protocol improvements lead to increased transaction efficiency.',
                'sentiment': 0.50
            },
            {
                'title': 'Crypto Market Sees Mixed Signals Amid Economic Data',
                'description': 'Traders remain cautious as macro indicators show conflicting trends.',
                'sentiment': 0.15
            },
            {
                'title': 'DeFi Protocol Launches Innovative Yield Strategy',
                'description': 'New automated market maker promises better returns for liquidity providers.',
                'sentiment': 0.40
            },
            {
                'title': 'Regulatory Framework Proposal Gains Bipartisan Support',
                'description': 'Lawmakers move closer to comprehensive crypto legislation.',
                'sentiment': 0.55
            }
        ]
        
        news_items = []
        for i, headline in enumerate(fallback_headlines):
            symbol = symbols[i % len(symbols)] if symbols else 'BTC'
            news_items.append(NewsItem(
                title=headline['title'],
                description=headline['description'],
                url=f"https://example.com/news/{i}",
                source="Fallback News",
                published_at=datetime.now() - timedelta(hours=i),
                symbol=symbol,
                sentiment=headline['sentiment']
            ))
        
        return news_items
    
    def fetch_all_news(self, symbols: List[str], days_back: int = 1) -> List[NewsItem]:
        """Fetch news from all available sources"""
        return self.fetch_crypto_news(symbols, days_back)
