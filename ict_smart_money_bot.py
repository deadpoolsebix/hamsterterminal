"""
🎯 ICT SMART MONEY BOT - Główny Moduł Tradingowy
================================================

Kompletny system tradingowy oparty na metodologii ICT (Inner Circle Trader).
Łączy wszystkie moduły Genius z zaawansowaną logiką Smart Money.

FUNKCJE:
- Liquidity Grab Detection
- FVG (Fair Value Gap) Scanner
- SMT Divergence (BTC vs ETH)
- Wyckoff Phase Detection
- Killzones (Asian, London, NY)
- ICT Bullish/Bearish Scenarios
- Piramidowanie pozycji (5x50$)
- Emergency Exit System
- ATR Trailing Stop
- Multi-Timeframe Analysis

ZARZĄDZANIE RYZYKIEM:
- Depozyt: 5000$
- Max pozycja: 250$ (5% kapitału)
- Piramidowanie: 5x50$
- Bufor bezpieczeństwa: 20% ceny BTC
- Dźwignia: 100x (realna ekspozycja niska)

Author: Genius Engine Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import json
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class Signal(Enum):
    STRONG_LONG = "STRONG_LONG"
    LONG = "LONG"
    NEUTRAL = "NEUTRAL"
    SHORT = "SHORT"
    STRONG_SHORT = "STRONG_SHORT"
    EXIT = "EXIT"


class MarketPhase(Enum):
    """Fazy Wyckoffa"""
    ACCUMULATION = "accumulation"        # Smart Money kupuje
    MARKUP = "markup"                    # Trend wzrostowy
    DISTRIBUTION = "distribution"        # Smart Money sprzedaje
    MARKDOWN = "markdown"               # Trend spadkowy
    UNKNOWN = "unknown"


class Killzone(Enum):
    """Sesje tradingowe ICT"""
    ASIAN = "asian"           # 20:00-00:00 NY - Range building
    LONDON = "london"         # 02:00-05:00 NY - Manipulation
    NY_OPEN = "ny_open"       # 08:00-11:00 NY - Main move
    LONDON_CLOSE = "london_close"  # 10:00-12:00 NY - Reversal
    OFF_HOURS = "off_hours"   # Poza głównymi sesjami


class ICTScenario(Enum):
    """Scenariusze ICT"""
    BULLISH_REVERSAL = "bullish_reversal"    # Po Liquidity Grab w dół
    BEARISH_REVERSAL = "bearish_reversal"    # Po Liquidity Grab w górę
    BULLISH_CONTINUATION = "bullish_continuation"
    BEARISH_CONTINUATION = "bearish_continuation"
    CONSOLIDATION = "consolidation"
    NO_TRADE = "no_trade"


# ═══════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Position:
    """Pozycja tradingowa"""
    id: str
    side: str  # 'long' lub 'short'
    entry_price: float
    size_usd: float
    leverage: int
    timestamp: datetime
    stop_loss: float = 0
    take_profit: float = 0
    trailing_stop: float = 0
    
    def pnl(self, current_price: float) -> float:
        """Oblicz P&L"""
        if self.side == 'long':
            return (current_price - self.entry_price) / self.entry_price * self.size_usd * self.leverage
        else:
            return (self.entry_price - current_price) / self.entry_price * self.size_usd * self.leverage
    
    def pnl_pct(self, current_price: float) -> float:
        """P&L w procentach"""
        if self.side == 'long':
            return (current_price - self.entry_price) / self.entry_price * 100
        else:
            return (self.entry_price - current_price) / self.entry_price * 100


@dataclass
class LiquidityLevel:
    """Poziom płynności"""
    price: float
    type: str  # 'high' lub 'low'
    strength: float  # Siła poziomu 0-1
    touched: bool = False
    swept: bool = False  # Czy nastąpił Liquidity Grab


@dataclass
class FVG:
    """Fair Value Gap - Luka cenowa"""
    high: float
    low: float
    midpoint: float
    timeframe: str
    bullish: bool  # True = bullish FVG (gap w górę)
    filled: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass 
class TradeSetup:
    """Kompletny setup tradingowy"""
    signal: Signal
    scenario: ICTScenario
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    confidence: float  # 0-1
    reasons: List[str]
    killzone: Killzone
    timeframe: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BotConfig:
    """Konfiguracja bota zgodna z Twoimi założeniami"""
    # Kapitał
    deposit: float = 5000.0
    max_position_size: float = 250.0  # 5% kapitału
    pyramid_step: float = 50.0        # Pojedyncza dokładka
    max_pyramids: int = 5             # Max 5 dokładek = 250$
    
    # Dźwignia i ryzyko
    leverage: int = 100
    safety_buffer_pct: float = 20.0   # 20% buffer przed likwidacją
    
    # Take Profit / Stop Loss
    min_rr_ratio: float = 3.0         # Minimum 1:3
    target_rr_ratio: float = 10.0     # Cel 1:10
    
    # Trading
    max_concurrent_positions: int = 3
    allow_scalping: bool = True
    scalp_timeframe: str = "5m"
    
    # Killzones
    aggressive_in_killzone: bool = True
    passive_in_asian: bool = True
    
    # Emergency
    emergency_exit_pct: float = 18.0  # Zamknij przed 20% buffer


# ═══════════════════════════════════════════════════════════════
# KILLZONE DETECTOR
# ═══════════════════════════════════════════════════════════════

class KillzoneDetector:
    """
    Wykrywanie sesji tradingowych (Killzones) wg ICT.
    Czas bazowy: New York (EST/EDT)
    """
    
    KILLZONES = {
        Killzone.ASIAN: ("20:00", "00:00"),        # Range building
        Killzone.LONDON: ("02:00", "05:00"),       # Manipulation
        Killzone.NY_OPEN: ("08:00", "11:00"),      # Main move
        Killzone.LONDON_CLOSE: ("10:00", "12:00"), # Reversal
    }
    
    def __init__(self):
        self.tz_ny = pytz.timezone('America/New_York')
    
    def get_current_killzone(self) -> Tuple[Killzone, Dict]:
        """
        Pobierz aktualną sesję.
        
        Returns:
            (Killzone, info_dict)
        """
        now_ny = datetime.now(self.tz_ny)
        current_time = now_ny.strftime("%H:%M")
        
        for zone, (start, end) in self.KILLZONES.items():
            if self._is_in_range(current_time, start, end):
                return zone, {
                    'name': zone.value,
                    'start': start,
                    'end': end,
                    'time_remaining': self._time_remaining(current_time, end),
                    'optimal_for_trading': zone in [Killzone.LONDON, Killzone.NY_OPEN]
                }
        
        return Killzone.OFF_HOURS, {
            'name': 'off_hours',
            'optimal_for_trading': False,
            'next_killzone': self._next_killzone(current_time)
        }
    
    def _is_in_range(self, current: str, start: str, end: str) -> bool:
        """Sprawdź czy czas jest w zakresie (obsługuje przejście przez północ)"""
        if start <= end:
            return start <= current <= end
        else:  # Przejście przez północ (np. 20:00 - 00:00)
            return current >= start or current <= end
    
    def _time_remaining(self, current: str, end: str) -> str:
        """Ile czasu do końca sesji"""
        # Uproszczona wersja
        return f"~{end}"
    
    def _next_killzone(self, current: str) -> str:
        """Następna sesja"""
        times = [("02:00", "London"), ("08:00", "NY"), ("20:00", "Asian")]
        for t, name in times:
            if current < t:
                return f"{name} @ {t}"
        return "Asian @ 20:00"


# ═══════════════════════════════════════════════════════════════
# LIQUIDITY ANALYZER
# ═══════════════════════════════════════════════════════════════

class LiquidityAnalyzer:
    """
    Analiza poziomów płynności (Liquidity Pools).
    
    Kluczowe koncepty ICT:
    - Equal Highs (EQH) = Liquidity above
    - Equal Lows (EQL) = Liquidity below
    - Liquidity Grab = Sweep of highs/lows before reversal
    """
    
    def __init__(self, lookback: int = 50):
        self.lookback = lookback
        self.liquidity_levels: List[LiquidityLevel] = []
    
    def find_liquidity_levels(self, data: pd.DataFrame) -> List[LiquidityLevel]:
        """
        Znajdź poziomy płynności (swing highs/lows).
        """
        highs = data['high'].values
        lows = data['low'].values
        levels = []
        
        # Znajdź swing highs (local maxima)
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                levels.append(LiquidityLevel(
                    price=highs[i],
                    type='high',
                    strength=self._calculate_strength(highs, i, 'high')
                ))
        
        # Znajdź swing lows (local minima)
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                levels.append(LiquidityLevel(
                    price=lows[i],
                    type='low',
                    strength=self._calculate_strength(lows, i, 'low')
                ))
        
        self.liquidity_levels = levels
        return levels
    
    def _calculate_strength(self, prices: np.ndarray, idx: int, level_type: str) -> float:
        """Oblicz siłę poziomu (ile razy testowany)"""
        level_price = prices[idx]
        tolerance = level_price * 0.001  # 0.1% tolerance
        
        touches = 0
        for i, p in enumerate(prices):
            if abs(p - level_price) <= tolerance:
                touches += 1
        
        return min(touches / 5, 1.0)  # Normalize to 0-1
    
    def detect_equal_highs(self, data: pd.DataFrame, tolerance: float = 0.002) -> List[float]:
        """
        Znajdź Equal Highs (EQH) - poziomy gdzie wielokrotnie zatrzymywała się cena.
        To są miejsca gdzie są Stop Lossy shortów = Liquidity above.
        """
        highs = data['high'].values[-self.lookback:]
        eqh = []
        
        for i in range(len(highs)):
            for j in range(i + 1, len(highs)):
                if abs(highs[i] - highs[j]) / highs[i] <= tolerance:
                    eqh.append((highs[i] + highs[j]) / 2)
        
        return list(set(eqh))
    
    def detect_equal_lows(self, data: pd.DataFrame, tolerance: float = 0.002) -> List[float]:
        """
        Znajdź Equal Lows (EQL) - Liquidity below.
        """
        lows = data['low'].values[-self.lookback:]
        eql = []
        
        for i in range(len(lows)):
            for j in range(i + 1, len(lows)):
                if abs(lows[i] - lows[j]) / lows[i] <= tolerance:
                    eql.append((lows[i] + lows[j]) / 2)
        
        return list(set(eql))
    
    def detect_liquidity_grab(self, data: pd.DataFrame, current_price: float) -> Dict:
        """
        🎯 KLUCZOWA FUNKCJA: Wykryj Liquidity Grab
        
        Liquidity Grab = cena wybija swing high/low, ale natychmiast wraca.
        To sygnał, że Smart Money zebrało płynność i zaraz nastąpi odwrócenie.
        """
        highs = data['high'].values
        lows = data['low'].values
        closes = data['close'].values
        
        result = {
            'detected': False,
            'type': None,
            'level': None,
            'strength': 0,
            'signal': Signal.NEUTRAL
        }
        
        # Znajdź ostatni swing high/low
        recent_high = max(highs[-20:-1])
        recent_low = min(lows[-20:-1])
        
        current_high = highs[-1]
        current_low = lows[-1]
        current_close = closes[-1]
        
        # BULLISH LIQUIDITY GRAB: Wybicie dołka i powrót
        if current_low < recent_low and current_close > recent_low:
            result['detected'] = True
            result['type'] = 'bullish'
            result['level'] = recent_low
            result['strength'] = (recent_low - current_low) / recent_low
            result['signal'] = Signal.LONG
        
        # BEARISH LIQUIDITY GRAB: Wybicie szczytu i powrót
        elif current_high > recent_high and current_close < recent_high:
            result['detected'] = True
            result['type'] = 'bearish'
            result['level'] = recent_high
            result['strength'] = (current_high - recent_high) / recent_high
            result['signal'] = Signal.SHORT
        
        return result


# ═══════════════════════════════════════════════════════════════
# FVG SCANNER (Fair Value Gap)
# ═══════════════════════════════════════════════════════════════

class FVGScanner:
    """
    Scanner luk FVG (Fair Value Gap).
    
    FVG = 3-świecowy pattern gdzie środkowa świeca nie pokrywa się z sąsiednimi.
    Pokazuje miejsca gdzie cena "przeskoczyła" = nierównowaga popytu/podaży.
    """
    
    def __init__(self):
        self.fvgs: List[FVG] = []
    
    def scan(self, data: pd.DataFrame, timeframe: str = "1h") -> List[FVG]:
        """
        Znajdź wszystkie FVG w danych.
        """
        highs = data['high'].values
        lows = data['low'].values
        
        fvgs = []
        
        for i in range(2, len(data)):
            # Bullish FVG: Low[i] > High[i-2]
            if lows[i] > highs[i-2]:
                fvg = FVG(
                    high=lows[i],
                    low=highs[i-2],
                    midpoint=(lows[i] + highs[i-2]) / 2,
                    timeframe=timeframe,
                    bullish=True
                )
                fvgs.append(fvg)
            
            # Bearish FVG: High[i] < Low[i-2]
            elif highs[i] < lows[i-2]:
                fvg = FVG(
                    high=lows[i-2],
                    low=highs[i],
                    midpoint=(lows[i-2] + highs[i]) / 2,
                    timeframe=timeframe,
                    bullish=False
                )
                fvgs.append(fvg)
        
        self.fvgs = fvgs
        return fvgs
    
    def get_unfilled_fvgs(self, current_price: float) -> List[FVG]:
        """Pobierz niezapełnione FVG blisko obecnej ceny"""
        unfilled = []
        
        for fvg in self.fvgs:
            if not fvg.filled:
                # Sprawdź czy cena jest blisko FVG
                distance = abs(current_price - fvg.midpoint) / current_price
                if distance < 0.05:  # 5% od ceny
                    unfilled.append(fvg)
        
        return unfilled
    
    def check_fvg_fill(self, current_price: float):
        """Sprawdź czy FVG zostały zapełnione"""
        for fvg in self.fvgs:
            if not fvg.filled:
                if fvg.bullish and current_price <= fvg.low:
                    fvg.filled = True
                elif not fvg.bullish and current_price >= fvg.high:
                    fvg.filled = True


# ═══════════════════════════════════════════════════════════════
# SMT DIVERGENCE (Smart Money Technique)
# ═══════════════════════════════════════════════════════════════

class SMTDivergence:
    """
    Korelacja SMT - porównanie BTC z ETH/DXY/Nasdaq.
    
    Jeśli BTC robi nowy szczyt, a ETH nie = divergence = fałszywy ruch!
    """
    
    def check_divergence(self, 
                         btc_data: pd.DataFrame, 
                         eth_data: pd.DataFrame,
                         lookback: int = 20) -> Dict:
        """
        Sprawdź dywergencję między BTC i ETH.
        """
        btc_highs = btc_data['high'].values[-lookback:]
        btc_lows = btc_data['low'].values[-lookback:]
        eth_highs = eth_data['high'].values[-lookback:]
        eth_lows = eth_data['low'].values[-lookback:]
        
        result = {
            'divergence_detected': False,
            'type': None,
            'signal': Signal.NEUTRAL,
            'confidence': 0
        }
        
        # Bearish divergence: BTC nowy szczyt, ETH nie
        btc_new_high = btc_highs[-1] == max(btc_highs)
        eth_new_high = eth_highs[-1] == max(eth_highs)
        
        if btc_new_high and not eth_new_high:
            result['divergence_detected'] = True
            result['type'] = 'bearish'
            result['signal'] = Signal.SHORT
            result['confidence'] = 0.7
        
        # Bullish divergence: BTC nowy dołek, ETH nie
        btc_new_low = btc_lows[-1] == min(btc_lows)
        eth_new_low = eth_lows[-1] == min(eth_lows)
        
        if btc_new_low and not eth_new_low:
            result['divergence_detected'] = True
            result['type'] = 'bullish'
            result['signal'] = Signal.LONG
            result['confidence'] = 0.7
        
        return result


# ═══════════════════════════════════════════════════════════════
# WYCKOFF PHASE DETECTOR
# ═══════════════════════════════════════════════════════════════

class WyckoffDetector:
    """
    Wykrywanie faz Wyckoffa:
    - Accumulation: Smart Money kupuje (dołek)
    - Markup: Trend wzrostowy
    - Distribution: Smart Money sprzedaje (szczyt)
    - Markdown: Trend spadkowy
    """
    
    def detect_phase(self, data: pd.DataFrame, volume: pd.Series = None) -> Tuple[MarketPhase, Dict]:
        """
        Wykryj aktualną fazę Wyckoffa.
        """
        closes = data['close'].values
        
        # Oblicz trend
        sma_20 = pd.Series(closes).rolling(20).mean().iloc[-1]
        sma_50 = pd.Series(closes).rolling(50).mean().iloc[-1]
        current_price = closes[-1]
        
        # Oblicz volatility
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns[-20:])
        avg_volatility = np.std(returns)
        
        # Określ fazę
        if current_price < sma_20 < sma_50:
            if volatility < avg_volatility * 0.7:
                phase = MarketPhase.ACCUMULATION
                info = {
                    'description': 'Smart Money akumuluje - szukaj Liquidity Grab w dół',
                    'bias': 'bullish',
                    'action': 'Szukaj LONG po Spring/Liquidity Grab'
                }
            else:
                phase = MarketPhase.MARKDOWN
                info = {
                    'description': 'Trend spadkowy - unikaj LONGów',
                    'bias': 'bearish',
                    'action': 'Szukaj SHORT lub czekaj'
                }
        
        elif current_price > sma_20 > sma_50:
            if volatility < avg_volatility * 0.7:
                phase = MarketPhase.DISTRIBUTION
                info = {
                    'description': 'Smart Money dystrybuuje - szukaj Liquidity Grab w górę',
                    'bias': 'bearish',
                    'action': 'Szukaj SHORT po UTAD/Liquidity Grab'
                }
            else:
                phase = MarketPhase.MARKUP
                info = {
                    'description': 'Trend wzrostowy - szukaj pullbacków',
                    'bias': 'bullish',
                    'action': 'Szukaj LONG na pullbackach do FVG'
                }
        else:
            phase = MarketPhase.UNKNOWN
            info = {
                'description': 'Faza przejściowa - zachowaj ostrożność',
                'bias': 'neutral',
                'action': 'Czekaj na jasny sygnał'
            }
        
        return phase, info


# ═══════════════════════════════════════════════════════════════
# ICT SCENARIO BUILDER
# ═══════════════════════════════════════════════════════════════

class ICTScenarioBuilder:
    """
    Buduje scenariusze ICT na podstawie wszystkich danych.
    """
    
    def __init__(self):
        self.liquidity = LiquidityAnalyzer()
        self.fvg_scanner = FVGScanner()
        self.smt = SMTDivergence()
        self.wyckoff = WyckoffDetector()
        self.killzone = KillzoneDetector()
    
    def build_scenario(self, 
                       btc_data: pd.DataFrame,
                       eth_data: pd.DataFrame = None,
                       current_price: float = None) -> Tuple[ICTScenario, Dict]:
        """
        🎯 GŁÓWNA FUNKCJA: Zbuduj kompletny scenariusz ICT
        """
        if current_price is None:
            current_price = btc_data['close'].iloc[-1]
        
        # 1. Killzone
        zone, zone_info = self.killzone.get_current_killzone()
        
        # 2. Liquidity levels
        liquidity_levels = self.liquidity.find_liquidity_levels(btc_data)
        liquidity_grab = self.liquidity.detect_liquidity_grab(btc_data, current_price)
        eqh = self.liquidity.detect_equal_highs(btc_data)
        eql = self.liquidity.detect_equal_lows(btc_data)
        
        # 3. FVG
        fvgs = self.fvg_scanner.scan(btc_data)
        unfilled_fvgs = self.fvg_scanner.get_unfilled_fvgs(current_price)
        
        # 4. SMT Divergence
        smt_result = {'divergence_detected': False}
        if eth_data is not None and len(eth_data) == len(btc_data):
            smt_result = self.smt.check_divergence(btc_data, eth_data)
        
        # 5. Wyckoff Phase
        phase, phase_info = self.wyckoff.detect_phase(btc_data)
        
        # 6. Zbuduj scenariusz
        scenario = ICTScenario.NO_TRADE
        confidence = 0.0
        reasons = []
        
        # ═══ LOGIKA SCENARIUSZY ═══
        
        # BULLISH REVERSAL: Liquidity Grab w dół + Bullish Wyckoff
        if liquidity_grab['detected'] and liquidity_grab['type'] == 'bullish':
            if phase in [MarketPhase.ACCUMULATION, MarketPhase.MARKUP]:
                if not smt_result.get('divergence_detected') or smt_result.get('type') == 'bullish':
                    scenario = ICTScenario.BULLISH_REVERSAL
                    confidence = 0.8
                    reasons = [
                        "✅ Liquidity Grab w dół (zebranie SL longów)",
                        f"✅ Faza Wyckoffa: {phase.value}",
                        "✅ Brak bearish SMT divergence"
                    ]
        
        # BEARISH REVERSAL: Liquidity Grab w górę + Bearish Wyckoff
        elif liquidity_grab['detected'] and liquidity_grab['type'] == 'bearish':
            if phase in [MarketPhase.DISTRIBUTION, MarketPhase.MARKDOWN]:
                if not smt_result.get('divergence_detected') or smt_result.get('type') == 'bearish':
                    scenario = ICTScenario.BEARISH_REVERSAL
                    confidence = 0.8
                    reasons = [
                        "✅ Liquidity Grab w górę (zebranie SL shortów)",
                        f"✅ Faza Wyckoffa: {phase.value}",
                        "✅ Brak bullish SMT divergence"
                    ]
        
        # CONTINUATION: Pullback do FVG w trendzie
        elif unfilled_fvgs:
            bullish_fvgs = [f for f in unfilled_fvgs if f.bullish]
            bearish_fvgs = [f for f in unfilled_fvgs if not f.bullish]
            
            if bullish_fvgs and phase == MarketPhase.MARKUP:
                scenario = ICTScenario.BULLISH_CONTINUATION
                confidence = 0.6
                reasons = [
                    f"✅ Niezapełniony bullish FVG @ {bullish_fvgs[0].midpoint:.2f}",
                    "✅ Trend wzrostowy (Markup)",
                    "📍 Szukaj LONG na pullbacku do FVG"
                ]
            
            elif bearish_fvgs and phase == MarketPhase.MARKDOWN:
                scenario = ICTScenario.BEARISH_CONTINUATION
                confidence = 0.6
                reasons = [
                    f"✅ Niezapełniony bearish FVG @ {bearish_fvgs[0].midpoint:.2f}",
                    "✅ Trend spadkowy (Markdown)",
                    "📍 Szukaj SHORT na pullbacku do FVG"
                ]
        
        # CONSOLIDATION: Brak jasnego sygnału
        elif phase == MarketPhase.UNKNOWN:
            scenario = ICTScenario.CONSOLIDATION
            confidence = 0.3
            reasons = ["⚠️ Rynek w konsolidacji - czekaj na jasny sygnał"]
        
        # SMT Divergence jako samodzielny sygnał (słabszy)
        elif smt_result.get('divergence_detected'):
            if smt_result['type'] == 'bullish':
                scenario = ICTScenario.BULLISH_REVERSAL
                confidence = 0.5
                reasons = ["⚠️ Bullish SMT Divergence (BTC słabszy niż ETH)"]
            else:
                scenario = ICTScenario.BEARISH_REVERSAL
                confidence = 0.5
                reasons = ["⚠️ Bearish SMT Divergence (BTC silniejszy niż ETH)"]
        
        # Wzmocnienie confidence w dobrym killzone
        if zone in [Killzone.LONDON, Killzone.NY_OPEN]:
            confidence = min(confidence + 0.1, 1.0)
            reasons.append(f"✅ Aktywna sesja: {zone.value}")
        elif zone == Killzone.ASIAN:
            confidence *= 0.8
            reasons.append("⚠️ Sesja azjatycka - mniejsza pewność")
        
        return scenario, {
            'confidence': confidence,
            'reasons': reasons,
            'killzone': zone.value,
            'wyckoff_phase': phase.value,
            'liquidity_grab': liquidity_grab,
            'smt_divergence': smt_result,
            'fvgs_count': len(unfilled_fvgs),
            'eqh': eqh[:3] if eqh else [],
            'eql': eql[:3] if eql else []
        }


# ═══════════════════════════════════════════════════════════════
# POSITION MANAGER (Piramidowanie)
# ═══════════════════════════════════════════════════════════════

class PositionManager:
    """
    Zarządzanie pozycjami z piramidowaniem.
    
    Logika: 5x50$ = 250$ maksymalnie
    """
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.positions: List[Position] = []
        self.closed_positions: List[Dict] = []
        self.total_pnl = 0
    
    def can_open_position(self) -> bool:
        """Czy możemy otworzyć nową pozycję?"""
        current_exposure = sum(p.size_usd for p in self.positions)
        return current_exposure < self.config.max_position_size
    
    def get_pyramid_count(self) -> int:
        """Ile mamy dokładek?"""
        return len(self.positions)
    
    def get_average_entry(self) -> float:
        """Średnia cena wejścia (ważona)"""
        if not self.positions:
            return 0
        
        total_size = sum(p.size_usd for p in self.positions)
        weighted_sum = sum(p.entry_price * p.size_usd for p in self.positions)
        
        return weighted_sum / total_size if total_size > 0 else 0
    
    def get_break_even(self) -> float:
        """Cena break-even (uwzględnia fees)"""
        avg = self.get_average_entry()
        return avg * 1.0008  # ~0.08% fee
    
    def open_pyramid(self, price: float, side: str) -> Optional[Position]:
        """
        Otwórz pozycję piramidy (dokładkę).
        """
        if self.get_pyramid_count() >= self.config.max_pyramids:
            logger.warning("Max pyramids reached (5)")
            return None
        
        if not self.can_open_position():
            logger.warning("Max position size reached")
            return None
        
        # Sprawdź czy wszystkie pozycje są w tym samym kierunku
        if self.positions and self.positions[0].side != side:
            logger.warning(f"Cannot pyramid {side} - existing positions are {self.positions[0].side}")
            return None
        
        position = Position(
            id=f"pos_{datetime.now().timestamp()}",
            side=side,
            entry_price=price,
            size_usd=self.config.pyramid_step,
            leverage=self.config.leverage,
            timestamp=datetime.now()
        )
        
        self.positions.append(position)
        logger.info(f"Opened pyramid {self.get_pyramid_count()}/5: {side} @ {price}")
        
        return position
    
    def close_all(self, current_price: float, reason: str) -> Dict:
        """Zamknij wszystkie pozycje"""
        if not self.positions:
            return {'closed': 0, 'pnl': 0}
        
        total_pnl = sum(p.pnl(current_price) for p in self.positions)
        total_size = sum(p.size_usd for p in self.positions)
        
        result = {
            'closed': len(self.positions),
            'pnl': total_pnl,
            'pnl_pct': total_pnl / total_size * 100 if total_size > 0 else 0,
            'reason': reason,
            'avg_entry': self.get_average_entry(),
            'exit_price': current_price
        }
        
        self.closed_positions.append(result)
        self.total_pnl += total_pnl
        self.positions = []
        
        logger.info(f"Closed all positions: {result}")
        
        return result
    
    def check_emergency_exit(self, current_price: float) -> bool:
        """
        🚨 EMERGENCY EXIT
        
        Zamknij pozycje jeśli strata zbliża się do 20% buffer.
        """
        if not self.positions:
            return False
        
        avg_entry = self.get_average_entry()
        side = self.positions[0].side
        
        # Oblicz % zmianę ceny
        price_change_pct = (current_price - avg_entry) / avg_entry * 100
        
        if side == 'long':
            # Dla LONG: zamknij jeśli cena spadła o więcej niż emergency_exit_pct
            if price_change_pct <= -self.config.emergency_exit_pct:
                self.close_all(current_price, f"EMERGENCY EXIT: Price dropped {price_change_pct:.1f}%")
                return True
        else:
            # Dla SHORT: zamknij jeśli cena wzrosła o więcej niż emergency_exit_pct
            if price_change_pct >= self.config.emergency_exit_pct:
                self.close_all(current_price, f"EMERGENCY EXIT: Price rose {price_change_pct:.1f}%")
                return True
        
        return False
    
    def update_trailing_stop(self, current_price: float, atr: float):
        """
        Aktualizuj trailing stop na podstawie ATR.
        """
        if not self.positions:
            return
        
        side = self.positions[0].side
        
        for pos in self.positions:
            if side == 'long':
                new_stop = current_price - (atr * 2)
                if new_stop > pos.trailing_stop:
                    pos.trailing_stop = new_stop
            else:
                new_stop = current_price + (atr * 2)
                if pos.trailing_stop == 0 or new_stop < pos.trailing_stop:
                    pos.trailing_stop = new_stop
    
    def check_trailing_stop(self, current_price: float) -> bool:
        """Sprawdź czy trailing stop został trafiony"""
        if not self.positions:
            return False
        
        side = self.positions[0].side
        
        for pos in self.positions:
            if pos.trailing_stop > 0:
                if side == 'long' and current_price <= pos.trailing_stop:
                    self.close_all(current_price, f"Trailing Stop hit @ {pos.trailing_stop}")
                    return True
                elif side == 'short' and current_price >= pos.trailing_stop:
                    self.close_all(current_price, f"Trailing Stop hit @ {pos.trailing_stop}")
                    return True
        
        return False


# ═══════════════════════════════════════════════════════════════
# MAIN BOT CLASS
# ═══════════════════════════════════════════════════════════════

class ICTSmartMoneyBot:
    """
    🎯 GŁÓWNY BOT ICT SMART MONEY
    
    Łączy wszystkie komponenty w jeden działający system.
    """
    
    def __init__(self, config: BotConfig = None):
        self.config = config or BotConfig()
        
        # Komponenty
        self.scenario_builder = ICTScenarioBuilder()
        self.position_manager = PositionManager(self.config)
        
        # State
        self.is_running = False
        self.last_analysis: Dict = {}
        self.trade_history: List[Dict] = []
        
        # Statistics
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0
        }
    
    def analyze(self, 
                btc_data: pd.DataFrame,
                eth_data: pd.DataFrame = None,
                current_price: float = None) -> Dict:
        """
        🔍 Analiza rynku - główna funkcja analizy
        """
        if current_price is None:
            current_price = btc_data['close'].iloc[-1]
        
        # Zbuduj scenariusz ICT
        scenario, details = self.scenario_builder.build_scenario(
            btc_data, eth_data, current_price
        )
        
        # Oblicz ATR dla trailing stop
        atr = self._calculate_atr(btc_data)
        
        # Sprawdź pozycje
        position_info = {
            'has_positions': len(self.position_manager.positions) > 0,
            'pyramid_count': self.position_manager.get_pyramid_count(),
            'avg_entry': self.position_manager.get_average_entry(),
            'break_even': self.position_manager.get_break_even(),
            'current_pnl': sum(p.pnl(current_price) for p in self.position_manager.positions)
        }
        
        # Zbuduj setup jeśli jest sygnał
        setup = self._build_trade_setup(scenario, details, current_price, atr)
        
        self.last_analysis = {
            'timestamp': datetime.now().isoformat(),
            'current_price': current_price,
            'scenario': scenario.value,
            'details': details,
            'setup': setup.to_dict() if setup else None,
            'position_info': position_info,
            'atr': atr
        }
        
        return self.last_analysis
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Oblicz ATR (Average True Range)"""
        highs = data['high'].values
        lows = data['low'].values
        closes = data['close'].values
        
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        
        return np.mean(tr[-period:])
    
    def _build_trade_setup(self, 
                           scenario: ICTScenario,
                           details: Dict,
                           current_price: float,
                           atr: float) -> Optional[TradeSetup]:
        """Zbuduj setup tradingowy"""
        
        if scenario in [ICTScenario.NO_TRADE, ICTScenario.CONSOLIDATION]:
            return None
        
        if details['confidence'] < 0.5:
            return None
        
        # Określ sygnał i parametry
        if scenario in [ICTScenario.BULLISH_REVERSAL, ICTScenario.BULLISH_CONTINUATION]:
            signal = Signal.LONG if details['confidence'] < 0.7 else Signal.STRONG_LONG
            stop_loss = current_price - (atr * 2)
            take_profit = current_price + (atr * self.config.target_rr_ratio * 2)
        else:
            signal = Signal.SHORT if details['confidence'] < 0.7 else Signal.STRONG_SHORT
            stop_loss = current_price + (atr * 2)
            take_profit = current_price - (atr * self.config.target_rr_ratio * 2)
        
        # Oblicz wielkość pozycji
        position_size = self.config.pyramid_step
        if details['confidence'] >= 0.8:
            position_size = self.config.pyramid_step * 2  # Podwójna dokładka przy high confidence
        
        return TradeSetup(
            signal=signal,
            scenario=scenario,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            confidence=details['confidence'],
            reasons=details['reasons'],
            killzone=Killzone(details['killzone']),
            timeframe="1h"
        )
    
    def execute(self, setup: TradeSetup, current_price: float) -> Dict:
        """
        🎯 Wykonaj trade na podstawie setupu
        """
        result = {
            'executed': False,
            'action': None,
            'position': None,
            'message': ''
        }
        
        if setup is None:
            result['message'] = "No valid setup"
            return result
        
        # Sprawdź emergency exit najpierw
        if self.position_manager.check_emergency_exit(current_price):
            result['message'] = "EMERGENCY EXIT executed"
            return result
        
        # Sprawdź trailing stop
        if self.position_manager.check_trailing_stop(current_price):
            result['message'] = "Trailing stop hit"
            return result
        
        # Sprawdź czy możemy otwierać pozycje
        if not self.position_manager.can_open_position():
            result['message'] = "Max position size reached"
            return result
        
        # Określ kierunek
        if setup.signal in [Signal.LONG, Signal.STRONG_LONG]:
            side = 'long'
        elif setup.signal in [Signal.SHORT, Signal.STRONG_SHORT]:
            side = 'short'
        else:
            result['message'] = f"Invalid signal: {setup.signal}"
            return result
        
        # Otwórz pozycję
        position = self.position_manager.open_pyramid(current_price, side)
        
        if position:
            position.stop_loss = setup.stop_loss
            position.take_profit = setup.take_profit
            
            result['executed'] = True
            result['action'] = 'OPEN'
            result['position'] = {
                'side': side,
                'entry': current_price,
                'stop_loss': setup.stop_loss,
                'take_profit': setup.take_profit,
                'size': position.size_usd,
                'pyramid_count': self.position_manager.get_pyramid_count()
            }
            result['message'] = f"Opened {side.upper()} @ {current_price}"
            
            self.stats['total_trades'] += 1
            
        return result
    
    def generate_report_pl(self, current_price: float) -> str:
        """
        📊 Generuj raport po polsku
        """
        analysis = self.last_analysis
        
        report = "\n" + "=" * 50
        report += "\n🤖 ICT SMART MONEY BOT - RAPORT"
        report += "\n" + "=" * 50
        
        # Czas i cena
        report += f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        report += f"\n💰 Cena BTC: ${current_price:,.2f}"
        
        # Scenariusz
        scenario = analysis.get('scenario', 'unknown')
        details = analysis.get('details', {})
        
        report += f"\n\n📈 SCENARIUSZ: {scenario}"
        report += f"\n   Pewność: {details.get('confidence', 0):.0%}"
        report += f"\n   Sesja: {details.get('killzone', 'unknown')}"
        report += f"\n   Faza Wyckoffa: {details.get('wyckoff_phase', 'unknown')}"
        
        # Reasons
        if details.get('reasons'):
            report += "\n\n📝 UZASADNIENIE:"
            for reason in details['reasons']:
                report += f"\n   {reason}"
        
        # Liquidity Grab
        lg = details.get('liquidity_grab', {})
        if lg.get('detected'):
            report += f"\n\n🎯 LIQUIDITY GRAB: {lg['type'].upper()}"
            report += f"\n   Poziom: ${lg['level']:,.2f}"
        
        # SMT Divergence
        smt = details.get('smt_divergence', {})
        if smt.get('divergence_detected'):
            report += f"\n\n⚠️ SMT DIVERGENCE: {smt['type'].upper()}"
        
        # Pozycje
        pos_info = analysis.get('position_info', {})
        if pos_info.get('has_positions'):
            report += "\n\n📊 POZYCJE OTWARTE:"
            report += f"\n   Dokładki: {pos_info['pyramid_count']}/5"
            report += f"\n   Średnie wejście: ${pos_info['avg_entry']:,.2f}"
            report += f"\n   Break-even: ${pos_info['break_even']:,.2f}"
            report += f"\n   P&L: ${pos_info['current_pnl']:,.2f}"
        else:
            report += "\n\n📊 Brak otwartych pozycji"
        
        # Setup
        setup = analysis.get('setup')
        if setup:
            report += "\n\n🎯 REKOMENDOWANY TRADE:"
            report += f"\n   Sygnał: {setup['signal']}"
            report += f"\n   Wejście: ${setup['entry_price']:,.2f}"
            report += f"\n   Stop Loss: ${setup['stop_loss']:,.2f}"
            report += f"\n   Take Profit: ${setup['take_profit']:,.2f}"
            report += f"\n   Wielkość: ${setup['position_size']}"
        
        # Statystyki
        report += "\n\n📈 STATYSTYKI:"
        report += f"\n   Total trades: {self.stats['total_trades']}"
        report += f"\n   Winning: {self.stats['winning_trades']}"
        report += f"\n   Losing: {self.stats['losing_trades']}"
        report += f"\n   Total P&L: ${self.stats['total_pnl']:,.2f}"
        
        report += "\n" + "=" * 50
        
        return report


