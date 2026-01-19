# ⚡ Breaking News - Quick Start (3 Minuty)

> 🎯 Szybki setup Breaking News do Hamster Terminal

---

## 📦 Co masz

✅ `breaking_news_component.html` - Gotowy komponent
✅ Twelve Data API key (taki sam co do Bloomberg Ticker)
✅ Dashboard gotów do integracji

---

## 🚀 3 Proste Kroki

### Krok 1️⃣: Ustaw API Key (30 sekund)

Plik: `breaking_news_component.html`
Linia ~113:

```javascript
const TWELVE_DATA_KEY = 'TUTAJ_WKLEJ_TWOJ_KLUCZ';
```

**Czym jest key?**
- Ten sam co do Bloomberg Ticker
- Jedno API na oba komponenty
- Weź z Twelve Data dashboard

### Krok 2️⃣: Skopiuj do Dashboard (1 minuta)

Plik: `professional_dashboard_final.html`

Szukaj (Ctrl+F): `<!-- END OF BLOOMBERG TICKER`

Pod tym komentarzem dodaj całą zawartość z `breaking_news_component.html`:
- CSS (linie z `<style>`)
- HTML (linie z `<div class="breaking-news-container">`)
- JavaScript (linie z `<script>`)

### Krok 3️⃣: Refresh i Gotowe! (30 sekund)

1. Zapisz plik (Ctrl+S)
2. Otwórz dashboard w przeglądarce
3. Czekaj ~10 sekund
4. **Powinny pojawić się wiadomości!**

---

## ✨ To wszystko!

Teraz masz:
✅ **Bloomberg Ticker** - 11 symboli na żywo
✅ **Breaking News** - Wiadomości rynkowe
✅ **Oba pod Twelve Data API**

---

## 🎨 Co Widzisz?

```
🔴 BREAKING NEWS

🔴 HIGH [CRYPTO] Bloomberg Bitcoin Surges... 5m temu
🟠 MEDIUM [STOCKS] Reuters Apple Beats Q4... 10m temu  
🟡 LOW [MARKETS] Reuters S&P Reaches... 15m temu
🔴 HIGH [ECONOMY] FT Fed Signals Pause... 20m temu
```

**Kolory:**
- 🔴 HIGH = Krytyczne
- 🟠 MEDIUM = Ważne
- 🟡 LOW = Normalne

---

## ⚙️ Szybka Konfiguracja

### Zmiana Symboli

Linia ~95:
```javascript
const NEWS_SYMBOLS = {
    'CRYPTO': ['BTCUSD', 'ETHUSD'],     // Dodaj/usuń
    'STOCKS': ['AAPL', 'MSFT', 'GOOGL'], // Symbole akcji
    'MARKETS': ['SPX', 'INDU'],           // Indeksy
    'ECONOMY': ['fed', 'inflation']       // Słowa kluczowe
};
```

### Zmiana Częstości

Linia ~200:
```javascript
setInterval(buildBreakingNews, 120000);  // 120000 ms = 2 minuty
// Zmień na: 60000 = 1 min, 300000 = 5 min
```

### Zmiana Ilości Newsów

Linia ~125:
```javascript
fetch(`https://api.twelvedata.com/stocks/news?symbol=${symbol}&limit=5&apikey=...`)
// limit=5  → limit=10  (więcej newsów)
// limit=5  → limit=3   (mniej newsów)
```

---

## 🔥 Zaawansowane (Opcjonalne)

### Dodaj Polskie Słowa

Linia ~117:
```javascript
const POLISH_TRANSLATIONS = {
    'Bitcoin': 'Bitcoin',
    'Surge': 'Gwałtowny wzrost',  // ← Dodaj tutaj
    'Your Term': 'Twoje słowo',
};
```

### Zmień Kolory

CSS (~161-188):
```css
.category-crypto {
    background: rgba(255, 215, 0, 0.2);  /* Tło - zmieniaj RGB */
    color: #ffd700;                      /* Kolor tekstu */
}
```

### Zmień Prędkość Scroll

CSS (~35):
```css
animation: newsScroll 60s linear infinite;
/* 30s = szybko, 60s = normalnie, 120s = wolno */
```

---

## 🆘 Coś Nie Działa?

### Wiadomości się nie ładują?
1. F12 → Console
2. Sprawdź czy jest API key
3. Sprawdź czy API key jest poprawny

### Wiadomości się nie przewijają?
1. Poczekaj - mogą być only 1-2 newsy
2. Zwiększ `limit` na 10 zamiast 5
3. Hard refresh: Ctrl+Shift+R

### Wiadomości powtarzają się?
1. To normalne - Twelve Data ma ograniczone newsy
2. Czekaj 2 minuty na refresh
3. Zmień `NEWS_SYMBOLS` na inne symbole

---

## 📊 Czego Oczekiwać

| Element | Czas | Działanie |
|---------|------|----------|
| Komponent się ładuje | ~1s | "Ładowanie wiadomości..." |
| API Request | ~2-5s | Pobiera newsy |
| Wiadomości pojawią się | ~5-10s | Rzeczywiste dane |
| Scroll animacja | ~60s | Ciągłe przewijanie |
| Refresh wiadomości | ~2 min | Nowe newsy pojawią się |

---

## 🎯 Best Practices

✅ **API key:** Taki sam co Bloomberg Ticker
✅ **Integracja:** Umieść pod tickerem (nie wewnątrz)
✅ **Czestość:** Co 2-5 minut (nie co 30 sekund)
✅ **Symbole:** Zacznij z domyślnymi, potem customize
✅ **Test:** Najpierw offline (mock data), potem live

---

## 📞 Pomoc

**Potrzebujesz więcej info?**
- Pełne info: `BREAKING_NEWS_GUIDE.md`
- Integracja: `BREAKING_NEWS_INTEGRATION.md`
- API docs: https://twelvedata.com/docs

---

**🎉 Gotowe!**

Twój Hamster Terminal ma teraz:
- Bloomberg Ticker (real-time)
- Breaking News (live updates)
- Polskie wsparcie (interfejs + tłumaczenia)
- Profesjonalny wygląd

Udanego tradingu! 🚀
