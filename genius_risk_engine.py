"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GENIUS RISK ENGINE v1.0                                    ║
║                    Advanced Risk Management System                            ║
║                                                                              ║
║  Features:                                                                   ║
║  • Value at Risk (VaR) - Parametric, Historical, Monte Carlo                ║
║  • Conditional VaR (CVaR / Expected Shortfall)                              ║
║  • Stress Testing & Scenario Analysis                                       ║
║  • Kelly Criterion Position Sizing                                          ║
║  • Maximum Drawdown Analysis                                                ║
║  • Tail Risk Metrics (Skewness, Kurtosis)                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging


class VaRMethod(Enum):
    PARAMETRIC = "parametric"
    HISTORICAL = "historical"
    MONTE_CARLO = "monte_carlo"
    CORNISH_FISHER = "cornish_fisher"


@dataclass
class VaRResult:
    """Value at Risk calculation result"""
    var: float  # VaR value
    cvar: float  # Conditional VaR (Expected Shortfall)
    confidence: float  # Confidence level
    method: str  # Calculation method
    horizon_days: int  # Time horizon
    portfolio_value: float
    var_pct: float  # VaR as percentage
    cvar_pct: float  # CVaR as percentage
    
    def __repr__(self):
        return f"VaR({self.method}): {self.confidence:.0%} confidence, {self.horizon_days}d: ${self.var:,.2f} ({self.var_pct:.2%})"


@dataclass
class StressTestResult:
    """Stress test scenario result"""
    scenario_name: str
    return_impact: float
    portfolio_value_after: float
    loss: float
    loss_pct: float
    probability: Optional[float] = None


@dataclass
class KellyResult:
    """Kelly Criterion result"""
    kelly_fraction: float  # Full Kelly
    half_kelly: float  # Half Kelly (recommended)
    quarter_kelly: float  # Quarter Kelly (conservative)
    expected_growth: float  # Expected log growth rate
    max_loss_probability: float  # Probability of max loss


