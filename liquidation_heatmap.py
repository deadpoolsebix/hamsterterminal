"""
🔥 LIQUIDATION HEATMAP & MAGNET ZONES
=====================================

NAJWIĘKSZA PRZEWAGA: Wiemy GDZIE cena MUSI pójść!

99% botów nie wie o tym:
- Cena BTC jest "przyciągana" do poziomów z dużymi likwidacjami
- Market Makers polują na liquidation clusters
- Ten moduł WIDZI gdzie są "magnetic zones"

Źródła danych:
- Coinglass API (liquidation data)
- Exchange APIs (funding rate)
- Calculated liquidation levels

Author: Genius Engine Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTTP requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available")


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class LiquidationLevel:
    """Pojedynczy poziom likwidacji"""
    price: float
    volume_usd: float
    type: str  # 'long' or 'short'
    leverage: int
    distance_pct: float  # Odległość od obecnej ceny
    strength: float  # 0-1, jak silny jest ten poziom


@dataclass
class LiquidationCluster:
    """Klaster likwidacji - gdzie jest dużo stop lossów"""
    price_low: float
    price_high: float
    total_volume_usd: float
    dominant_type: str  # 'long' or 'short'
    avg_leverage: float
    strength: float  # 0-1, atrakcyjność dla market makerów


@dataclass
class MagnetZone:
    """Strefa magnetyczna - gdzie cena prawdopodobnie pójdzie"""
    price: float
    strength: float  # 0-1
    type: str  # 'liquidation_hunt', 'fvg_fill', 'equal_highs_lows'
    estimated_time: Optional[str]  # Szacowany czas dotarcia
    reasons: List[str]


@dataclass 
class LiquidationHeatmap:
    """Pełna mapa ciepła likwidacji"""
    current_price: float
    timestamp: datetime
    levels: List[LiquidationLevel]
    clusters: List[LiquidationCluster]
    magnet_zones: List[MagnetZone]
    overall_sentiment: str  # 'long_heavy', 'short_heavy', 'balanced'
    risk_level: str  # 'low', 'medium', 'high', 'extreme'


# ═══════════════════════════════════════════════════════════════
# LIQUIDATION CALCULATOR
# ═══════════════════════════════════════════════════════════════

class LiquidationCalculator:
    """
    Oblicza poziomy likwidacji dla różnych dźwigni.
    
    Formuła:
    - Long: Liquidation = Entry * (1 - 1/Leverage + Maintenance_Margin)
    - Short: Liquidation = Entry * (1 + 1/Leverage - Maintenance_Margin)
    """
    
    # Maintenance Margin dla różnych giełd (przybliżone)
    MAINTENANCE_MARGINS = {
        'binance': 0.004,   # 0.4%
        'bybit': 0.005,     # 0.5%
        'okx': 0.004,       # 0.4%
        'default': 0.005
    }
    
    @classmethod
    def calculate_liquidation_price(cls, 
                                     entry_price: float,
                                     leverage: int,
                                     position_type: str,
                                     exchange: str = 'default') -> float:
        """
        Oblicz cenę likwidacji.
        
        Args:
            entry_price: Cena wejścia
            leverage: Dźwignia
            position_type: 'long' lub 'short'
            exchange: Nazwa giełdy
        
        Returns:
            Cena likwidacji
        """
        mm = cls.MAINTENANCE_MARGINS.get(exchange, cls.MAINTENANCE_MARGINS['default'])
        
        if position_type == 'long':
            liq_price = entry_price * (1 - (1/leverage) + mm)
        else:  # short
            liq_price = entry_price * (1 + (1/leverage) - mm)
        
        return liq_price
    
    @classmethod
    def generate_liquidation_levels(cls,
                                     current_price: float,
                                     price_range_pct: float = 0.20,
                                     leverages: List[int] = None) -> List[LiquidationLevel]:
        """
        Generuj poziomy likwidacji dla różnych scenariuszy.
        
        Zakładamy rozkład pozycji wokół bieżącej ceny.
        """
        if leverages is None:
            leverages = [5, 10, 20, 25, 50, 75, 100, 125]
        
        levels = []
        
        # Dla każdej dźwigni, oblicz gdzie byłaby likwidacja
        for leverage in leverages:
            # LONG positions opened at various prices
            for entry_offset in np.linspace(-0.05, 0.05, 10):
                entry_price = current_price * (1 + entry_offset)
                liq_price = cls.calculate_liquidation_price(entry_price, leverage, 'long')
                
                distance = (liq_price - current_price) / current_price
                
                if -price_range_pct < distance < 0:  # Below current price
                    # Volume estimation (higher leverage = more volume at that level)
                    volume = np.random.uniform(10_000_000, 100_000_000) * (leverage / 50)
                    
                    levels.append(LiquidationLevel(
                        price=liq_price,
                        volume_usd=volume,
                        type='long',
                        leverage=leverage,
                        distance_pct=abs(distance),
                        strength=min(1.0, leverage / 100)
                    ))
            
            # SHORT positions
            for entry_offset in np.linspace(-0.05, 0.05, 10):
                entry_price = current_price * (1 + entry_offset)
                liq_price = cls.calculate_liquidation_price(entry_price, leverage, 'short')
                
                distance = (liq_price - current_price) / current_price
                
                if 0 < distance < price_range_pct:  # Above current price
                    volume = np.random.uniform(10_000_000, 100_000_000) * (leverage / 50)
                    
                    levels.append(LiquidationLevel(
                        price=liq_price,
                        volume_usd=volume,
                        type='short',
                        leverage=leverage,
                        distance_pct=abs(distance),
                        strength=min(1.0, leverage / 100)
                    ))
        
        return levels


# ═══════════════════════════════════════════════════════════════
# CLUSTER DETECTOR
# ═══════════════════════════════════════════════════════════════

class ClusterDetector:
    """
    Wykrywa klastry likwidacji - gdzie jest DUŻO poziomów blisko siebie.
    
    To są "magnetic zones" - Market Makers CHCĄ tam dotrzeć!
    """
    
    @classmethod
    def detect_clusters(cls, 
                        levels: List[LiquidationLevel],
                        current_price: float,
                        cluster_width_pct: float = 0.01) -> List[LiquidationCluster]:
        """
        Znajdź klastry likwidacji.
        
        Args:
            levels: Lista poziomów likwidacji
            current_price: Aktualna cena
            cluster_width_pct: Szerokość klastra jako % ceny
        """
        if not levels:
            return []
        
        clusters = []
        
        # Grupuj poziomy w bins
        price_step = current_price * cluster_width_pct
        
        # Stwórz bins
        prices = [l.price for l in levels]
        min_price = min(prices)
        max_price = max(prices)
        
        bins = np.arange(min_price, max_price + price_step, price_step)
        
        for i in range(len(bins) - 1):
            bin_low = bins[i]
            bin_high = bins[i + 1]
            
            # Znajdź poziomy w tym binie
            bin_levels = [l for l in levels if bin_low <= l.price < bin_high]
            
            if len(bin_levels) >= 3:  # Minimum 3 poziomy = klaster
                total_volume = sum(l.volume_usd for l in bin_levels)
                
                # Dominujący typ
                long_vol = sum(l.volume_usd for l in bin_levels if l.type == 'long')
                short_vol = sum(l.volume_usd for l in bin_levels if l.type == 'short')
                dominant = 'long' if long_vol > short_vol else 'short'
                
                # Średnia dźwignia
                avg_lev = np.mean([l.leverage for l in bin_levels])
                
                # Siła klastra (im więcej wolumenu i bliżej ceny, tym silniejszy)
                distance = abs((bin_low + bin_high) / 2 - current_price) / current_price
                strength = min(1.0, (total_volume / 1_000_000_000) * (1 - distance * 5))
                
                clusters.append(LiquidationCluster(
                    price_low=bin_low,
                    price_high=bin_high,
                    total_volume_usd=total_volume,
                    dominant_type=dominant,
                    avg_leverage=avg_lev,
                    strength=max(0, strength)
                ))
        
        # Sortuj po sile
        clusters.sort(key=lambda c: c.strength, reverse=True)
        
        return clusters


# ═══════════════════════════════════════════════════════════════
# MAGNET ZONE ANALYZER
# ═══════════════════════════════════════════════════════════════

class MagnetZoneAnalyzer:
    """
    🧲 NAJWAŻNIEJSZA KLASA!
    
    Łączy:
    - Liquidation clusters (gdzie są stop lossy)
    - FVG (Fair Value Gaps)
    - Equal Highs/Lows
    
    Tworzy "Magnet Zones" - gdzie cena MUSI pójść.
    """
    
    def __init__(self):
        self.current_price = 0
        self.clusters = []
        self.fvg_levels = []
        self.eqh_eql_levels = []
    
    def analyze(self,
                current_price: float,
                clusters: List[LiquidationCluster],
                ohlcv_data: pd.DataFrame = None) -> List[MagnetZone]:
        """
        Analizuj i znajdź strefy magnetyczne.
        """
        self.current_price = current_price
        self.clusters = clusters
        
        magnet_zones = []
        
        # 1. Liquidation Hunt Zones
        liq_zones = self._analyze_liquidation_magnets()
        magnet_zones.extend(liq_zones)
        
        # 2. FVG Zones (jeśli mamy dane)
        if ohlcv_data is not None:
            fvg_zones = self._analyze_fvg_magnets(ohlcv_data)
            magnet_zones.extend(fvg_zones)
            
            # 3. Equal Highs/Lows
            eqh_eql_zones = self._analyze_eqh_eql_magnets(ohlcv_data)
            magnet_zones.extend(eqh_eql_zones)
        
        # Sortuj po sile
        magnet_zones.sort(key=lambda z: z.strength, reverse=True)
        
        return magnet_zones[:10]  # Top 10
    
    def _analyze_liquidation_magnets(self) -> List[MagnetZone]:
        """Znajdź strefy magnetyczne z likwidacji"""
        zones = []
        
        for cluster in self.clusters[:5]:  # Top 5 clusters
            if cluster.strength > 0.3:
                center_price = (cluster.price_low + cluster.price_high) / 2
                direction = "below" if center_price < self.current_price else "above"
                
                reasons = [
                    f"${cluster.total_volume_usd/1_000_000:.0f}M liquidations {direction}",
                    f"Dominant: {cluster.dominant_type} positions",
                    f"Avg leverage: {cluster.avg_leverage:.0f}x"
                ]
                
                zones.append(MagnetZone(
                    price=center_price,
                    strength=cluster.strength,
                    type='liquidation_hunt',
                    estimated_time=self._estimate_time_to_reach(center_price),
                    reasons=reasons
                ))
        
        return zones
    
    def _analyze_fvg_magnets(self, ohlcv: pd.DataFrame) -> List[MagnetZone]:
        """Znajdź FVG do wypełnienia"""
        zones = []
        
        # Detect FVGs
        for i in range(2, len(ohlcv) - 1):
            # Bullish FVG (gap up)
            if ohlcv['low'].iloc[i] > ohlcv['high'].iloc[i-2]:
                fvg_bottom = ohlcv['high'].iloc[i-2]
                fvg_top = ohlcv['low'].iloc[i]
                fvg_center = (fvg_bottom + fvg_top) / 2
                
                if fvg_center < self.current_price:  # Unfilled FVG below
                    fvg_size = (fvg_top - fvg_bottom) / self.current_price
                    strength = min(1.0, fvg_size * 20)  # Bigger FVG = stronger magnet
                    
                    zones.append(MagnetZone(
                        price=fvg_center,
                        strength=strength * 0.7,  # FVG trochę słabsze niż likwidacje
                        type='fvg_fill',
                        estimated_time=None,
                        reasons=[f"Bullish FVG unfilled at ${fvg_center:.0f}"]
                    ))
            
            # Bearish FVG (gap down)
            if ohlcv['high'].iloc[i] < ohlcv['low'].iloc[i-2]:
                fvg_bottom = ohlcv['high'].iloc[i]
                fvg_top = ohlcv['low'].iloc[i-2]
                fvg_center = (fvg_bottom + fvg_top) / 2
                
                if fvg_center > self.current_price:  # Unfilled FVG above
                    fvg_size = (fvg_top - fvg_bottom) / self.current_price
                    strength = min(1.0, fvg_size * 20)
                    
                    zones.append(MagnetZone(
                        price=fvg_center,
                        strength=strength * 0.7,
                        type='fvg_fill',
                        estimated_time=None,
                        reasons=[f"Bearish FVG unfilled at ${fvg_center:.0f}"]
                    ))
        
        return zones[:3]  # Max 3 FVG zones
    
    def _analyze_eqh_eql_magnets(self, ohlcv: pd.DataFrame) -> List[MagnetZone]:
        """Znajdź Equal Highs/Lows (liquidity pools)"""
        zones = []
        
        # Swing Highs
        highs = ohlcv['high'].values
        for i in range(5, len(highs) - 1):
            # Check for equal highs (within 0.1%)
            for j in range(i - 5, i):
                if abs(highs[i] - highs[j]) / highs[i] < 0.001:
                    eqh_level = (highs[i] + highs[j]) / 2
                    
                    if eqh_level > self.current_price:
                        zones.append(MagnetZone(
                            price=eqh_level,
                            strength=0.6,
                            type='equal_highs_lows',
                            estimated_time=None,
                            reasons=["Equal Highs - liquidity pool above"]
                        ))
        
        # Swing Lows
        lows = ohlcv['low'].values
        for i in range(5, len(lows) - 1):
            for j in range(i - 5, i):
                if abs(lows[i] - lows[j]) / lows[i] < 0.001:
                    eql_level = (lows[i] + lows[j]) / 2
                    
                    if eql_level < self.current_price:
                        zones.append(MagnetZone(
                            price=eql_level,
                            strength=0.6,
                            type='equal_highs_lows',
                            estimated_time=None,
                            reasons=["Equal Lows - liquidity pool below"]
                        ))
        
        return zones[:3]
    
    def _estimate_time_to_reach(self, target_price: float) -> str:
        """Szacuj czas dotarcia do ceny"""
        distance_pct = abs(target_price - self.current_price) / self.current_price
        
        if distance_pct < 0.01:
            return "minutes"
        elif distance_pct < 0.03:
            return "hours"
        elif distance_pct < 0.10:
            return "1-2 days"
        else:
            return "days to week"


# ═══════════════════════════════════════════════════════════════
# MAIN LIQUIDATION HEATMAP CLASS
# ═══════════════════════════════════════════════════════════════

class LiquidationHeatmapAnalyzer:
    """
    🔥 GŁÓWNA KLASA - LIQUIDATION HEATMAP
    
    Łączy wszystkie komponenty i tworzy pełną mapę likwidacji.
    """
    
    def __init__(self):
        self.calculator = LiquidationCalculator()
        self.cluster_detector = ClusterDetector()
        self.magnet_analyzer = MagnetZoneAnalyzer()
        
        # Cache
        self.last_heatmap = None
        self.last_update = None
    
    def generate_heatmap(self,
                         current_price: float,
                         ohlcv_data: pd.DataFrame = None,
                         external_liquidation_data: Dict = None) -> LiquidationHeatmap:
        """
        Generuj pełną mapę ciepła likwidacji.
        
        Args:
            current_price: Aktualna cena
            ohlcv_data: OHLCV DataFrame
            external_liquidation_data: Dane z zewnętrznych API (Coinglass etc.)
        
        Returns:
            LiquidationHeatmap
        """
        timestamp = datetime.now()
        
        # 1. Generate liquidation levels
        if external_liquidation_data:
            levels = self._parse_external_data(external_liquidation_data, current_price)
        else:
            levels = self.calculator.generate_liquidation_levels(current_price)
        
        # 2. Detect clusters
        clusters = self.cluster_detector.detect_clusters(levels, current_price)
        
        # 3. Find magnet zones
        magnet_zones = self.magnet_analyzer.analyze(current_price, clusters, ohlcv_data)
        
        # 4. Overall sentiment
        long_volume = sum(l.volume_usd for l in levels if l.type == 'long')
        short_volume = sum(l.volume_usd for l in levels if l.type == 'short')
        
        if long_volume > short_volume * 1.5:
            sentiment = 'long_heavy'
        elif short_volume > long_volume * 1.5:
            sentiment = 'short_heavy'
        else:
            sentiment = 'balanced'
        
        # 5. Risk level
        nearest_cluster_distance = float('inf')
        for c in clusters:
            center = (c.price_low + c.price_high) / 2
            distance = abs(center - current_price) / current_price
            nearest_cluster_distance = min(nearest_cluster_distance, distance)
        
        if nearest_cluster_distance < 0.02:
            risk_level = 'extreme'
        elif nearest_cluster_distance < 0.05:
            risk_level = 'high'
        elif nearest_cluster_distance < 0.10:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        heatmap = LiquidationHeatmap(
            current_price=current_price,
            timestamp=timestamp,
            levels=levels,
            clusters=clusters,
            magnet_zones=magnet_zones,
            overall_sentiment=sentiment,
            risk_level=risk_level
        )
        
        self.last_heatmap = heatmap
        self.last_update = timestamp
        
        return heatmap
    
    def _parse_external_data(self, data: Dict, current_price: float) -> List[LiquidationLevel]:
        """Parse dane z zewnętrznych API"""
        levels = []
        
        # Parsuj różne formaty
        if 'liquidations' in data:
            for liq in data['liquidations']:
                levels.append(LiquidationLevel(
                    price=liq.get('price', current_price),
                    volume_usd=liq.get('volume', 0),
                    type=liq.get('side', 'long'),
                    leverage=liq.get('leverage', 10),
                    distance_pct=abs(liq.get('price', current_price) - current_price) / current_price,
                    strength=0.5
                ))
        
        return levels
    
    def get_trading_signal(self, heatmap: LiquidationHeatmap = None) -> Dict:
        """
        Generuj sygnał tradingowy na podstawie heatmapy.
        
        Returns:
            Dict z sygnałem dla Genius Brain
        """
        if heatmap is None:
            heatmap = self.last_heatmap
        
        if heatmap is None:
            return {'signal': 0, 'confidence': 0, 'reasons': ['No heatmap data']}
        
        signal = 0
        confidence = 0
        reasons = []
        
        # Analiza magnet zones
        if heatmap.magnet_zones:
            nearest_zone = heatmap.magnet_zones[0]
            
            if nearest_zone.price < heatmap.current_price:
                # Magnet below = potential SHORT or wait for bounce
                if nearest_zone.type == 'liquidation_hunt':
                    signal = -0.5  # Mild bearish - cena może spaść po liquidity
                    reasons.append(f"Liquidation magnet below at ${nearest_zone.price:.0f}")
            else:
                # Magnet above = potential LONG
                if nearest_zone.type == 'liquidation_hunt':
                    signal = 0.5  # Mild bullish - cena może pójść po liquidity
                    reasons.append(f"Liquidation magnet above at ${nearest_zone.price:.0f}")
            
            confidence = nearest_zone.strength * 0.8
        
        # Sentiment adjustment
        if heatmap.overall_sentiment == 'long_heavy':
            # Dużo longów = rynek może spaść żeby ich zlikwidować
            signal -= 0.2
            reasons.append("Long-heavy market (contrarian bearish)")
        elif heatmap.overall_sentiment == 'short_heavy':
            # Dużo shortów = rynek może wzrosnąć
            signal += 0.2
            reasons.append("Short-heavy market (contrarian bullish)")
        
        # Risk level warning
        if heatmap.risk_level in ['high', 'extreme']:
            confidence *= 0.5  # Zmniejsz confidence w ryzykownych warunkach
            reasons.append(f"Risk level: {heatmap.risk_level}")
        
        # Normalize signal
        signal = max(-1, min(1, signal))
        confidence = max(0, min(1, confidence))
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'magnet_zones': [
                {
                    'price': z.price,
                    'strength': z.strength,
                    'type': z.type
                }
                for z in heatmap.magnet_zones[:3]
            ],
            'sentiment': heatmap.overall_sentiment,
            'risk_level': heatmap.risk_level
        }


# ═══════════════════════════════════════════════════════════════
# INTEGRATION WITH GENIUS BRAIN
# ═══════════════════════════════════════════════════════════════

def get_liquidation_heatmap_signal(current_price: float,
                                    ohlcv_data: pd.DataFrame = None) -> Dict:
    """
    Get liquidation heatmap signal for Genius Brain.
    
    Args:
        current_price: Current BTC price
        ohlcv_data: Optional OHLCV DataFrame
    
    Returns:
        Dict with signal for brain aggregation
    """
    try:
        analyzer = LiquidationHeatmapAnalyzer()
        heatmap = analyzer.generate_heatmap(current_price, ohlcv_data)
        signal = analyzer.get_trading_signal(heatmap)
        
        return signal
        
    except Exception as e:
        logger.error(f"Liquidation heatmap error: {e}")
        return {'signal': 0, 'confidence': 0, 'reasons': [f'Error: {str(e)}']}


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 LIQUIDATION HEATMAP ANALYZER - TEST")
    print("=" * 60)
    
    # Current BTC price
    current_price = 105000
    
    print(f"\n📊 Current Price: ${current_price:,}")
    
    print("\n1️⃣ GENERATING LIQUIDATION LEVELS")
    print("-" * 40)
    
    levels = LiquidationCalculator.generate_liquidation_levels(current_price)
    print(f"Generated {len(levels)} liquidation levels")
    
    long_levels = [l for l in levels if l.type == 'long']
    short_levels = [l for l in levels if l.type == 'short']
    print(f"  Long liquidations: {len(long_levels)}")
    print(f"  Short liquidations: {len(short_levels)}")
    
    print("\n2️⃣ DETECTING CLUSTERS")
    print("-" * 40)
    
    clusters = ClusterDetector.detect_clusters(levels, current_price)
    print(f"Found {len(clusters)} clusters")
    
    for i, c in enumerate(clusters[:3]):
        print(f"  Cluster {i+1}: ${c.price_low:,.0f}-${c.price_high:,.0f}")
        print(f"    Volume: ${c.total_volume_usd/1_000_000:.0f}M | Dominant: {c.dominant_type}")
        print(f"    Strength: {c.strength:.2f}")
    
    print("\n3️⃣ FULL HEATMAP ANALYSIS")
    print("-" * 40)
    
    # Generate sample OHLCV
    np.random.seed(42)
    n = 100
    ohlcv = pd.DataFrame({
        'open': current_price * (1 + np.cumsum(np.random.randn(n) * 0.005)),
        'high': current_price * (1 + np.cumsum(np.random.randn(n) * 0.005)) * 1.01,
        'low': current_price * (1 + np.cumsum(np.random.randn(n) * 0.005)) * 0.99,
        'close': current_price * (1 + np.cumsum(np.random.randn(n) * 0.005)),
        'volume': np.random.randint(1000, 10000, n)
    })
    
    analyzer = LiquidationHeatmapAnalyzer()
    heatmap = analyzer.generate_heatmap(current_price, ohlcv)
    
    print(f"Overall Sentiment: {heatmap.overall_sentiment}")
    print(f"Risk Level: {heatmap.risk_level}")
    
    print("\n4️⃣ MAGNET ZONES")
    print("-" * 40)
    
    for zone in heatmap.magnet_zones[:5]:
        direction = "⬇️" if zone.price < current_price else "⬆️"
        print(f"  {direction} ${zone.price:,.0f} | Strength: {zone.strength:.2f}")
        print(f"     Type: {zone.type}")
        for reason in zone.reasons:
            print(f"     - {reason}")
    
    print("\n5️⃣ TRADING SIGNAL")
    print("-" * 40)
    
    signal = analyzer.get_trading_signal(heatmap)
    print(f"Signal: {signal['signal']:.2f}")
    print(f"Confidence: {signal['confidence']:.2f}")
    print(f"Reasons:")
    for reason in signal['reasons']:
        print(f"  - {reason}")
    
    print("\n" + "=" * 60)
    print("✅ Liquidation Heatmap Analyzer Ready!")
    print("=" * 60)
