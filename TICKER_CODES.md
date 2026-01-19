# BLOOMBERG TICKER + BREAKING NEWS - KOMPLETNE KODY

## 1. HTML (wstaw w <body>)
```html
<!-- ===== BLOOMBERG TICKER ===== -->
<div class="bloomberg-ticker-wrapper" id="bloombergTicker">
    <div class="ticker-loading">Ladowanie Bloomberg Ticker...</div>
</div>

<!-- ===== BREAKING NEWS ===== -->
<div class="breaking-news-wrapper" id="breakingNewsWrapper">
    <span class="breaking-news-label">BREAKING NEWS</span>
    <div class="news-loading">Ladowanie wiadomosci...</div>
</div>
```

## 2. CSS (wstaw w <style>)
```css
/* ===== BLOOMBERG TICKER STYLES ===== */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');

.bloomberg-ticker-wrapper {
    background: linear-gradient(135deg, #0a0a0a 0%, #0f0f0f 100%);
    border: 2px solid #00d4ff;
    border-radius: 8px;
    overflow: hidden;
    padding: 8px 0;
    margin-bottom: 15px;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3), inset 0 0 10px rgba(0, 0, 0, 0.8);
}

.bloomberg-ticker-scroll {
    display: flex;
    animation: scroll-left 75s linear infinite;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 0.85em;
    letter-spacing: 0.5px;
}

@keyframes scroll-left {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}

.bloomberg-ticker-group {
    display: flex;
    align-items: center;
    margin: 0 30px;
    white-space: nowrap;
    gap: 15px;
}

.ticker-group-label {
    color: #ffaa00;
    font-weight: 700;
    font-size: 0.95em;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-right: 10px;
    text-shadow: 0 0 10px rgba(255, 170, 0, 0.5);
}

.ticker-instrument-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 10px;
    border: 1px solid;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.3);
}

.ticker-symbol {
    font-weight: 700;
    font-size: 0.9em;
    text-transform: uppercase;
}

.ticker-price {
    color: #ffff00;
    font-weight: 900;
    font-family: 'JetBrains Mono', monospace;
    text-shadow: 0 0 8px rgba(255, 255, 0, 0.5);
}

.ticker-change {
    font-weight: 700;
    font-size: 0.85em;
    min-width: 55px;
    text-align: right;
}

.ticker-change.positive {
    color: #00ff41;
    text-shadow: 0 0 8px rgba(0, 255, 65, 0.5);
}

.ticker-change.negative {
    color: #ff0033;
    text-shadow: 0 0 8px rgba(255, 0, 51, 0.5);
}

/* ===== BREAKING NEWS STYLES ===== */
.breaking-news-wrapper {
    background: linear-gradient(135deg, #1a0a0a 0%, #0f0f0f 100%);
    border: 2px solid #ff0033;
    border-radius: 8px;
    overflow: hidden;
    padding: 8px 0;
    margin-bottom: 15px;
    box-shadow: 0 0 20px rgba(255, 0, 51, 0.3), inset 0 0 10px rgba(0, 0, 0, 0.8);
}

.breaking-news-label {
    display: inline-block;
    padding: 6px 12px;
    background: #ff0033;
    color: #fff;
    font-weight: 900;
    font-size: 0.75em;
    letter-spacing: 1.5px;
    margin: 0 10px;
    border-radius: 4px;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
    text-shadow: 0 0 10px rgba(255, 0, 51, 0.8);
    animation: pulse-label 1.5s ease-in-out infinite;
}

@keyframes pulse-label {
    0%, 100% { transform: scale(1); box-shadow: 0 0 10px rgba(255, 0, 51, 0.8); }
    50% { transform: scale(1.05); box-shadow: 0 0 20px rgba(255, 0, 51, 1); }
}

.breaking-news-scroll {
    display: flex;
    animation: scroll-left 95s linear infinite;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 0.8em;
    padding: 0 10px;
}

.breaking-news-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 15px;
    margin: 0 10px;
    white-space: nowrap;
    border-left: 3px solid #ffaa00;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    flex-shrink: 0;
}

.news-importance {
    font-weight: 900;
    font-size: 0.75em;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 2px 6px;
    border-radius: 3px;
    min-width: 45px;
}

.news-importance.high {
    background: #ff0033;
    color: #fff;
    text-shadow: 0 0 8px rgba(255, 0, 51, 0.8);
}

.news-importance.medium {
    background: #ffaa00;
    color: #000;
    text-shadow: 0 0 5px rgba(255, 170, 0, 0.8);
}

.news-importance.low {
    background: #00ff41;
    color: #000;
    text-shadow: 0 0 5px rgba(0, 255, 65, 0.8);
}

.news-category-tag {
    font-weight: 700;
    font-size: 0.7em;
    text-transform: uppercase;
    padding: 2px 6px;
    border-radius: 3px;
    letter-spacing: 0.5px;
}

.news-category-tag.category-crypto {
    background: rgba(139, 69, 255, 0.3);
    color: #b091ff;
}

.news-category-tag.category-stocks {
    background: rgba(0, 255, 100, 0.3);
    color: #00ff41;
}

.news-category-tag.category-markets {
    background: rgba(0, 212, 255, 0.3);
    color: #00d4ff;
}

.news-category-tag.category-economy {
    background: rgba(255, 170, 0, 0.3);
    color: #ffaa00;
}

.news-source {
    font-weight: 700;
    color: #00d4ff;
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.news-headline {
    color: #fff;
    font-weight: 600;
    flex: 1;
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.news-time {
    color: #888;
    font-size: 0.75em;
    font-weight: 600;
    min-width: 60px;
    text-align: right;
}

.ticker-loading,
.news-loading {
    color: #999;
    font-size: 0.85em;
    padding: 12px;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
}
```

