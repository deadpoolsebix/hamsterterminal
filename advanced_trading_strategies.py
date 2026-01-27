"""
🚀 ADVANCED TRADING STRATEGIES - Dodatkowe strategie dla Samanty
================================================================

Strategie z profesjonalnych funduszy hedge:
1. TWAP (Time-Weighted Average Price) - Execution algorithm
2. Seasonality Trading - Calendar patterns
3. Genetic Algorithm Optimization - Ewolucja strategii
4. Smart Order Routing - Multi-exchange execution
5. Market Making Signals - Spread analysis

Author: Samanta Genius Engine
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing DEAP for genetic algorithms
try:
    from deap import base, creator, tools, algorithms
    DEAP_AVAILABLE = True
except ImportError:
    DEAP_AVAILABLE = False
    logger.warning("⚠️ DEAP not available - Genetic Algorithms disabled")


# ═══════════════════════════════════════════════════════════════
# 1. TWAP - TIME-WEIGHTED AVERAGE PRICE
# ═══════════════════════════════════════════════════════════════

@dataclass
class TWAPOrder:
    """TWAP order slice"""
    slice_number: int
    total_slices: int
    quantity: float
    execute_at: datetime
    executed: bool = False
    execution_price: float = 0.0


class TWAPStrategy:
    """
    TWAP (Time-Weighted Average Price) Strategy
    
    Dzieli duże zlecenie na mniejsze części wykonywane w równych odstępach czasu.
    Cel: uzyskać cenę blisko średniej z okresu wykonania.
    
    Używane przez instytucje do minimalizacji market impact.
    """
    
    def __init__(self):
        self.name = "TWAP"
        logger.info("📊 TWAP Strategy initialized")
    
    def create_execution_plan(
        self,
        total_quantity: float,
        duration_hours: float = 4.0,
        num_slices: int = 12,
        start_time: datetime = None
    ) -> List[TWAPOrder]:
        """
        Tworzy plan wykonania TWAP
        
        Args:
            total_quantity: Całkowita ilość do wykonania
            duration_hours: Czas wykonania w godzinach
            num_slices: Liczba kawałków (więcej = mniejszy impact)
            start_time: Czas rozpoczęcia (domyślnie teraz)
        
        Returns:
            Lista zleceń TWAP do wykonania
        """
        if start_time is None:
            start_time = datetime.now()
        
        slice_quantity = total_quantity / num_slices
        interval_minutes = (duration_hours * 60) / num_slices
        
        orders = []
        for i in range(num_slices):
            execute_at = start_time + timedelta(minutes=interval_minutes * i)
            order = TWAPOrder(
                slice_number=i + 1,
                total_slices=num_slices,
                quantity=slice_quantity,
                execute_at=execute_at
            )
            orders.append(order)
        
        logger.info(f"📊 TWAP Plan: {num_slices} slices over {duration_hours}h")
        logger.info(f"   Each slice: {slice_quantity:.4f} units")
        
        return orders
    
    def analyze_execution(
        self,
        orders: List[TWAPOrder],
        market_vwap: float
    ) -> Dict:
        """
        Analizuje wykonanie TWAP vs rynek
        """
        if not orders or not any(o.executed for o in orders):
            return {'status': 'not_executed'}
        
        executed = [o for o in orders if o.executed]
        total_qty = sum(o.quantity for o in executed)
        avg_price = sum(o.quantity * o.execution_price for o in executed) / total_qty
        
        slippage_bps = (avg_price / market_vwap - 1) * 10000  # basis points
        
        return {
            'status': 'executed',
            'avg_execution_price': avg_price,
            'market_vwap': market_vwap,
            'slippage_bps': slippage_bps,
            'slices_executed': len(executed),
            'total_quantity': total_qty,
            'quality': 'GOOD' if abs(slippage_bps) < 10 else 'FAIR' if abs(slippage_bps) < 30 else 'POOR'
        }
    
    def get_signal(self, current_price: float, vwap: float) -> Dict:
        """
        Sygnał bazujący na TWAP/VWAP deviation
        
        Gdy cena < VWAP - lepiej kupować (cena poniżej średniej)
        Gdy cena > VWAP - lepiej sprzedawać
        """
        deviation_pct = (current_price / vwap - 1) * 100
        
        if deviation_pct < -0.5:
            signal = 0.5  # Buy signal - cena poniżej średniej
            action = "BUY_BELOW_TWAP"
        elif deviation_pct > 0.5:
            signal = -0.5  # Sell signal - cena powyżej średniej
            action = "SELL_ABOVE_TWAP"
        else:
            signal = 0.0
            action = "AT_TWAP"
        
        return {
            'signal': signal,
            'action': action,
            'deviation_pct': deviation_pct,
            'current_price': current_price,
            'twap': vwap,
            'confidence': min(abs(deviation_pct) / 2, 1.0)
        }


# ═══════════════════════════════════════════════════════════════
# 2. SEASONALITY TRADING
# ═══════════════════════════════════════════════════════════════

class SeasonalityTrading:
    """
    Seasonality Trading Strategy
    
    Identyfikuje powtarzające się wzorce czasowe:
    - Dzień tygodnia (Monday effect, Friday selloff)
    - Pora dnia (Asian, London, NY sessions)
    - Miesiąc (January effect, Summer doldrums)
    - Kwartał (End-of-quarter rebalancing)
    
    Dla krypto szczególnie ważne:
    - Weekend effect (niższa płynność)
    - Funding rate settlement times
    - Options expiry (ostatni piątek miesiąca)
    """
    
    def __init__(self):
        self.name = "Seasonality"
        logger.info("📅 Seasonality Trading initialized")
        
        # Historyczne wzorce dla BTC (uproszczone)
        self.day_of_week_bias = {
            0: 0.1,   # Monday - slight bullish (institutional accumulation)
            1: 0.05,  # Tuesday - neutral-bullish
            2: 0.0,   # Wednesday - neutral
            3: -0.05, # Thursday - slight bearish
            4: -0.1,  # Friday - profit taking
            5: -0.15, # Saturday - low volume, slight bearish
            6: 0.05,  # Sunday - slight recovery before Monday
        }
        
        self.hour_of_day_bias = {
            # Asian session (0-8 UTC)
            **{h: -0.05 for h in range(0, 8)},
            # London session (8-13 UTC) - most volatile
            **{h: 0.1 for h in range(8, 13)},
            # NY session (13-21 UTC) - high volume
            **{h: 0.05 for h in range(13, 21)},
            # Late NY (21-24 UTC) - low volume
            **{h: -0.05 for h in range(21, 24)},
        }
        
        self.month_bias = {
            1: 0.15,   # January effect - new year optimism
            2: 0.05,   # February - continuation
            3: 0.0,    # March - tax season in US
            4: 0.1,    # April - post-tax buying
            5: -0.05,  # May - "Sell in May"
            6: -0.1,   # June - summer doldrums
            7: -0.1,   # July - low volume
            8: -0.05,  # August - vacation season
            9: 0.05,   # September - return from summer
            10: 0.15,  # October - Q4 push begins
            11: 0.2,   # November - historically strong
            12: 0.1,   # December - year-end rally
        }
    
    def analyze_seasonality(self, timestamp: datetime = None) -> Dict:
        """
        Analizuje sezonowość dla danego momentu
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        day_bias = self.day_of_week_bias[timestamp.weekday()]
        hour_bias = self.hour_of_day_bias[timestamp.hour]
        month_bias = self.month_bias[timestamp.month]
        
        # Sprawdź specjalne wydarzenia
        special_events = []
        
        # Ostatni piątek miesiąca (Options expiry)
        if timestamp.weekday() == 4:  # Friday
            days_to_month_end = (timestamp.replace(month=timestamp.month % 12 + 1, day=1) - timestamp).days
            if days_to_month_end <= 7:
                special_events.append("OPTIONS_EXPIRY")
                hour_bias *= 1.5  # Większa zmienność
        
        # Koniec kwartału (duże rebalancing)
        if timestamp.month in [3, 6, 9, 12] and timestamp.day >= 25:
            special_events.append("QUARTER_END_REBALANCING")
            day_bias += 0.1 if timestamp.month == 12 else -0.05
        
        # Weekend (niższa płynność)
        if timestamp.weekday() >= 5:
            special_events.append("WEEKEND_LOW_LIQUIDITY")
        
        # Oblicz końcowy sygnał
        combined_bias = (day_bias * 0.3 + hour_bias * 0.3 + month_bias * 0.4)
        
        # Confidence bazuje na zgodności sygnałów
        signals = [day_bias, hour_bias, month_bias]
        agreement = 1.0 if all(s >= 0 for s in signals) or all(s <= 0 for s in signals) else 0.5
        
        return {
            'signal': combined_bias,
            'confidence': agreement,
            'day_bias': day_bias,
            'hour_bias': hour_bias,
            'month_bias': month_bias,
            'special_events': special_events,
            'timestamp': timestamp.isoformat(),
            'day_name': timestamp.strftime('%A'),
            'session': self._get_session(timestamp.hour),
            'recommendation': 'LONG' if combined_bias > 0.05 else 'SHORT' if combined_bias < -0.05 else 'NEUTRAL'
        }
    
    def _get_session(self, hour: int) -> str:
        if 0 <= hour < 8:
            return "ASIAN"
        elif 8 <= hour < 13:
            return "LONDON"
        elif 13 <= hour < 21:
            return "NEW_YORK"
        else:
            return "LATE_NY"
    
    def get_signal(self) -> Dict:
        """Zwraca aktualny sygnał sezonowości"""
        return self.analyze_seasonality()


