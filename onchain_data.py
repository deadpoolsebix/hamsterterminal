"""
On-Chain Data Integration
Real-time blockchain metrics from CoinGecko and CoinGlass
"""

import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class OnChainDataProvider:
    """Fetch on-chain metrics and advanced crypto data"""
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get cached data if still valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _set_cache(self, key: str, data: Dict):
        """Cache data with timestamp"""
        self.cache[key] = (data, time.time())
    
    def get_trending_coins(self) -> Dict:
        """Get trending coins from CoinGecko"""
        cache_key = "trending"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.coingecko_base}/search/trending"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Format trending coins
            trending = []
            for item in data.get('coins', [])[:10]:
                coin = item.get('item', {})
                trending.append({
                    'symbol': coin.get('symbol', 'N/A').upper(),
                    'name': coin.get('name', 'Unknown'),
                    'rank': coin.get('market_cap_rank', 999),
                    'price_btc': coin.get('price_btc', 0),
                    'thumb': coin.get('thumb', ''),
                    'score': coin.get('score', 0)
                })
            
            result = {
                'trending': trending,
                'timestamp': datetime.now().isoformat(),
                'source': 'CoinGecko'
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Trending coins error: {e}")
            return {'trending': [], 'error': str(e)}
    
    def get_global_metrics(self) -> Dict:
        """Get global crypto market metrics"""
        cache_key = "global"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.coingecko_base}/global"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json().get('data', {})
            
            result = {
                'total_market_cap_usd': data.get('total_market_cap', {}).get('usd', 0),
                'total_volume_24h': data.get('total_volume', {}).get('usd', 0),
                'btc_dominance': data.get('market_cap_percentage', {}).get('btc', 0),
                'eth_dominance': data.get('market_cap_percentage', {}).get('eth', 0),
                'active_cryptocurrencies': data.get('active_cryptocurrencies', 0),
                'markets': data.get('markets', 0),
                'market_cap_change_24h': data.get('market_cap_change_percentage_24h_usd', 0),
                'timestamp': datetime.now().isoformat(),
                'source': 'CoinGecko'
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Global metrics error: {e}")
            return {'error': str(e)}
    
    def get_fear_greed_index(self) -> Dict:
        """Get Crypto Fear & Greed Index"""
        cache_key = "fear_greed"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Alternative API for Fear & Greed
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json().get('data', [{}])[0]
            
            value = int(data.get('value', 50))
            
            # Classify sentiment
            if value >= 75:
                classification = 'Extreme Greed'
            elif value >= 55:
                classification = 'Greed'
            elif value >= 45:
                classification = 'Neutral'
            elif value >= 25:
                classification = 'Fear'
            else:
                classification = 'Extreme Fear'
            
            result = {
                'value': value,
                'classification': classification,
                'timestamp': data.get('timestamp', ''),
                'source': 'Alternative.me'
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Fear & Greed error: {e}")
            return {
                'value': 50,
                'classification': 'Neutral',
                'error': str(e)
            }
    
    def get_exchange_volumes(self) -> List[Dict]:
        """Get top exchanges by volume"""
        cache_key = "exchanges"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.coingecko_base}/exchanges"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            exchanges = []
            for ex in response.json()[:10]:
                exchanges.append({
                    'name': ex.get('name', 'Unknown'),
                    'volume_24h_btc': ex.get('trade_volume_24h_btc', 0),
                    'trust_score': ex.get('trust_score', 0),
                    'trust_score_rank': ex.get('trust_score_rank', 999),
                    'year_established': ex.get('year_established')
                })
            
            result = {
                'exchanges': exchanges,
                'timestamp': datetime.now().isoformat()
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Exchange volumes error: {e}")
            return {'exchanges': [], 'error': str(e)}
    
    def get_defi_metrics(self) -> Dict:
        """Get DeFi protocol metrics"""
        cache_key = "defi"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.coingecko_base}/global/decentralized_finance_defi"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json().get('data', {})
            
            result = {
                'defi_market_cap': data.get('defi_market_cap', 0),
                'eth_market_cap': data.get('eth_market_cap', 0),
                'defi_to_eth_ratio': data.get('defi_to_eth_ratio', 0),
                'trading_volume_24h': data.get('trading_volume_24h', 0),
                'defi_dominance': data.get('defi_dominance', 0),
                'top_coin_name': data.get('top_coin_name', 'N/A'),
                'timestamp': datetime.now().isoformat(),
                'source': 'CoinGecko'
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"DeFi metrics error: {e}")
            return {'error': str(e)}
    
    def get_categories(self) -> List[Dict]:
        """Get crypto categories with market data"""
        cache_key = "categories"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.coingecko_base}/coins/categories"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            categories = []
            for cat in response.json()[:15]:
                categories.append({
                    'name': cat.get('name', 'Unknown'),
                    'market_cap': cat.get('market_cap', 0),
                    'market_cap_change_24h': cat.get('market_cap_change_24h', 0),
                    'volume_24h': cat.get('volume_24h', 0),
                    'top_3_coins': cat.get('top_3_coins', [])
                })
            
            result = {
                'categories': categories,
                'timestamp': datetime.now().isoformat()
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Categories error: {e}")
            return {'categories': [], 'error': str(e)}
    
    def get_nft_data(self) -> Dict:
        """Get NFT market overview"""
        cache_key = "nft"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.coingecko_base}/nfts/list"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            nfts = response.json()[:10]
            
            result = {
                'top_collections': [{
                    'name': nft.get('name', 'Unknown'),
                    'symbol': nft.get('symbol', 'N/A'),
                    'floor_price_eth': nft.get('floor_price', {}).get('native_currency', 0)
                } for nft in nfts],
                'timestamp': datetime.now().isoformat(),
                'source': 'CoinGecko'
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"NFT data error: {e}")
            return {'top_collections': [], 'error': str(e)}


# Singleton instance
_onchain_provider = None

def get_onchain_provider() -> OnChainDataProvider:
    """Get or create OnChain data provider instance"""
    global _onchain_provider
    if _onchain_provider is None:
        _onchain_provider = OnChainDataProvider()
    return _onchain_provider
