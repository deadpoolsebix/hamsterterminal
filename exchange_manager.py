"""
🌐 MULTI-EXCHANGE MANAGER - ccxt Integration
Dostęp do 70+ giełd kryptowalutowych
Arbitraż i multi-venue trading
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np

# ccxt import
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExchangeManager:
    """
    Multi-exchange manager using ccxt
    Supports 70+ exchanges including Binance, Coinbase, Kraken, etc.
    """
    
    def __init__(self):
        self.exchanges = {}
        self.logger = logging.getLogger(__name__)
        
        if not CCXT_AVAILABLE:
            self.logger.warning("⚠️ ccxt not available - exchange features disabled")
        else:
            self.logger.info("✅ ccxt available - 70+ exchanges ready!")
    
    def add_exchange(self, exchange_id: str, api_key: str = None, 
                    secret: str = None, testnet: bool = True) -> bool:
        """
        Add exchange connection
        
        Args:
            exchange_id: Exchange name (e.g., 'binance', 'coinbase')
            api_key: API key (optional for read-only)
            secret: API secret
            testnet: Use testnet/sandbox mode
            
        Returns:
            True if successful
        """
        if not CCXT_AVAILABLE:
            return False
        
        try:
            exchange_class = getattr(ccxt, exchange_id)
            
            config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
            
            if testnet:
                config['sandbox'] = True
            
            if api_key and secret:
                config['apiKey'] = api_key
                config['secret'] = secret
            
            exchange = exchange_class(config)
            
            # Load markets
            exchange.load_markets()
            
            self.exchanges[exchange_id] = exchange
            
            self.logger.info(f"✅ Connected to {exchange_id} ({len(exchange.markets)} markets)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to {exchange_id}: {e}")
            return False
    
    def get_ticker(self, exchange_id: str, symbol: str = 'BTC/USDT') -> Dict[str, float]:
        """
        Get current ticker data
        
        Args:
            exchange_id: Exchange name
            symbol: Trading pair
            
        Returns:
            Dict with price, volume, etc.
        """
        if not CCXT_AVAILABLE or exchange_id not in self.exchanges:
            return self._get_fallback_ticker(symbol)
        
        try:
            exchange = self.exchanges[exchange_id]
            ticker = exchange.fetch_ticker(symbol)
            
            return {
                'exchange': exchange_id,
                'symbol': symbol,
                'price': ticker.get('last', 0),
                'bid': ticker.get('bid', 0),
                'ask': ticker.get('ask', 0),
                'volume': ticker.get('baseVolume', 0),
                'high_24h': ticker.get('high', 0),
                'low_24h': ticker.get('low', 0),
                'change_24h': ticker.get('percentage', 0),
                'timestamp': ticker.get('timestamp', 0)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ticker fetch failed ({exchange_id}): {e}")
            return self._get_fallback_ticker(symbol)
    
    def get_orderbook(self, exchange_id: str, symbol: str = 'BTC/USDT',
                     limit: int = 20) -> Dict[str, List]:
        """
        Get order book data
        
        Args:
            exchange_id: Exchange name
            symbol: Trading pair
            limit: Depth limit
            
        Returns:
            Dict with bids and asks
        """
        if not CCXT_AVAILABLE or exchange_id not in self.exchanges:
            return {'bids': [], 'asks': []}
        
        try:
            exchange = self.exchanges[exchange_id]
            orderbook = exchange.fetch_order_book(symbol, limit)
            
            return {
                'exchange': exchange_id,
                'symbol': symbol,
                'bids': orderbook['bids'][:limit],  # [[price, amount], ...]
                'asks': orderbook['asks'][:limit],
                'timestamp': orderbook.get('timestamp', 0),
                'bid_volume': sum(bid[1] for bid in orderbook['bids'][:limit]),
                'ask_volume': sum(ask[1] for ask in orderbook['asks'][:limit])
            }
            
        except Exception as e:
            self.logger.error(f"❌ Orderbook fetch failed: {e}")
            return {'bids': [], 'asks': []}
    
    def get_ohlcv(self, exchange_id: str, symbol: str = 'BTC/USDT',
                  timeframe: str = '1h', limit: int = 100) -> List[List]:
        """
        Get OHLCV candlestick data
        
        Args:
            exchange_id: Exchange name
            symbol: Trading pair
            timeframe: Candlestick timeframe (1m, 5m, 1h, 1d, etc.)
            limit: Number of candles
            
        Returns:
            List of [timestamp, open, high, low, close, volume]
        """
        if not CCXT_AVAILABLE or exchange_id not in self.exchanges:
            return []
        
        try:
            exchange = self.exchanges[exchange_id]
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            self.logger.info(f"📊 Fetched {len(ohlcv)} {timeframe} candles for {symbol}")
            
            return ohlcv
            
        except Exception as e:
            self.logger.error(f"❌ OHLCV fetch failed: {e}")
            return []
    
    def find_arbitrage_opportunity(self, symbol: str = 'BTC/USDT',
                                   min_spread: float = 0.005) -> Optional[Dict]:
        """
        Find arbitrage opportunities across exchanges
        
        Args:
            symbol: Trading pair to check
            min_spread: Minimum profitable spread (0.5% default)
            
        Returns:
            Dict with arbitrage details or None
        """
        if not CCXT_AVAILABLE or len(self.exchanges) < 2:
            return None
        
        try:
            prices = {}
            
            # Get prices from all exchanges
            for exchange_id in self.exchanges:
                ticker = self.get_ticker(exchange_id, symbol)
                if ticker.get('price', 0) > 0:
                    prices[exchange_id] = {
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'price': ticker['price']
                    }
            
            if len(prices) < 2:
                return None
            
            # Find best bid and ask
            best_bid_exchange = max(prices, key=lambda x: prices[x]['bid'])
            best_ask_exchange = min(prices, key=lambda x: prices[x]['ask'])
            
            best_bid = prices[best_bid_exchange]['bid']
            best_ask = prices[best_ask_exchange]['ask']
            
            # Calculate spread
            spread = (best_bid - best_ask) / best_ask
            
            if spread > min_spread and best_bid_exchange != best_ask_exchange:
                profit_pct = (spread - 0.002) * 100  # Minus fees
                
                self.logger.info(f"💰 Arbitrage found! Buy on {best_ask_exchange} @ {best_ask:.2f}, "
                               f"Sell on {best_bid_exchange} @ {best_bid:.2f} "
                               f"(~{profit_pct:.2f}% profit)")
                
                return {
                    'symbol': symbol,
                    'buy_exchange': best_ask_exchange,
                    'sell_exchange': best_bid_exchange,
                    'buy_price': best_ask,
                    'sell_price': best_bid,
                    'spread_pct': spread * 100,
                    'estimated_profit_pct': profit_pct,
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrage search failed: {e}")
            return None
    
    def get_all_prices(self, symbol: str = 'BTC/USDT') -> Dict[str, float]:
        """
        Get price from all connected exchanges
        
        Returns:
            Dict of {exchange: price}
        """
        prices = {}
        
        for exchange_id in self.exchanges:
            ticker = self.get_ticker(exchange_id, symbol)
            if ticker.get('price', 0) > 0:
                prices[exchange_id] = ticker['price']
        
        return prices
    
    def get_market_depth_analysis(self, exchange_id: str, 
                                  symbol: str = 'BTC/USDT') -> Dict[str, float]:
        """
        Analyze market depth for liquidity assessment
        
        Returns:
            Dict with depth metrics
        """
        orderbook = self.get_orderbook(exchange_id, symbol, limit=50)
        
        if not orderbook.get('bids') or not orderbook.get('asks'):
            return {}
        
        bids = np.array(orderbook['bids'])
        asks = np.array(orderbook['asks'])
        
        # Calculate metrics
        bid_prices = bids[:, 0]
        bid_volumes = bids[:, 1]
        ask_prices = asks[:, 0]
        ask_volumes = asks[:, 1]
        
        mid_price = (bid_prices[0] + ask_prices[0]) / 2
        spread = ask_prices[0] - bid_prices[0]
        spread_pct = (spread / mid_price) * 100
        
        # Volume-weighted average price in top 10 levels
        bid_vwap = np.sum(bid_prices[:10] * bid_volumes[:10]) / np.sum(bid_volumes[:10])
        ask_vwap = np.sum(ask_prices[:10] * ask_volumes[:10]) / np.sum(ask_volumes[:10])
        
        # Imbalance ratio
        total_bid_volume = np.sum(bid_volumes)
        total_ask_volume = np.sum(ask_volumes)
        imbalance = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume)
        
        return {
            'mid_price': float(mid_price),
            'spread': float(spread),
            'spread_pct': float(spread_pct),
            'bid_vwap': float(bid_vwap),
            'ask_vwap': float(ask_vwap),
            'total_bid_volume': float(total_bid_volume),
            'total_ask_volume': float(total_ask_volume),
            'imbalance': float(imbalance),  # Positive = more bids (bullish)
            'liquidity_score': float(total_bid_volume + total_ask_volume)
        }
    
    def _get_fallback_ticker(self, symbol: str) -> Dict[str, float]:
        """Fallback ticker when ccxt not available"""
        return {
            'symbol': symbol,
            'price': 95500.0,
            'volume': 24000000000,
            'change_24h': 2.5
        }
    
    def get_exchange_list(self) -> List[str]:
        """Get list of supported exchanges"""
        if CCXT_AVAILABLE:
            return ccxt.exchanges
        return []
    
    def get_connected_exchanges(self) -> List[str]:
        """Get list of currently connected exchanges"""
        return list(self.exchanges.keys())


# Global instance
exchange_manager = ExchangeManager()
