# 🚀 HAMSTER TERMINAL - Dashboard API Setup

## ✅ Real-Time Data Working!

Dashboard jest teraz połączony z **rzeczywistymi danymi** z:
- **Binance API** - BTC/ETH ceny, wolumen 24h, funding rate, open interest
- **Alternative.me** - Fear & Greed Index
- **CoinGecko** - Backup crypto data

---

## 📡 Status Ostatniej Aktualizacji

**API Server Status:** ✅ DZIAŁA
- BTC: **$95,481.12** (+0.27%)
- ETH: **$3,349.88** (+1.21%)
- Fear & Greed Index: **49** (Neutralny)
- Aktualizacja: co **30 sekund**

---

## 🛠️ Jak Uruchomić Dashboard z API (LOCALHOST)

### Krok 1: Zainstaluj wymagane pakiety
```powershell
pip install flask flask-cors requests
```

### Krok 2: Uruchom API Server (port 5000)
```powershell
cd C:\Users\sebas\Desktop\finalbot
python api_server.py
```

Zobaczysz:
```
🚀 HAMSTER TERMINAL API SERVER
Server starting on http://0.0.0.0:5000
Real-time data fetching from:
  • Binance API
  • CoinGecko API
  • Alternative.me Fear & Greed
✅ Binance: BTC $95,481.12 (+0.27%)
✅ Fear & Greed: 49
```

### Krok 3: Uruchom HTML Server (port 8000)
W **drugim terminalu**:
```powershell
cd C:\Users\sebas\Desktop\finalbot
python -m http.server 8000
```

### Krok 4: Otwórz Dashboard
Otwórz w przeglądarce:
```
http://localhost:8000/professional_dashboard_final.html
```

---

## 🌐 GitHub Pages (Produkcja)

Na **hamsterterminal.com** dashboard używa **symulowanych danych** (fallback), ponieważ nie ma backendu.

Jeśli chcesz mieć **rzeczywiste dane na produkcji**, musisz:
1. Hostować `api_server.py` na Heroku/Railway/Render
2. Zmienić `API_BASE` w HTML na URL Twojego serwera

---

## 📊 API Endpoints

| Endpoint | Opis | Przykład |
|----------|------|----------|
| `/api/binance/summary` | BTC/ETH ceny + wolumen | `{"btcPrice": 95481.12, "btcChange24h": 0.27}` |
| `/api/binance/funding` | Funding rate futures | `{"lastFundingRate": 0.0082}` |
| `/api/binance/oi` | Open Interest | `{"openInterest": 12400000000}` |
| `/api/fng` | Fear & Greed Index | `{"value": "49"}` |
| `/api/coingecko/simple` | Crypto data backup | `{"bitcoin": {"usd": 95481.12}}` |
| `/api/status` | Status serwera + cache | `{"ok": true, "cache": {...}}` |

---

## 🔥 Automatyczna Detekcja Środowiska

Dashboard **automatycznie wykrywa** czy działa na localhost czy produkcji:

- **Localhost:** `http://localhost:5000/api/*`
- **Produkcja (GitHub Pages):** fallback do symulowanych danych

Sprawdź w konsoli przeglądarki:
```
🔌 API Mode: LOCALHOST (port 5000)
📡 API Base URL: http://localhost:5000
✅ BTC price: $95481.12 | Change: +0.27%
```

---

## ⚙️ Troubleshooting

### Problem: API nie odpowiada
```powershell
# Sprawdź czy serwer działa
curl.exe http://127.0.0.1:5000/api/status
```

### Problem: CORS errors
- Flask-CORS jest zainstalowany i włączony w `api_server.py`
- Upewnij się że oba serwery działają (port 5000 + 8000)

### Problem: "Module not found"
```powershell
pip install flask flask-cors requests
```

---

## 🎯 Dane Aktualizują Się Na Żywo

- **API Server:** aktualizuje cache co **30 sekund**
- **Dashboard:** pobiera dane co **3 sekundy**
- **UI Refresh:** co **5 sekund**

Wszystkie dane są **rzeczywiste** i **na żywo**! 🚀

---

## 📝 TODO: Deployment na Produkcję

Aby mieć rzeczywiste dane na **hamsterterminal.com**:

1. Deploy `api_server.py` na Render/Railway/Heroku
2. Zmień `API_BASE` w HTML:
```javascript
const API_BASE = 'https://your-api-server.com';
```
3. Push do GitHub Pages

---

**Created:** 2026-01-18  
**Status:** ✅ Working Locally  
**API Version:** 1.0  
