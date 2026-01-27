"""
🔥 ORDER FLOW & TAPE READING ANALYZER
======================================

CZYTA CO ROBIĄ WIELORYBY W CZASIE RZECZYWISTYM!

Co to robi:
- CVD (Cumulative Volume Delta) - kto kupuje, kto sprzedaje
- Iceberg Detection - ukryte duże zlecenia
- Absorption Analysis - blokowanie ruchu ceny
- Bid/Ask Imbalance - presja kupna/sprzedaży
- Whale Activity - wielkie transakcje

99% botów patrzy tylko na wykres.
Ten moduł patrzy "pod maskę" - na Order Book i Tape.

Author: Genius Engine Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Trade:
    """Pojedyncza transakcja z Tape"""
    timestamp: datetime
    price: float
    size: float
    side: str  # 'buy' or 'sell'
    is_aggressive: bool  # market order vs limit
    
    @property
    def value_usd(self) -> float:
        return self.price * self.size


@dataclass
class OrderBookLevel:
    """Poziom w Order Book"""
    price: float
    size: float
    orders_count: int = 1


@dataclass
class OrderBookSnapshot:
    """Snapshot Order Booka"""
    timestamp: datetime
    bids: List[OrderBookLevel]  # Kupujący
    asks: List[OrderBookLevel]  # Sprzedający
    
    @property
    def best_bid(self) -> float:
        return self.bids[0].price if self.bids else 0
    
    @property
    def best_ask(self) -> float:
        return self.asks[0].price if self.asks else 0
    
    @property
    def spread(self) -> float:
        return self.best_ask - self.best_bid
    
    @property
    def spread_pct(self) -> float:
        mid = (self.best_ask + self.best_bid) / 2
        return self.spread / mid if mid > 0 else 0


@dataclass
class CVDData:
    """Cumulative Volume Delta"""
    timestamp: datetime
    buy_volume: float
    sell_volume: float
    delta: float  # buy - sell
    cumulative_delta: float


@dataclass
class IcebergOrder:
    """Wykryty Iceberg (ukryte duże zlecenie)"""
    timestamp: datetime
    price: float
    estimated_size: float
    side: str
    detection_confidence: float
    fills_count: int


@dataclass
class AbsorptionEvent:
    """Wykryta absorpcja (blocking)"""
    timestamp: datetime
    price: float
    volume_absorbed: float
    side: str  # 'bid_absorption' or 'ask_absorption'
    strength: float  # 0-1


@dataclass
class WhaleAlert:
    """Alert o aktywności wieloryba"""
    timestamp: datetime
    trade_value_usd: float
    side: str
    price: float
    significance: str  # 'large', 'massive', 'whale'


# ═══════════════════════════════════════════════════════════════
# CVD ANALYZER
# ═══════════════════════════════════════════════════════════════

class CVDAnalyzer:
    """
    📊 CUMULATIVE VOLUME DELTA (CVD)
    
    Pokazuje realną presję kupna vs sprzedaży.
    
    - Rosnąca cena + rosnący CVD = zdrowy trend wzrostowy
    - Rosnąca cena + spadający CVD = słaby trend (divergence!)
    - Falling price + rising CVD = accumulation (buy signal!)
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.trades: deque = deque(maxlen=10000)
        self.cvd_history: deque = deque(maxlen=1000)
        self.cumulative_delta = 0
    
    def add_trade(self, trade: Trade):
        """Dodaj nową transakcję"""
        self.trades.append(trade)
        
        # Update cumulative delta
        if trade.side == 'buy':
            self.cumulative_delta += trade.value_usd
        else:
            self.cumulative_delta -= trade.value_usd
    
    def calculate_cvd(self, timeframe_minutes: int = 5) -> CVDData:
        """
        Oblicz CVD dla ostatniego timeframe'u.
        """
        if not self.trades:
            return CVDData(
                timestamp=datetime.now(),
                buy_volume=0,
                sell_volume=0,
                delta=0,
                cumulative_delta=self.cumulative_delta
            )
        
        cutoff = datetime.now() - timedelta(minutes=timeframe_minutes)
        
        recent_trades = [t for t in self.trades if t.timestamp >= cutoff]
        
        buy_vol = sum(t.value_usd for t in recent_trades if t.side == 'buy')
        sell_vol = sum(t.value_usd for t in recent_trades if t.side == 'sell')
        
        cvd = CVDData(
            timestamp=datetime.now(),
            buy_volume=buy_vol,
            sell_volume=sell_vol,
            delta=buy_vol - sell_vol,
            cumulative_delta=self.cumulative_delta
        )
        
        self.cvd_history.append(cvd)
        
        return cvd
    
    def detect_divergence(self, price_series: List[float]) -> Dict:
        """
        Wykryj rozbieżność między ceną a CVD.
        
        Returns:
            Dict z informacją o divergence
        """
        if len(self.cvd_history) < 20 or len(price_series) < 20:
            return {'divergence': False, 'type': None}
        
        recent_cvd = [c.cumulative_delta for c in list(self.cvd_history)[-20:]]
        recent_prices = price_series[-20:]
        
        # Price trend
        price_trend = np.polyfit(range(20), recent_prices, 1)[0]
        
        # CVD trend
        cvd_trend = np.polyfit(range(20), recent_cvd, 1)[0]
        
        # Bearish divergence: Price up, CVD down
        if price_trend > 0 and cvd_trend < 0:
            return {
                'divergence': True,
                'type': 'bearish',
                'strength': abs(cvd_trend) / (abs(price_trend) + 1),
                'signal': -0.7
            }
        
        # Bullish divergence: Price down, CVD up
        if price_trend < 0 and cvd_trend > 0:
            return {
                'divergence': True,
                'type': 'bullish',
                'strength': abs(cvd_trend) / (abs(price_trend) + 1),
                'signal': 0.7
            }
        
        return {'divergence': False, 'type': None, 'signal': 0}


