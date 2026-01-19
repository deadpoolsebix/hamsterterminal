# 🔴 Breaking News System - Dokumentacja

## Przegląd

Breaking News to **profesjonalny system wiadomości rynkowych** na żywo dla Hamster Terminal, który:

✅ **Pobiera wiadomości** z Twelve Data News API
✅ **Wyświetla w polskim** interfejsie z angielskimi nagłówkami
✅ **Kategoryzuje wiadomości** (CRYPTO, STOCKS, MARKETS, ECONOMY)
✅ **Wskazuje ważność** (HIGH, MEDIUM, LOW) z kolorami
✅ **Przewija się** smoothly pod tickerem Bloomberg
✅ **Aktualizuje się** co 2 minuty
✅ **Pause na hover** - można przeczytać spokojnie

---

## 🎯 Wyświetlanie

```
┌─────────────────────────────────────────────────────────────┐
│ 🔴 BREAKING NEWS                                           │
│                                                             │
│ 🔴 HIGH [CRYPTO] Bloomberg Bitcoin Surges... 5m temu       │
│ 🟠 MEDIUM [STOCKS] Reuters Apple Beats Q4... 10m temu      │
│ 🟡 LOW [MARKETS] Reuters S&P Reaches... 15m temu           │
│ 🔴 HIGH [ECONOMY] FT Fed Signals Pause... 20m temu        │
└─────────────────────────────────────────────────────────────┘
```

**Kolory ważności:**
- 🔴 **HIGH (Wysoka)** - Krytyczne: crash, surge, record, emergency
- 🟠 **MEDIUM (Średnia)** - Ważne: rally, decline, forecast, warns
- 🟡 **LOW (Niska)** - Zwyczajne: pozostałe wiadomości

**Kategorie:**
- 🟡 **CRYPTO** - Bitcoin, Ethereum, kryptowaluty
- 🟢 **STOCKS** - Akcje, spółki, corporate news
- 🔵 **MARKETS** - Indeksy, forex, rynki globalne
- 🟣 **ECONOMY** - Fed, inflacja, stopa procentowa

---

## ⚡ Szybki Start (3 Kroki)

### Krok 1: Potwierdź API Key
W `breaking_news_component.html` linia 113:
```javascript
const TWELVE_DATA_KEY = 'YOUR_API_KEY_HERE';
```

Jeśli masz już klucz z Bloomberg Ticker - wstaw tam sam 👆

### Krok 2: Scal komponent
1. Otwórz `professional_dashboard_final.html`
2. Znajdź Bloomberg Ticker (linia ~1318)
3. **Pod** tickerem (po `</div>`) dodaj zawartość z `breaking_news_component.html`

### Krok 3: Test
1. Otwórz dashboard w przeglądarce
2. Poczekaj na wiadomości (max 30 sekund)
3. Wiadomości będą się przewijać powoli

**Done!** 🎉

---

## 📱 Interfejs

### Struktura Wiadomości

```
[🔴 HIGH] [CRYPTO] Bloomberg Bitcoin Surges Past $95k on Fed Hints 5m temu
└─────┬────┘└──┬──┘└──┬────┘│
   Ważność  Kategoria Źródło  └─→ Czasaka względny
```

### Kolory i Ikony

| Element | Znaczenie | Kolor |
|---------|-----------|-------|
| 🔴 HIGH | Bardzo ważne | Czerwony #ff0033 |
| 🟠 MEDIUM | Ważne | Pomarańczowy #ffaa00 |
| 🟡 LOW | Normalne | Zielony #00ff41 |
| [CRYPTO] | Bitcoin/Ethereum | Złoty #ffd700 |
| [STOCKS] | Akcje | Zielony #00ff41 |
| [MARKETS] | Indeksy | Niebieski #00d4ff |
| [ECONOMY] | Gospodarka | Purpura #8a2be2 |

---

## 🔧 Konfiguracja

### Zmiana symboli

W `breaking_news_component.html` (~linia 95):

```javascript
const NEWS_SYMBOLS = {
    'CRYPTO': ['BTCUSD', 'ETHUSD', 'SOLUSD', 'crypto'],
    'STOCKS': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA'],
    'MARKETS': ['SPX', 'INDU', 'IXIC', 'EUR/USD'],
    'ECONOMY': ['economy', 'fed', 'inflation', 'interest']
};
```

