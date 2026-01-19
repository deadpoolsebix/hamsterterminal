# 🚀 Hamster Terminal WebSocket - Start Here!

## 30 Sekund Setup

```powershell
# Copy-paste poniżej do PowerShell

# 1. Instalacja
pip install -r requirements.txt

# 2. API Key
$env:TWELVE_DATA_API_KEY='demo'

# 3. Run
python api_server.py
```

W drugiej karcie:
```powershell
python -m http.server 8000
```

Otwórz: **http://localhost:8000/professional_websocket_dashboard.html**

✅ Gotowe! Real-time prices bez lagów! 🎉

---

## Co się zmieni?

### Był:
```
REST API co 30 sekund
  ❌ 30 sekund lag
  ❌ Mnóstwo API calls
  ❌ Jerky UI
```

### Jest teraz:
```
WebSocket real-time
  ✅ <100ms lag
  ✅ 99% mniej API calls
  ✅ Smooth updates
```

---

## Pełny Setup (jeśli coś nie działa)

1. **Zainstaluj wymagane pakiety**
   ```powershell
   pip install flask-socketio python-socketio python-engineio websockets requests python-dotenv flask-cors
   ```
   Lub:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Ustaw API Key**
   - Idź na https://twelvedata.com
   - Zaloguj się/zarejestruj
   - Pobierz API Key
   ```powershell
   $env:TWELVE_DATA_API_KEY='twm_xxxxxxxxxxxxxxx'
   ```

3. **Uruchom Backend**
   ```powershell
   python api_server.py
   ```
   
   Powinno pokazać:
   ```
   ✅ Connected to Twelve Data WebSocket
   📡 Subscribed to: BTC/USD,AAPL,MSFT,NVDA,SPY,EUR/USD,GBP/USD
   🌐 Server running on http://0.0.0.0:5000
   ```

4. **Uruchom HTTP Server** (w nowym terminal)
   ```powershell
   python -m http.server 8000
   ```

5. **Otwórz Dashboard**
   ```
   http://localhost:8000/professional_websocket_dashboard.html
   ```

Powinny być live prices! 🚀

---

## Pliki

| Plik | Opis |
|------|------|
| `api_server.py` | Backend z WebSocket + REST API |
| `professional_websocket_client.js` | JS client library |
| `professional_websocket_dashboard.html` | Live dashboard example |
| `start_websocket_server.bat` | Windows launcher |
| `start_websocket_server.ps1` | PowerShell launcher |
| `requirements.txt` | Python packages |

---

## Dokumentacja

📖 **Pełne poradniki:**
- [WEBSOCKET_INTEGRATION_GUIDE.md](./WEBSOCKET_INTEGRATION_GUIDE.md) - Jak to działa
- [TWELVE_DATA_SETUP.md](./TWELVE_DATA_SETUP.md) - Twelve Data setup
- [WEBSOCKET_SUMMARY.md](./WEBSOCKET_SUMMARY.md) - Technical summary

---

## ❓ FAQ

**P: Jaki lag mogę oczekiwać?**  
O: <100ms przy WebSocket, 30s przy REST fallback

**P: Ile to kosztuje?**  
O: Free! (jeśli używasz Twelve Data free tier)

**P: Czy to działa na mobile?**  
O: Tak! Dashboard jest responsive

**P: Czy mogę zmienić symbole?**  
O: Tak, edytuj linie ~300 w `api_server.py`

**P: Co jeśli API key się skończy?**  
O: Fallback na REST API co 30 sekund (powolniej, ale działa)

---

## 🎯 Dalej

### Integracja z Twoim Dashboardem
```html
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
<script src="professional_websocket_client.js"></script>

<script>
    const terminal = new HamsterTerminalWebSocket();
    
    terminal.subscribe('BTC/USD', (data) => {
        document.getElementById('price').textContent = data.price;
    });
</script>
```

### Trading Bot
```javascript
terminal.subscribe('BTC/USD', (data) => {
    if (data.price < 95000) {
        buyBTC();
    }
});
```

---

## 🆘 Problemy?

1. **"Connection refused"**
   - Sprawdź czy `api_server.py` jest uruchomiony
   - Sprawdź port 5000: `netstat -an | grep 5000`

2. **"No updates"**
   - F12 → Console - sprawdź błędy
   - Sprawdź Twelve Data API key jest poprawny
   - Sprawdź network tab (F12 → Network)

3. **Powolne updates**
   - To jest REST API fallback (30s) zamiast WebSocket
   - Sprawdź API key, WebSocket powinien być aktywny

---

## ✅ Gotowe!

Masz teraz profesjonalne real-time API streaming! 🚀

Pytania? Sprawdź pełną dokumentację w plikach `.md`

---

**Made with ❤️ for Wall Street traders** 📈
