# 💰 FUNDING RATE CALCULATOR - DOKUMENTACJA

## 📋 OPIS

Zaawansowany kalkulator **funding rate** dla pozycji na kryptowalutach (futures perpetual). System oblicza:
- **Koszt financowania** dla każdej pozycji
- **Break-even punkt** uwzględniając fees i funding
- **P&L scenariusze** dla różnych cen wyjścia
- **Optymalną wielkość pozycji** z uwzględnieniem kosztów
- **Rzeczywiste opłaty** (entry/exit fees + funding costs)

## 📁 PLIKI

### 1. `funding_rate_calculator.py` (NOWY)
Kompletny moduł do obliczania funding rate z klasą `FundingRateCalculator`

### 2. `ml_trading_brain.py` (ZAKTUALIZOWANY)
Zintegrowana klasa `TradingBrain` z nowymi metodami:
- `calculate_position_funding_cost()` - koszt pozycji
- `calculate_position_break_even()` - break-even
- `analyze_current_position()` - analiza bieżącej pozycji
- `simulate_price_scenarios()` - scenariusze P&L
- `calculate_optimal_position_with_funding()` - optymalna pozycja
- `evaluate_trade_with_funding()` - ocena transakcji

### 3. `professional_dashboard_final.html` (ZAKTUALIZOWANY)
Dodany nowy panel: **💰 FUNDING RATE CALC** w AI Trainer Game Boy

## 🎮 GAME BOY INTERFACE

### Nowy Panel: FUNDING RATE CALC
```
┌─────────────────────────────┐
│ 💰 FUNDING RATE CALC        │
├─────────────────────────────┤
│ Position (USDT): [10000]    │
│ Entry $: [95000]            │
│ Leverage: [10]              │
│ Hold (h): [4]               │
│                             │
│ [CALC FUNDING]              │
│                             │
│ Cost: $12.50                │
│ B/E: 0.1234%                │
└─────────────────────────────┘
```

**Oblicza:**
- Koszt financowania na podstawie czasu holdowania
- Break-even procent (ile % ruchu potrzeba aby pokryć koszty)
- Szacunkowe fees (entry + exit)

## 💻 UŻYCIE W PYTHONIE

### Przykład 1: Oblicz koszt pozycji

```python
from funding_rate_calculator import FundingRateCalculator
from datetime import datetime, timedelta

calc = FundingRateCalculator()

entry_time = datetime.now() - timedelta(hours=2)
exit_time = datetime.now()

cost = calc.calculate_funding_cost_position(
    position_size_usdt=10000,
    entry_price=95000,
    exit_price=97000,
    entry_time=entry_time,
    exit_time=exit_time,
    position_type='LONG',
    leverage=10,
    exchange='binance',
    volatility_level='medium'
)

print(f"Funding Cost: ${cost['total_funding_cost']}")
print(f"Fees: ${cost['total_fees']}")
print(f"Net P&L: ${cost['pnl_net']}")
print(f"ROI: {cost['roi_percent']}%")
```

### Przykład 2: Analiza bieżącej pozycji

```python
analysis = calc.calculate_position_analysis(
    symbol='BTCUSDT',
    position_size_usdt=10000,
    entry_price=95000,
    current_price=96500,
    position_type='LONG',
    leverage=10,
    exchange='binance',
    coin_name='BTC'
)

print(f"Unrealized P&L: ${analysis['unrealized_pnl']}")
print(f"Funding Cost (accumulated): ${analysis['accumulated_funding_cost']}")
print(f"Net P&L: ${analysis['net_pnl_current']}")
print(f"Liquidation Price: ${analysis['liquidation_price']}")
print(f"Distance to Liquidation: {analysis['distance_to_liquidation_percent']}%")
```

### Przykład 3: Break-even kalkulacja

