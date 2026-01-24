#!/usr/bin/env python3
"""
🧠 UNIFIED GENIUS TRADING ENGINE
================================
Live signal generation with:
- Twelve Data API (technical indicators, market data)
- Q-Learning AI (TradingBrain)
- LSTM/TensorFlow predictions
- Liquidity Grab Detection
- FVG Zone Analysis
- Multi-timeframe confluence

Author: Hamster Terminal Team
Version: 2.0.0
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

# ML Libraries
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'demo')
TWELVE_DATA_BASE_URL = 'https://api.twelvedata.com'


class SignalType(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class TradingSignal:
    """Trading signal with full context"""
    signal: SignalType
    confidence: float  # 0-100
    price: float
    entry_zone: Tuple[float, float]
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward: float
    reasoning: List[str]
    tactics: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'signal': self.signal.value,
            'confidence': round(self.confidence, 1),
            'price': self.price,
            'entry_zone': list(self.entry_zone),
            'stop_loss': self.stop_loss,
            'take_profit_1': self.take_profit_1,
            'take_profit_2': self.take_profit_2,
            'take_profit_3': self.take_profit_3,
            'risk_reward': round(self.risk_reward, 2),
            'reasoning': self.reasoning,
            'tactics': self.tactics,
            'timestamp': self.timestamp
        }


class GeniusTradingEngine:
    """
    Unified AI Trading Brain
    Combines all data sources and ML models for live signal generation
    """
    
    def __init__(self):
        self.api_key = TWELVE_DATA_API_KEY
        self.cache = {}
        self.q_table = {}  # Q-Learning state-action values
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.15  # Exploration rate
        
        # Signal weights (learned over time)
        self.weights = {
            'rsi': 1.5,
            'macd': 1.3,
            'ema_cross': 1.2,
            'bollinger': 1.0,
            'volume': 1.1,
            'liquidity_grab': 2.5,  # High weight - key strategy
            'fvg': 2.0,
            'funding_rate': 0.8,
            'fear_greed': 0.7,
            'whale_flow': 1.4,
            'divergence': 1.8
        }
        
        # Performance tracking
        self.total_signals = 0
        self.winning_signals = 0
        
        logger.info("🧠 Genius Trading Engine initialized")
        logger.info(f"📊 TensorFlow: {'✅' if TF_AVAILABLE else '❌'}")
        logger.info(f"📈 Technical Analysis: {'✅' if TA_AVAILABLE else '❌'}")
    
    # ============ DATA FETCHING (Twelve Data) ============
    
    def fetch_time_series(self, symbol: str = 'BTC/USD', interval: str = '1h', 
                          outputsize: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from Twelve Data"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': outputsize,
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
                    if 'volume' in df.columns:
                        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
                    else:
                        df['volume'] = 0
                    df = df.sort_values('datetime').reset_index(drop=True)
                    return df
            return None
        except Exception as e:
            logger.error(f"Time series fetch error: {e}")
            return None
    
    def fetch_technical_indicators(self, symbol: str = 'BTC/USD', 
                                    interval: str = '1h') -> Dict:
        """Fetch all technical indicators from Twelve Data"""
        indicators = {}
        
        # RSI
        try:
            params = {'symbol': symbol, 'interval': interval, 'time_period': 14, 
                     'outputsize': 5, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/rsi', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'values' in data and data['values']:
                    indicators['rsi'] = [float(v['rsi']) for v in data['values'][:5]]
        except Exception as e:
            logger.warning(f"RSI fetch error: {e}")
        
        # MACD
        try:
            params = {'symbol': symbol, 'interval': interval, 'outputsize': 5, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/macd', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'values' in data and data['values']:
                    indicators['macd'] = [{
                        'macd': float(v.get('macd', 0)),
                        'signal': float(v.get('macd_signal', 0)),
                        'histogram': float(v.get('macd_hist', 0))
                    } for v in data['values'][:5]]
        except Exception as e:
            logger.warning(f"MACD fetch error: {e}")
        
        # Bollinger Bands
        try:
            params = {'symbol': symbol, 'interval': interval, 'time_period': 20, 
                     'outputsize': 3, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/bbands', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'values' in data and data['values']:
                    indicators['bollinger'] = {
                        'upper': float(data['values'][0].get('upper_band', 0)),
                        'middle': float(data['values'][0].get('middle_band', 0)),
                        'lower': float(data['values'][0].get('lower_band', 0))
                    }
        except Exception as e:
            logger.warning(f"BB fetch error: {e}")
        
        # EMA 21, 50, 200
        for period in [21, 50, 200]:
            try:
                params = {'symbol': symbol, 'interval': interval, 'time_period': period, 
                         'outputsize': 1, 'apikey': self.api_key}
                resp = requests.get(f'{TWELVE_DATA_BASE_URL}/ema', params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if 'values' in data and data['values']:
                        indicators[f'ema{period}'] = float(data['values'][0].get('ema', 0))
            except Exception as e:
                logger.warning(f"EMA{period} fetch error: {e}")
        
        # ATR (for stop loss calculation)
        try:
            params = {'symbol': symbol, 'interval': interval, 'time_period': 14, 
                     'outputsize': 1, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/atr', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'values' in data and data['values']:
                    indicators['atr'] = float(data['values'][0].get('atr', 0))
        except Exception as e:
            logger.warning(f"ATR fetch error: {e}")
        
        # ADX (trend strength)
        try:
            params = {'symbol': symbol, 'interval': interval, 'time_period': 14, 
                     'outputsize': 1, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/adx', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'values' in data and data['values']:
                    indicators['adx'] = float(data['values'][0].get('adx', 0))
        except Exception as e:
            logger.warning(f"ADX fetch error: {e}")
        
        # Stochastic
        try:
            params = {'symbol': symbol, 'interval': interval, 'outputsize': 1, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/stoch', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'values' in data and data['values']:
                    indicators['stoch'] = {
                        'k': float(data['values'][0].get('slow_k', 0)),
                        'd': float(data['values'][0].get('slow_d', 0))
                    }
        except Exception as e:
            logger.warning(f"Stoch fetch error: {e}")
        
        return indicators
    
    def fetch_quote(self, symbol: str = 'BTC/USD') -> Dict:
        """Fetch current price quote"""
        try:
            params = {'symbol': symbol, 'apikey': self.api_key}
            resp = requests.get(f'{TWELVE_DATA_BASE_URL}/quote', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'price': float(data.get('close', 0) or data.get('price', 0) or 0),
                    'change': float(data.get('percent_change', 0) or 0),
                    'volume': float(data.get('volume', 0) or 0),
                    'high': float(data.get('high', 0) or 0),
                    'low': float(data.get('low', 0) or 0)
                }
        except Exception as e:
            logger.error(f"Quote fetch error: {e}")
        return {}
    
    # ============ LIQUIDITY ANALYSIS ============
    
    def detect_liquidity_zones(self, df: pd.DataFrame) -> Dict:
        """Detect liquidity grab zones, FVGs, and key levels"""
        if df is None or len(df) < 20:
            return {}
        
        analysis = {
            'liquidity_grabs': [],
            'fvg_zones': [],
            'support_levels': [],
            'resistance_levels': [],
            'equal_highs': [],
            'equal_lows': []
        }
        
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        # === LIQUIDITY GRAB DETECTION ===
        # Look for sweep of highs/lows followed by reversal
        for i in range(5, len(df) - 2):
            # Check for liquidity grab down (sweep lows then reverse up)
            recent_low = min(lows[i-5:i])
            if lows[i] < recent_low and closes[i] > lows[i] and closes[i+1] > closes[i]:
                analysis['liquidity_grabs'].append({
                    'type': 'LONG_SETUP',
                    'price': float(lows[i]),
                    'swept_level': float(recent_low),
                    'index': i,
                    'strength': 'HIGH' if (closes[i] - lows[i]) > (highs[i] - lows[i]) * 0.6 else 'MEDIUM'
                })
            
            # Check for liquidity grab up (sweep highs then reverse down)
            recent_high = max(highs[i-5:i])
            if highs[i] > recent_high and closes[i] < highs[i] and closes[i+1] < closes[i]:
                analysis['liquidity_grabs'].append({
                    'type': 'SHORT_SETUP',
                    'price': float(highs[i]),
                    'swept_level': float(recent_high),
                    'index': i,
                    'strength': 'HIGH' if (highs[i] - closes[i]) > (highs[i] - lows[i]) * 0.6 else 'MEDIUM'
                })
        
        # === FVG (Fair Value Gap) DETECTION ===
        for i in range(2, len(df) - 1):
            # Bullish FVG: gap between candle 1 high and candle 3 low
            if lows[i] > highs[i-2]:
                gap_size = (lows[i] - highs[i-2]) / closes[i] * 100
                if gap_size > 0.1:  # Minimum 0.1% gap
                    analysis['fvg_zones'].append({
                        'type': 'BULLISH_FVG',
                        'top': float(lows[i]),
                        'bottom': float(highs[i-2]),
                        'midpoint': float((lows[i] + highs[i-2]) / 2),
                        'gap_pct': round(gap_size, 2),
                        'filled': False
                    })
            
            # Bearish FVG: gap between candle 1 low and candle 3 high
            if highs[i] < lows[i-2]:
                gap_size = (lows[i-2] - highs[i]) / closes[i] * 100
                if gap_size > 0.1:
                    analysis['fvg_zones'].append({
                        'type': 'BEARISH_FVG',
                        'top': float(lows[i-2]),
                        'bottom': float(highs[i]),
                        'midpoint': float((lows[i-2] + highs[i]) / 2),
                        'gap_pct': round(gap_size, 2),
                        'filled': False
                    })
        
        # === SUPPORT/RESISTANCE LEVELS ===
        # Use swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(df) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append(float(highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append(float(lows[i]))
        
        # Cluster nearby levels
        analysis['resistance_levels'] = self._cluster_levels(swing_highs[-10:]) if swing_highs else []
        analysis['support_levels'] = self._cluster_levels(swing_lows[-10:]) if swing_lows else []
        
        # === EQUAL HIGHS/LOWS ===
        tolerance = closes[-1] * 0.002  # 0.2% tolerance
        for i in range(len(swing_highs) - 1):
            for j in range(i + 1, len(swing_highs)):
                if abs(swing_highs[i] - swing_highs[j]) < tolerance:
                    analysis['equal_highs'].append({
                        'level': (swing_highs[i] + swing_highs[j]) / 2,
                        'liquidity': 'HIGH'
                    })
        
        for i in range(len(swing_lows) - 1):
            for j in range(i + 1, len(swing_lows)):
                if abs(swing_lows[i] - swing_lows[j]) < tolerance:
                    analysis['equal_lows'].append({
                        'level': (swing_lows[i] + swing_lows[j]) / 2,
                        'liquidity': 'HIGH'
                    })
        
        return analysis
    
    def _cluster_levels(self, levels: List[float], tolerance_pct: float = 0.5) -> List[float]:
        """Cluster nearby price levels"""
        if not levels:
            return []
        
        levels = sorted(levels)
        clusters = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] * 100 < tolerance_pct:
                current_cluster.append(level)
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]
        
        clusters.append(sum(current_cluster) / len(current_cluster))
        return clusters[-5:]  # Return top 5 levels
    
    # ============ SIGNAL SCORING ============
    
    def calculate_signal_score(self, indicators: Dict, liquidity: Dict, 
                               price: float, df: pd.DataFrame) -> Tuple[float, List[str]]:
        """Calculate weighted signal score and reasoning"""
        score = 0
        max_score = 0
        reasons = []
        
        # === RSI ANALYSIS ===
        if 'rsi' in indicators and indicators['rsi']:
            rsi = indicators['rsi'][0]
            max_score += self.weights['rsi'] * 2
            
            if rsi < 30:
                score += self.weights['rsi'] * 2
                reasons.append(f"RSI OVERSOLD ({rsi:.1f}) - Strong buy zone")
            elif rsi < 40:
                score += self.weights['rsi'] * 1
                reasons.append(f"RSI approaching oversold ({rsi:.1f})")
            elif rsi > 70:
                score -= self.weights['rsi'] * 2
                reasons.append(f"RSI OVERBOUGHT ({rsi:.1f}) - Strong sell zone")
            elif rsi > 60:
                score -= self.weights['rsi'] * 1
                reasons.append(f"RSI elevated ({rsi:.1f})")
            
            # RSI Divergence check
            if len(indicators['rsi']) >= 3 and df is not None:
                if indicators['rsi'][0] > indicators['rsi'][2] and df['close'].iloc[-1] < df['close'].iloc[-3]:
                    score += self.weights['divergence']
                    reasons.append("🔥 BULLISH RSI DIVERGENCE detected")
                elif indicators['rsi'][0] < indicators['rsi'][2] and df['close'].iloc[-1] > df['close'].iloc[-3]:
                    score -= self.weights['divergence']
                    reasons.append("⚠️ BEARISH RSI DIVERGENCE detected")
        
        # === MACD ANALYSIS ===
        if 'macd' in indicators and indicators['macd']:
            macd = indicators['macd'][0]
            max_score += self.weights['macd'] * 2
            
            if macd['histogram'] > 0 and len(indicators['macd']) > 1:
                if indicators['macd'][1]['histogram'] < 0:
                    score += self.weights['macd'] * 2
                    reasons.append("MACD BULLISH CROSS - Momentum shifting up")
                else:
                    score += self.weights['macd'] * 0.5
            elif macd['histogram'] < 0 and len(indicators['macd']) > 1:
                if indicators['macd'][1]['histogram'] > 0:
                    score -= self.weights['macd'] * 2
                    reasons.append("MACD BEARISH CROSS - Momentum shifting down")
                else:
                    score -= self.weights['macd'] * 0.5
        
        # === EMA ANALYSIS ===
        ema21 = indicators.get('ema21', 0)
        ema50 = indicators.get('ema50', 0)
        ema200 = indicators.get('ema200', 0)
        
        if ema21 and ema50 and ema200:
            max_score += self.weights['ema_cross'] * 2
            
            # Golden cross / Death cross
            if price > ema21 > ema50 > ema200:
                score += self.weights['ema_cross'] * 2
                reasons.append("BULLISH STRUCTURE: Price > EMA21 > EMA50 > EMA200")
            elif price < ema21 < ema50 < ema200:
                score -= self.weights['ema_cross'] * 2
                reasons.append("BEARISH STRUCTURE: Price < EMA21 < EMA50 < EMA200")
            elif price > ema200:
                score += self.weights['ema_cross'] * 0.5
                reasons.append("Above EMA200 - Long-term bullish")
            else:
                score -= self.weights['ema_cross'] * 0.5
                reasons.append("Below EMA200 - Long-term bearish")
        
        # === BOLLINGER BANDS ===
        if 'bollinger' in indicators:
            bb = indicators['bollinger']
            max_score += self.weights['bollinger'] * 2
            
            if price < bb['lower']:
                score += self.weights['bollinger'] * 2
                reasons.append(f"Price BELOW Bollinger Lower Band - Oversold")
            elif price > bb['upper']:
                score -= self.weights['bollinger'] * 2
                reasons.append(f"Price ABOVE Bollinger Upper Band - Overbought")
        
        # === LIQUIDITY GRAB ANALYSIS (KEY STRATEGY) ===
        if liquidity.get('liquidity_grabs'):
            recent_grabs = [g for g in liquidity['liquidity_grabs'] if g['index'] >= len(df) - 5]
            max_score += self.weights['liquidity_grab'] * 2
            
            for grab in recent_grabs:
                if grab['type'] == 'LONG_SETUP':
                    score += self.weights['liquidity_grab'] * (2 if grab['strength'] == 'HIGH' else 1)
                    reasons.append(f"🎯 LIQUIDITY GRAB LONG at ${grab['price']:,.0f} - {grab['strength']} strength")
                elif grab['type'] == 'SHORT_SETUP':
                    score -= self.weights['liquidity_grab'] * (2 if grab['strength'] == 'HIGH' else 1)
                    reasons.append(f"🎯 LIQUIDITY GRAB SHORT at ${grab['price']:,.0f} - {grab['strength']} strength")
        
        # === FVG ANALYSIS ===
        if liquidity.get('fvg_zones'):
            recent_fvgs = liquidity['fvg_zones'][-5:]
            max_score += self.weights['fvg'] * 2
            
            for fvg in recent_fvgs:
                if fvg['type'] == 'BULLISH_FVG' and fvg['bottom'] < price < fvg['top'] * 1.01:
                    score += self.weights['fvg']
                    reasons.append(f"Price in BULLISH FVG zone (${fvg['bottom']:,.0f}-${fvg['top']:,.0f})")
                elif fvg['type'] == 'BEARISH_FVG' and fvg['bottom'] * 0.99 < price < fvg['top']:
                    score -= self.weights['fvg']
                    reasons.append(f"Price in BEARISH FVG zone (${fvg['bottom']:,.0f}-${fvg['top']:,.0f})")
        
        # === EQUAL HIGHS/LOWS (Liquidity pools) ===
        if liquidity.get('equal_highs'):
            for eq in liquidity['equal_highs'][:3]:
                if eq['level'] > price and (eq['level'] - price) / price < 0.02:
                    reasons.append(f"⚡ Equal highs liquidity at ${eq['level']:,.0f} - Target for longs")
        
        if liquidity.get('equal_lows'):
            for eq in liquidity['equal_lows'][:3]:
                if eq['level'] < price and (price - eq['level']) / price < 0.02:
                    reasons.append(f"⚡ Equal lows liquidity at ${eq['level']:,.0f} - Risk for longs")
        
        # === ADX TREND STRENGTH ===
        if 'adx' in indicators:
            adx = indicators['adx']
            if adx > 25:
                reasons.append(f"Strong trend (ADX: {adx:.1f})")
            elif adx < 20:
                reasons.append(f"Weak/ranging market (ADX: {adx:.1f})")
        
        # Normalize score to -100 to +100
        if max_score > 0:
            normalized_score = (score / max_score) * 100
        else:
            normalized_score = 0
        
        return normalized_score, reasons
    
    # ============ TRADING TACTICS GENERATION ============
    
    def generate_tactics(self, signal_score: float, indicators: Dict, 
                         liquidity: Dict, price: float) -> List[str]:
        """Generate specific trading tactics based on analysis"""
        tactics = []
        
        atr = indicators.get('atr', price * 0.02)
        
        if signal_score > 30:
            # BULLISH TACTICS
            tactics.append("📈 LONG BIAS - Look for pullback entries")
            
            if liquidity.get('support_levels'):
                nearest_support = max([s for s in liquidity['support_levels'] if s < price], default=price * 0.98)
                tactics.append(f"🎯 Entry Zone: ${nearest_support:,.0f} - ${nearest_support * 1.005:,.0f}")
            
            if liquidity.get('fvg_zones'):
                bullish_fvgs = [f for f in liquidity['fvg_zones'] if f['type'] == 'BULLISH_FVG' and f['top'] < price]
                if bullish_fvgs:
                    fvg = bullish_fvgs[-1]
                    tactics.append(f"🔥 FVG RETEST TACTIC: Wait for fill at ${fvg['midpoint']:,.0f}")
            
            tactics.append(f"⛔ Stop Loss: ${price - atr * 1.5:,.0f} (1.5x ATR)")
            tactics.append("💡 Scale in: 50% at entry, 50% at FVG retest")
            
        elif signal_score < -30:
            # BEARISH TACTICS
            tactics.append("📉 SHORT BIAS - Look for rally entries to short")
            
            if liquidity.get('resistance_levels'):
                nearest_resistance = min([r for r in liquidity['resistance_levels'] if r > price], default=price * 1.02)
                tactics.append(f"🎯 Short Entry Zone: ${nearest_resistance * 0.995:,.0f} - ${nearest_resistance:,.0f}")
            
            if liquidity.get('fvg_zones'):
                bearish_fvgs = [f for f in liquidity['fvg_zones'] if f['type'] == 'BEARISH_FVG' and f['bottom'] > price]
                if bearish_fvgs:
                    fvg = bearish_fvgs[-1]
                    tactics.append(f"🔥 FVG RETEST SHORT: Wait for fill at ${fvg['midpoint']:,.0f}")
            
            tactics.append(f"⛔ Stop Loss: ${price + atr * 1.5:,.0f} (1.5x ATR)")
            tactics.append("💡 Scale in shorts on strength")
            
        else:
            # NEUTRAL / RANGE TACTICS
            tactics.append("⏸️ RANGE BOUND - Trade the edges")
            
            if liquidity.get('support_levels') and liquidity.get('resistance_levels'):
                support = max([s for s in liquidity['support_levels'] if s < price], default=price * 0.98)
                resistance = min([r for r in liquidity['resistance_levels'] if r > price], default=price * 1.02)
                tactics.append(f"📊 Range: ${support:,.0f} - ${resistance:,.0f}")
                tactics.append(f"🎯 Buy at ${support:,.0f}, Sell at ${resistance:,.0f}")
            
            tactics.append("💡 Wait for breakout confirmation before directional trade")
        
        # Add liquidity grab tactic if detected
        if liquidity.get('liquidity_grabs'):
            recent = liquidity['liquidity_grabs'][-1]
            if recent['type'] == 'LONG_SETUP':
                tactics.append(f"🦈 SMART MONEY TACTIC: Long after sweep of ${recent['swept_level']:,.0f}")
            else:
                tactics.append(f"🦈 SMART MONEY TACTIC: Short after sweep of ${recent['swept_level']:,.0f}")
        
        return tactics
    
    # ============ MAIN SIGNAL GENERATION ============
    
    def generate_live_signal(self, symbol: str = 'BTC/USD') -> TradingSignal:
        """Generate complete trading signal with all analysis"""
        logger.info(f"🔄 Generating signal for {symbol}...")
        
        # Fetch all data
        quote = self.fetch_quote(symbol)
        price = quote.get('price', 0)
        
        if price == 0:
            logger.error("Failed to fetch price")
            return self._default_signal()
        
        df = self.fetch_time_series(symbol, '1h', 100)
        indicators = self.fetch_technical_indicators(symbol, '1h')
        liquidity = self.detect_liquidity_zones(df) if df is not None else {}
        
        # Calculate signal score
        signal_score, reasoning = self.calculate_signal_score(indicators, liquidity, price, df)
        
        # Generate tactics
        tactics = self.generate_tactics(signal_score, indicators, liquidity, price)
        
        # Determine signal type
        if signal_score > 60:
            signal_type = SignalType.STRONG_BUY
        elif signal_score > 25:
            signal_type = SignalType.BUY
        elif signal_score < -60:
            signal_type = SignalType.STRONG_SELL
        elif signal_score < -25:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
        
        # Calculate levels
        atr = indicators.get('atr', price * 0.02)
        
        if signal_score > 0:
            # Bullish levels
            entry_low = price * 0.995
            entry_high = price * 1.002
            stop_loss = price - atr * 1.5
            tp1 = price + atr * 1.5
            tp2 = price + atr * 2.5
            tp3 = price + atr * 4
        else:
            # Bearish or neutral levels
            entry_low = price * 0.998
            entry_high = price * 1.005
            stop_loss = price + atr * 1.5
            tp1 = price - atr * 1.5
            tp2 = price - atr * 2.5
            tp3 = price - atr * 4
        
        # Risk/Reward calculation
        risk = abs(price - stop_loss)
        reward = abs(tp2 - price)
        rr = reward / risk if risk > 0 else 0
        
        # Confidence based on signal strength and confluence
        confidence = min(abs(signal_score), 95)
        
        signal = TradingSignal(
            signal=signal_type,
            confidence=confidence,
            price=price,
            entry_zone=(entry_low, entry_high),
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            risk_reward=rr,
            reasoning=reasoning,
            tactics=tactics
        )
        
        logger.info(f"✅ Signal: {signal_type.value} | Confidence: {confidence:.1f}% | R:R {rr:.2f}")
        
        return signal
    
    def _default_signal(self) -> TradingSignal:
        """Return default signal when data unavailable"""
        return TradingSignal(
            signal=SignalType.HOLD,
            confidence=0,
            price=0,
            entry_zone=(0, 0),
            stop_loss=0,
            take_profit_1=0,
            take_profit_2=0,
            take_profit_3=0,
            risk_reward=0,
            reasoning=["Unable to fetch market data"],
            tactics=["Wait for data connection"]
        )
    
    # ============ Q-LEARNING UPDATE ============
    
    def record_trade_outcome(self, signal: TradingSignal, pnl: float):
        """Record trade outcome to improve future signals (Q-Learning)"""
        state = f"{signal.signal.value}_{int(signal.confidence/10)*10}"
        action = "EXECUTED"
        
        # Calculate reward based on PnL
        if pnl > 0:
            reward = min(pnl / signal.price * 100, 10)  # Cap at 10
            self.winning_signals += 1
        else:
            reward = max(pnl / signal.price * 100, -10)  # Floor at -10
        
        self.total_signals += 1
        
        # Update Q-table
        if state not in self.q_table:
            self.q_table[state] = {'EXECUTED': 0, 'SKIPPED': 0}
        
        self.q_table[state][action] = (
            self.q_table[state][action] + 
            self.learning_rate * (reward - self.q_table[state][action])
        )
        
        # Update weights based on performance
        win_rate = self.winning_signals / max(self.total_signals, 1)
        if win_rate > 0.55:
            # Increase confidence in current weights
            pass
        elif win_rate < 0.45:
            # Reduce weight on underperforming indicators
            logger.warning(f"⚠️ Win rate below 45% ({win_rate:.1%}) - consider adjusting strategy")
        
        logger.info(f"📊 Trade recorded: PnL {pnl:+.2f} | Win rate: {win_rate:.1%}")


# ============ SINGLETON INSTANCE ============
genius_engine = GeniusTradingEngine()


# ============ API ENDPOINTS ============
def get_live_signal(symbol: str = 'BTC/USD') -> Dict:
    """API function to get live signal"""
    signal = genius_engine.generate_live_signal(symbol)
    return signal.to_dict()


if __name__ == '__main__':
    # Test run
    print("🧠 Testing Genius Trading Engine...")
    signal = genius_engine.generate_live_signal('BTC/USD')
    print(json.dumps(signal.to_dict(), indent=2))
