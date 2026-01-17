# 📊 TradingView Integration - Instrukcja

## Profesjonalny Skrypt Pine Script z FVG i Dashboard

### Funkcje Skryptu:

**1. Fair Value Gaps (FVG)**
- ✅ Wykrywanie luk wzrostowych (Bullish FVG)
- ✅ Wykrywanie luk spadkowych (Bearish FVG)
- ✅ Automatyczne oznaczanie kolorami (zielony/czerwony)
- ✅ Labele "BULL FVG" i "BEAR FVG"

**2. Dashboard Terminal**
- 📈 Aktualna cena
- 📊 Zmiana procentowa 24h (kolorowa)
- 📉 RSI (14) z kolorowym oznaczeniem
- 🎯 Sygnał: OVERBOUGHT/OVERSOLD/NEUTRAL
- 📦 Wolumen z formatowaniem

**3. Sygnały**
- RSI > 70 → **OVERBOUGHT (SELL)** - czerwony
- RSI < 30 → **OVERSOLD (BUY)** - zielony
- RSI 30-70 → **NEUTRAL** - biały

---

## Jak Użyć na TradingView:

### Krok 1: Otwórz TradingView
1. Wejdź na: https://www.tradingview.com/
2. Zaloguj się (lub załóż darmowe konto)
3. Otwórz wykres BTC/USDT (lub inną parę)

### Krok 2: Dodaj Skrypt
1. Kliknij "Pine Editor" (na dole ekranu)
2. Skopiuj cały kod z pliku: `tradingview_fvg_dashboard.pine`
3. Wklej do Pine Editor
4. Kliknij "Add to Chart" (Dodaj do wykresu)

### Krok 3: Konfiguracja
1. Kliknij ikonę ⚙️ przy skrypcie na wykresie
2. Zakładka "Inputs":
   - ☑️ Pokaż Fair Value Gaps
   - 🎨 Zmień kolory FVG (opcjonalnie)
   - 🎨 Kolor dashboardu (opcjonalnie)
3. Kliknij "OK"

---

## Co Zobaczysz na Wykresie:

### Fair Value Gaps (FVG)
Zielone/czerwone prostokąty pokazujące luki cenowe:
- 🟢 **Bullish FVG** - obszar gdzie cena może wrócić (wsparcie)
- 🔴 **Bearish FVG** - obszar gdzie cena może wrócić (opór)

### Dashboard (prawy górny róg)
```
┌─────────────────────┬──────────┐
│ MARKET TERMINAL     │ STATUS   │
├─────────────────────┼──────────┤
│ Price:              │ 94839.00 │
│ 24h Change:         │ +2.35%   │ (zielony/czerwony)
│ RSI (14):           │ 59.32    │ (kolorowy)
│ Signal:             │ NEUTRAL  │
│ Volume:             │ 2.3M     │
└─────────────────────┴──────────┘
```

---

## Integracja z Botem

Ten skrypt Pine Script używa **tej samej logiki FVG** co Twój bot Python!

**W bocie masz:**
```python
# trading_bot/strategies/main_strategy.py
def detect_fvg(self, data):
    # Bullish FVG: low[0] > high[2]
    # Bearish FVG: high[0] < low[2]
```

**Na TradingView widzisz:**
- Te same FVG gaps co bot wykrywa
- Te same sygnały RSI
- Ten sam RSI (14)

**Synchronizacja:**
1. Bot traduje na podstawie FVG
2. TradingView pokazuje te same FVG wizualnie
3. Możesz potwierdzać sygnały bota na wykresie!

---

## Rozszerzenia (Opcjonalne)

### Dodaj SMT Divergence
Wklej przed `// --- DASHBOARD`:
```pinescript
// SMT Divergence (BTC vs ETH)
btcRsi = ta.rsi(close, 14)
ethClose = request.security("BINANCE:ETHUSDT", timeframe.period, close)
ethRsi = ta.rsi(ethClose, 14)
smtDiv = math.abs(btcRsi - ethRsi) > 15
bgcolor(smtDiv ? color.new(color.purple, 90) : na, title="SMT Divergence")
```

### Dodaj Wyckoff Phases
Wklej przed dashboard:
```pinescript
// Wyckoff Phase Detection
phase = ""
if rsiVal < 40 and volume > ta.sma(volume, 20)
    phase := "ACCUMULATION"
else if rsiVal > 60 and volume > ta.sma(volume, 20)
    phase := "DISTRIBUTION"
else if rsiVal > 50 and ta.change(close) > 0
    phase := "MARKUP"
else if rsiVal < 50 and ta.change(close) < 0
    phase := "MARKDOWN"
else
    phase := "NEUTRAL"
```

Dodaj do dashboardu (po Volume):
```pinescript
table.cell(terminalDash, 0, 6, "Wyckoff Phase:", text_color=color.white)
table.cell(terminalDash, 1, 6, phase, text_color=color.orange)
```

---

## Alerty TradingView → Telegram

### Krok 1: Utwórz Alert
1. Kliknij prawym na wykres → "Add Alert"
2. Condition: "Professional Terminal FVG & Dashboard"
3. Message: `{{ticker}} SIGNAL: {{close}}`
4. Webhook URL: (jeśli masz Telegram bot)

### Krok 2: Webhook → Telegram
Możesz użyć:
- **Alertatron** (zapłać za usługę)
- **Własny serwer Flask** (darmowy):
  ```python
  from flask import Flask, request
  import requests
  
  app = Flask(__name__)
  
  @app.route('/webhook', methods=['POST'])
  def webhook():
      data = request.json
      # Send to Telegram
      bot_token = "YOUR_BOT_TOKEN"
      chat_id = "YOUR_CHAT_ID"
      message = f"🚨 TradingView Alert: {data}"
      url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
      requests.post(url, data={"chat_id": chat_id, "text": message})
      return "OK", 200
  
  app.run(port=5000)
  ```

---

## FAQ

**Q: Czy mogę użyć tego na innych parach?**
A: Tak! Działa na wszystkich: BTC, ETH, SPY, EUR/USD, etc.

**Q: Czy skrypt jest darmowy?**
A: Tak, Pine Script jest darmowy. Premium tylko dla zaawansowanych funkcji (np. więcej alertów).

**Q: Czy FVG działa na wszystkich timeframe'ach?**
A: Tak, ale najlepiej działa na: 15m, 1h, 4h (te same co bot używa).

**Q: Czy mogę połączyć z botem?**
A: Tak! Bot traduje, a TradingView wizualizuje. Idealna kombinacja.

---

## Best Practices

1. **Multi-timeframe:** Otwórz 4 wykresy (1m, 15m, 1h, 4h) z tym skryptem
2. **Dodaj bota:** Bot traduje gdy FVG + RSI się zgadzają na wielu timeframe'ach
3. **Confluence:** Jeśli TradingView i bot pokazują to samo → silny sygnał!
4. **Backtesting:** Użyj TradingView "Bar Replay" do testowania strategii

---

**Gotowe!** Masz teraz profesjonalny terminal na TradingView z tą samą logiką co bot! 🚀
