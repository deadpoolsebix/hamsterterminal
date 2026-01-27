"""
📊 TIME SERIES ANALYSIS MODULE
Based on: "Successful Algorithmic Trading" by Michael Halls-Moore (QuantStart)
Chapter 10: Time Series Analysis

Features:
- Augmented Dickey-Fuller (ADF) Test for Mean Reversion
- Hurst Exponent for Trend/Mean-Reversion Detection
- Cointegrated ADF (CADF) Test for Pairs Trading
- Stationarity Testing
- Half-Life of Mean Reversion

Author: Genius Engine Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import warnings
warnings.filterwarnings('ignore')

# Statistical imports
try:
    from scipy import stats
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from statsmodels.tsa.stattools import adfuller, coint
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tsa.vector_ar.vecm import coint_johansen
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("⚠️ statsmodels not installed. Run: pip install statsmodels")

try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ADFResult:
    """Augmented Dickey-Fuller Test Result"""
    test_statistic: float
    p_value: float
    critical_values: Dict[str, float]
    is_stationary: bool
    is_mean_reverting: bool
    confidence_level: str  # '1%', '5%', '10%' or 'not significant'
    lags_used: int
    nobs: int
    
    def __repr__(self):
        status = "MEAN-REVERTING ✅" if self.is_mean_reverting else "TRENDING ❌"
        return f"ADF({status}): stat={self.test_statistic:.4f}, p={self.p_value:.4f}, conf={self.confidence_level}"


@dataclass
class HurstResult:
    """Hurst Exponent Result"""
    hurst_exponent: float
    regime: str  # 'mean_reverting', 'random_walk', 'trending'
    confidence: float
    r_squared: float
    
    def __repr__(self):
        return f"Hurst(H={self.hurst_exponent:.3f}): {self.regime.upper()}"


@dataclass
class CointegrationResult:
    """Cointegration Test Result"""
    test_statistic: float
    p_value: float
    critical_values: Dict[str, float]
    is_cointegrated: bool
    hedge_ratio: float
    spread_mean: float
    spread_std: float
    half_life: float
    confidence_level: str
    
    def __repr__(self):
        status = "COINTEGRATED ✅" if self.is_cointegrated else "NOT COINTEGRATED ❌"
        return f"CADF({status}): stat={self.test_statistic:.4f}, hedge={self.hedge_ratio:.4f}, half_life={self.half_life:.1f}"


@dataclass 
class TimeSeriesSignal:
    """Trading signal from time series analysis"""
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    analysis_type: str  # 'adf', 'hurst', 'cointegration'
    z_score: Optional[float]
    half_life: Optional[float]
    reasoning: str
    timestamp: datetime


# ═══════════════════════════════════════════════════════════════
# AUGMENTED DICKEY-FULLER TEST
# ═══════════════════════════════════════════════════════════════

class ADFTest:
    """
    Augmented Dickey-Fuller Test for Mean Reversion
    
    Tests if a time series is stationary (mean-reverting).
    H0: Series has a unit root (non-stationary, trending)
    H1: Series is stationary (mean-reverting)
    
    If p-value < 0.05, reject H0 → series is mean-reverting
    """
    
    @staticmethod
    def test(series: pd.Series, max_lag: Optional[int] = None, 
             regression: str = 'c') -> ADFResult:
        """
        Perform ADF test on a time series.
        
        Args:
            series: Price or return series
            max_lag: Maximum number of lags to use
            regression: 'c' (constant), 'ct' (constant+trend), 'ctt', 'nc'
        
        Returns:
            ADFResult with test statistics
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels required for ADF test")
        
        # Clean data
        series = series.dropna()
        
        if len(series) < 20:
            raise ValueError("Need at least 20 observations for ADF test")
        
        # Run ADF test
        result = adfuller(series, maxlag=max_lag, regression=regression, autolag='AIC')
        
        test_stat = result[0]
        p_value = result[1]
        lags_used = result[2]
        nobs = result[3]
        critical_values = result[4]
        
        # Determine significance level
        if test_stat < critical_values['1%']:
            confidence_level = '1%'
            is_stationary = True
        elif test_stat < critical_values['5%']:
            confidence_level = '5%'
            is_stationary = True
        elif test_stat < critical_values['10%']:
            confidence_level = '10%'
            is_stationary = True
        else:
            confidence_level = 'not significant'
            is_stationary = False
        
        return ADFResult(
            test_statistic=test_stat,
            p_value=p_value,
            critical_values=critical_values,
            is_stationary=is_stationary,
            is_mean_reverting=is_stationary,
            confidence_level=confidence_level,
            lags_used=lags_used,
            nobs=nobs
        )
    
    @staticmethod
    def test_prices(prices: pd.Series) -> ADFResult:
        """Test price series for mean reversion"""
        return ADFTest.test(prices, regression='c')
    
    @staticmethod
    def test_returns(prices: pd.Series) -> ADFResult:
        """Test returns for stationarity"""
        returns = prices.pct_change().dropna()
        return ADFTest.test(returns, regression='nc')
    
    @staticmethod
    def test_log_prices(prices: pd.Series) -> ADFResult:
        """Test log prices for mean reversion"""
        log_prices = np.log(prices)
        return ADFTest.test(log_prices, regression='c')


