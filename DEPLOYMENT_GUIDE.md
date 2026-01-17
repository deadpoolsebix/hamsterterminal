# 🚀 Deployment Guide - Trading Bot Dashboard

Kompletny przewodnik wdrożenia dashboardu na serwer produkcyjny.

## 📋 Spis treści

1. [Opcje deploymentu](#opcje-deploymentu)
2. [Deployment na VPS (DigitalOcean, AWS, Linode)](#deployment-na-vps)
3. [Deployment na Railway](#deployment-na-railway)
4. [Deployment na Render](#deployment-na-render)
5. [Deployment na Heroku](#deployment-na-heroku)
6. [Konfiguracja domeny i SSL](#konfiguracja-domeny-i-ssl)
7. [Monitoring i utrzymanie](#monitoring-i-utrzymanie)

---

## 🎯 Opcje Deploymentu

### 1. **VPS (Recommended for Production)**
- **Zalety**: Pełna kontrola, najlepsza wydajność, niski koszt długoterminowy
- **Koszt**: $5-20/miesiąc
- **Platformy**: DigitalOcean, Linode, Vultr, AWS Lightsail
- **Czas setup**: 15-30 minut

### 2. **Railway (Fastest)**
- **Zalety**: Darmowy tier, automatyczny deployment z GitHub, zero konfiguracji
- **Koszt**: Darmowy do 500h/miesiąc
- **Czas setup**: 5 minut

### 3. **Render**
- **Zalety**: Darmowy tier, automatyczne SSL, łatwa konfiguracja
- **Koszt**: Darmowy (z limitami)
- **Czas setup**: 10 minut

### 4. **Heroku**
- **Zalety**: Sprawdzony, dokumentowany
- **Koszt**: $7/miesiąc (brak free tier od 2022)
- **Czas setup**: 15 minut

---

## 🖥️ Deployment na VPS

### Krok 1: Utworzenie VPS

#### DigitalOcean (Recommended)
```bash
# 1. Utwórz konto: https://www.digitalocean.com/
# 2. Utwórz Droplet:
#    - Ubuntu 22.04 LTS
#    - Basic Plan: $6/month (1GB RAM)
#    - Region: Najbliższy Tobie
#    - SSH Key: Dodaj swój klucz SSH
```

#### AWS Lightsail
```bash
# 1. Zaloguj się do AWS: https://lightsail.aws.amazon.com/
# 2. Create Instance:
#    - Linux/Unix
#    - OS Only: Ubuntu 22.04 LTS
#    - $5/month plan
```

### Krok 2: Połączenie z serwerem

```bash
# SSH do serwera (zastąp YOUR_IP swoim IP)
ssh root@YOUR_IP

# Lub z użyciem klucza
ssh -i ~/.ssh/your_key root@YOUR_IP
```

### Krok 3: Przygotowanie serwera

```bash
# Update systemu
sudo apt update && sudo apt upgrade -y

# Instalacja niezbędnych pakietów
sudo apt install -y git curl wget ufw

# Konfiguracja firewall
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 8080/tcp   # Dashboard
sudo ufw enable

# Tworzenie użytkownika (zalecane, zamiast root)
sudo adduser botuser
sudo usermod -aG sudo botuser
```

### Krok 4: Instalacja Docker

```bash
# Instalacja Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Dodanie użytkownika do grupy docker
sudo usermod -aG docker $USER

# Instalacja Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Weryfikacja
docker --version
docker-compose --version

# WAŻNE: Wyloguj się i zaloguj ponownie dla grup
exit
ssh root@YOUR_IP
```

### Krok 5: Deployment aplikacji

```bash
# Przejdź na użytkownika (jeśli utworzono)
su - botuser

# Sklonuj repozytorium (jeśli masz na GitHub)
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# LUB prześlij pliki przez SCP (z lokalnego komputera)
# scp -r C:\Users\sebas\Desktop\finalbot root@YOUR_IP:/home/botuser/
```

### Krok 6: Uruchomienie aplikacji

```bash
# Nadaj uprawnienia do skryptu deploy
chmod +x deploy.sh

# Uruchom deployment
./deploy.sh

# LUB ręcznie z Docker Compose
docker-compose up -d

# Sprawdź logi
docker-compose logs -f
```

### Krok 7: Weryfikacja

```bash
# Sprawdź czy działa lokalnie
curl http://localhost:8080

# Sprawdź status kontenerów
docker-compose ps

# Otwórz w przeglądarce
# http://YOUR_SERVER_IP:8080
```

---

## 🚂 Deployment na Railway

### Metoda 1: Z GitHub (Recommended)

1. **Pushuj kod na GitHub**
```bash
cd C:\Users\sebas\Desktop\finalbot

# Inicjalizacja Git (jeśli jeszcze nie zrobione)
git init
git add .
git commit -m "Prepare for deployment"

# Utwórz repo na GitHub i pushuj
git remote add origin https://github.com/YOUR_USERNAME/trading-bot.git
git branch -M main
git push -u origin main
```

2. **Deploy na Railway**
- Wejdź na https://railway.app/
- Kliknij "Start a New Project"
- Wybierz "Deploy from GitHub repo"
- Wybierz swoje repo
- Railway automatycznie wykryje `Dockerfile` lub `requirements.txt`
- Kliknij "Deploy"

3. **Konfiguracja**
- W Settings → Environment: Dodaj zmienne (jeśli potrzebne)
- W Settings → Networking: Włącz Public Domain
- Skopiuj URL i gotowe!

### Metoda 2: Railway CLI

```bash
# Instalacja Railway CLI
npm i -g @railway/cli

# Lub (Windows)
# Pobierz: https://github.com/railwayapp/cli/releases

# Login
railway login

# Inicjalizacja projektu
railway init

# Deploy
railway up
```

---

## 🎨 Deployment na Render

1. **Przygotowanie**
- Utwórz konto: https://render.com/

2. **Utwórz Web Service**
- Dashboard → New → Web Service
- Connect repository (GitHub/GitLab)
- Wybierz swoje repo

3. **Konfiguracja**
```yaml
Name: trading-dashboard
Environment: Docker
Region: Oregon (US West) lub najbliższy
Branch: main
Build Command: (auto from Dockerfile)
Start Command: (auto from Dockerfile)
```

4. **Deploy**
- Kliknij "Create Web Service"
- Render automatycznie zbuduje i uruchomi aplikację
- Po ~5 minutach otrzymasz URL

---

## 🟣 Deployment na Heroku

### Przygotowanie

1. **Instalacja Heroku CLI**
```bash
# Windows
# Pobierz installer: https://devcenter.heroku.com/articles/heroku-cli

# Logowanie
heroku login
```

2. **Utworzenie aplikacji**
```bash
cd C:\Users\sebas\Desktop\finalbot

# Utwórz aplikację (nazwa musi być unikalna)
heroku create trading-bot-dashboard

# LUB z własną nazwą
heroku create your-custom-name
```

3. **Dodaj stack Container**
```bash
heroku stack:set container
```

4. **Deploy**
```bash
# Commit changes (jeśli jeszcze nie)
git add .
git commit -m "Deploy to Heroku"

# Push do Heroku
git push heroku main

# Otwórz aplikację
heroku open

# Sprawdź logi
heroku logs --tail
```

---

## 🌐 Konfiguracja Domeny i SSL

### Dodanie własnej domeny

#### Cloudflare (Recommended - Darmowe SSL)

1. **Dodaj domenę do Cloudflare**
- Wejdź na https://cloudflare.com
- Dodaj swoją domenę
- Zmień nameservery u rejestratora

2. **Konfiguracja DNS**
```
Type: A
Name: @
Content: YOUR_SERVER_IP
Proxy: Enabled (pomarańczowa chmurka)
```

3. **SSL/TLS**
- SSL/TLS → Overview → Full (strict)
- Edge Certificates → Always Use HTTPS: On

#### Let's Encrypt (VPS)

```bash
# Instalacja Certbot
sudo apt install certbot python3-certbot-nginx -y

# Wygenerowanie certyfikatu
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

---

## 📊 Monitoring i Utrzymanie

### Podstawowy monitoring

```bash
# Status kontenerów
docker-compose ps

# Logi w czasie rzeczywistym
docker-compose logs -f

# Zużycie zasobów
docker stats

# Restart
docker-compose restart

# Stop i usunięcie
docker-compose down
```

### Automatyczne restarty

Dodaj do `/etc/systemd/system/trading-bot.service`:

```ini
[Unit]
Description=Trading Bot Dashboard
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/botuser/finalbot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

Aktywacja:
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

### Aktualizacje

```bash
# Pull nowego kodu (z GitHub)
git pull origin main

# Rebuild i restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## ⚡ Quick Start Commands

### Deploy na VPS (One-liner)
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/main/deploy.sh | bash
```

### Deploy na Railway
```bash
railway init && railway up
```

### Deploy na Render
```bash
# Push to GitHub, then connect on Render dashboard
```

---

## 🆘 Troubleshooting

### Problem: Port zajęty
```bash
# Sprawdź co używa portu
sudo lsof -i :8080

# Kill proces
sudo kill -9 PID
```

### Problem: Container nie startuje
```bash
# Sprawdź logi
docker-compose logs dashboard

# Rebuild bez cache
docker-compose build --no-cache
```

### Problem: Brak połączenia
```bash
# Sprawdź firewall
sudo ufw status

# Otwórz port
sudo ufw allow 8080/tcp
```

---

## 📞 Wsparcie

Jeśli masz problemy:
1. Sprawdź logi: `docker-compose logs`
2. Sprawdź status: `docker-compose ps`
3. Restart: `docker-compose restart`

**Sukces!** 🎉 Twój dashboard jest teraz online!
