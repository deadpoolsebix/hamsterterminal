#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CVD (Cumulative Volume Delta) Filtering
Wygładzanie danych CVD dla czystości sygnałów
"""

import numpy as np
import pandas as pd
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CVDFilter:
    """
    Filtrowanie CVD dla eliminacji szumu HFT
    
    Problem: Dane z orderbooka mogą być "zaśmiecone" przez algorytmy HFT giełd.
    Rozwiązanie: Wielowarstwowe filtrowanie
    """
    
    def __init__(
        self,
        smoothing_window: int = 14,
        outlier_threshold: float = 3.0,
        momentum_period: int = 20
    ):
        """
        Parameters:
        - smoothing_window: Okno EMA dla CVD (domyślnie 14)
        - outlier_threshold: Threshold dla outlier detection (std devs)
        - momentum_period: Period dla momentum verification
        """
        self.smoothing_window = smoothing_window
        self.outlier_threshold = outlier_threshold
        self.momentum_period = momentum_period
        
        logger.info(f"CVD Filter initialized with window={smoothing_window}")
    
    def calculate_raw_cvd(self, df: pd.DataFrame) -> pd.Series:
        """
        Oblicz raw CVD (bez filtrowania)
        
        CVD = (Buy Volume - Sell Volume) cumsum
        """
        if 'buy_volume' not in df.columns or 'sell_volume' not in df.columns:
            # Proxy: jeśli close > open to buy_volume, else sell_volume
            volume_delta = df['volume'] * np.where(
                df['close'] > df['open'],
                1,
                -1
            )
        else:
            volume_delta = df['buy_volume'] - df['sell_volume']
        
        cvd_raw = volume_delta.cumsum()
        return cvd_raw
    
    def detect_outliers(self, series: pd.Series, threshold: float = 3.0) -> pd.Series:
        """
        Detektuj outliers używając Z-score
        """
        z_scores = np.abs((series - series.mean()) / series.std())
        outliers = z_scores > threshold
        
        if outliers.sum() > 0:
            logger.warning(f"⚠️ Detected {outliers.sum()} outliers in CVD")
        
        return outliers
    
    def smooth_cvd_ema(
        self,
        cvd_raw: pd.Series,
        span: int = None
    ) -> pd.Series:
        """
        Wygładź CVD przy użyciu EMA
        """
        if span is None:
            span = self.smoothing_window
        
        cvd_ema = cvd_raw.ewm(span=span, adjust=False).mean()
        return cvd_ema
    
    def smooth_cvd_sma(
        self,
        cvd_raw: pd.Series,
        window: int = None
    ) -> pd.Series:
        """
        Wygładź CVD przy użyciu SMA
        """
        if window is None:
            window = self.smoothing_window
        
        cvd_sma = cvd_raw.rolling(window=window).mean()
        return cvd_sma
    
    def apply_median_filter(
        self,
        series: pd.Series,
        kernel_size: int = 5
    ) -> pd.Series:
        """
        Zastosuj Median filter dla outlier removal
        """
        filtered = series.rolling(
            window=kernel_size,
            center=True
        ).median()
        return filtered
    
    def filter_cvd_comprehensive(
        self,
        df: pd.DataFrame,
        method: str = 'hybrid'
    ) -> Dict:
        """
        Kompleksowe filtrowanie CVD
        
        Methods:
        - 'ema': Tylko EMA smoothing
        - 'sma': Tylko SMA smoothing
        - 'median': Tylko Median filter
        - 'hybrid': Kombinacja wszystkich (rekomendowane)
        """
        # 1. Raw CVD
        cvd_raw = self.calculate_raw_cvd(df)
        
        # 2. Detect outliers
        outliers = self.detect_outliers(cvd_raw, self.outlier_threshold)
        
        # 3. Filter based on method
        if method == 'ema':
            cvd_filtered = self.smooth_cvd_ema(cvd_raw)
        
        elif method == 'sma':
            cvd_filtered = self.smooth_cvd_sma(cvd_raw)
        
        elif method == 'median':
            cvd_filtered = self.apply_median_filter(cvd_raw)
        
        elif method == 'hybrid':
            # Hybrid: Median first → EMA → SMA
            cvd_median = self.apply_median_filter(cvd_raw, kernel_size=3)
            cvd_ema = self.smooth_cvd_ema(cvd_median, span=7)
            cvd_filtered = self.smooth_cvd_sma(cvd_ema, window=14)
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # 4. Calculate momentum
        cvd_momentum = cvd_filtered.diff()
        cvd_momentum_sma = cvd_momentum.rolling(self.momentum_period).mean()
        
        # 5. Generate signal
        cvd_signal = 0
        if cvd_momentum_sma.iloc[-1] > 0:
            cvd_signal = 1  # Bullish
        elif cvd_momentum_sma.iloc[-1] < 0:
            cvd_signal = -1  # Bearish
        
        return {
            'cvd_raw': cvd_raw,
            'cvd_filtered': cvd_filtered,
            'cvd_momentum': cvd_momentum,
            'cvd_momentum_sma': cvd_momentum_sma,
            'outliers': outliers,
            'current_signal': cvd_signal,
            'outlier_count': outliers.sum()
        }
    
    def detect_divergence(
        self,
        df: pd.DataFrame,
        cvd_filtered: pd.Series,
        lookback: int = 50
    ) -> Dict:
        """
        Detektuj divergencję cenę vs CVD
        
        Bullish divergence: Price down, CVD up (kupowanie na dip)
        Bearish divergence: Price up, CVD down (selling into strength)
        """
        recent = df.tail(lookback)
        cvd_recent = cvd_filtered.tail(lookback)
        
        # Normalize both for comparison
        price_normalized = (recent['close'] - recent['close'].min()) / (recent['close'].max() - recent['close'].min())
        cvd_normalized = (cvd_recent - cvd_recent.min()) / (cvd_recent.max() - cvd_recent.min())
        
        # Calculate divergence
        price_trend = price_normalized.iloc[-1] - price_normalized.iloc[0]
        cvd_trend = cvd_normalized.iloc[-1] - cvd_normalized.iloc[0]
        
        divergence_type = None
        strength = 0
        
        if price_trend < -0.1 and cvd_trend > 0.1:
            divergence_type = 'bullish'  # Price down, CVD up
            strength = abs(cvd_trend) - abs(price_trend)
        
        elif price_trend > 0.1 and cvd_trend < -0.1:
            divergence_type = 'bearish'  # Price up, CVD down
            strength = abs(price_trend) - abs(cvd_trend)
        
        return {
            'divergence_type': divergence_type,
            'strength': strength,
            'price_trend': price_trend,
            'cvd_trend': cvd_trend,
            'signal': 'bullish' if divergence_type == 'bullish' else ('bearish' if divergence_type == 'bearish' else 'no_divergence')
        }


def demo_cvd_filtering():
    """Demo: CVD Filtering"""
    
    print("\n" + "="*70)
    print("📊 CVD FILTERING & DIVERGENCE DETECTION")
    print("="*70)
    
    # Generate synthetic data
    print("\n📈 Generating synthetic market data...")
    np.random.seed(42)
    
    periods = 200
    dates = pd.date_range('2024-01-01', periods=periods, freq='1H')
    
    # Base trend
    base_price = 50000
    trend = np.linspace(0, 0.05, periods)  # 5% uptrend
    noise = np.random.randn(periods) * 0.01
    prices = base_price * (1 + trend + noise).cumprod()
    
    # Volume with some spikes (HFT noise)
    base_volume = np.random.uniform(100, 500, periods)
    hft_spikes = np.random.binomial(1, 0.1, periods) * np.random.uniform(1000, 2000, periods)
    volumes = base_volume + hft_spikes
    
    # Buy/Sell volume
    buy_volume = volumes * np.random.uniform(0.4, 0.6, periods)
    sell_volume = volumes - buy_volume
    
    df = pd.DataFrame({
        'open': prices * 0.999,
        'high': prices * 1.002,
        'low': prices * 0.998,
        'close': prices,
        'volume': volumes,
        'buy_volume': buy_volume,
        'sell_volume': sell_volume
    }, index=dates)
    
    # Initialize filter
    filter = CVDFilter(smoothing_window=14, outlier_threshold=3.0)
    
    # Apply filtering
    print("\n🔍 Applying CVD filters...")
    result = filter.filter_cvd_comprehensive(df, method='hybrid')
    
    # Add to dataframe
    df['cvd_raw'] = result['cvd_raw']
    df['cvd_filtered'] = result['cvd_filtered']
    df['cvd_momentum'] = result['cvd_momentum']
    df['cvd_momentum_sma'] = result['cvd_momentum_sma']
    
    # Print statistics
    print("\n" + "="*70)
    print("📊 CVD STATISTICS")
    print("="*70)
    
    print(f"\nRaw CVD:")
    print(f"  Min: {result['cvd_raw'].min():,.0f}")
    print(f"  Max: {result['cvd_raw'].max():,.0f}")
    print(f"  Current: {result['cvd_raw'].iloc[-1]:,.0f}")
    
    print(f"\nFiltered CVD:")
    print(f"  Min: {result['cvd_filtered'].min():,.0f}")
    print(f"  Max: {result['cvd_filtered'].max():,.0f}")
    print(f"  Current: {result['cvd_filtered'].iloc[-1]:,.0f}")
    
    print(f"\nOutliers detected: {result['outlier_count']}")
    print(f"Outlier %: {(result['outlier_count'] / len(df)) * 100:.1f}%")
    
    # Current signal
    signal_emoji = "📈" if result['current_signal'] == 1 else "📉" if result['current_signal'] == -1 else "⏸️"
    signal_text = "BULLISH" if result['current_signal'] == 1 else "BEARISH" if result['current_signal'] == -1 else "NEUTRAL"
    print(f"\nCurrent CVD Signal: {signal_emoji} {signal_text}")
    
    # Divergence detection
    print("\n" + "="*70)
    print("🔄 DIVERGENCE ANALYSIS")
    print("="*70)
    
    div = filter.detect_divergence(df, result['cvd_filtered'], lookback=50)
    
    if div['divergence_type']:
        print(f"\n✅ DIVERGENCE DETECTED: {div['divergence_type'].upper()}")
        print(f"   Strength: {div['strength']:.2f}")
        print(f"   Price trend: {div['price_trend']:+.2%}")
        print(f"   CVD trend: {div['cvd_trend']:+.2%}")
        
        if div['divergence_type'] == 'bullish':
            print("\n   💡 Interpretation:")
            print("      - Price fell but volume buying continued")
            print("      - Smart money accumulating at lower prices")
            print("      - Potential bounce setup")
        else:
            print("\n   💡 Interpretation:")
            print("      - Price rose but volume selling started")
            print("      - Smart money distribution into strength")
            print("      - Potential reversal setup")
    else:
        print(f"\n⏸️  No divergence (price/CVD aligned)")
    
    # Comparison
    print("\n" + "="*70)
    print("📊 RAW vs FILTERED CVD COMPARISON")
    print("="*70)
    
    recent_idx = list(range(len(df)-10, len(df)))
    comparison = pd.DataFrame({
        'Time': df.index[-10:].strftime('%H:%M'),
        'Price': df['close'].iloc[-10:].values.astype(int),
        'Raw CVD': result['cvd_raw'].iloc[-10:].values.astype(int),
        'Filtered CVD': result['cvd_filtered'].iloc[-10:].values.astype(int),
        'Momentum': result['cvd_momentum_sma'].iloc[-10:].values.astype(int)
    })
    
    print("\n" + comparison.to_string(index=False))
    
    print("\n" + "="*70)
    print("💡 KEY INSIGHTS")
    print("="*70)
    print("""
1. Raw CVD can have spikes from HFT activity
   - Median filter removes outliers
   - EMA smooths over time
   - Hybrid approach is most robust

2. CVD Divergence = Smart Money Signal
   - Price down, CVD up = Accumulation (BUY)
   - Price up, CVD down = Distribution (SELL)
   - Strength indicates conviction

3. Use filtered CVD for:
   - Trend confirmation
   - Divergence detection
   - Risk management (exit if divergence breaks)

4. Filter configuration:
   - Median kernel: 3 (removes 1-2 candle spikes)
   - EMA span: 7 (quick response)
   - SMA window: 14 (longer-term trend)
   - Momentum period: 20 (smooth confirmation)
    """)
    print("="*70)


if __name__ == "__main__":
    demo_cvd_filtering()
