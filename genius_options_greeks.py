"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GENIUS OPTIONS GREEKS v1.0                                 ║
║                    Professional Options Analytics                             ║
║                                                                              ║
║  Features:                                                                   ║
║  • Delta - Price sensitivity                                                ║
║  • Gamma - Delta change rate                                                ║
║  • Theta - Time decay                                                       ║
║  • Vega - Volatility sensitivity                                            ║
║  • Rho - Interest rate sensitivity                                          ║
║  • Black-Scholes pricing with Greeks                                        ║
║  • Greeks-based trading signals                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from datetime import datetime, timedelta
import math

class OptionType(Enum):
    """Option type enumeration"""
    CALL = "call"
    PUT = "put"


@dataclass
class OptionGreeks:
    """Container for all option Greeks"""
    delta: float      # Price sensitivity (∂V/∂S)
    gamma: float      # Delta change rate (∂²V/∂S²)
    theta: float      # Time decay (∂V/∂t)
    vega: float       # Volatility sensitivity (∂V/∂σ)
    rho: float        # Interest rate sensitivity (∂V/∂r)
    
    # Additional metrics
    lambda_: float    # Leverage (Ω = Δ × S/V)
    vanna: float      # ∂Δ/∂σ = ∂V/(∂S∂σ)
    volga: float      # ∂²V/∂σ² (vomma)
    charm: float      # ∂Δ/∂t (delta decay)
    speed: float      # ∂Γ/∂S (gamma sensitivity)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'delta': self.delta,
            'gamma': self.gamma,
            'theta': self.theta,
            'vega': self.vega,
            'rho': self.rho,
            'lambda': self.lambda_,
            'vanna': self.vanna,
            'volga': self.volga,
            'charm': self.charm,
            'speed': self.speed
        }


@dataclass
class OptionData:
    """Container for option pricing data"""
    spot_price: float        # Current underlying price
    strike_price: float      # Option strike
    time_to_expiry: float    # Years until expiration
    volatility: float        # Implied volatility (annualized)
    risk_free_rate: float    # Risk-free interest rate
    dividend_yield: float    # Continuous dividend yield
    option_type: OptionType  # CALL or PUT


