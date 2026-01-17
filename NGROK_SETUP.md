# 🚀 Udostępnianie Dashboardu Online - Instrukcja Ngrok

## KROK 1: Instalacja Ngrok

1. Wejdź na: https://ngrok.com/
2. Załóż darmowe konto (wystarczy email)
3. Pobierz ngrok dla Windows
4. Wypakuj `ngrok.exe` do folderu `C:\Users\sebas\Desktop\finalbot\`

## KROK 2: Konfiguracja Ngrok

Otwórz terminal i wpisz:

```powershell
.\ngrok config add-authtoken <twój-token>
```

(Token znajdziesz na: https://dashboard.ngrok.com/get-started/your-authtoken)

## KROK 3: Uruchomienie Dashboardu

### Opcja A: Szybki start (all-in-one)

```powershell
python start_online_dashboard.py
```

To uruchomi:
- Dashboard Data Engine (aktualizuje dane co 3s)
- HTTP Server (port 8000)

### Opcja B: Krok po kroku

**Terminal 1** - Data Engine:
```powershell
python dashboard_server.py
```

**Terminal 2** - HTTP Server:
```powershell
python -m http.server 8000
```

**Terminal 3** - Ngrok:
```powershell
.\ngrok http 8000
```

## KROK 4: Udostępnienie znajomym

Po uruchomieniu ngrok zobaczysz:

```
Forwarding  https://a1b2-c3d4.ngrok-free.app -> http://localhost:8000
```

**TWÓJ LINK DO UDOSTĘPNIENIA:**
```
https://a1b2-c3d4.ngrok-free.app/dashboard_online.html
```

Wyślij ten link znajomym - mogą otworzyć go na telefonie, komputerze, wszędzie!

## ✨ Killer Features

### 1. Multi-User Mode
Dashboard pokazuje "Users Online: 5" - liczba aktualizuje się automatycznie

### 2. Live Updates
Dane odświeżają się co 3 sekundy bez przeładowania strony

### 3. Mobile-Friendly
Dashboard działa perfekcyjnie na telefonach

### 4. Real-time AI
Jeśli bot działa - dashboard pokazuje realne dane z rynku
Jeśli bot nie działa - pokazuje profesjonalne dane mock

## 🔥 Upgrade Options

### Powiadomienia Telegram
Dodaj do `dashboard_server.py`:

```python
import requests

def send_telegram_alert(message):
    bot_token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

# W update_loop():
if data['probability'] > 80:
    send_telegram_alert(f"🚨 HIGH PROBABILITY: {data['probability']}%")
```

### Persistent URL (płatna opcja)
Darmowy ngrok zmienia URL po każdym uruchomieniu.
Za $10/mies dostajesz stały link typu: `https://yourname.ngrok.io`

## 🛡️ Security Tips

1. **Nie udostępniaj linku publicznie** - tylko znajomym
2. **Zmień port** jeśli chcesz więcej prywatności: `ngrok http 8001`
3. **Basic Auth** - ngrok może dodać hasło: `ngrok http 8000 --basic-auth="user:pass"`

## 📊 Monitoring

Zobacz statystyki na: http://localhost:4040
(działa gdy ngrok jest uruchomiony)

## Troubleshooting

**Problem**: "Address already in use"
**Rozwiązanie**: Zmień port na 8001, 8080, itp.

**Problem**: Ngrok pokazuje "Tunnel not found"
**Rozwiązanie**: Upewnij się, że HTTP server działa na tym samym porcie

**Problem**: Dashboard nie pokazuje danych
**Rozwiązanie**: Sprawdź czy `dashboard_server.py` działa i tworzy `data.json`

## 🎯 Quick Commands

**Start wszystko:**
```powershell
python start_online_dashboard.py
```

**W nowym terminalu - Ngrok:**
```powershell
.\ngrok http 8000
```

**Zatrzymaj wszystko:**
```
Ctrl+C w każdym terminalu
```

---

Gotowe! Dashboard działa online i każdy może go zobaczyć! 🚀