## 3. JAVASCRIPT (wstaw w <script> bloku)
```javascript
/* ===== BLOOMBERG TICKER & BREAKING NEWS SCRIPTS ===== */
<script>
    const TWELVE_DATA_KEY = '5203977ec0204755904ef326abe77e7c';
    const TICKER_CONFIG = {
        'METALE': { symbols: ['XAU/USD', 'XAG/USD'], color: '#ffff00' },
        'INDEKSY': { symbols: ['SPX', 'INDU', 'IXIC', 'GDAXI'], color: '#00d4ff' },
        'MEGA CAPS': { symbols: ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'TSLA'], color: '#cccccc' }
    };
    
    async function fetchTickerData() {
        try {
            const allSymbols = Object.values(TICKER_CONFIG).flatMap(g => g.symbols).join(',');
            const url = `https://api.twelvedata.com/quote?symbol=${allSymbols}&apikey=${TWELVE_DATA_KEY}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error('API error');
            const data = await response.json();
            
            let items = [];
            if (Array.isArray(data?.results)) {
                items = data.results;
            } else if (data && typeof data === 'object') {
                items = Object.values(data).filter(v => v && typeof v === 'object' && v.symbol && v.price);
            }
            
            if (!items || items.length === 0) {
                throw new Error('Empty ticker payload');
            }
            return items;
        } catch (error) {
            console.error('Ticker error, using mock:', error);
            return getMockTickerData();
        }
    }
    
    function getMockTickerData() {
        return [
            { symbol: 'XAU/USD', price: '2645.30', percent_change: '0.45' },
            { symbol: 'XAG/USD', price: '31.25', percent_change: '0.32' },
            { symbol: 'SPX', price: '5847.50', percent_change: '1.42' },
            { symbol: 'INDU', price: '42850.20', percent_change: '0.87' },
            { symbol: 'IXIC', price: '18542.30', percent_change: '1.93' },
            { symbol: 'GDAXI', price: '18234.10', percent_change: '-0.62' },
            { symbol: 'AAPL', price: '234.56', percent_change: '2.18' },
            { symbol: 'MSFT', price: '445.32', percent_change: '1.87' },
            { symbol: 'NVDA', price: '892.15', percent_change: '3.24' },
            { symbol: 'AMZN', price: '456.78', percent_change: '-1.45' },
            { symbol: 'TSLA', price: '347.85', percent_change: '4.32' }
        ];
    }
    
    async function buildBloombergTicker() {
        const priceData = await fetchTickerData();
        const priceMap = new Map(priceData.map(item => [item.symbol, item]));
        let html = '<div class="bloomberg-ticker-scroll">';
        
        for (let loop = 0; loop < 2; loop++) {
            if (loop === 1) html += '<div style="width: 100px;"></div>';
            
            for (const [groupName, cfg] of Object.entries(TICKER_CONFIG)) {
                html += '<div class="bloomberg-ticker-group"><span class="ticker-group-label">' + groupName + '</span>';
                
                for (const symbol of cfg.symbols) {
                    const data = priceMap.get(symbol);
                    if (!data) continue;
                    
                    const price = parseFloat(data.price).toFixed(2);
                    const change = parseFloat(data.percent_change);
                    const col = change >= 0 ? '#00ff41' : '#ff0033';
                    const sign = change >= 0 ? '+' : '';
                    
                    html += `<div class="ticker-instrument-item" style="border-color: ${cfg.color}33;">
                        <span class="ticker-symbol" style="color: ${cfg.color};">${symbol}</span>
                        <span class="ticker-price">$${price}</span>
                        <span class="ticker-change ${change >= 0 ? 'positive' : 'negative'}" style="color: ${col};">${sign}${change.toFixed(2)}%</span>
                    </div>`;
                }
                
                html += '</div>';
            }
        }
        
        html += '</div>';
        const ticker = document.getElementById('bloombergTicker');
        if (ticker) ticker.innerHTML = html;
    }
    
    buildBloombergTicker();
    setInterval(buildBloombergTicker, 30000);

    // ===== BREAKING NEWS =====
    function getImportanceLevel(h) {
        const high = ['crash', 'surge', 'record', 'historic', 'emergency', 'halt', 'alert'];
        const med = ['rally', 'decline', 'forecast', 'warns', 'announces'];
        const l = h.toLowerCase();
        return high.some(k => l.includes(k)) ? 'high' : med.some(k => l.includes(k)) ? 'medium' : 'low';
    }

    function categorizeNews(h) {
        const l = h.toLowerCase();
        if (l.includes('crypto') || l.includes('bitcoin') || l.includes('ethereum')) return 'CRYPTO';
        if (l.includes('stock') || l.includes('apple') || l.includes('microsoft')) return 'STOCKS';
        if (l.includes('market') || l.includes('index') || l.includes('s&p')) return 'MARKETS';
        if (l.includes('fed') || l.includes('economy') || l.includes('inflation')) return 'ECONOMY';
        return 'MARKETS';
    }

    function getRelativeTime(d) {
        try {
            const nd = new Date(d);
            const now = new Date();
            const ms = now - nd;
            const mins = Math.floor(ms / 60000);
            const hrs = Math.floor(ms / 3600000);
            const days = Math.floor(ms / 86400000);
            if (mins < 1) return 'Teraz';
            if (mins < 60) return mins + 'm temu';
            if (hrs < 24) return hrs + 'h temu';
            if (days < 7) return days + 'd temu';
            return nd.toLocaleDateString('pl-PL');
        } catch (e) { return 'Niedawno'; }
    }

    async function fetchBreakingNews() {
        try {
            const syms = ['BTCUSD', 'ETHUSD', 'AAPL', 'MSFT', 'SPX'];
            const reqs = syms.map(s => fetch(`https://api.twelvedata.com/stocks/news?symbol=${s}&limit=5&apikey=${TWELVE_DATA_KEY}`).then(r => r.json()).catch(() => ({ data: [] })));
            const results = await Promise.all(reqs);
            const news = results.flatMap(r => r.data || []).filter(a => a && a.title).slice(0, 20);
            return news.length > 0 ? news : getMockNews();
        } catch (e) { return getMockNews(); }
    }

    function getMockNews() {
        return [
            { title: 'Bitcoin Surges Past $95,000', source: 'Bloomberg', published_date: new Date(Date.now() - 300000).toISOString(), symbol: 'BTCUSD' },
            { title: 'Apple Beats Q4 Earnings - Stock Soars', source: 'Reuters', published_date: new Date(Date.now() - 600000).toISOString(), symbol: 'AAPL' },
            { title: 'Fed Signals Possible Rate Pause', source: 'FT', published_date: new Date(Date.now() - 900000).toISOString(), symbol: 'INDU' },
            { title: 'Ethereum Network Upgrade Boosts Performance', source: 'CoinDesk', published_date: new Date(Date.now() - 1200000).toISOString(), symbol: 'ETHUSD' },
            { title: 'S&P 500 Reaches All-Time High', source: 'MarketWatch', published_date: new Date(Date.now() - 1500000).toISOString(), symbol: 'SPX' },
            { title: 'Microsoft AI Investment Initiative', source: 'TechCrunch', published_date: new Date(Date.now() - 1800000).toISOString(), symbol: 'MSFT' }
        ];
    }

    async function buildBreakingNews() {
        const newsData = await fetchBreakingNews();
        if (!newsData || newsData.length === 0) {
            const wrapper = document.getElementById('breakingNewsWrapper');
            if (wrapper) wrapper.innerHTML = '<span class="breaking-news-label">BREAKING NEWS</span><div class="news-loading">Brak wiadomosci</div>';
            return;
        }

        let html = '<div class="breaking-news-scroll">';
        
        for (let loop = 0; loop < 2; loop++) {
            for (const article of newsData) {
                const imp = getImportanceLevel(article.title);
                const cat = categorizeNews(article.title);
                const time = getRelativeTime(article.published_date);
                const src = article.source || 'News';
                const icon = imp === 'high' ? 'RED' : imp === 'medium' ? 'ORANGE' : 'GREEN';
                
                html += `<div class="breaking-news-item">
                    <span class="news-importance ${imp}">${icon} ${imp.toUpperCase()}</span>
                    <span class="news-category-tag category-${cat.toLowerCase()}">${cat}</span>
                    <span class="news-source">${src}</span>
                    <span class="news-headline">${article.title}</span>
                    <span class="news-time">${time}</span>
                </div>`;
            }
            html += '<div style="width: 50px; flex-shrink: 0;"></div>';
        }
        
        html += '</div>';
        const wrapper = document.getElementById('breakingNewsWrapper');
        if (wrapper) wrapper.innerHTML = '<span class="breaking-news-label">BREAKING NEWS</span>' + html;
    }
    
    buildBreakingNews();
    setInterval(buildBreakingNews, 120000);
</script>
```

---

## INSTRUKCJA DODANIA DO TWOJEJ STRONY

1. **Wklej HTML** w sekcji `<body>` tam gdzie chcesz tickery (najlepiej na górze)
2. **Wklej CSS** w sekcji `<head>` wewnątrz `<style>`
3. **Wklej JavaScript** w sekcji `<body>` na końcu wewnątrz `<script>`

## KONFIGURACJA

- **Szybkość Bloomberg:** zmień `75s` w `@keyframes scroll-left` na inne wartości (np. 60s szybciej, 90s wolniej)
- **Szybkość Breaking News:** zmień `95s`
- **Font:** `JetBrains Mono` - jeśli nie chcesz, zmień na `'Courier New'`, `'Roboto Mono'`, itp.
- **Kolory:** zmodyfikuj w CSS (np. `#00d4ff` = jasno-niebieski, `#ff0033` = czerwony)
- **API Key:** zmień `5203977ec0204755904ef326abe77e7c` na swój TwelveData API key

Gotowe! 🚀
