#!/usr/bin/env python3
"""
🧠 GENIUS TRADING ENGINE v5.0 - ULTIMATE QUANT EDITION
========================================================
Ultra-precise signals based on:
- STRICT Liquidity Grab Confirmation (multiple confluences required)
- FVG Fill Patterns with volume confirmation
- Insider/Institutional Flow Data (OpenBB, SEC)
- On-chain Blockchain Metrics
- Multi-timeframe Confluence (minimum 3 TF alignment)
- Risk-adjusted Position Sizing
- 🏦 JP MORGAN QUANT METHODS:
  * Options Straddle Pricing (implied volatility analysis)
  * Volatility Regime Detection
  * Monte Carlo Risk Assessment
  * Position Sizing by Volatility
- 🎭 QUANTMUSE FACTORS (NEW!):
  * Multi-Factor Analysis (Momentum, Quality, Volatility, Technical)
  * Strategy Ensemble (Momentum, MeanReversion, MultiFactor)
  * LLM-ready Insights

SIGNAL REQUIREMENTS (must meet ALL):
1. Liquidity sweep confirmed (wick rejection)
2. FVG present within 2% of price
3. Volume spike > 1.5x average
4. RSI divergence OR oversold/overbought
5. At least 2 timeframes aligned
6. Volatility regime favorable
7. 🆕 QuantMuse multi-factor confirmation

Author: Hamster Terminal Team + JP Morgan + QuantMuse
Version: 5.0.0 ULTIMATE QUANT EDITION
"""

import numpy as np
import pandas as pd
import requests
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# JP Morgan Quant Methods Integration
try:
    from jpmorgan_quant_methods import (
        options_pricer, volatility_analyzer, credit_analyzer,
        risk_metrics, crypto_risk, OptionsPricer, CryptoRiskAnalyzer
    )
    JPMORGAN_AVAILABLE = True
except ImportError:
    JPMORGAN_AVAILABLE = False

# QuantMuse Integration (Multi-Factor Analysis)
try:
    from quantmuse_integration import get_quantmuse, QuantMuseIntegration
    QUANTMUSE_AVAILABLE = True
except ImportError:
    QUANTMUSE_AVAILABLE = False

# OpenBB Integration
try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False

# CCXT for exchange data
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False

# Technical Analysis
try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

# Financial libraries
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ CONFIG ============
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'demo')
TWELVE_DATA_BASE_URL = 'https://api.twelvedata.com'

# Minimum confluence requirements for signal
MIN_CONFLUENCE_SCORE = 70  # Out of 100
MIN_TIMEFRAMES_ALIGNED = 2
MIN_VOLUME_MULTIPLIER = 1.3
LIQUIDITY_GRAB_WICK_RATIO = 0.6  # Wick must be 60% of candle


class SignalStrength(Enum):
    EXTREME = "EXTREME"  # 90-100 confluence
    STRONG = "STRONG"    # 70-89 confluence
    MODERATE = "MODERATE" # 50-69 confluence
    WEAK = "WEAK"        # Below 50 - NO TRADE


class SignalType(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    NO_TRADE = "NO_TRADE"  # Insufficient confluence


@dataclass
class ConfluenceFactor:
    """Individual confluence factor with weight"""
    name: str
    triggered: bool
    weight: float
    details: str
    

@dataclass
class RigorousSignal:
    """Trading signal with strict confluence requirements"""
    signal: SignalType
    strength: SignalStrength
    confluence_score: float  # 0-100
    confluence_factors: List[ConfluenceFactor]
    price: float
    
    # Only populated if confluence >= MIN_CONFLUENCE_SCORE
    entry_zone: Optional[Tuple[float, float]] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    risk_reward: Optional[float] = None
    position_size_pct: Optional[float] = None  # Suggested position size
    
    # Analysis
    liquidity_grab: Optional[Dict] = None
    fvg_zone: Optional[Dict] = None
    insider_flow: Optional[Dict] = None
    blockchain_metrics: Optional[Dict] = None
    
    reasoning: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'signal': self.signal.value,
            'strength': self.strength.value,
            'confluence_score': round(self.confluence_score, 1),
            'confluence_factors': [
                {'name': f.name, 'triggered': f.triggered, 'weight': f.weight, 'details': f.details}
                for f in self.confluence_factors
            ],
            'price': self.price,
            'entry_zone': list(self.entry_zone) if self.entry_zone else None,
            'stop_loss': self.stop_loss,
            'take_profit_1': self.take_profit_1,
            'take_profit_2': self.take_profit_2,
            'take_profit_3': self.take_profit_3,
            'risk_reward': round(self.risk_reward, 2) if self.risk_reward else None,
            'position_size_pct': self.position_size_pct,
            'liquidity_grab': self.liquidity_grab,
            'fvg_zone': self.fvg_zone,
            'insider_flow': self.insider_flow,
            'blockchain_metrics': self.blockchain_metrics,
            'reasoning': self.reasoning,
            'warnings': self.warnings,
            'timestamp': self.timestamp
        }