```python
be = calc.calculate_funding_break_even(
    position_size_usdt=10000,
    entry_price=95000,
    position_type='LONG',
    leverage=10,
    hold_hours=4
)

print(f"Break-Even Price: ${be['break_even_price']}")
print(f"Price Move Needed: {be['move_needed_percent']}%")
print(f"Total Cost: ${be['total_cost_to_recover']}")
```

### Przykład 4: Scenariusze P&L

```python
scenarios = calc.simulate_position_scenarios(
    position_size_usdt=10000,
    entry_price=95000,
    position_type='LONG',
    leverage=10,
    hold_hours=8
)

for scenario in scenarios['scenarios']:
    print(f"Exit @ ${scenario['exit_price']}: " +
          f"P&L ${scenario['net_pnl']} " +
          f"({scenario['roi_percent']}%)")
```

### Przykład 5: Integracja z AI Brain

```python
from ml_trading_brain import TradingBrain
from datetime import datetime, timedelta

brain = TradingBrain()

# Analiza bieżącej pozycji z fundingiem
analysis = brain.analyze_current_position(
    symbol='BTCUSDT',
    position_size_usdt=10000,
    entry_price=95000,
    current_price=96500,
    position_type='LONG',
    leverage=10,
    exchange='binance'
)

# Ocena transakcji ze wszystkimi kosztami
trade = brain.evaluate_trade_with_funding(
    symbol='BTCUSDT',
    entry_price=95000,
    exit_price=96500,
    entry_time=datetime.now() - timedelta(hours=2),
    exit_time=datetime.now(),
    position_type='LONG',
    position_size_usdt=10000,
    leverage=10
)

print(f"Gross P&L: ${trade['gross_pnl']}")
print(f"Net P&L (with funding): ${trade['net_pnl']}")
print(f"ROI: {trade['roi_percent']}%")

# Optymalna pozycja z uwzględnieniem kosztów
opt = brain.calculate_optimal_position_with_funding(
    capital=50000,
    confidence=75,
    entry_price=95000,
    target_roi_percent=2.5,
    max_hold_hours=24,
    leverage=10
)

print(f"Optimized Position: ${opt['optimized_position_size']}")
print(f"Total Costs: ${opt['total_estimated_costs']}")
```

## 📊 FEATURE DETAILS

### Giełdy wspierane:
- **Binance** (0.01% avg funding)
- **Bybit** (0.005% avg)
- **OKX** (0.01% avg)
- **dYdX** (0.015% avg)
- **Hyperliquid** (0.02% avg)

### Levele volatilności:
- **Low**: 0.5x multiplier (volatility < 20%)
- **Medium**: 1.0x multiplier (volatility 20-50%)
- **High**: 1.5x multiplier (volatility 50-100%)
- **Extreme**: 2.5x multiplier (volatility > 100%)

### Parametry kalkulacji:

```python
# Takerka fee: 0.04% per side = 0.08% total
# Daily funding rate: ~0.01% (średnia Binance)
# Leverage: od 1x do 125x
# Hold time: dowolny (godziny, dni)
```

## ⚡ QUICK START - GAME BOY PANEL

1. Wpisz **Position Size** w USDT (przykład: 10000)
2. Wpisz **Entry Price** (przykład: 95000)
3. Wpisz **Leverage** (przykład: 10)
4. Wpisz **Hold Hours** (przykład: 4)
5. Kliknij **CALC FUNDING**
6. Zobaczysz:
   - **Cost**: Całkowity koszt funding + fees
   - **B/E**: Procent ruchu potrzebny do break-even

## 🎯 WSKAŹNIKI MONITOROWANIA

### Daily Funding Rate Impact:
- **0.01%/day** = $1 na $10,000 pozycji dziennie
- **0.02%/day** = $2 na $10,000 pozycji dziennie
- **-0.005%/day** = SHORT zarabia $0.50 na $10,000 dziennie

### Break-Even Rule:
```
Move needed (%) = (Funding Cost + Fees) / Entry Price * 100
```