class GeniusOptionsGreeks:
    """
    Professional Options Greeks Calculator
    
    Implements Black-Scholes model with all Greeks for options analysis.
    Includes higher-order Greeks for advanced risk management.
    """
    
    def __init__(self, precision: int = 6):
        self.precision = precision
        
        # Cache for repeated calculations
        self._cache: Dict[str, Any] = {}
    
    # ═══════════════════════════════════════════════════════════════════════
    # BLACK-SCHOLES CORE
    # ═══════════════════════════════════════════════════════════════════════
    
    def _d1(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0
    ) -> float:
        """Calculate d1 parameter for Black-Scholes"""
        
        if T <= 0 or sigma <= 0:
            return 0.0
        
        return (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    
    def _d2(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0
    ) -> float:
        """Calculate d2 parameter for Black-Scholes"""
        
        if T <= 0 or sigma <= 0:
            return 0.0
        
        return self._d1(S, K, T, r, sigma, q) - sigma * np.sqrt(T)
    
    def black_scholes_price(
        self,
        S: float,           # Spot price
        K: float,           # Strike price
        T: float,           # Time to expiry (years)
        r: float,           # Risk-free rate
        sigma: float,       # Volatility
        q: float = 0,       # Dividend yield
        option_type: OptionType = OptionType.CALL
    ) -> float:
        """
        Calculate Black-Scholes option price
        
        Args:
            S: Current underlying price
            K: Strike price
            T: Time to expiration in years
            r: Risk-free interest rate
            sigma: Volatility (annualized)
            q: Continuous dividend yield
            option_type: CALL or PUT
            
        Returns:
            Option price
        """
        
        if T <= 0:
            # At expiration
            if option_type == OptionType.CALL:
                return max(0, S - K)
            else:
                return max(0, K - S)
        
        d1 = self._d1(S, K, T, r, sigma, q)
        d2 = self._d2(S, K, T, r, sigma, q)
        
        if option_type == OptionType.CALL:
            price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # PUT
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
        
        return round(price, self.precision)
    
    # ═══════════════════════════════════════════════════════════════════════
    # FIRST-ORDER GREEKS
    # ═══════════════════════════════════════════════════════════════════════
    
    def delta(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0,
        option_type: OptionType = OptionType.CALL
    ) -> float:
        """
        Calculate Delta (Δ) - Rate of change of option price with respect to underlying
        
        Delta represents:
        - Hedge ratio (number of shares to hedge 1 option)
        - Approximate probability of expiring ITM
        - Price sensitivity to $1 move in underlying
        
        Range:
        - Call: 0 to 1
        - Put: -1 to 0
        """
        
        if T <= 0:
            if option_type == OptionType.CALL:
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0
        
        d1 = self._d1(S, K, T, r, sigma, q)
        
        if option_type == OptionType.CALL:
            return round(np.exp(-q * T) * norm.cdf(d1), self.precision)
        else:
            return round(np.exp(-q * T) * (norm.cdf(d1) - 1), self.precision)
    
    def gamma(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0
    ) -> float:
        """
        Calculate Gamma (Γ) - Rate of change of Delta with respect to underlying
        
        Gamma represents:
        - How quickly delta changes
        - Curvature of option price curve
        - Same for both calls and puts
        
        High gamma = More sensitive delta (ATM options)
        """
        
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1 = self._d1(S, K, T, r, sigma, q)
        
        gamma = (np.exp(-q * T) * norm.pdf(d1)) / (S * sigma * np.sqrt(T))
        
        return round(gamma, self.precision)
    
    def theta(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0,
        option_type: OptionType = OptionType.CALL
    ) -> float:
        """
        Calculate Theta (Θ) - Rate of change of option price with respect to time
        
        Theta represents:
        - Time decay per day
        - Usually negative (options lose value over time)
        - Expressed as daily decay (divided by 365)
        """
        
        if T <= 0:
            return 0.0
        
        d1 = self._d1(S, K, T, r, sigma, q)
        d2 = self._d2(S, K, T, r, sigma, q)
        
        # First term (same for call and put)
        term1 = -(S * np.exp(-q * T) * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        
        if option_type == OptionType.CALL:
            theta = (
                term1 
                + q * S * np.exp(-q * T) * norm.cdf(d1)
                - r * K * np.exp(-r * T) * norm.cdf(d2)
            )
        else:  # PUT
            theta = (
                term1
                - q * S * np.exp(-q * T) * norm.cdf(-d1)
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
            )
        
        # Convert to daily theta
        daily_theta = theta / 365
        
        return round(daily_theta, self.precision)
    
    def vega(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0
    ) -> float:
        """
        Calculate Vega (ν) - Rate of change of option price with respect to volatility
        
        Vega represents:
        - Sensitivity to 1% change in volatility
        - Same for both calls and puts
        - Highest for ATM options
        
        Note: Vega is not a Greek letter, but commonly used
        """
        
        if T <= 0:
            return 0.0
        
        d1 = self._d1(S, K, T, r, sigma, q)
        
        # Vega per 1% volatility change
        vega = (S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)) / 100
        
        return round(vega, self.precision)
    
    def rho(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0,
        option_type: OptionType = OptionType.CALL
    ) -> float:
        """
        Calculate Rho (ρ) - Rate of change of option price with respect to interest rate
        
        Rho represents:
        - Sensitivity to 1% change in risk-free rate
        - Calls have positive rho (benefit from higher rates)
        - Puts have negative rho
        """
        
        if T <= 0:
            return 0.0
        
        d2 = self._d2(S, K, T, r, sigma, q)
        
        if option_type == OptionType.CALL:
            rho = (K * T * np.exp(-r * T) * norm.cdf(d2)) / 100
        else:  # PUT
            rho = -(K * T * np.exp(-r * T) * norm.cdf(-d2)) / 100
        
        return round(rho, self.precision)
    
    # ═══════════════════════════════════════════════════════════════════════
    # HIGHER-ORDER GREEKS
    # ═══════════════════════════════════════════════════════════════════════
    
    def lambda_leverage(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0,
        option_type: OptionType = OptionType.CALL
    ) -> float:
        """
        Calculate Lambda (Ω) - Leverage / Elasticity
        
        Lambda = Delta × (Spot / Option Price)
        
        Represents percentage change in option price for 1% change in underlying
        """
        
        delta_val = self.delta(S, K, T, r, sigma, q, option_type)
        price = self.black_scholes_price(S, K, T, r, sigma, q, option_type)
        
        if price <= 0:
            return 0.0
        
        return round(delta_val * S / price, self.precision)
    
    def vanna(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0
    ) -> float:
        """
        Calculate Vanna - Cross derivative of delta with respect to volatility
        
        Vanna = ∂Delta/∂σ = ∂Vega/∂S
        
        Important for volatility smile/skew risk management
        """
        
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1 = self._d1(S, K, T, r, sigma, q)
        d2 = self._d2(S, K, T, r, sigma, q)
        
        vanna = -np.exp(-q * T) * norm.pdf(d1) * d2 / sigma
        
        return round(vanna, self.precision)
    
    def volga(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0
    ) -> float:
        """
        Calculate Volga (Vomma) - Second derivative of option price with respect to volatility
        
        Volga = ∂²V/∂σ² = ∂Vega/∂σ
        
        Measures convexity of vega
        """
        
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1 = self._d1(S, K, T, r, sigma, q)
        d2 = self._d2(S, K, T, r, sigma, q)
        
        vega_val = self.vega(S, K, T, r, sigma, q) * 100  # Convert back
        volga = vega_val * d1 * d2 / sigma
        
        return round(volga, self.precision)
    
    def charm(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0,
        option_type: OptionType = OptionType.CALL
    ) -> float:
        """
        Calculate Charm - Rate of change of delta over time
        
        Charm = ∂Delta/∂t (Delta Decay)
        
        Important for understanding how delta changes as time passes
        """
        
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1 = self._d1(S, K, T, r, sigma, q)
        d2 = self._d2(S, K, T, r, sigma, q)
        
        term1 = np.exp(-q * T) * norm.pdf(d1)
        term2 = 2 * (r - q) * T - d2 * sigma * np.sqrt(T)
        term3 = 2 * T * sigma * np.sqrt(T)
        
        charm = -q * np.exp(-q * T) * norm.cdf(d1 if option_type == OptionType.CALL else -d1) + \
                term1 * term2 / term3
        
        # Daily charm
        return round(charm / 365, self.precision)
    
    def speed(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0
    ) -> float:
        """
        Calculate Speed - Rate of change of gamma with respect to underlying
        
        Speed = ∂Gamma/∂S = ∂³V/∂S³
        
        Third derivative, important for large moves
        """
        
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1 = self._d1(S, K, T, r, sigma, q)
        gamma_val = self.gamma(S, K, T, r, sigma, q)
        
        speed = -gamma_val / S * (d1 / (sigma * np.sqrt(T)) + 1)
        
        return round(speed, self.precision)
    
    # ═══════════════════════════════════════════════════════════════════════
    # ALL GREEKS CALCULATOR
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_all_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0,
        option_type: OptionType = OptionType.CALL
    ) -> OptionGreeks:
        """
        Calculate all Greeks at once
        
        Returns:
            OptionGreeks dataclass with all values
        """
        
        return OptionGreeks(
            delta=self.delta(S, K, T, r, sigma, q, option_type),
            gamma=self.gamma(S, K, T, r, sigma, q),
            theta=self.theta(S, K, T, r, sigma, q, option_type),
            vega=self.vega(S, K, T, r, sigma, q),
            rho=self.rho(S, K, T, r, sigma, q, option_type),
            lambda_=self.lambda_leverage(S, K, T, r, sigma, q, option_type),
            vanna=self.vanna(S, K, T, r, sigma, q),
            volga=self.volga(S, K, T, r, sigma, q),
            charm=self.charm(S, K, T, r, sigma, q, option_type),
            speed=self.speed(S, K, T, r, sigma, q)
        )
    
    def calculate_from_option_data(self, data: OptionData) -> OptionGreeks:
        """Calculate all Greeks from OptionData object"""
        
        return self.calculate_all_greeks(
            S=data.spot_price,
            K=data.strike_price,
            T=data.time_to_expiry,
            r=data.risk_free_rate,
            sigma=data.volatility,
            q=data.dividend_yield,
            option_type=data.option_type
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # IMPLIED VOLATILITY
    # ═══════════════════════════════════════════════════════════════════════
    
    def implied_volatility(
        self,
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        q: float = 0,
        option_type: OptionType = OptionType.CALL,
        precision: float = 1e-6,
        max_iterations: int = 100
    ) -> float:
        """
        Calculate Implied Volatility using Brent's method
        
        Args:
            market_price: Observed option price
            S, K, T, r, q: Option parameters
            option_type: CALL or PUT
            
        Returns:
            Implied volatility (annualized)
        """
        
        def objective(sigma):
            return self.black_scholes_price(S, K, T, r, sigma, q, option_type) - market_price
        
        try:
            # Search between 0.1% and 500% volatility
            iv = brentq(objective, 0.001, 5.0, xtol=precision, maxiter=max_iterations)
            return round(iv, self.precision)
        except ValueError:
            # If no solution found, return NaN
            return float('nan')
    
    # ═══════════════════════════════════════════════════════════════════════
    # TRADING SIGNAL INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def analyze_greeks_for_trading(
        self,
        greeks: OptionGreeks,
        option_type: OptionType = OptionType.CALL
    ) -> Dict[str, Any]:
        """
        Analyze Greeks for trading signals
        
        Returns insights about:
        - Directional bias
        - Risk level
        - Optimal strategies
        """
        
        analysis = {
            'directional_bias': 'NEUTRAL',
            'risk_level': 'MEDIUM',
            'time_decay_impact': 'MODERATE',
            'volatility_sensitivity': 'MODERATE',
            'recommendations': []
        }
        
        # Directional bias from delta
        if option_type == OptionType.CALL:
            if greeks.delta > 0.7:
                analysis['directional_bias'] = 'STRONG_BULLISH'
            elif greeks.delta > 0.5:
                analysis['directional_bias'] = 'BULLISH'
            elif greeks.delta < 0.3:
                analysis['directional_bias'] = 'WEAK'
        else:  # PUT
            if greeks.delta < -0.7:
                analysis['directional_bias'] = 'STRONG_BEARISH'
            elif greeks.delta < -0.5:
                analysis['directional_bias'] = 'BEARISH'
            elif greeks.delta > -0.3:
                analysis['directional_bias'] = 'WEAK'
        
        # Risk from gamma
        if greeks.gamma > 0.05:
            analysis['risk_level'] = 'HIGH'
            analysis['recommendations'].append('High gamma - consider hedging more frequently')
        elif greeks.gamma < 0.01:
            analysis['risk_level'] = 'LOW'
        
        # Time decay analysis
        if abs(greeks.theta) > 0.5:
            analysis['time_decay_impact'] = 'HIGH'
            analysis['recommendations'].append('High theta decay - time is working against long positions')
        elif abs(greeks.theta) < 0.1:
            analysis['time_decay_impact'] = 'LOW'
        
        # Volatility sensitivity
        if greeks.vega > 0.5:
            analysis['volatility_sensitivity'] = 'HIGH'
            analysis['recommendations'].append('High vega - position sensitive to IV changes')
        elif greeks.vega < 0.1:
            analysis['volatility_sensitivity'] = 'LOW'
        
        # Strategy recommendations
        if greeks.gamma > 0.03 and abs(greeks.theta) > 0.3:
            analysis['recommendations'].append('Consider selling options (positive theta)')
        
        if greeks.vega > 0.4 and greeks.volga > 0:
            analysis['recommendations'].append('Position benefits from volatility increases')
        
        return analysis


