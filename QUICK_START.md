# 🚀 QUICK START - Command Reference

**Szybkie komendy do uruchomienia wszystkich testów i demów**

---

## 📋 SETUP (First Time Only)

```powershell
# 1. Navigate to project
cd C:\Users\sebas\Desktop\finalbot

# 2. Activate venv
.\venv\Scripts\Activate

# 3. Install/Update requirements
pip install -r requirements.txt --upgrade

# 4. Verify installation
python -c "import pandas, numpy, keras; print('✅ All libraries OK')"
```

---

## 🎬 DEMO COMMANDS

### Run Complete Bot Demo
```powershell
python trading_bot\complete_bot.py
```
**Output:** Full trading cycle with all modules integrated

### Run Technical Indicators Demo
```powershell
python trading_bot\indicators\technical.py
```
**Output:** RSI, MACD, ATR, Bollinger, Stochastic, ICT, Volume indicators

### Run SMT & Killzones Demo
```powershell
python trading_bot\strategies\smt_killzones.py
```
**Output:** BTC-ETH divergence, Killzones timing, manipulation signals

### Run Strategy Demo
```powershell
python trading_bot\strategies\main_strategy.py
```
**Output:** Liquidity grab, FVG, bull/bear traps, Wyckoff, ORB, sentiment

### Run Crash Backtesting
```powershell
python trading_bot\analysis\advanced_backtest.py
```
**Output:** Survival rates during -20%, -40%, -50% crashes

### Run CVD Filtering Demo
```powershell
python trading_bot\analysis\cvd_filtering.py
```
**Output:** CVD filtering, outlier detection, divergence analysis

### Run Fees & Slippage Demo
```powershell
python trading_bot\risk_management\fees_and_slippage.py
```
**Output:** Fee calculation, true P&L, slippage impact

### Run Exception Handling Demo
```powershell
python trading_bot\risk_management\exception_handling.py
```
**Output:** Retry mechanism, API freeze scenarios, order queue

### Run Risk Management Demo
```powershell
python trading_bot\risk_management\risk_manager.py
```
**Output:** Position sizing, pyramiding, liquidation calculation

### Run Trailing Stop Demo
```powershell
python trading_bot\risk_management\trailing_emergency.py
```
**Output:** Dynamic trailing stop, emergency exit system

### Run WebSocket Demo
```powershell
python trading_bot\data\websocket_feed.py
```
**Output:** Real-time price feed, bid/ask walls, latency monitoring
(requires internet connection)

---

## 🧪 TESTING COMMANDS

### Run all tests
```powershell
python -m pytest trading_bot\ -v
```

### Test specific module
```powershell
python -m pytest trading_bot\indicators\technical.py -v
python -m pytest trading_bot\strategies\ -v
python -m pytest trading_bot\risk_management\ -v
```

### Check for errors/warnings
```powershell
python trading_bot\complete_bot.py --check
python trading_bot\analysis\advanced_backtest.py --verbose
```

---

## 📊 DATA COMMANDS

### Download and save market data
```powershell
python -c "
from trading_bot.data.websocket_feed import WebSocketFeed
import asyncio

async def demo():
    feed = WebSocketFeed('btcusdt')
    await feed.connect()
    await asyncio.sleep(30)  # 30 seconds
    df = feed.get_recent_prices(100)
    df.to_csv('btc_data.csv')
    print(f'✅ Downloaded {len(df)} candles')
    await feed.stop()

asyncio.run(demo())
"
```

### Check real-time price
```powershell
python -c "
import ccxt
exchange = ccxt.binance()
ticker = exchange.fetch_ticker('BTC/USDT')
print(f\"BTC Price: \${ticker['last']:,.0f}\")
print(f\"24h Change: {ticker['percentage']:+.2f}%\")
"
```

---

## 🔧 DEVELOPMENT COMMANDS

### Code formatting
```powershell
black trading_bot\
```

### Linting
```powershell
pylint trading_bot\
```

### Type checking
```powershell
mypy trading_bot\
```

### Run with debug logging
```powershell
$env:LOG_LEVEL = "DEBUG"
python trading_bot\complete_bot.py
```

---

## 📈 ANALYSIS COMMANDS

### Generate backtest report
```powershell
python -c "
from trading_bot.analysis.advanced_backtest import AdvancedBacktest, generate_crash_scenario

bt = AdvancedBacktest()
crash = generate_crash_scenario(crash_percent=-30)
result = bt.run_crash_test(crash, 'Test')

print(f'Survival: {result.survival_rate:.0f}%')
print(f'P&L: {result.total_pnl:,.0f}')
print(f'Sharpe: {result.sharpe_ratio:.2f}')
"
```

### Run extended backtesting (all scenarios)
```powershell
python -c "
from trading_bot.analysis.advanced_backtest import AdvancedBacktest, generate_crash_scenario

crashes = [
    ('Moderate', -20, 2.0),
    ('Severe', -40, 5.0),
    ('Extreme', -50, 10.0),
]

for name, pct, vol in crashes:
    bt = AdvancedBacktest()
    data = generate_crash_scenario(crash_percent=pct, volatility_multiplier=vol)
    result = bt.run_crash_test(data, f'{name} Crash')
    print(f'{name}: {result.survival_rate:.0f}% survival rate')
"
```

