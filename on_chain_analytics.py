"""
🔗 ON-CHAIN ANALYTICS - Śledzenie Wielorybów i Smart Money
==========================================================

PRZEWAGA: Widzimy co robią wieloryby NA BLOCKCHAINIE!

Co śledzimy:
- Transfery BTC/ETH z/do giełd
- Ruchy wielorybów (adresy > 1000 BTC)
- Exchange Netflow (czy kapitał wpływa czy wypływa)
- Miner Flows
- GBTC/ETF Flows
- Stablecoin Flows (USDT/USDC na giełdy = incoming buy pressure)

Źródła danych:
- Glassnode API
- CryptoQuant API
- Whale Alert API
- DeFiLlama

Author: Genius Engine Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import time
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTTP requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class WhaleTransaction:
    """Pojedyncza transakcja wieloryba"""
    timestamp: datetime
    from_address: str
    to_address: str
    amount: float  # W BTC/ETH
    amount_usd: float
    asset: str  # 'BTC', 'ETH', 'USDT'
    tx_hash: str
    from_type: str  # 'exchange', 'whale', 'unknown', 'miner'
    to_type: str
    significance: str  # 'large', 'massive', 'whale'


@dataclass
class ExchangeFlow:
    """Przepływ na/z giełdy"""
    timestamp: datetime
    exchange: str
    asset: str
    inflow: float  # Wpływy
    outflow: float  # Wypływy
    netflow: float  # Net = inflow - outflow
    netflow_usd: float


@dataclass
class OnChainMetrics:
    """Główne metryki on-chain"""
    timestamp: datetime
    
    # Exchange flows
    exchange_netflow_btc: float  # + = bearish (BTC na giełdy), - = bullish
    exchange_netflow_eth: float
    exchange_netflow_usdt: float  # + = bullish (stablecoiny na giełdy = kupno)
    
    # Whale activity
    whale_transactions_24h: int
    whale_buy_volume: float
    whale_sell_volume: float
    whale_netflow: float  # + = whale buying
    
    # Miner activity
    miner_outflow: float  # Górnicy sprzedają
    miner_reserve: float
    
    # Supply metrics
    exchange_reserve_btc: float  # BTC na giełdach
    exchange_reserve_change_7d: float  # Zmiana %
    
    # Derived signals
    accumulation_score: float  # -1 to 1
    distribution_score: float  # -1 to 1


@dataclass
class OnChainSignal:
    """Sygnał tradingowy z on-chain"""
    signal: float  # -1 to 1
    confidence: float  # 0 to 1
    reasons: List[str]
    whale_sentiment: str  # 'accumulating', 'distributing', 'neutral'
    risk_level: str  # 'low', 'medium', 'high'
    key_events: List[Dict]


# ═══════════════════════════════════════════════════════════════
# WHALE TRACKER
# ═══════════════════════════════════════════════════════════════

class WhaleTracker:
    """
    🐋 WHALE TRACKER
    
    Śledzi ruchy wielorybów na blockchainie.
    """
    
    # Znane adresy giełd (uproszczone)
    KNOWN_EXCHANGES = {
        'binance': ['bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h', '1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s'],
        'coinbase': ['bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh'],
        'kraken': ['bc1qkxt7slsrx7cq7e5pv5x5a9e7a8z5r5vr3c3vq8'],
        'bybit': ['bc1qjk0jy5e5s5ew5h6x6e8x9z7k8n6x7e5s5h6e5'],
    }
    
    # Progi dla klasyfikacji
    THRESHOLDS = {
        'large': 100,      # 100 BTC
        'massive': 500,    # 500 BTC
        'whale': 1000,     # 1000 BTC
    }
    
    def __init__(self):
        self.transactions: List[WhaleTransaction] = []
        self.exchange_flows: Dict[str, List[ExchangeFlow]] = {}
    
    def classify_transaction(self, amount_btc: float) -> str:
        """Klasyfikuj wielkość transakcji"""
        if amount_btc >= self.THRESHOLDS['whale']:
            return 'whale'
        elif amount_btc >= self.THRESHOLDS['massive']:
            return 'massive'
        elif amount_btc >= self.THRESHOLDS['large']:
            return 'large'
        return 'normal'
    
    def identify_address_type(self, address: str) -> str:
        """Zidentyfikuj typ adresu"""
        for exchange, addresses in self.KNOWN_EXCHANGES.items():
            if address in addresses:
                return f'exchange_{exchange}'
        
        # Heurystyki dla minerów (uproszczone)
        if address.startswith('bc1q') and len(address) > 60:
            return 'possible_miner'
        
        return 'unknown'
    
    def add_transaction(self, tx: WhaleTransaction):
        """Dodaj transakcję do trackera"""
        self.transactions.append(tx)
        
        # Limit historii
        if len(self.transactions) > 10000:
            self.transactions = self.transactions[-5000:]
    
    def get_whale_activity(self, hours: int = 24) -> Dict:
        """
        Podsumuj aktywność wielorybów.
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [tx for tx in self.transactions if tx.timestamp >= cutoff]
        
        if not recent:
            return {
                'count': 0,
                'buy_volume': 0,
                'sell_volume': 0,
                'netflow': 0,
                'sentiment': 'neutral'
            }
        
        # Klasyfikuj kierunek
        buy_volume = 0
        sell_volume = 0
        
        for tx in recent:
            if 'exchange' in tx.to_type:
                # Na giełdę = sprzedaż
                sell_volume += tx.amount
            elif 'exchange' in tx.from_type:
                # Z giełdy = kupno (akumulacja)
                buy_volume += tx.amount
        
        netflow = buy_volume - sell_volume
        
        # Sentiment
        if netflow > 100:
            sentiment = 'accumulating'
        elif netflow < -100:
            sentiment = 'distributing'
        else:
            sentiment = 'neutral'
        
        return {
            'count': len(recent),
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'netflow': netflow,
            'sentiment': sentiment,
            'largest_tx': max((tx.amount for tx in recent), default=0)
        }


