"""
🏛️ INSTITUTIONAL EDGE ENGINE
=============================
Moduł na poziomie funduszu hedgingowego.

WYKORZYSTUJE:
- hmmlearn: Hidden Markov Model (wykrywanie ukrytych stanów rynku)
- scipy: Kelly Criterion (optymalna wielkość pozycji)
- numpy: Microstructure analysis
- sklearn: Adaptive learning

CO ROBIĄ INSTYTUCJE, CZEGO NIE ROBIĄ RETAIL:
1. Kelly Criterion - matematycznie optymalna wielkość pozycji
2. Hidden Markov Models - wykrywanie "ukrytych" stanów rynku
3. Microstructure Analysis - analiza spreadu, imbalance, toxicity
4. Smart Execution - TWAP, VWAP, minimalizacja slippage
5. Alpha Decay Monitoring - czy strategia traci edge?

Autor: Genius Trading System
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# KELLY CRITERION - OPTYMALNA WIELKOŚĆ POZYCJI
# ═══════════════════════════════════════════════════════════════

class KellyCriterion:
    """
    🎯 Kelly Criterion - Matematycznie Optymalna Wielkość Pozycji
    
    DLACZEGO TO WAŻNE:
    - Za mała pozycja = tracisz potencjalny zysk
    - Za duża pozycja = ryzyko ruiny
    - Kelly = OPTYMALNY balans
    
    Instytucje używają "Fractional Kelly" (25-50% pełnego Kelly)
    dla bezpieczeństwa.
    """
    
    def __init__(self, 
                 win_rate: float = 0.55,
                 avg_win: float = 0.03,
                 avg_loss: float = 0.01,
                 kelly_fraction: float = 0.25):  # Konserwatywne 25%
        """
        Args:
            win_rate: Procent wygranych (0.55 = 55%)
            avg_win: Średni zysk (0.03 = 3%)
            avg_loss: Średnia strata (0.01 = 1%)
            kelly_fraction: Ułamek Kelly (0.25 = ćwierć Kelly)
        """
        self.win_rate = win_rate
        self.avg_win = avg_win
        self.avg_loss = avg_loss
        self.kelly_fraction = kelly_fraction
        
        # Historia do adaptacji
        self.trade_history: List[Dict] = []
        
    def calculate_full_kelly(self) -> float:
        """
        Oblicza pełny Kelly Criterion.
        
        Formula: f* = (p * b - q) / b
        gdzie:
            p = prawdopodobieństwo wygranej
            q = prawdopodobieństwo przegranej (1-p)
            b = stosunek wygranej do przegranej (win/loss ratio)
        """
        if self.avg_loss == 0:
            return 0
            
        p = self.win_rate
        q = 1 - p
        b = self.avg_win / self.avg_loss
        
        kelly = (p * b - q) / b
        
        # Kelly nie może być ujemny ani większy niż 1
        return max(0, min(1, kelly))
    
    def get_optimal_position_size(self, 
                                   capital: float,
                                   confidence: float = 1.0) -> Dict:
        """
        Zwraca optymalną wielkość pozycji.
        
        Args:
            capital: Dostępny kapitał
            confidence: Pewność sygnału (0-1)
            
        Returns:
            Dict z rekomendacją
        """
        full_kelly = self.calculate_full_kelly()
        
        # Fractional Kelly (bezpieczniejszy)
        fractional = full_kelly * self.kelly_fraction
        
        # Dostosuj do pewności sygnału
        adjusted = fractional * confidence
        
        # Oblicz kwotę
        position_size = capital * adjusted
        
        # Limity bezpieczeństwa
        max_position = capital * 0.05  # Max 5% kapitału na trade
        position_size = min(position_size, max_position)
        
        return {
            'full_kelly': full_kelly,
            'fractional_kelly': fractional,
            'adjusted_kelly': adjusted,
            'position_size_usd': round(position_size, 2),
            'position_pct': round(adjusted * 100, 2),
            'risk_level': self._get_risk_level(adjusted),
            'recommendation': self._get_recommendation(adjusted, confidence)
        }
    
    def update_from_trade(self, profit_pct: float, won: bool):
        """Aktualizuje statystyki po trade."""
        self.trade_history.append({
            'profit_pct': profit_pct,
            'won': won,
            'timestamp': datetime.now()
        })
        
        # Przelicz statystyki z ostatnich 100 tradów
        if len(self.trade_history) >= 10:
            recent = self.trade_history[-100:]
            wins = [t for t in recent if t['won']]
            losses = [t for t in recent if not t['won']]
            
            if len(recent) > 0:
                self.win_rate = len(wins) / len(recent)
            if wins:
                self.avg_win = np.mean([t['profit_pct'] for t in wins])
            if losses:
                self.avg_loss = abs(np.mean([t['profit_pct'] for t in losses]))
    
    def _get_risk_level(self, kelly: float) -> str:
        if kelly < 0.01:
            return 'minimal'
        elif kelly < 0.02:
            return 'low'
        elif kelly < 0.03:
            return 'medium'
        elif kelly < 0.05:
            return 'elevated'
        else:
            return 'high'
    
    def _get_recommendation(self, kelly: float, conf: float) -> str:
        if kelly < 0.005 or conf < 0.5:
            return "SKIP - Zbyt niski edge"
        elif kelly < 0.015:
            return "SMALL - Mała pozycja (1 dokładka)"
        elif kelly < 0.03:
            return "NORMAL - Standardowa pozycja"
        else:
            return "STRONG - Mocny sygnał, można piramidować"


# ═══════════════════════════════════════════════════════════════
# HIDDEN MARKOV MODEL - WYKRYWANIE UKRYTYCH STANÓW RYNKU
# ═══════════════════════════════════════════════════════════════

class MarketRegimeHMM:
    """
    🔮 Hidden Markov Model - Wykrywanie Ukrytych Stanów Rynku
    
    STANY RYNKU (ukryte):
    0 = LOW_VOLATILITY_BULL (spokojny wzrost)
    1 = HIGH_VOLATILITY_BULL (gwałtowny wzrost)
    2 = LOW_VOLATILITY_BEAR (spokojny spadek)
    3 = HIGH_VOLATILITY_BEAR (panika)
    4 = CONSOLIDATION (range)
    
    PRZEWAGA: HMM "widzi" przejścia między stanami ZANIM stają się
    oczywiste na wykresie!
    """
    
    def __init__(self, n_states: int = 4):
        self.n_states = n_states
        self.model = None
        self.fitted = False
        self.state_names = {
            0: 'low_vol_bull',
            1: 'high_vol_bull', 
            2: 'low_vol_bear',
            3: 'high_vol_bear'
        }
        
        # Próbuj załadować hmmlearn
        try:
            from hmmlearn import hmm
            self.hmm_available = True
            self.model = hmm.GaussianHMM(
                n_components=n_states,
                covariance_type='full',
                n_iter=100,
                random_state=42
            )
            logger.info("✅ HMM (hmmlearn) loaded")
        except ImportError:
            self.hmm_available = False
            logger.warning("⚠️ hmmlearn not available, using simplified regime detection")
    
    def prepare_features(self, prices: pd.Series) -> np.ndarray:
        """Przygotowuje features dla HMM."""
        returns = prices.pct_change().dropna()
        
        # Feature 1: Returns
        ret = returns.values
        
        # Feature 2: Volatility (rolling std)
        vol = returns.rolling(20).std().dropna().values
        
        # Feature 3: Momentum (ROC)
        mom = prices.pct_change(10).dropna().values
        
        # Wyrównaj długości
        min_len = min(len(ret), len(vol), len(mom))
        
        features = np.column_stack([
            ret[-min_len:],
            vol[-min_len:] if len(vol) >= min_len else np.zeros(min_len),
            mom[-min_len:] if len(mom) >= min_len else np.zeros(min_len)
        ])
        
        # Usuń NaN i Inf
        features = np.nan_to_num(features, nan=0, posinf=0, neginf=0)
        
        return features
    
    def fit(self, prices: pd.Series):
        """Trenuje model HMM na danych historycznych."""
        if not self.hmm_available:
            return
            
        features = self.prepare_features(prices)
        
        if len(features) < 50:
            logger.warning("Za mało danych do treningu HMM")
            return
            
        try:
            self.model.fit(features)
            self.fitted = True
            logger.info("✅ HMM model fitted successfully")
        except Exception as e:
            logger.error(f"HMM fit error: {e}")
    
    def predict_regime(self, prices: pd.Series) -> Dict:
        """
        Przewiduje aktualny reżim rynku.
        
        Returns:
            Dict z predykcją i prawdopodobieństwami
        """
        if not self.hmm_available or not self.fitted:
            return self._fallback_regime_detection(prices)
        
        features = self.prepare_features(prices)
        
        if len(features) < 10:
            return self._fallback_regime_detection(prices)
        
        try:
            # Predykcja stanu
            states = self.model.predict(features)
            current_state = states[-1]
            
            # Prawdopodobieństwa stanów
            probs = self.model.predict_proba(features)
            current_probs = probs[-1]
            
            # Macierz przejść
            transition_matrix = self.model.transmat_
            
            # Prawdopodobieństwo przejścia do innego stanu
            transition_probs = transition_matrix[current_state]
            
            # Najbardziej prawdopodobny następny stan
            next_state = np.argmax(transition_probs)
            
            return {
                'current_regime': self.state_names.get(current_state, 'unknown'),
                'regime_id': int(current_state),
                'confidence': float(current_probs[current_state]),
                'state_probabilities': {
                    self.state_names[i]: float(p) 
                    for i, p in enumerate(current_probs)
                },
                'likely_next_regime': self.state_names.get(next_state, 'unknown'),
                'transition_probability': float(transition_probs[next_state]),
                'regime_stability': float(transition_probs[current_state]),
                'trading_recommendation': self._get_trading_recommendation(
                    current_state, current_probs[current_state]
                )
            }
            
        except Exception as e:
            logger.error(f"HMM predict error: {e}")
            return self._fallback_regime_detection(prices)
    
    def _fallback_regime_detection(self, prices: pd.Series) -> Dict:
        """Uproszczona detekcja reżimu gdy HMM niedostępny."""
        returns = prices.pct_change().dropna()
        
        if len(returns) < 20:
            return {
                'current_regime': 'unknown',
                'confidence': 0.5,
                'trading_recommendation': 'WAIT'
            }
        
        # Prosty model bazujący na momentum i volatility
        avg_return = returns.tail(20).mean()
        volatility = returns.tail(20).std()
        
        high_vol = volatility > returns.std() * 1.5
        bullish = avg_return > 0
        
        if bullish and not high_vol:
            regime = 'low_vol_bull'
            conf = 0.7
        elif bullish and high_vol:
            regime = 'high_vol_bull'
            conf = 0.6
        elif not bullish and not high_vol:
            regime = 'low_vol_bear'
            conf = 0.7
        else:
            regime = 'high_vol_bear'
            conf = 0.6
        
        return {
            'current_regime': regime,
            'confidence': conf,
            'trading_recommendation': self._get_trading_recommendation_simple(regime)
        }
    
    def _get_trading_recommendation(self, state: int, confidence: float) -> str:
        """Rekomendacja tradingowa na podstawie stanu HMM."""
        if confidence < 0.5:
            return "WAIT - Niestabilny reżim"
        
        recommendations = {
            0: "LONG_TREND - Spokojny trend wzrostowy, trzymaj pozycje",
            1: "SCALP_LONG - Wysoka zmienność w górę, szybkie wejścia",
            2: "SHORT_TREND - Spokojny trend spadkowy, szukaj shortów",
            3: "HEDGE - Panika! Zamknij longa lub hedguj"
        }
        return recommendations.get(state, "WAIT")
    
    def _get_trading_recommendation_simple(self, regime: str) -> str:
        """Rekomendacja dla uproszczonej detekcji."""
        recs = {
            'low_vol_bull': "LONG_TREND",
            'high_vol_bull': "SCALP_LONG", 
            'low_vol_bear': "SHORT_TREND",
            'high_vol_bear': "HEDGE"
        }
        return recs.get(regime, "WAIT")


# ═══════════════════════════════════════════════════════════════
# MICROSTRUCTURE ANALYSIS - ANALIZA MIKROSTRUKTURY RYNKU
# ═══════════════════════════════════════════════════════════════

class MicrostructureAnalyzer:
    """
    🔬 Market Microstructure Analysis
    
    ANALIZUJE:
    - Spread dynamics (szerokość spreadu = miara płynności)
    - Order imbalance (nierównowaga zleceń)
    - Trade toxicity (czy handlujemy z "informed traders"?)
    - Price impact estimation
    
    INSTYTUCJE używają tego do:
    - Wyboru momentu egzekucji (mniejszy spread = tańsze wejście)
    - Wykrywania manipulacji
    - Szacowania slippage przed trade'em
    """
    
    def __init__(self):
        self.spread_history: List[float] = []
        self.imbalance_history: List[float] = []
        
    def analyze_spread(self, bid: float, ask: float) -> Dict:
        """
        Analizuje spread i płynność.
        
        Args:
            bid: Najlepsza cena kupna
            ask: Najlepsza cena sprzedaży
        """
        if bid <= 0 or ask <= 0:
            return {'spread_pct': 0, 'liquidity': 'unknown'}
        
        mid = (bid + ask) / 2
        spread = ask - bid
        spread_pct = (spread / mid) * 100
        
        self.spread_history.append(spread_pct)
        if len(self.spread_history) > 1000:
            self.spread_history = self.spread_history[-1000:]
        
        # Porównaj z historycznym spreadem
        if len(self.spread_history) >= 20:
            avg_spread = np.mean(self.spread_history[-100:])
            spread_zscore = (spread_pct - avg_spread) / (np.std(self.spread_history[-100:]) + 1e-10)
        else:
            avg_spread = spread_pct
            spread_zscore = 0
        
        # Klasyfikacja płynności
        if spread_pct < 0.01:
            liquidity = 'excellent'
            exec_quality = 1.0
        elif spread_pct < 0.03:
            liquidity = 'good'
            exec_quality = 0.9
        elif spread_pct < 0.05:
            liquidity = 'moderate'
            exec_quality = 0.7
        elif spread_pct < 0.1:
            liquidity = 'poor'
            exec_quality = 0.5
        else:
            liquidity = 'very_poor'
            exec_quality = 0.3
        
        return {
            'spread_pct': round(spread_pct, 4),
            'spread_bps': round(spread_pct * 100, 2),  # Basis points
            'mid_price': mid,
            'liquidity': liquidity,
            'execution_quality': exec_quality,
            'spread_zscore': round(spread_zscore, 2),
            'is_wide_spread': spread_zscore > 2,
            'recommendation': self._spread_recommendation(spread_zscore, liquidity)
        }
    
    def analyze_order_imbalance(self, 
                                 bid_volume: float, 
                                 ask_volume: float) -> Dict:
        """
        Analizuje nierównowagę zleceń w orderbooku.
        
        Imbalance > 0 = więcej kupujących (bullish)
        Imbalance < 0 = więcej sprzedających (bearish)
        """
        total = bid_volume + ask_volume
        if total == 0:
            return {'imbalance': 0, 'signal': 'neutral'}
        
        imbalance = (bid_volume - ask_volume) / total
        
        self.imbalance_history.append(imbalance)
        if len(self.imbalance_history) > 500:
            self.imbalance_history = self.imbalance_history[-500:]
        
        # Analiza trendu imbalance
        if len(self.imbalance_history) >= 10:
            recent_avg = np.mean(self.imbalance_history[-10:])
            imbalance_momentum = imbalance - recent_avg
        else:
            imbalance_momentum = 0
        
        # Klasyfikacja
        if imbalance > 0.3:
            signal = 'strong_buy'
            strength = 1.0
        elif imbalance > 0.1:
            signal = 'buy'
            strength = 0.6
        elif imbalance < -0.3:
            signal = 'strong_sell'
            strength = -1.0
        elif imbalance < -0.1:
            signal = 'sell'
            strength = -0.6
        else:
            signal = 'neutral'
            strength = 0
        
        return {
            'imbalance': round(imbalance, 3),
            'imbalance_pct': round(imbalance * 100, 1),
            'signal': signal,
            'strength': strength,
            'bid_dominance': round((bid_volume / total) * 100, 1) if total > 0 else 50,
            'ask_dominance': round((ask_volume / total) * 100, 1) if total > 0 else 50,
            'momentum': round(imbalance_momentum, 3),
            'is_significant': abs(imbalance) > 0.2
        }
    
    def estimate_price_impact(self, 
                               order_size: float,
                               avg_volume: float,
                               volatility: float) -> Dict:
        """
        Szacuje wpływ zlecenia na cenę (slippage).
        
        Model: Impact = σ * √(V/ADV)
        gdzie:
            σ = volatility
            V = order size
            ADV = average daily volume
        """
        if avg_volume <= 0:
            return {'estimated_slippage_pct': 0.1, 'risk': 'unknown'}
        
        participation_rate = order_size / avg_volume
        
        # Square root law (używany przez instytucje)
        impact = volatility * np.sqrt(participation_rate)
        
        # Dodaj stały komponent (spread)
        total_impact = impact + 0.01  # 1 bps minimum
        
        if total_impact < 0.02:
            risk = 'low'
        elif total_impact < 0.05:
            risk = 'moderate'
        elif total_impact < 0.1:
            risk = 'high'
        else:
            risk = 'very_high'
        
        return {
            'estimated_slippage_pct': round(total_impact * 100, 3),
            'participation_rate': round(participation_rate * 100, 2),
            'risk': risk,
            'recommendation': f"{'OK' if risk in ['low', 'moderate'] else 'REDUCE SIZE'}"
        }
    
    def _spread_recommendation(self, zscore: float, liquidity: str) -> str:
        if liquidity in ['very_poor', 'poor'] or zscore > 2:
            return "WAIT - Słaba płynność, poczekaj na lepszy spread"
        elif liquidity == 'excellent':
            return "EXECUTE - Świetna płynność, wchodź teraz"
        else:
            return "OK - Akceptowalna płynność"


# ═══════════════════════════════════════════════════════════════
# ALPHA DECAY MONITOR - CZY STRATEGIA TRACI EDGE?
# ═══════════════════════════════════════════════════════════════

class AlphaDecayMonitor:
    """
    📉 Alpha Decay Monitor
    
    Monitoruje czy strategia traci swoją przewagę (alpha).
    
    DLACZEGO TO WAŻNE:
    - Rynki się zmieniają
    - Strategie "wypalają się" gdy inni je odkryją
    - Wczesne wykrycie decay = uniknięcie strat
    
    METRYKI:
    - Rolling Sharpe Ratio
    - Win Rate Trend
    - Drawdown Frequency
    - Edge Stability Index
    """
    
    def __init__(self, lookback_window: int = 100):
        self.lookback = lookback_window
        self.trade_results: List[Dict] = []
        self.sharpe_history: List[float] = []
        self.winrate_history: List[float] = []
        
    def log_trade(self, pnl_pct: float, holding_time_minutes: int):
        """Loguje wynik trade'u."""
        self.trade_results.append({
            'pnl_pct': pnl_pct,
            'won': pnl_pct > 0,
            'holding_time': holding_time_minutes,
            'timestamp': datetime.now()
        })
        
        # Trim to lookback
        if len(self.trade_results) > self.lookback * 2:
            self.trade_results = self.trade_results[-self.lookback * 2:]
    
    def analyze_alpha_decay(self) -> Dict:
        """
        Analizuje czy strategia traci edge.
        """
        if len(self.trade_results) < 20:
            return {
                'status': 'insufficient_data',
                'message': f'Potrzeba min. 20 tradów (masz: {len(self.trade_results)})'
            }
        
        results = self.trade_results
        
        # Split na dwie połowy
        mid = len(results) // 2
        first_half = results[:mid]
        second_half = results[mid:]
        
        # Win Rate comparison
        wr_first = sum(1 for t in first_half if t['won']) / len(first_half)
        wr_second = sum(1 for t in second_half if t['won']) / len(second_half)
        wr_change = wr_second - wr_first
        
        # Average PnL comparison
        pnl_first = np.mean([t['pnl_pct'] for t in first_half])
        pnl_second = np.mean([t['pnl_pct'] for t in second_half])
        pnl_change = pnl_second - pnl_first
        
        # Rolling Sharpe (uproszczony)
        pnls = [t['pnl_pct'] for t in results[-self.lookback:]]
        if len(pnls) >= 20:
            sharpe = np.mean(pnls) / (np.std(pnls) + 1e-10) * np.sqrt(252)
        else:
            sharpe = 0
        
        self.sharpe_history.append(sharpe)
        self.winrate_history.append(wr_second)
        
        # Trend analysis
        if len(self.sharpe_history) >= 5:
            sharpe_trend = np.polyfit(range(len(self.sharpe_history[-10:])), 
                                       self.sharpe_history[-10:], 1)[0]
        else:
            sharpe_trend = 0
        
        # Decay detection
        decay_signals = 0
        reasons = []
        
        if wr_change < -0.1:  # Win rate spadł o >10%
            decay_signals += 1
            reasons.append(f"Win Rate spadł: {wr_first:.1%} → {wr_second:.1%}")
        
        if pnl_change < -0.5:  # Średni PnL spadł o >0.5%
            decay_signals += 1
            reasons.append(f"Avg PnL spadł: {pnl_first:.2f}% → {pnl_second:.2f}%")
        
        if sharpe_trend < -0.1:  # Sharpe spada
            decay_signals += 1
            reasons.append("Sharpe Ratio w trendzie spadkowym")
        
        # Status
        if decay_signals >= 2:
            status = 'DECAY_DETECTED'
            action = "STOP TRADING - Przeanalizuj strategię!"
            health = 'critical'
        elif decay_signals == 1:
            status = 'WARNING'
            action = "REDUCE SIZE - Obserwuj uważnie"
            health = 'warning'
        else:
            status = 'HEALTHY'
            action = "CONTINUE - Strategia działa"
            health = 'good'
        
        return {
            'status': status,
            'health': health,
            'action': action,
            'metrics': {
                'win_rate_first_half': round(wr_first, 3),
                'win_rate_second_half': round(wr_second, 3),
                'win_rate_change': round(wr_change, 3),
                'avg_pnl_first': round(pnl_first, 3),
                'avg_pnl_second': round(pnl_second, 3),
                'rolling_sharpe': round(sharpe, 2),
                'sharpe_trend': round(sharpe_trend, 4),
                'total_trades': len(results)
            },
            'decay_signals': decay_signals,
            'reasons': reasons
        }