### Best Practices:
1. **Shorts gdy funding ujemny** - zarabiasz na fundingu
2. **Longi gdy funding niski** - mniejszy koszt holdowania
3. **Scalp handlowanie** - unika długotrwałych kosztów
4. **Monitoruj daily rates** - zmienią się wraz z markerem

## 📈 PRZYKŁADOWE SCENARIUSZE

### Scenariusz 1: LONG na BTC
```
Position: $10,000
Entry: $95,000
Leverage: 10x
Hold: 4 godziny
Daily Funding: 0.01%
Exchange: Binance

Results:
- Funding Cost: $1.67
- Fees: $8.00
- Total Cost: $9.67
- Break-Even: 0.0102%
- Coins: 0.1053 BTC
```

### Scenariusz 2: SHORT na BTC (funding ujemny)
```
Position: $10,000
Entry: $95,000
Leverage: 10x
Hold: 24 godziny
Daily Funding: -0.005% (SHORT zarabia!)
Exchange: Binance

Results:
- Funding Income: +$1.20 (SHORT otrzymuje!)
- Fees: $8.00
- Net Cost: -$6.80 (zarobek na fundingu!)
- Break-Even: -0.0072%
```

### Scenariusz 3: Scalp trade
```
Position: $5,000
Entry: $95,000
Leverage: 5x
Hold: 15 minut
Daily Funding: 0.01%

Results:
- Funding Cost: $0.052 (niemal zero!)
- Fees: $4.00
- Total Cost: $4.05
- Break-Even: 0.0085%
```

## ⚠️ OSTRZEŻENIA

1. **Liquidation Risk**: Upewnij się że margin jest wystarczający
2. **Funding Spikes**: Raty mogą skoczyć w górę 10x podczas volatilności
3. **Fees Accumulate**: Entry + exit fees to 0.08% - znaczące dla scalping
4. **Time Is Cost**: Długie holdowanie = więcej fundingu
5. **Leverage Kill**: 100x leverage = mały ruch = liquidacja

## 📝 INTEGRACJA Z BOTAMI

Aby używać w swoim tradering bota:

```python
from ml_trading_brain import TradingBrain

class MyTradingBot:
    def __init__(self):
        self.brain = TradingBrain()
    
    def check_trade_profitability(self, entry_price, exit_price, hold_hours):
        # Oblicz rzeczywisty profit z fundingiem
        trade_eval = self.brain.evaluate_trade_with_funding(
            symbol='BTCUSDT',
            entry_price=entry_price,
            exit_price=exit_price,
            entry_time=datetime.now() - timedelta(hours=hold_hours),
            exit_time=datetime.now(),
            position_type='LONG',
            position_size_usdt=10000,
            leverage=10
        )
        
        return trade_eval['is_profitable']
    
    def get_optimal_position_size(self, capital, confidence):
        # Uzyskaj pozycję z uwzględnieniem fundingu
        opt = self.brain.calculate_optimal_position_with_funding(
            capital=capital,
            confidence=confidence,
            entry_price=95000,
            target_roi_percent=2.5
        )
        
        return opt['optimized_position_size']
```

## 🚀 TESTING

Uruchom test:
```bash
python funding_rate_calculator.py
```

Lub w AI Brain:
```bash
python ml_trading_brain.py
```

## ✅ CHECKLIST PRZED TRADINGIEM

- [ ] Sprawdzić daily funding rate na wybranej giełdzie
- [ ] Obliczyć break-even % przed wejściem
- [ ] Upewnić się że target ROI > break-even cost
- [ ] Monitorować zmianę funding rate (może się zmienić co 8h)
- [ ] Dla SHORT pozycji sprawdzić czy funding jest ujemny (zarobek)
- [ ] Nie ignorować fees - suma się szybko
- [ ] Scalp trades lepsze niż swing (mniej fundingu)

---

**Autorzy**: Financial AI Team | Zaktualizowanie: 2026-01-17
**Wersja**: 2.0 | Funkcjonalność: Funding Rate Calculations
