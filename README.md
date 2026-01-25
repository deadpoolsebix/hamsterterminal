# 🚀 Professional Trading Bot Dashboard

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-green.svg)

**Profesjonalny dashboard tradingowy w stylu Bloomberg Terminal z zaawansowaną analizą techniczną, machine learning i real-time danymi.**

---

## ✨ Kluczowe Funkcje

- 📊 **Real-time Market Data** - Dane z Yahoo Finance
- 🤖 **AI Trading Bot** - Machine learning predictions z TensorFlow
- **Funding Rate Calculator** - Obliczanie kosztów finansowania dla kryptowalut (NEW!)
- 📈 **Advanced Charts** - Plotly interactive charts w stylu Bloomberg
- 💹 **Technical Indicators** - RSI, MACD, Bollinger Bands, FVG, Order Blocks
- 🎯 **Risk Management** - Trailing stops, position sizing, leverage control
- 📱 **Responsive Design** - Działa na desktop i mobile
- 🌐 **Cloud Ready** - Docker, Railway, Render deployment
- 💎 **ICT Concepts** - Fair Value Gap, Smart Money analysis
- 🎮 **Game Boy AI Trainer** - Interactive trading advisor z wbudowanym kalkulator

---

## 📋 SPIS TREŚCI

1. [Quick Start](#-quick-start)
2. [Screenshots](#-screenshots)
3. [Deployment](#-deployment)
4. [Technologie](#-technologie)
5. [Trading Bot](#-trading-bot)
6. [Contributing](#-contributing)

---

## 🚀 Quick Start

### Lokalne uruchomienie

```bash
# Sklonuj repo
git clone https://github.com/TWOJ_USERNAME/trading-bot-pro.git
cd trading-bot-pro

# Utwórz virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Zainstaluj zależności
pip install -r requirements.txt

# Uruchom dashboard
python serve_dashboard.py
```

Dashboard dostępny na: **http://localhost:8080**

### Docker

```bash
# Build i uruchom
docker-compose up -d

# Sprawdź status
docker-compose ps
```

---

## 🖼️ Screenshots

![Dashboard Preview](dashboard_screenshots/preview.png)

---

## ✨ FUNKCJONALNOŚĆ

### 📊 Technical Analysis
- **Wskaźniki:** RSI, Momentum, MACD, Stochastic
- **Trend:** SMA, EMA, Bollinger Bands
- **Zmienność:** ATR (Average True Range)
- **Support/Resistance:** Automatyczna detekcja poziomów

### 💎 ICT/Smart Money Concepts
- **Fair Value Gap (FVG):** Wykrywanie luk wartości godziwej
- **Order Blocks:** Identyfikacja bloków zleceń instytucjonalnych
- **Liquidity Grab:** Detekcja sweep'ów EQH/EQL (Equal Highs/Lows)
- **Market Structure:** Break of Structure (BOS), Change of Character (CHoCH)

### 🔗 SMT (Smart Money Technique)
- **Korelacja BTC-ETH:** Detekcja dywergencji jako sygnał manipulacji
- **DXY Correlation:** Wpływ dolara na rynek crypto
- **Nasdaq Correlation:** Korelacja z tradycyjnymi rynkami
- **Manipulation Signals:** Wykrywanie akcji Smart Money

### ⏰ Time-Based Strategies
- **Killzones:** Optymalne czasy tradingu
  - 🇬🇧 London Open (7-10 UTC) - PRIORITY: High
  - 🇺🇸 NY AM (12-15 UTC) - PRIORITY: High  
  - 🇺🇸 NY PM (18-21 UTC) - PRIORITY: Medium
  - 🌏 Asia (1-5 UTC) - PRIORITY: Low
- **Session Analysis:** Analiza sentymentu sesji
- **Open Range Breakout (ORB):** Wybicie z zakresu otwarcia

### 💰 Advanced Risk Management (100x Leverage)
- **20% Safety Buffer:** Ochrona przed przedwczesną likwidacją
- **Position Sizing:** $250 risk per trade (5% konta)
- **Pyramiding:** 5 pozycji × $50 każda
- **Liquidation Calculation:** Precyzyjna kalkulacja ceny likwidacji
- **Dynamic Trailing Stop:** Oparty na ATR i poziomach płynności
  - Breakeven at 1:1 R:R
  - Active trailing at 1:3 R:R (ATR × 1.5)
  - Tight trailing at 1:10+ R:R (ATR × 0.5)

### 🚨 Emergency Systems
- **API Connection Monitoring:** Detekcja utraty połączenia
- **Max Drawdown Protection:** Limit 50% drawdown
- **Extreme Volatility Detection:** Threshold >10%
- **Max Position Duration:** 24h timeout
- **Liquidation Risk Alerts:** Warning gdy <5% od likwidacji
- **Emergency Close All:** Natychmiastowe zamykanie przy krytycznych warunkach

### 🔄 Exception Handling
- **Exponential Backoff Retry:** Inteligentne ponawianie połączeń
- **Order Queue:** Kolejka zleceń dla failed orders
- **Critical Orders → Market:** Konwersja przy krytycznych sytuacjach
- **API Freeze Recovery:** Automatyczne odzyskiwanie po zamrożeniu API

### 📈 Volume Analysis
- **CVD (Cumulative Volume Delta):** Akumulacja wolumenu
- **OBV (On-Balance Volume):** Potwierdzenie trendu
- **Volume Profile:** Rozkład wolumenu na poziomach cenowych
- **Bid/Ask Walls:** Detekcja dużych zleceń w orderbooku

### 🎯 Multiple Strategies
- **Liquidity Grab + FVG:** Kombinacja sweep'u z FVG entry
- **Bull/Bear Trap Detection:** Fałszywe wybicia
- **Wyckoff Phase Detection:** Accumulation/Markup/Distribution/Markdown
- **Session Sentiment:** Analiza sentymentu z komentarzem po polsku

---

## 🏗️ ARCHITEKTURA

```
finalbot/
├── trading_bot/
│   ├── complete_bot.py           # 🤖 GŁÓWNY BOT - wszystkie funkcje
│   ├── main_bot.py                # Legacy version
│   │
│   ├── indicators/
│   │   └── technical.py           # Technical + ICT + Volume indicators
│   │
│   ├── strategies/
│   │   ├── main_strategy.py       # Multiple strategies + signal aggregation
│   │   └── smt_killzones.py       # SMT correlation + Killzones timing
│   │
│   ├── risk_management/
│   │   ├── risk_manager.py        # Position sizing, leverage, pyramiding
│   │   ├── trailing_emergency.py  # Dynamic trailing stop + Emergency exits
│   │   └── exception_handling.py  # Retry logic, order queue, emergency protocol
│   │
│   ├── data/
│   │   └── websocket_feed.py      # Real-time WebSocket feed (Binance)
│   │
│   └── analysis/
│       └── advanced_backtest.py   # Crash scenario backtesting
│
├── ML_Finance_Codes/              # Machine Learning pipeline
└── venv/                          # Virtual environment
```

---

## 📦 INSTALACJA

### 1. Clone lub pobierz repozytorium

```bash
cd C:\Users\sebas\Desktop\finalbot
```

### 2. Utwórz virtual environment (jeśli nie istnieje)

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

### 3. Zainstaluj dependencje

```powershell
pip install pandas numpy scipy matplotlib
pip install ffn FinancePy pysabr
pip install openbb[all]
pip install tensorflow keras scikit-learn
pip install websockets  # dla WebSocket feed
```

### 4. Sprawdź instalację

```powershell
python trading_bot\complete_bot.py
```

---

## 🚀 UŻYCIE

### Basic Usage

```python
from trading_bot.complete_bot import CompleteTradingBot
import pandas as pd

# Initialize bot
bot = CompleteTradingBot(
    symbol='BTCUSDT',
    account_size=5000,
    leverage=100,
    risk_per_trade=250
)

# Przygotuj dane (OHLCV DataFrame)
# df = pobierz_dane_z_wymiany()

# Run trading cycle
result = bot.run_trading_cycle({
    'main': df,
    'btc': btc_data,  # dla SMT
    'eth': eth_data   # dla SMT
})

# Check signal
if result['signal']['signal']:
    signal = result['signal']['signal']
    print(f"Signal: {signal.direction}")
    print(f"Confidence: {signal.confidence}%")
    print(f"Entry: ${signal.entry_price:,.0f}")
```

### WebSocket Real-Time Feed

```python
from trading_bot.data.websocket_feed import WebSocketFeed
import asyncio

feed = WebSocketFeed(symbol='btcusdt')

def on_price_update(trade):
    print(f"Price: ${trade['price']:,.2f}")

feed.add_callback(on_price_update)

await feed.connect()
await feed.listen()
```

### Advanced Backtesting

```python
from trading_bot.analysis.advanced_backtest import AdvancedBacktest, generate_crash_scenario

bt = AdvancedBacktest(
    initial_capital=5000,
    leverage=100,
    safety_buffer_percent=20
)

# Test podczas crash
crash_data = generate_crash_scenario(
    base_price=50000,
    crash_percent=-30,
    duration_hours=24
)

result = bt.run_crash_test(crash_data, "Test Crash -30%")
print(f"Survival Rate: {result.survival_rate:.0f}%")
print(f"P&L: ${result.total_pnl:,.0f}")
```

---

## 🧩 MODUŁY

### 1️⃣ Technical Indicators (`indicators/technical.py`)

```python
from indicators.technical import TechnicalIndicators, ICTIndicators, VolumeIndicators

tech = TechnicalIndicators()
df = tech.calculate_all(df)  # RSI, MACD, ATR, Bollinger...

ict = ICTIndicators()
fvg = ict.detect_fvg(df)
order_blocks = ict.identify_order_blocks(df)
liquidity = ict.detect_liquidity_levels(df)

volume = VolumeIndicators()
cvd = volume.calculate_cvd(df)
```

### 2️⃣ Trading Strategy (`strategies/main_strategy.py`)

```python
from strategies.main_strategy import TradingStrategy

strategy = TradingStrategy()

# Detect strategies
liq_grab = strategy.detect_liquidity_grab(df, liquidity)
fvg_signal = strategy.detect_fvg_strategy(df, fvg)
trap = strategy.detect_bull_bear_trap(df)
wyckoff = strategy.wyckoff_phase_detection(df)

# Aggregate signal
final_signal = strategy.generate_final_signal(df, fvg, liq_grab, trap, wyckoff)
```

### 3️⃣ SMT & Killzones (`strategies/smt_killzones.py`)

```python
from strategies.smt_killzones import SMTAnalyzer, KillzonesManager

# SMT Correlation
smt = SMTAnalyzer()
divergence = smt.detect_divergence(btc_data, eth_data)

if divergence['manipulation_signal']:
    print("⚠️ Smart Money manipulation detected!")

# Killzones
killzones = KillzonesManager()
should_trade, info = killzones.should_trade_now()

if not should_trade:
    print(f"⏰ Outside killzone: {info['reason']}")
```

### 4️⃣ Risk Management (`risk_management/`)

```python
from risk_management.risk_manager import RiskManager
from risk_management.trailing_emergency import DynamicTrailingStop, EmergencyExitSystem

# Position sizing
risk_mgr = RiskManager(account_size=5000, leverage=100, risk_per_trade=250)
position = risk_mgr.calculate_position_size(entry_price=50000, stop_loss_price=49000, side='long')

# Dynamic trailing stop
trailing = DynamicTrailingStop()
new_stop = trailing.update_trailing_stop(position, current_price, atr)

# Emergency exits
emergency = EmergencyExitSystem()
should_exit, reason = emergency.should_emergency_exit(position, current_price, account_balance)
```

### 5️⃣ Exception Handling (`risk_management/exception_handling.py`)

```python
from risk_management.exception_handling import OrderQueue, EmergencyProtocol, retry_with_backoff

# Order queue
queue = OrderQueue()
queue.add_order({
    'type': 'stop_market',
    'side': 'sell',
    'quantity': 0.1,
    'critical': True
})

# Emergency protocol
emergency = EmergencyProtocol()
should_halt, reason = emergency.should_halt_trading(
    api_health=False,
    current_drawdown=15,
    max_drawdown=20,
    volatility=12,
    max_volatility=10
)

if should_halt:
    emergency.trigger_emergency(reason, positions, close_all=True)
```

---

## 💰 RISK MANAGEMENT

### Account Setup
- **Starting Capital:** $5,000
- **Leverage:** 100x (z 20% safety buffer)
- **Risk per Trade:** $250 (5% konta)
- **Max Positions:** 5 (pyramiding)

### Position Sizing Formula

```
Margin Required = Position Size / Leverage
Usable Margin = Margin × (1 - 0.20)  # 20% buffer
Position Size = Risk / (Entry - Stop Loss) × Entry
```

### Liquidation Price Calculation

**Long:**
```
Liquidation Price = Entry Price - (Usable Margin / Quantity)
```

**Short:**
```
Liquidation Price = Entry Price + (Usable Margin / Quantity)
```

### Dynamic Trailing Stop

| R:R Achieved | Trailing Mode | Distance |
|--------------|---------------|----------|
| < 1:1 | Fixed Stop | Original stop |
| 1:1 - 1:3 | Breakeven | Entry price |
| 1:3 - 1:10 | Active Trailing | ATR × 1.5 |
| > 1:10 | Tight Trailing | ATR × 0.5 |

### Emergency Exit Triggers

1. **API Connection Lost** → Close all at market
2. **Drawdown > 50%** → Close all positions
3. **Volatility > 10%** → Halt new positions
4. **Position Duration > 24h** → Close position
5. **Liquidation Distance < 5%** → Emergency close

---

## 📈 BACKTESTING

### Crash Scenario Testing

Bot testuje strategie podczas:
- **Moderate Crash (-20%):** Normal volatility
- **Severe Crash (-40%):** Extreme volatility + liquidation cascades
- **Flash Crash (-50% w 1h):** Extreme conditions

### Key Metrics

```python
result = bt.run_crash_test(crash_data, "Test Name")

# Metrics
result.total_trades        # Liczba transakcji
result.win_rate            # % wygranych
result.liquidated_trades   # Ile likwidacji
result.survival_rate       # % trades bez likwidacji
result.total_pnl           # Total P&L
result.max_drawdown        # Największy drawdown
result.sharpe_ratio        # Sharpe ratio
result.profit_factor       # Gross profit / Gross loss
```

### Example Results

```
📊 CRASH TEST: Severe Crash -40%
============================================================
Capital początkowy:     $5,000
Capital końcowy:        $3,850
P&L:                    -$1,150 (-23.0%)

Trades:
  Total:                25
  Winning:              12 (48.0%)
  Losing:               10
  ⚠️ LIQUIDATED:         3

Risk Metrics:
  Max Drawdown:         $1,500 (30.0%)
  Survival Rate:        88.0%
  Sharpe Ratio:         -0.45
  Profit Factor:        0.78
============================================================
```

---

## ❓ FAQ

### Q: Dlaczego bot nie traduje?
**A:** Sprawdź:
1. Czy jesteś w Killzone? (London/NY optimal times)
2. Czy confidence signal >= 70%?
3. Czy API połączone?
4. Czy nie przekroczono max drawdown?

### Q: Co zrobi bot gdy giełda 'zamrozi' API?
**A:** Bot:
1. Zapisze zlecenia do kolejki (`OrderQueue`)
2. Retry z exponential backoff (1s → 2s → 4s → 8s...)
3. Po powrocie API: przetworzy kolejkę
4. Critical orders (stop loss) → konwersja na MARKET

### Q: Jak buffer 20% chroni przed likwidacją?
**A:** 
- Bez bufferu: Liquidation przy -1% (100x leverage)
- Z bufferem 20%: Liquidation przy ~-0.8%
- Buffer daje margines bezpieczeństwa na spread, slippage, volatility

### Q: Czy bot może stracić więcej niż $250 per trade?
**A:** 
- **Normalnie: NIE** - stop loss chroni
- **Wyjątki:**
  - Gap/slippage podczas ekstremalnej zmienności
  - Liquidation cascade
  - API freeze podczas ruchu przeciwko pozycji
- **Ochrona:** Emergency exit system zamyka przy 50% drawdown

### Q: Jak często bot aktualizuje trailing stop?
**A:** 
- **Real-time:** Przy każdym tick'u ceny (WebSocket)
- **Warunki:**
  - Profit >= 1:1 → Breakeven
  - Profit >= 1:3 → Active trailing (ATR × 1.5)
  - Profit >= 1:10 → Tight trailing (ATR × 0.5)

### Q: Czy bot działa 24/7?
**A:** 
- **TAK**, ale preferuje Killzones:
  - **HIGH priority:** London Open (7-10 UTC), NY AM (12-15 UTC)
  - **MEDIUM priority:** NY PM (18-21 UTC)
  - **LOW priority:** Asia (1-5 UTC)
- Poza Killzones: tylko sygnały z confidence > 80%

### Q: Jak przetestować bot bez real money?
**A:**
```python
# 1. Demo mode (synthetic data)
python trading_bot/complete_bot.py

# 2. Backtesting
python trading_bot/analysis/advanced_backtest.py

# 3. Paper trading (testnet API)
# Skonfiguruj API keys dla testnet giełdy
```

---

## 🛡️ BEZPIECZEŃSTWO

### OSTRZEŻENIA ⚠️

1. **Leverage 100x = EXTREME RISK**
   - Możesz stracić cały kapitał w kilka minut
   - Tylko dla doświadczonych traderów
   - NIGDY nie używaj pieniędzy których nie możesz stracić

2. **Testuj ZAWSZE na testnet/demo**
   - Min. 1 miesiąc testów przed real money
   - Sprawdź wszystkie edge cases
   - Przetestuj crash scenarios

3. **Monitor 24/7**
   - Bot wymaga monitorowania
   - Ustaw alerty (drawdown, liquidation risk)
   - Miej plan awaryjny

4. **API Security**
   - NIGDY nie commituj API keys do git
   - Użyj .env dla secrets
   - Enable tylko potrzebne permissions (trade, read)
   - Disable withdrawals na API keys

### Best Practices

```python
# 1. Zacznij od małych pozycji
risk_per_trade = 50  # $50 zamiast $250

# 2. Zmniejsz leverage dla testów
leverage = 20  # 20x zamiast 100x

# 3. Zwiększ safety buffer
safety_buffer_percent = 30  # 30% zamiast 20%

# 4. Testuj disconnect scenarios
emergency.trigger_emergency("API test", positions, close_all=False)
```

---

## 📞 SUPPORT

- **Issues:** [GitHub Issues](https://github.com/yourusername/finalbot/issues)
- **Discord:** [Trading Bot Community](#)
- **Docs:** [Full Documentation](https://docs.yourbot.com)

---

## 📜 LICENSE

MIT License - używaj na własne ryzyko.

**DISCLAIMER:** Ten bot jest narzędziem edukacyjnym. Trading z leverage jest ekstremalnie ryzykowny. Autor nie ponosi odpowiedzialności za straty finansowe.

---

## 🎓 RESOURCES

### Nauka ICT/Smart Money:
- [The Inner Circle Trader (ICT)](https://www.youtube.com/@TheInnerCircleTrader)
- [Smart Money Concepts Explained](https://www.youtube.com/watch?v=...)
- [Fair Value Gaps Tutorial](https://www.youtube.com/watch?v=...)

### Algorithmic Trading:
- "Successful Algorithmic Trading" - książka podstawowa
- "Advances in Financial Machine Learning" - Marcos López de Prado
- [Quantopian Lectures](https://www.quantopian.com/lectures)

### Risk Management:
- "Trading Risk" - Kenneth L. Grant
- [Position Sizing Calculator](https://www.myfxbook.com/position-size-calculator)

---

**Powodzenia w tradingu! 🚀**

*Remember: The best trade is sometimes no trade at all.*