# ═══════════════════════════════════════════════════════════════
# 3. GENETIC ALGORITHM OPTIMIZATION
# ═══════════════════════════════════════════════════════════════

class GeneticStrategyOptimizer:
    """
    Genetic Algorithm Strategy Optimizer
    
    Używa algorytmów genetycznych do optymalizacji parametrów strategii.
    Symuluje "ewolucję" najlepszych parametrów przez:
    - Selekcję najlepszych strategii
    - Krzyżowanie parametrów
    - Mutacje
    
    Optymalizowane parametry:
    - RSI thresholds
    - Moving average periods
    - Stop loss / Take profit levels
    - Position sizing
    """
    
    def __init__(self, population_size: int = 50, generations: int = 20):
        self.name = "GeneticOptimizer"
        self.population_size = population_size
        self.generations = generations
        
        if DEAP_AVAILABLE:
            self._setup_deap()
            logger.info(f"🧬 Genetic Optimizer initialized (pop={population_size}, gen={generations})")
        else:
            logger.warning("🧬 Genetic Optimizer running in SIMPLE mode (no DEAP)")
    
    def _setup_deap(self):
        """Setup DEAP framework"""
        # Unikaj wielokrotnego tworzenia klas
        if not hasattr(creator, "FitnessMax"):
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMax)
        
        self.toolbox = base.Toolbox()
        
        # Geny: [rsi_oversold, rsi_overbought, sma_fast, sma_slow, sl_pct, tp_pct]
        self.toolbox.register("rsi_oversold", random.randint, 15, 40)
        self.toolbox.register("rsi_overbought", random.randint, 60, 85)
        self.toolbox.register("sma_fast", random.randint, 5, 30)
        self.toolbox.register("sma_slow", random.randint, 20, 100)
        self.toolbox.register("sl_pct", random.uniform, 0.5, 5.0)
        self.toolbox.register("tp_pct", random.uniform, 1.0, 10.0)
        
        self.toolbox.register("individual", tools.initCycle, creator.Individual,
                             (self.toolbox.rsi_oversold, self.toolbox.rsi_overbought,
                              self.toolbox.sma_fast, self.toolbox.sma_slow,
                              self.toolbox.sl_pct, self.toolbox.tp_pct), n=1)
        
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=5, indpb=0.2)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
    
    def evaluate_strategy(self, individual: list, price_data: pd.Series) -> Tuple[float]:
        """
        Ocenia strategię na podstawie parametrów
        
        Returns:
            Tuple z fitness (sharpe ratio lub total return)
        """
        rsi_oversold, rsi_overbought, sma_fast, sma_slow, sl_pct, tp_pct = individual
        
        # Upewnij się, że parametry są sensowne
        if sma_fast >= sma_slow:
            return (-10.0,)  # Kara za złe parametry
        
        if rsi_oversold >= rsi_overbought:
            return (-10.0,)
        
        # Prosta symulacja backtestowa
        try:
            import ta
            
            df = pd.DataFrame({'close': price_data})
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            df['sma_fast'] = df['close'].rolling(int(sma_fast)).mean()
            df['sma_slow'] = df['close'].rolling(int(sma_slow)).mean()
            
            # Sygnały
            df['signal'] = 0
            df.loc[(df['rsi'] < rsi_oversold) & (df['sma_fast'] > df['sma_slow']), 'signal'] = 1
            df.loc[(df['rsi'] > rsi_overbought) & (df['sma_fast'] < df['sma_slow']), 'signal'] = -1
            
            # Prosta symulacja returns
            df['returns'] = df['close'].pct_change()
            df['strategy_returns'] = df['signal'].shift(1) * df['returns']
            
            # Fitness = Sharpe Ratio
            if df['strategy_returns'].std() > 0:
                sharpe = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(365 * 24)
            else:
                sharpe = 0
            
            # Kara za zbyt częste trading
            trade_frequency = df['signal'].diff().abs().sum() / len(df)
            if trade_frequency > 0.1:  # Więcej niż 10% zmian
                sharpe *= 0.8
            
            return (max(sharpe, -10.0),)
            
        except Exception as e:
            return (-10.0,)
    
    def optimize(self, price_data: pd.Series) -> Dict:
        """
        Uruchom optymalizację genetyczną
        
        Args:
            price_data: Seria cen do optymalizacji
        
        Returns:
            Najlepsze parametry i statystyki
        """
        if not DEAP_AVAILABLE:
            return self._simple_optimization(price_data)
        
        logger.info("🧬 Starting genetic optimization...")
        
        # Ustaw funkcję fitness
        self.toolbox.register("evaluate", self.evaluate_strategy, price_data=price_data)
        
        # Stwórz populację
        pop = self.toolbox.population(n=self.population_size)
        
        # Statystyki
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("max", np.max)
        stats.register("min", np.min)
        
        # Hall of fame - najlepsze jednostki
        hof = tools.HallOfFame(5)
        
        # Uruchom algorytm
        pop, logbook = algorithms.eaSimple(
            pop, self.toolbox,
            cxpb=0.7,  # Crossover probability
            mutpb=0.2,  # Mutation probability
            ngen=self.generations,
            stats=stats,
            halloffame=hof,
            verbose=False
        )
        
        # Najlepszy osobnik
        best = hof[0]
        
        result = {
            'best_params': {
                'rsi_oversold': int(best[0]),
                'rsi_overbought': int(best[1]),
                'sma_fast': int(best[2]),
                'sma_slow': int(best[3]),
                'stop_loss_pct': round(best[4], 2),
                'take_profit_pct': round(best[5], 2),
            },
            'fitness': best.fitness.values[0],
            'generations': self.generations,
            'population_size': self.population_size,
            'convergence': [record['max'] for record in logbook],
        }
        
        logger.info(f"🧬 Optimization complete! Best fitness: {result['fitness']:.4f}")
        logger.info(f"   Best params: RSI {result['best_params']['rsi_oversold']}-{result['best_params']['rsi_overbought']}")
        
        return result
    
    def _simple_optimization(self, price_data: pd.Series) -> Dict:
        """Prosta optymalizacja grid search gdy DEAP niedostępny"""
        logger.info("🧬 Running simple grid search optimization...")
        
        best_fitness = -float('inf')
        best_params = None
        
        # Grid search
        for rsi_os in [20, 25, 30, 35]:
            for rsi_ob in [65, 70, 75, 80]:
                for sma_f in [10, 15, 20]:
                    for sma_s in [30, 50, 100]:
                        if sma_f >= sma_s:
                            continue
                        
                        params = [rsi_os, rsi_ob, sma_f, sma_s, 2.0, 4.0]
                        fitness = self.evaluate_strategy(params, price_data)[0]
                        
                        if fitness > best_fitness:
                            best_fitness = fitness
                            best_params = params
        
        if best_params is None:
            best_params = [30, 70, 10, 50, 2.0, 4.0]
            best_fitness = 0.0
        
        return {
            'best_params': {
                'rsi_oversold': int(best_params[0]),
                'rsi_overbought': int(best_params[1]),
                'sma_fast': int(best_params[2]),
                'sma_slow': int(best_params[3]),
                'stop_loss_pct': round(best_params[4], 2),
                'take_profit_pct': round(best_params[5], 2),
            },
            'fitness': best_fitness,
            'method': 'grid_search'
        }
    
    def get_signal(self, optimized_params: Dict, current_rsi: float, sma_fast: float, sma_slow: float) -> Dict:
        """
        Generuje sygnał bazując na zoptymalizowanych parametrach
        """
        params = optimized_params.get('best_params', {})
        rsi_os = params.get('rsi_oversold', 30)
        rsi_ob = params.get('rsi_overbought', 70)
        
        signal = 0.0
        action = "HOLD"
        
        if current_rsi < rsi_os and sma_fast > sma_slow:
            signal = 0.8
            action = "STRONG_BUY"
        elif current_rsi < 40 and sma_fast > sma_slow:
            signal = 0.4
            action = "BUY"
        elif current_rsi > rsi_ob and sma_fast < sma_slow:
            signal = -0.8
            action = "STRONG_SELL"
        elif current_rsi > 60 and sma_fast < sma_slow:
            signal = -0.4
            action = "SELL"
        
        return {
            'signal': signal,
            'action': action,
            'current_rsi': current_rsi,
            'optimized_thresholds': (rsi_os, rsi_ob),
            'confidence': abs(signal),
            'stop_loss_pct': params.get('stop_loss_pct', 2.0),
            'take_profit_pct': params.get('take_profit_pct', 4.0)
        }