# ═══════════════════════════════════════════════════════════════
# SMART EXECUTION ENGINE - INTELIGENTNA EGZEKUCJA
# ═══════════════════════════════════════════════════════════════

class SmartExecutionEngine:
    """
    ⚡ Smart Order Execution
    
    STRATEGIE EGZEKUCJI:
    - TWAP (Time Weighted Average Price)
    - VWAP (Volume Weighted Average Price)
    - Iceberg (ukryte zlecenia)
    - Adaptive (dostosowuje się do warunków)
    
    MINIMALIZUJE:
    - Slippage
    - Market impact
    - Timing risk
    """
    
    def __init__(self, default_strategy: str = 'adaptive'):
        self.strategy = default_strategy
        self.execution_history: List[Dict] = []
        
    def plan_execution(self,
                       total_size: float,
                       urgency: str = 'normal',
                       market_conditions: Dict = None) -> Dict:
        """
        Planuje optymalną egzekucję zlecenia.
        
        Args:
            total_size: Całkowita wielkość pozycji (USD)
            urgency: 'low', 'normal', 'high'
            market_conditions: Info o rynku (spread, volatility)
        """
        if market_conditions is None:
            market_conditions = {}
        
        volatility = market_conditions.get('volatility', 'normal')
        spread_quality = market_conditions.get('spread_quality', 'good')
        
        # Wybór strategii
        if urgency == 'high':
            # Pilne - wejdź natychmiast
            strategy = 'market'
            chunks = 1
            interval = 0
        elif total_size < 100:
            # Mała pozycja - wejdź od razu
            strategy = 'market'
            chunks = 1
            interval = 0
        elif volatility == 'high' or spread_quality == 'poor':
            # Zła płynność - używaj TWAP
            strategy = 'twap'
            chunks = 5
            interval = 60  # 1 minuta między chunk'ami
        else:
            # Normalne warunki - adaptive
            strategy = 'adaptive'
            chunks = 3
            interval = 30
        
        chunk_size = total_size / chunks
        
        return {
            'strategy': strategy,
            'total_size': total_size,
            'chunks': chunks,
            'chunk_size': round(chunk_size, 2),
            'interval_seconds': interval,
            'estimated_time': chunks * interval,
            'order_type': 'limit' if strategy != 'market' else 'market',
            'execution_plan': self._create_execution_plan(strategy, chunks, chunk_size, interval)
        }
    
    def _create_execution_plan(self, strategy: str, chunks: int, chunk_size: float, interval: int) -> List[Dict]:
        """Tworzy szczegółowy plan egzekucji."""
        plan = []
        
        for i in range(chunks):
            order = {
                'chunk_number': i + 1,
                'size': chunk_size,
                'delay_seconds': i * interval,
                'order_type': 'limit' if strategy in ['twap', 'adaptive'] else 'market'
            }
            
            if strategy == 'twap':
                order['price_adjustment'] = 0  # Po mid price
            elif strategy == 'adaptive':
                order['price_adjustment'] = -0.01 if i > 0 else 0  # Lepsze ceny dla kolejnych
            
            plan.append(order)
        
        return plan
    
    def get_slippage_stats(self) -> Dict:
        """Zwraca statystyki slippage z historii."""
        if not self.execution_history:
            return {'avg_slippage': 0, 'max_slippage': 0, 'trades': 0}
        
        slippages = [e.get('slippage_pct', 0) for e in self.execution_history]
        
        return {
            'avg_slippage': round(np.mean(slippages), 4),
            'max_slippage': round(max(slippages), 4),
            'min_slippage': round(min(slippages), 4),
            'trades': len(self.execution_history)
        }


