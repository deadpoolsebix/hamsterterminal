#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Advanced Technical Indicators Analyzer
RSI, Momentum, MACD, Bollinger Bands, FVG, Sentiment, ATR, Volume Profile
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


class AdvancedIndicators:
    """
    Comprehensive technical analysis indicator suite
    """
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> np.ndarray:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return np.full(len(prices), np.nan)
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.values
    
    @staticmethod
    def calculate_momentum(prices: pd.Series, period: int = 10) -> np.ndarray:
        """Momentum Indicator"""
        if len(prices) < period:
            return np.full(len(prices), np.nan)
        momentum = prices - prices.shift(period)
        return momentum.values
    
    @staticmethod
    def calculate_macd(prices: pd.Series) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD: Moving Average Convergence Divergence"""
        if len(prices) < 26:
            return np.full(len(prices), np.nan), np.full(len(prices), np.nan), np.full(len(prices), np.nan)
        
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line.values, signal_line.values, histogram.values
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands"""
        if len(prices) < period:
            return np.full(len(prices), np.nan), np.full(len(prices), np.nan), np.full(len(prices), np.nan)
        
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper.values, middle.values, lower.values
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> np.ndarray:
        """Average True Range"""
        if len(high) < period:
            return np.full(len(high), np.nan)
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.values
    
    @staticmethod
    def calculate_volume_momentum(volume: pd.Series, period: int = 10) -> np.ndarray:
        """Volume Momentum Indicator"""
        if len(volume) < period:
            return np.full(len(volume), np.nan)
        
        vol_mom = volume - volume.shift(period)
        return vol_mom.values
    
    @staticmethod
    def detect_fvg(high: pd.Series, low: pd.Series) -> List[Dict]:
        """
        Fair Value Gaps Detection
        Occurs when there's a gap in price that hasn't been filled
        """
        fvgs = []
        
        for i in range(2, len(high)):
            # Bearish FVG: gap down
            if low.iloc[i] > high.iloc[i-2]:
                fvgs.append({
                    'index': i,
                    'type': 'BEARISH',
                    'gap_top': high.iloc[i-2],
                    'gap_bottom': low.iloc[i]
                })
            
            # Bullish FVG: gap up
            if high.iloc[i] < low.iloc[i-2]:
                fvgs.append({
                    'index': i,
                    'type': 'BULLISH',
                    'gap_bottom': low.iloc[i-2],
                    'gap_top': high.iloc[i]
                })
        
        return fvgs
    
    @staticmethod
    def detect_bull_trap(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 5) -> List[Dict]:
        """
        Bull Trap Detection
        Price goes up, breaks resistance, then reverses sharply down
        """
        traps = []
        
        for i in range(period + 1, len(close)):
            # High above recent highs (breakout attempt)
            recent_high = high.iloc[i-period:i].max()
            recent_low = low.iloc[i-period:i].min()
            
            if high.iloc[i] > recent_high:
                # Check if followed by sharp reversal down
                if i + 2 < len(close):
                    if close.iloc[i+1] < close.iloc[i] * 0.98:  # 2% drop
                        traps.append({
                            'index': i,
                            'type': 'BULL_TRAP',
                            'entry_price': high.iloc[i],
                            'rejection_price': close.iloc[i+1]
                        })
        
        return traps
    
    @staticmethod
    def detect_bear_trap(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 5) -> List[Dict]:
        """
        Bear Trap Detection
        Price goes down, breaks support, then reverses sharply up
        """
        traps = []
        
        for i in range(period + 1, len(close)):
            # Low below recent lows (breakdown attempt)
            recent_high = high.iloc[i-period:i].max()
            recent_low = low.iloc[i-period:i].min()
            
            if low.iloc[i] < recent_low:
                # Check if followed by sharp reversal up
                if i + 2 < len(close):
                    if close.iloc[i+1] > close.iloc[i] * 1.02:  # 2% gain
                        traps.append({
                            'index': i,
                            'type': 'BEAR_TRAP',
                            'entry_price': low.iloc[i],
                            'rejection_price': close.iloc[i+1]
                        })
        
        return traps
    
    @staticmethod
    def calculate_market_sentiment(close: pd.Series, volume: pd.Series, period: int = 20) -> Tuple[np.ndarray, np.ndarray]:
        """
        Market Sentiment Analysis
        Returns: sentiment_score (-1 to 1), sentiment_strength (0 to 1)
        """
        if len(close) < period:
            return np.full(len(close), np.nan), np.full(len(close), np.nan)
        
        # Price momentum
        returns = close.pct_change()
        momentum = returns.rolling(window=period).mean() * 100
        
        # Volume analysis
        volume_avg = volume.rolling(window=period).mean()
        volume_ratio = volume / volume_avg
        
        # Sentiment: positive if up on volume, negative if down on volume
        sentiment = np.where(
            returns > 0,
            np.clip(momentum / 5, -1, 1) * np.clip(volume_ratio / 2, 0, 1),
            np.clip(momentum / 5, -1, 1) * np.clip(volume_ratio / 2, 0, 1)
        )
        
        strength = np.abs(sentiment)
        
        return sentiment, strength
    
    @staticmethod
    def analyze_price_action(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        """
        Comprehensive Price Action Analysis
        """
        if len(close) < 3:
            return {}
        
        current = close.iloc[-1]
        prev_close = close.iloc[-2]
        current_high = high.iloc[-1]
        current_low = low.iloc[-1]
        
        # Candlestick analysis
        body = abs(current - prev_close)
        wick_up = current_high - max(current, prev_close)
        wick_down = min(current, prev_close) - current_low
        total_range = current_high - current_low
        
        analysis = {
            'current_price': current,
            'high': current_high,
            'low': current_low,
            'body_size': body / total_range if total_range > 0 else 0,
            'wick_up': wick_up / total_range if total_range > 0 else 0,
            'wick_down': wick_down / total_range if total_range > 0 else 0,
            'is_bullish': current > prev_close,
            'is_bearish': current < prev_close,
        }
        
        return analysis

    @staticmethod
    def estimate_open_interest(df: pd.DataFrame, fast_window: int = 5, momentum_window: int = 8) -> Dict:
        """
        Szybka estymacja open interest (proxy) na bazie wolumenu i kierunku świecy.
        Używa krótkich okien, żeby reagować na świeże ruchy (scalp 1m/5m).
        Zwraca: proxy (skumulowane), zmiana i momentum wygładzone krótkim SMA.
        """
        if len(df) < max(fast_window, momentum_window) + 1:
            empty = np.full(len(df), np.nan)
            return {
                'proxy': empty,
                'change': empty,
                'momentum': empty,
                'rate': empty,
            }

        close = df['close']
        volume = df['volume']
        price_delta = close.diff().fillna(0)

        # Kierunek świecy: +1 gdy cena rośnie, -1 gdy spada, 0 gdy brak ruchu
        direction = np.sign(price_delta)

        # Skala wolumenu do [0,1] dla stabilności
        vol_scaled = volume / (volume.rolling(fast_window).max().replace(0, np.nan))
        vol_scaled = vol_scaled.fillna(0)

        # Proxy: wolumen kierunkowy (rośnie gdy rośnie cena na wolumenie)
        oi_change = direction * vol_scaled
        oi_proxy = oi_change.cumsum()

        # Momentum OI (krótkie okno = szybsza reakcja)
        oi_rate = oi_change.rolling(fast_window).mean()
        oi_momentum = oi_proxy.diff().rolling(momentum_window).mean()

        return {
            'proxy': oi_proxy.values,
            'change': oi_change.values,
            'momentum': oi_momentum.values,
            'rate': oi_rate.values,
        }

    @staticmethod
    def calculate_cvd(df: pd.DataFrame, momentum_window: int = 10) -> Dict:
        """
        Lightweight CVD z kierunkowego wolumenu (close vs open) + szybkie momentum.
        Zwraca: raw, ema, momentum oraz bias: 1 bullish, -1 bearish, 0 neutral.
        """
        if len(df) < momentum_window + 2:
            empty = np.full(len(df), np.nan)
            return {
                'raw': empty,
                'ema': empty,
                'momentum': empty,
                'bias': 0,
            }

        close = df['close']
        open_ = df['open']
        volume = df['volume']

        direction = np.where(close >= open_, 1, -1)
        volume_delta = volume * direction
        cvd_raw = pd.Series(volume_delta).cumsum()
        cvd_ema = cvd_raw.ewm(span=momentum_window, adjust=False).mean()
        cvd_momentum = cvd_ema.diff().rolling(momentum_window // 2).mean()

        bias = 0
        if cvd_momentum.iloc[-1] > 0:
            bias = 1
        elif cvd_momentum.iloc[-1] < 0:
            bias = -1

        return {
            'raw': cvd_raw.values,
            'ema': cvd_ema.values,
            'momentum': cvd_momentum.values,
            'bias': bias,
        }

    @staticmethod
    def detect_liquidity_grab(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, wick_ratio: float = 0.65, body_max_ratio: float = 0.35) -> Dict:
        """
        Wykrywa proste "liquidity grab" (stop hunt): długi knot i szybki powrót do zakresu.
        - Bullish: długi dolny knot, zamknięcie w górnej połowie świecy.
        - Bearish: długi górny knot, zamknięcie w dolnej połowie świecy.
        Zwraca dict z typem ('bullish'/'bearish'/None) i siłą (0-1).
        """
        if len(close) < 3:
            return {'type': None, 'strength': 0.0}

        rng = high.iloc[-1] - low.iloc[-1]
        if rng == 0:
            return {'type': None, 'strength': 0.0}

        o = open_.iloc[-1]
        h = high.iloc[-1]
        l = low.iloc[-1]
        c = close.iloc[-1]

        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        body = abs(c - o)

        upper_ratio = upper_wick / rng if rng else 0
        lower_ratio = lower_wick / rng if rng else 0
        body_ratio = body / rng if rng else 0

        grab_type = None
        strength = 0.0

        # Bullish stop hunt: długi dolny knot i zamknięcie > połowy zakresu
        if lower_ratio > wick_ratio and c > (l + rng * 0.55) and body_ratio < body_max_ratio:
            grab_type = 'bullish'
            strength = min(1.0, lower_ratio)

        # Bearish stop hunt: długi górny knot i zamknięcie < połowy zakresu
        if upper_ratio > wick_ratio and c < (l + rng * 0.45) and body_ratio < body_max_ratio:
            grab_type = 'bearish'
            strength = max(strength, min(1.0, upper_ratio))

        return {'type': grab_type, 'strength': strength}

