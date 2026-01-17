#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Główna Strategia Tradingowa - ICT + Smart Money + ML
Wszystkie sygnały i taktyki
"""

import pandas as pd
import numpy as np
from enum import Enum
from typing import Dict, List, Tuple
from dataclasses import dataclass

class Signal(Enum):
    """Typy sygnałów"""
    LONG = "LONG"
    SHORT = "SHORT"
    EXIT_LONG = "EXIT_LONG"
    EXIT_SHORT = "EXIT_SHORT"
    NEUTRAL = "NEUTRAL"


@dataclass
class TradingSignal:
    """Struktura sygnału tradingowego"""
    signal: Signal
    confidence: float  # 0-100%
    entry_price: float
    stop_loss: float
    take_profit: float
    reasons: List[str]
    timeframe: str
    timestamp: pd.Timestamp


class TradingStrategy:
    """
    Główna strategia łącząca:
    - ICT Concepts (Liquidity, FVG, Order Blocks)
    - Smart Money Concepts
    - Wskaźniki techniczne
    - Volume Analysis
    - Wyckoff Method
    - ML predictions
    """
    
    def __init__(self):
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M']
        self.signals_history = []
        
    def detect_liquidity_grab(self, df: pd.DataFrame, 
                             liquidity_levels: Dict) -> Dict:
        """
        LIQUIDITY GRAB Detection
        
        Wykrywa:
        - Stop hunt powyżej Equal Highs
        - Stop hunt poniżej Equal Lows
        - Wejście po liquidity grab
        """
        current_price = df['close'].iloc[-1]
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        signals = []
        
        # Liquidity Grab LONG (sweep below EQL, then reversal)
        for eql in liquidity_levels.get('equal_lows', []):
            if current_low < eql and current_price > eql:
                # Świeca przeszła przez EQL i zamknęła się powyżej
                signals.append({
                    'type': 'LIQUIDITY_GRAB_LONG',
                    'level': eql,
                    'confidence': 80,
                    'reason': f'Liquidity swept at ${eql:.2f}, bullish reversal'
                })
        
        # Liquidity Grab SHORT (sweep above EQH, then reversal)
        for eqh in liquidity_levels.get('equal_highs', []):
            if current_high > eqh and current_price < eqh:
                # Świeca przeszła przez EQH i zamknęła się poniżej
                signals.append({
                    'type': 'LIQUIDITY_GRAB_SHORT',
                    'level': eqh,
                    'confidence': 80,
                    'reason': f'Liquidity swept at ${eqh:.2f}, bearish reversal'
                })
        
        return {'signals': signals, 'count': len(signals)}
    
    def detect_fvg_strategy(self, df: pd.DataFrame, fvg_data: pd.DataFrame) -> List[Dict]:
        """
        FVG (Fair Value Gap) Strategy
        
        Wejście gdy cena wraca do FVG:
        - Bullish FVG: entry gdy cena spada do FVG
        - Bearish FVG: entry gdy cena rośnie do FVG
        """
        current_price = df['close'].iloc[-1]
        signals = []
        
        if fvg_data.empty:
            return signals
        
        # Szukaj niewypełnionych FVG
        for _, fvg in fvg_data.iterrows():
            if fvg['type'] == 'bullish':
                # Czy cena w obszarze FVG?
                if fvg['low'] <= current_price <= fvg['high']:
                    signals.append({
                        'type': 'FVG_LONG',
                        'entry': current_price,
                        'confidence': 75,
                        'reason': f'Price in Bullish FVG ${fvg["low"]:.2f}-${fvg["high"]:.2f}'
                    })
            
            elif fvg['type'] == 'bearish':
                if fvg['low'] <= current_price <= fvg['high']:
                    signals.append({
                        'type': 'FVG_SHORT',
                        'entry': current_price,
                        'confidence': 75,
                        'reason': f'Price in Bearish FVG ${fvg["low"]:.2f}-${fvg["high"]:.2f}'
                    })
        
        return signals
    
    def detect_bull_bear_trap(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        BULL TRAP & BEAR TRAP Detection
        
        Bull Trap:
        - Cena przebija opór
        - Niski wolumen
        - Szybki powrót poniżej oporu
        
        Bear Trap:
        - Cena przebija wsparcie
        - Niski wolumen
        - Szybki powrót powyżej wsparcia
        """
        if len(df) < lookback:
            return {'trap': None}
        
        recent = df.tail(lookback)
        current_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        
        # Oblicz support/resistance
        resistance = recent['high'].quantile(0.95)
        support = recent['low'].quantile(0.05)
        avg_volume = recent['volume'].mean()
        current_volume = df['volume'].iloc[-1]
        
        # BULL TRAP Detection
        if (df['high'].iloc[-2] > resistance and  # Breakout
            current_close < resistance and         # Failed breakout
            current_volume < avg_volume * 0.8):    # Low volume
            return {
                'trap': 'BULL_TRAP',
                'signal': 'SHORT',
                'confidence': 85,
                'entry': current_close,
                'stop': resistance * 1.01,
                'reason': 'Bull trap detected - fake breakout above resistance'
            }
        
        # BEAR TRAP Detection
        if (df['low'].iloc[-2] < support and      # Breakdown
            current_close > support and            # Failed breakdown
            current_volume < avg_volume * 0.8):    # Low volume
            return {
                'trap': 'BEAR_TRAP',
                'signal': 'LONG',
                'confidence': 85,
                'entry': current_close,
                'stop': support * 0.99,
                'reason': 'Bear trap detected - fake breakdown below support'
            }
        
        return {'trap': None}
    
    def wyckoff_phase_detection(self, df: pd.DataFrame, lookback: int = 100) -> str:
        """
        WYCKOFF METHOD - Phase Detection
        
        Phases:
        - Accumulation (faza A-E)
        - Markup (wzrost)
        - Distribution (faza A-E)
        - Markdown (spadek)
        """
        if len(df) < lookback:
            return 'UNKNOWN'
        
        recent = df.tail(lookback)
        
        # Oblicz trendy
        price_change = (recent['close'].iloc[-1] - recent['close'].iloc[0]) / recent['close'].iloc[0]
        volume_trend = recent['volume'].iloc[-20:].mean() / recent['volume'].iloc[:20].mean()
        volatility = recent['close'].pct_change().std()
        
        # ACCUMULATION: niska zmienność, rosnący wolumen, cena sideways
        if abs(price_change) < 0.05 and volume_trend > 1.2 and volatility < 0.02:
            return 'ACCUMULATION'
        
        # MARKUP: silny wzrost, rosnący wolumen
        if price_change > 0.15 and volume_trend > 1.0:
            return 'MARKUP'
        
        # DISTRIBUTION: niska zmienność, wysoki wolumen, cena sideways na górze
        if abs(price_change) < 0.05 and volume_trend > 1.2 and recent['close'].iloc[-1] > recent['close'].quantile(0.9):
            return 'DISTRIBUTION'
        
        # MARKDOWN: silny spadek
        if price_change < -0.15:
            return 'MARKDOWN'
        
        return 'NEUTRAL'
    
    def open_range_breakout(self, df: pd.DataFrame, 
                           session_start: int = 0,
                           session_length: int = 30) -> Dict:
        """
        OPEN RANGE BREAKOUT Strategy
        
        Wykrywa:
        - Range w pierwszych N świecach sesji
        - Breakout powyżej high range = LONG
        - Breakdown poniżej low range = SHORT
        """
        if len(df) < session_start + session_length:
            return {'signal': None}
        
        # Zakres otwarcia (pierwsze N świec)
        open_range = df.iloc[session_start:session_start + session_length]
        or_high = open_range['high'].max()
        or_low = open_range['low'].min()
        or_mid = (or_high + or_low) / 2
        
        current_price = df['close'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].iloc[-50:].mean()
        
        # Breakout LONG
        if current_price > or_high and current_volume > avg_volume * 1.5:
            return {
                'signal': 'LONG',
                'type': 'ORB_LONG',
                'entry': current_price,
                'stop': or_mid,
                'target': or_high + (or_high - or_low),  # Range projection
                'confidence': 80,
                'reason': f'Open Range Breakout LONG above ${or_high:.2f}'
            }
        
        # Breakdown SHORT
        if current_price < or_low and current_volume > avg_volume * 1.5:
            return {
                'signal': 'SHORT',
                'type': 'ORB_SHORT',
                'entry': current_price,
                'stop': or_mid,
                'target': or_low - (or_high - or_low),  # Range projection
                'confidence': 80,
                'reason': f'Open Range Breakdown SHORT below ${or_low:.2f}'
            }
        
        return {'signal': None}
    
    def calculate_session_sentiment(self, df: pd.DataFrame) -> Dict:
        """
        Sentyment Sesji
        
        Analizuje:
        - Open vs Close
        - High vs Low (wicks)
        - Volume
        - Komentarz PL
        """
        open_price = df['open'].iloc[0]
        close_price = df['close'].iloc[-1]
        high_price = df['high'].max()
        low_price = df['low'].min()
        total_volume = df['volume'].sum()
        
        # Body vs Wick analysis
        body = abs(close_price - open_price)
        upper_wick = high_price - max(open_price, close_price)
        lower_wick = min(open_price, close_price) - low_price
        total_range = high_price - low_price
        
        body_percent = (body / total_range) * 100 if total_range > 0 else 0
        
        # Sentyment
        if close_price > open_price:
            sentiment = 'BULLISH'
            strength = (close_price - open_price) / open_price * 100
        elif close_price < open_price:
            sentiment = 'BEARISH'
            strength = (open_price - close_price) / open_price * 100
        else:
            sentiment = 'NEUTRAL'
            strength = 0
        
        # Komentarz PL
        if sentiment == 'BULLISH':
            if body_percent > 70:
                komentarz = f"💪 Silna sesja bycza! Wzrost {strength:.2f}%. Duży body, minimalne knoty."
            elif upper_wick > body * 2:
                komentarz = f"⚠️ Bycza sesja z rejestracją. Wzrost {strength:.2f}%, ale długi górny knot - opór."
            else:
                komentarz = f"📈 Umiarkowana sesja bycza. Wzrost {strength:.2f}%."
        
        elif sentiment == 'BEARISH':
            if body_percent > 70:
                komentarz = f"📉 Silna sesja niedźwiedzia! Spadek {strength:.2f}%. Duży body, minimalne knoty."
            elif lower_wick > body * 2:
                komentarz = f"⚠️ Niedźwiedzia sesja z rejestracją. Spadek {strength:.2f}%, ale długi dolny knot - wsparcie."
            else:
                komentarz = f"📉 Umiarkowana sesja niedźwiedzia. Spadek {strength:.2f}%."
        else:
            komentarz = "➡️ Sesja neutralna. Brak wyraźnego kierunku."
        
        # Volume komentarz
        if 'volume' in df.columns:
            avg_vol = df['volume'].mean()
            if total_volume > avg_vol * 1.5:
                komentarz += " 🔊 Wysoki wolumen - silne zaangażowanie."
            elif total_volume < avg_vol * 0.7:
                komentarz += " 🔇 Niski wolumen - słabe zaangażowanie."
        
        return {
            'sentiment': sentiment,
            'strength': strength,
            'open': open_price,
            'close': close_price,
            'high': high_price,
            'low': low_price,
            'body_percent': body_percent,
            'upper_wick_percent': (upper_wick / total_range * 100),
            'lower_wick_percent': (lower_wick / total_range * 100),
            'volume': total_volume,
            'komentarz': komentarz
        }
    
    def generate_final_signal(self, df: pd.DataFrame, 
                             all_indicators: Dict,
                             risk_params: Dict) -> TradingSignal:
        """
        FINALNA AGREGACJA SYGNAŁÓW
        
        Łączy wszystkie wskaźniki i generuje ostateczny sygnał
        z confidence score
        """
        signals_long = 0
        signals_short = 0
        reasons = []
        confidence = 0
        
        # RSI
        if all_indicators.get('rsi'):
            rsi = all_indicators['rsi'].iloc[-1]
            if rsi < 30:
                signals_long += 2
                reasons.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 70:
                signals_short += 2
                reasons.append(f"RSI overbought ({rsi:.1f})")
        
        # Momentum
        if all_indicators.get('momentum'):
            mom = all_indicators['momentum'].iloc[-1]
            if mom > 0:
                signals_long += 1
                reasons.append("Positive momentum")
            elif mom < 0:
                signals_short += 1
                reasons.append("Negative momentum")
        
        # Liquidity Grab
        if all_indicators.get('liquidity_grab'):
            liq = all_indicators['liquidity_grab']
            if liq.get('signals'):
                for sig in liq['signals']:
                    if sig['type'] == 'LIQUIDITY_GRAB_LONG':
                        signals_long += 3
                        reasons.append(sig['reason'])
                    elif sig['type'] == 'LIQUIDITY_GRAB_SHORT':
                        signals_short += 3
                        reasons.append(sig['reason'])
        
        # FVG
        if all_indicators.get('fvg_signals'):
            for fvg_sig in all_indicators['fvg_signals']:
                if fvg_sig['type'] == 'FVG_LONG':
                    signals_long += 2
                    reasons.append(fvg_sig['reason'])
                elif fvg_sig['type'] == 'FVG_SHORT':
                    signals_short += 2
                    reasons.append(fvg_sig['reason'])
        
        # Trap Detection
        if all_indicators.get('trap'):
            trap = all_indicators['trap']
            if trap.get('signal') == 'LONG':
                signals_long += 3
                reasons.append(trap['reason'])
            elif trap.get('signal') == 'SHORT':
                signals_short += 3
                reasons.append(trap['reason'])
        
        # Determine final signal
        total_signals = signals_long + signals_short
        if total_signals == 0:
            final_signal = Signal.NEUTRAL
            confidence = 0
        elif signals_long > signals_short:
            final_signal = Signal.LONG
            confidence = (signals_long / total_signals) * 100
        else:
            final_signal = Signal.SHORT
            confidence = (signals_short / total_signals) * 100
        
        # Calculate entry, stop, TP
        current_price = df['close'].iloc[-1]
        atr = all_indicators.get('atr', pd.Series([current_price * 0.02])).iloc[-1]
        
        if final_signal == Signal.LONG:
            entry = current_price
            stop_loss = current_price - (atr * 2)
            take_profit = current_price + (atr * 6)  # 1:3 R:R minimum
        elif final_signal == Signal.SHORT:
            entry = current_price
            stop_loss = current_price + (atr * 2)
            take_profit = current_price - (atr * 6)
        else:
            entry = current_price
            stop_loss = None
            take_profit = None
        
        return TradingSignal(
            signal=final_signal,
            confidence=confidence,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasons=reasons,
            timeframe='adaptive',
            timestamp=pd.Timestamp.now()
        )