# ═══════════════════════════════════════════════════════════════
# ICEBERG DETECTOR
# ═══════════════════════════════════════════════════════════════

class IcebergDetector:
    """
    🧊 ICEBERG DETECTION
    
    Wykrywa duże ukryte zlecenia, które są wykonywane w kawałkach.
    
    Sygnały:
    - Wielokrotne fills na tym samym poziomie cenowym
    - Stałe odnawianie się wolumenu po każdym fill
    - Brak znaczącego ruchu ceny mimo dużego wolumenu
    """
    
    def __init__(self, 
                 min_fills: int = 5,
                 price_tolerance: float = 0.0001,
                 time_window_seconds: int = 60):
        self.min_fills = min_fills
        self.price_tolerance = price_tolerance
        self.time_window = time_window_seconds
        self.recent_trades: deque = deque(maxlen=5000)
        self.detected_icebergs: List[IcebergOrder] = []
    
    def add_trade(self, trade: Trade):
        """Dodaj transakcję do analizy"""
        self.recent_trades.append(trade)
    
    def detect(self) -> List[IcebergOrder]:
        """
        Wykryj icebergi w ostatnich transakcjach.
        """
        if len(self.recent_trades) < self.min_fills:
            return []
        
        icebergs = []
        cutoff = datetime.now() - timedelta(seconds=self.time_window)
        
        recent = [t for t in self.recent_trades if t.timestamp >= cutoff]
        
        # Grupuj po cenie (z tolerancją)
        price_groups: Dict[float, List[Trade]] = {}
        
        for trade in recent:
            # Znajdź istniejącą grupę lub stwórz nową
            found_group = False
            for ref_price in price_groups:
                if abs(trade.price - ref_price) / ref_price < self.price_tolerance:
                    price_groups[ref_price].append(trade)
                    found_group = True
                    break
            
            if not found_group:
                price_groups[trade.price] = [trade]
        
        # Szukaj icebergów - dużo fills na jednym poziomie
        for ref_price, trades in price_groups.items():
            if len(trades) >= self.min_fills:
                # Sprawdź czy to iceberg pattern
                total_volume = sum(t.value_usd for t in trades)
                avg_fill_size = total_volume / len(trades)
                
                # Iceberg ma podobne rozmiary fills
                sizes = [t.value_usd for t in trades]
                size_std = np.std(sizes) / np.mean(sizes) if np.mean(sizes) > 0 else 1
                
                if size_std < 0.5:  # Spójne rozmiary = iceberg
                    # Określ stronę
                    buy_count = sum(1 for t in trades if t.side == 'buy')
                    sell_count = len(trades) - buy_count
                    side = 'buy' if buy_count > sell_count else 'sell'
                    
                    confidence = min(1.0, len(trades) / (self.min_fills * 2))
                    
                    iceberg = IcebergOrder(
                        timestamp=datetime.now(),
                        price=ref_price,
                        estimated_size=total_volume * 2,  # Zakładamy jeszcze tyle ukryte
                        side=side,
                        detection_confidence=confidence,
                        fills_count=len(trades)
                    )
                    
                    icebergs.append(iceberg)
        
        self.detected_icebergs = icebergs
        return icebergs