# ═══════════════════════════════════════════════════════════════
# 4. SMART ORDER ROUTING (Simplified)
# ═══════════════════════════════════════════════════════════════

class SmartOrderRouter:
    """
    Smart Order Routing - Routing do najlepszych cen
    
    Analizuje ceny na różnych giełdach i routuje zlecenia
    gdzie jest najlepsza płynność/cena.
    
    Uwaga: Pełna implementacja wymaga połączeń do wielu giełd.
    Ta wersja analizuje arbitraż między giełdami.
    """
    
    def __init__(self):
        self.name = "SmartOrderRouter"
        self.exchanges = ['Binance', 'Bybit', 'OKX', 'Kraken', 'Coinbase']
        logger.info("🔀 Smart Order Router initialized")
    
    def analyze_prices(self, prices: Dict[str, float]) -> Dict:
        """
        Analizuje ceny z różnych giełd
        
        Args:
            prices: Dict z cenami {exchange: price}
        
        Returns:
            Analiza z rekomendacją gdzie kupić/sprzedać
        """
        if len(prices) < 2:
            return {'error': 'Need at least 2 exchanges'}
        
        sorted_exchanges = sorted(prices.items(), key=lambda x: x[1])
        lowest = sorted_exchanges[0]
        highest = sorted_exchanges[-1]
        
        spread_pct = (highest[1] / lowest[1] - 1) * 100
        avg_price = sum(prices.values()) / len(prices)
        
        # Arbitrage signal
        arbitrage_signal = 0.0
        if spread_pct > 0.1:  # > 0.1% spread
            arbitrage_signal = min(spread_pct / 0.5, 1.0)  # Max 1.0 at 0.5% spread
        
        return {
            'best_buy': {'exchange': lowest[0], 'price': lowest[1]},
            'best_sell': {'exchange': highest[0], 'price': highest[1]},
            'spread_pct': spread_pct,
            'avg_price': avg_price,
            'arbitrage_signal': arbitrage_signal,
            'arbitrage_opportunity': spread_pct > 0.15,
            'recommendation': f"BUY on {lowest[0]}, SELL on {highest[0]}" if spread_pct > 0.15 else "No significant arbitrage"
        }
    
    def get_signal(self, prices: Dict[str, float] = None) -> Dict:
        """
        Sygnał bazujący na analizie cross-exchange
        
        Jeśli nie podano cen, zwraca placeholder
        """
        if prices is None:
            # Placeholder - w produkcji pobieraj realtime
            return {
                'signal': 0.0,
                'confidence': 0.0,
                'note': 'Need realtime multi-exchange prices'
            }
        
        analysis = self.analyze_prices(prices)
        
        return {
            'signal': analysis['arbitrage_signal'],
            'confidence': min(analysis['spread_pct'] / 0.3, 1.0),
            'best_buy_exchange': analysis['best_buy']['exchange'],
            'best_sell_exchange': analysis['best_sell']['exchange'],
            'spread_pct': analysis['spread_pct']
        }


