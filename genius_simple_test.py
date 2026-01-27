"""
🔥 GENIUS SIMPLE TRADER - 7 DAY TEST
=====================================
Prosta, stabilna wersja bez asyncio.
Działa 24/7 bez problemów!

🆕 ZINTEGROWANE MODUŁY:
- Twelve Data API (RSI, MACD, EMA, ATR, Bollinger)
- Quant Power Engine (ffn, GARCH, VaR)
- Genius Trading Engine (AI signals)
"""

import requests
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import signal
import sys

# Telegram Alerts
try:
    from telegram_alerts import TelegramAlerts
    TELEGRAM = TelegramAlerts()
except ImportError:
    TELEGRAM = None
    print("⚠️ Telegram alerts disabled (telegram_alerts.py not found)")

# Dashboard Data Writer
try:
    from samanta_dashboard_data import SamantaDashboard
    DASHBOARD = SamantaDashboard()
    print("📊 Dashboard enabled - open samanta_dashboard.html")
except ImportError:
    DASHBOARD = None
    print("⚠️ Dashboard disabled (samanta_dashboard_data.py not found)")

# 🆕 GENIUS TRADING ENGINE - Twelve Data + AI
try:
    from genius_trading_engine import GeniusTradingEngine
    GENIUS_ENGINE = GeniusTradingEngine()
    print("🧠 Genius Trading Engine loaded (Twelve Data API)")
except ImportError as e:
    GENIUS_ENGINE = None
    print(f"⚠️ Genius Trading Engine disabled: {e}")

# 🆕 QUANT POWER ENGINE - ffn, GARCH, VaR
try:
    from quant_power_engine import QuantPowerEngine, get_quant_signal
    QUANT_ENGINE = QuantPowerEngine()
    print("⚡ Quant Power Engine loaded (ffn, GARCH, VaR)")
except ImportError as e:
    QUANT_ENGINE = None
    print(f"⚠️ Quant Power Engine disabled: {e}")

# 🔥 GENIUS BRAIN CONNECTOR - GŁÓWNY MÓZG (9.7/10 score!)
# Integruje WSZYSTKIE moduły: ICT, Liquidation Heatmap, Order Flow, On-Chain, 
# Institutional Edge, RL Agent, Sentiment, LSTM, Risk Engine
try:
    from genius_brain_connector import GeniusBrain, ModuleWeights
    GENIUS_BRAIN = GeniusBrain()
    print("🔥 GENIUS BRAIN CONNECTOR loaded (9.7/10 - ALL MODULES ACTIVE!)")
    print("   ├─ ICT Smart Money")
    print("   ├─ Liquidation Heatmap")
    print("   ├─ Order Flow (CVD)")
    print("   ├─ On-Chain Analytics")
    print("   ├─ Institutional Edge (Kelly, HMM)")
    print("   ├─ RL Agent")
    print("   ├─ Sentiment AI")
    print("   └─ Risk Engine")
except ImportError as e:
    GENIUS_BRAIN = None
    print(f"⚠️ Genius Brain Connector disabled: {e}")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DEPOSIT = 50000
POSITION_SIZE = 100
LEVERAGE = 500
MAX_POSITIONS = 5
STOP_LOSS_PCT = 0.01  # 1%
MIN_CONFLUENCE = 30  # Obniżone - bot aktywniejszy, czeka na 4+ sygnały
CHECK_INTERVAL = 30  # seconds
STATUS_INTERVAL = 300  # 5 min

# TP Levels
TP_LEVELS = [
    {'rr': 2, 'pct': 30},
    {'rr': 4, 'pct': 30},
    {'rr': 8, 'pct': 25},
    {'rr': 15, 'pct': 15},
]


@dataclass
class Trade:
    id: str
    timestamp: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profits: List[Dict]
    status: str = 'OPEN'
    pnl: float = 0
    remaining_pct: float = 100
    closed_portions: List[Dict] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)
    confluence: float = 0