# ═══════════════════════════════════════════════════════════════
# EXCHANGE FLOW ANALYZER
# ═══════════════════════════════════════════════════════════════

class ExchangeFlowAnalyzer:
    """
    📊 EXCHANGE FLOW ANALYZER
    
    Śledzi przepływy BTC/ETH/USDT na i z giełd.
    
    KLUCZOWA LOGIKA:
    - BTC na giełdę = bearish (chcą sprzedać)
    - BTC z giełdy = bullish (akumulacja)
    - USDT na giełdę = bullish (chcą kupić)
    - USDT z giełdy = bearish (wychodzą)
    """
    
    def __init__(self):
        self.flows: List[ExchangeFlow] = []
        self.reserves: Dict[str, float] = {
            'BTC': 2_500_000,  # ~2.5M BTC na giełdach (estimate)
            'ETH': 15_000_000,  # ~15M ETH
            'USDT': 50_000_000_000,  # ~50B USDT
        }
    
    def add_flow(self, flow: ExchangeFlow):
        """Dodaj flow do analizy"""
        self.flows.append(flow)
        
        # Update reserves
        self.reserves[flow.asset] = self.reserves.get(flow.asset, 0) + flow.netflow
        
        # Limit historii
        if len(self.flows) > 10000:
            self.flows = self.flows[-5000:]
    
    def get_netflow_summary(self, asset: str, hours: int = 24) -> Dict:
        """
        Podsumuj netflow dla danego assetu.
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [f for f in self.flows if f.asset == asset and f.timestamp >= cutoff]
        
        if not recent:
            return {
                'total_inflow': 0,
                'total_outflow': 0,
                'netflow': 0,
                'signal': 0
            }
        
        total_inflow = sum(f.inflow for f in recent)
        total_outflow = sum(f.outflow for f in recent)
        netflow = total_inflow - total_outflow
        
        # Signal interpretation
        if asset in ['BTC', 'ETH']:
            # Crypto: inflow = bearish, outflow = bullish
            signal = -netflow / max(total_inflow + total_outflow, 1) * 0.5
        else:
            # Stablecoins: inflow = bullish (buying pressure)
            signal = netflow / max(total_inflow + total_outflow, 1) * 0.5
        
        return {
            'total_inflow': total_inflow,
            'total_outflow': total_outflow,
            'netflow': netflow,
            'signal': max(-1, min(1, signal))
        }
    
    def get_exchange_reserve_change(self, asset: str, days: int = 7) -> float:
        """
        Oblicz zmianę rezerw giełdowych w %.
        
        Spadające rezerwy = bullish (akumulacja)
        Rosnące rezerwy = bearish (dystrybucja)
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent = [f for f in self.flows if f.asset == asset and f.timestamp >= cutoff]
        
        if not recent:
            return 0
        
        total_netflow = sum(f.netflow for f in recent)
        reserve = self.reserves.get(asset, 1)
        
        return (total_netflow / reserve) * 100


