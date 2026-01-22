"""
💼 PORTFOLIO OPTIMIZER - Professional Portfolio Management
Wykorzystuje biblioteki: empyrical, statsmodels, scipy
Algorytmy używane przez prawdziwe fundusze hedgingowe
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

# Try to import quant libraries
try:
    import empyrical as ep
    EMPYRICAL_AVAILABLE = True
except ImportError:
    EMPYRICAL_AVAILABLE = False

try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """
    Professional portfolio optimization
    Methods used by Renaissance Technologies, Two Sigma, Bridgewater
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize portfolio optimizer
        
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
        
        if not EMPYRICAL_AVAILABLE:
            self.logger.warning("⚠️ empyrical not available - some metrics disabled")
        if not SCIPY_AVAILABLE:
            self.logger.warning("⚠️ scipy not available - optimization disabled")
        if not STATSMODELS_AVAILABLE:
            self.logger.warning("⚠️ statsmodels not available - forecasting disabled")
    
    def calculate_performance_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """
        Calculate professional performance metrics
        Used by all major funds for reporting
        
        Args:
            returns: Series of daily returns
            
        Returns:
            Dict with metrics: sharpe, sortino, calmar, max_drawdown, etc.
        """
        if not EMPYRICAL_AVAILABLE:
            return self._calculate_basic_metrics(returns)
        
        try:
            metrics = {
                'total_return': ep.cum_returns_final(returns),
                'annual_return': ep.annual_return(returns),
                'annual_volatility': ep.annual_volatility(returns),
                'sharpe_ratio': ep.sharpe_ratio(returns, risk_free=self.risk_free_rate),
                'sortino_ratio': ep.sortino_ratio(returns, required_return=0),
                'calmar_ratio': ep.calmar_ratio(returns),
                'max_drawdown': ep.max_drawdown(returns),
                'omega_ratio': ep.omega_ratio(returns, risk_free=self.risk_free_rate),
                'tail_ratio': ep.tail_ratio(returns),
                'value_at_risk': ep.value_at_risk(returns, cutoff=0.05),
                'conditional_value_at_risk': ep.conditional_value_at_risk(returns, cutoff=0.05)
            }
            
            self.logger.info(f"📊 Performance: Sharpe={metrics['sharpe_ratio']:.2f}, "
                           f"MaxDD={metrics['max_drawdown']:.2%}, "
                           f"Annual Return={metrics['annual_return']:.2%}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Empyrical metrics failed: {e}")
            return self._calculate_basic_metrics(returns)
    
    def _calculate_basic_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Fallback basic metrics when empyrical not available"""
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe = (annual_return - self.risk_free_rate) / volatility if volatility > 0 else 0
        
        # Calculate max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd
        }
    
    def optimize_portfolio_weights(self, returns_df: pd.DataFrame, 
                                   method: str = 'sharpe') -> Dict[str, float]:
        """
        Optimize portfolio weights using Modern Portfolio Theory
        Methods: 'sharpe', 'min_variance', 'risk_parity'
        
        Args:
            returns_df: DataFrame with asset returns (columns = assets)
            method: Optimization method
            
        Returns:
            Dict with optimal weights for each asset
        """
        if not SCIPY_AVAILABLE:
            return self._equal_weight_portfolio(returns_df)
        
        try:
            n_assets = len(returns_df.columns)
            
            if method == 'sharpe':
                weights = self._maximize_sharpe(returns_df)
            elif method == 'min_variance':
                weights = self._minimize_variance(returns_df)
            elif method == 'risk_parity':
                weights = self._risk_parity(returns_df)
            else:
                weights = np.array([1/n_assets] * n_assets)
            
            # Create dict with asset names
            weight_dict = {
                asset: float(weight) 
                for asset, weight in zip(returns_df.columns, weights)
            }
            
            self.logger.info(f"🎯 Optimized weights ({method}): {weight_dict}")
            return weight_dict
            
        except Exception as e:
            self.logger.error(f"Portfolio optimization failed: {e}")
            return self._equal_weight_portfolio(returns_df)
    
    def _maximize_sharpe(self, returns_df: pd.DataFrame) -> np.ndarray:
        """Maximize Sharpe ratio (used by most quant funds)"""
        mean_returns = returns_df.mean() * 252  # Annualized
        cov_matrix = returns_df.cov() * 252
        n_assets = len(returns_df.columns)
        
        def neg_sharpe(weights):
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
            return -sharpe
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_guess = np.array([1/n_assets] * n_assets)
        
        result = minimize(neg_sharpe, initial_guess, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        return result.x
    
    def _minimize_variance(self, returns_df: pd.DataFrame) -> np.ndarray:
        """Minimize portfolio variance (conservative approach)"""
        cov_matrix = returns_df.cov() * 252
        n_assets = len(returns_df.columns)
        
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_guess = np.array([1/n_assets] * n_assets)
        
        result = minimize(portfolio_variance, initial_guess, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        return result.x
    
    def _risk_parity(self, returns_df: pd.DataFrame) -> np.ndarray:
        """
        Risk Parity allocation (Bridgewater's All Weather Portfolio)
        Equal risk contribution from each asset
        """
        cov_matrix = returns_df.cov() * 252
        n_assets = len(returns_df.columns)
        
        def risk_parity_objective(weights):
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            risk_contrib = weights * marginal_contrib
            target = portfolio_vol / n_assets
            return np.sum((risk_contrib - target) ** 2)
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0.01, 1) for _ in range(n_assets))  # Min 1% per asset
        initial_guess = np.array([1/n_assets] * n_assets)
        
        result = minimize(risk_parity_objective, initial_guess, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        return result.x
    
    def _equal_weight_portfolio(self, returns_df: pd.DataFrame) -> Dict[str, float]:
        """Fallback: equal weight allocation"""
        n_assets = len(returns_df.columns)
        weight = 1 / n_assets
        return {asset: weight for asset in returns_df.columns}
    
    def kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly Criterion position size
        Used by Renaissance Technologies and professional gamblers
        
        Args:
            win_rate: Probability of winning (0-1)
            avg_win: Average win amount
            avg_loss: Average loss amount (positive number)
            
        Returns:
            Optimal fraction of capital to risk (0-1)
        """
        if avg_loss == 0:
            return 0
        
        # Kelly formula: f = (p * b - q) / b
        # where p = win_rate, q = 1-p, b = avg_win/avg_loss
        q = 1 - win_rate
        b = avg_win / avg_loss
        kelly = (win_rate * b - q) / b
        
        # Use fractional Kelly for safety (typically 0.25x to 0.5x)
        # Full Kelly is too aggressive for real trading
        fractional_kelly = max(0, min(kelly * 0.25, 0.5))  # Cap at 50%
        
        self.logger.info(f"🎲 Kelly Criterion: {fractional_kelly:.2%} "
                        f"(win_rate={win_rate:.1%}, ratio={b:.2f})")
        
        return fractional_kelly
    
    def calculate_var_cvar(self, returns: pd.Series, 
                          confidence: float = 0.95) -> Tuple[float, float]:
        """
        Calculate Value at Risk (VaR) and Conditional VaR (CVaR)
        Required by Basel III banking regulations
        
        Args:
            returns: Series of returns
            confidence: Confidence level (default 95%)
            
        Returns:
            Tuple of (VaR, CVaR)
        """
        if EMPYRICAL_AVAILABLE:
            var = ep.value_at_risk(returns, cutoff=1-confidence)
            cvar = ep.conditional_value_at_risk(returns, cutoff=1-confidence)
        else:
            # Fallback calculation
            sorted_returns = np.sort(returns)
            index = int((1 - confidence) * len(sorted_returns))
            var = abs(sorted_returns[index])
            cvar = abs(sorted_returns[:index].mean())
        
        self.logger.info(f"📉 Risk Metrics: VaR({confidence:.0%})={var:.2%}, "
                        f"CVaR={cvar:.2%}")
        
        return var, cvar
    
    def forecast_returns(self, price_history: pd.Series, 
                        periods: int = 5) -> pd.Series:
        """
        Forecast future returns using ARIMA
        
        Args:
            price_history: Historical price series
            periods: Number of periods to forecast
            
        Returns:
            Forecasted prices
        """
        if not STATSMODELS_AVAILABLE:
            # Simple fallback: use last return
            last_return = price_history.pct_change().iloc[-1]
            last_price = price_history.iloc[-1]
            forecast = [last_price * (1 + last_return) ** i for i in range(1, periods + 1)]
            return pd.Series(forecast)
        
        try:
            from statsmodels.tsa.arima.model import ARIMA
            
            # Fit ARIMA model
            model = ARIMA(price_history, order=(1, 1, 1))
            fitted = model.fit()
            
            # Forecast
            forecast = fitted.forecast(steps=periods)
            
            self.logger.info(f"📈 ARIMA Forecast: {forecast.iloc[0]:.2f} → {forecast.iloc[-1]:.2f}")
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"ARIMA forecast failed: {e}")
            # Fallback
            last_return = price_history.pct_change().iloc[-1]
            last_price = price_history.iloc[-1]
            forecast = [last_price * (1 + last_return) ** i for i in range(1, periods + 1)]
            return pd.Series(forecast)
    
    def efficient_frontier(self, returns_df: pd.DataFrame, 
                          n_points: int = 50) -> pd.DataFrame:
        """
        Calculate efficient frontier points
        Used for portfolio visualization by wealth managers
        
        Args:
            returns_df: DataFrame with asset returns
            n_points: Number of points on frontier
            
        Returns:
            DataFrame with (risk, return) pairs
        """
        if not SCIPY_AVAILABLE:
            return pd.DataFrame({'risk': [0], 'return': [0]})
        
        mean_returns = returns_df.mean() * 252
        cov_matrix = returns_df.cov() * 252
        n_assets = len(returns_df.columns)
        
        target_returns = np.linspace(mean_returns.min(), mean_returns.max(), n_points)
        efficient_portfolios = []
        
        for target in target_returns:
            def portfolio_variance(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))
            
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(mean_returns * x) - target}
            ]
            bounds = tuple((0, 1) for _ in range(n_assets))
            initial_guess = np.array([1/n_assets] * n_assets)
            
            try:
                result = minimize(portfolio_variance, initial_guess, 
                                method='SLSQP', bounds=bounds, constraints=constraints)
                if result.success:
                    vol = np.sqrt(portfolio_variance(result.x))
                    efficient_portfolios.append({'risk': vol, 'return': target})
            except:
                continue
        
        return pd.DataFrame(efficient_portfolios)


# Global instance
portfolio_optimizer = PortfolioOptimizer()