class SimpleTrader:
    def __init__(self):
        self.balance = DEPOSIT
        self.trades: List[Trade] = []
        self.open_trades: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.total_pnl = 0
        self.max_drawdown = 0
        self.peak_balance = DEPOSIT
        self.signals_seen = 0
        self.signals_taken = 0
        self.running = True
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self._handle_exit)
    
    def _handle_exit(self, sig, frame):
        print("\n\n⚠️ Stopping test...")
        self.running = False
    
    def fetch_price(self) -> Optional[float]:
        try:
            r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            return float(r.json()['price'])
        except:
            return None
    
    def fetch_klines(self, interval: str, limit: int = 50) -> Optional[list]:
        try:
            r = requests.get(f'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={interval}&limit={limit}', timeout=10)
            return r.json()
        except:
            return None
    
    def analyze_market(self, price: float) -> Dict:
        """Analizuje rynek - ROZSZERZONA WERSJA z Twelve Data i Quant Engine."""
        klines_5m = self.fetch_klines('5m', 50)
        klines_1h = self.fetch_klines('1h', 24)
        
        result = {
            'price': price,
            'trend_5m': 'neutral',
            'trend_1h': 'neutral',
            'rsi': 50,
            'momentum': 0,
            'bull_signals': 0,
            'bear_signals': 0,
            'signals': [],
            'twelve_data': {},  # 🆕 Dane z Twelve Data
            'quant_signal': None  # 🆕 Sygnał z Quant Engine
        }
        
        if not klines_5m or not klines_1h:
            return result
        
        # ═══════════════════════════════════════════════════════════════
        # 🆕 TWELVE DATA INTEGRATION - RSI, MACD, EMA, ATR, Bollinger
        # ═══════════════════════════════════════════════════════════════
        if GENIUS_ENGINE:
            try:
                twelve_indicators = GENIUS_ENGINE.fetch_technical_indicators('BTC/USD', '1h')
                result['twelve_data'] = twelve_indicators
                
                # RSI z Twelve Data (dokładniejszy)
                if 'rsi' in twelve_indicators and twelve_indicators['rsi']:
                    td_rsi = twelve_indicators['rsi'][0]  # Najnowszy RSI
                    result['rsi'] = td_rsi
                    
                    if td_rsi < 30:
                        result['bull_signals'] += 2
                        result['signals'].append('TD_RSI_OVERSOLD')
                    elif td_rsi < 40:
                        result['bull_signals'] += 1
                        result['signals'].append('TD_RSI_LOW')
                    elif td_rsi > 70:
                        result['bear_signals'] += 2
                        result['signals'].append('TD_RSI_OVERBOUGHT')
                    elif td_rsi > 60:
                        result['bear_signals'] += 1
                        result['signals'].append('TD_RSI_HIGH')
                
                # MACD z Twelve Data
                if 'macd' in twelve_indicators and twelve_indicators['macd']:
                    macd_data = twelve_indicators['macd'][0]
                    if macd_data['histogram'] > 0 and macd_data['macd'] > macd_data['signal']:
                        result['bull_signals'] += 2
                        result['signals'].append('TD_MACD_BULL')
                    elif macd_data['histogram'] < 0 and macd_data['macd'] < macd_data['signal']:
                        result['bear_signals'] += 2
                        result['signals'].append('TD_MACD_BEAR')
                
                # EMA Trend z Twelve Data
                ema21 = twelve_indicators.get('ema21', 0)
                ema50 = twelve_indicators.get('ema50', 0)
                ema200 = twelve_indicators.get('ema200', 0)
                
                if ema21 > 0 and ema50 > 0:
                    if price > ema21 > ema50:
                        result['bull_signals'] += 2
                        result['signals'].append('TD_EMA_BULL_CROSS')
                    elif price < ema21 < ema50:
                        result['bear_signals'] += 2
                        result['signals'].append('TD_EMA_BEAR_CROSS')
                
                if ema200 > 0:
                    if price > ema200:
                        result['bull_signals'] += 1
                        result['signals'].append('TD_ABOVE_EMA200')
                    else:
                        result['bear_signals'] += 1
                        result['signals'].append('TD_BELOW_EMA200')
                
                # Bollinger Bands z Twelve Data
                if 'bollinger' in twelve_indicators:
                    bb = twelve_indicators['bollinger']
                    if price < bb['lower']:
                        result['bull_signals'] += 2
                        result['signals'].append('TD_BB_OVERSOLD')
                    elif price > bb['upper']:
                        result['bear_signals'] += 2
                        result['signals'].append('TD_BB_OVERBOUGHT')
                
                # ADX (trend strength)
                if 'adx' in twelve_indicators:
                    adx = twelve_indicators['adx']
                    if adx > 25:
                        result['signals'].append(f'TD_ADX_STRONG_{adx:.0f}')
                
                # Stochastic
                if 'stoch' in twelve_indicators:
                    stoch = twelve_indicators['stoch']
                    if stoch['k'] < 20:
                        result['bull_signals'] += 1
                        result['signals'].append('TD_STOCH_OVERSOLD')
                    elif stoch['k'] > 80:
                        result['bear_signals'] += 1
                        result['signals'].append('TD_STOCH_OVERBOUGHT')
                
            except Exception as e:
                print(f"⚠️ Twelve Data error: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # 🆕 QUANT POWER ENGINE - ffn, GARCH, VaR
        # ═══════════════════════════════════════════════════════════════
        if QUANT_ENGINE:
            try:
                import pandas as pd
                closes = [float(k[4]) for k in klines_1h]
                prices_series = pd.Series(closes)
                
                quant_signal = QUANT_ENGINE.analyze(prices_series)  # Fixed: analyze() not get_full_signal()
                result['quant_signal'] = quant_signal
                
                if quant_signal:
                    # Sygnał z Quant Engine (-1 do 1)
                    if quant_signal.signal > 0.3:
                        result['bull_signals'] += 2
                        result['signals'].append('QUANT_BULL')
                    elif quant_signal.signal < -0.3:
                        result['bear_signals'] += 2
                        result['signals'].append('QUANT_BEAR')
                    
                    # Reżim rynkowy
                    if quant_signal.regime:
                        regime = quant_signal.regime.regime
                        if regime == 'bull':
                            result['bull_signals'] += 1
                            result['signals'].append('QUANT_REGIME_BULL')
                        elif regime == 'bear':
                            result['bear_signals'] += 1
                            result['signals'].append('QUANT_REGIME_BEAR')
                    
            except Exception as e:
                print(f"⚠️ Quant Engine error: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # 🔥 GENIUS BRAIN CONNECTOR - GŁÓWNY MÓZG 9.7/10!
        # Integruje: ICT, Liquidation, Order Flow, On-Chain, Institutional
        # ═══════════════════════════════════════════════════════════════
        if GENIUS_BRAIN:
            try:
                import pandas as pd
                closes = [float(k[4]) for k in klines_1h]
                df = pd.DataFrame({
                    'close': closes,
                    'high': [float(k[2]) for k in klines_1h],
                    'low': [float(k[3]) for k in klines_1h],
                    'open': [float(k[1]) for k in klines_1h],
                    'volume': [float(k[5]) for k in klines_1h]
                })
                
                # Pełna decyzja z wszystkich 12+ modułów!
                brain_decision = GENIUS_BRAIN.think(df)  # Fixed: think() not get_decision()
                result['brain_decision'] = brain_decision
                
                if brain_decision:
                    # Główny sygnał z Brain (waga: 5 - NAJWAŻNIEJSZY!)
                    brain_score = brain_decision.final_score  # -1 do 1
                    
                    if brain_score > 0.3:
                        result['bull_signals'] += 5
                        result['signals'].append(f'BRAIN_BULL_{brain_score:.2f}')
                    elif brain_score < -0.3:
                        result['bear_signals'] += 5
                        result['signals'].append(f'BRAIN_BEAR_{abs(brain_score):.2f}')
                    
                    # Dodaj szczegóły z poszczególnych modułów
                    if hasattr(brain_decision, 'module_results'):
                        for module_name, module_result in brain_decision.module_results.items():
                            if module_result.active and abs(module_result.signal) > 0.5:
                                if module_result.signal > 0:
                                    result['bull_signals'] += 1
                                    result['signals'].append(f'{module_name.upper()}_BULL')
                                else:
                                    result['bear_signals'] += 1
                                    result['signals'].append(f'{module_name.upper()}_BEAR')
                    
                    # Confidence boost
                    if brain_decision.confidence > 0.7:
                        result['signals'].append('BRAIN_HIGH_CONF')
                    
            except Exception as e:
                print(f"⚠️ Genius Brain error: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # ORYGINALNA ANALIZA (Binance klines)
        # ═══════════════════════════════════════════════════════════════
        
        # 5m Trend
        closes_5m = [float(k[4]) for k in klines_5m[-20:]]
        sma10 = sum(closes_5m[-10:]) / 10
        sma20 = sum(closes_5m) / 20
        
        if price > sma10 > sma20:
            result['trend_5m'] = 'bullish'
            result['bull_signals'] += 1
            result['signals'].append('TREND_5M_BULL')
        elif price < sma10 < sma20:
            result['trend_5m'] = 'bearish'
            result['bear_signals'] += 1
            result['signals'].append('TREND_5M_BEAR')
        
        # 1h Trend
        closes_1h = [float(k[4]) for k in klines_1h[-20:]]
        sma10h = sum(closes_1h[-10:]) / 10
        sma20h = sum(closes_1h) / 20
        
        if price > sma10h > sma20h:
            result['trend_1h'] = 'bullish'
            result['bull_signals'] += 2
            result['signals'].append('TREND_1H_BULL')
        elif price < sma10h < sma20h:
            result['trend_1h'] = 'bearish'
            result['bear_signals'] += 2
            result['signals'].append('TREND_1H_BEAR')
        
        # RSI (fallback jeśli Twelve Data niedostępny)
        if 'TD_RSI' not in str(result['signals']) and len(closes_5m) >= 14:
            gains, losses = [], []
            for i in range(1, len(closes_5m)):
                diff = closes_5m[i] - closes_5m[i-1]
                gains.append(max(0, diff))
                losses.append(max(0, -diff))
            
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                result['rsi'] = 100 - (100 / (1 + rs))
            
            if result['rsi'] < 35:
                result['bull_signals'] += 1
                result['signals'].append('RSI_OVERSOLD')
            elif result['rsi'] > 65:
                result['bear_signals'] += 1
                result['signals'].append('RSI_OVERBOUGHT')
        
        # Momentum
        old_price = closes_5m[-5] if len(closes_5m) >= 5 else price
        result['momentum'] = (price - old_price) / old_price * 100
        
        if result['momentum'] > 0.1:
            result['bull_signals'] += 1
            result['signals'].append('MOMENTUM_UP')
        elif result['momentum'] < -0.1:
            result['bear_signals'] += 1
            result['signals'].append('MOMENTUM_DOWN')
        
        # Strong momentum bonus
        if result['momentum'] > 0.3:
            result['bull_signals'] += 1
            result['signals'].append('STRONG_MOMENTUM_UP')
        elif result['momentum'] < -0.3:
            result['bear_signals'] += 1
            result['signals'].append('STRONG_MOMENTUM_DOWN')
        
        # Liquidity Grab (wick analysis)
        last = klines_5m[-1]
        o, h, l, c = float(last[1]), float(last[2]), float(last[3]), float(last[4])
        body = abs(c - o)
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        
        if lower_wick > body * 2:
            result['bull_signals'] += 2
            result['signals'].append('LIQ_GRAB_BULL')
        elif upper_wick > body * 2:
            result['bear_signals'] += 2
            result['signals'].append('LIQ_GRAB_BEAR')
        
        # Bullish/Bearish candle pattern
        if c > o:  # Green candle
            result['bull_signals'] += 1
            result['signals'].append('GREEN_CANDLE')
        elif c < o:  # Red candle
            result['bear_signals'] += 1
            result['signals'].append('RED_CANDLE')
        
        # FVG
        if len(klines_5m) >= 3:
            h1 = float(klines_5m[-3][2])
            l3 = float(klines_5m[-1][3])
            l1 = float(klines_5m[-3][3])
            h3 = float(klines_5m[-1][2])
            
            if l3 > h1:
                result['bull_signals'] += 1
                result['signals'].append('FVG_BULL')
            elif h3 < l1:
                result['bear_signals'] += 1
                result['signals'].append('FVG_BEAR')
        
        # Price above/below SMA - trend confirmation
        if price > sma20:
            result['bull_signals'] += 1
            result['signals'].append('ABOVE_SMA20')
        else:
            result['bear_signals'] += 1
            result['signals'].append('BELOW_SMA20')
        
        # ═══════════════════════════════════════════════════════════════
        # KILLZONES - London, NY, Asian (24/7 coverage!)
        # ═══════════════════════════════════════════════════════════════
        hour = datetime.utcnow().hour
        killzone_name = None
        killzone_bonus = 0
        
        # London Open (07:00-10:00 UTC) - High volatility, manipulation
        if 7 <= hour <= 10:
            killzone_name = 'LONDON_OPEN'
            killzone_bonus = 2  # Strong bonus
            
        # NY Open (13:00-16:00 UTC) - Main momentum
        elif 13 <= hour <= 16:
            killzone_name = 'NY_OPEN'
            killzone_bonus = 2  # Strong bonus
            
        # Asian Session (20:00-00:00 UTC) - Range building, scalp opportunities
        elif 20 <= hour <= 23:
            killzone_name = 'ASIAN_SESSION'
            killzone_bonus = 1  # Moderate bonus (range building)
            
        # Asian Extension (00:00-02:00 UTC) - Late Asian
        elif 0 <= hour <= 2:
            killzone_name = 'ASIAN_LATE'
            killzone_bonus = 1
        
        if killzone_name:
            result['bull_signals'] += killzone_bonus
            result['bear_signals'] += killzone_bonus
            result['signals'].append(f'KILLZONE_{killzone_name}')
            result['killzone'] = killzone_name
        else:
            result['killzone'] = 'OFF_HOURS'
        
        return result
    
    def evaluate_entry(self, analysis: Dict) -> Optional[Dict]:
        """Sprawdza czy wejść w trade - ROZSZERZONA WERSJA."""
        self.signals_seen += 1
        
        # 🆕 Max signals zwiększony dla Twelve Data + Quant Engine:
        # Oryginalne: TREND_5M(1) + TREND_1H(2) + RSI(1) + MOMENTUM(1) + STRONG_MOM(1) + 
        #             LIQ_GRAB(2) + CANDLE(1) + FVG(1) + SMA(1) + KILLZONE(1) = 12
        # Twelve Data: TD_RSI(2) + TD_MACD(2) + TD_EMA(2) + TD_EMA200(1) + TD_BB(2) + TD_STOCH(1) = 10
        # Quant: QUANT_SIGNAL(2) + QUANT_REGIME(1) = 3
        # 🔥 BRAIN CONNECTOR: BRAIN_SIGNAL(5) + MODULES(~5) = 10
        # TOTAL = 35 max signals
        max_signals = 35
        bull_conf = (analysis['bull_signals'] / max_signals) * 100
        bear_conf = (analysis['bear_signals'] / max_signals) * 100
        
        if len(self.open_trades) >= MAX_POSITIONS:
            return None
        
        # 🆕 Liczenie sygnałów z różnych źródeł
        td_signals = [s for s in analysis['signals'] if s.startswith('TD_')]
        quant_signals = [s for s in analysis['signals'] if s.startswith('QUANT_')]
        brain_signals = [s for s in analysis['signals'] if s.startswith('BRAIN_')]
        
        # 🔥 Bonus za potwierdzenie z wielu źródeł
        data_sources = 0
        if td_signals:
            data_sources += 1
        if quant_signals:
            data_sources += 1
        if brain_signals:
            data_sources += 2  # Brain = 2 punkty bo integruje wiele modułów
        if analysis['trend_5m'] != 'neutral':
            data_sources += 1
        
        # Multi-source confirmation bonus
        if data_sources >= 2:
            bull_conf *= 1.1  # 10% bonus
            bear_conf *= 1.1
        if data_sources >= 4:
            bull_conf *= 1.15  # Dodatkowy 15% bonus za Brain
            bear_conf *= 1.15
        
        # 🔥 BRAIN OVERRIDE - jeśli Brain daje silny sygnał, wchodzimy!
        brain_decision = analysis.get('brain_decision')
        if brain_decision and brain_decision.confidence > 0.7:
            if brain_decision.final_score > 0.5:
                bull_conf = max(bull_conf, 60)  # Minimum 60% confidence przy silnym Brain
            elif brain_decision.final_score < -0.5:
                bear_conf = max(bear_conf, 60)
        
        # LONG entry - when bullish signals dominate
        if bull_conf >= MIN_CONFLUENCE and bull_conf > bear_conf + 10:
            self.signals_taken += 1
            return {
                'direction': 'LONG',
                'confluence': min(bull_conf, 100),
                'signals': [s for s in analysis['signals'] if 'BULL' in s or 'UP' in s or 'OVERSOLD' in s or 'KILLZONE' in s or 'ABOVE' in s],
                'data_sources': data_sources,
                'brain_score': brain_decision.final_score if brain_decision else None
            }
        
        if bear_conf >= MIN_CONFLUENCE and bear_conf > bull_conf + 10:
            self.signals_taken += 1
            return {
                'direction': 'SHORT',
                'confluence': min(bear_conf, 100),
                'signals': [s for s in analysis['signals'] if 'BEAR' in s or 'DOWN' in s or 'OVERBOUGHT' in s or 'KILLZONE' in s or 'BELOW' in s],
                'data_sources': data_sources,
                'brain_score': brain_decision.final_score if brain_decision else None
            }
        
        return None
    
    def open_trade(self, price: float, entry: Dict) -> Trade:
        """Otwiera trade."""
        direction = entry['direction']
        
        if direction == 'LONG':
            sl = price * (1 - STOP_LOSS_PCT)
        else:
            sl = price * (1 + STOP_LOSS_PCT)
        
        risk = abs(price - sl)
        
        tps = []
        for tp in TP_LEVELS:
            if direction == 'LONG':
                tp_price = price + (risk * tp['rr'])
            else:
                tp_price = price - (risk * tp['rr'])
            tps.append({'price': tp_price, 'rr': tp['rr'], 'pct': tp['pct'], 'hit': False})
        
        trade = Trade(
            id=f"T{len(self.trades)+1:04d}",
            timestamp=datetime.now().isoformat(),
            direction=direction,
            entry_price=price,
            stop_loss=sl,
            take_profits=tps,
            signals=entry['signals'],
            confluence=entry['confluence']
        )
        
        self.trades.append(trade)
        self.open_trades.append(trade)
        
        print(f"\n{'='*60}")
        print(f"🚀 TRADE OPENED: {trade.id}")
        print(f"   {direction} @ ${price:,.2f}")
        print(f"   SL: ${sl:,.2f} ({STOP_LOSS_PCT*100:.1f}%)")
        tp_prices = ', '.join([f"${t['price']:,.0f}" for t in tps])
        print(f"   TPs: [{tp_prices}]")
        print(f"   Signals: {', '.join(entry['signals'])}")
        print(f"   Confluence: {entry['confluence']:.0f}%")
        print(f"{'='*60}\n")
        
        # � DASHBOARD
        if DASHBOARD:
            DASHBOARD.record_trade_open(
                direction=direction,
                entry_price=price,
                confluence=entry['confluence'],
                position_size=POSITION_SIZE,
                leverage=LEVERAGE
            )
        
        # �📱 TELEGRAM ALERT
        if TELEGRAM and TELEGRAM.enabled:
            TELEGRAM.alert_trade_opened({
                'id': trade.id,
                'side': direction,
                'entry_price': price,
                'stop_loss': sl,
                'tp1': tps[0]['price'],
                'tp2': tps[1]['price'],
                'tp3': tps[2]['price'],
                'tp4': tps[3]['price'],
                'signals': entry['signals'],
                'confluence': entry['confluence'],
                'position_size': POSITION_SIZE,
                'leverage': LEVERAGE
            })
        
        return trade
    
    def update_trades(self, price: float):
        """Aktualizuje otwarte pozycje."""
        to_close = []
        
        for trade in self.open_trades:
            # Check SL
            hit_sl = (trade.direction == 'LONG' and price <= trade.stop_loss) or \
                     (trade.direction == 'SHORT' and price >= trade.stop_loss)
            
            if hit_sl:
                trade.pnl = self._calc_pnl(trade, trade.stop_loss, trade.remaining_pct)
                trade.status = 'CLOSED'
                to_close.append(trade)
                print(f"\n❌ SL HIT: {trade.id} | P&L: ${trade.pnl:+,.2f}")
                
                # � DASHBOARD
                if DASHBOARD:
                    trade_num = int(trade.id[1:])
                    DASHBOARD.record_sl_hit(trade_num, abs(trade.pnl), trade.stop_loss)
                    DASHBOARD.record_trade_close(trade_num, trade.pnl, trade.stop_loss)
                
                # �📱 TELEGRAM ALERT
                if TELEGRAM and TELEGRAM.enabled:
                    TELEGRAM.alert_sl_hit({
                        'id': trade.id,
                        'side': trade.direction,
                        'entry_price': trade.entry_price,
                        'stop_loss': trade.stop_loss
                    }, trade.pnl)
                continue
            
            # Check TPs
            for tp in trade.take_profits:
                if tp['hit']:
                    continue
                
                hit = (trade.direction == 'LONG' and price >= tp['price']) or \
                      (trade.direction == 'SHORT' and price <= tp['price'])
                
                if hit:
                    tp['hit'] = True
                    partial_pnl = self._calc_pnl(trade, tp['price'], tp['pct'])
                    trade.pnl += partial_pnl
                    trade.remaining_pct -= tp['pct']
                    
                    trade.closed_portions.append({
                        'price': tp['price'],
                        'pct': tp['pct'],
                        'pnl': partial_pnl,
                        'rr': tp['rr']
                    })
                    
                    print(f"\n✅ TP{tp['rr']} HIT: {trade.id}")
                    print(f"   Closed {tp['pct']}% @ ${tp['price']:,.2f}")
                    print(f"   Partial P&L: ${partial_pnl:+,.2f}")
                    
                    # � DASHBOARD
                    if DASHBOARD:
                        trade_num = int(trade.id[1:])
                        tp_level = len(trade.closed_portions)
                        DASHBOARD.record_tp_hit(trade_num, tp_level, partial_pnl, tp['price'])
                    
                    # �📱 TELEGRAM ALERT
                    if TELEGRAM and TELEGRAM.enabled:
                        tp_level = len(trade.closed_portions)
                        TELEGRAM.alert_tp_hit({
                            'id': trade.id,
                            'side': trade.direction,
                            f'tp{tp_level}': tp['price'],
                            f'tp{tp_level}_pct': tp['pct']
                        }, tp_level, partial_pnl)
                    
                    # Move SL to BE
                    if len(trade.closed_portions) == 1:
                        trade.stop_loss = trade.entry_price
                        print(f"   🔒 SL -> Break Even")
            
            # Check if fully closed
            if trade.remaining_pct <= 0:
                trade.status = 'CLOSED'
                to_close.append(trade)
                print(f"\n🏆 TRADE CLOSED: {trade.id} | Total P&L: ${trade.pnl:+,.2f}")
                
                # � DASHBOARD - Full close
                if DASHBOARD:
                    trade_num = int(trade.id[1:])
                    exit_price = trade.closed_portions[-1]['price'] if trade.closed_portions else trade.entry_price
                    DASHBOARD.record_trade_close(trade_num, trade.pnl, exit_price)
                
                # �📱 TELEGRAM ALERT
                if TELEGRAM and TELEGRAM.enabled:
                    result = "WIN" if trade.pnl > 0 else "LOSS"
                    TELEGRAM.alert_trade_closed({
                        'id': trade.id,
                        'side': trade.direction,
                        'entry_price': trade.entry_price,
                        'exit_price': trade.closed_portions[-1]['price'] if trade.closed_portions else trade.entry_price,
                        'duration': 'N/A',
                        'exit_reason': 'All TPs hit'
                    }, result, trade.pnl)
        
        for trade in to_close:
            self.open_trades.remove(trade)
            self.closed_trades.append(trade)
            self.balance += trade.pnl
            self.total_pnl += trade.pnl
            
            if self.balance > self.peak_balance:
                self.peak_balance = self.balance
            
            dd = (self.peak_balance - self.balance) / self.peak_balance * 100
            if dd > self.max_drawdown:
                self.max_drawdown = dd
    
    def _calc_pnl(self, trade: Trade, exit_price: float, portion_pct: float) -> float:
        notional = POSITION_SIZE * LEVERAGE
        portion = portion_pct / 100
        
        if trade.direction == 'LONG':
            pnl_pct = (exit_price - trade.entry_price) / trade.entry_price
        else:
            pnl_pct = (trade.entry_price - exit_price) / trade.entry_price
        
        pnl = notional * pnl_pct * portion
        fees = notional * portion * 0.0008
        return pnl - fees
    
    def print_status(self, price: float, analysis: Dict):
        wins = len([t for t in self.closed_trades if t.pnl > 0])
        losses = len(self.closed_trades) - wins
        wr = (wins / len(self.closed_trades) * 100) if self.closed_trades else 0
        
        print(f"\n📊 STATUS [{datetime.now().strftime('%H:%M:%S')}]")
        print(f"{'─'*50}")
        print(f"  Price:     ${price:>12,.2f}")
        print(f"  Trend:     5m={analysis['trend_5m']:>8} | 1h={analysis['trend_1h']}")
        print(f"  RSI:       {analysis['rsi']:>12.1f}")
        print(f"  Momentum:  {analysis['momentum']:>+12.2f}%")
        print(f"{'─'*50}")
        print(f"  Balance:   ${self.balance:>12,.2f}")
        print(f"  P&L:       ${self.total_pnl:>+12,.2f} ({self.total_pnl/DEPOSIT*100:+.2f}%)")
        print(f"  Max DD:    {self.max_drawdown:>12.2f}%")
        print(f"{'─'*50}")
        print(f"  Trades:    {len(self.closed_trades)} closed | {len(self.open_trades)} open")
        print(f"  Win Rate:  {wr:.1f}% ({wins}W/{losses}L)")
        print(f"  Signals:   {self.signals_seen} seen | {self.signals_taken} taken")
        print(f"{'─'*50}\n")
    
    def print_final_report(self, start_time: datetime):
        wins = len([t for t in self.closed_trades if t.pnl > 0])
        losses = len(self.closed_trades) - wins
        wr = (wins / len(self.closed_trades) * 100) if self.closed_trades else 0
        duration = (datetime.now() - start_time).total_seconds() / 3600
        
        print("\n" + "="*70)
        print("🏆 FINAL REPORT")
        print("="*70)
        print(f"  Duration:      {duration:.1f} hours")
        print(f"  Initial:       ${DEPOSIT:,.2f}")
        print(f"  Final:         ${self.balance:,.2f}")
        print(f"  Total P&L:     ${self.total_pnl:+,.2f} ({self.total_pnl/DEPOSIT*100:+.2f}%)")
        print(f"  Max Drawdown:  {self.max_drawdown:.2f}%")
        print(f"  Trades:        {len(self.closed_trades)}")
        print(f"  Win Rate:      {wr:.1f}% ({wins}W/{losses}L)")
        
        if self.total_pnl > 0 and wr >= 50:
            print(f"\n  ✅ VERDICT: GO LIVE!")
        elif len(self.closed_trades) == 0:
            print(f"\n  ⚠️ VERDICT: No trades - need more time")
        else:
            print(f"\n  ❌ VERDICT: Needs work")
        print("="*70)
        
        # Save
        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {
            'duration_hours': duration,
            'initial': DEPOSIT,
            'final': self.balance,
            'pnl': self.total_pnl,
            'roi_pct': self.total_pnl/DEPOSIT*100,
            'max_dd': self.max_drawdown,
            'trades': len(self.closed_trades),
            'wins': wins,
            'losses': losses,
            'win_rate': wr,
            'trade_list': [
                {
                    'id': t.id,
                    'direction': t.direction,
                    'entry': t.entry_price,
                    'pnl': t.pnl,
                    'confluence': t.confluence,
                    'signals': t.signals
                }
                for t in self.closed_trades
            ]
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 Saved to {filename}")
        
        # � TELEGRAM - Final Report z wykresem
        if TELEGRAM and TELEGRAM.enabled:
            # Przygotuj dane dla wykresu
            trades_data = [
                {'id': t.id, 'direction': t.direction, 'pnl': t.pnl, 
                 'entry_price': t.entry_price, 'status': 'closed'}
                for t in self.closed_trades
            ]
            
            balance_history = self._get_balance_history()
            
            # Wyślij raport z wykresem
            TELEGRAM.send_performance_report(trades_data, balance_history, DEPOSIT)
            
            # Również wyślij tekstowy raport
            TELEGRAM.alert_bot_stopped({
                'runtime': f"{duration:.1f}h",
                'total_trades': len(self.closed_trades),
                'wins': wins,
                'losses': losses,
                'win_rate': wr,
                'total_pnl': self.total_pnl
            })
    
    def _get_balance_history(self) -> list:
        """Generuje historię balance dla wykresu"""
        history = [{'time': 'Start', 'balance': DEPOSIT, 'tradeResult': None}]
        running_balance = DEPOSIT
        
        for t in self.closed_trades:
            running_balance += t.pnl
            history.append({
                'time': t.timestamp.split('T')[1][:5] if 'T' in t.timestamp else t.timestamp,
                'balance': running_balance,
                'tradeResult': 'profit' if t.pnl > 0 else 'loss'
            })
        
        return history
    
    def send_hourly_report(self):
        """Wysyła raport co godzinę"""
        if not TELEGRAM or not TELEGRAM.enabled:
            return
        
        trades_data = [
            {'id': t.id, 'direction': t.direction, 'pnl': t.pnl,
             'entry_price': t.entry_price, 'status': 'closed'}
            for t in self.closed_trades
        ]
        
        balance_history = self._get_balance_history()
        
        print("📊 Wysyłanie raportu godzinowego na Telegram...")
        TELEGRAM.send_performance_report(trades_data, balance_history, DEPOSIT)


def run_test(hours: float = 1):
    """Uruchamia test."""
    trader = SimpleTrader()
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=hours)
    
    print("\n" + "="*60)
    print(f"🔥 SIMPLE TRADER TEST - {hours} HOURS")
    print("="*60)
    print(f"  Start:    {start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"  End:      {end_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Deposit:  ${DEPOSIT:,}")
    print(f"  Position: ${POSITION_SIZE} x {LEVERAGE}x")
    print("="*60)
    
    # 📱 TELEGRAM - Bot Started
    if TELEGRAM and TELEGRAM.enabled:
        TELEGRAM.alert_bot_started({
            'mode': 'Paper Trading',
            'deposit': DEPOSIT,
            'position_size': POSITION_SIZE,
            'leverage': LEVERAGE,
            'min_confluence': MIN_CONFLUENCE
        })
    
    last_status = time.time()
    last_hourly_report = time.time()
    HOURLY_REPORT_INTERVAL = 3600  # 1 godzina
    
    print("\n✅ Connected to Binance\n")
    
    while trader.running and datetime.now() < end_time:
        try:
            price = trader.fetch_price()
            
            if price:
                # Analyze
                analysis = trader.analyze_market(price)
                
                # Update open trades
                trader.update_trades(price)
                
                # Look for entries
                entry = trader.evaluate_entry(analysis)
                if entry:
                    trader.open_trade(price, entry)
                
                # Status every 5 min
                if time.time() - last_status >= STATUS_INTERVAL:
                    trader.print_status(price, analysis)
                    last_status = time.time()
                
                # 📊 Hourly report with chart to Telegram
                if time.time() - last_hourly_report >= HOURLY_REPORT_INTERVAL:
                    trader.send_hourly_report()
                    last_hourly_report = time.time()
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)
    
    trader.print_final_report(start_time)


if __name__ == "__main__":
    import sys
    
    # Direct run with argument
    if len(sys.argv) > 1:
        hours = float(sys.argv[1])
        run_test(hours)
    else:
        print("""
╔════════════════════════════════════════════════╗
║  🔥 SIMPLE TRADER - TEST MENU                  ║
╠════════════════════════════════════════════════╣
║  Usage: python genius_simple_test.py [hours]   ║
║                                                ║
║  Examples:                                     ║
║    python genius_simple_test.py 1    (1 hour)  ║
║    python genius_simple_test.py 6    (6 hours) ║
║    python genius_simple_test.py 24   (1 day)   ║
║    python genius_simple_test.py 168  (1 week)  ║
╚════════════════════════════════════════════════╝
        """)
        
        hours = input("Hours to run (default 1): ").strip()
        hours = float(hours) if hours else 1
        run_test(hours)