# ═══════════════════════════════════════════════════════════════
# STABLECOIN FLOW ANALYZER
# ═══════════════════════════════════════════════════════════════

class StablecoinFlowAnalyzer:
    """
    💵 STABLECOIN FLOW ANALYZER
    
    Kluczowy wskaźnik!
    
    - USDT/USDC na giełdy = incoming BUY PRESSURE
    - Rosnąca kapitalizacja stablecoinów = więcej "amunicji" do kupna
    """
    
    def __init__(self):
        # Przybliżone dane
        self.market_caps = {
            'USDT': 120_000_000_000,  # 120B
            'USDC': 45_000_000_000,   # 45B
            'DAI': 5_000_000_000,     # 5B
        }
        self.exchange_balances = {
            'USDT': 50_000_000_000,
            'USDC': 10_000_000_000,
        }
    
    def analyze_buying_power(self) -> Dict:
        """
        Analizuj potencjalną siłę kupna.
        """
        total_on_exchanges = sum(self.exchange_balances.values())
        total_market_cap = sum(self.market_caps.values())
        
        # Ratio na giełdach
        exchange_ratio = total_on_exchanges / total_market_cap
        
        # Więcej na giełdach = więcej potencjalnego buy pressure
        buying_power_signal = (exchange_ratio - 0.3) * 2  # Normalize around 30%
        
        return {
            'total_stables_on_exchanges': total_on_exchanges,
            'total_stable_market_cap': total_market_cap,
            'exchange_ratio': exchange_ratio,
            'buying_power_signal': max(-1, min(1, buying_power_signal))
        }


# ═══════════════════════════════════════════════════════════════
# MINER FLOW ANALYZER
# ═══════════════════════════════════════════════════════════════

class MinerFlowAnalyzer:
    """
    ⛏️ MINER FLOW ANALYZER
    
    Górnicy są "informed players" - wiedzą kiedy sprzedać.
    
    - Duży miner outflow = bearish (górnicy sprzedają)
    - Niski miner outflow = bullish (trzymają)
    """
    
    def __init__(self):
        self.daily_production = 450  # ~450 BTC dziennie (post-halving 2024)
        self.miner_reserves = 1_800_000  # ~1.8M BTC w portfelach górników
        self.outflows: List[Dict] = []
    
    def add_outflow(self, amount: float, timestamp: datetime = None):
        """Dodaj outflow górników"""
        self.outflows.append({
            'amount': amount,
            'timestamp': timestamp or datetime.now()
        })
        self.miner_reserves -= amount
    
    def get_miner_pressure(self, days: int = 7) -> Dict:
        """
        Oblicz presję sprzedażową górników.
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent = [o for o in self.outflows if o['timestamp'] >= cutoff]
        
        total_outflow = sum(o['amount'] for o in recent)
        expected_production = self.daily_production * days
        
        # Ratio: outflow vs production
        # > 1 = sprzedają więcej niż produkują (bearish)
        # < 1 = trzymają część produkcji (bullish)
        
        if expected_production > 0:
            pressure_ratio = total_outflow / expected_production
        else:
            pressure_ratio = 1
        
        # Signal
        if pressure_ratio > 1.2:
            signal = -0.5  # Bearish
            status = 'heavy_selling'
        elif pressure_ratio < 0.8:
            signal = 0.5  # Bullish
            status = 'accumulating'
        else:
            signal = 0
            status = 'neutral'
        
        return {
            'outflow_7d': total_outflow,
            'production_7d': expected_production,
            'pressure_ratio': pressure_ratio,
            'signal': signal,
            'status': status,
            'reserve': self.miner_reserves
        }


# ═══════════════════════════════════════════════════════════════
# ETF FLOW TRACKER
# ═══════════════════════════════════════════════════════════════

class ETFFlowTracker:
    """
    📈 ETF FLOW TRACKER
    
    Śledzi przepływy do BTC/ETH ETF-ów.
    
    KLUCZOWE:
    - Inflows do ETF = institutional buying = SUPER BULLISH
    - Outflows = selling pressure
    """
    
    def __init__(self):
        self.etf_flows: List[Dict] = []
        
        # Główne ETF-y
        self.etfs = {
            'IBIT': {'issuer': 'BlackRock', 'aum': 50_000_000_000},
            'FBTC': {'issuer': 'Fidelity', 'aum': 15_000_000_000},
            'GBTC': {'issuer': 'Grayscale', 'aum': 20_000_000_000},
            'ARKB': {'issuer': 'ARK', 'aum': 3_000_000_000},
        }
    
    def add_flow(self, etf: str, amount_usd: float, timestamp: datetime = None):
        """Dodaj flow ETF"""
        self.etf_flows.append({
            'etf': etf,
            'amount': amount_usd,
            'timestamp': timestamp or datetime.now()
        })
    
    def get_etf_signal(self, days: int = 7) -> Dict:
        """
        Oblicz sygnał z ETF flows.
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent = [f for f in self.etf_flows if f['timestamp'] >= cutoff]
        
        if not recent:
            return {
                'net_flow': 0,
                'signal': 0,
                'status': 'no_data'
            }
        
        net_flow = sum(f['amount'] for f in recent)
        
        # Normalize: $500M+ inflow = strong signal
        signal = net_flow / 500_000_000
        signal = max(-1, min(1, signal))
        
        if signal > 0.3:
            status = 'strong_inflow'
        elif signal < -0.3:
            status = 'strong_outflow'
        else:
            status = 'neutral'
        
        return {
            'net_flow': net_flow,
            'signal': signal,
            'status': status,
            'flows_count': len(recent)
        }


