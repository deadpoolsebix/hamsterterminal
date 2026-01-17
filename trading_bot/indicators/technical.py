#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Wskaźniki Techniczne - Moduł ICT & Smart Money Concepts
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict

class TechnicalIndicators:
    """Wszystkie wskaźniki techniczne"""
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI - Relative Strength Index
        Wartości: 0-100
        Oversold: < 30, Overbought: > 70
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def momentum(prices: pd.Series, period: int = 10) -> pd.Series:
        """Momentum - różnica między obecną ceną a ceną sprzed N okresów"""
        return prices - prices.shift(period)
    
    @staticmethod
    def sma(prices: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        ATR - Average True Range
        Mierzy zmienność rynku
        """
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, std: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        Returns: (upper, middle, lower)
        """
        middle = prices.rolling(window=period).mean()
        std_dev = prices.rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return upper, middle, lower
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD - Moving Average Convergence Divergence
        Returns: (macd, signal, histogram)
        """
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator
        Returns: (K%, D%)
        """
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=3).mean()
        return k, d


class ICTIndicators:
    """ICT (Inner Circle Trader) & Smart Money Concepts"""
    
    @staticmethod
    def fair_value_gap(high: pd.Series, low: pd.Series, close: pd.Series, 
                       threshold: float = 0.001) -> pd.DataFrame:
        """
        FVG - Fair Value Gap (Luki)
        Wykrywa luki cenowe, które mogą być wypełnione
        """
        fvg_bullish = []
        fvg_bearish = []
        
        for i in range(2, len(close)):
            # Bullish FVG: niska świeca[i] > wysoka świeca[i-2]
            if low.iloc[i] > high.iloc[i-2]:
                gap_size = low.iloc[i] - high.iloc[i-2]
                if gap_size / close.iloc[i] > threshold:
                    fvg_bullish.append({
                        'index': i,
                        'low': high.iloc[i-2],
                        'high': low.iloc[i],
                        'size': gap_size,
                        'type': 'bullish'
                    })
            
            # Bearish FVG: wysoka świeca[i] < niska świeca[i-2]
            if high.iloc[i] < low.iloc[i-2]:
                gap_size = low.iloc[i-2] - high.iloc[i]
                if gap_size / close.iloc[i] > threshold:
                    fvg_bearish.append({
                        'index': i,
                        'low': high.iloc[i],
                        'high': low.iloc[i-2],
                        'size': gap_size,
                        'type': 'bearish'
                    })
        
        return pd.DataFrame(fvg_bullish + fvg_bearish)
    
    @staticmethod
    def order_blocks(high: pd.Series, low: pd.Series, close: pd.Series, 
                     volume: pd.Series, lookback: int = 20) -> pd.DataFrame:
        """
        Order Blocks - Bloki zleceń
        Obszary, gdzie instytucje składały duże zlecenia
        """
        order_blocks = []
        
        for i in range(lookback, len(close)):
            # Bullish Order Block: ostatnia świeca przed silnym ruchem w górę
            if close.iloc[i] > close.iloc[i-1] * 1.02:  # 2% wzrost
                if volume.iloc[i] > volume.iloc[i-lookback:i].mean() * 1.5:
                    order_blocks.append({
                        'index': i-1,
                        'low': low.iloc[i-1],
                        'high': high.iloc[i-1],
                        'type': 'bullish',
                        'strength': volume.iloc[i] / volume.iloc[i-lookback:i].mean()
                    })
            
            # Bearish Order Block: ostatnia świeca przed silnym ruchem w dół
            if close.iloc[i] < close.iloc[i-1] * 0.98:  # 2% spadek
                if volume.iloc[i] > volume.iloc[i-lookback:i].mean() * 1.5:
                    order_blocks.append({
                        'index': i-1,
                        'low': low.iloc[i-1],
                        'high': high.iloc[i-1],
                        'type': 'bearish',
                        'strength': volume.iloc[i] / volume.iloc[i-lookback:i].mean()
                    })
        
        return pd.DataFrame(order_blocks)
    
    @staticmethod
    def liquidity_levels(high: pd.Series, low: pd.Series, 
                        lookback: int = 50) -> Dict[str, List[float]]:
        """
        Poziomy Płynności
        Wykrywa Equal Highs (EQH) i Equal Lows (EQL)
        """
        tolerance = 0.001  # 0.1% tolerancja
        
        # Equal Highs
        eqh = []
        for i in range(lookback, len(high)):
            window_highs = high.iloc[i-lookback:i]
            max_high = window_highs.max()
            
            # Znajdź podobne szczyty
            similar_highs = window_highs[
                (window_highs >= max_high * (1 - tolerance)) &
                (window_highs <= max_high * (1 + tolerance))
            ]
            
            if len(similar_highs) >= 2:
                eqh.append(max_high)
        
        # Equal Lows
        eql = []
        for i in range(lookback, len(low)):
            window_lows = low.iloc[i-lookback:i]
            min_low = window_lows.min()
            
            # Znajdź podobne dołki
            similar_lows = window_lows[
                (window_lows >= min_low * (1 - tolerance)) &
                (window_lows <= min_low * (1 + tolerance))
            ]
            
            if len(similar_lows) >= 2:
                eql.append(min_low)
        
        return {
            'equal_highs': list(set(eqh)),
            'equal_lows': list(set(eql)),
            'liquidity_grab_buy': list(set(eql)),  # Potencjalne liquidity grab long
            'liquidity_grab_sell': list(set(eqh))  # Potencjalne liquidity grab short
        }
    
    @staticmethod
    def market_structure(high: pd.Series, low: pd.Series, close: pd.Series, 
                        lookback: int = 10) -> pd.Series:
        """
        Struktura Rynku - Higher Highs, Lower Lows
        Returns: 'bullish', 'bearish', 'neutral'
        """
        structure = []
        
        for i in range(lookback, len(close)):
            recent_highs = high.iloc[i-lookback:i]
            recent_lows = low.iloc[i-lookback:i]
            
            # Higher Highs & Higher Lows = Bullish
            if (high.iloc[i] > recent_highs.max() and 
                low.iloc[i] > recent_lows.min()):
                structure.append('bullish')
            
            # Lower Highs & Lower Lows = Bearish
            elif (high.iloc[i] < recent_highs.max() and 
                  low.iloc[i] < recent_lows.min()):
                structure.append('bearish')
            
            else:
                structure.append('neutral')
        
        # Wypełnij początkowe wartości
        return pd.Series(['neutral'] * lookback + structure, index=close.index)


