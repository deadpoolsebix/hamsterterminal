# 📡 ŹRÓDŁA DANYCH API - PROFESSIONAL TRADING TERMINAL

## Przegląd systemu real-time data

Dashboard automatycznie pobiera dane z następujących źródeł:

---

## 🔥 GŁÓWNE API (Aktywne)

### 1. **Binance API** (Podstawowe źródło crypto)
- **URL**: `https://api.binance.com/api/v3`
- **Typ**: REST API (publiczne, bez klucza)
- **Dane**: 
  - BTC/USDT cena spot (real-time)
  - ETH/USDT cena spot
  - Zmiana 24h (%)
  - Volume 24h (USDT)
  - High/Low 24h
- **Odświeżanie**: Co 5 sekund
- **Limit**: 1200 requestów/minutę (wystarczające)
- **Dokumentacja**: https://binance-docs.github.io/apidocs/spot/en/

**Endpointy używane:**
```
GET /api/v3/ticker/24hr?symbol=BTCUSDT
GET /api/v3/ticker/price?symbol=BTCUSDT
GET /api/v3/ticker/24hr?symbol=ETHUSDT
GET /api/v3/ticker/price?symbol=ETHUSDT
```

---

### 2. **Binance Futures API** (Funding Rate & Open Interest)
- **URL**: `https://fapi.binance.com/fapi/v1`
- **Typ**: REST API (publiczne)
- **Dane**:
  - Funding Rate (stopa finansowania perpetual contracts)
  - Open Interest (otwarte pozycje)
  - Premium Index
- **Odświeżanie**: Co 5 sekund
- **Dokumentacja**: https://binance-docs.github.io/apidocs/futures/en/

**Endpointy używane:**
```
GET /fapi/v1/premiumIndex?symbol=BTCUSDT
GET /fapi/v1/openInterest?symbol=BTCUSDT
```

---

### 3. **Alternative.me API** (Fear & Greed Index)
- **URL**: `https://api.alternative.me/fng/`
- **Typ**: REST API (publiczne, darmowe)
- **Dane**:
  - Crypto Fear & Greed Index (0-100)
  - Klasyfikacja: Extreme Fear, Fear, Neutral, Greed, Extreme Greed
- **Odświeżanie**: Co 5 sekund (cache na serwerze: 10 min)
- **Limit**: Brak oficjalnego limitu
- **Dokumentacja**: https://alternative.me/crypto/fear-and-greed-index/

**Endpoint:**
```
GET /?limit=1
```

---

## 📊 DODATKOWE ŹRÓDŁA (Opcjonalne)

### 4. **CoinGecko API** (Backup crypto data)
- **URL**: `https://api.coingecko.com/api/v3`
- **Typ**: REST API (darmowy tier: 10-50 calls/min)
- **Dane**:
  - Market cap
  - Total volume
  - Dominance BTC
  - Top coins ranking
- **Status**: Backup source (nie używane domyślnie)
- **Dokumentacja**: https://www.coingecko.com/en/api/documentation

---

### 5. **CryptoWatch API** (Zaawansowane dane)
- **URL**: `https://api.cryptowat.ch`
- **Typ**: REST API (wymaga API key dla >8M credits/miesiąc)
- **Dane**:
  - Order book depth
  - Recent trades
  - OHLC candles
- **Status**: Opcjonalne rozszerzenie
- **Dokumentacja**: https://docs.cryptowat.ch/rest-api/

---

## ⚙️ KONFIGURACJA

### Częstotliwość odświeżania:
```javascript
// Główna pętla aktualizacji danych
setInterval(updateAllMarketData, 5000); // Co 5 sekund

// Szybka aktualizacja UI (smooth transitions)
setInterval(updateDashboardUI, 1000); // Co 1 sekundę
```

### Retry logic:
```javascript
// Automatyczne retry przy błędach
try {
    await fetchBinanceData();
} catch (error) {
    console.error('API error - retrying...');
    // Fallback do cache/mock data
}
```

---

## 🔒 BEZPIECZEŃSTWO & LIMITY

| Źródło | Limit | CORS | API Key Required |
|--------|-------|------|------------------|
| Binance Spot | 1200/min | ✅ Allowed | ❌ No |
| Binance Futures | 2400/min | ✅ Allowed | ❌ No |
| Alternative.me | Unlimited | ✅ Allowed | ❌ No |
| CoinGecko | 10-50/min | ✅ Allowed | ❌ No (free tier) |
| CryptoWatch | 8M credits/mo | ✅ Allowed | ⚠️ Yes (paid) |

**Wszystkie API działają bez CORS proxy i bez kluczy API w trybie publicznym!**

---

## 📈 JAKOŚĆ DANYCH

### Opóźnienia:
- **Binance**: <100ms (najbardziej dokładne)
- **Fear & Greed**: Cache 10 min (aktualizacja co 8h)
- **Funding Rate**: Real-time (zmiana co 8h)

### Dokładność:
- ✅ **Binance**: 99.9% uptime, sub-second latency
- ✅ **Alternative.me**: Zaufane źródło (CNN, Bloomberg używają)
- ⚠️ **CoinGecko**: 5-minute delay na darmowym tierze

---

## 🚀 PRZYSZŁE ROZSZERZENIA

### Plan na przyszłość:
1. **WebSocket** zamiast REST dla realtime tickera
2. **TradingView datafeed** dla zaawansowanych wykresów
3. **Twitter API** dla social sentiment analysis
4. **Glassnode API** dla on-chain metrics
5. **DeFi Pulse API** dla TVL metrics

---

## 🛠️ DEBUGGING

### Console commands:
```javascript
// Sprawdź aktualne dane
console.log(window.marketData);

// Wymuś update
window.updateAllMarketData();

// Sprawdź ostatnią aktualizację
console.log(marketData.lastUpdate);
```

### Testy API:
```bash
# Test Binance ticker
curl "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"

# Test Fear & Greed
curl "https://api.alternative.me/fng/?limit=1"

# Test Funding Rate
curl "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT"
```

---

## 📞 KONTAKT & WSPARCIE

**Binance Support**: https://www.binance.com/en/support  
**CoinGecko Support**: https://www.coingecko.com/en/api  
**Alternative.me**: https://alternative.me/about/

---

**Ostatnia aktualizacja**: 17 stycznia 2026  
**Wersja dokumentacji**: 1.0  
**Status wszystkich API**: ✅ Operational