# ═══════════════════════════════════════════════════════════════
# 5. MARKET MAKING SIGNALS
# ═══════════════════════════════════════════════════════════════

class MarketMakingAnalyzer:
    """
    Market Making Analyzer
    
    Analizuje spread bid-ask i płynność.
    NIE jest to prawdziwy market maker (wymaga licencji/kapitału),
    ale pomaga identyfikować:
    - Niską płynność (wysoki spread)
    - Momenty gdy market makerzy wycofują się
    - Sygnały z order book depth
    
    Używane do: unikania tradowania przy złej płynności
    """
    
    def __init__(self):
        self.name = "MarketMakingAnalyzer"
        logger.info("📊 Market Making Analyzer initialized")
    
    def analyze_spread(
        self,
        bid: float,
        ask: float,
        historical_spread_bps: float = 5.0  # Typowy spread w basis points
    ) -> Dict:
        """
        Analizuje spread bid-ask
        
        Args:
            bid: Cena kupna
            ask: Cena sprzedaży
            historical_spread_bps: Historyczny typowy spread
        
        Returns:
            Analiza spreadu
        """
        mid_price = (bid + ask) / 2
        spread_bps = (ask - bid) / mid_price * 10000  # basis points
        
        spread_ratio = spread_bps / historical_spread_bps
        
        # Sygnały
        if spread_ratio > 3.0:
            liquidity_status = "VERY_LOW"
            signal = -0.5  # Unikaj tradowania
            warning = "⚠️ Spread 3x normalny - UNIKAJ"
        elif spread_ratio > 2.0:
            liquidity_status = "LOW"
            signal = -0.3
            warning = "⚠️ Spread 2x normalny - ostrożnie"
        elif spread_ratio > 1.5:
            liquidity_status = "BELOW_NORMAL"
            signal = -0.1
            warning = "Spread podwyższony"
        elif spread_ratio < 0.5:
            liquidity_status = "EXCELLENT"
            signal = 0.2  # Dobry moment na trading
            warning = None
        else:
            liquidity_status = "NORMAL"
            signal = 0.0
            warning = None
        
        return {
            'bid': bid,
            'ask': ask,
            'mid_price': mid_price,
            'spread_bps': spread_bps,
            'spread_ratio': spread_ratio,
            'liquidity_status': liquidity_status,
            'signal': signal,
            'warning': warning,
            'recommendation': 'TRADE' if signal >= 0 else 'WAIT'
        }
    
    def analyze_order_book_imbalance(
        self,
        bid_volume: float,
        ask_volume: float
    ) -> Dict:
        """
        Analizuje nierównowagę w order book
        
        Duża przewaga bid = presja kupna (bullish)
        Duża przewaga ask = presja sprzedaży (bearish)
        """
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return {'error': 'No volume data'}
        
        imbalance = (bid_volume - ask_volume) / total_volume  # -1 to 1
        
        if imbalance > 0.3:
            signal = 0.5
            interpretation = "STRONG_BUY_PRESSURE"
        elif imbalance > 0.1:
            signal = 0.2
            interpretation = "BUY_PRESSURE"
        elif imbalance < -0.3:
            signal = -0.5
            interpretation = "STRONG_SELL_PRESSURE"
        elif imbalance < -0.1:
            signal = -0.2
            interpretation = "SELL_PRESSURE"
        else:
            signal = 0.0
            interpretation = "BALANCED"
        
        return {
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'imbalance': imbalance,
            'signal': signal,
            'interpretation': interpretation,
            'confidence': abs(imbalance)
        }
    
    def get_signal(self, bid: float = None, ask: float = None, bid_vol: float = None, ask_vol: float = None) -> Dict:
        """Kombinowany sygnał"""
        signals = []
        
        if bid and ask:
            spread_analysis = self.analyze_spread(bid, ask)
            signals.append(spread_analysis['signal'])
        
        if bid_vol and ask_vol:
            imbalance_analysis = self.analyze_order_book_imbalance(bid_vol, ask_vol)
            signals.append(imbalance_analysis['signal'])
        
        if not signals:
            return {'signal': 0.0, 'confidence': 0.0, 'note': 'Need bid/ask data'}
        
        avg_signal = sum(signals) / len(signals)
        
        return {
            'signal': avg_signal,
            'confidence': min(abs(avg_signal) * 2, 1.0),
            'components': len(signals)
        }