# ═══════════════════════════════════════════════════════════════
# MAIN INSTITUTIONAL ENGINE
# ═══════════════════════════════════════════════════════════════

class InstitutionalEdgeEngine:
    """
    🏛️ GŁÓWNY SILNIK INSTITUTIONAL EDGE
    
    Łączy wszystkie komponenty instytucjonalne:
    - Kelly Criterion (position sizing)
    - Hidden Markov Model (regime detection)
    - Microstructure Analysis (liquidity)
    - Alpha Decay Monitor (strategy health)
    - Smart Execution (order routing)
    """
    
    def __init__(self, capital: float = 5000):
        self.capital = capital
        
        # Komponenty
        self.kelly = KellyCriterion(kelly_fraction=0.25)
        self.hmm = MarketRegimeHMM(n_states=4)
        self.microstructure = MicrostructureAnalyzer()
        self.alpha_monitor = AlphaDecayMonitor()
        self.execution = SmartExecutionEngine()
        
        logger.info("🏛️ InstitutionalEdgeEngine initialized")
        
    def full_analysis(self,
                      prices: pd.Series,
                      bid: float,
                      ask: float,
                      bid_volume: float,
                      ask_volume: float,
                      signal_confidence: float) -> Dict:
        """
        Pełna analiza instytucjonalna.
        
        Returns:
            Kompletna rekomendacja z wszystkich modułów
        """
        results = {}
        
        # 1. Regime Detection (HMM)
        if len(prices) >= 50:
            if not self.hmm.fitted:
                self.hmm.fit(prices)
            results['regime'] = self.hmm.predict_regime(prices)
        else:
            results['regime'] = {'current_regime': 'unknown', 'confidence': 0.5}
        
        # 2. Kelly Position Sizing
        results['position_sizing'] = self.kelly.get_optimal_position_size(
            self.capital, signal_confidence
        )
        
        # 3. Microstructure Analysis
        results['spread'] = self.microstructure.analyze_spread(bid, ask)
        results['imbalance'] = self.microstructure.analyze_order_imbalance(
            bid_volume, ask_volume
        )
        
        # 4. Alpha Decay Check
        results['alpha_health'] = self.alpha_monitor.analyze_alpha_decay()
        
        # 5. Execution Plan
        position_size = results['position_sizing']['position_size_usd']
        results['execution'] = self.execution.plan_execution(
            position_size,
            urgency='normal',
            market_conditions={
                'spread_quality': results['spread']['liquidity'],
                'volatility': 'high' if 'high_vol' in results['regime'].get('current_regime', '') else 'normal'
            }
        )
        
        # 6. Final Signal
        results['final_recommendation'] = self._combine_signals(results, signal_confidence)
        
        return results
    
    def _combine_signals(self, results: Dict, base_confidence: float) -> Dict:
        """Łączy wszystkie sygnały w finalną rekomendację."""
        
        # Modyfikatory
        confidence_mods = []
        
        # Regime modifier
        regime = results.get('regime', {}).get('current_regime', 'unknown')
        if regime in ['low_vol_bull', 'low_vol_bear']:
            confidence_mods.append(0.1)  # Bonus za stabilny reżim
        elif regime in ['high_vol_bull', 'high_vol_bear']:
            confidence_mods.append(-0.1)  # Kara za wysoką zmienność
        
        # Spread modifier
        spread_quality = results.get('spread', {}).get('liquidity', 'good')
        if spread_quality == 'excellent':
            confidence_mods.append(0.05)
        elif spread_quality in ['poor', 'very_poor']:
            confidence_mods.append(-0.15)
        
        # Imbalance modifier
        imbalance_signal = results.get('imbalance', {}).get('strength', 0)
        confidence_mods.append(imbalance_signal * 0.1)
        
        # Alpha health modifier
        alpha_status = results.get('alpha_health', {}).get('status', 'HEALTHY')
        if alpha_status == 'DECAY_DETECTED':
            confidence_mods.append(-0.3)
        elif alpha_status == 'WARNING':
            confidence_mods.append(-0.1)
        
        # Final confidence
        final_confidence = base_confidence + sum(confidence_mods)
        final_confidence = max(0, min(1, final_confidence))
        
        # Decision
        if final_confidence >= 0.7:
            action = 'EXECUTE'
            size = 'full'
        elif final_confidence >= 0.5:
            action = 'EXECUTE'
            size = 'reduced'
        elif final_confidence >= 0.3:
            action = 'WAIT'
            size = 'none'
        else:
            action = 'SKIP'
            size = 'none'
        
        return {
            'action': action,
            'size': size,
            'final_confidence': round(final_confidence, 3),
            'base_confidence': base_confidence,
            'confidence_modifiers': confidence_mods,
            'reasons': self._get_decision_reasons(results, action)
        }
    
    def _get_decision_reasons(self, results: Dict, action: str) -> List[str]:
        """Generuje uzasadnienie decyzji."""
        reasons = []
        
        regime = results.get('regime', {}).get('current_regime', 'unknown')
        reasons.append(f"📊 Reżim rynku: {regime}")
        
        spread_liq = results.get('spread', {}).get('liquidity', 'unknown')
        reasons.append(f"💧 Płynność: {spread_liq}")
        
        imbalance = results.get('imbalance', {}).get('imbalance_pct', 0)
        reasons.append(f"⚖️ Imbalance: {imbalance}%")
        
        kelly = results.get('position_sizing', {}).get('recommendation', '')
        reasons.append(f"🎯 Kelly: {kelly}")
        
        alpha = results.get('alpha_health', {}).get('status', 'unknown')
        reasons.append(f"📈 Alpha health: {alpha}")
        
        return reasons


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTION DLA GENIUS BRAIN
# ═══════════════════════════════════════════════════════════════

