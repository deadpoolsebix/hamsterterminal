#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Advanced Market Levels Analyzer
Analiza ALL zaawansowanych poziomów:
- Support/Resistance
- Likwidacja górna/dolna
- Strefy internal/external (50% podzial)
- Equal Highs/Equal Lows
- Poziomy płynności
- Wyckoff phases
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict


class AdvancedMarketLevels:
    """
    Zaawansowana analiza poziomów rynku
    """
    
    @staticmethod
    def find_support_resistance(high: pd.Series, low: pd.Series, period: int = 20) -> Tuple[List[float], List[float]]:
        """
        Znajdź poziomy Support i Resistance
        """
        support_levels = []
        resistance_levels = []
        
        if len(low) < period:
            return support_levels, resistance_levels
        
        # Lokalne minima (Support)
        for i in range(period, len(low) - period):
            if low.iloc[i] == low.iloc[i-period:i+period].min():
                support_levels.append(low.iloc[i])
        
        # Lokalne maksima (Resistance)
        for i in range(period, len(high) - period):
            if high.iloc[i] == high.iloc[i-period:i+period].max():
                resistance_levels.append(high.iloc[i])
        
        return list(set(support_levels)), list(set(resistance_levels))
    
    @staticmethod
    def calculate_50_percent_division(high: pd.Series, low: pd.Series) -> Dict:
        """
        Podzial wykresu na 50% - Internal i External Zones
        Matematyka: 
        - High Point = highest high w przedziale
        - Low Point = lowest low w przedziale
        - Mid Point = (High + Low) / 2
        - Internal Zones: między Low i Mid, między Mid i High
        - External Zones: poniżej Low i powyżej High
        """
        if len(high) == 0 or len(low) == 0:
            return {}
        
        highest = high.max()
        lowest = low.min()
        mid_point = (highest + lowest) / 2
        
        # Internal zones (50% podzial)
        lower_internal = (lowest + mid_point) / 2
        upper_internal = (mid_point + highest) / 2
        
        return {
            'highest': highest,
            'lowest': lowest,
            'mid_point': mid_point,
            'lower_internal': lower_internal,  # 25% podzial
            'upper_internal': upper_internal,  # 75% podzial
            'external_high': highest * 1.02,    # 2% powyżej High
            'external_low': lowest * 0.98,      # 2% poniżej Low
        }
    
    @staticmethod
    def find_equal_highs_equal_lows(high: pd.Series, low: pd.Series, tolerance: float = 0.001) -> Dict:
        """
        Znajdź Equal Highs (EQH) i Equal Lows (EQL)
        EQH: Kilka lokalnych szczytów na prawie tej samej cenie
        EQL: Kilka lokalnych dołków na prawie tej samej cenie
        tolerance: % tolerancji na porównanie
        """
        eqh_list = []
        eql_list = []
        
        # Znajdź lokalne max i min
        local_highs = []
        local_lows = []
        
        for i in range(5, len(high) - 5):
            if high.iloc[i] == high.iloc[i-5:i+5].max():
                local_highs.append((i, high.iloc[i]))
            if low.iloc[i] == low.iloc[i-5:i+5].min():
                local_lows.append((i, low.iloc[i]))
        
        # Porównaj wysokości
        for i in range(len(local_highs)):
            for j in range(i+1, len(local_highs)):
                price_i = local_highs[i][1]
                price_j = local_highs[j][1]
                if abs(price_i - price_j) / price_i < tolerance:
                    eqh_list.append((local_highs[i][0], local_highs[j][0], price_i))
        
        for i in range(len(local_lows)):
            for j in range(i+1, len(local_lows)):
                price_i = local_lows[i][1]
                price_j = local_lows[j][1]
                if abs(price_i - price_j) / price_i < tolerance:
                    eql_list.append((local_lows[i][0], local_lows[j][0], price_i))
        
        return {
            'equal_highs': eqh_list,
            'equal_lows': eql_list,
        }
    
    @staticmethod
    def detect_wyckoff_phases(close: pd.Series, volume: pd.Series) -> List[Dict]:
        """
        Detektuj fazy Wyckoffa:
        1. Accumulation (boczny trend, rosnący wolumen)
        2. Mark-Up (trend wzrostowy)
        3. Distribution (szczyt, rosnący wolumen)
        4. Mark-Down (trend spadkowy)
        """
        phases = []
        
        if len(close) < 50:
            return phases
        
        for i in range(20, len(close) - 20):
            window = close.iloc[i-20:i+20]
            volume_window = volume.iloc[i-20:i+20]
            
            # Oblicz trend w oknie
            trend = (window.iloc[-1] - window.iloc[0]) / window.iloc[0]
            avg_volume = volume_window.mean()
            current_volume = volume.iloc[i]
            
            # Accumulation: boczny, podwyższony wolumen
            if abs(trend) < 0.01 and current_volume > avg_volume * 1.5:
                phases.append({
                    'index': i,
                    'phase': 'ACCUMULATION',
                    'signal_strength': min(current_volume / (avg_volume * 1.5), 2.0)
                })
            
            # Mark-Up: trend wzrostowy
            elif trend > 0.02 and current_volume > avg_volume:
                phases.append({
                    'index': i,
                    'phase': 'MARKUP',
                    'signal_strength': min(trend / 0.05, 2.0)
                })
            
            # Distribution: szczyt, rosnący wolumen
            elif trend < 0.02 and trend > -0.01 and current_volume > avg_volume * 2:
                phases.append({
                    'index': i,
                    'phase': 'DISTRIBUTION',
                    'signal_strength': min(current_volume / (avg_volume * 2), 2.0)
                })
            
            # Mark-Down: trend spadkowy
            elif trend < -0.02 and current_volume > avg_volume:
                phases.append({
                    'index': i,
                    'phase': 'MARKDOWN',
                    'signal_strength': min(abs(trend) / 0.05, 2.0)
                })
        
        return phases
    
    @staticmethod
    def calculate_liquidity_levels(orderbook_data: Dict = None, price: float = 0) -> Dict:
        """
        Oblicz poziomy płynności na podstawie orderbooka
        """
        if orderbook_data is None:
            orderbook_data = {}
        
        return {
            'bid_walls': orderbook_data.get('bid_walls', []),
            'ask_walls': orderbook_data.get('ask_walls', []),
            'major_support': price * 0.98,  # Duże wsparcie 2% poniżej
            'major_resistance': price * 1.02,  # Duży opór 2% powyżej
        }
    
    @staticmethod
    def find_open_range_breakout(open_: float, high_range: pd.Series, low_range: pd.Series, period: int = 60) -> Dict:
        """
        Detectuj Open Range Breakout (ORB)
        ORB: Po otwarciu sesji, jeśli cena przebije otwarcie w ciągu X minut
        """
        if len(high_range) < period or len(low_range) < period:
            return {}
        
        opening_price = open_
        high_orb = high_range.iloc[:period].max()
        low_orb = low_range.iloc[:period].min()
        
        breakout_high = high_orb > opening_price * 1.005  # 0.5% powyżej open
        breakout_low = low_orb < opening_price * 0.995    # 0.5% poniżej open
        
        return {
            'opening_price': opening_price,
            'high_orb': high_orb,
            'low_orb': low_orb,
            'breakout_high': breakout_high,
            'breakout_low': breakout_low,
        }
    
    @staticmethod
    def detect_liquidity_grab(high: pd.Series, low: pd.Series, period: int = 5) -> List[Dict]:
        """
        Detectuj Liquidity Grab (szybkie wybicie i powrót)
        """
        grabs = []
        
        for i in range(period, len(high) - period):
            # Szybkie wybicie do góry
            if high.iloc[i] > high.iloc[i-period:i].max() * 1.005:
                # Jeśli następnie wraca w dół
                if low.iloc[i] < high.iloc[i] * 0.995:
                    grabs.append({
                        'index': i,
                        'type': 'LIQUIDITY_GRAB_UP',
                        'price': high.iloc[i],
                        'confirmation_price': low.iloc[i]
                    })
            
            # Szybkie wybicie w dół
            if low.iloc[i] < low.iloc[i-period:i].min() * 0.995:
                # Jeśli następnie wraca w górę
                if high.iloc[i] > low.iloc[i] * 1.005:
                    grabs.append({
                        'index': i,
                        'type': 'LIQUIDITY_GRAB_DOWN',
                        'price': low.iloc[i],
                        'confirmation_price': high.iloc[i]
                    })
        
        return grabs
    
    @staticmethod
    def detect_session_info(dates: pd.DatetimeIndex) -> Dict:
        """
        Detectuj informacje o sesjach:
        - Asian Session: 20:00 - 00:00 (NY time)
        - London Session: 02:00 - 05:00 (NY time)
        - New York Session: 08:00 - 11:00 (NY time)
        - London Close: 10:00 - 12:00 (NY time)
        """
        sessions = {
            'asian': [],
            'london': [],
            'newyork': [],
            'london_close': [],
        }
        
        for i, date in enumerate(dates):
            hour = date.hour
            
            if 20 <= hour or hour < 1:
                sessions['asian'].append(i)
            elif 2 <= hour < 6:
                sessions['london'].append(i)
            elif 8 <= hour < 12:
                sessions['newyork'].append(i)
            elif 10 <= hour < 13:
                sessions['london_close'].append(i)
        
        return sessions
    
    @staticmethod
    def calculate_wick_analysis(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        """
        Analiza Wick Price & Action (Wicków)
        """
        wick_data = pd.DataFrame({
            'upper_wick': high - np.maximum(open_, close),
            'lower_wick': np.minimum(open_, close) - low,
            'body': np.abs(close - open_),
            'range': high - low,
            'is_bullish': close >= open_,
        })
        
        # % wicks relative to range
        wick_data['upper_wick_pct'] = (wick_data['upper_wick'] / wick_data['range'] * 100).round(2)
        wick_data['lower_wick_pct'] = (wick_data['lower_wick'] / wick_data['range'] * 100).round(2)
        
        return wick_data
    
    @staticmethod
    def detect_convergence_divergence(close: pd.Series, high: pd.Series, low: pd.Series) -> List[Dict]:
        """
        Detectuj zbieżności i rozbieżności
        (cena tworzy nowy szczyt, ale wskaźnik nie potwierdza)
        """
        signals = []
        
        for i in range(10, len(close)):
            recent_high_price = high.iloc[i-10:i].max()
            recent_high_idx = high.iloc[i-10:i].idxmax()
            
            recent_low_price = low.iloc[i-10:i].min()
            recent_low_idx = low.iloc[i-10:i].idxmin()
            
            # Hidden Divergence: nowy high, ale close niżej
            if close.iloc[i] > close.iloc[i-10] and high.iloc[i] > recent_high_price:
                if close.iloc[i] < recent_high_price * 0.99:
                    signals.append({
                        'index': i,
                        'type': 'HIDDEN_DIVERGENCE_BEARISH',
                        'price': high.iloc[i]
                    })
            
            # Regular Divergence: nowy low, ale close wyżej
            if close.iloc[i] < close.iloc[i-10] and low.iloc[i] < recent_low_price:
                if close.iloc[i] > recent_low_price * 1.01:
                    signals.append({
                        'index': i,
                        'type': 'HIDDEN_DIVERGENCE_BULLISH',
                        'price': low.iloc[i]
                    })
        
        return signals

