"""Genius Quant Engine
----------------------
Aggregates premium quant libraries (ffn, FinancePy, QuantPy, py_vollib, pysabr, quantsbin,
finoptions, willowtree, pynance, gs-quant, qfin, optlib, tf-quant-finance, etc.) to produce
advanced market intelligence for the Genius Hamster backend.

Each dependency is optional – the engine degrades gracefully when a library is missing or raises
an import/runtime error. The goal is to surface as much structured insight as possible while
maintaining resilience in production deployments where some quant stacks might be unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import logging
import math
import time

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency loader
# ---------------------------------------------------------------------------

@dataclass
class OptionalDependency:
    """Holds import status for a single library."""

    name: str
    module: Optional[Any]
    error: Optional[str] = None

    @property
    def available(self) -> bool:
        return self.module is not None


def _load_optional_dependency(module_name: str, alias: Optional[str] = None) -> OptionalDependency:
    """Attempt to import a module, returning metadata without raising."""

    try:
        module = __import__(module_name, fromlist=["*"]) if alias else __import__(module_name)
        return OptionalDependency(name=alias or module_name, module=module)
    except Exception as exc:  # pragma: no cover - defensive logging only
        logger.debug("Optional dependency %s unavailable: %s", module_name, exc)
        return OptionalDependency(name=alias or module_name, module=None, error=str(exc))


class GeniusQuantEngine:
    """Central orchestrator that powers the Genius Hamster quant intelligence layer."""

    LIBRARIES = {
        "ffn": ("ffn", None),
        "py_vollib": ("py_vollib", None),
        "pysabr": ("pysabr", None),
        "FinancePy": ("FinancePy", None),
        "quantpy": ("quantpy", None),
        "quantsbin": ("quantsbin", None),
        "finoptions": ("finoptions", None),
        "willowtree": ("willowtree", None),
        "pynance": ("pynance", None),
        "gs_quant": ("gs_quant", None),
        "qfin": ("qfin", None),
        "optlib": ("optlib", None),
        "finance_python": ("finance_python", None),
        "tf_quant_finance": ("tf_quant_finance", None),
    }

    def __init__(self, requests_session: Optional[requests.Session] = None) -> None:
        self.session = requests_session or requests.Session()
        self.session.headers.update({"User-Agent": "GeniusHamster/2.0"})
        self.dependencies = {
            name: _load_optional_dependency(module_name, alias=name)
            for name, (module_name, _) in self.LIBRARIES.items()
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_market(self, symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 500) -> Dict[str, Any]:
        """Build full quant insight payload for the requested trading symbol."""

        analysis: Dict[str, Any] = {
            "symbol": symbol,
            "generated_at": int(time.time()),
            "library_status": {name: dep.available for name, dep in self.dependencies.items()},
            "insights": {},
            "warnings": [],
        }

        prices_df = self._fetch_price_series(symbol, interval=interval, limit=limit)
        if prices_df is None or prices_df.empty:
            analysis["warnings"].append("PRICE_SERIES_NOT_AVAILABLE")
            return analysis

        prices = prices_df["close"].astype(float)
        prices.index = pd.to_datetime(prices_df["open_time"], unit="ms")
        returns = prices.pct_change().dropna()

        base_metrics = self._compute_base_metrics(prices, returns)
        analysis["insights"]["performance"] = base_metrics

        ffn_metrics = self._compute_ffn_metrics(prices)
        if ffn_metrics:
            analysis["insights"]["ffn"] = ffn_metrics
        else:
            analysis["warnings"].append("FFN_METRICS_UNAVAILABLE")

        analysis["insights"]["risk"] = self._compute_risk_metrics(returns)
        options_metrics, option_warnings = self._compute_option_metrics(prices.iloc[-1])
        analysis["insights"]["options"] = options_metrics
        analysis["warnings"].extend(option_warnings)

        quantpy_metrics = self._compute_quantpy_metrics(returns)
        if quantpy_metrics:
            analysis["insights"]["quantpy"] = quantpy_metrics

        financepy_metrics = self._compute_financepy_metrics(prices.iloc[-1])
        if financepy_metrics:
            analysis["insights"]["financepy"] = financepy_metrics

        library_issues = self._collect_library_issues()
        if library_issues:
            analysis["library_notes"] = library_issues

        return analysis

    # ------------------------------------------------------------------
    # Data acquisition helpers
    # ------------------------------------------------------------------

    def _fetch_price_series(self, symbol: str, interval: str, limit: int) -> Optional[pd.DataFrame]:
        """Load historical candles from Binance public API."""

        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        try:
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            klines = response.json()
            df = pd.DataFrame(
                klines,
                columns=[
                    "open_time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_volume",
                    "trades",
                    "taker_buy_volume",
                    "taker_buy_quote",
                    "ignore",
                ],
            )
            return df
        except Exception as exc:  # pragma: no cover - network/HTTP issues only
            logger.warning("Failed to fetch klines for %s: %s", symbol, exc)
            return None

    # ------------------------------------------------------------------
    # Base analytics
    # ------------------------------------------------------------------

    def _compute_base_metrics(self, prices: pd.Series, returns: pd.Series) -> Dict[str, Any]:
        """Plain pandas/numpy metrics – always available."""

        daily_vol = float(returns.std() * math.sqrt(24))  # interval is 1h → 24 periods per day
        sharpe = (
            (returns.mean() * 24) / (returns.std() * math.sqrt(24))
            if returns.std() > 0
            else 0.0
        )
        drawdown = float((prices.cummax() - prices).max())

        return {
            "last_price": float(prices.iloc[-1]),
            "daily_volatility": daily_vol,
            "hourly_mean_return": float(returns.mean()),
            "sharpe_like": sharpe,
            "max_drawdown_abs": drawdown,
            "periods": len(prices),
        }

    def _compute_risk_metrics(self, returns: pd.Series) -> Dict[str, Any]:
        """Basic risk analytics (VaR/ES) with numpy fallback."""

        if returns.empty:
            return {"value_at_risk": None, "expected_shortfall": None}

        percentile = 5
        var = float(np.percentile(returns, percentile))
        es = float(returns[returns <= var].mean()) if not returns[returns <= var].empty else float(var)
        return {
            "horizon": "1h",
            "confidence": 1 - percentile / 100,
            "value_at_risk": var,
            "expected_shortfall": es,
        }

    # ------------------------------------------------------------------
    # Optional-library analytics
    # ------------------------------------------------------------------

    def _compute_ffn_metrics(self, prices: pd.Series) -> Optional[Dict[str, Any]]:
        dep = self.dependencies.get("ffn")
        if not dep or not dep.available:
            return None

        try:
            # Import inside the method so pandas gets monkey-patched by ffn
            import ffn  # type: ignore

            stats = ffn.core.PerformanceStats(prices.astype(float))
            calc_stats = stats.calc_stats()
            stats_dict = calc_stats.stats if hasattr(calc_stats, "stats") else stats.stats
            return {
                "cagr": float(stats_dict.get("cagr", 0.0)),
                "volatility": float(stats_dict.get("daily_vol", 0.0)),
                "sortino": float(stats_dict.get("daily_sortino", 0.0)),
                "calmar": float(stats_dict.get("calmar", 0.0)),
            }
        except Exception as exc:  # pragma: no cover - relies on third-party internals
            logger.warning("ffn metric computation failed: %s", exc)
            return None

    def _compute_option_metrics(self, spot_price: float) -> Tuple[Dict[str, Any], List[str]]:
        """Gather option/vol analytics from multiple quant libraries if available."""

        results: Dict[str, Any] = {}
        warnings: List[str] = []
        risk_free = 0.02
        maturity = 30 / 365
        strike = spot_price * 1.02

        # py_vollib Black-Scholes pricing & Greeks
        dep_vollib = self.dependencies.get("py_vollib")
        if dep_vollib and dep_vollib.available:
            try:
                from py_vollib.black_scholes import black_scholes  # type: ignore
                from py_vollib.black_scholes.greeks.analytical import delta  # type: ignore

                implied_vol = 0.55
                call_price = black_scholes("c", spot_price, strike, maturity, risk_free, implied_vol)
                put_price = black_scholes("p", spot_price, strike, maturity, risk_free, implied_vol)
                results["py_vollib"] = {
                    "call_price": float(call_price),
                    "put_price": float(put_price),
                    "delta_call": float(delta("c", spot_price, strike, maturity, risk_free, implied_vol)),
                }
            except Exception as exc:  # pragma: no cover - library-specific behaviour
                warnings.append(f"PY_VOLLIB_ERROR: {exc}")

        # pysabr – SABR implied vol surface snapshot
        dep_sabr = self.dependencies.get("pysabr")
        if dep_sabr and dep_sabr.available:
            try:
                from pysabr import hagan  # type: ignore

                sabr_vol = hagan.implied_volatility(
                    "lognormal",
                    spot_price,
                    strike,
                    maturity,
                    alpha=0.4,
                    beta=0.5,
                    rho=-0.2,
                    nu=0.6,
                )
                results["pysabr"] = {"sabr_volatility": float(sabr_vol)}
            except Exception as exc:  # pragma: no cover
                warnings.append(f"PYSABR_ERROR: {exc}")

        # quantsbin – European option pricing (Black-Scholes)
        dep_quantsbin = self.dependencies.get("quantsbin")
        if dep_quantsbin and dep_quantsbin.available:
            try:
                from quantsbin.derivative import EquityOption  # type: ignore

                opt = EquityOption(
                    strike=strike,
                    expiry=maturity,
                    spot0=spot_price,
                    option_type="call",
                    dividend_yield=0.0,
                    option_style="european",
                )
                qb_res = opt.price(method="black_scholes", sigma=0.5, r=risk_free)
                results["quantsbin"] = {
                    "price": float(qb_res.get("price", 0.0)),
                    "vega": float(qb_res.get("vega", 0.0)),
                }
            except Exception as exc:  # pragma: no cover
                warnings.append(f"QUANTSBIN_ERROR: {exc}")

        # finoptions – vanilla Black/Scholes payoff
        dep_finoptions = self.dependencies.get("finoptions")
        if dep_finoptions and dep_finoptions.available:
            try:
                from finoptions import black_scholes_option

                bs = black_scholes_option(
                    S=spot_price,
                    K=strike,
                    r=risk_free,
                    sigma=0.5,
                    t=maturity,
                    option_type="call",
                )
                results["finoptions"] = {
                    "value": float(bs["value"]) if isinstance(bs, dict) else float(bs),
                }
            except Exception as exc:  # pragma: no cover
                warnings.append(f"FINOPTIONS_ERROR: {exc}")

        # willowtree – binomial lattice pricing (if installed)
        dep_willow = self.dependencies.get("willowtree")
        if dep_willow and dep_willow.available:
            try:
                from willowtree import binomial

                wt_price = binomial.option_price(
                    spot_price,
                    strike,
                    maturity,
                    risk_free,
                    0.5,
                    steps=100,
                    option_type="call",
                )
                results["willowtree"] = {"binomial_price": float(wt_price)}
            except Exception as exc:  # pragma: no cover
                warnings.append(f"WILLOWTREE_ERROR: {exc}")

        return results, warnings

    def _compute_quantpy_metrics(self, returns: pd.Series) -> Optional[Dict[str, Any]]:
        dep = self.dependencies.get("quantpy")
        if not dep or not dep.available:
            return None

        try:
            from quantpy import utils  # type: ignore

            skew = float(utils.skewness(returns.values)) if hasattr(utils, "skewness") else float(returns.skew())
            kurt = float(utils.kurtosis(returns.values)) if hasattr(utils, "kurtosis") else float(returns.kurt())
            return {"skew": skew, "kurtosis": kurt}
        except Exception as exc:  # pragma: no cover
            logger.warning("QuantPy metrics failed: %s", exc)
            return None

    def _compute_financepy_metrics(self, spot_price: float) -> Optional[Dict[str, Any]]:
        dep = self.dependencies.get("FinancePy")
        if not dep or not dep.available:
            return None

        try:
            from FinancePy.market.curves.discount_curve_flat import DiscountCurveFlat  # type: ignore
            from FinancePy.products.equity.equity_option import EquityOption  # type: ignore

            curve = DiscountCurveFlat(0.0, 0.02)
            option = EquityOption("CALL", strike=spot_price * 1.02, expiry=30 / 365)
            value = option.price(spot_price, curve, sigma=0.5)
            return {"equity_option_price": float(value)}
        except Exception as exc:  # pragma: no cover
            logger.warning("FinancePy metrics failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------

    def _collect_library_issues(self) -> List[str]:
        issues: List[str] = []
        for name, dep in self.dependencies.items():
            if not dep.available and dep.error:
                issues.append(f"{name}: {dep.error}")
        return issues


__all__ = ["GeniusQuantEngine"]