# ═══════════════════════════════════════════════════════════════
# HURST EXPONENT
# ═══════════════════════════════════════════════════════════════

class HurstExponent:
    """
    Hurst Exponent Calculator
    
    H < 0.5: Mean-reverting series (anti-persistent)
    H = 0.5: Random walk (geometric Brownian motion)
    H > 0.5: Trending series (persistent)
    
    The further from 0.5, the stronger the characteristic.
    """
    
    @staticmethod
    def calculate(series: pd.Series, max_lag: int = 100) -> HurstResult:
        """
        Calculate Hurst exponent using R/S analysis.
        
        Args:
            series: Price series
            max_lag: Maximum lag for analysis
        
        Returns:
            HurstResult with exponent and regime
        """
        series = series.dropna().values
        n = len(series)
        
        if n < max_lag:
            max_lag = n // 2
        
        # Ensure we have enough lags
        lags = range(2, max_lag)
        
        # Calculate R/S for each lag
        rs_values = []
        for lag in lags:
            rs = HurstExponent._rs_for_lag(series, lag)
            if rs > 0:
                rs_values.append((lag, rs))
        
        if len(rs_values) < 10:
            # Fallback: return random walk assumption
            return HurstResult(
                hurst_exponent=0.5,
                regime='random_walk',
                confidence=0.0,
                r_squared=0.0
            )
        
        # Log-log regression
        log_lags = np.log([x[0] for x in rs_values])
        log_rs = np.log([x[1] for x in rs_values])
        
        # Linear regression: log(R/S) = H * log(n) + c
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_lags, log_rs)
        
        hurst = slope
        r_squared = r_value ** 2
        
        # Determine regime
        if hurst < 0.4:
            regime = 'mean_reverting'
        elif hurst < 0.6:
            regime = 'random_walk'
        else:
            regime = 'trending'
        
        # Confidence based on distance from 0.5 and R²
        confidence = min(1.0, abs(hurst - 0.5) * 2 * r_squared)
        
        return HurstResult(
            hurst_exponent=hurst,
            regime=regime,
            confidence=confidence,
            r_squared=r_squared
        )
    
    @staticmethod
    def _rs_for_lag(series: np.ndarray, lag: int) -> float:
        """Calculate R/S statistic for a given lag"""
        # Split series into chunks
        n = len(series)
        num_chunks = n // lag
        
        if num_chunks == 0:
            return 0
        
        rs_values = []
        
        for i in range(num_chunks):
            chunk = series[i * lag:(i + 1) * lag]
            
            # Mean-adjusted series
            mean = np.mean(chunk)
            adjusted = chunk - mean
            
            # Cumulative deviations
            cumsum = np.cumsum(adjusted)
            
            # Range
            R = np.max(cumsum) - np.min(cumsum)
            
            # Standard deviation
            S = np.std(chunk, ddof=1)
            
            if S > 0:
                rs_values.append(R / S)
        
        if len(rs_values) == 0:
            return 0
        
        return np.mean(rs_values)
    
    @staticmethod
    def calculate_simplified(series: pd.Series) -> HurstResult:
        """
        Simplified Hurst calculation using variance ratio.
        Faster but less accurate.
        """
        series = series.dropna().values
        
        # Calculate variance at different lags
        lags = [2, 4, 8, 16, 32, 64]
        lags = [l for l in lags if l < len(series) // 4]
        
        if len(lags) < 3:
            return HurstResult(0.5, 'random_walk', 0.0, 0.0)
        
        log_lags = []
        log_vars = []
        
        for lag in lags:
            # Variance of lagged differences
            diff = series[lag:] - series[:-lag]
            var = np.var(diff)
            
            if var > 0:
                log_lags.append(np.log(lag))
                log_vars.append(np.log(var))
        
        if len(log_lags) < 3:
            return HurstResult(0.5, 'random_walk', 0.0, 0.0)
        
        # Regression
        slope, _, r_value, _, _ = stats.linregress(log_lags, log_vars)
        
        hurst = slope / 2
        r_squared = r_value ** 2
        
        if hurst < 0.4:
            regime = 'mean_reverting'
        elif hurst < 0.6:
            regime = 'random_walk'
        else:
            regime = 'trending'
        
        confidence = min(1.0, abs(hurst - 0.5) * 2 * r_squared)
        
        return HurstResult(hurst, regime, confidence, r_squared)


# ═══════════════════════════════════════════════════════════════
# COINTEGRATION TEST (CADF)
# ═══════════════════════════════════════════════════════════════

class CointegrationTest:
    """
    Cointegrated Augmented Dickey-Fuller (CADF) Test
    
    Tests if two price series are cointegrated (move together long-term).
    Used for pairs trading: if cointegrated, spread is mean-reverting.
    
    Process:
    1. Regress Y on X to find hedge ratio β
    2. Calculate spread: S = Y - β*X
    3. Test spread for stationarity with ADF
    """
    
    @staticmethod
    def test(series1: pd.Series, series2: pd.Series) -> CointegrationResult:
        """
        Test two series for cointegration.
        
        Args:
            series1: First price series (Y)
            series2: Second price series (X)
        
        Returns:
            CointegrationResult with hedge ratio and statistics
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels required for cointegration test")
        
        # Align series
        df = pd.DataFrame({'y': series1, 'x': series2}).dropna()
        y = df['y'].values
        x = df['x'].values
        
        if len(df) < 30:
            raise ValueError("Need at least 30 observations for cointegration test")
        
        # Step 1: OLS regression to find hedge ratio
        x_const = sm.add_constant(x)
        model = OLS(y, x_const).fit()
        hedge_ratio = model.params[1]
        
        # Step 2: Calculate spread
        spread = y - hedge_ratio * x
        spread_series = pd.Series(spread)
        
        # Step 3: ADF test on spread
        adf_result = ADFTest.test(spread_series)
        
        # Calculate spread statistics
        spread_mean = np.mean(spread)
        spread_std = np.std(spread)
        
        # Calculate half-life of mean reversion
        half_life = CointegrationTest._calculate_half_life(spread)
        
        return CointegrationResult(
            test_statistic=adf_result.test_statistic,
            p_value=adf_result.p_value,
            critical_values=adf_result.critical_values,
            is_cointegrated=adf_result.is_stationary,
            hedge_ratio=hedge_ratio,
            spread_mean=spread_mean,
            spread_std=spread_std,
            half_life=half_life,
            confidence_level=adf_result.confidence_level
        )
    
    @staticmethod
    def engle_granger_test(series1: pd.Series, series2: pd.Series) -> CointegrationResult:
        """
        Engle-Granger two-step cointegration test.
        Uses statsmodels coint function.
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels required")
        
        # Align series
        df = pd.DataFrame({'y': series1, 'x': series2}).dropna()
        y = df['y'].values
        x = df['x'].values
        
        # Run cointegration test
        score, p_value, critical_values = coint(y, x)
        
        # Calculate hedge ratio
        x_const = sm.add_constant(x)
        model = OLS(y, x_const).fit()
        hedge_ratio = model.params[1]
        
        # Calculate spread
        spread = y - hedge_ratio * x
        spread_mean = np.mean(spread)
        spread_std = np.std(spread)
        half_life = CointegrationTest._calculate_half_life(spread)
        
        # Critical values dict
        cv_dict = {
            '1%': critical_values[0],
            '5%': critical_values[1],
            '10%': critical_values[2]
        }
        
        # Determine significance
        if score < critical_values[0]:
            confidence_level = '1%'
            is_cointegrated = True
        elif score < critical_values[1]:
            confidence_level = '5%'
            is_cointegrated = True
        elif score < critical_values[2]:
            confidence_level = '10%'
            is_cointegrated = True
        else:
            confidence_level = 'not significant'
            is_cointegrated = False
        
        return CointegrationResult(
            test_statistic=score,
            p_value=p_value,
            critical_values=cv_dict,
            is_cointegrated=is_cointegrated,
            hedge_ratio=hedge_ratio,
            spread_mean=spread_mean,
            spread_std=spread_std,
            half_life=half_life,
            confidence_level=confidence_level
        )
    
    @staticmethod
    def _calculate_half_life(spread: np.ndarray) -> float:
        """
        Calculate half-life of mean reversion.
        
        Uses Ornstein-Uhlenbeck process:
        dS = θ(μ - S)dt + σdW
        
        Half-life = ln(2) / θ
        """
        spread = np.array(spread)
        
        # Lagged spread
        spread_lag = spread[:-1]
        spread_diff = spread[1:] - spread[:-1]
        
        # Regression: ΔS = θ(μ - S_lag) ≈ a + b*S_lag
        # where b = -θ
        if SKLEARN_AVAILABLE:
            model = LinearRegression()
            model.fit(spread_lag.reshape(-1, 1), spread_diff)
            theta = -model.coef_[0]
        else:
            # Simple OLS
            n = len(spread_lag)
            x_mean = np.mean(spread_lag)
            y_mean = np.mean(spread_diff)
            
            numerator = np.sum((spread_lag - x_mean) * (spread_diff - y_mean))
            denominator = np.sum((spread_lag - x_mean) ** 2)
            
            theta = -numerator / denominator if denominator != 0 else 0
        
        if theta <= 0:
            return float('inf')  # Not mean-reverting
        
        half_life = np.log(2) / theta
        
        return max(0, half_life)
    
    @staticmethod
    def johansen_test(series_list: List[pd.Series], det_order: int = 0) -> Dict:
        """
        Johansen cointegration test for multiple series.
        
        Args:
            series_list: List of price series
            det_order: Deterministic term (-1=no const, 0=const, 1=const+trend)
        
        Returns:
            Dict with test results
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels required")
        
        # Create dataframe
        df = pd.DataFrame({f'series_{i}': s for i, s in enumerate(series_list)}).dropna()
        
        # Run Johansen test
        result = coint_johansen(df, det_order, 1)
        
        return {
            'trace_stat': result.lr1,
            'trace_crit_95': result.cvt[:, 1],
            'eigen_stat': result.lr2,
            'eigen_crit_95': result.cvm[:, 1],
            'eigenvectors': result.evec,
            'eigenvalues': result.eig
        }


# ═══════════════════════════════════════════════════════════════
# Z-SCORE CALCULATOR
# ═══════════════════════════════════════════════════════════════

class ZScoreCalculator:
    """Calculate Z-score for mean reversion trading"""
    
    @staticmethod
    def calculate(series: pd.Series, lookback: int = 20) -> pd.Series:
        """
        Calculate rolling Z-score.
        
        Z = (X - μ) / σ
        
        Args:
            series: Price or spread series
            lookback: Rolling window for mean and std
        
        Returns:
            Z-score series
        """
        mean = series.rolling(window=lookback).mean()
        std = series.rolling(window=lookback).std()
        
        z_score = (series - mean) / std
        
        return z_score
    
    @staticmethod
    def calculate_static(series: pd.Series) -> pd.Series:
        """
        Calculate Z-score using full series statistics.
        """
        mean = series.mean()
        std = series.std()
        
        z_score = (series - mean) / std
        
        return z_score
    
    @staticmethod
    def get_signal(z_score: float, 
                   entry_threshold: float = 2.0,
                   exit_threshold: float = 0.5) -> str:
        """
        Generate trading signal from Z-score.
        
        Args:
            z_score: Current Z-score
            entry_threshold: Z-score for entry (e.g., 2.0)
            exit_threshold: Z-score for exit (e.g., 0.5)
        
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        if z_score < -entry_threshold:
            return 'BUY'  # Price below mean, expect reversion up
        elif z_score > entry_threshold:
            return 'SELL'  # Price above mean, expect reversion down
        elif abs(z_score) < exit_threshold:
            return 'EXIT'  # Close position, near mean
        else:
            return 'HOLD'


# ═══════════════════════════════════════════════════════════════
# MAIN ANALYZER CLASS
# ═══════════════════════════════════════════════════════════════

class TimeSeriesAnalyzer:
    """
    Complete Time Series Analyzer for Trading
    
    Combines:
    - ADF Test (mean reversion detection)
    - Hurst Exponent (regime detection)
    - Cointegration (pairs trading)
    - Z-Score (signal generation)
    """
    
    def __init__(self):
        self.adf = ADFTest()
        self.hurst = HurstExponent()
        self.coint = CointegrationTest()
        self.zscore = ZScoreCalculator()
    
    def analyze_single(self, prices: pd.Series, symbol: str = 'UNKNOWN') -> Dict[str, Any]:
        """
        Complete analysis of a single price series.
        
        Returns:
            Dict with all analysis results
        """
        results = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'n_observations': len(prices)
        }
        
        # ADF Test
        try:
            adf_result = self.adf.test_prices(prices)
            results['adf'] = adf_result
            results['is_mean_reverting'] = adf_result.is_mean_reverting
        except Exception as e:
            logger.warning(f"ADF test failed: {e}")
            results['adf'] = None
            results['is_mean_reverting'] = None
        
        # Hurst Exponent
        try:
            hurst_result = self.hurst.calculate(prices)
            results['hurst'] = hurst_result
            results['regime'] = hurst_result.regime
        except Exception as e:
            logger.warning(f"Hurst calculation failed: {e}")
            results['hurst'] = None
            results['regime'] = None
        
        # Current Z-Score
        try:
            z_scores = self.zscore.calculate(prices, lookback=20)
            current_z = z_scores.iloc[-1] if not z_scores.empty else 0
            results['z_score'] = current_z
            results['z_signal'] = self.zscore.get_signal(current_z)
        except Exception as e:
            logger.warning(f"Z-score calculation failed: {e}")
            results['z_score'] = None
            results['z_signal'] = None
        
        # Generate overall signal
        results['signal'] = self._generate_signal(results)
        
        return results
    
    def analyze_pair(self, prices1: pd.Series, prices2: pd.Series,
                     symbol1: str = 'ASSET1', symbol2: str = 'ASSET2') -> Dict[str, Any]:
        """
        Analyze a pair of assets for pairs trading.
        
        Returns:
            Dict with cointegration results and trading signals
        """
        results = {
            'pair': f"{symbol1}/{symbol2}",
            'timestamp': datetime.now()
        }
        
        # Cointegration test
        try:
            coint_result = self.coint.engle_granger_test(prices1, prices2)
            results['cointegration'] = coint_result
            results['is_cointegrated'] = coint_result.is_cointegrated
            results['hedge_ratio'] = coint_result.hedge_ratio
            results['half_life'] = coint_result.half_life
        except Exception as e:
            logger.warning(f"Cointegration test failed: {e}")
            results['cointegration'] = None
            results['is_cointegrated'] = False
            return results
        
        # Calculate spread
        spread = prices1 - coint_result.hedge_ratio * prices2
        results['spread_current'] = spread.iloc[-1]
        results['spread_mean'] = coint_result.spread_mean
        results['spread_std'] = coint_result.spread_std
        
        # Z-score of spread
        z_scores = self.zscore.calculate(spread, lookback=20)
        current_z = z_scores.iloc[-1] if not z_scores.empty else 0
        results['z_score'] = current_z
        
        # Generate pair trading signal
        if coint_result.is_cointegrated:
            results['signal'] = self._generate_pairs_signal(current_z, coint_result.half_life)
        else:
            results['signal'] = {'type': 'NO_TRADE', 'reason': 'Not cointegrated'}
        
        return results
    
    def find_cointegrated_pairs(self, prices_dict: Dict[str, pd.Series],
                                 p_value_threshold: float = 0.05) -> List[Dict]:
        """
        Find all cointegrated pairs from a dict of price series.
        
        Args:
            prices_dict: Dict of symbol -> price series
            p_value_threshold: Maximum p-value for cointegration
        
        Returns:
            List of cointegrated pairs with statistics
        """
        symbols = list(prices_dict.keys())
        cointegrated_pairs = []
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                sym1, sym2 = symbols[i], symbols[j]
                
                try:
                    result = self.analyze_pair(
                        prices_dict[sym1], 
                        prices_dict[sym2],
                        sym1, sym2
                    )
                    
                    if result.get('is_cointegrated'):
                        coint = result['cointegration']
                        cointegrated_pairs.append({
                            'pair': f"{sym1}/{sym2}",
                            'symbol1': sym1,
                            'symbol2': sym2,
                            'p_value': coint.p_value,
                            'hedge_ratio': coint.hedge_ratio,
                            'half_life': coint.half_life,
                            'z_score': result.get('z_score', 0)
                        })
                except Exception as e:
                    logger.debug(f"Error testing {sym1}/{sym2}: {e}")
                    continue
        
        # Sort by p-value (most significant first)
        cointegrated_pairs.sort(key=lambda x: x['p_value'])
        
        return cointegrated_pairs
    
    def _generate_signal(self, analysis: Dict) -> Dict:
        """Generate trading signal from single asset analysis"""
        signal = {
            'type': 'HOLD',
            'confidence': 0.0,
            'reasons': []
        }
        
        # Check if mean-reverting
        if analysis.get('is_mean_reverting'):
            signal['reasons'].append('ADF: Mean-reverting confirmed')
            
            # Use Z-score for direction
            z = analysis.get('z_score', 0)
            if z and abs(z) > 2:
                if z < -2:
                    signal['type'] = 'BUY'
                    signal['reasons'].append(f'Z-score: {z:.2f} (oversold)')
                elif z > 2:
                    signal['type'] = 'SELL'
                    signal['reasons'].append(f'Z-score: {z:.2f} (overbought)')
                signal['confidence'] = min(1.0, abs(z) / 3)
        
        # Check Hurst
        hurst = analysis.get('hurst')
        if hurst:
            if hurst.regime == 'mean_reverting':
                signal['reasons'].append(f'Hurst: {hurst.hurst_exponent:.2f} (mean-reverting)')
                signal['confidence'] = max(signal['confidence'], hurst.confidence)
            elif hurst.regime == 'trending':
                signal['reasons'].append(f'Hurst: {hurst.hurst_exponent:.2f} (trending)')
                # Could flip signal for trend-following
        
        return signal
    
    def _generate_pairs_signal(self, z_score: float, half_life: float) -> Dict:
        """Generate pairs trading signal"""
        signal = {
            'type': 'HOLD',
            'confidence': 0.0,
            'z_score': z_score,
            'half_life': half_life,
            'reasons': []
        }
        
        # Entry signals
        if z_score < -2:
            signal['type'] = 'LONG_SPREAD'  # Buy Y, Sell X
            signal['reasons'].append(f'Z-score {z_score:.2f} < -2: Spread undervalued')
            signal['confidence'] = min(1.0, abs(z_score) / 3)
        elif z_score > 2:
            signal['type'] = 'SHORT_SPREAD'  # Sell Y, Buy X
            signal['reasons'].append(f'Z-score {z_score:.2f} > 2: Spread overvalued')
            signal['confidence'] = min(1.0, abs(z_score) / 3)
        elif abs(z_score) < 0.5:
            signal['type'] = 'EXIT'
            signal['reasons'].append(f'Z-score {z_score:.2f} near 0: Close position')
        
        # Adjust confidence by half-life
        if half_life < 5:
            signal['confidence'] *= 1.2  # Fast reversion = higher confidence
            signal['reasons'].append(f'Half-life {half_life:.1f} days: Fast reversion')
        elif half_life > 30:
            signal['confidence'] *= 0.7  # Slow reversion = lower confidence
            signal['reasons'].append(f'Half-life {half_life:.1f} days: Slow reversion')
        
        signal['confidence'] = min(1.0, signal['confidence'])
        
        return signal


