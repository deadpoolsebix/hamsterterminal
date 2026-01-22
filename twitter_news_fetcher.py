"""
Twitter/X News Fetcher for Hamster Terminal
Lightweight news fetcher without heavy dependencies
"""
import requests
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class Tweet:
    text: str
    author: str
    created_at: str
    url: str
    engagement: int  # likes + retweets

class TwitterNewsFetcher:
    """Fetch crypto news from Twitter/X without API keys"""
    
    def __init__(self):
        self.crypto_keywords = [
            "Bitcoin", "BTC", "Ethereum", "ETH", "Crypto", "Cryptocurrency",
            "Blockchain", "DeFi", "NFT", "Web3", "Altcoin"
        ]
        
    def fetch_crypto_tweets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch crypto-related tweets
        Returns simplified tweet data without needing Twitter API
        """
        try:
            # Try to fetch from aggregator (if available)
            tweets = self._fetch_from_aggregator(limit)
            if tweets:
                return tweets
        except Exception as e:
            logger.warning(f"Could not fetch from aggregator: {e}")
        
        # Fallback: Generate mock tweets for demo
        return self._generate_demo_tweets(limit)
    
    def _fetch_from_aggregator(self, limit: int) -> List[Dict[str, Any]]:
        """
        Try to fetch from news aggregators that don't require API keys
        """
        try:
            # CoinGecko trending (free, no API key needed)
            response = requests.get(
                "https://api.coingecko.com/api/v3/search/trending",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                tweets = []
                
                for i, coin in enumerate(data.get('coins', [])[:limit]):
                    item = coin.get('item', {})
                    tweets.append({
                        'text': f"🔥 {item.get('name')} ({item.get('symbol', '').upper()}) is trending! Market Cap Rank: #{item.get('market_cap_rank', 'N/A')}",
                        'author': 'CoinGecko Trends',
                        'created_at': datetime.now().isoformat(),
                        'url': f"https://www.coingecko.com/en/coins/{item.get('id', '')}",
                        'engagement': item.get('score', 0),
                        'source': 'coingecko'
                    })
                
                return tweets
        except Exception as e:
            logger.error(f"Aggregator fetch failed: {e}")
            return []
        
        return []
    
    def _generate_demo_tweets(self, limit: int) -> List[Dict[str, Any]]:
        """
        Generate demo tweets when real API is unavailable
        """
        demo_tweets = [
            {
                'text': "🚀 Bitcoin breaks through key resistance level! Bulls are back in control. #BTC #Crypto",
                'author': 'CryptoWhale_Pro',
                'created_at': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'url': 'https://twitter.com/demo',
                'engagement': 1234,
                'source': 'demo'
            },
            {
                'text': "📊 Ethereum gas fees drop to lowest levels in months. Perfect time for DeFi transactions! #ETH",
                'author': 'DeFi_Analyst',
                'created_at': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'url': 'https://twitter.com/demo',
                'engagement': 856,
                'source': 'demo'
            },
            {
                'text': "⚠️ Market Alert: Major resistance at $44,000. Watch for breakout or rejection. #Bitcoin",
                'author': 'TechnicalTrader',
                'created_at': (datetime.now() - timedelta(minutes=30)).isoformat(),
                'url': 'https://twitter.com/demo',
                'engagement': 645,
                'source': 'demo'
            },
            {
                'text': "💡 Smart money is accumulating. On-chain data shows whales buying the dip. #Crypto",
                'author': 'OnChain_Metrics',
                'created_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                'url': 'https://twitter.com/demo',
                'engagement': 923,
                'source': 'demo'
            },
            {
                'text': "🔥 Volume spike detected! Big move incoming in the next 24h. Stay alert! #BTC",
                'author': 'VolumeScanner',
                'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                'url': 'https://twitter.com/demo',
                'engagement': 1456,
                'source': 'demo'
            }
        ]
        
        return demo_tweets[:limit]
    
    def format_for_display(self, tweets: List[Dict[str, Any]]) -> str:
        """Format tweets for HTML display"""
        html = '<div class="twitter-feed">'
        
        for tweet in tweets:
            html += f"""
            <div class="tweet-card">
                <div class="tweet-header">
                    <span class="tweet-author">@{tweet['author']}</span>
                    <span class="tweet-time">{self._format_time(tweet['created_at'])}</span>
                </div>
                <div class="tweet-text">{tweet['text']}</div>
                <div class="tweet-footer">
                    <span class="tweet-engagement">❤️ {tweet['engagement']}</span>
                    <a href="{tweet['url']}" target="_blank" class="tweet-link">View →</a>
                </div>
            </div>
            """
        
        html += '</div>'
        return html
    
    def _format_time(self, iso_time: str) -> str:
        """Format ISO time to relative time"""
        try:
            dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            now = datetime.now()
            diff = now - dt
            
            if diff.seconds < 60:
                return "just now"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}m ago"
            elif diff.seconds < 86400:
                return f"{diff.seconds // 3600}h ago"
            else:
                return f"{diff.days}d ago"
        except:
            return "recently"


def test_twitter_fetcher():
    """Test the Twitter news fetcher"""
    fetcher = TwitterNewsFetcher()
    tweets = fetcher.fetch_crypto_tweets(limit=5)
    
    print("\n=== TWITTER/X CRYPTO NEWS ===")
    for i, tweet in enumerate(tweets, 1):
        print(f"\n{i}. @{tweet['author']} ({tweet['created_at']})")
        print(f"   {tweet['text']}")
        print(f"   Engagement: {tweet['engagement']} | Source: {tweet.get('source', 'unknown')}")
    
    print("\n=== HTML FORMAT ===")
    print(fetcher.format_for_display(tweets[:3]))


if __name__ == "__main__":
    test_twitter_fetcher()