def get_institutional_signal(prices: pd.Series,
                              bid: float = 0,
                              ask: float = 0,
                              bid_volume: float = 1000,
                              ask_volume: float = 1000,
                              base_confidence: float = 0.6) -> Dict:
    """
    Helper function dla integracji z Genius Brain.
    
    Returns:
        Dict z sygnałem i confidence
    """
    engine = InstitutionalEdgeEngine()
    
    # Ustawienia domyślne jeśli brak danych
    if bid <= 0 or ask <= 0:
        if len(prices) > 0:
            last_price = float(prices.iloc[-1])
            bid = last_price * 0.9999
            ask = last_price * 1.0001
    
    try:
        analysis = engine.full_analysis(
            prices=prices,
            bid=bid,
            ask=ask,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            signal_confidence=base_confidence
        )
        
        # Konwertuj na format dla Genius Brain
        final_rec = analysis.get('final_recommendation', {})
        action = final_rec.get('action', 'WAIT')
        
        # Signal mapping
        if action == 'EXECUTE':
            regime = analysis.get('regime', {}).get('current_regime', '')
            if 'bull' in regime:
                signal = 0.7
            elif 'bear' in regime:
                signal = -0.7
            else:
                signal = 0.3
        else:
            signal = 0
        
        return {
            'signal': signal,
            'confidence': final_rec.get('final_confidence', 0.5),
            'regime': analysis.get('regime', {}).get('current_regime', 'unknown'),
            'liquidity': analysis.get('spread', {}).get('liquidity', 'unknown'),
            'kelly_size': analysis.get('position_sizing', {}).get('position_size_usd', 50),
            'alpha_health': analysis.get('alpha_health', {}).get('status', 'unknown'),
            'execution_strategy': analysis.get('execution', {}).get('strategy', 'market'),
            'reasons': final_rec.get('reasons', [])
        }
        
    except Exception as e:
        logger.error(f"Institutional signal error: {e}")
        return {
            'signal': 0,
            'confidence': 0.3,
            'regime': 'error',
            'reasons': [f"Error: {e}"]
        }


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🏛️ INSTITUTIONAL EDGE ENGINE TEST")
    print("=" * 50)
    
    # Symulowane dane
    np.random.seed(42)
    prices = pd.Series(np.random.randn(200).cumsum() + 100000)
    
    # Test głównego silnika
    engine = InstitutionalEdgeEngine(capital=5000)
    
    analysis = engine.full_analysis(
        prices=prices,
        bid=99950,
        ask=99960,
        bid_volume=150,
        ask_volume=100,
        signal_confidence=0.65
    )
    
    print("\n📊 REGIME DETECTION:")
    print(f"  Current: {analysis['regime'].get('current_regime', 'unknown')}")
    print(f"  Confidence: {analysis['regime'].get('confidence', 0):.1%}")
    
    print("\n🎯 KELLY POSITION SIZING:")
    print(f"  Optimal size: ${analysis['position_sizing']['position_size_usd']}")
    print(f"  Risk level: {analysis['position_sizing']['risk_level']}")
    print(f"  Recommendation: {analysis['position_sizing']['recommendation']}")
    
    print("\n💧 MICROSTRUCTURE:")
    print(f"  Spread: {analysis['spread']['spread_bps']} bps")
    print(f"  Liquidity: {analysis['spread']['liquidity']}")
    print(f"  Imbalance: {analysis['imbalance']['imbalance_pct']}%")
    
    print("\n📈 ALPHA HEALTH:")
    print(f"  Status: {analysis['alpha_health'].get('status', 'unknown')}")
    
    print("\n⚡ EXECUTION PLAN:")
    print(f"  Strategy: {analysis['execution']['strategy']}")
    print(f"  Chunks: {analysis['execution']['chunks']}")
    
    print("\n🎯 FINAL RECOMMENDATION:")
    final = analysis['final_recommendation']
    print(f"  Action: {final['action']}")
    print(f"  Confidence: {final['final_confidence']:.1%}")
    print("  Reasons:")
    for r in final['reasons']:
        print(f"    - {r}")
    
    print("\n✅ TEST COMPLETE!")
