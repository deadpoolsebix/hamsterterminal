"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GENIUS PORTFOLIO OPTIMIZER v1.0                            ║
║                    Professional Portfolio Management                          ║
║                                                                              ║
║  Features:                                                                   ║
║  • Mean-Variance Optimization (Markowitz)                                   ║
║  • Black-Litterman Model with Views                                         ║
║  • Risk Parity Portfolio                                                    ║
║  • Maximum Sharpe Ratio Portfolio                                           ║
║  • Minimum Volatility Portfolio                                             ║
║  • Custom Constraints (sector, asset limits)                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy import linalg
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging


@dataclass
class PortfolioResult:
    """Portfolio optimization result"""
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    method: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __repr__(self):
        return f"Portfolio({self.method}: Return={self.expected_return:.2%}, Vol={self.volatility:.2%}, Sharpe={self.sharpe_ratio:.2f})"


@dataclass
class BlackLittermanView:
    """Single view for Black-Litterman model"""
    assets: List[str]  # Assets involved
    weights: List[float]  # View weights (sum should be 0 for relative, 1 for absolute)
    expected_return: float  # Expected return
    confidence: float  # Confidence level (0-1)


class GeniusPortfolioOptimizer:
    """
    Professional Portfolio Optimizer
    
    Implements:
    - Mean-Variance Optimization (Markowitz, 1952)
    - Black-Litterman Model (Black & Litterman, 1992)
    - Risk Parity
    - Maximum Sharpe Ratio
    - Minimum Volatility
    """
    
    def __init__(
        self,
        returns: pd.DataFrame,
        risk_free_rate: float = 0.04,
        trading_days: int = 252
    ):
        """
        Initialize optimizer
        
        Args:
            returns: DataFrame of asset returns (daily)
            risk_free_rate: Annual risk-free rate
            trading_days: Number of trading days per year
        """
        self.returns = returns
        self.assets = list(returns.columns)
        self.n_assets = len(self.assets)
        self.rf = risk_free_rate
        self.trading_days = trading_days
        
        # Calculate statistics
        self.mean_returns = returns.mean() * trading_days  # Annualized
        self.cov_matrix = returns.cov() * trading_days  # Annualized
        self.corr_matrix = returns.corr()
        
        self.logger = logging.getLogger('PortfolioOptimizer')
    
    # ═══════════════════════════════════════════════════════════════════════
    # MEAN-VARIANCE OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def mean_variance_optimize(
        self,
        target_return: Optional[float] = None,
        target_volatility: Optional[float] = None,
        constraints: Optional[Dict] = None
    ) -> PortfolioResult:
        """
        Mean-Variance Optimization (Markowitz)
        
        Args:
            target_return: Target annual return
            target_volatility: Target annual volatility
            constraints: Additional constraints
        """
        
        # Default constraints - weights sum to 1, long only
        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        
        if target_return is not None:
            # Minimize volatility for given return
            cons.append({
                'type': 'eq',
                'fun': lambda x: self._portfolio_return(x) - target_return
            })
            objective = self._portfolio_volatility
        elif target_volatility is not None:
            # Maximize return for given volatility
            cons.append({
                'type': 'ineq',
                'fun': lambda x: target_volatility - self._portfolio_volatility(x)
            })
            objective = lambda x: -self._portfolio_return(x)
        else:
            # Maximize Sharpe ratio
            objective = lambda x: -self._sharpe_ratio(x)
        
        # Add custom constraints
        if constraints:
            if 'max_weight' in constraints:
                bounds = tuple((0, constraints['max_weight']) for _ in range(self.n_assets))
            if 'min_weight' in constraints:
                bounds = tuple((constraints['min_weight'], 1) for _ in range(self.n_assets))
        
        # Initial guess - equal weights
        x0 = np.array([1/self.n_assets] * self.n_assets)
        
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )
        
        weights = dict(zip(self.assets, result.x))
        
        return PortfolioResult(
            weights=weights,
            expected_return=self._portfolio_return(result.x),
            volatility=self._portfolio_volatility(result.x),
            sharpe_ratio=self._sharpe_ratio(result.x),
            method='Mean-Variance'
        )
    
    def _portfolio_return(self, weights: np.ndarray) -> float:
        """Calculate portfolio expected return"""
        return np.dot(weights, self.mean_returns)
    
    def _portfolio_volatility(self, weights: np.ndarray) -> float:
        """Calculate portfolio volatility"""
        return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
    
    def _sharpe_ratio(self, weights: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        ret = self._portfolio_return(weights)
        vol = self._portfolio_volatility(weights)
        return (ret - self.rf) / vol if vol > 0 else 0
    
    # ═══════════════════════════════════════════════════════════════════════
    # BLACK-LITTERMAN MODEL
    # ═══════════════════════════════════════════════════════════════════════
    
    def black_litterman(
        self,
        market_caps: Dict[str, float],
        views: List[BlackLittermanView],
        tau: float = 0.05,
        risk_aversion: float = 2.5
    ) -> PortfolioResult:
        """
        Black-Litterman Model
        
        Combines market equilibrium with investor views
        
        Args:
            market_caps: Market capitalizations
            views: List of investor views
            tau: Uncertainty of equilibrium (usually 0.025-0.05)
            risk_aversion: Risk aversion coefficient
        """
        
        # Market cap weights
        total_cap = sum(market_caps.values())
        w_mkt = np.array([market_caps.get(a, 0) / total_cap for a in self.assets])
        
        # Implied equilibrium returns
        sigma = self.cov_matrix.values
        pi = risk_aversion * np.dot(sigma, w_mkt)
        
        if not views:
            # No views - return market portfolio
            weights = dict(zip(self.assets, w_mkt))
            return PortfolioResult(
                weights=weights,
                expected_return=np.dot(w_mkt, pi),
                volatility=np.sqrt(np.dot(w_mkt.T, np.dot(sigma, w_mkt))),
                sharpe_ratio=(np.dot(w_mkt, pi) - self.rf) / np.sqrt(np.dot(w_mkt.T, np.dot(sigma, w_mkt))),
                method='Black-Litterman (Market Equilibrium)'
            )
        
        # Build view matrices
        n_views = len(views)
        P = np.zeros((n_views, self.n_assets))  # View portfolio matrix
        Q = np.zeros(n_views)  # View returns
        omega_diag = np.zeros(n_views)  # View uncertainties
        
        for i, view in enumerate(views):
            for asset, weight in zip(view.assets, view.weights):
                if asset in self.assets:
                    P[i, self.assets.index(asset)] = weight
            Q[i] = view.expected_return
            # View uncertainty - proportional to view volatility and inverse of confidence
            view_var = np.dot(P[i], np.dot(sigma, P[i].T))
            omega_diag[i] = view_var * (1 - view.confidence) / view.confidence
        
        omega = np.diag(omega_diag)
        
        # Black-Litterman formula
        tau_sigma = tau * sigma
        
        # M = [(τΣ)^(-1) + P'Ω^(-1)P]^(-1)
        M = linalg.inv(linalg.inv(tau_sigma) + np.dot(P.T, np.dot(linalg.inv(omega), P)))
        
        # μ_BL = M × [(τΣ)^(-1)π + P'Ω^(-1)Q]
        bl_returns = np.dot(M, np.dot(linalg.inv(tau_sigma), pi) + 
                           np.dot(P.T, np.dot(linalg.inv(omega), Q)))
        
        # Optimal weights from BL returns
        bl_sigma = sigma + M
        w_bl = np.dot(linalg.inv(risk_aversion * bl_sigma), bl_returns)
        
        # Normalize weights
        w_bl = np.maximum(w_bl, 0)  # Long only
        w_bl = w_bl / np.sum(w_bl)
        
        weights = dict(zip(self.assets, w_bl))
        
        return PortfolioResult(
            weights=weights,
            expected_return=np.dot(w_bl, bl_returns),
            volatility=np.sqrt(np.dot(w_bl.T, np.dot(sigma, w_bl))),
            sharpe_ratio=(np.dot(w_bl, bl_returns) - self.rf) / np.sqrt(np.dot(w_bl.T, np.dot(sigma, w_bl))),
            method='Black-Litterman'
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # RISK PARITY
    # ═══════════════════════════════════════════════════════════════════════
    
    def risk_parity(self) -> PortfolioResult:
        """
        Risk Parity Portfolio
        
        Each asset contributes equally to portfolio risk
        """
        
        def risk_contribution(weights):
            """Calculate risk contribution of each asset"""
            sigma = self.cov_matrix.values
            port_vol = np.sqrt(np.dot(weights.T, np.dot(sigma, weights)))
            
            # Marginal risk contribution
            mrc = np.dot(sigma, weights)
            
            # Risk contribution = weight * marginal contribution
            rc = weights * mrc / port_vol
            
            return rc
        
        def objective(weights):
            """Minimize deviation from equal risk contribution"""
            rc = risk_contribution(weights)
            target_rc = np.mean(rc)
            return np.sum((rc - target_rc) ** 2)
        
        # Constraints and bounds
        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds = tuple((0.01, 1) for _ in range(self.n_assets))
        x0 = np.array([1/self.n_assets] * self.n_assets)
        
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )
        
        weights = dict(zip(self.assets, result.x))
        
        return PortfolioResult(
            weights=weights,
            expected_return=self._portfolio_return(result.x),
            volatility=self._portfolio_volatility(result.x),
            sharpe_ratio=self._sharpe_ratio(result.x),
            method='Risk Parity'
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # MAXIMUM SHARPE RATIO
    # ═══════════════════════════════════════════════════════════════════════
    
    def max_sharpe(self, constraints: Optional[Dict] = None) -> PortfolioResult:
        """
        Maximum Sharpe Ratio Portfolio
        
        Also known as tangency portfolio
        """
        
        def neg_sharpe(weights):
            return -self._sharpe_ratio(weights)
        
        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        
        if constraints:
            if 'max_weight' in constraints:
                bounds = tuple((0, constraints['max_weight']) for _ in range(self.n_assets))
        
        x0 = np.array([1/self.n_assets] * self.n_assets)
        
        result = minimize(
            neg_sharpe,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )
        
        weights = dict(zip(self.assets, result.x))
        
        return PortfolioResult(
            weights=weights,
            expected_return=self._portfolio_return(result.x),
            volatility=self._portfolio_volatility(result.x),
            sharpe_ratio=self._sharpe_ratio(result.x),
            method='Maximum Sharpe Ratio'
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # MINIMUM VOLATILITY
    # ═══════════════════════════════════════════════════════════════════════
    
    def min_volatility(self, constraints: Optional[Dict] = None) -> PortfolioResult:
        """
        Minimum Volatility Portfolio
        
        Also known as Global Minimum Variance (GMV) portfolio
        """
        
        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        
        if constraints:
            if 'max_weight' in constraints:
                bounds = tuple((0, constraints['max_weight']) for _ in range(self.n_assets))
        
        x0 = np.array([1/self.n_assets] * self.n_assets)
        
        result = minimize(
            self._portfolio_volatility,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )
        
        weights = dict(zip(self.assets, result.x))
        
        return PortfolioResult(
            weights=weights,
            expected_return=self._portfolio_return(result.x),
            volatility=self._portfolio_volatility(result.x),
            sharpe_ratio=self._sharpe_ratio(result.x),
            method='Minimum Volatility'
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # EFFICIENT FRONTIER
    # ═══════════════════════════════════════════════════════════════════════
    
    def efficient_frontier(
        self,
        n_points: int = 50,
        constraints: Optional[Dict] = None
    ) -> List[PortfolioResult]:
        """
        Generate Efficient Frontier
        
        Returns portfolios along the efficient frontier
        """
        
        # Find min/max returns
        min_vol_port = self.min_volatility(constraints)
        max_sharpe_port = self.max_sharpe(constraints)
        
        min_ret = min_vol_port.expected_return
        max_ret = max(self.mean_returns) * 0.95  # 95% of max individual return
        
        target_returns = np.linspace(min_ret, max_ret, n_points)
        
        frontier = []
        for target_ret in target_returns:
            try:
                port = self.mean_variance_optimize(
                    target_return=target_ret,
                    constraints=constraints
                )
                frontier.append(port)
            except Exception:
                continue
        
        return frontier
    
    # ═══════════════════════════════════════════════════════════════════════
    # PORTFOLIO ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════
    
    def analyze_portfolio(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze a portfolio's characteristics
        """
        
        w = np.array([weights.get(a, 0) for a in self.assets])
        
        # Basic metrics
        exp_return = self._portfolio_return(w)
        volatility = self._portfolio_volatility(w)
        sharpe = self._sharpe_ratio(w)
        
        # Risk decomposition
        sigma = self.cov_matrix.values
        mrc = np.dot(sigma, w) / volatility
        rc = w * mrc  # Risk contribution
        
        # Diversification metrics
        weighted_vol = np.sum(w * np.sqrt(np.diag(sigma)))
        div_ratio = weighted_vol / volatility
        
        # Concentration metrics
        hhi = np.sum(w ** 2)  # Herfindahl-Hirschman Index
        eff_n = 1 / hhi  # Effective number of assets
        
        # VaR and CVaR (parametric)
        var_95 = exp_return - 1.645 * volatility
        var_99 = exp_return - 2.326 * volatility
        
        return {
            'expected_return': exp_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'risk_contribution': dict(zip(self.assets, rc)),
            'diversification_ratio': div_ratio,
            'herfindahl_index': hhi,
            'effective_n_assets': eff_n,
            'var_95': var_95,
            'var_99': var_99,
            'max_weight': max(w),
            'min_weight': min(w[w > 0]) if np.any(w > 0) else 0,
            'n_active_assets': np.sum(w > 0.001)
        }
    
    def rebalance_triggers(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        threshold_pct: float = 5.0
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Check if rebalancing is needed
        
        Returns:
            (needs_rebalance, drift_by_asset)
        """
        
        drift = {}
        max_drift = 0
        
        for asset in self.assets:
            current = current_weights.get(asset, 0)
            target = target_weights.get(asset, 0)
            
            if target > 0:
                asset_drift = abs(current - target) / target * 100
            else:
                asset_drift = abs(current) * 100
            
            drift[asset] = asset_drift
            max_drift = max(max_drift, asset_drift)
        
        needs_rebalance = max_drift > threshold_pct
        
        return needs_rebalance, drift


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demo the portfolio optimizer"""
    
    print("=" * 70)
    print("📊 GENIUS PORTFOLIO OPTIMIZER v1.0 - DEMO")
    print("=" * 70)
    
    # Generate sample data
    np.random.seed(42)
    n_days = 252 * 2
    
    assets = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP']
    
    # Simulated daily returns
    returns_data = {
        'BTC': np.random.normal(0.001, 0.03, n_days),
        'ETH': np.random.normal(0.0015, 0.04, n_days),
        'SOL': np.random.normal(0.002, 0.06, n_days),
        'BNB': np.random.normal(0.0008, 0.035, n_days),
        'XRP': np.random.normal(0.0005, 0.05, n_days),
    }
    
    returns = pd.DataFrame(returns_data)
    
    print(f"\n📈 Sample Data: {len(returns)} days, {len(assets)} assets")
    print(f"   Assets: {', '.join(assets)}")
    
    # Initialize optimizer
    optimizer = GeniusPortfolioOptimizer(returns, risk_free_rate=0.04)
    
    # 1. Mean-Variance Optimization
    print("\n" + "─" * 50)
    print("1️⃣ MEAN-VARIANCE OPTIMIZATION (Markowitz)")
    mv_port = optimizer.mean_variance_optimize()
    print(f"   {mv_port}")
    for asset, weight in sorted(mv_port.weights.items(), key=lambda x: -x[1]):
        if weight > 0.01:
            print(f"      {asset}: {weight:.1%}")
    
    # 2. Maximum Sharpe Ratio
    print("\n" + "─" * 50)
    print("2️⃣ MAXIMUM SHARPE RATIO (Tangency Portfolio)")
    ms_port = optimizer.max_sharpe()
    print(f"   {ms_port}")
    for asset, weight in sorted(ms_port.weights.items(), key=lambda x: -x[1]):
        if weight > 0.01:
            print(f"      {asset}: {weight:.1%}")
    
    # 3. Minimum Volatility
    print("\n" + "─" * 50)
    print("3️⃣ MINIMUM VOLATILITY (GMV Portfolio)")
    mv_port = optimizer.min_volatility()
    print(f"   {mv_port}")
    for asset, weight in sorted(mv_port.weights.items(), key=lambda x: -x[1]):
        if weight > 0.01:
            print(f"      {asset}: {weight:.1%}")
    
    # 4. Risk Parity
    print("\n" + "─" * 50)
    print("4️⃣ RISK PARITY (Equal Risk Contribution)")
    rp_port = optimizer.risk_parity()
    print(f"   {rp_port}")
    for asset, weight in sorted(rp_port.weights.items(), key=lambda x: -x[1]):
        if weight > 0.01:
            print(f"      {asset}: {weight:.1%}")
    
    # 5. Black-Litterman
    print("\n" + "─" * 50)
    print("5️⃣ BLACK-LITTERMAN (with Views)")
    
    market_caps = {
        'BTC': 1900e9,
        'ETH': 400e9,
        'SOL': 80e9,
        'BNB': 90e9,
        'XRP': 30e9
    }
    
    views = [
        BlackLittermanView(
            assets=['ETH'],
            weights=[1.0],
            expected_return=0.50,  # 50% return expectation
            confidence=0.7
        ),
        BlackLittermanView(
            assets=['SOL'],
            weights=[1.0],
            expected_return=0.80,  # 80% return expectation
            confidence=0.5
        ),
        BlackLittermanView(
            assets=['ETH', 'BTC'],
            weights=[1.0, -1.0],
            expected_return=0.10,  # ETH outperforms BTC by 10%
            confidence=0.6
        )
    ]
    
    bl_port = optimizer.black_litterman(market_caps, views)
    print(f"   {bl_port}")
    for asset, weight in sorted(bl_port.weights.items(), key=lambda x: -x[1]):
        if weight > 0.01:
            print(f"      {asset}: {weight:.1%}")
    
    # 6. Portfolio Analysis
    print("\n" + "─" * 50)
    print("6️⃣ PORTFOLIO ANALYSIS (Risk Parity)")
    analysis = optimizer.analyze_portfolio(rp_port.weights)
    print(f"   Expected Return: {analysis['expected_return']:.1%}")
    print(f"   Volatility: {analysis['volatility']:.1%}")
    print(f"   Sharpe Ratio: {analysis['sharpe_ratio']:.2f}")
    print(f"   VaR (95%): {analysis['var_95']:.1%}")
    print(f"   VaR (99%): {analysis['var_99']:.1%}")
    print(f"   Diversification Ratio: {analysis['diversification_ratio']:.2f}")
    print(f"   Effective # Assets: {analysis['effective_n_assets']:.1f}")
    
    # 7. Efficient Frontier
    print("\n" + "─" * 50)
    print("7️⃣ EFFICIENT FRONTIER")
    frontier = optimizer.efficient_frontier(n_points=10)
    print(f"   Generated {len(frontier)} portfolios on efficient frontier:")
    for i, p in enumerate(frontier[::3]):  # Every 3rd
        print(f"      {i+1}. Return: {p.expected_return:.1%}, Vol: {p.volatility:.1%}, Sharpe: {p.sharpe_ratio:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ Portfolio Optimizer Demo Complete!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    demo()
