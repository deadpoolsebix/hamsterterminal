"""
🔗 GENIUS BRAIN CONNECTOR - Łącznik wszystkich modułów
======================================================

Ten moduł integruje WSZYSTKIE komponenty systemu w jeden spójny "mózg".
Każdy moduł dostarcza sygnały, a Brain Connector je waży i podejmuje decyzję.

INTEGROWANE MODUŁY:
1. ICT Smart Money Bot (ict_smart_money_bot.py)
2. Time Series Analysis (time_series_analysis.py)
3. ML Ensemble (ml_models_extended.py)
4. Pairs Trading (pairs_trading_strategy.py)
5. Strategy Optimizer (strategy_optimizer.py)
6. Genius Trading Engine (genius_trading_engine.py)
7. Sentiment AI (genius_sentiment_ai.py)
8. LSTM Predictor (genius_lstm_predictor.py)
9. Funding Rate (funding_rate_calculator.py)
10. Risk Engine (genius_risk_engine.py)

Author: Genius Engine Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# SIGNAL AGGREGATION
# ═══════════════════════════════════════════════════════════════

@dataclass
class ModuleResult:
    """Wynik z pojedynczego modułu"""
    module_name: str
    signal: float  # -1 (short) do 1 (long)
    confidence: float  # 0-1
    weight: float  # Waga w końcowej decyzji
    reasons: List[str]
    active: bool = True
    error: str = None
    
    def weighted_signal(self) -> float:
        return self.signal * self.confidence * self.weight if self.active else 0


@dataclass
class BrainDecision:
    """Końcowa decyzja systemu"""
    action: str  # 'STRONG_LONG', 'LONG', 'NEUTRAL', 'SHORT', 'STRONG_SHORT'
    final_score: float  # -1 do 1
    confidence: float  # 0-1
    
    # Szczegóły od modułów
    module_results: Dict[str, ModuleResult]
    
    # Parametry trade'a
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size_pct: float
    
    # Meta
    reasons: List[str]
    warnings: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'action': self.action,
            'score': self.final_score,
            'confidence': self.confidence,
            'entry': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size_pct': self.position_size_pct,
            'reasons': self.reasons,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# MODULE WEIGHTS CONFIGURATION
# ═══════════════════════════════════════════════════════════════

class ModuleWeights:
    """
    Wagi dla każdego modułu.
    Możesz dostosować wagi do swojej strategii.
    """
    
    # Domyślne wagi (suma = 1.0) - ORYGINALNA STRATEGIA SAMANTY + BONUSY
    DEFAULT = {
        # 🎯 CORE SAMANTA (oryginalne wagi)
        'ict_smart_money': 0.14,    # ICT / Smart Money - GŁÓWNY MODUŁ
        'technical': 0.06,          # RSI, MACD, MA
        'ml_ensemble': 0.05,        # SVM, LDA, QDA
        'time_series': 0.04,        # ADF, Hurst, mean reversion
        'sentiment': 0.04,          # News, social
        'funding_rate': 0.04,       # Crypto funding
        'lstm': 0.02,               # Deep learning (6 lat danych!)
        'risk_engine': 0.03,        # Risk assessment
        # 🔥 EDGE MODULES
        'rl_agent': 0.07,           # Reinforcement Learning
        'liquidation_heatmap': 0.10, # Liquidation Magnets
        'order_flow': 0.04,         # CVD, Icebergs, Whales
        # 🆕 POWER MODULES
        'on_chain': 0.05,           # 🔗 Whale tracking on-chain
        'quant_power': 0.06,        # ⚡ FFN, GARCH, VaR, Scipy
        # 🏛️ INSTITUTIONAL
        'institutional': 0.10,      # 🏛️ Kelly, HMM, Microstructure
        # 📰 ADVANCED STRATEGIES (zamienione na lepsze!)
        'twap': 0.02,               # 📊 TWAP - lepsze execution
        'event_driven': 0.03,       # 📰 Event-Driven (news reaction)
        'divergence': 0.03,         # 📐 Divergence Detection (reversal signals)
        'mtf_confluence': 0.02,     # 🔍 Multi-Timeframe Confluence
        # 🐋 WHALE & ORDER BOOK
        'whale_alert': 0.02,        # 🐋 Whale transactions tracker
        'orderbook_depth': 0.02,    # 📊 Level 2 order book analysis
        # 🚀 MOMENTUM
        'momentum': 0.02,           # 🚀 Time-series + Cross-sectional momentum
    }
    
    # Agresywny profil
    AGGRESSIVE = {
        'ict_smart_money': 0.22,
        'technical': 0.10,
        'ml_ensemble': 0.10,
        'time_series': 0.03,
        'sentiment': 0.08,
        'funding_rate': 0.07,
        'lstm': 0.00,
        'pairs_trading': 0.00,
        'risk_engine': 0.00,
        # 🔥 NEW MODULES
        'rl_agent': 0.10,
        'liquidation_heatmap': 0.12,
        'order_flow': 0.03,
        # 🆕 POWER MODULES
        'on_chain': 0.08,
        'quant_power': 0.07,
    }
    
    # Konserwatywny profil
    CONSERVATIVE = {
        'ict_smart_money': 0.14,
        'technical': 0.10,
        'ml_ensemble': 0.06,
        'time_series': 0.10,
        'sentiment': 0.06,
        'funding_rate': 0.04,
        'lstm': 0.04,
        'pairs_trading': 0.04,
        'risk_engine': 0.12,
        # 🔥 NEW MODULES
        'rl_agent': 0.06,
        'liquidation_heatmap': 0.08,
        'order_flow': 0.02,
        # 🆕 POWER MODULES - niższe wagi dla konserwatywnego
        'on_chain': 0.06,
        'quant_power': 0.08,
    }
    
    # ICT Focus (dla Twojej strategii)
    ICT_FOCUS = {
        'ict_smart_money': 0.26,    # Główny moduł!
        'technical': 0.10,          # RSI, MACD
        'ml_ensemble': 0.06,        # ML wsparcie
        'time_series': 0.02,
        'sentiment': 0.06,
        'funding_rate': 0.03,
        'lstm': 0.00,
        'pairs_trading': 0.00,
        'risk_engine': 0.04,
        # 🔥 NEW MODULES - KEY ADVANTAGE!
        'rl_agent': 0.10,           # Agent uczący się z Twoich trade'ów
        'liquidation_heatmap': 0.12, # Widzi gdzie są stop lossy!
        'order_flow': 0.04,         # Czyta co robią wieloryby
        # 🆕 POWER MODULES
        'on_chain': 0.08,           # 🔗 On-chain data
        'quant_power': 0.09,        # ⚡ Quant libraries
    }
    
    # 🔥 ULTIMATE EDGE - Maksymalna przewaga
    ULTIMATE_EDGE = {
        'ict_smart_money': 0.22,    # ICT fundamentals
        'technical': 0.08,          # Basic TA
        'ml_ensemble': 0.06,        # ML backup
        'time_series': 0.02,
        'sentiment': 0.04,
        'funding_rate': 0.04,
        'lstm': 0.00,
        'pairs_trading': 0.00,
        'risk_engine': 0.04,
        # 🔥 EDGE MODULES
        'rl_agent': 0.10,           # Self-learning bot
        'liquidation_heatmap': 0.12, # Know where price MUST go
        'order_flow': 0.04,         # See whales in real-time
        'on_chain': 0.06,           # 🔗 On-chain whale tracking
        'quant_power': 0.06,        # ⚡ Full quant library power
        'institutional': 0.12,      # 🏛️ Kelly, HMM, Microstructure
    }
    
    # 🔥🔥🔥 FULL POWER - Wszystkie biblioteki aktywne
    FULL_POWER = {
        'ict_smart_money': 0.15,    # ICT fundamentals
        'technical': 0.06,          # Basic TA
        'ml_ensemble': 0.05,        # ML backup
        'time_series': 0.02,
        'sentiment': 0.04,
        'funding_rate': 0.03,
        'lstm': 0.00,
        'pairs_trading': 0.00,
        'risk_engine': 0.03,
        # 🔥 EDGE MODULES
        'rl_agent': 0.10,           # Self-learning bot
        'liquidation_heatmap': 0.12, # Know where price MUST go
        'order_flow': 0.05,         # CVD, Icebergs
        # 🆕 POWER MODULES
        'on_chain': 0.08,           # 🔗 Whale tracking
        'quant_power': 0.10,        # ⚡ FFN, GARCH, Risk metrics
        'institutional': 0.17,      # 🏛️ Kelly, HMM, Microstructure
    }
    
    # 🏛️🏛️🏛️ INSTITUTIONAL KILLER - POZIOM HEDGE FUND
    INSTITUTIONAL_KILLER = {
        'ict_smart_money': 0.12,    # ICT fundamentals
        'technical': 0.05,          # Minimal TA
        'ml_ensemble': 0.04,        # ML backup
        'time_series': 0.02,
        'sentiment': 0.03,
        'funding_rate': 0.03,
        'lstm': 0.00,
        'pairs_trading': 0.00,
        'risk_engine': 0.02,
        # 🔥 EDGE MODULES - 35%
        'rl_agent': 0.10,           # Self-learning agent
        'liquidation_heatmap': 0.12, # Liquidation magnets
        'order_flow': 0.05,         # Whale detection
        # 🆕 POWER MODULES - 25%
        'on_chain': 0.07,           # 🔗 On-chain signals
        'quant_power': 0.10,        # ⚡ Full quant power
        # 🏛️ INSTITUTIONAL - 25% (GŁÓWNA MOC!)
        'institutional': 0.25,      # 🏛️ Kelly + HMM + Microstructure
    }


# ═══════════════════════════════════════════════════════════════
# MODULE LOADERS
# ═══════════════════════════════════════════════════════════════

class ModuleLoader:
    """
    Bezpieczne ładowanie modułów.
    Jeśli moduł nie jest dostępny, zwraca neutralny wynik.
    """
    
    @staticmethod
    def load_ict_signal(btc_data: pd.DataFrame, eth_data: pd.DataFrame = None) -> ModuleResult:
        """Załaduj sygnał ICT Smart Money"""
        try:
            from ict_smart_money_bot import get_ict_signal
            
            result = get_ict_signal(btc_data, eth_data)
            
            return ModuleResult(
                module_name='ict_smart_money',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT['ict_smart_money'],
                reasons=result.get('reasons', [])
            )
        except Exception as e:
            logger.warning(f"ICT module error: {e}")
            return ModuleResult(
                module_name='ict_smart_money',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_technical_signal(data: pd.DataFrame) -> ModuleResult:
        """Załaduj sygnał techniczny"""
        try:
            from genius_trading_engine import GeniusTradingEngine
            
            engine = GeniusTradingEngine()
            
            market_data = {
                'prices': data['close'].tolist(),
                'highs': data['high'].tolist(),
                'lows': data['low'].tolist(),
                'volumes': data['volume'].tolist() if 'volume' in data else [0] * len(data),
            }
            
            result = engine.analyze(market_data)
            
            signal_map = {'STRONG BUY': 1.0, 'BUY': 0.6, 'NEUTRAL': 0, 'SELL': -0.6, 'STRONG SELL': -1.0}
            
            return ModuleResult(
                module_name='technical',
                signal=signal_map.get(result.get('signal', 'NEUTRAL'), 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT['technical'],
                reasons=result.get('reasons', [])
            )
        except Exception as e:
            logger.warning(f"Technical module error: {e}")
            return ModuleResult(
                module_name='technical',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_ml_signal(data: pd.DataFrame) -> ModuleResult:
        """Załaduj sygnał ML Ensemble"""
        try:
            from ml_models_extended import get_ml_confluence
            
            score, reasons = get_ml_confluence(data)
            
            return ModuleResult(
                module_name='ml_ensemble',
                signal=score,
                confidence=min(abs(score) + 0.3, 1.0),
                weight=ModuleWeights.DEFAULT['ml_ensemble'],
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"ML module error: {e}")
            return ModuleResult(
                module_name='ml_ensemble',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_time_series_signal(data: pd.DataFrame) -> ModuleResult:
        """Załaduj sygnał Time Series"""
        try:
            from time_series_analysis import get_time_series_confluence
            
            prices = data['close'].values
            score, reasons = get_time_series_confluence(prices)
            
            return ModuleResult(
                module_name='time_series',
                signal=score,
                confidence=min(abs(score) + 0.2, 1.0),
                weight=ModuleWeights.DEFAULT['time_series'],
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Time series module error: {e}")
            return ModuleResult(
                module_name='time_series',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_sentiment_signal(symbol: str = "BTC") -> ModuleResult:
        """Załaduj sygnał Sentiment"""
        try:
            from genius_sentiment_ai import get_sentiment_signal
            
            result = get_sentiment_signal(symbol)
            
            return ModuleResult(
                module_name='sentiment',
                signal=result.get('score', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT['sentiment'],
                reasons=result.get('reasons', [])
            )
        except Exception as e:
            logger.warning(f"Sentiment module error: {e}")
            return ModuleResult(
                module_name='sentiment',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_funding_rate_signal(symbol: str = "BTC") -> ModuleResult:
        """Załaduj sygnał Funding Rate"""
        try:
            from funding_rate_calculator import get_funding_rate_signal
            
            result = get_funding_rate_signal(symbol)
            
            return ModuleResult(
                module_name='funding_rate',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT['funding_rate'],
                reasons=result.get('reasons', [])
            )
        except Exception as e:
            logger.warning(f"Funding rate module error: {e}")
            return ModuleResult(
                module_name='funding_rate',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_lstm_signal(data: pd.DataFrame) -> ModuleResult:
        """Załaduj sygnał LSTM"""
        try:
            from genius_lstm_predictor import get_lstm_prediction
            
            prices = data['close'].values
            result = get_lstm_prediction(prices)
            
            return ModuleResult(
                module_name='lstm',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT['lstm'],
                reasons=result.get('reasons', [])
            )
        except Exception as e:
            logger.warning(f"LSTM module error: {e}")
            return ModuleResult(
                module_name='lstm',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    # ═══════════════════════════════════════════════════════════════
    # 🔥 NEW EDGE MODULES
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def load_rl_agent_signal(data: pd.DataFrame, model_path: str = None) -> ModuleResult:
        """
        🤖 Załaduj sygnał z Reinforcement Learning Agent.
        
        PRZEWAGA: Bot który uczy się z własnych transakcji!
        """
        try:
            from rl_trading_agent import get_rl_signal
            
            result = get_rl_signal(data, model_path)
            
            return ModuleResult(
                module_name='rl_agent',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('rl_agent', 0.1),
                reasons=result.get('reasons', ['RL Agent signal'])
            )
        except Exception as e:
            logger.warning(f"RL Agent module error: {e}")
            return ModuleResult(
                module_name='rl_agent',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_liquidation_heatmap_signal(current_price: float, 
                                         ohlcv_data: pd.DataFrame = None) -> ModuleResult:
        """
        🔥 Załaduj sygnał z Liquidation Heatmap.
        
        PRZEWAGA: Wiemy GDZIE cena musi pójść po płynność!
        """
        try:
            from liquidation_heatmap import get_liquidation_heatmap_signal
            
            result = get_liquidation_heatmap_signal(current_price, ohlcv_data)
            
            reasons = result.get('reasons', [])
            
            # Dodaj info o magnet zones
            if 'magnet_zones' in result and result['magnet_zones']:
                top_magnet = result['magnet_zones'][0]
                reasons.append(f"Top magnet: ${top_magnet['price']:,.0f} ({top_magnet['type']})")
            
            return ModuleResult(
                module_name='liquidation_heatmap',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('liquidation_heatmap', 0.1),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Liquidation Heatmap module error: {e}")
            return ModuleResult(
                module_name='liquidation_heatmap',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_order_flow_signal(orderbook_data: Dict = None,
                                trades_data: List[Dict] = None,
                                price_series: List[float] = None) -> ModuleResult:
        """
        📊 Załaduj sygnał z Order Flow Engine.
        
        PRZEWAGA: Widzimy co robią wieloryby w czasie rzeczywistym!
        """
        try:
            from order_flow_engine import get_order_flow_signal
            
            result = get_order_flow_signal(orderbook_data, trades_data, price_series)
            
            reasons = result.get('reasons', [])
            
            # Dodaj szczegóły
            details = result.get('details', {})
            if details.get('whale_flow', 0) != 0:
                flow_dir = "buying" if details['whale_flow'] > 0 else "selling"
                reasons.append(f"Whale flow: {flow_dir}")
            
            return ModuleResult(
                module_name='order_flow',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('order_flow', 0.05),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Order Flow module error: {e}")
            return ModuleResult(
                module_name='order_flow',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    # ═══════════════════════════════════════════════════════════════
    # 🆕 NEW POWER MODULES
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def load_on_chain_signal() -> ModuleResult:
        """
        🔗 Załaduj sygnał z On-Chain Analytics.
        
        PRZEWAGA: Śledzimy wieloryby na blockchainie!
        - Exchange flows (BTC/ETH wpływy/wypływy)
        - Whale transactions
        - Miner flows
        - ETF flows
        """
        try:
            from on_chain_analytics import get_on_chain_signal
            
            result = get_on_chain_signal()
            
            reasons = result.get('reasons', [])
            
            # Dodaj whale sentiment
            whale_sentiment = result.get('whale_sentiment', 'neutral')
            if whale_sentiment != 'neutral':
                reasons.append(f"🐋 Whale sentiment: {whale_sentiment}")
            
            return ModuleResult(
                module_name='on_chain',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('on_chain', 0.08),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"On-Chain module error: {e}")
            return ModuleResult(
                module_name='on_chain',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_quant_power_signal(prices: pd.Series, benchmark: pd.Series = None) -> ModuleResult:
        """
        ⚡ Załaduj sygnał z Quant Power Engine.
        
        WYKORZYSTUJE BIBLIOTEKI:
        - ffn: Performance metrics, Sharpe, Sortino
        - scipy: VaR, CVaR, optimization
        - arch: GARCH volatility forecasting
        - sklearn: ML predictions
        
        PRZEWAGA: Profesjonalne narzędzia kwantowe!
        """
        try:
            from quant_power_engine import get_quant_signal
            
            result = get_quant_signal(prices, benchmark)
            
            reasons = result.get('reasons', [])
            
            # Dodaj info o reżimie
            regime = result.get('regime', 'unknown')
            reasons.append(f"⚡ Market regime: {regime}")
            
            # Dodaj Sharpe jeśli znaczący
            sharpe = result.get('sharpe_ratio', 0)
            if abs(sharpe) > 0.5:
                reasons.append(f"📊 Sharpe Ratio: {sharpe:.2f}")
            
            return ModuleResult(
                module_name='quant_power',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('quant_power', 0.08),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Quant Power module error: {e}")
            return ModuleResult(
                module_name='quant_power',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_institutional_signal(prices: pd.Series, bid: float = 0, ask: float = 0) -> ModuleResult:
        """
        🏛️ Załaduj sygnał z Institutional Edge Engine.
        
        KOMPONENTY INSTYTUCJONALNE:
        - Kelly Criterion: Matematycznie optymalna wielkość pozycji
        - Hidden Markov Model: Wykrywanie ukrytych stanów rynku
        - Microstructure Analysis: Spread, imbalance, toxicity
        - Alpha Decay Monitor: Czy strategia traci edge?
        - Smart Execution: TWAP, VWAP, minimalizacja slippage
        
        PRZEWAGA: Poziom profesjonalnego funduszu hedgingowego!
        """
        try:
            from institutional_edge import get_institutional_signal
            
            result = get_institutional_signal(
                prices=prices,
                bid=bid,
                ask=ask,
                base_confidence=0.6
            )
            
            reasons = result.get('reasons', [])
            
            # Dodaj info o Kelly sizing
            kelly_size = result.get('kelly_size', 50)
            reasons.append(f"🎯 Kelly optimal: ${kelly_size}")
            
            # Dodaj alpha health
            alpha = result.get('alpha_health', 'unknown')
            if alpha != 'unknown':
                reasons.append(f"📈 Alpha: {alpha}")
            
            return ModuleResult(
                module_name='institutional',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('institutional', 0.10),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Institutional module error: {e}")
            return ModuleResult(
                module_name='institutional',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    # ═══════════════════════════════════════════════════════════════
    # 🆕 ADVANCED STRATEGIES (from advanced_trading_strategies.py)
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def load_twap_signal(current_price: float, vwap: float) -> ModuleResult:
        """
        📊 TWAP (Time-Weighted Average Price) Signal
        
        Gdy cena < VWAP - lepiej kupować
        Gdy cena > VWAP - lepiej sprzedawać
        """
        try:
            from advanced_trading_strategies import get_twap_signal
            
            result = get_twap_signal(current_price, vwap)
            
            return ModuleResult(
                module_name='twap',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('twap', 0.03),
                reasons=[f"TWAP: {result.get('action', 'UNKNOWN')} (dev: {result.get('deviation_pct', 0):.2f}%)"]
            )
        except Exception as e:
            logger.warning(f"TWAP module error: {e}")
            return ModuleResult(
                module_name='twap',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_seasonality_signal() -> ModuleResult:
        """
        📅 Seasonality Signal
        
        Wzorce czasowe: dzień tygodnia, pora dnia, miesiąc
        """
        try:
            from advanced_trading_strategies import get_seasonality_signal
            
            result = get_seasonality_signal()
            
            reasons = [
                f"Session: {result.get('session', 'UNKNOWN')}",
                f"Day: {result.get('day_name', 'UNKNOWN')} bias={result.get('day_bias', 0):.2f}",
            ]
            if result.get('special_events'):
                reasons.append(f"Events: {', '.join(result['special_events'])}")
            
            return ModuleResult(
                module_name='seasonality',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('seasonality', 0.03),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Seasonality module error: {e}")
            return ModuleResult(
                module_name='seasonality',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_market_making_signal(bid: float, ask: float) -> ModuleResult:
        """
        📊 Market Making / Liquidity Signal
        
        Analizuje spread i płynność - unika tradowania przy złej płynności
        """
        try:
            from advanced_trading_strategies import get_market_making_signal
            
            result = get_market_making_signal(bid, ask)
            
            spread_bps = (ask - bid) / ((bid + ask) / 2) * 10000
            
            return ModuleResult(
                module_name='market_making',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('market_making', 0.02),
                reasons=[f"Spread: {spread_bps:.1f}bps, Liquidity: {'GOOD' if result.get('signal', 0) >= 0 else 'LOW'}"]
            )
        except Exception as e:
            logger.warning(f"Market Making module error: {e}")
            return ModuleResult(
                module_name='market_making',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_whale_alert_signal() -> ModuleResult:
        """
        🐋 Whale Alert Signal
        
        Monitoruje duże transakcje BTC:
        - Exchange → Wallet = BULLISH (whales accumulating)
        - Wallet → Exchange = BEARISH (whales selling)
        """
        try:
            from whale_alert_tracker import get_whale_alert_signal
            
            result = get_whale_alert_signal()
            
            direction = result.get('direction', 'NEUTRAL')
            
            return ModuleResult(
                module_name='whale_alert',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('whale_alert', 0.02),
                reasons=[
                    f"Whale Direction: {direction}",
                    f"Recent alerts: {len(result.get('recent_alerts', []))}"
                ]
            )
        except Exception as e:
            logger.warning(f"Whale Alert module error: {e}")
            return ModuleResult(
                module_name='whale_alert',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_orderbook_depth_signal(symbol: str = "BTCUSDT") -> ModuleResult:
        """
        📊 Order Book Depth Signal
        
        Analizuje głębokość order book:
        - Bid walls = SUPPORT
        - Ask walls = RESISTANCE
        - Imbalance = przewaga kupujących/sprzedających
        """
        try:
            from orderbook_depth_analyzer import get_orderbook_signal
            
            result = get_orderbook_signal(symbol)
            
            reasons = [
                f"Imbalance: {result.get('imbalance', 0):.2f}",
                f"Direction: {result.get('direction', 'NEUTRAL')}",
                f"Spread: {result.get('spread_bps', 0):.1f}bps"
            ]
            
            bid_wall = result.get('bid_wall', {})
            ask_wall = result.get('ask_wall', {})
            
            if bid_wall.get('size_usd', 0) > 5_000_000:
                reasons.append(f"Bid wall: ${bid_wall['price']:,.0f}")
            if ask_wall.get('size_usd', 0) > 5_000_000:
                reasons.append(f"Ask wall: ${ask_wall['price']:,.0f}")
            
            return ModuleResult(
                module_name='orderbook_depth',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('orderbook_depth', 0.02),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Order Book Depth module error: {e}")
            return ModuleResult(
                module_name='orderbook_depth',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_momentum_signal(prices: pd.Series, benchmark: pd.Series = None) -> ModuleResult:
        """
        🚀 Momentum Trading Signal
        
        Strategia momentum jak w hedge fundach (AQR, Two Sigma):
        - Time-Series Momentum (trend following)
        - Cross-Sectional Momentum (relative strength)
        - Risk-Adjusted Momentum
        - Dual Momentum (Antonacci)
        """
        try:
            from momentum_trading import get_momentum_signal
            
            result = get_momentum_signal(prices, benchmark)
            
            reasons = [
                f"Direction: {result.get('direction', 'NEUTRAL')}",
                f"Regime: {result.get('regime', 'UNKNOWN')}",
                f"Trend Strength: {result.get('trend_strength', 0):.2f}",
                f"Acceleration: {result.get('acceleration', 0):.2f}"
            ]
            
            return ModuleResult(
                module_name='momentum',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('momentum', 0.03),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Momentum module error: {e}")
            return ModuleResult(
                module_name='momentum',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_event_driven_signal() -> ModuleResult:
        """
        📰 Event-Driven Trading Signal
        
        Reaguje na newsy i wydarzenia:
        - Breaking news (ETF, regulations, hacks)
        - Scheduled events (FOMC, CPI)
        - Social sentiment spikes
        """
        try:
            from event_driven_trading import get_event_driven_signal
            
            result = get_event_driven_signal()
            
            reasons = [
                f"Impact: {result.get('impact_level', 'LOW')}",
                f"Time Sensitivity: {result.get('time_sensitivity', 'MEDIUM_TERM')}"
            ]
            if result.get('trigger_event'):
                reasons.append(f"Trigger: {result.get('trigger_event', '')[:50]}")
            
            return ModuleResult(
                module_name='event_driven',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('event_driven', 0.03),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Event-Driven module error: {e}")
            return ModuleResult(
                module_name='event_driven',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_divergence_signal(prices: pd.Series) -> ModuleResult:
        """
        📐 Divergence Detection Signal
        
        Wykrywa rozbieżności cena vs wskaźniki:
        - Regular Divergence (reversal signal)
        - Hidden Divergence (continuation)
        - Multi-indicator confirmation
        """
        try:
            from divergence_detector import get_divergence_signal
            
            result = get_divergence_signal(prices)
            
            reasons = [
                f"Type: {result.get('divergence_type', 'NONE')}",
                f"Indicator: {result.get('indicator', 'NONE')}",
                f"Strength: {result.get('strength', 'WEAK')}"
            ]
            
            return ModuleResult(
                module_name='divergence',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('divergence', 0.03),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"Divergence module error: {e}")
            return ModuleResult(
                module_name='divergence',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )
    
    @staticmethod
    def load_mtf_confluence_signal(prices: pd.Series) -> ModuleResult:
        """
        🔍 Multi-Timeframe Confluence Signal
        
        Analizuje alignment między timeframe'ami:
        - HTF (trend direction)
        - MTF (entry timing)
        - LTF (precision entry)
        
        Sygnał tylko gdy wszystkie TF się zgadzają!
        """
        try:
            from multi_timeframe_confluence import get_mtf_signal
            
            result = get_mtf_signal(prices)
            
            aligned_str = "✅ ALIGNED" if result.get('aligned', False) else "❌ NOT ALIGNED"
            
            reasons = [
                f"HTF: {result.get('htf_bias', 'NEUTRAL')}",
                f"MTF: {result.get('mtf_signal', 'NEUTRAL')}",
                f"LTF: {result.get('ltf_trigger', 'NEUTRAL')}",
                aligned_str
            ]
            
            return ModuleResult(
                module_name='mtf_confluence',
                signal=result.get('signal', 0),
                confidence=result.get('confidence', 0.5),
                weight=ModuleWeights.DEFAULT.get('mtf_confluence', 0.02),
                reasons=reasons
            )
        except Exception as e:
            logger.warning(f"MTF Confluence module error: {e}")
            return ModuleResult(
                module_name='mtf_confluence',
                signal=0, confidence=0, weight=0,
                reasons=[], active=False, error=str(e)
            )


# ═══════════════════════════════════════════════════════════════
# GENIUS BRAIN - GŁÓWNY MÓZG
# ═══════════════════════════════════════════════════════════════

class GeniusBrain:
    """
    🧠 GŁÓWNY MÓZG SYSTEMU
    
    Zbiera sygnały ze WSZYSTKICH modułów i podejmuje ostateczną decyzję.
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Args:
            weights: Własne wagi modułów (opcjonalne)
        """
        self.weights = weights or ModuleWeights.ICT_FOCUS
        self._normalize_weights()
        
        self.last_decision: Optional[BrainDecision] = None
        self.history: List[BrainDecision] = []
    
    def _normalize_weights(self):
        """Upewnij się że wagi sumują się do 1"""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in self.weights.items()}
    
    def set_weights(self, weights: Dict[str, float]):
        """Zmień wagi modułów"""
        self.weights = weights
        self._normalize_weights()
    
    def think(self, 
              btc_data: pd.DataFrame,
              eth_data: pd.DataFrame = None,
              symbol: str = "BTC") -> BrainDecision:
        """
        🧠 GŁÓWNA FUNKCJA - Zbierz wszystkie sygnały i podejmij decyzję
        
        Args:
            btc_data: OHLCV DataFrame dla BTC
            eth_data: OHLCV DataFrame dla ETH (opcjonalne, dla SMT)
            symbol: Symbol (dla sentiment, funding)
        
        Returns:
            BrainDecision - ostateczna decyzja
        """
        logger.info("🧠 Brain thinking...")
        
        current_price = btc_data['close'].iloc[-1]
        
        # ═══ ZBIERZ SYGNAŁY ZE WSZYSTKICH MODUŁÓW ═══
        
        module_results = {}
        
        # 1. ICT Smart Money (główny!)
        result = ModuleLoader.load_ict_signal(btc_data, eth_data)
        result.weight = self.weights.get('ict_smart_money', 0.25)
        module_results['ict_smart_money'] = result
        logger.info(f"  ICT: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 2. Technical Analysis
        result = ModuleLoader.load_technical_signal(btc_data)
        result.weight = self.weights.get('technical', 0.15)
        module_results['technical'] = result
        logger.info(f"  Technical: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 3. ML Ensemble
        result = ModuleLoader.load_ml_signal(btc_data)
        result.weight = self.weights.get('ml_ensemble', 0.15)
        module_results['ml_ensemble'] = result
        logger.info(f"  ML: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 4. Time Series
        result = ModuleLoader.load_time_series_signal(btc_data)
        result.weight = self.weights.get('time_series', 0.10)
        module_results['time_series'] = result
        logger.info(f"  TimeSeries: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 5. Sentiment
        result = ModuleLoader.load_sentiment_signal(symbol)
        result.weight = self.weights.get('sentiment', 0.10)
        module_results['sentiment'] = result
        logger.info(f"  Sentiment: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 6. Funding Rate
        result = ModuleLoader.load_funding_rate_signal(symbol)
        result.weight = self.weights.get('funding_rate', 0.10)
        module_results['funding_rate'] = result
        logger.info(f"  FundingRate: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 7. LSTM (opcjonalnie)
        if self.weights.get('lstm', 0) > 0:
            result = ModuleLoader.load_lstm_signal(btc_data)
            result.weight = self.weights.get('lstm', 0.05)
            module_results['lstm'] = result
        
        # ═══════════════════════════════════════════════════════════════
        # 🔥 NEW EDGE MODULES - TWOJA PRZEWAGA!
        # ═══════════════════════════════════════════════════════════════
        
        # 8. RL Agent (self-learning bot)
        if self.weights.get('rl_agent', 0) > 0:
            result = ModuleLoader.load_rl_agent_signal(btc_data)
            result.weight = self.weights.get('rl_agent', 0.10)
            module_results['rl_agent'] = result
            logger.info(f"  🤖 RL Agent: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 9. Liquidation Heatmap (widzi gdzie są stop lossy!)
        if self.weights.get('liquidation_heatmap', 0) > 0:
            result = ModuleLoader.load_liquidation_heatmap_signal(current_price, btc_data)
            result.weight = self.weights.get('liquidation_heatmap', 0.10)
            module_results['liquidation_heatmap'] = result
            logger.info(f"  🔥 Liquidation: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 10. Order Flow (czyta wieloryby w real-time)
        if self.weights.get('order_flow', 0) > 0:
            price_series = btc_data['close'].tolist()
            result = ModuleLoader.load_order_flow_signal(price_series=price_series)
            result.weight = self.weights.get('order_flow', 0.05)
            module_results['order_flow'] = result
            logger.info(f"  🐋 OrderFlow: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # ═══════════════════════════════════════════════════════════════
        # 🆕 NEW POWER MODULES - Wykorzystują biblioteki kwantowe!
        # ═══════════════════════════════════════════════════════════════
        
        # 11. On-Chain Analytics (wieloryby na blockchainie)
        if self.weights.get('on_chain', 0) > 0:
            result = ModuleLoader.load_on_chain_signal()
            result.weight = self.weights.get('on_chain', 0.08)
            module_results['on_chain'] = result
            logger.info(f"  🔗 OnChain: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 12. Quant Power Engine (ffn, scipy, GARCH, VaR)
        if self.weights.get('quant_power', 0) > 0:
            prices = btc_data['close']
            eth_prices = eth_data['close'] if eth_data is not None else None
            result = ModuleLoader.load_quant_power_signal(prices, eth_prices)
            result.weight = self.weights.get('quant_power', 0.08)
            module_results['quant_power'] = result
            logger.info(f"  ⚡ QuantPower: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # ═══════════════════════════════════════════════════════════════
        # 🏛️ INSTITUTIONAL EDGE - POZIOM HEDGE FUND
        # ═══════════════════════════════════════════════════════════════
        
        # 13. Institutional Edge (Kelly, HMM, Microstructure)
        if self.weights.get('institutional', 0) > 0:
            prices = btc_data['close']
            # Spróbuj pobrać bid/ask z orderbooka
            bid = current_price * 0.9999  # Domyślny spread
            ask = current_price * 1.0001
            result = ModuleLoader.load_institutional_signal(prices, bid, ask)
            result.weight = self.weights.get('institutional', 0.10)
            module_results['institutional'] = result
            logger.info(f"  🏛️ Institutional: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # ═══════════════════════════════════════════════════════════════
        # 🐋 WHALE & ORDER BOOK - WAŻNE DANE!
        # ═══════════════════════════════════════════════════════════════
        
        # 14. Whale Alert Tracker (monitoruje duże transakcje)
        if self.weights.get('whale_alert', 0) > 0:
            result = ModuleLoader.load_whale_alert_signal()
            result.weight = self.weights.get('whale_alert', 0.02)
            module_results['whale_alert'] = result
            logger.info(f"  🐋 WhaleAlert: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 15. Order Book Depth (Level 2 data z Binance)
        if self.weights.get('orderbook_depth', 0) > 0:
            result = ModuleLoader.load_orderbook_depth_signal("BTCUSDT")
            result.weight = self.weights.get('orderbook_depth', 0.02)
            module_results['orderbook_depth'] = result
            logger.info(f"  📊 OrderBook: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # ═══════════════════════════════════════════════════════════════
        # 🚀 MOMENTUM - HEDGE FUND STRATEGY!
        # ═══════════════════════════════════════════════════════════════
        
        # 16. Momentum Trading (Time-Series + Cross-Sectional)
        if self.weights.get('momentum', 0) > 0:
            prices = btc_data['close']
            benchmark = eth_data['close'] if eth_data is not None else None
            result = ModuleLoader.load_momentum_signal(prices, benchmark)
            result.weight = self.weights.get('momentum', 0.03)
            module_results['momentum'] = result
            logger.info(f"  🚀 Momentum: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # ═══════════════════════════════════════════════════════════════
        # 📰 ADVANCED STRATEGIES - ZAMIENIONE NA LEPSZE!
        # ═══════════════════════════════════════════════════════════════
        
        # 17. Event-Driven Trading (News Reaction)
        if self.weights.get('event_driven', 0) > 0:
            result = ModuleLoader.load_event_driven_signal()
            result.weight = self.weights.get('event_driven', 0.03)
            module_results['event_driven'] = result
            logger.info(f"  📰 EventDriven: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 18. Divergence Detection (RSI/MACD vs Price)
        if self.weights.get('divergence', 0) > 0:
            prices = btc_data['close']
            result = ModuleLoader.load_divergence_signal(prices)
            result.weight = self.weights.get('divergence', 0.03)
            module_results['divergence'] = result
            logger.info(f"  📐 Divergence: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # 19. Multi-Timeframe Confluence
        if self.weights.get('mtf_confluence', 0) > 0:
            prices = btc_data['close']
            result = ModuleLoader.load_mtf_confluence_signal(prices)
            result.weight = self.weights.get('mtf_confluence', 0.02)
            module_results['mtf_confluence'] = result
            logger.info(f"  🔍 MTF: signal={result.signal:.2f}, conf={result.confidence:.2f}")
        
        # ═══ OBLICZ KOŃCOWY SYGNAŁ ═══
        
        final_score, confidence, warnings = self._calculate_final_score(module_results)
        
        # ═══ OKREŚL AKCJĘ ═══
        
        action = self._determine_action(final_score, confidence)
        
        # ═══ OBLICZ PARAMETRY TRADE'A ═══
        
        atr = self._calculate_atr(btc_data)
        stop_loss, take_profit = self._calculate_sl_tp(current_price, final_score, atr)
        position_size_pct = self._calculate_position_size(confidence, final_score)
        
        # ═══ ZBIERZ REASONS ═══
        
        reasons = self._compile_reasons(module_results, final_score, action)
        
        # ═══ STWÓRZ DECYZJĘ ═══
        
        decision = BrainDecision(
            action=action,
            final_score=final_score,
            confidence=confidence,
            module_results=module_results,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size_pct=position_size_pct,
            reasons=reasons,
            warnings=warnings
        )
        
        self.last_decision = decision
        self.history.append(decision)
        
        return decision
    
    def _calculate_final_score(self, results: Dict[str, ModuleResult]) -> Tuple[float, float, List[str]]:
        """Oblicz końcowy score z ważoną średnią"""
        warnings = []
        
        # Filtruj aktywne moduły
        active_results = {k: v for k, v in results.items() if v.active}
        
        if not active_results:
            return 0, 0, ["No active modules!"]
        
        # Ważona średnia
        weighted_sum = 0
        weight_sum = 0
        confidences = []
        
        for name, result in active_results.items():
            weighted_sum += result.weighted_signal()
            weight_sum += result.weight * result.confidence
            confidences.append(result.confidence)
        
        final_score = weighted_sum / weight_sum if weight_sum > 0 else 0
        
        # Sprawdź agreement
        bullish = sum(1 for r in active_results.values() if r.signal > 0.1)
        bearish = sum(1 for r in active_results.values() if r.signal < -0.1)
        
        if bullish > 0 and bearish > 0:
            conflict_ratio = min(bullish, bearish) / max(bullish, bearish)
            if conflict_ratio > 0.4:
                warnings.append(f"⚠️ Konflikty sygnałów: {bullish} bullish vs {bearish} bearish")
                final_score *= 0.7
        
        # Confidence jako średnia ważona
        confidence = np.average(confidences, weights=[r.weight for r in active_results.values()])
        
        # Zmniejsz confidence jeśli są nieaktywne moduły
        inactive_count = sum(1 for r in results.values() if not r.active)
        if inactive_count > 2:
            warnings.append(f"⚠️ {inactive_count} modułów nieaktywnych")
            confidence *= 0.8
        
        return final_score, confidence, warnings
    
    def _determine_action(self, score: float, confidence: float) -> str:
        """Określ akcję na podstawie score'a"""
        if confidence < 0.4:
            return "NEUTRAL"
        
        if score >= 0.6:
            return "STRONG_LONG"
        elif score >= 0.3:
            return "LONG"
        elif score <= -0.6:
            return "STRONG_SHORT"
        elif score <= -0.3:
            return "SHORT"
        else:
            return "NEUTRAL"
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Oblicz ATR"""
        highs = data['high'].values
        lows = data['low'].values
        closes = data['close'].values
        
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        
        return np.mean(tr[-period:])
    
    def _calculate_sl_tp(self, price: float, score: float, atr: float) -> Tuple[float, float]:
        """Oblicz Stop Loss i Take Profit"""
        # SL: 2x ATR
        # TP: 6x ATR (minimum 1:3 R:R)
        
        if score > 0:  # Long
            stop_loss = price - (atr * 2)
            take_profit = price + (atr * 6)  # 1:3 R:R
        else:  # Short
            stop_loss = price + (atr * 2)
            take_profit = price - (atr * 6)
        
        return stop_loss, take_profit
    
    def _calculate_position_size(self, confidence: float, score: float) -> float:
        """Oblicz wielkość pozycji (% kapitału)"""
        # Bazowa wielkość: 5% kapitału
        base_size = 5.0
        
        # Skaluj przez confidence i siłę sygnału
        size = base_size * confidence * min(abs(score) + 0.3, 1.0)
        
        # Min 1%, max 5%
        return max(1.0, min(size, 5.0))
    
    def _compile_reasons(self, results: Dict[str, ModuleResult], 
                         score: float, action: str) -> List[str]:
        """Zbierz uzasadnienie"""
        reasons = []
        
        # Główny kierunek
        if score > 0.1:
            reasons.append(f"📈 Bullish confluence: {score:.2f}")
        elif score < -0.1:
            reasons.append(f"📉 Bearish confluence: {score:.2f}")
        else:
            reasons.append("➡️ Brak jasnego kierunku")
        
        # Top 3 contributors
        sorted_results = sorted(
            results.items(),
            key=lambda x: abs(x[1].weighted_signal()),
            reverse=True
        )
        
        for name, result in sorted_results[:3]:
            if result.active:
                direction = "↑" if result.signal > 0 else "↓" if result.signal < 0 else "→"
                reasons.append(f"{name}: {direction} ({result.signal:.2f})")
        
        # Dodaj reasons z ICT jeśli dostępne
        ict_result = results.get('ict_smart_money')
        if ict_result and ict_result.active and ict_result.reasons:
            reasons.extend(ict_result.reasons[:2])
        
        return reasons
    
    def generate_report_pl(self) -> str:
        """Generuj raport po polsku"""
        if not self.last_decision:
            return "Brak decyzji do wyświetlenia"
        
        d = self.last_decision
        
        report = "\n" + "=" * 60
        report += "\n🧠 GENIUS BRAIN - RAPORT DECYZJI"
        report += "\n" + "=" * 60
        
        # Główna decyzja
        action_emoji = {
            'STRONG_LONG': '🚀',
            'LONG': '📈',
            'NEUTRAL': '➡️',
            'SHORT': '📉',
            'STRONG_SHORT': '💥'
        }
        
        report += f"\n\n🎯 DECYZJA: {action_emoji.get(d.action, '')} {d.action}"
        report += f"\n   Score: {d.final_score:.2f} | Pewność: {d.confidence:.0%}"
        
        # Parametry trade'a
        if d.action != 'NEUTRAL':
            report += f"\n\n💰 PARAMETRY TRADE'A:"
            report += f"\n   Wejście: ${d.entry_price:,.2f}"
            report += f"\n   Stop Loss: ${d.stop_loss:,.2f}"
            report += f"\n   Take Profit: ${d.take_profit:,.2f}"
            report += f"\n   Wielkość pozycji: {d.position_size_pct:.1f}% kapitału"
        
        # Moduły
        report += f"\n\n📊 SYGNAŁY MODUŁÓW:"
        
        for name, result in d.module_results.items():
            if result.active:
                direction = "📈" if result.signal > 0.1 else "📉" if result.signal < -0.1 else "➡️"
                report += f"\n   {direction} {name}: {result.signal:.2f} (waga: {result.weight:.0%})"
            else:
                report += f"\n   ❌ {name}: nieaktywny"
        
        # Reasons
        if d.reasons:
            report += f"\n\n📝 UZASADNIENIE:"
            for reason in d.reasons:
                report += f"\n   {reason}"
        
        # Warnings
        if d.warnings:
            report += f"\n\n⚠️ OSTRZEŻENIA:"
            for warning in d.warnings:
                report += f"\n   {warning}"
        
        report += "\n\n" + "=" * 60
        
        return report


# ═══════════════════════════════════════════════════════════════
# QUICK FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_brain_decision(btc_data: pd.DataFrame,
                       eth_data: pd.DataFrame = None,
                       symbol: str = "BTC",
                       weights: Dict[str, float] = None) -> Dict:
    """
    Szybka funkcja do uzyskania decyzji Brain.
    
    Returns:
        Dict z decyzją
    """
    brain = GeniusBrain(weights)
    decision = brain.think(btc_data, eth_data, symbol)
    return decision.to_dict()


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 GENIUS BRAIN - TEST")
    print("=" * 60)
    
    # Generate sample data
    np.random.seed(42)
    n = 200
    
    prices = 100000 * np.exp(np.cumsum(np.random.randn(n) * 0.02))
    
    btc_data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(n) * 0.01)),
        'low': prices * (1 - np.abs(np.random.randn(n) * 0.01)),
        'close': prices,
        'volume': np.random.randint(1000, 10000, n)
    })
    
    eth_prices = 3500 * np.exp(np.cumsum(np.random.randn(n) * 0.025))
    
    eth_data = pd.DataFrame({
        'open': eth_prices * (1 + np.random.randn(n) * 0.005),
        'high': eth_prices * (1 + np.abs(np.random.randn(n) * 0.01)),
        'low': eth_prices * (1 - np.abs(np.random.randn(n) * 0.01)),
        'close': eth_prices,
        'volume': np.random.randint(5000, 50000, n)
    })
    
    # Test z różnymi wagami
    print("\n1️⃣ TEST Z WAGAMI ICT FOCUS")
    print("-" * 40)
    
    brain = GeniusBrain(ModuleWeights.ICT_FOCUS)
    decision = brain.think(btc_data, eth_data, "BTC")
    
    print(brain.generate_report_pl())
    
    print("\n2️⃣ TEST Z WAGAMI AGGRESSIVE")
    print("-" * 40)
    
    brain.set_weights(ModuleWeights.AGGRESSIVE)
    decision = brain.think(btc_data, eth_data, "BTC")
    
    print(f"Decyzja: {decision.action}, Score: {decision.final_score:.2f}")
    
    print("\n3️⃣ TEST Z WAGAMI CONSERVATIVE")
    print("-" * 40)
    
    brain.set_weights(ModuleWeights.CONSERVATIVE)
    decision = brain.think(btc_data, eth_data, "BTC")
    
    print(f"Decyzja: {decision.action}, Score: {decision.final_score:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Genius Brain Ready!")
    print("=" * 60)
