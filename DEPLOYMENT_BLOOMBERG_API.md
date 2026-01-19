# 🚀 HAMSTER TERMINAL - DEPLOYMENT GUIDE
## Bloomberg Clean Dashboard with API Integration

### Status: ✅ READY FOR DEPLOYMENT

---

## 📁 Files Created

### 1. **demo_bloomberg_with_api.html** (57 KB)
- Complete Bloomberg Terminal-style dashboard
- Monochromatic styling (white/gray only)
- Built-in theme switcher (Bloomberg, Professional, Dark)
- Real-time API integration with fallback to mock data
- Responsive design (mobile-friendly)
- Features:
  - Live BTC/ETH price updates
  - 24h change percentages
  - Fear & Greed Index
  - Large transfers section
  - GENIUS AI analysis panel
  - Multi-tab interface (Trend, KPI, Multi-TF)
  - Ticker with key assets

### 2. **api_server_enhanced.py** (8 KB)
- Flask REST API server
- CORS enabled for cross-origin requests
- Real-time data fetching from:
  - Binance API (crypto prices)
  - CoinGecko API (market cap)
  - Alternative.me (Fear & Greed)
- Background data updater (30-second interval)
- Endpoints:
  - `/api/binance/summary` - Market data
  - `/api/fear-greed` - Sentiment index
  - `/api/status` - Server status
  - `/dashboard` - Serve HTML

---

## 🌐 LOCAL SETUP (Localhost)

### Step 1: Start API Server
```powershell
cd C:\Users\sebas\Desktop\finalbot
python api_server_enhanced.py
```

Expected output:
```
🚀 HAMSTER TERMINAL - BLOOMBERG CLEAN API SERVER v2.0
================================================== ====
Server: http://0.0.0.0:5000
Dashboard: http://localhost:5000/dashboard
API Docs: http://localhost:5000/

📡 Real-time data sources:
  • Binance API (BTC/ETH prices, volume)
  • CoinGecko API (Market cap)
  • Alternative.me (Fear & Greed Index)

🔄 Data update interval: 30 seconds
================================================== ====
```

### Step 2: Access Dashboard
```
http://localhost:5000/dashboard
```

OR

```
http://localhost:8000/demo_bloomberg_with_api.html
```

---

## 🚀 PRODUCTION DEPLOYMENT (hamsterterminal.com)

### Option A: Deploy to Render (Recommended)

#### 1. Create `render.yaml` in project root:
```yaml
services:
  - type: web
    name: hamster-terminal-api
    env: python
    plan: free
    pythonVersion: 3.9
    buildCommand: pip install -r requirements.txt
    startCommand: python api_server_enhanced.py
    envVars:
      - key: FLASK_ENV
        value: production
```

#### 2. Deploy:
```bash
# Push to GitHub
git add .
git commit -m "Deploy: Bloomberg Clean Dashboard with API"
git push

# Then use Render dashboard to deploy
```

#### 3. Update HTML API endpoint:
In `demo_bloomberg_with_api.html`, change:
```javascript
const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000'
  : 'https://hamster-terminal-api.onrender.com';  // Your Render URL
```

### Option B: Deploy to Railway

```bash
# Login to Railway
railway login

# Initialize and deploy
railway init
railway up
```

### Option C: Deploy to Heroku

```bash
# Login
heroku login

# Create app
heroku create hamster-terminal

# Add Procfile (already exists)
git push heroku main
```

---

## 🌐 Update GitHub Pages (hamsterterminal.com)

### 1. Copy files to docs/
```powershell
Copy-Item demo_bloomberg_with_api.html docs/index.html -Force
```

### 2. Update docs/index.html API endpoint:
```html
<!-- At top of <body>, add: -->
<script>
  // Use GitHub Pages API endpoint or fallback to live data
  const API_BASE = 'https://hamster-terminal-api.onrender.com';
</script>
```

### 3. Push to GitHub
```bash
git add docs/index.html
git commit -m "Update: New Bloomberg Clean Dashboard"
git push origin main
```

### 4. Dashboard will be live at:
```
https://hamsterterminal.com
https://hamsterterminal.com/index.html
```

---

## 🎨 THEME SWITCHER

Users can now switch between:
- **Bloomberg** (Default) - Orange/Burgundy + white text
- **Professional** - Blue/dark professional theme
- **Dark** - Pure black with minimal styling

Buttons visible in top-right corner of dashboard.

---

## 📊 API ENDPOINTS

| Endpoint | Method | Response | Update Interval |
|----------|--------|----------|-----------------|
| `/` | GET | Server info & endpoints | - |
| `/api/binance/summary` | GET | BTC/ETH prices, volume, market cap | 30s |
| `/api/fear-greed` | GET | Fear & Greed Index (0-100) | 30s |
| `/api/status` | GET | Server status & cache | - |
| `/dashboard` | GET | HTML dashboard file | - |

---

## 🔌 REAL-TIME DATA FLOW

```
Binance API
    ↓ (30s interval)
[api_server_enhanced.py - Cache]
    ↓ (JSON response)
HTML Dashboard
    ↓ (JavaScript fetch every 10s)
UI Update (Price, sentiment, fear_greed)
```

---

## ✅ TESTING

### Local test:
```bash
# Test API response
curl http://localhost:5000/api/binance/summary

# Expected:
# {"ok":true,"btcPrice":98432.50,"btcChange24h":0.27,...}
```

### Production test:
```bash
curl https://hamster-terminal-api.onrender.com/api/binance/summary
```

---

## 🛠️ TROUBLESHOOTING

### Issue: "API error - Using mock data"
- Check if API server is running
- Verify internet connection
- Check CORS settings
- Review browser console for errors

### Issue: Prices not updating
- API server may have crashed
- Binance/CoinGecko may be rate-limited
- Check server logs: `ps aux | grep python`

### Issue: Dashboard styling broken
- Clear browser cache (Ctrl+Shift+R)
- Check CSS variables in <head>
- Verify no conflicting styles

---

## 📝 REQUIREMENTS.TXT

Make sure `requirements.txt` includes:
```
flask==2.3.0
flask-cors==4.0.0
requests==2.31.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 🎯 NEXT STEPS

1. ✅ **Local Testing** - Test on localhost:5000
2. ✅ **API Integration** - Verify real data fetching
3. ✅ **Theme Switching** - Test all 3 themes
4. 🔄 **Deploy to Render/Railway**
5. 🔄 **Update hamsterterminal.com**
6. 🔄 **Monitor Performance**

---

## 📞 SUPPORT

For issues or feature requests:
- Check browser console (F12 → Console)
- Review server logs
- Verify API endpoint responds: `curl http://localhost:5000/api/status`

---

**Created:** 2026-01-19  
**Status:** ✅ Ready for production  
**Version:** 2.0 - Bloomberg Clean with API