# ═══════════════════════════════════════════════════════════════
# ABSORPTION ANALYZER
# ═══════════════════════════════════════════════════════════════

class AbsorptionAnalyzer:
    """
    🛡️ ABSORPTION DETECTION
    
    Wykrywa gdy duży gracz "pochłania" presję w jednym kierunku.
    
    Przykład: Cena próbuje spaść, ale bid wall pochłania całą sprzedaż
    → Silny sygnał kupna!
    """
    
    def __init__(self, min_volume_ratio: float = 3.0):
        self.min_volume_ratio = min_volume_ratio
        self.absorption_events: List[AbsorptionEvent] = []
    
    def analyze(self,
                trades: List[Trade],
                orderbook: OrderBookSnapshot,
                price_movement_pct: float) -> Optional[AbsorptionEvent]:
        """
        Sprawdź czy występuje absorpcja.
        
        Args:
            trades: Ostatnie transakcje
            orderbook: Aktualny orderbook
            price_movement_pct: Ruch ceny w ostatnim okresie
        """
        if not trades:
            return None
        
        # Oblicz wolumen po każdej stronie
        buy_volume = sum(t.value_usd for t in trades if t.side == 'buy')
        sell_volume = sum(t.value_usd for t in trades if t.side == 'sell')
        
        total_volume = buy_volume + sell_volume
        
        # BID ABSORPTION: Dużo sell volume, ale cena nie spada
        if sell_volume > buy_volume * self.min_volume_ratio:
            if price_movement_pct >= -0.001:  # Cena stabilna lub rośnie
                absorption = AbsorptionEvent(
                    timestamp=datetime.now(),
                    price=orderbook.best_bid,
                    volume_absorbed=sell_volume,
                    side='bid_absorption',
                    strength=min(1.0, sell_volume / buy_volume / 5)
                )
                self.absorption_events.append(absorption)
                return absorption
        
        # ASK ABSORPTION: Dużo buy volume, ale cena nie rośnie
        if buy_volume > sell_volume * self.min_volume_ratio:
            if price_movement_pct <= 0.001:  # Cena stabilna lub spada
                absorption = AbsorptionEvent(
                    timestamp=datetime.now(),
                    price=orderbook.best_ask,
                    volume_absorbed=buy_volume,
                    side='ask_absorption',
                    strength=min(1.0, buy_volume / sell_volume / 5)
                )
                self.absorption_events.append(absorption)
                return absorption
        
        return None


# ═══════════════════════════════════════════════════════════════
# WHALE DETECTOR
# ═══════════════════════════════════════════════════════════════