# ═══════════════════════════════════════════════════════════════
# INTEGRATION WITH GENIUS ENGINE
# ═══════════════════════════════════════════════════════════════

def get_time_series_confluence(prices: pd.Series) -> Tuple[float, List[str]]:
    """
    Get time series analysis as confluence factor for Genius Engine.
    
    Returns:
        (score, reasons) where score is -1 to 1
    """
    analyzer = TimeSeriesAnalyzer()
    analysis = analyzer.analyze_single(prices)
    
    score = 0.0
    reasons = []
    
    # ADF contribution
    if analysis.get('is_mean_reverting'):
        adf = analysis['adf']
        if adf.confidence_level == '1%':
            score += 0.3
        elif adf.confidence_level == '5%':
            score += 0.2
        else:
            score += 0.1
        reasons.append(f"ADF: Mean-reverting ({adf.confidence_level})")
    
    # Hurst contribution
    hurst = analysis.get('hurst')
    if hurst:
        if hurst.regime == 'mean_reverting':
            score += 0.2 * hurst.confidence
            reasons.append(f"Hurst: {hurst.hurst_exponent:.2f} (MR)")
        elif hurst.regime == 'trending':
            score -= 0.1 * hurst.confidence
            reasons.append(f"Hurst: {hurst.hurst_exponent:.2f} (Trend)")
    
    # Z-score contribution
    z = analysis.get('z_score', 0)
    if z and abs(z) > 1.5:
        z_contrib = min(0.3, abs(z) / 10)
        if z < 0:
            score += z_contrib  # Bullish
            reasons.append(f"Z-score: {z:.2f} (Oversold)")
        else:
            score -= z_contrib  # Bearish
            reasons.append(f"Z-score: {z:.2f} (Overbought)")
    
    return (max(-1, min(1, score)), reasons)


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("📊 TIME SERIES ANALYSIS MODULE - TEST")
    print("=" * 60)
    
    # Generate sample data
    np.random.seed(42)
    n = 500
    
    # Mean-reverting series (Ornstein-Uhlenbeck)
    theta = 0.1
    mu = 100
    sigma = 2
    mr_series = [mu]
    for _ in range(n - 1):
        dx = theta * (mu - mr_series[-1]) + sigma * np.random.randn()
        mr_series.append(mr_series[-1] + dx)
    mr_series = pd.Series(mr_series)
    
    # Trending series (random walk with drift)
    trend_series = pd.Series(np.cumsum(np.random.randn(n) + 0.1) + 100)
    
    # Cointegrated pair
    x = pd.Series(np.cumsum(np.random.randn(n)) + 100)
    y = 2 * x + np.random.randn(n) * 2 + 50  # y = 2x + noise
    
    analyzer = TimeSeriesAnalyzer()
    
    print("\n1️⃣ MEAN-REVERTING SERIES TEST")
    print("-" * 40)
    result = analyzer.analyze_single(mr_series, 'MR_SERIES')
    print(f"ADF: {result['adf']}")
    print(f"Hurst: {result['hurst']}")
    print(f"Z-Score: {result.get('z_score', 'N/A'):.2f}")
    print(f"Signal: {result['signal']}")
    
    print("\n2️⃣ TRENDING SERIES TEST")
    print("-" * 40)
    result = analyzer.analyze_single(trend_series, 'TREND_SERIES')
    print(f"ADF: {result['adf']}")
    print(f"Hurst: {result['hurst']}")
    print(f"Signal: {result['signal']}")
    
    print("\n3️⃣ COINTEGRATION TEST")
    print("-" * 40)
    result = analyzer.analyze_pair(y, x, 'Y', 'X')
    print(f"Cointegration: {result['cointegration']}")
    print(f"Hedge Ratio: {result.get('hedge_ratio', 'N/A'):.4f}")
    print(f"Half-Life: {result.get('half_life', 'N/A'):.1f} periods")
    print(f"Z-Score: {result.get('z_score', 'N/A'):.2f}")
    print(f"Signal: {result['signal']}")
    
    print("\n4️⃣ GENIUS ENGINE INTEGRATION")
    print("-" * 40)
    score, reasons = get_time_series_confluence(mr_series)
    print(f"Confluence Score: {score:.2f}")
    print(f"Reasons: {reasons}")
    
    print("\n" + "=" * 60)
    print("✅ Time Series Analysis Module Ready!")
    print("=" * 60)
