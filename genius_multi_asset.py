"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GENIUS MULTI-ASSET TRADING v1.0                            ║
║                    Cross-Asset Trading Platform                               ║
║                                                                              ║
║  Features:                                                                   ║
║  • Cryptocurrency (BTC, ETH, SOL, etc.)                                     ║
║  • Forex (EUR/USD, GBP/USD, USD/JPY, etc.)                                 ║
║  • Stocks & ETFs (AAPL, TSLA, SPY, QQQ)                                    ║
║  • Commodities (Gold, Silver, Oil)                                         ║
║  • Cross-Asset Correlation Analysis                                         ║
║  • Unified Signal Generation                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

# Data providers
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance not installed. Run: pip install yfinance")

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    print("⚠️ ccxt not installed for crypto data")


class AssetClass(Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCKS = "stocks"
    ETF = "etf"
    COMMODITIES = "commodities"
    INDICES = "indices"


@dataclass
class AssetInfo:
    """Asset information"""
    symbol: str
    name: str
    asset_class: AssetClass
    exchange: str
    currency: str
    trading_hours: str
    min_lot_size: float
    tick_size: float
    leverage_available: bool
    typical_spread_pct: float


@dataclass
class MarketData:
    """Market data for an asset"""
    symbol: str
    asset_class: AssetClass
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    change_pct: Optional[float] = None


@dataclass
class CrossAssetSignal:
    """Signal for multi-asset trading"""
    symbol: str
    asset_class: AssetClass
    direction: str  # LONG, SHORT, NEUTRAL
    strength: float  # 0-100
    confidence: float  # 0-1
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    correlation_context: Dict[str, float]  # Correlations with other assets
    timestamp: datetime = field(default_factory=datetime.now)


class GeniusMultiAsset:
    """
    Multi-Asset Trading Platform
    
    Supports:
    - Cryptocurrency: BTC, ETH, SOL, XRP, etc.
    - Forex: EUR/USD, GBP/USD, USD/JPY, etc.
    - Stocks: AAPL, MSFT, TSLA, NVDA, etc.
    - ETFs: SPY, QQQ, IWM, GLD, etc.
    - Commodities: Gold, Silver, Oil
    - Indices: S&P 500, NASDAQ, DJI
    """
    
    # Asset definitions
    ASSETS = {
        # Cryptocurrency
        'BTC/USDT': AssetInfo('BTC/USDT', 'Bitcoin', AssetClass.CRYPTO, 'Binance', 'USDT', '24/7', 0.001, 0.01, True, 0.05),
        'ETH/USDT': AssetInfo('ETH/USDT', 'Ethereum', AssetClass.CRYPTO, 'Binance', 'USDT', '24/7', 0.01, 0.01, True, 0.05),
        'SOL/USDT': AssetInfo('SOL/USDT', 'Solana', AssetClass.CRYPTO, 'Binance', 'USDT', '24/7', 0.1, 0.01, True, 0.08),
        'XRP/USDT': AssetInfo('XRP/USDT', 'Ripple', AssetClass.CRYPTO, 'Binance', 'USDT', '24/7', 1.0, 0.0001, True, 0.10),
        'BNB/USDT': AssetInfo('BNB/USDT', 'BNB', AssetClass.CRYPTO, 'Binance', 'USDT', '24/7', 0.01, 0.01, True, 0.06),
        
        # Forex
        'EUR/USD': AssetInfo('EUR/USD', 'Euro/Dollar', AssetClass.FOREX, 'FOREX', 'USD', 'Sun-Fri', 1000, 0.00001, True, 0.01),
        'GBP/USD': AssetInfo('GBP/USD', 'Pound/Dollar', AssetClass.FOREX, 'FOREX', 'USD', 'Sun-Fri', 1000, 0.00001, True, 0.02),
        'USD/JPY': AssetInfo('USD/JPY', 'Dollar/Yen', AssetClass.FOREX, 'FOREX', 'JPY', 'Sun-Fri', 1000, 0.001, True, 0.01),
        'USD/CHF': AssetInfo('USD/CHF', 'Dollar/Franc', AssetClass.FOREX, 'FOREX', 'CHF', 'Sun-Fri', 1000, 0.00001, True, 0.02),
        'AUD/USD': AssetInfo('AUD/USD', 'Aussie/Dollar', AssetClass.FOREX, 'FOREX', 'USD', 'Sun-Fri', 1000, 0.00001, True, 0.02),
        
        # Stocks
        'AAPL': AssetInfo('AAPL', 'Apple Inc.', AssetClass.STOCKS, 'NASDAQ', 'USD', 'NYSE Hours', 1, 0.01, False, 0.02),
        'MSFT': AssetInfo('MSFT', 'Microsoft', AssetClass.STOCKS, 'NASDAQ', 'USD', 'NYSE Hours', 1, 0.01, False, 0.02),
        'TSLA': AssetInfo('TSLA', 'Tesla', AssetClass.STOCKS, 'NASDAQ', 'USD', 'NYSE Hours', 1, 0.01, False, 0.05),
        'NVDA': AssetInfo('NVDA', 'NVIDIA', AssetClass.STOCKS, 'NASDAQ', 'USD', 'NYSE Hours', 1, 0.01, False, 0.03),
        'AMZN': AssetInfo('AMZN', 'Amazon', AssetClass.STOCKS, 'NASDAQ', 'USD', 'NYSE Hours', 1, 0.01, False, 0.02),
        'GOOGL': AssetInfo('GOOGL', 'Alphabet', AssetClass.STOCKS, 'NASDAQ', 'USD', 'NYSE Hours', 1, 0.01, False, 0.02),
        'META': AssetInfo('META', 'Meta Platforms', AssetClass.STOCKS, 'NASDAQ', 'USD', 'NYSE Hours', 1, 0.01, False, 0.03),
        
        # ETFs
        'SPY': AssetInfo('SPY', 'S&P 500 ETF', AssetClass.ETF, 'NYSE', 'USD', 'NYSE Hours', 1, 0.01, False, 0.01),
        'QQQ': AssetInfo('QQQ', 'NASDAQ 100 ETF', AssetClass.ETF, 'NASDAQ', 'USD', 'NYSE Hours', 1, 0.01, False, 0.01),
        'IWM': AssetInfo('IWM', 'Russell 2000 ETF', AssetClass.ETF, 'NYSE', 'USD', 'NYSE Hours', 1, 0.01, False, 0.02),
        'GLD': AssetInfo('GLD', 'Gold ETF', AssetClass.ETF, 'NYSE', 'USD', 'NYSE Hours', 1, 0.01, False, 0.02),
        'SLV': AssetInfo('SLV', 'Silver ETF', AssetClass.ETF, 'NYSE', 'USD', 'NYSE Hours', 1, 0.01, False, 0.03),
        'USO': AssetInfo('USO', 'Oil ETF', AssetClass.ETF, 'NYSE', 'USD', 'NYSE Hours', 1, 0.01, False, 0.04),
        
        # Commodities (via futures/CFD symbols)
        'GC=F': AssetInfo('GC=F', 'Gold Futures', AssetClass.COMMODITIES, 'COMEX', 'USD', 'Sun-Fri', 1, 0.1, True, 0.02),
        'SI=F': AssetInfo('SI=F', 'Silver Futures', AssetClass.COMMODITIES, 'COMEX', 'USD', 'Sun-Fri', 1, 0.01, True, 0.03),
        'CL=F': AssetInfo('CL=F', 'Crude Oil Futures', AssetClass.COMMODITIES, 'NYMEX', 'USD', 'Sun-Fri', 1, 0.01, True, 0.05),
        
        # Indices
        '^GSPC': AssetInfo('^GSPC', 'S&P 500', AssetClass.INDICES, 'INDEX', 'USD', 'NYSE Hours', 1, 0.01, False, 0.01),
        '^IXIC': AssetInfo('^IXIC', 'NASDAQ Composite', AssetClass.INDICES, 'INDEX', 'USD', 'NYSE Hours', 1, 0.01, False, 0.01),
        '^DJI': AssetInfo('^DJI', 'Dow Jones', AssetClass.INDICES, 'INDEX', 'USD', 'NYSE Hours', 1, 0.01, False, 0.01),
    }
    
    def __init__(self):
        """Initialize multi-asset platform"""
        self.logger = logging.getLogger('MultiAsset')
        self.cache: Dict[str, MarketData] = {}
        self.historical_data: Dict[str, pd.DataFrame] = {}
        
        # Initialize exchange for crypto
        if CCXT_AVAILABLE:
            self.crypto_exchange = ccxt.binance({
                'enableRateLimit': True
            })
        else:
            self.crypto_exchange = None
    
    # ═══════════════════════════════════════════════════════════════════════
    # DATA FETCHING
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """
        Get current market data for any asset
        """
        
        asset_info = self.ASSETS.get(symbol)
        if not asset_info:
            self.logger.warning(f"Unknown symbol: {symbol}")
            return None
        
        try:
            if asset_info.asset_class == AssetClass.CRYPTO:
                return self._get_crypto_data(symbol, asset_info)
            else:
                return self._get_traditional_data(symbol, asset_info)
        except Exception as e:
            self.logger.error(f"Failed to get data for {symbol}: {e}")
            return None
    
    def _get_crypto_data(self, symbol: str, asset_info: AssetInfo) -> Optional[MarketData]:
        """Get crypto data via CCXT"""
        
        if not self.crypto_exchange:
            return None
        
        try:
            ticker = self.crypto_exchange.fetch_ticker(symbol)
            
            return MarketData(
                symbol=symbol,
                asset_class=AssetClass.CRYPTO,
                open=ticker.get('open', 0),
                high=ticker.get('high', 0),
                low=ticker.get('low', 0),
                close=ticker.get('last', 0),
                volume=ticker.get('quoteVolume', 0),
                timestamp=datetime.now(),
                bid=ticker.get('bid'),
                ask=ticker.get('ask'),
                change_pct=ticker.get('percentage')
            )
        except Exception as e:
            self.logger.error(f"Crypto data error: {e}")
            return None
    
    def _get_traditional_data(self, symbol: str, asset_info: AssetInfo) -> Optional[MarketData]:
        """Get traditional asset data via yfinance"""
        
        if not YFINANCE_AVAILABLE:
            return None
        
        try:
            # Convert forex symbols
            yf_symbol = symbol
            if asset_info.asset_class == AssetClass.FOREX:
                yf_symbol = symbol.replace('/', '') + '=X'
            
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period='1d')
            
            if hist.empty:
                return None
            
            row = hist.iloc[-1]
            
            return MarketData(
                symbol=symbol,
                asset_class=asset_info.asset_class,
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row.get('Volume', 0),
                timestamp=datetime.now(),
                change_pct=((row['Close'] - row['Open']) / row['Open']) * 100
            )
        except Exception as e:
            self.logger.error(f"Traditional data error: {e}")
            return None
    
    def get_historical_data(
        self,
        symbol: str,
        period: str = '3mo',
        interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """Get historical OHLCV data"""
        
        asset_info = self.ASSETS.get(symbol)
        if not asset_info:
            return None
        
        try:
            if asset_info.asset_class == AssetClass.CRYPTO:
                return self._get_crypto_historical(symbol, period, interval)
            else:
                return self._get_traditional_historical(symbol, asset_info, period, interval)
        except Exception as e:
            self.logger.error(f"Historical data error for {symbol}: {e}")
            return None
    
    def _get_crypto_historical(
        self,
        symbol: str,
        period: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Get crypto historical via CCXT"""
        
        if not self.crypto_exchange:
            return None
        
        # Convert period to since timestamp
        period_map = {
            '1mo': 30, '3mo': 90, '6mo': 180, '1y': 365
        }
        days = period_map.get(period, 90)
        since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        # Convert interval
        timeframe_map = {
            '1d': '1d', '1h': '1h', '4h': '4h', '1w': '1w'
        }
        timeframe = timeframe_map.get(interval, '1d')
        
        try:
            ohlcv = self.crypto_exchange.fetch_ohlcv(symbol, timeframe, since)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        except Exception as e:
            self.logger.error(f"Crypto historical error: {e}")
            return None
    
    def _get_traditional_historical(
        self,
        symbol: str,
        asset_info: AssetInfo,
        period: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Get traditional historical via yfinance"""
        
        if not YFINANCE_AVAILABLE:
            return None
        
        yf_symbol = symbol
        if asset_info.asset_class == AssetClass.FOREX:
            yf_symbol = symbol.replace('/', '') + '=X'
        
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period, interval=interval)
            return df
        except Exception as e:
            self.logger.error(f"Traditional historical error: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════════
    # CORRELATION ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_correlations(
        self,
        symbols: List[str],
        period: str = '3mo'
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between assets
        """
        
        returns_data = {}
        
        for symbol in symbols:
            df = self.get_historical_data(symbol, period)
            if df is not None and not df.empty:
                returns = df['Close'].pct_change().dropna()
                returns_data[symbol] = returns
        
        if not returns_data:
            return pd.DataFrame()
        
        returns_df = pd.DataFrame(returns_data)
        correlation_matrix = returns_df.corr()
        
        return correlation_matrix
    
    def find_uncorrelated_pairs(
        self,
        symbols: List[str],
        threshold: float = 0.3
    ) -> List[Tuple[str, str, float]]:
        """Find pairs with low correlation for diversification"""
        
        corr_matrix = self.calculate_correlations(symbols)
        
        if corr_matrix.empty:
            return []
        
        pairs = []
        
        for i, s1 in enumerate(corr_matrix.columns):
            for j, s2 in enumerate(corr_matrix.columns):
                if i < j:
                    corr = corr_matrix.loc[s1, s2]
                    if abs(corr) < threshold:
                        pairs.append((s1, s2, corr))
        
        # Sort by correlation (lowest first)
        pairs.sort(key=lambda x: abs(x[2]))
        
        return pairs
    
    def find_correlated_pairs(
        self,
        symbols: List[str],
        threshold: float = 0.7
    ) -> List[Tuple[str, str, float]]:
        """Find highly correlated pairs for pair trading"""
        
        corr_matrix = self.calculate_correlations(symbols)
        
        if corr_matrix.empty:
            return []
        
        pairs = []
        
        for i, s1 in enumerate(corr_matrix.columns):
            for j, s2 in enumerate(corr_matrix.columns):
                if i < j:
                    corr = corr_matrix.loc[s1, s2]
                    if corr > threshold:
                        pairs.append((s1, s2, corr))
        
        # Sort by correlation (highest first)
        pairs.sort(key=lambda x: x[2], reverse=True)
        
        return pairs
    
    # ═══════════════════════════════════════════════════════════════════════
    # SIGNAL GENERATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_signal(
        self,
        symbol: str,
        related_symbols: List[str] = None
    ) -> Optional[CrossAssetSignal]:
        """
        Generate trading signal for an asset
        """
        
        asset_info = self.ASSETS.get(symbol)
        if not asset_info:
            return None
        
        # Get historical data
        df = self.get_historical_data(symbol, period='3mo')
        if df is None or df.empty:
            return None
        
        # Calculate indicators
        close = df['Close']
        
        # Moving averages
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        
        # MACD
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9).mean()
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        bb_middle = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std
        
        # Current values
        current_price = close.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd.iloc[-1]
        current_signal = signal_line.iloc[-1]
        
        # Generate signal
        score = 0
        max_score = 100
        
        # Trend (40 points)
        if current_price > sma_20.iloc[-1] > sma_50.iloc[-1]:
            score += 40  # Strong uptrend
        elif current_price < sma_20.iloc[-1] < sma_50.iloc[-1]:
            score -= 40  # Strong downtrend
        elif current_price > sma_20.iloc[-1]:
            score += 20
        elif current_price < sma_20.iloc[-1]:
            score -= 20
        
        # MACD (30 points)
        if current_macd > current_signal:
            score += 30
        else:
            score -= 30
        
        # RSI (30 points)
        if current_rsi < 30:
            score += 30  # Oversold
        elif current_rsi > 70:
            score -= 30  # Overbought
        elif current_rsi < 50:
            score += 15
        else:
            score -= 15
        
        # Determine direction
        if score >= 30:
            direction = 'LONG'
        elif score <= -30:
            direction = 'SHORT'
        else:
            direction = 'NEUTRAL'
        
        # Calculate stop loss and take profit
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        
        if direction == 'LONG':
            stop_loss = current_price - 2 * atr
            take_profit = current_price + 3 * atr
        elif direction == 'SHORT':
            stop_loss = current_price + 2 * atr
            take_profit = current_price - 3 * atr
        else:
            stop_loss = current_price - 2 * atr
            take_profit = current_price + 2 * atr
        
        # Risk/reward ratio
        risk = abs(current_price - stop_loss)
        reward = abs(take_profit - current_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        # Correlation context
        correlations = {}
        if related_symbols:
            corr_matrix = self.calculate_correlations([symbol] + related_symbols)
            if not corr_matrix.empty:
                for s in related_symbols:
                    if s in corr_matrix.columns:
                        correlations[s] = corr_matrix.loc[symbol, s]
        
        return CrossAssetSignal(
            symbol=symbol,
            asset_class=asset_info.asset_class,
            direction=direction,
            strength=abs(score),
            confidence=min(abs(score) / max_score, 1.0),
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=risk_reward,
            correlation_context=correlations
        )
    
    def scan_all_assets(
        self,
        asset_classes: List[AssetClass] = None
    ) -> List[CrossAssetSignal]:
        """
        Scan all assets for signals
        """
        
        signals = []
        
        for symbol, info in self.ASSETS.items():
            if asset_classes and info.asset_class not in asset_classes:
                continue
            
            try:
                signal = self.generate_signal(symbol)
                if signal and signal.direction != 'NEUTRAL':
                    signals.append(signal)
            except Exception as e:
                self.logger.warning(f"Failed to scan {symbol}: {e}")
        
        # Sort by strength
        signals.sort(key=lambda x: x.strength, reverse=True)
        
        return signals
    
    # ═══════════════════════════════════════════════════════════════════════
    # PORTFOLIO ALLOCATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def suggest_allocation(
        self,
        capital: float,
        risk_tolerance: str = 'moderate',
        preferred_classes: List[AssetClass] = None
    ) -> Dict[str, float]:
        """
        Suggest portfolio allocation across asset classes
        
        Args:
            capital: Total capital
            risk_tolerance: 'conservative', 'moderate', 'aggressive'
            preferred_classes: Preferred asset classes
        """
        
        # Base allocations by risk tolerance
        allocations = {
            'conservative': {
                AssetClass.STOCKS: 0.30,
                AssetClass.ETF: 0.30,
                AssetClass.COMMODITIES: 0.20,
                AssetClass.CRYPTO: 0.10,
                AssetClass.FOREX: 0.10,
            },
            'moderate': {
                AssetClass.STOCKS: 0.35,
                AssetClass.ETF: 0.20,
                AssetClass.COMMODITIES: 0.15,
                AssetClass.CRYPTO: 0.20,
                AssetClass.FOREX: 0.10,
            },
            'aggressive': {
                AssetClass.STOCKS: 0.30,
                AssetClass.ETF: 0.10,
                AssetClass.COMMODITIES: 0.10,
                AssetClass.CRYPTO: 0.40,
                AssetClass.FOREX: 0.10,
            }
        }
        
        base_alloc = allocations.get(risk_tolerance, allocations['moderate'])
        
        # Adjust for preferred classes
        if preferred_classes:
            for asset_class in preferred_classes:
                if asset_class in base_alloc:
                    base_alloc[asset_class] += 0.10
            
            # Normalize
            total = sum(base_alloc.values())
            base_alloc = {k: v / total for k, v in base_alloc.items()}
        
        # Calculate dollar amounts
        allocation = {
            asset_class.value: capital * pct
            for asset_class, pct in base_alloc.items()
        }
        
        return allocation
    
    def get_available_assets(
        self,
        asset_class: AssetClass = None
    ) -> List[AssetInfo]:
        """Get list of available assets"""
        
        assets = []
        
        for symbol, info in self.ASSETS.items():
            if asset_class is None or info.asset_class == asset_class:
                assets.append(info)
        
        return assets


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demo the multi-asset platform"""
    
    print("=" * 70)
    print("🌐 GENIUS MULTI-ASSET TRADING v1.0 - DEMO")
    print("=" * 70)
    
    print(f"\n📦 Dependencies:")
    print(f"   yfinance: {'✅' if YFINANCE_AVAILABLE else '❌'}")
    print(f"   ccxt: {'✅' if CCXT_AVAILABLE else '❌'}")
    
    platform = GeniusMultiAsset()
    
    # 1. Available Assets
    print("\n" + "─" * 50)
    print("1️⃣ AVAILABLE ASSET CLASSES")
    
    for asset_class in AssetClass:
        assets = platform.get_available_assets(asset_class)
        print(f"\n   {asset_class.value.upper()} ({len(assets)} assets):")
        for asset in assets[:3]:
            print(f"      • {asset.symbol}: {asset.name}")
        if len(assets) > 3:
            print(f"      ... and {len(assets) - 3} more")
    
    # 2. Market Data (simulated if not available)
    print("\n" + "─" * 50)
    print("2️⃣ SAMPLE MARKET DATA")
    
    sample_assets = ['BTC/USDT', 'AAPL', 'EUR/USD', 'GLD', '^GSPC']
    
    for symbol in sample_assets:
        info = platform.ASSETS.get(symbol)
        if info:
            print(f"   {symbol:12s} ({info.asset_class.value:12s}): {info.name}")
    
    # 3. Correlation Analysis (simulated)
    print("\n" + "─" * 50)
    print("3️⃣ CORRELATION MATRIX (Simulated)")
    
    # Simulated correlation data
    symbols = ['BTC', 'ETH', 'SPY', 'GLD', 'EUR']
    np.random.seed(42)
    
    # Create realistic correlations
    corr_data = {
        'BTC': [1.00, 0.85, 0.35, -0.10, 0.15],
        'ETH': [0.85, 1.00, 0.40, -0.05, 0.20],
        'SPY': [0.35, 0.40, 1.00, -0.20, 0.30],
        'GLD': [-0.10, -0.05, -0.20, 1.00, 0.45],
        'EUR': [0.15, 0.20, 0.30, 0.45, 1.00],
    }
    
    print("\n         BTC    ETH    SPY    GLD    EUR")
    for s1 in symbols:
        row = f"   {s1:4s}"
        for i, s2 in enumerate(symbols):
            row += f"  {corr_data[s1][i]:+.2f}"
        print(row)
    
    # 4. Uncorrelated Pairs
    print("\n" + "─" * 50)
    print("4️⃣ DIVERSIFICATION OPPORTUNITIES (Low Correlation)")
    
    uncorrelated = [
        ('BTC/USDT', 'GLD', -0.10),
        ('ETH/USDT', 'GLD', -0.05),
        ('EUR/USD', 'BTC/USDT', 0.15),
    ]
    
    for s1, s2, corr in uncorrelated:
        print(f"   {s1} + {s2}: correlation = {corr:+.2f}")
    
    # 5. Pair Trading Candidates
    print("\n" + "─" * 50)
    print("5️⃣ PAIR TRADING CANDIDATES (High Correlation)")
    
    correlated = [
        ('BTC/USDT', 'ETH/USDT', 0.85),
        ('SPY', 'QQQ', 0.92),
        ('GLD', 'SLV', 0.88),
    ]
    
    for s1, s2, corr in correlated:
        print(f"   {s1} + {s2}: correlation = {corr:+.2f}")
    
    # 6. Portfolio Allocation
    print("\n" + "─" * 50)
    print("6️⃣ SUGGESTED PORTFOLIO ALLOCATION")
    
    for tolerance in ['conservative', 'moderate', 'aggressive']:
        allocation = platform.suggest_allocation(100000, tolerance)
        print(f"\n   {tolerance.upper()} ($100,000):")
        for asset_class, amount in sorted(allocation.items(), key=lambda x: -x[1]):
            print(f"      {asset_class:15s}: ${amount:,.0f} ({amount/1000:.0f}%)")
    
    # 7. Simulated Signals
    print("\n" + "─" * 50)
    print("7️⃣ SAMPLE TRADING SIGNALS")
    
    # Simulated signals
    sample_signals = [
        CrossAssetSignal(
            symbol='BTC/USDT', asset_class=AssetClass.CRYPTO,
            direction='LONG', strength=75, confidence=0.75,
            entry_price=97500, stop_loss=95000, take_profit=102000,
            risk_reward=1.8, correlation_context={'ETH': 0.85}
        ),
        CrossAssetSignal(
            symbol='NVDA', asset_class=AssetClass.STOCKS,
            direction='LONG', strength=68, confidence=0.68,
            entry_price=140, stop_loss=135, take_profit=150,
            risk_reward=2.0, correlation_context={'QQQ': 0.78}
        ),
        CrossAssetSignal(
            symbol='EUR/USD', asset_class=AssetClass.FOREX,
            direction='SHORT', strength=55, confidence=0.55,
            entry_price=1.0850, stop_loss=1.0950, take_profit=1.0700,
            risk_reward=1.5, correlation_context={'GBP/USD': 0.65}
        ),
    ]
    
    for signal in sample_signals:
        print(f"\n   📊 {signal.symbol} ({signal.asset_class.value})")
        print(f"      Direction: {signal.direction}")
        print(f"      Strength: {signal.strength}/100")
        print(f"      Entry: {signal.entry_price:.4f}")
        print(f"      Stop Loss: {signal.stop_loss:.4f}")
        print(f"      Take Profit: {signal.take_profit:.4f}")
        print(f"      Risk/Reward: {signal.risk_reward:.1f}")
    
    print("\n" + "=" * 70)
    print("✅ Multi-Asset Platform Demo Complete!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    demo()
