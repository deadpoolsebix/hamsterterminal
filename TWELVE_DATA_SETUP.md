# 🚀 Twelve Data Integration - Setup Guide

## Co to jest Twelve Data?

**Twelve Data** to unified API dla:
- ✅ **Crypto** - BTC, ETH, wszystkie altcoiny
- ✅ **Stock** - AAPL, MSFT, NVDA, SPY, etc.
- ✅ **Forex** - EUR/USD, GBP/USD, etc.
- ✅ **Real-time quotes** - WebSocket support
- ✅ **Historical data** - OHLC candles

---

## 📋 Setup (3 kroki)

### Krok 1: Rejestracja na Twelve Data

1. Idź na https://twelvedata.com
2. Kliknij **"Sign Up"**
3. Potwierdź email
4. Zaloguj się do dashboard

### Krok 2: Pobierz API Key

1. W dashboard, wejdź do **Settings → API Keys**
2. Skopiuj **API Key** (zaczyna się `demo_...`)
3. Darmowy tier: **800 calls/minute** (wystarczający!)

### Krok 3: Ustaw w systemie

**Windows PowerShell:**
```powershell
$env:TWELVE_DATA_API_KEY='twm_xxxxxxxxxxxxxxx'
```

**Windows CMD:**
```cmd
set TWELVE_DATA_API_KEY=twm_xxxxxxxxxxxxxxx
```

**Linux/Mac Bash:**
```bash
export TWELVE_DATA_API_KEY='twm_xxxxxxxxxxxxxxx'
```

**Permanent (Windows):**
- System Settings → Environment Variables → New
- Variable name: `TWELVE_DATA_API_KEY`
- Value: Twój API key

---

## 🎯 Testowanie

### Zainstaluj pakiety:
```powershell
pip install -r requirements.txt
```

### Uruchom API Server:
```powershell
cd C:\Users\sebas\Desktop\finalbot
python api_server.py
```

### Sprawdź status:
```bash
curl http://localhost:5000/api/status
```

Powinno pokazać:
```json
{
  "ok": true,
  "data_source": "Twelve Data (crypto, stocks, forex)",
  "cache": {
    "btcPrice": 95500.00,
    "spyPrice": 470.50,
    "eurusd": 1.0850
  }
}
```

---

## 📊 Dostępne API Endpoints

### Crypto
```
GET /api/binance/summary
{
  "btcPrice": 95500.00,
  "btcChange24h": 2.45,
  "ethPrice": 2845.00,
  "ethChange24h": 1.80
}
```

### Stocks
```
GET /api/stocks
{
  "spy": {"price": 470.50, "change": 0.8},
  "aapl": {"price": 235.50, "change": 0.5},
  "msft": {"price": 425.75, "change": 0.3},
  "nvda": {"price": 145.20, "change": 1.2}
}
```

### Forex
```
GET /api/forex
{
  "eurusd": {"price": 1.0850, "change": 0.2},
  "gbpusd": {"price": 1.2650, "change": -0.1}
}
```

### Markets
```
GET /api/markets
{
  "gold": {"price": 2650.00, "change": 0.5},
  "spy": {"price": 470.50, "change": 0.8},
  "dxy": {"price": 103.50, "change": -0.2}
}
```

### Fear & Greed
```
GET /api/fng
{
  "value": 62,
  "value_classification": "Greed"
}
```

---

## 💰 Pricing Plans

| Tier | Price | Calls/Min | Features |
|------|-------|-----------|----------|
| **Free** | $0 | 800 | Quotes, OHLC |
| **Starter** | $29/mo | 3,000 | + Historical data |
| **Professional** | $99/mo | 10,000 | + Options, Technicals |
| **Professional+** | $499/mo | 50,000 | + Priority |

**Rekomendacja:** Zacznij na Free tier (wystarczający dla Twojego dashboarda)

---

## 🔧 Limity i Rate Limiting

- **Free tier:** 800 API calls/minute
- **Reset:** co minutę
- **Timeout:** Jeśli przekroczysz, zaczekaj minutę
- **Batch requests:** Maksymalnie 3-5 na raz

Nasz system:
- 📊 Pobiera 4 crypto (BTC, ETH) = 2 calls
- 📈 Pobiera 4 stock (SPY, AAPL, MSFT, NVDA) = 4 calls
- 💱 Pobiera 2 forex (EUR/USD, GBP/USD) = 2 calls
- 💛 Pobiera 2 commodities (GOLD, DXY) = 2 calls
- **Total: ~10 calls per update (co 30 sec = 1,200/hour = OK!)**

---

## ❌ Troubleshooting

### "API key not found" error
```
⚠️  USING DEMO KEY - LIMITED TO 800 CALLS/MIN
```
**Fix:** Ustaw `TWELVE_DATA_API_KEY` environment variable

### "Rate limit exceeded"
```
❌ Twelve Data crypto error: Too many requests
```
**Fix:** Czekaj minutę, system będzie czekać before retry

### "Invalid symbol"
```
❌ Twelve Data stock error: Unknown symbol
```
**Fix:** Sprawdź czy symbol istnieje na Twelve Data

---

## 🎓 Wskazówki

### 1. WebSocket (dla produkcji)
```python
# Zamiast co 30 sekund robić REST calls,
# można używać WebSocket dla real-time pushes
# TODO: Implementacja w przyszłości
```

### 2. Dodaj nowe aktywa
W `api_server.py`, dodaj w funkcji `fetch_stock_prices()`:
```python
('TSLA', 'tsla_price', 'tsla_change'),  # Tesla
('AMD', 'amd_price', 'amd_change'),     # AMD
```

### 3. Monitoruj usage
```bash
curl https://api.twelvedata.com/usage
```

---

## 📚 Dokumentacja Twelve Data

- **API Docs:** https://twelvedata.com/docs
- **Supported Symbols:** https://twelvedata.com/symbols
- **Changelog:** https://twelvedata.com/changelog
- **Status:** https://status.twelvedata.com

---

## ✅ Następny krok

Serwer jest gotowy! Uruchom:
```powershell
python api_server.py
```

Otwórz dashboard w przeglądarce:
```
http://localhost:8000/professional_dashboard_final.html
```

Powinny być rzeczywiste ceny z Twelve Data! 🚀