# ═══════════════════════════════════════════════════════════════
# INTEGRATION WITH GENIUS ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

def get_ict_signal(btc_data: pd.DataFrame, 
                   eth_data: pd.DataFrame = None) -> Dict:
    """
    Funkcja integracyjna dla Genius Orchestrator.
    
    Returns:
        Dict z sygnałem ICT
    """
    bot = ICTSmartMoneyBot()
    analysis = bot.analyze(btc_data, eth_data)
    
    # Konwertuj na format dla orchestratora
    scenario = analysis.get('scenario', 'no_trade')
    details = analysis.get('details', {})
    
    # Mapowanie na score -1 do 1
    score_map = {
        'bullish_reversal': 0.8,
        'bullish_continuation': 0.6,
        'consolidation': 0,
        'no_trade': 0,
        'bearish_continuation': -0.6,
        'bearish_reversal': -0.8
    }
    
    score = score_map.get(scenario, 0) * details.get('confidence', 0.5)
    
    return {
        'signal': score,
        'confidence': details.get('confidence', 0.5),
        'scenario': scenario,
        'reasons': details.get('reasons', []),
        'killzone': details.get('killzone', 'unknown'),
        'wyckoff_phase': details.get('wyckoff_phase', 'unknown')
    }


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 ICT SMART MONEY BOT - TEST")
    print("=" * 60)
    
    # Generate sample BTC data
    np.random.seed(42)
    n = 200
    
    # Simulate BTC price movement
    base_price = 100000
    returns = np.random.randn(n) * 0.02 + 0.0001
    prices = base_price * np.exp(np.cumsum(returns))
    
    btc_data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(n) * 0.01)),
        'low': prices * (1 - np.abs(np.random.randn(n) * 0.01)),
        'close': prices,
        'volume': np.random.randint(1000, 10000, n)
    })
    
    # Similar for ETH (correlated)
    eth_returns = returns * 1.2 + np.random.randn(n) * 0.01
    eth_prices = 3500 * np.exp(np.cumsum(eth_returns))
    
    eth_data = pd.DataFrame({
        'open': eth_prices * (1 + np.random.randn(n) * 0.005),
        'high': eth_prices * (1 + np.abs(np.random.randn(n) * 0.01)),
        'low': eth_prices * (1 - np.abs(np.random.randn(n) * 0.01)),
        'close': eth_prices,
        'volume': np.random.randint(5000, 50000, n)
    })
    
    # Create bot
    config = BotConfig(
        deposit=5000,
        max_position_size=250,
        pyramid_step=50,
        leverage=100,
        safety_buffer_pct=20
    )
    
    bot = ICTSmartMoneyBot(config)
    
    # Analyze
    print("\n🔍 ANALIZA RYNKU...")
    analysis = bot.analyze(btc_data, eth_data)
    
    current_price = btc_data['close'].iloc[-1]
    
    # Generate report
    print(bot.generate_report_pl(current_price))
    
    # Test execution
    if analysis.get('setup'):
        print("\n🎯 TEST WYKONANIA TRADE...")
        
        setup_data = analysis['setup']
        
        # Recreate setup object
        setup = TradeSetup(
            signal=Signal[setup_data['signal']],
            scenario=ICTScenario[setup_data['scenario']],
            entry_price=setup_data['entry_price'],
            stop_loss=setup_data['stop_loss'],
            take_profit=setup_data['take_profit'],
            position_size=setup_data['position_size'],
            confidence=setup_data['confidence'],
            reasons=setup_data['reasons'],
            killzone=Killzone[setup_data['killzone']],
            timeframe=setup_data['timeframe']
        )
        
        result = bot.execute(setup, current_price)
        print(f"\nWynik: {result}")
    
    print("\n" + "=" * 60)
    print("✅ ICT Smart Money Bot Ready!")
    print("=" * 60)