class VolumeIndicators:
    """Wskaźniki wolumenu"""
    
    @staticmethod
    def cvd(volume: pd.Series, close: pd.Series) -> pd.Series:
        """
        CVD - Cumulative Volume Delta
        Różnica między wolumenem kupna a sprzedaży
        """
        # Uproszczona wersja: dodatni wolumen gdy cena rośnie
        delta = np.where(close.diff() > 0, volume, -volume)
        cvd = pd.Series(delta, index=volume.index).cumsum()
        return cvd
    
    @staticmethod
    def volume_profile(prices: pd.Series, volume: pd.Series, 
                      bins: int = 50) -> pd.DataFrame:
        """
        Volume Profile - Rozkład wolumenu na różnych poziomach cenowych
        """
        price_range = prices.max() - prices.min()
        bin_size = price_range / bins
        
        profile = []
        for i in range(bins):
            level_low = prices.min() + (i * bin_size)
            level_high = level_low + bin_size
            
            mask = (prices >= level_low) & (prices < level_high)
            volume_at_level = volume[mask].sum()
            
            profile.append({
                'price_level': (level_low + level_high) / 2,
                'volume': volume_at_level
            })
        
        return pd.DataFrame(profile)
    
    @staticmethod
    def on_balance_volume(close: pd.Series, volume: pd.Series) -> pd.Series:
        """OBV - On Balance Volume"""
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])
        
        return pd.Series(obv, index=close.index)