---

## 🌐 EXCHANGE SETUP

### Test Binance connection
```powershell
python -c "
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()
exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY', 'your_key'),
    'secret': os.getenv('BINANCE_API_SECRET', 'your_secret'),
    'sandbox': True  # testnet
})

try:
    balance = exchange.fetch_balance()
    print('✅ Connected to Binance testnet')
    print(f'USDT: {balance.get(\"USDT\", {}).get(\"free\", 0):.2f}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

### Create .env file
```powershell
@"
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
MODE=testnet
"@ | Out-File -Encoding UTF8 .env
```

---

## 📊 MONITORING COMMANDS

### Monitor bot performance
```powershell
# Run monitoring dashboard
python -c "
from trading_bot.complete_bot import CompleteTradingBot
from datetime import datetime

bot = CompleteTradingBot()

while True:
    import time
    print(f'\n{datetime.now().strftime(\"%H:%M:%S\")} - Bot monitoring active')
    print(f'Account: \${bot.account_size:,.0f}')
    print(f'Positions: {len(bot.active_positions)}')
    
    should_trade, kz = bot.killzones.should_trade_now()
    print(f'Killzone: {kz[\"current_zone\"]} ({\"✅\" if should_trade else \"❌\"})')
    
    time.sleep(60)  # Check every minute
"
```

### Log bot activity
```powershell
# Redirect output to file
python trading_bot\complete_bot.py > bot_activity.log 2>&1

# Tail the log
Get-Content bot_activity.log -Tail 50 -Wait
```

---

## 🆘 TROUBLESHOOTING COMMANDS

### Check Python version
```powershell
python --version  # Should be 3.11+
```

### List installed packages
```powershell
pip list | findstr pandas
pip list | findstr keras
pip list | findstr ccxt
```

### Test import all modules
```powershell
python -c "
try:
    from trading_bot.indicators.technical import TechnicalIndicators
    from trading_bot.strategies.main_strategy import TradingStrategy
    from trading_bot.risk_management.risk_manager import RiskManager
    from trading_bot.analysis.advanced_backtest import AdvancedBacktest
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
"
```

### Reinstall specific package
```powershell
pip uninstall pandas -y
pip install pandas==2.3.3
```

### Update all packages
```powershell
pip list --outdated
pip install -r requirements.txt --upgrade
```

---

## 🎯 PRODUCTION COMMANDS

### Start paper trading
```powershell
python -c "
from trading_bot.complete_bot import CompleteTradingBot
import pandas as pd
import numpy as np

bot = CompleteTradingBot(
    account_size=5000,
    leverage=100,
    risk_per_trade=50  # START SMALL
)

print('🤖 Bot started in PAPER TRADING mode')
print(f'Account: \${bot.account_size:,.0f}')
print(f'Risk per trade: \${50:,.0f}')
print('Monitor carefully!')
"
```

### Activate kill switch (EMERGENCY)
```powershell
python -c "
from trading_bot.risk_management.exception_handling import EmergencyProtocol

emergency = EmergencyProtocol()
positions = []  # Your open positions

print('🚨 ACTIVATING KILL SWITCH')
emergency.trigger_emergency(
    'Manual emergency activation',
    positions,
    close_all=True
)
print('✅ All positions closed')
"
```

---

## 📁 FILE ORGANIZATION

### Important files
```
trading_bot\
├── complete_bot.py          # MAIN BOT
├── indicators\technical.py  # Indicators
├── strategies\
│   ├── main_strategy.py     # Strategies
│   └── smt_killzones.py     # SMT+Killzones
├── risk_management\
│   ├── risk_manager.py      # Position sizing
│   ├── trailing_emergency.py # Trailing stop
│   ├── exception_handling.py # Error recovery
│   └── fees_and_slippage.py # Fee management
├── analysis\
│   ├── advanced_backtest.py # Backtesting
│   └── cvd_filtering.py     # CVD analysis
└── data\
    └── websocket_feed.py    # Real-time data
```

---

## 📝 LOGGING & OUTPUT

### Enable detailed logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Save output to file
```powershell
python trading_bot\complete_bot.py | Tee-Object -FilePath output.log
```

---

## 🎓 LEARNING PATH

1. **Start here:** `python trading_bot\complete_bot.py`
2. **Understand indicators:** `python trading_bot\indicators\technical.py`
3. **Learn strategies:** `python trading_bot\strategies\main_strategy.py`
4. **Test backtesting:** `python trading_bot\analysis\advanced_backtest.py`
5. **Understand risk:** `python trading_bot\risk_management\risk_manager.py`
6. **Study fees:** `python trading_bot\risk_management\fees_and_slippage.py`
7. **Read guide:** See `IMPLEMENTATION_GUIDE.md`

---

## ✅ QUICK CHECKLIST

- [ ] Installed all requirements: `pip install -r requirements.txt`
- [ ] Ran complete bot demo: `python trading_bot\complete_bot.py`
- [ ] Tested crash scenarios: `python trading_bot\analysis\advanced_backtest.py`
- [ ] Understood risk management: `python trading_bot\risk_management\risk_manager.py`
- [ ] Created .env file with API keys
- [ ] Tested connection to testnet/exchange
- [ ] Ready for paper trading!

---

**Now go implement! 🚀**