# ═══════════════════════════════════════════════════════════════
# COMBINED ADVANCED STRATEGIES
# ═══════════════════════════════════════════════════════════════

class AdvancedStrategiesEngine:
    """
    Główny silnik łączący wszystkie zaawansowane strategie
    """
    
    def __init__(self):
        self.twap = TWAPStrategy()
        self.seasonality = SeasonalityTrading()
        self.genetic = GeneticStrategyOptimizer()
        self.smart_router = SmartOrderRouter()
        self.market_making = MarketMakingAnalyzer()
        
        logger.info("🚀 Advanced Strategies Engine initialized with 5 strategies")
    
    def get_combined_signal(
        self,
        current_price: float,
        vwap: float = None,
        bid: float = None,
        ask: float = None,
        multi_exchange_prices: Dict[str, float] = None
    ) -> Dict:
        """
        Łączy sygnały ze wszystkich zaawansowanych strategii
        """
        signals = []
        components = {}
        
        # 1. TWAP Signal
        if vwap:
            twap_sig = self.twap.get_signal(current_price, vwap)
            signals.append(twap_sig['signal'] * 0.2)  # 20% weight
            components['twap'] = twap_sig
        
        # 2. Seasonality Signal
        season_sig = self.seasonality.get_signal()
        signals.append(season_sig['signal'] * 0.3)  # 30% weight
        components['seasonality'] = season_sig
        
        # 3. Smart Order Routing
        if multi_exchange_prices:
            sor_sig = self.smart_router.get_signal(multi_exchange_prices)
            signals.append(sor_sig['signal'] * 0.2)  # 20% weight
            components['smart_router'] = sor_sig
        
        # 4. Market Making/Liquidity
        if bid and ask:
            mm_sig = self.market_making.get_signal(bid, ask)
            signals.append(mm_sig['signal'] * 0.3)  # 30% weight
            components['market_making'] = mm_sig
        
        # Combined signal
        combined = sum(signals) if signals else 0.0
        
        # Determine action
        if combined > 0.3:
            action = "LONG"
        elif combined < -0.3:
            action = "SHORT"
        else:
            action = "NEUTRAL"
        
        return {
            'combined_signal': combined,
            'action': action,
            'confidence': min(abs(combined), 1.0),
            'components': components,
            'strategies_used': len(signals)
        }