class GeniusRiskEngine:
    """
    Professional Risk Management Engine
    
    Implements institutional-grade risk metrics:
    - Multiple VaR methodologies
    - CVaR / Expected Shortfall
    - Stress Testing
    - Position Sizing (Kelly Criterion)
    - Drawdown Analysis
    """
    
    def __init__(
        self,
        returns: pd.Series = None,
        trading_days: int = 252
    ):
        """
        Initialize Risk Engine
        
        Args:
            returns: Historical returns series
            trading_days: Number of trading days per year
        """
        self.returns = returns
        self.trading_days = trading_days
        
        if returns is not None:
            self.mean = returns.mean()
            self.std = returns.std()
            self.skewness = stats.skew(returns)
            self.kurtosis = stats.kurtosis(returns)
        else:
            self.mean = 0
            self.std = 0
            self.skewness = 0
            self.kurtosis = 0
        
        self.logger = logging.getLogger('RiskEngine')
        
        # Historical scenarios for stress testing
        self.historical_scenarios = {
            'COVID Crash 2020': -0.50,
            'FTX Collapse 2022': -0.65,
            'LUNA Crash 2022': -0.80,
            'Flash Crash 2010': -0.15,
            '2008 Financial Crisis': -0.55,
            'Black Monday 1987': -0.22,
            'Dot-com Crash 2000': -0.40,
            'ETH DAO Hack 2016': -0.30,
            'China Ban 2021': -0.45,
            'Mt. Gox 2014': -0.70,
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # VALUE AT RISK (VaR)
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_var(
        self,
        portfolio_value: float,
        confidence: float = 0.95,
        horizon_days: int = 1,
        method: VaRMethod = VaRMethod.PARAMETRIC,
        n_simulations: int = 10000
    ) -> VaRResult:
        """
        Calculate Value at Risk
        
        Args:
            portfolio_value: Current portfolio value
            confidence: Confidence level (e.g., 0.95, 0.99)
            horizon_days: Time horizon in days
            method: VaR calculation method
            n_simulations: Number of Monte Carlo simulations
        """
        
        if self.returns is None or len(self.returns) == 0:
            raise ValueError("Returns data required for VaR calculation")
        
        # Scale for time horizon
        time_factor = np.sqrt(horizon_days)
        
        if method == VaRMethod.PARAMETRIC:
            var, cvar = self._var_parametric(confidence, time_factor)
        
        elif method == VaRMethod.HISTORICAL:
            var, cvar = self._var_historical(confidence, horizon_days)
        
        elif method == VaRMethod.MONTE_CARLO:
            var, cvar = self._var_monte_carlo(confidence, horizon_days, n_simulations)
        
        elif method == VaRMethod.CORNISH_FISHER:
            var, cvar = self._var_cornish_fisher(confidence, time_factor)
        
        else:
            raise ValueError(f"Unknown VaR method: {method}")
        
        # Convert to dollar amount
        var_dollar = portfolio_value * var
        cvar_dollar = portfolio_value * cvar
        
        return VaRResult(
            var=var_dollar,
            cvar=cvar_dollar,
            confidence=confidence,
            method=method.value,
            horizon_days=horizon_days,
            portfolio_value=portfolio_value,
            var_pct=var,
            cvar_pct=cvar
        )
    
    def _var_parametric(self, confidence: float, time_factor: float) -> Tuple[float, float]:
        """Parametric (Normal) VaR"""
        
        z_score = stats.norm.ppf(1 - confidence)
        
        var = -(self.mean * time_factor + z_score * self.std * time_factor)
        
        # CVaR for normal distribution
        cvar = -(self.mean * time_factor - self.std * time_factor * 
                 stats.norm.pdf(z_score) / (1 - confidence))
        
        return var, cvar
    
    def _var_historical(self, confidence: float, horizon_days: int) -> Tuple[float, float]:
        """Historical Simulation VaR"""
        
        # Calculate rolling returns for horizon
        if horizon_days > 1:
            horizon_returns = self.returns.rolling(horizon_days).sum().dropna()
        else:
            horizon_returns = self.returns
        
        var = -np.percentile(horizon_returns, (1 - confidence) * 100)
        
        # CVaR = average of returns below VaR
        tail_returns = horizon_returns[horizon_returns <= -var]
        cvar = -tail_returns.mean() if len(tail_returns) > 0 else var
        
        return var, cvar
    
    def _var_monte_carlo(
        self,
        confidence: float,
        horizon_days: int,
        n_simulations: int
    ) -> Tuple[float, float]:
        """Monte Carlo VaR"""
        
        # Simulate returns
        simulated_returns = np.random.normal(
            self.mean * horizon_days,
            self.std * np.sqrt(horizon_days),
            n_simulations
        )
        
        var = -np.percentile(simulated_returns, (1 - confidence) * 100)
        
        # CVaR
        tail_returns = simulated_returns[simulated_returns <= -var]
        cvar = -tail_returns.mean() if len(tail_returns) > 0 else var
        
        return var, cvar
    
    def _var_cornish_fisher(self, confidence: float, time_factor: float) -> Tuple[float, float]:
        """Cornish-Fisher VaR (adjusted for skewness and kurtosis)"""
        
        z = stats.norm.ppf(1 - confidence)
        S = self.skewness
        K = self.kurtosis
        
        # Cornish-Fisher expansion
        z_cf = (z + (z**2 - 1) * S / 6 +
                (z**3 - 3*z) * K / 24 -
                (2*z**3 - 5*z) * S**2 / 36)
        
        var = -(self.mean * time_factor + z_cf * self.std * time_factor)
        
        # Approximate CVaR
        cvar = var * 1.15  # Rough approximation
        
        return var, cvar
    
    def compare_var_methods(
        self,
        portfolio_value: float,
        confidence: float = 0.95,
        horizon_days: int = 1
    ) -> Dict[str, VaRResult]:
        """Compare all VaR methods"""
        
        results = {}
        
        for method in VaRMethod:
            try:
                results[method.value] = self.calculate_var(
                    portfolio_value, confidence, horizon_days, method
                )
            except Exception as e:
                self.logger.warning(f"Failed to calculate {method.value} VaR: {e}")
        
        return results
    
    # ═══════════════════════════════════════════════════════════════════════
    # STRESS TESTING
    # ═══════════════════════════════════════════════════════════════════════
    
    def stress_test(
        self,
        portfolio_value: float,
        custom_scenarios: Optional[Dict[str, float]] = None
    ) -> List[StressTestResult]:
        """
        Run stress tests against historical and custom scenarios
        
        Args:
            portfolio_value: Current portfolio value
            custom_scenarios: Custom scenarios {name: return_impact}
        """
        
        all_scenarios = {**self.historical_scenarios}
        
        if custom_scenarios:
            all_scenarios.update(custom_scenarios)
        
        results = []
        
        for name, impact in all_scenarios.items():
            loss = portfolio_value * abs(impact)
            value_after = portfolio_value + (portfolio_value * impact)
            
            results.append(StressTestResult(
                scenario_name=name,
                return_impact=impact,
                portfolio_value_after=value_after,
                loss=loss,
                loss_pct=abs(impact)
            ))
        
        # Sort by severity
        results.sort(key=lambda x: x.loss_pct, reverse=True)
        
        return results
    
    def reverse_stress_test(
        self,
        portfolio_value: float,
        loss_threshold: float,
        current_price: float,
        position_size: float
    ) -> Dict[str, Any]:
        """
        Reverse stress test: what conditions would cause threshold loss?
        
        Args:
            portfolio_value: Current portfolio value
            loss_threshold: Loss threshold in dollars
            current_price: Current asset price
            position_size: Position size
        """
        
        loss_pct = loss_threshold / portfolio_value
        
        # Price move needed
        price_move_pct = loss_pct / (position_size * current_price / portfolio_value)
        price_at_threshold = current_price * (1 - price_move_pct)
        
        # Historical probability
        if self.returns is not None:
            prob_daily = np.mean(self.returns <= -price_move_pct)
            # Approximate probability over 30 days
            prob_30d = 1 - (1 - prob_daily) ** 30
        else:
            prob_daily = 0
            prob_30d = 0
        
        return {
            'loss_threshold': loss_threshold,
            'required_price_drop_pct': price_move_pct,
            'price_at_threshold': price_at_threshold,
            'historical_probability_daily': prob_daily,
            'historical_probability_30d': prob_30d,
            'volatility_multiple': price_move_pct / (self.std if self.std > 0 else 1)
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # KELLY CRITERION
    # ═══════════════════════════════════════════════════════════════════════
    
    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> KellyResult:
        """
        Calculate Kelly Criterion for optimal position sizing
        
        Kelly f = (p * b - q) / b
        Where:
        - p = probability of winning
        - q = probability of losing (1 - p)
        - b = ratio of win to loss
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average win amount/percentage
            avg_loss: Average loss amount/percentage (positive number)
        """
        
        p = win_rate
        q = 1 - p
        b = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Kelly fraction
        if b > 0:
            kelly = (p * b - q) / b
        else:
            kelly = 0
        
        # Cap at 100%
        kelly = max(0, min(1, kelly))
        
        # Calculate expected growth rate
        if kelly > 0:
            expected_growth = p * np.log(1 + kelly * avg_win) + q * np.log(1 - kelly * avg_loss)
        else:
            expected_growth = 0
        
        # Max loss probability with full Kelly
        max_loss_prob = q  # Simplified
        
        return KellyResult(
            kelly_fraction=kelly,
            half_kelly=kelly / 2,
            quarter_kelly=kelly / 4,
            expected_growth=expected_growth,
            max_loss_probability=max_loss_prob
        )
    
    def kelly_from_returns(self) -> KellyResult:
        """Calculate Kelly from historical returns"""
        
        if self.returns is None or len(self.returns) == 0:
            raise ValueError("Returns data required")
        
        positive_returns = self.returns[self.returns > 0]
        negative_returns = self.returns[self.returns < 0]
        
        win_rate = len(positive_returns) / len(self.returns)
        avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0
        avg_loss = abs(negative_returns.mean()) if len(negative_returns) > 0 else 0
        
        return self.kelly_criterion(win_rate, avg_win, avg_loss)
    
    # ═══════════════════════════════════════════════════════════════════════
    # DRAWDOWN ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    
    def analyze_drawdowns(self, prices: pd.Series = None) -> Dict[str, Any]:
        """
        Comprehensive drawdown analysis
        
        Args:
            prices: Price series (will use cumulative returns if not provided)
        """
        
        if prices is not None:
            cumulative = prices / prices.iloc[0]
        elif self.returns is not None:
            cumulative = (1 + self.returns).cumprod()
        else:
            raise ValueError("Prices or returns required")
        
        # Running maximum
        running_max = cumulative.expanding().max()
        
        # Drawdown series
        drawdown = (cumulative - running_max) / running_max
        
        # Maximum drawdown
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # Peak before max drawdown
        peak_idx = running_max[:max_dd_idx].idxmax()
        
        # Recovery (if any)
        recovery_idx = None
        if cumulative.iloc[-1] >= running_max[max_dd_idx]:
            for idx in drawdown[max_dd_idx:].index:
                if drawdown[idx] >= 0:
                    recovery_idx = idx
                    break
        
        # All drawdown periods
        drawdown_periods = self._identify_drawdown_periods(drawdown)
        
        # Calculate Calmar ratio
        if len(self.returns) > 0:
            annual_return = self.returns.mean() * self.trading_days
            calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
        else:
            calmar = 0
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_date': max_dd_idx,
            'peak_date': peak_idx,
            'recovery_date': recovery_idx,
            'current_drawdown': drawdown.iloc[-1],
            'avg_drawdown': drawdown.mean(),
            'n_drawdown_periods': len(drawdown_periods),
            'drawdown_periods': drawdown_periods[:5],  # Top 5
            'calmar_ratio': calmar,
            'time_underwater_pct': (drawdown < 0).mean() * 100
        }
    
    def _identify_drawdown_periods(
        self,
        drawdown: pd.Series,
        threshold: float = -0.05
    ) -> List[Dict]:
        """Identify significant drawdown periods"""
        
        periods = []
        in_drawdown = False
        start_idx = None
        
        for idx, dd in drawdown.items():
            if dd <= threshold and not in_drawdown:
                in_drawdown = True
                start_idx = idx
            elif dd > threshold and in_drawdown:
                in_drawdown = False
                periods.append({
                    'start': start_idx,
                    'end': idx,
                    'max_drawdown': drawdown[start_idx:idx].min(),
                    'duration_days': (idx - start_idx).days if hasattr(idx, 'days') else None
                })
        
        # Sort by severity
        periods.sort(key=lambda x: x['max_drawdown'])
        
        return periods
    
    # ═══════════════════════════════════════════════════════════════════════
    # TAIL RISK METRICS
    # ═══════════════════════════════════════════════════════════════════════
    
    def tail_risk_metrics(self) -> Dict[str, Any]:
        """Calculate tail risk metrics"""
        
        if self.returns is None or len(self.returns) == 0:
            raise ValueError("Returns data required")
        
        # Skewness and Kurtosis
        skew = stats.skew(self.returns)
        kurt = stats.kurtosis(self.returns)
        
        # Left tail (losses)
        left_tail_5 = np.percentile(self.returns, 5)
        left_tail_1 = np.percentile(self.returns, 1)
        
        # Right tail (gains)
        right_tail_95 = np.percentile(self.returns, 95)
        right_tail_99 = np.percentile(self.returns, 99)
        
        # Tail ratio (upside/downside)
        tail_ratio = abs(right_tail_95) / abs(left_tail_5) if left_tail_5 != 0 else 0
        
        # Jarque-Bera test for normality
        jb_stat, jb_pvalue = stats.jarque_bera(self.returns)
        
        # Omega ratio
        threshold = 0
        gains = self.returns[self.returns > threshold].sum()
        losses = abs(self.returns[self.returns < threshold].sum())
        omega_ratio = gains / losses if losses > 0 else 0
        
        return {
            'skewness': skew,
            'kurtosis': kurt,
            'left_tail_5pct': left_tail_5,
            'left_tail_1pct': left_tail_1,
            'right_tail_95pct': right_tail_95,
            'right_tail_99pct': right_tail_99,
            'tail_ratio': tail_ratio,
            'jarque_bera_stat': jb_stat,
            'jarque_bera_pvalue': jb_pvalue,
            'is_normal': jb_pvalue > 0.05,
            'omega_ratio': omega_ratio
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # POSITION SIZING
    # ═══════════════════════════════════════════════════════════════════════
    
    def optimal_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss_price: float,
        method: str = 'fixed_risk',
        risk_pct: float = 1.0,
        win_rate: float = None,
        avg_win: float = None,
        avg_loss: float = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size
        
        Methods:
        - fixed_risk: Fixed percentage risk per trade
        - kelly: Kelly criterion based
        - volatility: Volatility-adjusted
        """
        
        risk_per_share = abs(entry_price - stop_loss_price)
        
        if method == 'fixed_risk':
            # Fixed percentage risk
            risk_amount = capital * (risk_pct / 100)
            position_size = risk_amount / risk_per_share
            
        elif method == 'kelly':
            if win_rate is None or avg_win is None or avg_loss is None:
                raise ValueError("Kelly method requires win_rate, avg_win, avg_loss")
            
            kelly = self.kelly_criterion(win_rate, avg_win, avg_loss)
            position_value = capital * kelly.half_kelly  # Use half Kelly
            position_size = position_value / entry_price
            
        elif method == 'volatility':
            # Target volatility-based sizing
            target_vol = risk_pct / 100
            daily_vol = self.std if self.std > 0 else 0.02
            
            position_value = capital * (target_vol / daily_vol)
            position_size = position_value / entry_price
            
        else:
            raise ValueError(f"Unknown method: {method}")
        
        position_value = position_size * entry_price
        risk_amount = position_size * risk_per_share
        
        return {
            'position_size': position_size,
            'position_value': position_value,
            'risk_amount': risk_amount,
            'risk_pct_of_capital': (risk_amount / capital) * 100,
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price,
            'method': method
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demo the risk engine"""
    
    print("=" * 70)
    print("🛡️ GENIUS RISK ENGINE v1.0 - DEMO")
    print("=" * 70)
    
    # Generate sample returns
    np.random.seed(42)
    n_days = 252 * 2
    
    # Slightly skewed returns (more negative tail)
    returns = pd.Series(
        np.random.normal(0.0005, 0.02, n_days) + 
        np.random.exponential(0.005, n_days) * np.random.choice([-1, 1], n_days, p=[0.6, 0.4])
    )
    
    risk_engine = GeniusRiskEngine(returns)
    
    portfolio_value = 100000
    
    # 1. Value at Risk
    print("\n" + "─" * 50)
    print("1️⃣ VALUE AT RISK (VaR)")
    
    var_results = risk_engine.compare_var_methods(portfolio_value, confidence=0.95)
    for method, result in var_results.items():
        print(f"   {method:20s}: VaR=${result.var:,.0f} ({result.var_pct:.2%}), CVaR=${result.cvar:,.0f}")
    
    # 2. Multi-period VaR
    print("\n" + "─" * 50)
    print("2️⃣ MULTI-PERIOD VaR (Parametric)")
    
    for days in [1, 5, 10, 30]:
        var = risk_engine.calculate_var(portfolio_value, 0.95, days, VaRMethod.PARAMETRIC)
        print(f"   {days:2d}-day: VaR=${var.var:,.0f} ({var.var_pct:.2%}), CVaR=${var.cvar:,.0f}")
    
    # 3. Stress Testing
    print("\n" + "─" * 50)
    print("3️⃣ STRESS TESTING")
    
    stress_results = risk_engine.stress_test(portfolio_value)
    for result in stress_results[:5]:  # Top 5 worst
        print(f"   {result.scenario_name:25s}: -{result.loss_pct:.0%} (${result.loss:,.0f})")
    
    # 4. Kelly Criterion
    print("\n" + "─" * 50)
    print("4️⃣ KELLY CRITERION")
    
    kelly = risk_engine.kelly_from_returns()
    print(f"   Full Kelly: {kelly.kelly_fraction:.1%}")
    print(f"   Half Kelly: {kelly.half_kelly:.1%} (Recommended)")
    print(f"   Quarter Kelly: {kelly.quarter_kelly:.1%} (Conservative)")
    print(f"   Expected Growth: {kelly.expected_growth:.4%}")
    
    # 5. Drawdown Analysis
    print("\n" + "─" * 50)
    print("5️⃣ DRAWDOWN ANALYSIS")
    
    prices = (1 + returns).cumprod() * 100
    dd_analysis = risk_engine.analyze_drawdowns(prices)
    print(f"   Max Drawdown: {dd_analysis['max_drawdown']:.1%}")
    print(f"   Current Drawdown: {dd_analysis['current_drawdown']:.1%}")
    print(f"   Avg Drawdown: {dd_analysis['avg_drawdown']:.1%}")
    print(f"   Time Underwater: {dd_analysis['time_underwater_pct']:.0f}%")
    print(f"   Calmar Ratio: {dd_analysis['calmar_ratio']:.2f}")
    
    # 6. Tail Risk Metrics
    print("\n" + "─" * 50)
    print("6️⃣ TAIL RISK METRICS")
    
    tail_metrics = risk_engine.tail_risk_metrics()
    print(f"   Skewness: {tail_metrics['skewness']:.2f} ({'negative' if tail_metrics['skewness'] < 0 else 'positive'} tail)")
    print(f"   Kurtosis: {tail_metrics['kurtosis']:.2f} ({'fat' if tail_metrics['kurtosis'] > 0 else 'thin'} tails)")
    print(f"   Left Tail (5%): {tail_metrics['left_tail_5pct']:.2%}")
    print(f"   Tail Ratio: {tail_metrics['tail_ratio']:.2f}")
    print(f"   Omega Ratio: {tail_metrics['omega_ratio']:.2f}")
    print(f"   Normal Distribution: {'Yes' if tail_metrics['is_normal'] else 'No'}")
    
    # 7. Position Sizing
    print("\n" + "─" * 50)
    print("7️⃣ POSITION SIZING")
    
    pos = risk_engine.optimal_position_size(
        capital=100000,
        entry_price=97500,
        stop_loss_price=95000,
        method='fixed_risk',
        risk_pct=1.0
    )
    print(f"   Method: {pos['method']}")
    print(f"   Position Size: {pos['position_size']:.4f} BTC")
    print(f"   Position Value: ${pos['position_value']:,.2f}")
    print(f"   Risk Amount: ${pos['risk_amount']:,.2f} ({pos['risk_pct_of_capital']:.1f}%)")
    
    # 8. Reverse Stress Test
    print("\n" + "─" * 50)
    print("8️⃣ REVERSE STRESS TEST")
    
    reverse = risk_engine.reverse_stress_test(
        portfolio_value=100000,
        loss_threshold=10000,  # $10k loss
        current_price=97500,
        position_size=0.5  # 0.5 BTC
    )
    print(f"   Loss Threshold: ${reverse['loss_threshold']:,.0f}")
    print(f"   Required Price Drop: {reverse['required_price_drop_pct']:.1%}")
    print(f"   Price at Threshold: ${reverse['price_at_threshold']:,.0f}")
    print(f"   Volatility Multiple: {reverse['volatility_multiple']:.1f}σ")
    
    print("\n" + "=" * 70)
    print("✅ Risk Engine Demo Complete!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    demo()
