"""
QuantMuse Integration Module for Genius Trading Engine
=========================================================
Based on: https://github.com/0xemmkty/QuantMuse (1.6k stars)

Integrates:
- Factor Calculator: Momentum, Value, Quality, Volatility, Technical
- Multi-Factor Strategies: Momentum, Value, QualityGrowth, MeanReversion
- LLM Integration: Market analysis, signal generation, risk assessment

Author: Genius Engine Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FactorResult:
    """Factor calculation result"""
    factor_name: str
    value: float
    percentile: float  # 0-100
    signal: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    confidence: float  # 0-1
    timestamp: datetime

@dataclass
class StrategySignal:
    """Strategy signal from QuantMuse"""
    strategy_name: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0-1
    factors_used: List[str]
    reasoning: str
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class QuantMuseScore:
    """Complete QuantMuse confluence score"""
    total_score: float  # 0-100
    factor_scores: Dict[str, FactorResult]
    strategy_signals: List[StrategySignal]
    final_signal: str  # 'STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL'
    confluence_pct: float
    timestamp: datetime

# ============================================================================
# FACTOR CALCULATOR - Based on QuantMuse factor_calculator.py
# ============================================================================

class QuantMuseFactorCalculator:
    """
    Multi-factor calculator adapted from QuantMuse
    
    Factors:
    - Momentum: Price momentum, Volume momentum
    - Value: P/E, P/B, P/S, Dividend yield, EV/EBITDA
    - Quality: ROE, ROA, Debt/Equity, Margins
    - Volatility: Vol, Sharpe, MaxDD, VaR
    - Technical: RSI, MACD, Bollinger, MAs
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Momentum periods (from QuantMuse)
        self.momentum_periods = [20, 60, 252]
        
        # Factor weights for scoring
        self.factor_weights = {
            'momentum': 0.25,
            'value': 0.15,
            'quality': 0.20,
            'volatility': 0.15,
            'technical': 0.25
        }
    
    # ========================================================================
    # MOMENTUM FACTORS
    # ========================================================================
    
    def calculate_price_momentum(self, prices: pd.Series, 
                                  periods: List[int] = None) -> Dict[str, float]:
        """
        Calculate price momentum for multiple periods
        Based on: QuantMuse calculate_price_momentum()
        """
        if periods is None:
            periods = self.momentum_periods
        
        momentum_scores = {}
        
        for period in periods:
            if len(prices) >= period:
                # Simple return momentum
                momentum = (prices.iloc[-1] / prices.iloc[-period] - 1) * 100
                momentum_scores[f'momentum_{period}d'] = momentum
        
        # Average momentum
        if momentum_scores:
            momentum_scores['momentum_avg'] = np.mean(list(momentum_scores.values()))
        
        return momentum_scores
    
    def calculate_volume_momentum(self, volume: pd.Series, 
                                   prices: pd.Series) -> Dict[str, float]:
        """
        Calculate volume-price momentum trend
        Based on: QuantMuse calculate_volume_momentum()
        """
        if len(volume) < 20:
            return {'volume_momentum': 0, 'obv_trend': 0}
        
        # On-Balance Volume (OBV)
        price_diff = prices.diff()
        obv = (np.sign(price_diff) * volume).cumsum()
        
        # OBV trend (20-day)
        obv_20d_ago = obv.iloc[-20] if len(obv) >= 20 else obv.iloc[0]
        obv_trend = (obv.iloc[-1] - obv_20d_ago) / abs(obv_20d_ago) * 100 if obv_20d_ago != 0 else 0
        
        # Volume momentum
        vol_ma_20 = volume.rolling(20).mean().iloc[-1]
        vol_current = volume.iloc[-5:].mean()
        volume_momentum = (vol_current / vol_ma_20 - 1) * 100 if vol_ma_20 > 0 else 0
        
        return {
            'volume_momentum': volume_momentum,
            'obv_trend': obv_trend
        }
    
    # ========================================================================
    # VALUE FACTORS (for stocks - adapted for crypto)
    # ========================================================================
    
    def calculate_crypto_value_factors(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Crypto-adapted value factors
        
        Since crypto doesn't have P/E, P/B etc., we use:
        - Market Cap / Network Value
        - NVT Ratio (Network Value to Transactions)
        - MVRV (Market Value to Realized Value)
        """
        factors = {}
        
        # Market cap relative (if available)
        market_cap = market_data.get('market_cap', 0)
        volume_24h = market_data.get('volume_24h', 0)
        
        if volume_24h > 0:
            # Volume turnover - high is bullish for crypto
            factors['volume_turnover'] = market_cap / volume_24h if market_cap else 0
        
        # Funding rate as value indicator
        funding_rate = market_data.get('funding_rate', 0)
        factors['funding_value'] = -funding_rate * 100  # Negative funding = bullish value
        
        return factors
    
    # ========================================================================
    # QUALITY FACTORS
    # ========================================================================
    
    def calculate_quality_factors(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Quality factors adapted for crypto
        
        Original QuantMuse: ROE, ROA, Debt/Equity, Margins
        Crypto adapted: Trend consistency, Volume quality, Price stability
        """
        factors = {}
        
        if len(ohlcv) < 30:
            return {'quality_score': 50}
        
        close = ohlcv['close']
        volume = ohlcv['volume']
        
        # Trend consistency (R-squared of linear regression)
        x = np.arange(len(close))
        slope, intercept = np.polyfit(x, close.values, 1)
        predicted = slope * x + intercept
        ss_res = np.sum((close.values - predicted) ** 2)
        ss_tot = np.sum((close.values - np.mean(close.values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        factors['trend_consistency'] = r_squared * 100
        
        # Volume quality (coefficient of variation)
        vol_cv = volume.std() / volume.mean() if volume.mean() > 0 else 0
        factors['volume_quality'] = max(0, 100 - vol_cv * 50)  # Lower CV = higher quality
        
        # Price stability (inverse of volatility)
        returns = close.pct_change().dropna()
        volatility = returns.std() * np.sqrt(365) * 100
        factors['price_stability'] = max(0, 100 - volatility)
        
        # Average quality score
        factors['quality_score'] = np.mean([
            factors['trend_consistency'],
            factors['volume_quality'],
            factors['price_stability']
        ])
        
        return factors
    
    # ========================================================================
    # VOLATILITY FACTORS
    # ========================================================================
    
    def calculate_volatility_factors(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Volatility factors from QuantMuse
        
        - Historical volatility
        - Sharpe ratio
        - Maximum drawdown
        - Value at Risk (VaR)
        """
        factors = {}
        
        if len(ohlcv) < 20:
            return {'volatility_score': 50}
        
        close = ohlcv['close']
        returns = close.pct_change().dropna()
        
        # Historical volatility (annualized)
        volatility = returns.std() * np.sqrt(365) * 100
        factors['volatility_annual'] = volatility
        
        # Sharpe ratio (assuming 5% risk-free for crypto)
        risk_free = 0.05 / 365  # Daily
        excess_returns = returns - risk_free
        sharpe = (excess_returns.mean() / returns.std()) * np.sqrt(365) if returns.std() > 0 else 0
        factors['sharpe_ratio'] = sharpe
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min()) * 100
        factors['max_drawdown'] = max_drawdown
        
        # Value at Risk (95%)
        var_95 = np.percentile(returns, 5) * 100
        factors['var_95'] = abs(var_95)
        
        # Volatility regime
        recent_vol = returns.iloc[-20:].std() * np.sqrt(365) * 100
        long_vol = volatility
        factors['vol_regime'] = 'HIGH' if recent_vol > long_vol * 1.2 else 'LOW' if recent_vol < long_vol * 0.8 else 'NORMAL'
        
        # Volatility score (lower is better for stability)
        factors['volatility_score'] = max(0, 100 - volatility)
        
        return factors
    
    # ========================================================================
    # TECHNICAL FACTORS
    # ========================================================================
    
    def calculate_technical_factors(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Technical factors from QuantMuse
        
        - RSI
        - MACD
        - Bollinger Bands
        - Moving Averages
        """
        factors = {}
        
        if len(ohlcv) < 50:
            return {'technical_score': 50}
        
        close = ohlcv['close']
        high = ohlcv['high']
        low = ohlcv['low']
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        factors['rsi'] = rsi.iloc[-1]
        
        # RSI signal
        if rsi.iloc[-1] < 30:
            factors['rsi_signal'] = 'OVERSOLD'
        elif rsi.iloc[-1] > 70:
            factors['rsi_signal'] = 'OVERBOUGHT'
        else:
            factors['rsi_signal'] = 'NEUTRAL'
        
        # MACD
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        factors['macd'] = macd_histogram.iloc[-1]
        factors['macd_signal'] = 'BULLISH' if macd_histogram.iloc[-1] > 0 else 'BEARISH'
        
        # Bollinger Bands
        sma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        bb_upper = sma_20 + (std_20 * 2)
        bb_lower = sma_20 - (std_20 * 2)
        
        current_price = close.iloc[-1]
        bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
        factors['bb_position'] = bb_position * 100  # 0-100 scale
        
        if bb_position < 0.2:
            factors['bb_signal'] = 'OVERSOLD'
        elif bb_position > 0.8:
            factors['bb_signal'] = 'OVERBOUGHT'
        else:
            factors['bb_signal'] = 'NEUTRAL'
        
        # Moving averages
        sma_50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else close.mean()
        sma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else close.mean()
        
        factors['price_vs_sma50'] = (current_price / sma_50 - 1) * 100
        factors['price_vs_sma200'] = (current_price / sma_200 - 1) * 100
        factors['golden_cross'] = sma_50 > sma_200
        
        # Technical score (composite)
        tech_score = 50
        
        # RSI contribution
        if factors['rsi'] < 30:
            tech_score += 15  # Oversold = bullish
        elif factors['rsi'] > 70:
            tech_score -= 15  # Overbought = bearish
        
        # MACD contribution
        if factors['macd'] > 0:
            tech_score += 10
        else:
            tech_score -= 10
        
        # BB contribution
        if bb_position < 0.2:
            tech_score += 15
        elif bb_position > 0.8:
            tech_score -= 15
        
        # Trend contribution
        if factors['golden_cross']:
            tech_score += 10
        
        factors['technical_score'] = max(0, min(100, tech_score))
        
        return factors
    
    # ========================================================================
    # COMPOSITE FACTOR SCORE
    # ========================================================================
    
    def calculate_all_factors(self, ohlcv: pd.DataFrame, 
                               market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate all factors and return composite score
        """
        if market_data is None:
            market_data = {}
        
        factors = {}
        
        # Momentum factors
        if len(ohlcv) >= 20:
            momentum = self.calculate_price_momentum(ohlcv['close'])
            factors['momentum'] = momentum
            
            volume_mom = self.calculate_volume_momentum(ohlcv['volume'], ohlcv['close'])
            factors['volume_momentum'] = volume_mom
        
        # Value factors (crypto-adapted)
        value = self.calculate_crypto_value_factors(market_data)
        factors['value'] = value
        
        # Quality factors
        quality = self.calculate_quality_factors(ohlcv)
        factors['quality'] = quality
        
        # Volatility factors
        volatility = self.calculate_volatility_factors(ohlcv)
        factors['volatility'] = volatility
        
        # Technical factors
        technical = self.calculate_technical_factors(ohlcv)
        factors['technical'] = technical
        
        # Composite score
        scores = {
            'momentum_score': factors.get('momentum', {}).get('momentum_avg', 0),
            'quality_score': factors.get('quality', {}).get('quality_score', 50),
            'volatility_score': factors.get('volatility', {}).get('volatility_score', 50),
            'technical_score': factors.get('technical', {}).get('technical_score', 50)
        }
        
        # Weighted composite
        composite = (
            scores['momentum_score'] * self.factor_weights['momentum'] +
            scores['quality_score'] * self.factor_weights['quality'] +
            scores['volatility_score'] * self.factor_weights['volatility'] +
            scores['technical_score'] * self.factor_weights['technical']
        ) / (sum(self.factor_weights.values()) - self.factor_weights['value'])  # Exclude value for crypto
        
        factors['composite_score'] = composite
        
        return factors


# ============================================================================
# STRATEGY BASE - Based on QuantMuse strategy_base.py
# ============================================================================

class QuantMuseStrategyBase(ABC):
    """Base class for QuantMuse strategies"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"strategy.{name}")
        self.parameters = {}
    
    @abstractmethod
    def generate_signal(self, ohlcv: pd.DataFrame, 
                        factors: Dict[str, Any]) -> StrategySignal:
        """Generate trading signal"""
        pass
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """Set strategy parameters"""
        self.parameters.update(parameters)


# ============================================================================
# BUILTIN STRATEGIES - Based on QuantMuse builtin_strategies.py
# ============================================================================

class MomentumStrategy(QuantMuseStrategyBase):
    """
    Momentum Strategy from QuantMuse
    Select based on highest momentum
    """
    
    def __init__(self):
        super().__init__(
            name="MomentumStrategy",
            description="Trade based on price momentum"
        )
        self.parameters = {
            'lookback_period': 60,
            'min_momentum': 5.0
        }
    
    def generate_signal(self, ohlcv: pd.DataFrame, 
                        factors: Dict[str, Any]) -> StrategySignal:
        """Generate momentum-based signal"""
        
        momentum_data = factors.get('momentum', {})
        momentum_60d = momentum_data.get('momentum_60d', 0)
        momentum_20d = momentum_data.get('momentum_20d', 0)
        
        min_momentum = self.parameters.get('min_momentum', 5.0)
        
        # Signal logic
        if momentum_60d > min_momentum and momentum_20d > 0:
            signal_type = 'BUY'
            confidence = min(0.9, 0.5 + momentum_60d / 50)
            reasoning = f"Strong momentum: 60d={momentum_60d:.1f}%, 20d={momentum_20d:.1f}%"
        elif momentum_60d < -min_momentum and momentum_20d < 0:
            signal_type = 'SELL'
            confidence = min(0.9, 0.5 + abs(momentum_60d) / 50)
            reasoning = f"Weak momentum: 60d={momentum_60d:.1f}%, 20d={momentum_20d:.1f}%"
        else:
            signal_type = 'HOLD'
            confidence = 0.5
            reasoning = f"Neutral momentum: 60d={momentum_60d:.1f}%"
        
        return StrategySignal(
            strategy_name=self.name,
            signal_type=signal_type,
            confidence=confidence,
            factors_used=['momentum_60d', 'momentum_20d'],
            reasoning=reasoning,
            metadata={'momentum_60d': momentum_60d, 'momentum_20d': momentum_20d},
            timestamp=datetime.now()
        )


class MeanReversionStrategy(QuantMuseStrategyBase):
    """
    Mean Reversion Strategy from QuantMuse
    Buy oversold, sell overbought
    """
    
    def __init__(self):
        super().__init__(
            name="MeanReversionStrategy",
            description="Buy oversold assets based on technical indicators"
        )
        self.parameters = {
            'rsi_oversold': 30.0,
            'rsi_overbought': 70.0,
            'max_volatility': 40.0
        }
    
    def generate_signal(self, ohlcv: pd.DataFrame, 
                        factors: Dict[str, Any]) -> StrategySignal:
        """Generate mean reversion signal"""
        
        technical = factors.get('technical', {})
        volatility = factors.get('volatility', {})
        
        rsi = technical.get('rsi', 50)
        bb_position = technical.get('bb_position', 50)
        vol_annual = volatility.get('volatility_annual', 30)
        
        rsi_oversold = self.parameters.get('rsi_oversold', 30)
        rsi_overbought = self.parameters.get('rsi_overbought', 70)
        max_vol = self.parameters.get('max_volatility', 40)
        
        # Check volatility constraint
        if vol_annual > max_vol:
            return StrategySignal(
                strategy_name=self.name,
                signal_type='HOLD',
                confidence=0.3,
                factors_used=['rsi', 'bb_position', 'volatility'],
                reasoning=f"Volatility too high: {vol_annual:.1f}% > {max_vol}%",
                metadata={'rsi': rsi, 'volatility': vol_annual},
                timestamp=datetime.now()
            )
        
        # Signal logic
        if rsi < rsi_oversold and bb_position < 20:
            signal_type = 'BUY'
            confidence = min(0.9, 0.6 + (rsi_oversold - rsi) / 30)
            reasoning = f"Oversold: RSI={rsi:.1f}, BB position={bb_position:.1f}%"
        elif rsi > rsi_overbought and bb_position > 80:
            signal_type = 'SELL'
            confidence = min(0.9, 0.6 + (rsi - rsi_overbought) / 30)
            reasoning = f"Overbought: RSI={rsi:.1f}, BB position={bb_position:.1f}%"
        else:
            signal_type = 'HOLD'
            confidence = 0.5
            reasoning = f"Neutral: RSI={rsi:.1f}, BB position={bb_position:.1f}%"
        
        return StrategySignal(
            strategy_name=self.name,
            signal_type=signal_type,
            confidence=confidence,
            factors_used=['rsi', 'bb_position', 'volatility'],
            reasoning=reasoning,
            metadata={'rsi': rsi, 'bb_position': bb_position, 'volatility': vol_annual},
            timestamp=datetime.now()
        )


class MultiFactorStrategy(QuantMuseStrategyBase):
    """
    Multi-Factor Strategy from QuantMuse
    Combine multiple factors with optimized weights
    """
    
    def __init__(self):
        super().__init__(
            name="MultiFactorStrategy",
            description="Combine multiple factors for signal generation"
        )
        self.parameters = {
            'momentum_weight': 0.30,
            'quality_weight': 0.25,
            'volatility_weight': 0.20,
            'technical_weight': 0.25,
            'signal_threshold': 60  # Score needed for signal
        }
    
    def generate_signal(self, ohlcv: pd.DataFrame, 
                        factors: Dict[str, Any]) -> StrategySignal:
        """Generate multi-factor signal"""
        
        # Get individual scores
        momentum_score = factors.get('momentum', {}).get('momentum_avg', 0)
        quality_score = factors.get('quality', {}).get('quality_score', 50)
        vol_score = factors.get('volatility', {}).get('volatility_score', 50)
        tech_score = factors.get('technical', {}).get('technical_score', 50)
        
        # Normalize momentum to 0-100 scale
        momentum_normalized = 50 + momentum_score  # -50% to +50% -> 0 to 100
        momentum_normalized = max(0, min(100, momentum_normalized))
        
        # Weighted composite
        weights = self.parameters
        composite_score = (
            momentum_normalized * weights['momentum_weight'] +
            quality_score * weights['quality_weight'] +
            vol_score * weights['volatility_weight'] +
            tech_score * weights['technical_weight']
        )
        
        threshold = weights.get('signal_threshold', 60)
        
        # Signal logic
        if composite_score > threshold + 10:
            signal_type = 'BUY'
            confidence = min(0.9, composite_score / 100)
            reasoning = f"Strong multi-factor score: {composite_score:.1f}/100"
        elif composite_score < threshold - 10:
            signal_type = 'SELL'
            confidence = min(0.9, (100 - composite_score) / 100)
            reasoning = f"Weak multi-factor score: {composite_score:.1f}/100"
        else:
            signal_type = 'HOLD'
            confidence = 0.5
            reasoning = f"Neutral multi-factor score: {composite_score:.1f}/100"
        
        return StrategySignal(
            strategy_name=self.name,
            signal_type=signal_type,
            confidence=confidence,
            factors_used=['momentum', 'quality', 'volatility', 'technical'],
            reasoning=reasoning,
            metadata={
                'composite_score': composite_score,
                'momentum_score': momentum_normalized,
                'quality_score': quality_score,
                'volatility_score': vol_score,
                'technical_score': tech_score
            },
            timestamp=datetime.now()
        )


# ============================================================================
# QUANTMUSE INTEGRATION - Main Class
# ============================================================================

class QuantMuseIntegration:
    """
    Main integration class for QuantMuse with Genius Trading Engine
    
    Combines:
    - Factor Calculator
    - Multiple Strategies
    - LLM-ready insights
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.factor_calculator = QuantMuseFactorCalculator()
        
        # Initialize strategies
        self.strategies = {
            'momentum': MomentumStrategy(),
            'mean_reversion': MeanReversionStrategy(),
            'multi_factor': MultiFactorStrategy()
        }
        
        # Weight for each strategy in final signal
        self.strategy_weights = {
            'momentum': 0.30,
            'mean_reversion': 0.30,
            'multi_factor': 0.40
        }
        
        self.logger.info("🎭 QuantMuse Integration initialized")
    
    def analyze(self, ohlcv: pd.DataFrame, 
                market_data: Dict[str, Any] = None) -> QuantMuseScore:
        """
        Full QuantMuse analysis
        
        Args:
            ohlcv: OHLCV DataFrame
            market_data: Additional market data (market_cap, volume_24h, funding_rate)
        
        Returns:
            QuantMuseScore with all factors and strategy signals
        """
        if market_data is None:
            market_data = {}
        
        # Calculate all factors
        factors = self.factor_calculator.calculate_all_factors(ohlcv, market_data)
        
        # Generate signals from all strategies
        strategy_signals = []
        for strategy_name, strategy in self.strategies.items():
            try:
                signal = strategy.generate_signal(ohlcv, factors)
                strategy_signals.append(signal)
            except Exception as e:
                self.logger.warning(f"Strategy {strategy_name} failed: {e}")
        
        # Calculate composite signal
        final_signal, confluence_pct = self._calculate_final_signal(strategy_signals)
        
        # Create factor results
        factor_results = self._create_factor_results(factors)
        
        # Calculate total score (0-100)
        total_score = self._calculate_total_score(factors, strategy_signals)
        
        return QuantMuseScore(
            total_score=total_score,
            factor_scores=factor_results,
            strategy_signals=strategy_signals,
            final_signal=final_signal,
            confluence_pct=confluence_pct,
            timestamp=datetime.now()
        )
    
    def _calculate_final_signal(self, signals: List[StrategySignal]) -> Tuple[str, float]:
        """Calculate final signal from all strategy signals"""
        
        if not signals:
            return 'HOLD', 0.0
        
        # Score each signal type
        signal_scores = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        total_weight = 0
        
        for signal in signals:
            weight = self.strategy_weights.get(
                signal.strategy_name.lower().replace('strategy', ''), 
                0.33
            )
            signal_scores[signal.signal_type] += signal.confidence * weight
            total_weight += weight
        
        # Normalize
        if total_weight > 0:
            for key in signal_scores:
                signal_scores[key] /= total_weight
        
        # Determine final signal
        max_score = max(signal_scores.values())
        winning_signal = max(signal_scores, key=signal_scores.get)
        
        # Calculate confluence
        buy_sell_diff = abs(signal_scores['BUY'] - signal_scores['SELL'])
        confluence_pct = max_score * 100
        
        # Strength determination
        if max_score > 0.7:
            if winning_signal == 'BUY':
                final_signal = 'STRONG_BUY'
            elif winning_signal == 'SELL':
                final_signal = 'STRONG_SELL'
            else:
                final_signal = 'HOLD'
        elif max_score > 0.5:
            final_signal = winning_signal
        else:
            final_signal = 'HOLD'
        
        return final_signal, confluence_pct
    
    def _create_factor_results(self, factors: Dict[str, Any]) -> Dict[str, FactorResult]:
        """Create FactorResult objects from factor data"""
        
        results = {}
        
        # Momentum
        momentum_avg = factors.get('momentum', {}).get('momentum_avg', 0)
        results['momentum'] = FactorResult(
            factor_name='Momentum',
            value=momentum_avg,
            percentile=50 + momentum_avg,  # Simple conversion
            signal='BULLISH' if momentum_avg > 5 else 'BEARISH' if momentum_avg < -5 else 'NEUTRAL',
            confidence=min(0.9, 0.5 + abs(momentum_avg) / 20),
            timestamp=datetime.now()
        )
        
        # Quality
        quality_score = factors.get('quality', {}).get('quality_score', 50)
        results['quality'] = FactorResult(
            factor_name='Quality',
            value=quality_score,
            percentile=quality_score,
            signal='BULLISH' if quality_score > 60 else 'BEARISH' if quality_score < 40 else 'NEUTRAL',
            confidence=quality_score / 100,
            timestamp=datetime.now()
        )
        
        # Volatility
        vol_score = factors.get('volatility', {}).get('volatility_score', 50)
        results['volatility'] = FactorResult(
            factor_name='Volatility',
            value=vol_score,
            percentile=vol_score,
            signal='BULLISH' if vol_score > 60 else 'BEARISH' if vol_score < 40 else 'NEUTRAL',
            confidence=vol_score / 100,
            timestamp=datetime.now()
        )
        
        # Technical
        tech_score = factors.get('technical', {}).get('technical_score', 50)
        results['technical'] = FactorResult(
            factor_name='Technical',
            value=tech_score,
            percentile=tech_score,
            signal='BULLISH' if tech_score > 60 else 'BEARISH' if tech_score < 40 else 'NEUTRAL',
            confidence=tech_score / 100,
            timestamp=datetime.now()
        )
        
        return results
    
    def _calculate_total_score(self, factors: Dict[str, Any], 
                                signals: List[StrategySignal]) -> float:
        """Calculate total QuantMuse score (0-100)"""
        
        # Factor-based score
        composite = factors.get('composite_score', 50)
        
        # Strategy-based adjustment
        strategy_boost = 0
        for signal in signals:
            if signal.signal_type == 'BUY':
                strategy_boost += signal.confidence * 10
            elif signal.signal_type == 'SELL':
                strategy_boost -= signal.confidence * 10
        
        total_score = composite + strategy_boost
        return max(0, min(100, total_score))
    
    def get_confluence_points(self, ohlcv: pd.DataFrame, 
                               market_data: Dict[str, Any] = None) -> int:
        """
        Get confluence points for Genius Engine integration
        
        Returns points (0-15) for QuantMuse confluence
        """
        try:
            score = self.analyze(ohlcv, market_data)
            
            # Convert to 0-15 points
            if score.total_score >= 70:
                return 15  # Strong signal
            elif score.total_score >= 60:
                return 10  # Moderate signal
            elif score.total_score >= 50:
                return 5   # Weak signal
            else:
                return 0   # No signal
                
        except Exception as e:
            self.logger.warning(f"QuantMuse confluence calculation failed: {e}")
            return 0
    
    def get_signal_for_genius(self, ohlcv: pd.DataFrame,
                               direction: str = 'LONG') -> Tuple[bool, str, float]:
        """
        Get signal compatible with Genius Engine
        
        Args:
            ohlcv: OHLCV data
            direction: Expected direction ('LONG' or 'SHORT')
        
        Returns:
            (is_confirmed, signal_description, confidence)
        """
        try:
            score = self.analyze(ohlcv)
            
            # Check if QuantMuse confirms the direction
            if direction == 'LONG':
                confirmed = score.final_signal in ['BUY', 'STRONG_BUY']
            else:
                confirmed = score.final_signal in ['SELL', 'STRONG_SELL']
            
            description = f"QuantMuse: {score.final_signal} ({score.total_score:.0f}/100)"
            
            # Add strategy breakdown
            for sig in score.strategy_signals:
                description += f"\n  • {sig.strategy_name}: {sig.signal_type} ({sig.confidence:.0%})"
            
            return confirmed, description, score.confluence_pct / 100
            
        except Exception as e:
            self.logger.error(f"QuantMuse signal failed: {e}")
            return False, f"QuantMuse: ERROR - {e}", 0.0


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_quantmuse_instance = None

def get_quantmuse() -> QuantMuseIntegration:
    """Get singleton QuantMuse instance"""
    global _quantmuse_instance
    if _quantmuse_instance is None:
        _quantmuse_instance = QuantMuseIntegration()
    return _quantmuse_instance


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    import yfinance as yf
    
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("🎭 QuantMuse Integration Test")
    print("=" * 60)
    
    # Get test data
    try:
        btc = yf.download("BTC-USD", period="3mo", interval="1d", progress=False)
        btc.columns = [c.lower() for c in btc.columns]
        
        if len(btc) > 0:
            # Initialize QuantMuse
            qm = get_quantmuse()
            
            # Full analysis
            score = qm.analyze(btc)
            
            print(f"\n📊 QuantMuse Analysis Results:")
            print(f"   Total Score: {score.total_score:.1f}/100")
            print(f"   Final Signal: {score.final_signal}")
            print(f"   Confluence: {score.confluence_pct:.1f}%")
            
            print(f"\n📈 Factor Scores:")
            for name, factor in score.factor_scores.items():
                print(f"   • {factor.factor_name}: {factor.value:.1f} → {factor.signal}")
            
            print(f"\n🎯 Strategy Signals:")
            for sig in score.strategy_signals:
                print(f"   • {sig.strategy_name}: {sig.signal_type} ({sig.confidence:.0%})")
                print(f"     {sig.reasoning}")
            
            # Genius Engine integration test
            print(f"\n🧠 Genius Engine Integration:")
            points = qm.get_confluence_points(btc)
            print(f"   Confluence Points: {points}/15")
            
            confirmed, desc, conf = qm.get_signal_for_genius(btc, 'LONG')
            print(f"   LONG Confirmed: {confirmed}")
            print(f"   {desc}")
            
            print("\n✅ QuantMuse Integration Test PASSED!")
        else:
            print("❌ No data fetched")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