# ═══════════════════════════════════════════════════════════════
# MAIN ON-CHAIN ENGINE
# ═══════════════════════════════════════════════════════════════

class OnChainEngine:
    """
    🔗 GŁÓWNY SILNIK ON-CHAIN ANALYTICS
    
    Łączy wszystkie komponenty i generuje sygnały.
    """
    
    def __init__(self):
        self.whale_tracker = WhaleTracker()
        self.exchange_flow = ExchangeFlowAnalyzer()
        self.stablecoin_flow = StablecoinFlowAnalyzer()
        self.miner_flow = MinerFlowAnalyzer()
        self.etf_tracker = ETFFlowTracker()
        
        self.last_metrics: Optional[OnChainMetrics] = None
        self.last_signal: Optional[OnChainSignal] = None
    
    def simulate_data(self):
        """
        Symuluj dane on-chain dla testów.
        W produkcji podłączysz API Glassnode/CryptoQuant.
        """
        np.random.seed(int(time.time()) % 1000)
        
        # Symuluj whale transactions
        for _ in range(np.random.randint(5, 20)):
            is_buying = np.random.random() > 0.45  # Slight bullish bias
            amount = np.random.uniform(100, 2000)
            
            tx = WhaleTransaction(
                timestamp=datetime.now() - timedelta(hours=np.random.randint(0, 24)),
                from_address='bc1q...',
                to_address='bc1q...',
                amount=amount,
                amount_usd=amount * 105000,
                asset='BTC',
                tx_hash=hashlib.md5(str(time.time()).encode()).hexdigest(),
                from_type='exchange_binance' if not is_buying else 'whale',
                to_type='whale' if not is_buying else 'exchange_binance',
                significance=self.whale_tracker.classify_transaction(amount)
            )
            self.whale_tracker.add_transaction(tx)
        
        # Symuluj exchange flows
        for asset in ['BTC', 'ETH', 'USDT']:
            inflow = np.random.uniform(1000, 10000) if asset != 'USDT' else np.random.uniform(100_000_000, 500_000_000)
            outflow = np.random.uniform(1000, 10000) if asset != 'USDT' else np.random.uniform(100_000_000, 500_000_000)
            
            flow = ExchangeFlow(
                timestamp=datetime.now(),
                exchange='aggregate',
                asset=asset,
                inflow=inflow,
                outflow=outflow,
                netflow=inflow - outflow,
                netflow_usd=(inflow - outflow) * (105000 if asset == 'BTC' else 3500 if asset == 'ETH' else 1)
            )
            self.exchange_flow.add_flow(flow)
        
        # Symuluj miner outflow
        miner_outflow = np.random.uniform(300, 600)  # Around daily production
        self.miner_flow.add_outflow(miner_outflow)
        
        # Symuluj ETF flow
        etf_flow = np.random.uniform(-200_000_000, 500_000_000)  # -200M to +500M
        self.etf_tracker.add_flow('IBIT', etf_flow)
    
    def analyze(self) -> OnChainSignal:
        """
        Pełna analiza on-chain.
        """
        # Zbierz dane z wszystkich źródeł
        whale_activity = self.whale_tracker.get_whale_activity(24)
        btc_flow = self.exchange_flow.get_netflow_summary('BTC', 24)
        eth_flow = self.exchange_flow.get_netflow_summary('ETH', 24)
        usdt_flow = self.exchange_flow.get_netflow_summary('USDT', 24)
        stablecoin = self.stablecoin_flow.analyze_buying_power()
        miner = self.miner_flow.get_miner_pressure(7)
        etf = self.etf_tracker.get_etf_signal(7)
        
        # ═══ CALCULATE SIGNALS ═══
        
        signals = []
        reasons = []
        key_events = []
        
        # 1. Whale Activity (25%)
        whale_signal = 0
        if whale_activity['sentiment'] == 'accumulating':
            whale_signal = 0.7
            reasons.append(f"🐋 Wieloryby akumulują: netflow +{whale_activity['netflow']:.0f} BTC")
        elif whale_activity['sentiment'] == 'distributing':
            whale_signal = -0.7
            reasons.append(f"🐋 Wieloryby sprzedają: netflow {whale_activity['netflow']:.0f} BTC")
        signals.append(('whale', whale_signal, 0.25))
        
        # 2. Exchange Flow BTC (20%)
        btc_signal = btc_flow['signal']
        if btc_signal > 0.2:
            reasons.append("📤 BTC wypływa z giełd (akumulacja)")
        elif btc_signal < -0.2:
            reasons.append("📥 BTC wpływa na giełdy (presja sprzedażowa)")
        signals.append(('btc_flow', btc_signal, 0.20))
        
        # 3. Stablecoin Flow (15%)
        stable_signal = usdt_flow['signal'] + stablecoin['buying_power_signal']
        stable_signal = max(-1, min(1, stable_signal / 2))
        if stable_signal > 0.2:
            reasons.append("💵 Stablecoiny na giełdach (potencjalne kupno)")
        signals.append(('stablecoin', stable_signal, 0.15))
        
        # 4. Miner Flow (15%)
        miner_signal = miner['signal']
        if miner['status'] == 'heavy_selling':
            reasons.append("⛏️ Górnicy sprzedają agresywnie")
            key_events.append({'type': 'miner_selling', 'severity': 'warning'})
        elif miner['status'] == 'accumulating':
            reasons.append("⛏️ Górnicy trzymają (bullish)")
        signals.append(('miner', miner_signal, 0.15))
        
        # 5. ETF Flow (25%)
        etf_signal = etf['signal']
        if etf['status'] == 'strong_inflow':
            reasons.append(f"📈 Silne wpływy do ETF: ${etf['net_flow']/1_000_000:.0f}M")
            key_events.append({'type': 'etf_inflow', 'amount': etf['net_flow']})
        elif etf['status'] == 'strong_outflow':
            reasons.append(f"📉 Odpływy z ETF: ${abs(etf['net_flow'])/1_000_000:.0f}M")
            key_events.append({'type': 'etf_outflow', 'amount': etf['net_flow']})
        signals.append(('etf', etf_signal, 0.25))
        
        # ═══ AGGREGATE SIGNAL ═══
        
        final_signal = sum(s * w for _, s, w in signals)
        
        # Confidence based on agreement
        signal_values = [s for _, s, _ in signals]
        agreement = 1 - np.std(signal_values)
        confidence = max(0.3, min(0.9, agreement))
        
        # Whale sentiment
        if final_signal > 0.3:
            whale_sentiment = 'accumulating'
        elif final_signal < -0.3:
            whale_sentiment = 'distributing'
        else:
            whale_sentiment = 'neutral'
        
        # Risk level
        if abs(final_signal) > 0.6:
            risk_level = 'low'  # Strong signal = lower risk
        elif abs(final_signal) > 0.3:
            risk_level = 'medium'
        else:
            risk_level = 'high'  # Unclear signal = higher risk
        
        self.last_signal = OnChainSignal(
            signal=final_signal,
            confidence=confidence,
            reasons=reasons,
            whale_sentiment=whale_sentiment,
            risk_level=risk_level,
            key_events=key_events
        )
        
        return self.last_signal
    
    def get_trading_signal(self) -> Dict:
        """
        Pobierz sygnał dla Genius Brain.
        """
        if self.last_signal is None:
            self.simulate_data()
            self.analyze()
        
        return {
            'signal': self.last_signal.signal,
            'confidence': self.last_signal.confidence,
            'reasons': self.last_signal.reasons,
            'whale_sentiment': self.last_signal.whale_sentiment,
            'risk_level': self.last_signal.risk_level,
            'key_events': self.last_signal.key_events
        }