Dodaj/usuń symbole wg potrzeb.

### Zmiana częstości aktualizacji

Linia ~200:
```javascript
setInterval(buildBreakingNews, 120000);  // Zmień 120000 ms = 2 minuty
```

- `60000` = 1 minuta (często)
- `120000` = 2 minuty (domyślnie)
- `300000` = 5 minut (rzadko)

### Zmiana ilości wiadomości

Linia ~125 - zmień `limit=5`:
```javascript
fetch(`https://api.twelvedata.com/stocks/news?symbol=${symbol}&limit=10&apikey=${TWELVE_DATA_KEY}`)
```

- `limit=5` = 5 wiadomości na symbol
- `limit=10` = 10 wiadomości na symbol
- `limit=20` = 20 wiadomości na symbol

---

## 🌍 Język Polski

### Tłumaczenie Nagłówków

Komponent ma wbudowany słownik (`POLISH_TRANSLATIONS`) który tłumaczy:

```javascript
const POLISH_TRANSLATIONS = {
    'Bitcoin': 'Bitcoin',
    'Ethereum': 'Ethereum',
    'Surge': 'Gwałtowny wzrost',
    'Crash': 'Gwałtowny spadek',
    'Fed': 'Fed',
    'Inflation': 'Inflacja',
    // ... itd
};
```

### Dodaj Swoje Tłumaczenia

Rozszerz słownik (linia ~117):

```javascript
const POLISH_TRANSLATIONS = {
    // Istniejące...
    'Your English Term': 'Twój polski termin',
    'Another Term': 'Inne słowo',
};
```

### Tekst UI po Polsku

- 🔴 BREAKING NEWS - nagłówek
- m temu, h temu, d temu - "minut temu", "godzin temu", "dni temu"
- HIGH, MEDIUM, LOW - można zmienić na: WYSOKA, ŚREDNIA, NISKA

---

## 📡 API Integration

### Twelve Data News API

```
GET https://api.twelvedata.com/stocks/news
?symbol=BTCUSD
&limit=5
&apikey=YOUR_KEY
```

**Parametry:**
- `symbol` - Symbol akcji/kryptowaluty
- `limit` - Ile wiadomości (1-20)
- `apikey` - Twój klucz

**Odpowiedź:**
```json
{
  "data": [
    {
      "title": "Bitcoin Surges...",
      "description": "Market rallies...",
      "source": "Bloomberg",
      "published_date": "2026-01-19T10:30:00",
      "symbol": "BTCUSD"
    }
  ]
}
```

### Plan: Batch Request (przyszłość)

Aktualnie: Pobiera 5 symboli × 5 wiadomości = 25 wiadomości
```
GET /news?symbol=BTCUSD &limit=5  (1 request)
GET /news?symbol=ETHUSD &limit=5  (1 request)
GET /news?symbol=AAPL   &limit=5  (1 request)
... (5 requests total)
```

Można ulepszyć do single batch call.

---

## 🎨 Personalizacja

### Zmiana Kolorów Kategorii

W CSS (linia ~161-188):

```css
.category-crypto {
    background: rgba(255, 215, 0, 0.2);  /* Tło */
    color: #ffd700;                      /* Tekst */
    border: 1px solid #ffd700;           /* Ramka */
}
```

### Zmiana Prędkości Przewijania

W CSS (linia ~35):
```css
animation: newsScroll 60s linear infinite;
```

- `30s` = szybko
- `60s` = normalnie (domyślnie)
- `120s` = wolno

### Zmiana Rozmiaru Czcionki

W CSS (linia ~53):
```css
.breaking-news-scroll {
    font-size: 0.9em;  /* Zmień na 0.8em lub 1em */
}
```

---

## 🔍 Troubleshooting

### Problem: "Loading breaking news..." się nie zmienia

**Przyczynę:**
- API key nie skonfigurowany
- Brak internetu
- Twelve Data service down

**Rozwiązanie:**
1. Otwórz konsola (F12)
2. Sprawdź console tab na błędy
3. Potwierdź API key w kodzie
4. Sprawdź status Twelve Data: status.twelvedata.com

### Problem: Wiadomości się nie przewijają

**Przyczynę:**
- CSS animacja disabled
- Mało wiadomości

**Rozwiązanie:**
1. Sprawdź CSS - `animation: newsScroll` powinna być tam
2. Zwiększ `limit` w API call (np. na 20)
3. Hard refresh: Ctrl+Shift+R

### Problem: Wiadomości nie po polsku

**Przyczynę:**
- Słownik POLISH_TRANSLATIONS niekompletny
- Typo w tłumaczeniach

**Rozwiązanie:**
1. Dodaj brakujące terminy do słownika
2. Sprawdź pisownię (case-sensitive!)
3. Pamiętaj: `.title` zaciąga angielskie nagłówki z API

---

## ✨ Zaawansowane

### Filtrowanie po Ważności

Modyfikuj `getImportanceLevel()` (linia ~140):

```javascript
function getImportanceLevel(headline) {
    const highImportanceKeywords = [
        'crash', 'surge', 'record', 'historic', 'emergency', 'halt', 'alert',
        'TWOJA_FRAZA'  // Dodaj tutaj
    ];
    // ...
}
```

### Filtrowanie po Kategorii

Modyfikuj `categorizeNews()` (linia ~155):

```javascript
function categorizeNews(headline) {
    const lowerHeadline = headline.toLowerCase();
    
    if (lowerHeadline.includes('twoja_fraza')) {
        return 'TWOJA_KATEGORIA';
    }
    // ...
}
```

### Emoji i Ikony

Zmień emojis w HTML (linia ~109):
```javascript
const importanceIcon = importance === 'high' ? '🔴' : '...';
```

---

## 📊 Statystyki API

### Zużycie Credits

| Scenariusz | Requests/Dzień | Credits/Dzień |
|-----------|-----------------|---------------|
| 5 symboli × 5 wiadomości | 5 | 5 |
| Co 2 minuty | ~720 | ~720 |
| Co 1 godzinę | ~24 | ~24 |
| Co 4 godziny | ~6 | ~6 |

**Free Tier:** 800 calls/minute = wystarczy dla co 2-minutowych updates

---

## 🚀 Następne Kroki

### Phase 1: Integracja (Teraz)
- [ ] Skopiuj komponent
- [ ] Ustaw API key
- [ ] Scal z dashboard
- [ ] Przetestuj

### Phase 2: Personalizacja (Dziś)
- [ ] Dostosuj symbole
- [ ] Dodaj swoje słowa kluczowe
- [ ] Zmień kolorystykę
- [ ] Dostosuj prędkość

### Phase 3: Zaawansowanie (Przyszłość)
- [ ] Filtry wiadomości (tylko HIGH importance)
- [ ] Powiadomienia audio na HIGH importance
- [ ] Archiwum wiadomości
- [ ] Integracja z trading signalami

---

## 📚 Referencja

### Słowa Kluczowe Ważności

**HIGH (Wysoka):**
crash, surge, record, historic, emergency, halt, alert, massive, collapse, explode, breakthrough

**MEDIUM (Średnia):**
rally, decline, forecast, warns, announces, expects, reports, signals, indicates, plans

**LOW (Niska):**
Wszystko inne

### Symbole Twelve Data

**Kryptowaluty:**
- BTCUSD, ETHUSD, SOLUSD, XRPUSD, ADAUSD

**Akcje (top):**
- AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, JPM

**Indeksy:**
- SPX (S&P 500), INDU (Dow), IXIC (Nasdaq), GDAXI (DAX)

---

## 🎯 Best Practices

✅ **Ustaw rozumną częstość:** Co 2-5 minut (nie co 30 sekund)
✅ **Monitoruj API credits:** Nie zbyt wiele requestów
✅ **Testeruj offline:** Fallback na mock data działa
✅ **Czytaj hovering:** Pause pozwala przeczytać
✅ **Dodaj własne słowa:** Rozszerz słownik dla swojej niszy

---

## 🔐 Security

✅ API key w komponencie (bezpieczne - frontend)
✅ Brak data storage
✅ Brak user tracking
✅ Publiczne dane rynkowe
✅ CORS-friendly

---

## 📞 Pomoc

**Pytania o setup?**
→ Przeczytaj "Quick Start" powyżej

**Pytania o API?**
→ https://twelvedata.com/docs

**Błędy w konsoli?**
→ Otwórz F12 → Console → sprawdź komunikaty

---

**Status:** ✅ Production Ready
**Version:** 1.0 Breaking News Ticker
**Date:** January 19, 2026