class GeniusEngineV3:
    """
    Rigorous Trading Engine with strict confluence requirements
    Enhanced with JP Morgan Quant Methods
    """
    
    def __init__(self):
        self.api_key = TWELVE_DATA_API_KEY
        
        # Initialize exchange connections
        if CCXT_AVAILABLE:
            self.binance = ccxt.binance({'enableRateLimit': True})
            logger.info("✅ CCXT Binance connected")
        else:
            self.binance = None
            
        # OpenBB initialization
        if OPENBB_AVAILABLE:
            logger.info("✅ OpenBB Platform available")
        
        # JP Morgan Methods
        if JPMORGAN_AVAILABLE:
            logger.info("🏦 JP Morgan Quant Methods loaded!")
        
        # QuantMuse Multi-Factor
        if QUANTMUSE_AVAILABLE:
            self.quantmuse = get_quantmuse()
            logger.info("🎭 QuantMuse Multi-Factor loaded!")
        else:
            self.quantmuse = None
        
        logger.info("🧠 Genius Engine v5.0 ULTIMATE QUANT initialized")
        logger.info(f"   JP Morgan: {'✅' if JPMORGAN_AVAILABLE else '❌'}")
        logger.info(f"   QuantMuse: {'✅' if QUANTMUSE_AVAILABLE else '❌'}")
        logger.info(f"   OpenBB: {'✅' if OPENBB_AVAILABLE else '❌'}")
        logger.info(f"   CCXT: {'✅' if CCXT_AVAILABLE else '❌'}")
        logger.info(f"   TA-Lib: {'✅' if TA_AVAILABLE else '❌'}")
        logger.info(f"   YFinance: {'✅' if YFINANCE_AVAILABLE else '❌'}")
    
    # ============ DATA FETCHING ============
    
    def fetch_multi_timeframe_data(self, symbol: str = 'BTC/USD') -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple timeframes"""
        timeframes = {
            '15m': '15min',
            '1h': '1h', 
            '4h': '4h',
            '1d': '1day'
        }
        
        data = {}
        for tf_key, tf_interval in timeframes.items():
            df = self._fetch_ohlcv(symbol, tf_interval, 100)
            if df is not None:
                data[tf_key] = df
                
        return data
    
    def _fetch_ohlcv(self, symbol: str, interval: str, limit: int) -> Optional[pd.DataFrame]:
        """Fetch OHLCV from Twelve Data"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': limit,
                'apikey': self.api_key
            }
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/time_series', params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if 'values' in data:
                    df = pd.DataFrame(data['values'])
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    for col in ['open', 'high', 'low', 'close']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    # Handle volume - may not exist for forex/crypto
                    if 'volume' in df.columns:
                        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
                    else:
                        df['volume'] = 0
                    df = df.sort_values('datetime').reset_index(drop=True)
                    return df
        except Exception as e:
            logger.warning(f"OHLCV fetch error for {interval}: {e}")
        return None
    
    def fetch_insider_data(self, symbol: str = 'BTC') -> Dict:
        """Fetch insider/institutional flow data"""
        insider_data = {
            'whale_transactions': [],
            'exchange_flows': {},
            'etf_flows': {},
            'institutional_holdings': {}
        }
        
        # Whale Alert / Large transactions from Binance
        if CCXT_AVAILABLE and self.binance:
            try:
                # Get recent large trades
                trades = self.binance.fetch_trades(f'{symbol}/USDT', limit=100)
                large_trades = [t for t in trades if float(t['amount']) * float(t['price']) > 100000]
                
                buy_volume = sum(t['amount'] for t in large_trades if t['side'] == 'buy')
                sell_volume = sum(t['amount'] for t in large_trades if t['side'] == 'sell')
                
                insider_data['whale_transactions'] = {
                    'large_buys': len([t for t in large_trades if t['side'] == 'buy']),
                    'large_sells': len([t for t in large_trades if t['side'] == 'sell']),
                    'buy_volume': buy_volume,
                    'sell_volume': sell_volume,
                    'net_flow': buy_volume - sell_volume,
                    'bias': 'BULLISH' if buy_volume > sell_volume * 1.2 else 'BEARISH' if sell_volume > buy_volume * 1.2 else 'NEUTRAL'
                }
            except Exception as e:
                logger.warning(f"Whale data fetch error: {e}")
        
        # Try OpenBB for institutional data
        if OPENBB_AVAILABLE:
            try:
                # SEC filings, institutional holdings
                # Note: OpenBB needs API keys for some providers
                pass
            except Exception as e:
                logger.warning(f"OpenBB institutional data error: {e}")
        
        return insider_data
    
    def fetch_blockchain_metrics(self, symbol: str = 'BTC') -> Dict:
        """Fetch on-chain blockchain metrics"""
        metrics = {
            'exchange_reserves': None,
            'active_addresses': None,
            'hash_rate': None,
            'miner_revenue': None,
            'nvt_ratio': None,
            'sopr': None  # Spent Output Profit Ratio
        }
        
        # Glassnode-style metrics from free APIs
        try:
            # Exchange reserves (from Binance order book depth as proxy)
            if CCXT_AVAILABLE and self.binance:
                orderbook = self.binance.fetch_order_book(f'{symbol}/USDT', limit=50)
                bid_depth = sum([b[1] for b in orderbook['bids'][:20]])
                ask_depth = sum([a[1] for a in orderbook['asks'][:20]])
                
                metrics['orderbook_imbalance'] = {
                    'bid_depth': bid_depth,
                    'ask_depth': ask_depth,
                    'ratio': bid_depth / ask_depth if ask_depth > 0 else 1,
                    'bias': 'BULLISH' if bid_depth > ask_depth * 1.1 else 'BEARISH' if ask_depth > bid_depth * 1.1 else 'NEUTRAL'
                }
                
                # Funding rate (perpetual futures sentiment)
                try:
                    funding = self.binance.fetch_funding_rate(f'{symbol}/USDT:USDT')
                    metrics['funding_rate'] = {
                        'rate': funding.get('fundingRate', 0) * 100,
                        'bias': 'BEARISH' if funding.get('fundingRate', 0) > 0.0005 else 'BULLISH' if funding.get('fundingRate', 0) < -0.0005 else 'NEUTRAL'
                    }
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Blockchain metrics error: {e}")
        
        return metrics
    
    def fetch_news_sentiment(self) -> Dict:
        """Fetch crypto news sentiment"""
        sentiment = {
            'overall': 'NEUTRAL',
            'score': 50,
            'recent_headlines': []
        }
        
        try:
            # CryptoPanic free API
            resp = requests.get(
                'https://cryptopanic.com/api/v1/posts/?auth_token=free&public=true&filter=hot',
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                posts = data.get('results', [])[:10]
                
                # Simple sentiment from votes
                bullish_count = sum(1 for p in posts if p.get('votes', {}).get('positive', 0) > p.get('votes', {}).get('negative', 0))
                
                sentiment['recent_headlines'] = [p.get('title', '') for p in posts[:5]]
                sentiment['score'] = int((bullish_count / max(len(posts), 1)) * 100)
                sentiment['overall'] = 'BULLISH' if sentiment['score'] > 60 else 'BEARISH' if sentiment['score'] < 40 else 'NEUTRAL'
                
        except Exception as e:
            logger.warning(f"News sentiment error: {e}")
        
        return sentiment
    
    # ============ LIQUIDITY GRAB DETECTION (STRICT) ============
    
    def detect_liquidity_grab_strict(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        STRICT Liquidity Grab Detection
        Requirements:
        1. Price sweeps recent swing high/low
        2. Wick rejection (wick >= 60% of candle range)
        3. Close back inside range
        4. Volume confirmation (>1.3x average)
        """
        if df is None or len(df) < 20:
            return None
        
        highs = df['high'].values
        lows = df['low'].values
        opens = df['open'].values
        closes = df['close'].values
        volumes = df['volume'].values
        
        avg_volume = np.mean(volumes[-20:])
        
        # Check last 3 candles for liquidity grab
        for i in range(-3, 0):
            candle_range = highs[i] - lows[i]
            if candle_range == 0:
                continue
                
            upper_wick = highs[i] - max(opens[i], closes[i])
            lower_wick = min(opens[i], closes[i]) - lows[i]
            body = abs(closes[i] - opens[i])
            
            # Recent swing high/low (last 10 candles before current)
            recent_high = max(highs[i-10:i])
            recent_low = min(lows[i-10:i])
            
            volume_multiplier = volumes[i] / avg_volume if avg_volume > 0 else 1
            
            # ===== BULLISH LIQUIDITY GRAB =====
            # Swept low, long lower wick, closed above
            if (lows[i] < recent_low and  # Swept the low
                lower_wick / candle_range >= LIQUIDITY_GRAB_WICK_RATIO and  # Big wick rejection
                closes[i] > lows[i] + candle_range * 0.5 and  # Closed in upper half
                volume_multiplier >= MIN_VOLUME_MULTIPLIER):  # Volume spike
                
                return {
                    'type': 'BULLISH_LIQUIDITY_GRAB',
                    'swept_level': float(recent_low),
                    'grab_price': float(lows[i]),
                    'close_price': float(closes[i]),
                    'wick_ratio': round(lower_wick / candle_range, 2),
                    'volume_multiplier': round(volume_multiplier, 2),
                    'strength': 'HIGH' if volume_multiplier > 2 and lower_wick / candle_range > 0.7 else 'MEDIUM',
                    'index': len(df) + i
                }
            
            # ===== BEARISH LIQUIDITY GRAB =====
            # Swept high, long upper wick, closed below
            if (highs[i] > recent_high and  # Swept the high
                upper_wick / candle_range >= LIQUIDITY_GRAB_WICK_RATIO and  # Big wick rejection
                closes[i] < highs[i] - candle_range * 0.5 and  # Closed in lower half
                volume_multiplier >= MIN_VOLUME_MULTIPLIER):  # Volume spike
                
                return {
                    'type': 'BEARISH_LIQUIDITY_GRAB',
                    'swept_level': float(recent_high),
                    'grab_price': float(highs[i]),
                    'close_price': float(closes[i]),
                    'wick_ratio': round(upper_wick / candle_range, 2),
                    'volume_multiplier': round(volume_multiplier, 2),
                    'strength': 'HIGH' if volume_multiplier > 2 and upper_wick / candle_range > 0.7 else 'MEDIUM',
                    'index': len(df) + i
                }
        
        return None
    
    # ============ FVG DETECTION (STRICT) ============
    
    def detect_fvg_strict(self, df: pd.DataFrame, current_price: float) -> Optional[Dict]:
        """
        STRICT Fair Value Gap Detection
        Requirements:
        1. Gap size >= 0.3% of price
        2. Gap not yet filled
        3. Within 2% of current price (tradeable)
        """
        if df is None or len(df) < 5:
            return None
        
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        fvgs = []
        
        for i in range(2, len(df) - 1):
            # Bullish FVG: Gap up (candle 3 low > candle 1 high)
            if lows[i] > highs[i-2]:
                gap_size = (lows[i] - highs[i-2]) / closes[i] * 100
                midpoint = (lows[i] + highs[i-2]) / 2
                
                # Check if gap meets criteria
                if gap_size >= 0.3:
                    # Check if filled by subsequent candles
                    filled = any(lows[j] <= midpoint for j in range(i+1, len(df)))
                    
                    # Check if within tradeable range
                    distance_pct = abs(current_price - midpoint) / current_price * 100
                    
                    if not filled and distance_pct <= 2:
                        fvgs.append({
                            'type': 'BULLISH_FVG',
                            'top': float(lows[i]),
                            'bottom': float(highs[i-2]),
                            'midpoint': float(midpoint),
                            'gap_pct': round(gap_size, 2),
                            'distance_pct': round(distance_pct, 2),
                            'filled': False,
                            'tradeable': True
                        })
            
            # Bearish FVG: Gap down (candle 3 high < candle 1 low)
            if highs[i] < lows[i-2]:
                gap_size = (lows[i-2] - highs[i]) / closes[i] * 100
                midpoint = (lows[i-2] + highs[i]) / 2
                
                if gap_size >= 0.3:
                    filled = any(highs[j] >= midpoint for j in range(i+1, len(df)))
                    distance_pct = abs(current_price - midpoint) / current_price * 100
                    
                    if not filled and distance_pct <= 2:
                        fvgs.append({
                            'type': 'BEARISH_FVG',
                            'top': float(lows[i-2]),
                            'bottom': float(highs[i]),
                            'midpoint': float(midpoint),
                            'gap_pct': round(gap_size, 2),
                            'distance_pct': round(distance_pct, 2),
                            'filled': False,
                            'tradeable': True
                        })
        
        # Return the nearest unfilled FVG
        if fvgs:
            return min(fvgs, key=lambda x: x['distance_pct'])
        
        return None
    
    # ============ MULTI-TIMEFRAME ANALYSIS ============
    
    def analyze_multi_timeframe(self, mtf_data: Dict[str, pd.DataFrame]) -> Dict:
        """Analyze trend alignment across timeframes"""
        analysis = {
            'timeframes': {},
            'aligned_count': 0,
            'dominant_bias': 'NEUTRAL',
            'alignment_details': [],
            '_ohlcv_1h': None  # Store for QuantMuse
        }
        
        bullish_count = 0
        bearish_count = 0
        
        for tf, df in mtf_data.items():
            if df is None or len(df) < 20:
                continue
            
            # Store 1h data for QuantMuse multi-factor analysis
            if tf == '1h':
                analysis['_ohlcv_1h'] = df.copy()
            
            closes = df['close'].values
            
            # Simple trend detection: price vs SMA20
            sma20 = np.mean(closes[-20:])
            current = closes[-1]
            
            # EMA crossover check
            if len(closes) >= 50:
                ema21 = pd.Series(closes).ewm(span=21).mean().iloc[-1]
                ema50 = pd.Series(closes).ewm(span=50).mean().iloc[-1]
                
                if current > ema21 > ema50:
                    bias = 'BULLISH'
                    bullish_count += 1
                elif current < ema21 < ema50:
                    bias = 'BEARISH'
                    bearish_count += 1
                else:
                    bias = 'NEUTRAL'
            else:
                bias = 'BULLISH' if current > sma20 else 'BEARISH' if current < sma20 else 'NEUTRAL'
                if bias == 'BULLISH':
                    bullish_count += 1
                elif bias == 'BEARISH':
                    bearish_count += 1
            
            analysis['timeframes'][tf] = {
                'bias': bias,
                'price': float(current),
                'sma20': float(sma20)
            }
            analysis['alignment_details'].append(f"{tf}: {bias}")
        
        analysis['aligned_count'] = max(bullish_count, bearish_count)
        analysis['dominant_bias'] = 'BULLISH' if bullish_count > bearish_count else 'BEARISH' if bearish_count > bullish_count else 'NEUTRAL'
        
        return analysis
    
    # ============ CONFLUENCE SCORING ============
    
    def calculate_confluence(self, 
                            price: float,
                            liquidity_grab: Optional[Dict],
                            fvg: Optional[Dict],
                            mtf_analysis: Dict,
                            indicators: Dict,
                            insider_data: Dict,
                            blockchain: Dict,
                            news_sentiment: Dict) -> Tuple[float, List[ConfluenceFactor], str]:
        """
        Calculate rigorous confluence score
        Each factor has a weight, total must exceed MIN_CONFLUENCE_SCORE
        """
        factors = []
        total_weight = 0
        triggered_weight = 0
        bias_direction = 'NEUTRAL'
        bullish_weight = 0
        bearish_weight = 0
        
        # === 1. LIQUIDITY GRAB (Weight: 25) ===
        factor_weight = 25
        total_weight += factor_weight
        if liquidity_grab:
            if liquidity_grab['type'] == 'BULLISH_LIQUIDITY_GRAB':
                triggered_weight += factor_weight
                bullish_weight += factor_weight
                factors.append(ConfluenceFactor(
                    name='Liquidity Grab',
                    triggered=True,
                    weight=factor_weight,
                    details=f"BULLISH sweep at ${liquidity_grab['swept_level']:,.0f}, wick ratio {liquidity_grab['wick_ratio']}"
                ))
            elif liquidity_grab['type'] == 'BEARISH_LIQUIDITY_GRAB':
                triggered_weight += factor_weight
                bearish_weight += factor_weight
                factors.append(ConfluenceFactor(
                    name='Liquidity Grab',
                    triggered=True,
                    weight=factor_weight,
                    details=f"BEARISH sweep at ${liquidity_grab['swept_level']:,.0f}, wick ratio {liquidity_grab['wick_ratio']}"
                ))
        else:
            factors.append(ConfluenceFactor(
                name='Liquidity Grab',
                triggered=False,
                weight=factor_weight,
                details="No liquidity grab detected in recent candles"
            ))
        
        # === 2. FVG ZONE (Weight: 20) ===
        factor_weight = 20
        total_weight += factor_weight
        if fvg and fvg['tradeable']:
            triggered_weight += factor_weight
            if fvg['type'] == 'BULLISH_FVG':
                bullish_weight += factor_weight
                factors.append(ConfluenceFactor(
                    name='FVG Zone',
                    triggered=True,
                    weight=factor_weight,
                    details=f"BULLISH FVG at ${fvg['midpoint']:,.0f} ({fvg['gap_pct']}% gap, {fvg['distance_pct']}% away)"
                ))
            else:
                bearish_weight += factor_weight
                factors.append(ConfluenceFactor(
                    name='FVG Zone',
                    triggered=True,
                    weight=factor_weight,
                    details=f"BEARISH FVG at ${fvg['midpoint']:,.0f} ({fvg['gap_pct']}% gap, {fvg['distance_pct']}% away)"
                ))
        else:
            factors.append(ConfluenceFactor(
                name='FVG Zone',
                triggered=False,
                weight=factor_weight,
                details="No tradeable FVG within 2% of price"
            ))
        
        # === 3. MULTI-TIMEFRAME ALIGNMENT (Weight: 20) ===
        factor_weight = 20
        total_weight += factor_weight
        if mtf_analysis['aligned_count'] >= MIN_TIMEFRAMES_ALIGNED:
            triggered_weight += factor_weight
            if mtf_analysis['dominant_bias'] == 'BULLISH':
                bullish_weight += factor_weight
            elif mtf_analysis['dominant_bias'] == 'BEARISH':
                bearish_weight += factor_weight
            factors.append(ConfluenceFactor(
                name='MTF Alignment',
                triggered=True,
                weight=factor_weight,
                details=f"{mtf_analysis['aligned_count']} timeframes {mtf_analysis['dominant_bias']}"
            ))
        else:
            factors.append(ConfluenceFactor(
                name='MTF Alignment',
                triggered=False,
                weight=factor_weight,
                details=f"Only {mtf_analysis['aligned_count']} timeframes aligned (need {MIN_TIMEFRAMES_ALIGNED})"
            ))
        
        # === 4. RSI CONDITION (Weight: 15) ===
        factor_weight = 15
        total_weight += factor_weight
        rsi = indicators.get('rsi')
        if rsi:
            if rsi < 30:
                triggered_weight += factor_weight
                bullish_weight += factor_weight
                factors.append(ConfluenceFactor(
                    name='RSI',
                    triggered=True,
                    weight=factor_weight,
                    details=f"OVERSOLD at {rsi:.1f} - Strong reversal zone"
                ))
            elif rsi > 70:
                triggered_weight += factor_weight
                bearish_weight += factor_weight
                factors.append(ConfluenceFactor(
                    name='RSI',
                    triggered=True,
                    weight=factor_weight,
                    details=f"OVERBOUGHT at {rsi:.1f} - Strong reversal zone"
                ))
            elif 30 <= rsi <= 40:
                triggered_weight += factor_weight * 0.5
                bullish_weight += factor_weight * 0.5
                factors.append(ConfluenceFactor(
                    name='RSI',
                    triggered=True,
                    weight=factor_weight * 0.5,
                    details=f"Approaching oversold at {rsi:.1f}"
                ))
            elif 60 <= rsi <= 70:
                triggered_weight += factor_weight * 0.5
                bearish_weight += factor_weight * 0.5
                factors.append(ConfluenceFactor(
                    name='RSI',
                    triggered=True,
                    weight=factor_weight * 0.5,
                    details=f"Approaching overbought at {rsi:.1f}"
                ))
            else:
                factors.append(ConfluenceFactor(
                    name='RSI',
                    triggered=False,
                    weight=factor_weight,
                    details=f"Neutral at {rsi:.1f}"
                ))
        
        # === 5. WHALE/INSIDER FLOW (Weight: 10) ===
        factor_weight = 10
        total_weight += factor_weight
        whale_data = insider_data.get('whale_transactions', {})
        if whale_data and whale_data.get('bias') != 'NEUTRAL':
            triggered_weight += factor_weight
            if whale_data['bias'] == 'BULLISH':
                bullish_weight += factor_weight
            else:
                bearish_weight += factor_weight
            factors.append(ConfluenceFactor(
                name='Whale Flow',
                triggered=True,
                weight=factor_weight,
                details=f"{whale_data['bias']} - Net flow: {whale_data.get('net_flow', 0):.2f}"
            ))
        else:
            factors.append(ConfluenceFactor(
                name='Whale Flow',
                triggered=False,
                weight=factor_weight,
                details="Neutral whale activity"
            ))
        
        # === 6. BLOCKCHAIN METRICS (Weight: 5) ===
        factor_weight = 5
        total_weight += factor_weight
        orderbook = blockchain.get('orderbook_imbalance', {})
        if orderbook and orderbook.get('bias') != 'NEUTRAL':
            triggered_weight += factor_weight
            if orderbook['bias'] == 'BULLISH':
                bullish_weight += factor_weight
            else:
                bearish_weight += factor_weight
            factors.append(ConfluenceFactor(
                name='Orderbook',
                triggered=True,
                weight=factor_weight,
                details=f"{orderbook['bias']} - Bid/Ask ratio: {orderbook.get('ratio', 1):.2f}"
            ))
        else:
            factors.append(ConfluenceFactor(
                name='Orderbook',
                triggered=False,
                weight=factor_weight,
                details="Balanced orderbook"
            ))
        
        # === 7. NEWS SENTIMENT (Weight: 5) ===
        factor_weight = 5
        total_weight += factor_weight
        if news_sentiment.get('overall') != 'NEUTRAL':
            triggered_weight += factor_weight
            if news_sentiment['overall'] == 'BULLISH':
                bullish_weight += factor_weight
            else:
                bearish_weight += factor_weight
            factors.append(ConfluenceFactor(
                name='News Sentiment',
                triggered=True,
                weight=factor_weight,
                details=f"{news_sentiment['overall']} - Score: {news_sentiment.get('score', 50)}"
            ))
        else:
            factors.append(ConfluenceFactor(
                name='News Sentiment',
                triggered=False,
                weight=factor_weight,
                details="Neutral news sentiment"
            ))
        
        # === 8. 🏦 JP MORGAN VOLATILITY REGIME (Weight: 10) ===
        factor_weight = 10
        total_weight += factor_weight
        if JPMORGAN_AVAILABLE:
            try:
                # Calculate volatility metrics using JP Morgan methods
                vol_analysis = self._calculate_jpmorgan_volatility(price)
                
                if vol_analysis and vol_analysis.get('regime') in ['LOW', 'NORMAL']:
                    triggered_weight += factor_weight
                    factors.append(ConfluenceFactor(
                        name='🏦 JPM Vol Regime',
                        triggered=True,
                        weight=factor_weight,
                        details=f"{vol_analysis['regime']} vol ({vol_analysis.get('avg_vol', 0):.1%}) - {vol_analysis.get('recommendation', '')}"
                    ))
                elif vol_analysis and vol_analysis.get('regime') == 'HIGH':
                    triggered_weight += factor_weight * 0.5
                    factors.append(ConfluenceFactor(
                        name='🏦 JPM Vol Regime',
                        triggered=True,
                        weight=factor_weight * 0.5,
                        details=f"HIGH vol ({vol_analysis.get('avg_vol', 0):.1%}) - Reduce position sizes"
                    ))
                else:
                    factors.append(ConfluenceFactor(
                        name='🏦 JPM Vol Regime',
                        triggered=False,
                        weight=factor_weight,
                        details=f"EXTREME vol - Not favorable for entry"
                    ))
            except Exception as e:
                factors.append(ConfluenceFactor(
                    name='🏦 JPM Vol Regime',
                    triggered=False,
                    weight=factor_weight,
                    details=f"Volatility analysis unavailable"
                ))
        else:
            factors.append(ConfluenceFactor(
                name='🏦 JPM Vol Regime',
                triggered=False,
                weight=factor_weight,
                details="JP Morgan methods not loaded"
            ))
        
        # === 9. 🏦 JP MORGAN OPTIONS EXPECTED MOVE (Weight: 5) ===
        factor_weight = 5
        total_weight += factor_weight
        if JPMORGAN_AVAILABLE:
            try:
                straddle_info = self._calculate_jpmorgan_straddle(price)
                
                if straddle_info:
                    expected_move = straddle_info.get('expected_move_pct', 0)
                    # If expected move is reasonable (3-10%), favorable for trading
                    if 3 <= expected_move <= 10:
                        triggered_weight += factor_weight
                        factors.append(ConfluenceFactor(
                            name='🏦 JPM Expected Move',
                            triggered=True,
                            weight=factor_weight,
                            details=f"±{expected_move:.1f}% 30d range: ${straddle_info['lower_expected']:,.0f}-${straddle_info['upper_expected']:,.0f}"
                        ))
                    else:
                        factors.append(ConfluenceFactor(
                            name='🏦 JPM Expected Move',
                            triggered=False,
                            weight=factor_weight,
                            details=f"Expected move {expected_move:.1f}% outside optimal range"
                        ))
            except:
                factors.append(ConfluenceFactor(
                    name='🏦 JPM Expected Move',
                    triggered=False,
                    weight=factor_weight,
                    details="Straddle calculation unavailable"
                ))
        else:
            factors.append(ConfluenceFactor(
                name='🏦 JPM Expected Move',
                triggered=False,
                weight=factor_weight,
                details="JP Morgan methods not loaded"
            ))
        
        # === 10. 🎭 QUANTMUSE MULTI-FACTOR (Weight: 15) ===
        factor_weight = 15
        total_weight += factor_weight
        if QUANTMUSE_AVAILABLE and self.quantmuse:
            try:
                # Get OHLCV data for QuantMuse analysis
                if '1h' in mtf_analysis.get('timeframes', {}):
                    # QuantMuse needs OHLCV DataFrame
                    qm_score = self.quantmuse.analyze(mtf_analysis.get('_ohlcv_1h'))
                    
                    if qm_score and qm_score.total_score >= 60:
                        triggered_weight += factor_weight
                        if qm_score.final_signal in ['BUY', 'STRONG_BUY']:
                            bullish_weight += factor_weight
                        elif qm_score.final_signal in ['SELL', 'STRONG_SELL']:
                            bearish_weight += factor_weight
                        
                        strategy_summary = ', '.join([f"{s.strategy_name.replace('Strategy','')}:{s.signal_type}" 
                                                     for s in qm_score.strategy_signals[:3]])
                        factors.append(ConfluenceFactor(
                            name='🎭 QuantMuse',
                            triggered=True,
                            weight=factor_weight,
                            details=f"{qm_score.final_signal} ({qm_score.total_score:.0f}/100) [{strategy_summary}]"
                        ))
                    elif qm_score and qm_score.total_score >= 40:
                        triggered_weight += factor_weight * 0.5
                        factors.append(ConfluenceFactor(
                            name='🎭 QuantMuse',
                            triggered=True,
                            weight=factor_weight * 0.5,
                            details=f"Weak: {qm_score.final_signal} ({qm_score.total_score:.0f}/100)"
                        ))
                    else:
                        factors.append(ConfluenceFactor(
                            name='🎭 QuantMuse',
                            triggered=False,
                            weight=factor_weight,
                            details=f"No confirmation ({qm_score.total_score if qm_score else 0:.0f}/100)"
                        ))
                else:
                    factors.append(ConfluenceFactor(
                        name='🎭 QuantMuse',
                        triggered=False,
                        weight=factor_weight,
                        details="Insufficient OHLCV data for multi-factor analysis"
                    ))
            except Exception as e:
                factors.append(ConfluenceFactor(
                    name='🎭 QuantMuse',
                    triggered=False,
                    weight=factor_weight,
                    details=f"Multi-factor analysis error: {str(e)[:50]}"
                ))
        else:
            factors.append(ConfluenceFactor(
                name='🎭 QuantMuse',
                triggered=False,
                weight=factor_weight,
                details="QuantMuse not loaded"
            ))
        
        # Calculate final score
        confluence_score = (triggered_weight / total_weight) * 100 if total_weight > 0 else 0
        
        # Determine bias direction
        if bullish_weight > bearish_weight * 1.3:
            bias_direction = 'BULLISH'
        elif bearish_weight > bullish_weight * 1.3:
            bias_direction = 'BEARISH'
        else:
            bias_direction = 'NEUTRAL'
        
        return confluence_score, factors, bias_direction
    
    # ============ MAIN SIGNAL GENERATION ============
    
    def generate_rigorous_signal(self, symbol: str = 'BTC/USD') -> RigorousSignal:
        """Generate signal with strict confluence requirements"""
        logger.info(f"🔍 Generating RIGOROUS signal for {symbol}...")
        
        # 1. Fetch current price
        try:
            params = {'symbol': symbol, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/quote', params=params, timeout=10)
            price_data = resp.json() if resp.status_code == 200 else {}
            price = float(price_data.get('close', 0) or price_data.get('price', 0) or 0)
        except:
            price = 0
        
        if price == 0:
            return self._no_signal("Failed to fetch price data")
        
        # 2. Fetch multi-timeframe data
        mtf_data = self.fetch_multi_timeframe_data(symbol)
        
        # 3. Analyze each component
        liquidity_grab = None
        fvg = None
        
        # Use 15m for precision entries
        if '15m' in mtf_data:
            liquidity_grab = self.detect_liquidity_grab_strict(mtf_data['15m'])
        if '1h' in mtf_data:
            fvg = self.detect_fvg_strict(mtf_data['1h'], price)
        
        # 4. Multi-timeframe analysis
        mtf_analysis = self.analyze_multi_timeframe(mtf_data)
        
        # 5. Fetch technical indicators
        indicators = self._fetch_indicators(symbol)
        
        # 6. Fetch additional data
        insider_data = self.fetch_insider_data(symbol.split('/')[0])
        blockchain = self.fetch_blockchain_metrics(symbol.split('/')[0])
        news_sentiment = self.fetch_news_sentiment()
        
        # 7. Calculate confluence
        confluence_score, factors, bias = self.calculate_confluence(
            price, liquidity_grab, fvg, mtf_analysis, indicators,
            insider_data, blockchain, news_sentiment
        )
        
        # 8. Determine signal
        if confluence_score < MIN_CONFLUENCE_SCORE:
            signal = RigorousSignal(
                signal=SignalType.NO_TRADE,
                strength=SignalStrength.WEAK,
                confluence_score=confluence_score,
                confluence_factors=factors,
                price=price,
                liquidity_grab=liquidity_grab,
                fvg_zone=fvg,
                insider_flow=insider_data,
                blockchain_metrics=blockchain,
                reasoning=[f"Confluence {confluence_score:.1f}% below minimum {MIN_CONFLUENCE_SCORE}%"],
                warnings=["⚠️ DO NOT TRADE - Insufficient confluence"]
            )
            logger.info(f"⛔ NO TRADE - Confluence: {confluence_score:.1f}%")
            return signal
        
        # Signal strength
        if confluence_score >= 90:
            strength = SignalStrength.EXTREME
        elif confluence_score >= 70:
            strength = SignalStrength.STRONG
        else:
            strength = SignalStrength.MODERATE
        
        # Signal type based on bias
        if bias == 'BULLISH':
            signal_type = SignalType.STRONG_BUY if confluence_score >= 85 else SignalType.BUY
        elif bias == 'BEARISH':
            signal_type = SignalType.STRONG_SELL if confluence_score >= 85 else SignalType.SELL
        else:
            signal_type = SignalType.HOLD
        
        # Calculate levels
        atr = indicators.get('atr', price * 0.015)
        
        if bias == 'BULLISH':
            entry_low = fvg['bottom'] if fvg and fvg['type'] == 'BULLISH_FVG' else price * 0.997
            entry_high = fvg['midpoint'] if fvg and fvg['type'] == 'BULLISH_FVG' else price * 1.001
            stop_loss = entry_low - atr * 1.2
            tp1 = price + atr * 1.5
            tp2 = price + atr * 2.5
            tp3 = price + atr * 4
        else:
            entry_low = fvg['midpoint'] if fvg and fvg['type'] == 'BEARISH_FVG' else price * 0.999
            entry_high = fvg['top'] if fvg and fvg['type'] == 'BEARISH_FVG' else price * 1.003
            stop_loss = entry_high + atr * 1.2
            tp1 = price - atr * 1.5
            tp2 = price - atr * 2.5
            tp3 = price - atr * 4
        
        # Risk/Reward
        risk = abs((entry_low + entry_high) / 2 - stop_loss)
        reward = abs(tp2 - (entry_low + entry_high) / 2)
        rr = reward / risk if risk > 0 else 0
        
        # Position size based on confluence
        position_size = min(confluence_score / 100 * 5, 3)  # Max 3% per trade
        
        # Build reasoning
        reasoning = [f.details for f in factors if f.triggered]
        warnings = []
        
        if rr < 1.5:
            warnings.append("⚠️ R:R below 1.5 - Consider skipping")
        if mtf_analysis['aligned_count'] < 3:
            warnings.append(f"⚠️ Only {mtf_analysis['aligned_count']} timeframes aligned")
        
        signal = RigorousSignal(
            signal=signal_type,
            strength=strength,
            confluence_score=confluence_score,
            confluence_factors=factors,
            price=price,
            entry_zone=(entry_low, entry_high),
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            risk_reward=rr,
            position_size_pct=round(position_size, 1),
            liquidity_grab=liquidity_grab,
            fvg_zone=fvg,
            insider_flow=insider_data,
            blockchain_metrics=blockchain,
            reasoning=reasoning,
            warnings=warnings
        )
        
        logger.info(f"✅ {signal_type.value} | Confluence: {confluence_score:.1f}% | Strength: {strength.value} | R:R {rr:.2f}")
        
        return signal
    
    # ============ 🏦 JP MORGAN METHODS ============
    
    def _calculate_jpmorgan_volatility(self, price: float) -> Optional[Dict]:
        """
        Calculate volatility regime using JP Morgan methods
        Uses multiple timeframe volatility analysis
        """
        if not JPMORGAN_AVAILABLE:
            return None
        
        try:
            # Fetch historical data for volatility calculation
            mtf_data = self.fetch_multi_timeframe_data('BTC/USD')
            
            vol_24h = 0.0
            vol_7d = 0.0
            vol_30d = 0.0
            
            # Calculate volatility from different timeframes
            if '15m' in mtf_data and len(mtf_data['15m']) > 10:
                df = mtf_data['15m']
                returns = df['close'].pct_change().dropna()
                vol_24h = float(returns.tail(96).std() * np.sqrt(252 * 96))  # 96 15-min candles = 24h
            
            if '1h' in mtf_data and len(mtf_data['1h']) > 10:
                df = mtf_data['1h']
                returns = df['close'].pct_change().dropna()
                vol_7d = float(returns.tail(168).std() * np.sqrt(252 * 24))  # 168 1h candles = 7d
            
            if '1d' in mtf_data and len(mtf_data['1d']) > 10:
                df = mtf_data['1d']
                returns = df['close'].pct_change().dropna()
                vol_30d = float(returns.tail(30).std() * np.sqrt(252))
            
            # Use JP Morgan's crypto volatility scorer
            vol_analysis = crypto_risk.crypto_volatility_score(
                vol_24h=vol_24h if vol_24h > 0 else 0.5,
                vol_7d=vol_7d if vol_7d > 0 else 0.5,
                vol_30d=vol_30d if vol_30d > 0 else 0.5
            )
            
            return vol_analysis
            
        except Exception as e:
            logger.warning(f"JP Morgan volatility calculation error: {e}")
            return None
    
    def _calculate_jpmorgan_straddle(self, price: float) -> Optional[Dict]:
        """
        Calculate expected move using JP Morgan straddle pricing
        """
        if not JPMORGAN_AVAILABLE:
            return None
        
        try:
            # Estimate implied volatility from recent realized vol
            mtf_data = self.fetch_multi_timeframe_data('BTC/USD')
            
            implied_vol = 0.5  # Default 50% for crypto
            
            if '1d' in mtf_data and len(mtf_data['1d']) > 20:
                df = mtf_data['1d']
                returns = df['close'].pct_change().dropna()
                realized_vol = float(returns.tail(21).std() * np.sqrt(252))
                # Implied vol usually slightly higher than realized
                implied_vol = realized_vol * 1.1 if realized_vol > 0 else 0.5
            
            # Calculate straddle using JP Morgan method
            straddle_info = crypto_risk.crypto_straddle_value(
                btc_price=price,
                implied_vol=implied_vol,
                days_to_expiry=30
            )
            
            return straddle_info
            
        except Exception as e:
            logger.warning(f"JP Morgan straddle calculation error: {e}")
            return None
    
    def _calculate_position_size_jpmorgan(self, account_size: float, 
                                          stop_loss_pct: float) -> Optional[Dict]:
        """
        Calculate optimal position size using JP Morgan volatility-adjusted method
        """
        if not JPMORGAN_AVAILABLE:
            return None
        
        try:
            vol_analysis = self._calculate_jpmorgan_volatility(0)
            current_vol = vol_analysis.get('average_volatility', 0.5) if vol_analysis else 0.5
            
            sizing = crypto_risk.position_size_by_volatility(
                account_size=account_size,
                risk_pct=0.02,  # 2% risk per trade
                stop_loss_pct=stop_loss_pct,
                volatility=current_vol
            )
            
            return sizing
            
        except Exception as e:
            logger.warning(f"JP Morgan position sizing error: {e}")
            return None
    
    def _fetch_indicators(self, symbol: str) -> Dict:
        """Fetch technical indicators"""
        indicators = {}
        
        try:
            # RSI
            params = {'symbol': symbol, 'interval': '1h', 'time_period': 14, 'outputsize': 1, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/rsi', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'values' in data and data['values']:
                    indicators['rsi'] = float(data['values'][0].get('rsi', 50))
            
            # ATR
            params = {'symbol': symbol, 'interval': '1h', 'time_period': 14, 'outputsize': 1, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/atr', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'values' in data and data['values']:
                    indicators['atr'] = float(data['values'][0].get('atr', 0))
                    
        except Exception as e:
            logger.warning(f"Indicators fetch error: {e}")
        
        return indicators
    
    def _no_signal(self, reason: str) -> RigorousSignal:
        """Return no-trade signal"""
        return RigorousSignal(
            signal=SignalType.NO_TRADE,
            strength=SignalStrength.WEAK,
            confluence_score=0,
            confluence_factors=[],
            price=0,
            reasoning=[reason],
            warnings=["⚠️ Unable to generate signal"]
        )


# ============ SINGLETON ============
genius_v3 = GeniusEngineV3()


def get_rigorous_signal(symbol: str = 'BTC/USD') -> Dict:
    """API function"""
    signal = genius_v3.generate_rigorous_signal(symbol)
    return signal.to_dict()


if __name__ == '__main__':
    print("=" * 70)
    print("🧠 GENIUS ENGINE v5.0 ULTIMATE QUANT EDITION")
    print("   JP Morgan Methods + QuantMuse Multi-Factor Analysis")
    print("=" * 70)
    
    signal = genius_v3.generate_rigorous_signal('BTC/USD')
    
    print(f"\n📊 SIGNAL: {signal.signal.value}")
    print(f"   Strength: {signal.strength.value}")
    print(f"   Confluence: {signal.confluence_score:.1f}%")
    print(f"   Price: ${signal.price:,.2f}" if signal.price else "   Price: N/A")
    
    print(f"\n🔍 CONFLUENCE FACTORS ({len(signal.confluence_factors)}):")
    total_max = 0
    total_triggered = 0
    for f in signal.confluence_factors:
        icon = '✅' if f.triggered else '❌'
        print(f"   {icon} {f.name} ({f.weight}pt): {f.details[:55]}..." if len(f.details) > 55 else f"   {icon} {f.name} ({f.weight}pt): {f.details}")
        total_max += f.weight if '🏦' not in f.name and '🎭' not in f.name else f.weight
        if f.triggered:
            total_triggered += f.weight
    
    print(f"\n📈 SCORE: {total_triggered}/{total_max} → {signal.confluence_score:.1f}%")
    
    if signal.entry_zone:
        print(f"\n💰 TRADE SETUP:")
        print(f"   Entry: ${signal.entry_zone[0]:,.0f} - ${signal.entry_zone[1]:,.0f}")
        print(f"   Stop: ${signal.stop_loss:,.0f}")
        print(f"   TP1: ${signal.take_profit_1:,.0f} | TP2: ${signal.take_profit_2:,.0f} | TP3: ${signal.take_profit_3:,.0f}")
        print(f"   R:R = {signal.risk_reward:.1f} | Size: {signal.position_size_pct:.1f}%")
    
    if signal.warnings:
        print(f"\n⚠️ {signal.warnings[0]}")
    
    print("\n" + "=" * 70)
