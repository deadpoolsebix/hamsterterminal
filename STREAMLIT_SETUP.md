# 🚀 Streamlit Terminal - Instrukcja Uruchomienia

## ALPHA TERMINAL - Bloomberg-Style Professional Dashboard

### Co to jest?
Profesjonalna aplikacja webowa w stylu Bloomberg Terminal z:
- 📊 Interaktywne wykresy FVG (Fair Value Gaps)
- 🧠 AI Market Sentiment & Analysis
- 📈 MACD, RSI, Bollinger Bands, Volume Profile
- 📰 Live Market News
- 🎯 Trading Signals (BUY/SELL)

---

## Instalacja Wymaganych Bibliotek

```powershell
# W terminalu z aktywowanym venv:
pip install streamlit pandas-ta plotly
```

Biblioteki które będą zainstalowane:
- **streamlit** - Framework do tworzenia web aplikacji
- **pandas-ta** - Biblioteka wskaźników technicznych
- **plotly** - Interaktywne wykresy
- **yfinance** - Już masz zainstalowane (pobieranie danych)

---

## Uruchomienie Aplikacji

### Opcja 1: Lokalnie (tylko dla Ciebie)

```powershell
streamlit run streamlit_terminal.py
```

Aplikacja otworzy się automatycznie w przeglądarce pod: **http://localhost:8501**

### Opcja 2: W sieci lokalnej (dla znajomych w tej samej WiFi)

```powershell
streamlit run streamlit_terminal.py --server.address 0.0.0.0
```

Znajomi mogą wejść przez: **http://TWOJ_IP:8501**  
(Sprawdź swoje IP przez: `ipconfig` → szukaj "IPv4 Address")

### Opcja 3: Publicznie przez Ngrok (dla każdego w internecie)

**Terminal 1** - Uruchom Streamlit:
```powershell
streamlit run streamlit_terminal.py --server.port 8501
```

**Terminal 2** - Uruchom Ngrok:
```powershell
ngrok http 8501
```

Ngrok wygeneruje publiczny link typu: `https://abc123.ngrok-free.app`

Wyślij ten link znajomym - będą mogli korzystać z terminalu!

---

## Funkcje Aplikacji

### 🕹️ Panel Sterowania (Sidebar)

**Instrument:**
- BTC-USD (Bitcoin)
- ETH-USD (Ethereum)
- AAPL (Apple Stock)
- TSLA (Tesla Stock)
- Dowolny symbol z Yahoo Finance

**Interwał:**
- 1h - Godzinowy (day trading)
- 4h - 4-godzinny (swing trading)
- 1d - Dzienny (pozycyjny)

**Dane Historyczne:**
- 30-365 dni danych do analizy

**Zaawansowane:**
- ☑️ Pokaż Fair Value Gaps (zielone/czerwone prostokąty)
- ☑️ Pokaż MACD (momentum)
- ☑️ Pokaż Volume Profile (wolumen)

---

## Zakładki

### 📊 Wykres Pro
- **Candlestick Chart** z FVG detection
- **Bollinger Bands** (niebieskie linie)
- **MACD Histogram** (zielone/czerwone bary)
- **Volume Analysis** (kolorowy wolumen)
- **FVG Counter** - ile luk wykryto

### 🧠 AI Insights
- **Market Sentiment** - AI analiza sytuacji
- **Technical Summary** - kluczowe statystyki
- **Trading Signals** - sygnały BUY/SELL
  - RSI Oversold/Overbought
  - MACD + Momentum confluence
  - Bullish/Bearish/Neutral status

### 📜 Dane Historyczne
- **Statystyki** - min, max, mean, std
- **RSI History** - wykres linijny
- **Recent Price Action** - ostatnie 20 barów w tabeli

### 📰 Market News
- **Live News Feed** z Yahoo Finance
- Ostatnie 5 newsów z linkami
- Publisher i timestamp

---

## Kluczowe Metryki (Top Panel)

1. **💰 Aktualna Cena** - z performance % od początku okresu
2. **📊 Momentum (10)** - Bullish/Bearish
3. **📉 RSI (14)** - Overbought/Oversold/Neutral
4. **📈 Volatility (AVG)** - średnia zmienność + ATH
5. **📦 Volume** - obecny vs średni (% zmiana)

---

## AI Insights - Co Pokazuje?