# ═══════════════════════════════════════════════════════════════════════════════
# CRYPTO OPTIONS ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class CryptoOptionsAnalyzer:
    """
    Specialized analyzer for crypto options (Deribit, Binance Options, etc.)
    """
    
    def __init__(self):
        self.greeks_calc = GeniusOptionsGreeks()
        
        # Default crypto parameters
        self.default_risk_free_rate = 0.05  # 5% (conservative)
        self.default_dividend_yield = 0.0   # Crypto has no dividends
    
    def analyze_btc_option(
        self,
        spot_price: float,
        strike: float,
        days_to_expiry: int,
        volatility: float,  # As decimal (0.80 = 80%)
        option_type: str = 'call'
    ) -> Dict[str, Any]:
        """
        Analyze a BTC option
        
        Args:
            spot_price: Current BTC price
            strike: Strike price
            days_to_expiry: Days until expiration
            volatility: IV as decimal
            option_type: 'call' or 'put'
        """
        
        opt_type = OptionType.CALL if option_type.lower() == 'call' else OptionType.PUT
        T = days_to_expiry / 365
        
        # Calculate price
        price = self.greeks_calc.black_scholes_price(
            S=spot_price,
            K=strike,
            T=T,
            r=self.default_risk_free_rate,
            sigma=volatility,
            q=self.default_dividend_yield,
            option_type=opt_type
        )
        
        # Calculate all Greeks
        greeks = self.greeks_calc.calculate_all_greeks(
            S=spot_price,
            K=strike,
            T=T,
            r=self.default_risk_free_rate,
            sigma=volatility,
            q=self.default_dividend_yield,
            option_type=opt_type
        )
        
        # Moneyness
        if opt_type == OptionType.CALL:
            moneyness = "ITM" if spot_price > strike else ("ATM" if abs(spot_price - strike) / strike < 0.02 else "OTM")
        else:
            moneyness = "ITM" if spot_price < strike else ("ATM" if abs(spot_price - strike) / strike < 0.02 else "OTM")
        
        # Probability of profit (approximate)
        prob_itm = abs(greeks.delta) if opt_type == OptionType.CALL else abs(greeks.delta)
        
        # Get trading analysis
        analysis = self.greeks_calc.analyze_greeks_for_trading(greeks, opt_type)
        
        return {
            'symbol': 'BTC',
            'type': option_type.upper(),
            'spot': spot_price,
            'strike': strike,
            'expiry_days': days_to_expiry,
            'iv': volatility,
            'moneyness': moneyness,
            'price': price,
            'greeks': greeks.to_dict(),
            'prob_itm': prob_itm,
            'analysis': analysis
        }
    
    def create_greeks_summary(self, results: List[Dict]) -> str:
        """Create a formatted summary of Greeks analysis"""
        
        summary = []
        summary.append("=" * 60)
        summary.append("OPTIONS GREEKS ANALYSIS")
        summary.append("=" * 60)
        
        for r in results:
            summary.append(f"\n{r['symbol']} {r['type']} ${r['strike']:,.0f} ({r['moneyness']})")
            summary.append(f"  Spot: ${r['spot']:,.2f} | IV: {r['iv']*100:.1f}% | Days: {r['expiry_days']}")
            summary.append(f"  Price: ${r['price']:,.2f}")
            summary.append(f"  Delta: {r['greeks']['delta']:+.4f} | Gamma: {r['greeks']['gamma']:.6f}")
            summary.append(f"  Theta: ${r['greeks']['theta']:,.4f}/day | Vega: ${r['greeks']['vega']:.4f}")
            summary.append(f"  P(ITM): {r['prob_itm']*100:.1f}%")
        
        return "\n".join(summary)


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demo Options Greeks calculations"""
    
    print("=" * 70)
    print("📊 GENIUS OPTIONS GREEKS v1.0 - DEMO")
    print("=" * 70)
    
    # Initialize calculator
    greeks_calc = GeniusOptionsGreeks()
    crypto_analyzer = CryptoOptionsAnalyzer()
    
    # Example: BTC Call Option
    print("\n🪙 BTC CALL OPTION ANALYSIS")
    print("-" * 50)
    
    spot = 97500       # Current BTC price
    strike = 100000    # Strike price
    days = 30          # Days to expiry
    iv = 0.65          # 65% implied volatility
    r = 0.05           # 5% risk-free rate
    
    T = days / 365
    
    # Calculate price
    call_price = greeks_calc.black_scholes_price(
        S=spot, K=strike, T=T, r=r, sigma=iv,
        option_type=OptionType.CALL
    )
    
    put_price = greeks_calc.black_scholes_price(
        S=spot, K=strike, T=T, r=r, sigma=iv,
        option_type=OptionType.PUT
    )
    
    print(f"   Spot Price:     ${spot:,.2f}")
    print(f"   Strike Price:   ${strike:,.2f}")
    print(f"   Days to Expiry: {days}")
    print(f"   IV:             {iv*100:.1f}%")
    print(f"   Risk-Free Rate: {r*100:.1f}%")
    print(f"\n   CALL Price:     ${call_price:,.2f}")
    print(f"   PUT Price:      ${put_price:,.2f}")
    
    # Calculate all Greeks for CALL
    print("\n📈 CALL OPTION GREEKS:")
    print("-" * 50)
    
    call_greeks = greeks_calc.calculate_all_greeks(
        S=spot, K=strike, T=T, r=r, sigma=iv,
        option_type=OptionType.CALL
    )
    
    print(f"   Δ Delta:  {call_greeks.delta:+.4f}  (price sensitivity)")
    print(f"   Γ Gamma:  {call_greeks.gamma:.6f}  (delta sensitivity)")
    print(f"   Θ Theta:  ${call_greeks.theta:.4f}/day  (time decay)")
    print(f"   ν Vega:   ${call_greeks.vega:.4f}  (volatility sensitivity)")
    print(f"   ρ Rho:    ${call_greeks.rho:.4f}  (rate sensitivity)")
    print(f"\n   Higher-Order Greeks:")
    print(f"   Ω Lambda: {call_greeks.lambda_:.2f}x  (leverage)")
    print(f"   Vanna:    {call_greeks.vanna:.6f}")
    print(f"   Volga:    {call_greeks.volga:.6f}")
    print(f"   Charm:    {call_greeks.charm:.6f}/day")
    print(f"   Speed:    {call_greeks.speed:.8f}")
    
    # Calculate all Greeks for PUT
    print("\n📉 PUT OPTION GREEKS:")
    print("-" * 50)
    
    put_greeks = greeks_calc.calculate_all_greeks(
        S=spot, K=strike, T=T, r=r, sigma=iv,
        option_type=OptionType.PUT
    )
    
    print(f"   Δ Delta:  {put_greeks.delta:+.4f}")
    print(f"   Γ Gamma:  {put_greeks.gamma:.6f}")
    print(f"   Θ Theta:  ${put_greeks.theta:.4f}/day")
    print(f"   ν Vega:   ${put_greeks.vega:.4f}")
    print(f"   ρ Rho:    ${put_greeks.rho:.4f}")
    
    # Implied Volatility calculation
    print("\n🎯 IMPLIED VOLATILITY SOLVER:")
    print("-" * 50)
    
    market_price = 5000  # Observed market price
    iv_solved = greeks_calc.implied_volatility(
        market_price=market_price,
        S=spot, K=strike, T=T, r=r,
        option_type=OptionType.CALL
    )
    print(f"   Market Price: ${market_price:,.2f}")
    print(f"   Implied IV:   {iv_solved*100:.2f}%")
    
    # Crypto analyzer
    print("\n🔍 CRYPTO OPTIONS ANALYZER:")
    print("-" * 50)
    
    result = crypto_analyzer.analyze_btc_option(
        spot_price=97500,
        strike=100000,
        days_to_expiry=30,
        volatility=0.65,
        option_type='call'
    )
    
    print(f"   Moneyness: {result['moneyness']}")
    print(f"   P(ITM):    {result['prob_itm']*100:.1f}%")
    print(f"   Analysis:  {result['analysis']['directional_bias']}")
    for rec in result['analysis']['recommendations'][:2]:
        print(f"   • {rec}")
    
    print("\n" + "=" * 70)
    print("✅ Options Greeks calculator ready!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    demo()