class WhaleDetector:
    """
    🐋 WHALE ACTIVITY DETECTION
    
    Wykrywa duże transakcje i alarmuje.
    
    Progi (dla BTC):
    - Large: > $500K
    - Massive: > $2M
    - Whale: > $10M
    """
    
    THRESHOLDS = {
        'large': 500_000,
        'massive': 2_000_000,
        'whale': 10_000_000
    }
    
    def __init__(self):
        self.whale_alerts: List[WhaleAlert] = []
    
    def check_trade(self, trade: Trade) -> Optional[WhaleAlert]:
        """
        Sprawdź czy transakcja to whale activity.
        """
        value = trade.value_usd
        
        if value >= self.THRESHOLDS['whale']:
            significance = 'whale'
        elif value >= self.THRESHOLDS['massive']:
            significance = 'massive'
        elif value >= self.THRESHOLDS['large']:
            significance = 'large'
        else:
            return None
        
        alert = WhaleAlert(
            timestamp=trade.timestamp,
            trade_value_usd=value,
            side=trade.side,
            price=trade.price,
            significance=significance
        )
        
        self.whale_alerts.append(alert)
        return alert
    
    def get_recent_whale_activity(self, minutes: int = 60) -> Dict:
        """
        Podsumuj aktywność wielorybów.
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [a for a in self.whale_alerts if a.timestamp >= cutoff]
        
        if not recent:
            return {
                'total_alerts': 0,
                'buy_volume': 0,
                'sell_volume': 0,
                'net_flow': 0,
                'signal': 0
            }
        
        buy_vol = sum(a.trade_value_usd for a in recent if a.side == 'buy')
        sell_vol = sum(a.trade_value_usd for a in recent if a.side == 'sell')
        
        net_flow = buy_vol - sell_vol
        
        # Signal based on whale flow
        if net_flow > 0:
            signal = min(1.0, net_flow / 50_000_000)  # Normalize to 50M
        else:
            signal = max(-1.0, net_flow / 50_000_000)
        
        return {
            'total_alerts': len(recent),
            'buy_volume': buy_vol,
            'sell_volume': sell_vol,
            'net_flow': net_flow,
            'signal': signal
        }


# ═══════════════════════════════════════════════════════════════
# ORDER BOOK ANALYZER
# ═══════════════════════════════════════════════════════════════

class OrderBookAnalyzer:
    """
    📚 ORDER BOOK ANALYSIS
    
    Analizuje orderbook w poszukiwaniu:
    - Bid/Ask imbalance
    - Support/Resistance walls
    - Spoofing patterns
    """
    
    def __init__(self):
        self.history: deque = deque(maxlen=100)
    
    def analyze(self, orderbook: OrderBookSnapshot) -> Dict:
        """
        Analizuj snapshot orderbooka.
        """
        self.history.append(orderbook)
        
        # Bid/Ask imbalance
        bid_volume = sum(level.size for level in orderbook.bids[:10])
        ask_volume = sum(level.size for level in orderbook.asks[:10])
        
        total = bid_volume + ask_volume
        imbalance = (bid_volume - ask_volume) / total if total > 0 else 0
        
        # Find walls (unusually large orders)
        avg_bid_size = np.mean([l.size for l in orderbook.bids[:10]]) if orderbook.bids else 0
        avg_ask_size = np.mean([l.size for l in orderbook.asks[:10]]) if orderbook.asks else 0
        
        bid_walls = [l for l in orderbook.bids if l.size > avg_bid_size * 5]
        ask_walls = [l for l in orderbook.asks if l.size > avg_ask_size * 5]
        
        # Signal
        signal = imbalance * 0.5  # Bid heavy = bullish, Ask heavy = bearish
        
        if bid_walls and not ask_walls:
            signal += 0.2  # Strong support below
        elif ask_walls and not bid_walls:
            signal -= 0.2  # Strong resistance above
        
        return {
            'imbalance': imbalance,
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'spread_pct': orderbook.spread_pct,
            'bid_walls': [(w.price, w.size) for w in bid_walls],
            'ask_walls': [(w.price, w.size) for w in ask_walls],
            'signal': max(-1, min(1, signal)),
            'confidence': min(1.0, abs(imbalance) * 2)
        }


# ═══════════════════════════════════════════════════════════════
# MAIN ORDER FLOW ENGINE
# ═══════════════════════════════════════════════════════════════

class OrderFlowEngine:
    """
    🔥 GŁÓWNY SILNIK ORDER FLOW
    
    Łączy wszystkie komponenty i generuje sygnały.
    """
    
    def __init__(self):
        self.cvd_analyzer = CVDAnalyzer()
        self.iceberg_detector = IcebergDetector()
        self.absorption_analyzer = AbsorptionAnalyzer()
        self.whale_detector = WhaleDetector()
        self.orderbook_analyzer = OrderBookAnalyzer()
        
        self.last_analysis = None
    
    def process_trade(self, trade: Trade):
        """Przetwórz nową transakcję"""
        self.cvd_analyzer.add_trade(trade)
        self.iceberg_detector.add_trade(trade)
        self.whale_detector.check_trade(trade)
    
    def analyze(self,
                orderbook: OrderBookSnapshot,
                price_series: List[float]) -> Dict:
        """
        Pełna analiza order flow.
        
        Returns:
            Dict z wszystkimi sygnałami
        """
        results = {}
        
        # 1. CVD Analysis
        cvd = self.cvd_analyzer.calculate_cvd()
        cvd_divergence = self.cvd_analyzer.detect_divergence(price_series)
        
        results['cvd'] = {
            'delta': cvd.delta,
            'cumulative': cvd.cumulative_delta,
            'divergence': cvd_divergence,
            'signal': cvd_divergence.get('signal', 0)
        }
        
        # 2. Iceberg Detection
        icebergs = self.iceberg_detector.detect()
        
        iceberg_signal = 0
        if icebergs:
            # Buy icebergs = bullish, Sell icebergs = bearish
            buy_ice = sum(i.estimated_size for i in icebergs if i.side == 'buy')
            sell_ice = sum(i.estimated_size for i in icebergs if i.side == 'sell')
            iceberg_signal = (buy_ice - sell_ice) / (buy_ice + sell_ice + 1) * 0.5
        
        results['icebergs'] = {
            'count': len(icebergs),
            'details': [(i.price, i.estimated_size, i.side) for i in icebergs],
            'signal': iceberg_signal
        }
        
        # 3. Absorption
        price_change = (price_series[-1] - price_series[-10]) / price_series[-10] if len(price_series) >= 10 else 0
        
        recent_trades = list(self.cvd_analyzer.trades)[-100:]
        absorption = self.absorption_analyzer.analyze(recent_trades, orderbook, price_change)
        
        absorption_signal = 0
        if absorption:
            if absorption.side == 'bid_absorption':
                absorption_signal = absorption.strength * 0.7  # Bullish
            else:
                absorption_signal = -absorption.strength * 0.7  # Bearish
        
        results['absorption'] = {
            'detected': absorption is not None,
            'side': absorption.side if absorption else None,
            'signal': absorption_signal
        }
        
        # 4. Whale Activity
        whale_activity = self.whale_detector.get_recent_whale_activity()
        results['whales'] = whale_activity
        
        # 5. Order Book
        ob_analysis = self.orderbook_analyzer.analyze(orderbook)
        results['orderbook'] = ob_analysis
        
        # ═══ AGGREGATE SIGNAL ═══
        
        signals = [
            results['cvd']['signal'] * 0.25,
            results['icebergs']['signal'] * 0.20,
            results['absorption']['signal'] * 0.25,
            results['whales']['signal'] * 0.15,
            results['orderbook']['signal'] * 0.15
        ]
        
        aggregate_signal = sum(signals)
        
        # Confidence
        confidences = [
            0.5 if results['cvd']['divergence'].get('divergence') else 0.2,
            min(1.0, len(icebergs) / 3) if icebergs else 0,
            absorption.strength if absorption else 0,
            min(1.0, whale_activity['total_alerts'] / 5),
            results['orderbook']['confidence']
        ]
        
        aggregate_confidence = np.mean(confidences)
        
        results['aggregate'] = {
            'signal': max(-1, min(1, aggregate_signal)),
            'confidence': aggregate_confidence,
            'reasons': self._generate_reasons(results)
        }
        
        self.last_analysis = results
        return results
    
    def _generate_reasons(self, results: Dict) -> List[str]:
        """Generuj powody dla sygnału"""
        reasons = []
        
        if results['cvd']['divergence'].get('divergence'):
            reasons.append(f"CVD {results['cvd']['divergence']['type']} divergence detected")
        
        if results['icebergs']['count'] > 0:
            reasons.append(f"{results['icebergs']['count']} iceberg orders detected")
        
        if results['absorption']['detected']:
            reasons.append(f"Absorption at {results['absorption']['side']}")
        
        if results['whales']['total_alerts'] > 0:
            flow_dir = "buying" if results['whales']['net_flow'] > 0 else "selling"
            reasons.append(f"Whales {flow_dir} (${abs(results['whales']['net_flow'])/1_000_000:.1f}M)")
        
        if abs(results['orderbook']['imbalance']) > 0.3:
            direction = "bid-heavy" if results['orderbook']['imbalance'] > 0 else "ask-heavy"
            reasons.append(f"Order book {direction}")
        
        return reasons


# ═══════════════════════════════════════════════════════════════
# INTEGRATION WITH GENIUS BRAIN
# ═══════════════════════════════════════════════════════════════

def get_order_flow_signal(orderbook_data: Dict = None,
                           trades_data: List[Dict] = None,
                           price_series: List[float] = None) -> Dict:
    """
    Get order flow signal for Genius Brain.
    
    Args:
        orderbook_data: Order book snapshot (bids, asks)
        trades_data: Recent trades list
        price_series: Recent prices
    
    Returns:
        Dict with signal for brain aggregation
    """
    try:
        engine = OrderFlowEngine()
        
        # Create mock data if not provided
        if price_series is None:
            price_series = list(np.random.randn(100) * 0.01 + 105000)
        
        # Process trades
        if trades_data:
            for t in trades_data:
                trade = Trade(
                    timestamp=datetime.fromisoformat(t.get('timestamp', datetime.now().isoformat())),
                    price=t.get('price', 105000),
                    size=t.get('size', 0.1),
                    side=t.get('side', 'buy'),
                    is_aggressive=t.get('is_aggressive', True)
                )
                engine.process_trade(trade)
        else:
            # Generate mock trades
            for _ in range(100):
                trade = Trade(
                    timestamp=datetime.now(),
                    price=105000 + np.random.randn() * 100,
                    size=np.random.uniform(0.01, 1.0),
                    side=np.random.choice(['buy', 'sell']),
                    is_aggressive=np.random.random() > 0.5
                )
                engine.process_trade(trade)
        
        # Create orderbook
        if orderbook_data:
            bids = [OrderBookLevel(b['price'], b['size']) for b in orderbook_data.get('bids', [])]
            asks = [OrderBookLevel(a['price'], a['size']) for a in orderbook_data.get('asks', [])]
        else:
            # Mock orderbook
            mid_price = price_series[-1] if price_series else 105000
            bids = [OrderBookLevel(mid_price - i * 10, np.random.uniform(0.5, 5)) for i in range(1, 11)]
            asks = [OrderBookLevel(mid_price + i * 10, np.random.uniform(0.5, 5)) for i in range(1, 11)]
        
        orderbook = OrderBookSnapshot(
            timestamp=datetime.now(),
            bids=bids,
            asks=asks
        )
        
        # Analyze
        analysis = engine.analyze(orderbook, price_series)
        
        return {
            'signal': analysis['aggregate']['signal'],
            'confidence': analysis['aggregate']['confidence'],
            'reasons': analysis['aggregate']['reasons'],
            'details': {
                'cvd_signal': analysis['cvd']['signal'],
                'iceberg_count': analysis['icebergs']['count'],
                'absorption': analysis['absorption']['detected'],
                'whale_flow': analysis['whales']['net_flow'],
                'ob_imbalance': analysis['orderbook']['imbalance']
            }
        }
        
    except Exception as e:
        logger.error(f"Order flow error: {e}")
        return {'signal': 0, 'confidence': 0, 'reasons': [f'Error: {str(e)}']}


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 ORDER FLOW ENGINE - TEST")
    print("=" * 60)
    
    # Create engine
    engine = OrderFlowEngine()
    
    print("\n1️⃣ SIMULATING TRADES")
    print("-" * 40)
    
    # Generate realistic trades
    np.random.seed(42)
    base_price = 105000
    
    for i in range(500):
        # Trend: slight upward
        price = base_price + i * 2 + np.random.randn() * 50
        
        # More buy pressure
        is_buy = np.random.random() > 0.45
        
        # Occasional whale
        if np.random.random() > 0.99:
            size = np.random.uniform(50, 200)  # Whale
        else:
            size = np.random.uniform(0.01, 2)
        
        trade = Trade(
            timestamp=datetime.now(),
            price=price,
            size=size,
            side='buy' if is_buy else 'sell',
            is_aggressive=np.random.random() > 0.3
        )
        
        engine.process_trade(trade)
    
    print(f"Processed 500 trades")
    
    print("\n2️⃣ CREATING ORDER BOOK")
    print("-" * 40)
    
    current_price = base_price + 500
    
    # Order book with bid wall
    bids = [
        OrderBookLevel(current_price - 50, 20),  # BIG BID WALL
        OrderBookLevel(current_price - 100, 5),
        OrderBookLevel(current_price - 150, 3),
        OrderBookLevel(current_price - 200, 2),
    ]
    
    asks = [
        OrderBookLevel(current_price + 50, 2),
        OrderBookLevel(current_price + 100, 3),
        OrderBookLevel(current_price + 150, 4),
        OrderBookLevel(current_price + 200, 5),
    ]
    
    orderbook = OrderBookSnapshot(
        timestamp=datetime.now(),
        bids=bids,
        asks=asks
    )
    
    print(f"Best Bid: ${orderbook.best_bid:,.0f}")
    print(f"Best Ask: ${orderbook.best_ask:,.0f}")
    print(f"Spread: ${orderbook.spread:,.0f} ({orderbook.spread_pct*100:.3f}%)")
    
    print("\n3️⃣ FULL ANALYSIS")
    print("-" * 40)
    
    price_series = list(base_price + np.arange(100) * 5 + np.random.randn(100) * 20)
    
    analysis = engine.analyze(orderbook, price_series)
    
    print(f"\n📊 CVD:")
    print(f"  Delta: ${analysis['cvd']['delta']:,.0f}")
    print(f"  Divergence: {analysis['cvd']['divergence'].get('type', 'None')}")
    
    print(f"\n🧊 Icebergs:")
    print(f"  Detected: {analysis['icebergs']['count']}")
    
    print(f"\n🛡️ Absorption:")
    print(f"  Detected: {analysis['absorption']['detected']}")
    
    print(f"\n🐋 Whale Activity:")
    print(f"  Total alerts: {analysis['whales']['total_alerts']}")
    print(f"  Net flow: ${analysis['whales']['net_flow']:,.0f}")
    
    print(f"\n📚 Order Book:")
    print(f"  Imbalance: {analysis['orderbook']['imbalance']:.2f}")
    print(f"  Bid walls: {len(analysis['orderbook']['bid_walls'])}")
    print(f"  Ask walls: {len(analysis['orderbook']['ask_walls'])}")
    
    print(f"\n🎯 AGGREGATE SIGNAL")
    print("-" * 40)
    print(f"Signal: {analysis['aggregate']['signal']:.3f}")
    print(f"Confidence: {analysis['aggregate']['confidence']:.3f}")
    print(f"Reasons:")
    for reason in analysis['aggregate']['reasons']:
        print(f"  - {reason}")
    
    print("\n4️⃣ GENIUS BRAIN INTEGRATION TEST")
    print("-" * 40)
    
    signal = get_order_flow_signal(price_series=price_series)
    print(f"Brain Signal: {signal}")
    
    print("\n" + "=" * 60)
    print("✅ Order Flow Engine Ready!")
    print("=" * 60)