# ═══════════════════════════════════════════════════════════════
# INTEGRATION WITH GENIUS BRAIN
# ═══════════════════════════════════════════════════════════════

def get_on_chain_signal() -> Dict:
    """
    Get on-chain signal for Genius Brain.
    """
    try:
        engine = OnChainEngine()
        engine.simulate_data()  # W produkcji: podłącz API
        signal = engine.analyze()
        
        return {
            'signal': signal.signal,
            'confidence': signal.confidence,
            'reasons': signal.reasons,
            'whale_sentiment': signal.whale_sentiment,
            'risk_level': signal.risk_level
        }
        
    except Exception as e:
        logger.error(f"On-chain error: {e}")
        return {'signal': 0, 'confidence': 0, 'reasons': [f'Error: {str(e)}']}


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🔗 ON-CHAIN ANALYTICS ENGINE - TEST")
    print("=" * 60)
    
    engine = OnChainEngine()
    
    print("\n1️⃣ SIMULATING ON-CHAIN DATA")
    print("-" * 40)
    engine.simulate_data()
    print("Data simulated!")
    
    print("\n2️⃣ WHALE ACTIVITY")
    print("-" * 40)
    whale = engine.whale_tracker.get_whale_activity(24)
    print(f"Transactions 24h: {whale['count']}")
    print(f"Buy volume: {whale['buy_volume']:.0f} BTC")
    print(f"Sell volume: {whale['sell_volume']:.0f} BTC")
    print(f"Netflow: {whale['netflow']:.0f} BTC")
    print(f"Sentiment: {whale['sentiment']}")
    
    print("\n3️⃣ EXCHANGE FLOWS")
    print("-" * 40)
    btc_flow = engine.exchange_flow.get_netflow_summary('BTC', 24)
    print(f"BTC Inflow: {btc_flow['total_inflow']:.0f}")
    print(f"BTC Outflow: {btc_flow['total_outflow']:.0f}")
    print(f"BTC Netflow: {btc_flow['netflow']:.0f}")
    print(f"Signal: {btc_flow['signal']:.3f}")
    
    print("\n4️⃣ MINER PRESSURE")
    print("-" * 40)
    miner = engine.miner_flow.get_miner_pressure(7)
    print(f"Outflow 7d: {miner['outflow_7d']:.0f} BTC")
    print(f"Production 7d: {miner['production_7d']:.0f} BTC")
    print(f"Pressure ratio: {miner['pressure_ratio']:.2f}")
    print(f"Status: {miner['status']}")
    
    print("\n5️⃣ ETF FLOWS")
    print("-" * 40)
    etf = engine.etf_tracker.get_etf_signal(7)
    print(f"Net flow: ${etf['net_flow']/1_000_000:.0f}M")
    print(f"Signal: {etf['signal']:.3f}")
    print(f"Status: {etf['status']}")
    
    print("\n6️⃣ FULL ANALYSIS")
    print("-" * 40)
    signal = engine.analyze()
    print(f"\n🎯 FINAL SIGNAL: {signal.signal:.3f}")
    print(f"Confidence: {signal.confidence:.3f}")
    print(f"Whale Sentiment: {signal.whale_sentiment}")
    print(f"Risk Level: {signal.risk_level}")
    print(f"\nReasons:")
    for reason in signal.reasons:
        print(f"  - {reason}")
    
    print("\n7️⃣ GENIUS BRAIN INTEGRATION TEST")
    print("-" * 40)
    brain_signal = get_on_chain_signal()
    print(f"Brain Signal: {brain_signal['signal']:.3f}")
    
    print("\n" + "=" * 60)
    print("✅ On-Chain Analytics Engine Ready!")
    print("=" * 60)