### Logika AI:
```
RSI > 70 + Momentum > 0 → ⚠️ DYWERGENCJA (pułapka na byki)
RSI < 30 → 💎 OKAZJA (akumulacja)
Performance > 20% → 📈 STRONG RALLY
MACD > 0 → 🟢 MOMENTUM BULLISH
MACD < 0 → 🔴 MOMENTUM BEARISH
Brak sygnałów → ⚖️ KONSOLIDACJA
```

---

## Integracja z Botem

### Synchronizacja Strategii

**Bot (Python):**
```python
# trading_bot/strategies/main_strategy.py
def detect_fvg(data):
    # Wykrywa Bull/Bear FVG
```

**Streamlit (Web):**
```python
# streamlit_terminal.py
if df['Low'].iloc[i] > df['High'].iloc[i-2]: # Bull FVG
```

**Korzyści:**
- Bot traduje automatycznie
- Streamlit wizualizuje decyzje bota
- Znajomi mogą śledzić live trading

---

## Deployment na Produkcję

### Streamlit Cloud (Darmowe Hosting)

1. Wrzuć kod na GitHub (repo publiczne)
2. Wejdź na: https://share.streamlit.io/
3. Połącz GitHub account
4. Deploy: wybierz `streamlit_terminal.py`
5. Gotowe! Dostajesz link: `https://your-app.streamlit.app`

**Limit darmowy:**
- 1 GB RAM
- Unlimited visitors
- Auto-updates z GitHub

### Ngrok (Tymczasowy Link)

```powershell
streamlit run streamlit_terminal.py --server.port 8501
ngrok http 8501
```

**Zalety:**
- Instant deployment (5 sekund)
- Darmowy public link
- Działa lokalnie

**Wady:**
- Link zmienia się po restart
- Wymaga działającego komputera

---

## Customizacja

### Zmiana Koloru Tematu

W pliku `streamlit_terminal.py` znajdź:
```python
st.markdown("""
    <style>
    .main { background-color: #0b0e11; }  # ← Zmień kolor tła
    </style>
""")
```

### Dodanie Nowego Wskaźnika

```python
# Dodaj po RSI:
df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)

# W metrykach:
col_m6.metric("ATR (14)", f"{df['ATR'].iloc[-1]:.2f}")
```

### Dodanie Alertów

```python
# Po obliczeniu sygnałów:
if current_rsi < 30:
    st.balloons()  # Animacja
    st.success("🚨 ALERT: Strong BUY signal!")
```

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'streamlit'"
**Rozwiązanie:**
```powershell
pip install streamlit pandas-ta plotly
```

### Problem: "Port 8501 already in use"
**Rozwiązanie:**
```powershell
streamlit run streamlit_terminal.py --server.port 8502
```

### Problem: Wykres nie ładuje się
**Rozwiązanie:**
- Sprawdź symbol (musi być z Yahoo Finance)
- Zmniejsz `history_days` (np. do 30)
- Sprawdź połączenie z internetem

### Problem: Brak newsów
**Rozwiązanie:**
- Niektóre symbole (np. crypto) mają mniej newsów
- Spróbuj AAPL, TSLA, SPY (zawsze mają newsy)

---

## Porównanie: Streamlit vs HTML Dashboard

| Feature | Streamlit | HTML Dashboard |
|---------|-----------|----------------|
| **Setup** | 1 linia kodu | Ręczne serwery |
| **Interaktywność** | Natywna | JavaScript required |
| **Deploy** | Streamlit Cloud | Ngrok/własny serwer |
| **Real-time** | Auto-refresh | Manual fetch |
| **Mobile** | Responsive | Custom CSS |
| **Sharing** | 1 link | Serwer + ngrok |

**Kiedy użyć Streamlit:**
- Chcesz szybko pokazać znajomym
- Potrzebujesz interakcji (zmiany symbolu, timeframe)
- Chcesz darmowy hosting (Streamlit Cloud)

**Kiedy użyć HTML Dashboard:**
- Bot ma być zawsze online
- Chcesz ultra customizację (CSS/JS)
- Potrzebujesz JSON API dla zewnętrznych apek

---

## Quick Commands

```powershell
# Uruchom lokalnie
streamlit run streamlit_terminal.py

# Uruchom + Ngrok (publiczny dostęp)
# Terminal 1:
streamlit run streamlit_terminal.py --server.port 8501
# Terminal 2:
ngrok http 8501

# Zatrzymaj
Ctrl+C

# Zainstaluj wszystkie wymagania
pip install streamlit pandas-ta plotly yfinance pandas numpy
```

---

**Gotowe!** 🚀 Masz profesjonalny terminal webowy w stylu Bloomberg!

Uruchom: `streamlit run streamlit_terminal.py` i korzystaj! 📊
