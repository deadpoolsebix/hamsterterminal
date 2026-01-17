# 🖥️ Desktop Terminal - CustomTkinter GUI

## ALPHA TERMINAL - Professional Desktop Application

### Co to jest?
Natywna aplikacja desktopowa (Windows/Mac/Linux) w stylu Bloomberg Terminal z:
- 📈 Live price chart z FVG detection
- 📜 THE TAPE - Time & Sales feed (jak na prawdziwej giełdzie)
- 🧠 AI Market Insights w czasie rzeczywistym
- ⚡ Session markers (Asian/London/NY)
- 🐳 Whale trade detection
- 📊 RSI, MACD, Sentiment analysis

---

## Instalacja

### Krok 1: Zainstaluj CustomTkinter

```powershell
pip install customtkinter matplotlib
```

### Krok 2: Uruchom Aplikację

```powershell
python desktop_terminal.py
```

Aplikacja otworzy się w osobnym oknie (nie w przeglądarce!)

---

## Funkcje

### 📈 Live Chart Panel (Lewy)
- **FVG Detection** - zielone/czerwone strefy (Fair Value Gaps)
- **Highs/Lows markers** - złote/fioletowe punkty
- **Price line** - cyjan kolor (#00d4ff)
- **Auto-refresh** - co 3 sekundy

### 🧠 Middle Panel (Środek)
**Metryki:**
- 💰 Current Price ($94,839.00)
- 📊 24h Change (+2.35%)
- 📉 RSI (59.3) - z kolorem (oversold/overbought/neutral)

**Session Info:**
- 🌏 ASIAN SESSION (00:00-08:00)
- 🇬🇧 LONDON SESSION (08:00-16:00)
- 🇺🇸 NEW YORK SESSION (16:00-24:00)

**AI Analysis:**
```
🤖 AI MARKET ANALYSIS
========================================

⚠️ OVERBOUGHT ZONE
RSI at 72.3 suggests potential reversal.

📈 BULLISH MOMENTUM
MACD +145.2 - buyers in control.

🎯 STRATEGY SUGGESTION:
⏳ WAIT - No clear edge detected
```

### 📜 THE TAPE Panel (Prawy)
**Time & Sales Feed:**
```
TIME       PRICE        SIZE
18:42:15   $94,839.00   0.521
🐳 18:42:12   $94,842.00   4.235  ← Whale!
18:42:09   $94,838.00   1.023
```

**Whale Detection:**
- Transakcje > 3.0 BTC oznaczone 🐳
- Pokazuje wielkie zlecenia w czasie rzeczywistym

---

## Kontrolki

### Top Bar
- **Symbol Input** - wpisz BTC-USD, ETH-USD, AAPL, itp.
- **🔄 Update Button** - zmień instrument
- **● LIVE Status** - zielony = działa, czerwony = błąd

### Keyboard Shortcuts
- `Ctrl+Q` - Zamknij aplikację
- `F5` - Force refresh (przyszła wersja)

---

## Tryby Działania

### Mode 1: Z Botem (Realne Dane)
Jeśli bot działa - terminal używa:
- `RealDataFetcher` - dane z yfinance
- `LiveIndicatorsAnalyzer` - wskaźniki z bota
- Pełna integracja z AI Brain

### Mode 2: Standalone (Symulacja)
Jeśli bot nie działa:
- Pobiera dane bezpośrednio z yfinance
- Oblicza proste RSI/MACD
- Symuluje sentiment

---

## Customizacja

### Zmiana Kolorów

W pliku `desktop_terminal.py` znajdź:
```python
self.configure(fg_color="#050505")  # ← Tło główne (czarne)
```

Zmień na:
- `#0b0e11` - Ciemny niebieski (jak Streamlit)
- `#1a1a1a` - Ciemny szary
- `#000000` - Kompletnie czarny

### Zmiana Timeframe

```python
# Linia ~280:
df = yf.download(self.current_symbol, period='2d', interval='15m')
```

Zmień na:
- `interval='1h'` - Godzinowy (więcej historii)
- `interval='5m'` - 5-minutowy (ultra-fast)
- `interval='1d'` - Dzienny (long-term)

### Dodanie Nowych Metryk

W `update_metrics()`:
```python
# Dodaj nowy label:
self.volume_label = ctk.CTkLabel(
    metrics_frame,
    text=f"VOL: {df['Volume'].iloc[-1]:,.0f}",
    font=("Consolas", 12)
)
self.volume_label.pack(pady=5)
```

---

## Integracja z Botem

### Scenariusz 1: Bot + Desktop Terminal
```powershell
# Terminal 1 - Bot traduje
python run_professional_bot.py

# Terminal 2 - Desktop terminal wizualizuje
python desktop_terminal.py
```

**Korzyści:**
- Bot wykonuje zlecenia
- Desktop terminal pokazuje na żywo co się dzieje
- THE TAPE pokazuje wszystkie transakcje

### Scenariusz 2: Multi-Monitor Setup
**Monitor 1:** Desktop terminal (chart + tape)
**Monitor 2:** HTML dashboard (web browser)
**Monitor 3:** TradingView (Pine Script)

= **Ultimate Professional Setup** 🚀

---

## Performance

### Optimalizacja
- **Tape limit:** 50 entries (żeby nie zwalniać)
- **Chart refresh:** 3 sekundy
- **Thread-safe:** Updates w osobnym wątku
- **Memory:** ~50-100 MB RAM

### Jeśli Działa Wolno
1. Zwiększ refresh interval:
```python
time.sleep(3)  # ← Zmień na 5 lub 10
```

2. Zmniejsz tape entries:
```python
if len(lines) > 50:  # ← Zmień na 30
```

3. Uproszcz chart:
```python
ax.plot(..., linewidth=1)  # ← Zmień na 0.5
```

---

## Porównanie: Desktop vs Web

| Feature | Desktop (CTk) | Web (Streamlit) | HTML Dashboard |
|---------|---------------|-----------------|----------------|
| **Speed** | Natywny (szybki) | Przeglądarka | Ultra-fast |
| **Setup** | 1 komenda | 1 komenda | Serwer + ngrok |
| **UI Control** | Pełna kontrola | Ograniczona | Pełna kontrola |
| **THE TAPE** | ✅ Natywny | ❌ Trudne | ✅ JavaScript |
| **Offline** | ✅ Działa | ❌ Wymaga serwera | ❌ Wymaga serwera |
| **Mobile** | ❌ Desktop only | ✅ Responsive | ✅ Responsive |

**Kiedy użyć Desktop Terminal:**
- Day trading (potrzebujesz THE TAPE)
- Multi-monitor setup
- Offline praca
- Maksymalna wydajność

---

## Advanced Features

### Dodanie Alerts

```python
def check_alerts(self, rsi):
    if rsi > 75:
        # Dźwięk alertu
        import winsound
        winsound.Beep(1000, 500)  # 1000 Hz, 500 ms
        
        # Popup
        from tkinter import messagebox
        messagebox.showwarning("Alert", "RSI > 75: OVERBOUGHT!")
```

### Zapis THE TAPE do pliku

```python
def save_tape_to_csv(self):
    tape_text = self.tape_box.get("1.0", "end")
    with open("tape_log.csv", "w") as f:
        f.write("Time,Price,Size\n")
        f.write(tape_text)
```

### Dark/Light Mode Toggle

```python
def toggle_theme(self):
    current = ctk.get_appearance_mode()
    new = "light" if current == "Dark" else "dark"
    ctk.set_appearance_mode(new)
```

---

## Troubleshooting

### Problem: "No module named 'customtkinter'"
**Rozwiązanie:**
```powershell
pip install customtkinter
```

### Problem: Chart nie wyświetla się
**Rozwiązanie:**
```powershell
pip install matplotlib --upgrade
```

### Problem: "Threading error"
**Rozwiązanie:**
- Zamknij aplikację (Ctrl+Q)
- Uruchom ponownie
- Jeśli dalej problem: usuń `daemon=True` z threading

### Problem: Tape się nie aktualizuje
**Rozwiązanie:**
Sprawdź czy `live_feed_loop()` działa:
```python
print("Feed loop running...")  # Dodaj debug
```

---

## Deployment

### Windows Executable (.exe)

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed desktop_terminal.py
```

**Output:** `dist/desktop_terminal.exe` (20-30 MB)

Wyślij znajomym - mogą uruchomić bez Pythona!

### Mac Application (.app)

```bash
pip install py2app
python setup.py py2app
```

### Linux AppImage

```bash
pip install pyinstaller
pyinstaller --onefile desktop_terminal.py
```

---

## Quick Commands

```powershell
# Zainstaluj wymagania
pip install customtkinter matplotlib yfinance pandas

# Uruchom terminal
python desktop_terminal.py

# Uruchom z botem
python run_professional_bot.py  # Terminal 1
python desktop_terminal.py      # Terminal 2

# Build .exe
pyinstaller --onefile --windowed desktop_terminal.py
```

---

**Gotowe!** 🖥️ Masz profesjonalny desktop terminal jak na prawdziwej giełdzie! 

Uruchom: `python desktop_terminal.py` i traduj! ⚡