# ═══════════════════════════════════════════════════════════════
# QUICK ACCESS FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_twap_signal(current_price: float, vwap: float) -> Dict:
    """Quick access to TWAP signal"""
    return TWAPStrategy().get_signal(current_price, vwap)


def get_seasonality_signal() -> Dict:
    """Quick access to seasonality signal"""
    return SeasonalityTrading().get_signal()


def get_genetic_optimized_params(price_data: pd.Series) -> Dict:
    """Quick access to genetic optimization"""
    return GeneticStrategyOptimizer().optimize(price_data)


def get_market_making_signal(bid: float, ask: float) -> Dict:
    """Quick access to market making signal"""
    return MarketMakingAnalyzer().get_signal(bid, ask)


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("ADVANCED TRADING STRATEGIES TEST")
    print("=" * 70)
    print()
    
    # 1. TWAP
    print("1. TWAP STRATEGY")
    twap = TWAPStrategy()
    plan = twap.create_execution_plan(1.0, duration_hours=2, num_slices=6)
    signal = twap.get_signal(current_price=100500, vwap=100000)
    print(f"   Signal: {signal['action']} (deviation: {signal['deviation_pct']:.2f}%)")
    print()
    
    # 2. Seasonality
    print("2. SEASONALITY STRATEGY")
    season = SeasonalityTrading()
    sig = season.get_signal()
    print(f"   Session: {sig['session']}")
    print(f"   Day: {sig['day_name']}")
    print(f"   Signal: {sig['signal']:.3f} ({sig['recommendation']})")
    print(f"   Events: {sig['special_events']}")
    print()
    
    # 3. Genetic Algorithm
    print("3. GENETIC ALGORITHM")
    print(f"   DEAP available: {DEAP_AVAILABLE}")
    genetic = GeneticStrategyOptimizer(population_size=20, generations=5)
    # Generate test data
    test_prices = pd.Series([100000 + np.random.randn() * 500 + i * 10 for i in range(500)])
    result = genetic.optimize(test_prices)
    print(f"   Best params: RSI {result['best_params']['rsi_oversold']}-{result['best_params']['rsi_overbought']}")
    print(f"   Fitness: {result['fitness']:.4f}")
    print()
    
    # 4. Smart Order Router
    print("4. SMART ORDER ROUTING")
    sor = SmartOrderRouter()
    prices = {
        'Binance': 100000,
        'Bybit': 100050,
        'OKX': 99980,
        'Kraken': 100020
    }
    analysis = sor.analyze_prices(prices)
    print(f"   Best buy: {analysis['best_buy']['exchange']} @ ${analysis['best_buy']['price']:,.0f}")
    print(f"   Best sell: {analysis['best_sell']['exchange']} @ ${analysis['best_sell']['price']:,.0f}")
    print(f"   Spread: {analysis['spread_pct']:.3f}%")
    print()
    
    # 5. Market Making
    print("5. MARKET MAKING ANALYZER")
    mm = MarketMakingAnalyzer()
    spread_analysis = mm.analyze_spread(bid=99990, ask=100010)
    print(f"   Spread: {spread_analysis['spread_bps']:.1f} bps")
    print(f"   Liquidity: {spread_analysis['liquidity_status']}")
    print()
    
    # Combined
    print("6. COMBINED ENGINE")
    engine = AdvancedStrategiesEngine()
    combined = engine.get_combined_signal(
        current_price=100000,
        vwap=99800,
        bid=99990,
        ask=100010,
        multi_exchange_prices=prices
    )
    print(f"   Combined Signal: {combined['combined_signal']:.3f}")
    print(f"   Action: {combined['action']}")
    print(f"   Confidence: {combined['confidence']:.1%}")
    print()
    
    print("=" * 70)
    print("ALL ADVANCED STRATEGIES OPERATIONAL!")
    print("=" * 70)
