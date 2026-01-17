# 🚀 GitHub Quick Start - Trading Bot

## 📋 Metoda 1: AUTOMATYCZNA (Recommended) ⚡

### Krok 1: Utwórz repo na GitHub

1. Wejdź na: https://github.com/new
2. Repository name: `trading-bot-pro` (lub dowolna nazwa)
3. Description: "Professional Trading Bot Dashboard"
4. Wybierz: **Public** lub **Private**
5. ⚠️ **NIE** zaznaczaj "Add a README file"
6. ⚠️ **NIE** zaznaczaj "Add .gitignore"
7. Kliknij **"Create repository"**

### Krok 2: Uruchom automatyczny skrypt

```powershell
# W folderze projektu
.\push_to_github.ps1
```

Skrypt automatycznie:
- ✅ Zainicjalizuje Git
- ✅ Skonfiguruje użytkownika
- ✅ Doda wszystkie pliki
- ✅ Wykona commit
- ✅ Wyśle na GitHub

**GOTOWE!** 🎉

---

## 📋 Metoda 2: MANUALNA (Krok po kroku)

### Krok 1: Zainstaluj Git (jeśli nie masz)

Pobierz: https://git-scm.com/download/win

### Krok 2: Konfiguracja Git

```powershell
# Ustaw nazwę użytkownika
git config --global user.name "Twoje Imię"

# Ustaw email
git config --global user.email "twoj@email.com"

# Sprawdź konfigurację
git config --list
```

### Krok 3: Utwórz repo na GitHub

1. Wejdź na: https://github.com/new
2. Nazwa: `trading-bot-pro`
3. Ustaw jako Public/Private
4. **NIE** dodawaj README ani .gitignore
5. Utwórz repo

### Krok 4: Inicjalizacja lokalnego repo

```powershell
# W folderze C:\Users\sebas\Desktop\finalbot
cd C:\Users\sebas\Desktop\finalbot

# Inicjalizuj Git
git init

# Sprawdź status
git status
```

### Krok 5: Dodaj pliki

```powershell
# Dodaj wszystkie pliki
git add .

# Lub wybrane pliki
git add serve_dashboard.py professional_dashboard_final.html Dockerfile requirements.txt

# Sprawdź co zostanie dodane
git status
```

### Krok 6: Pierwszy commit

```powershell
# Utwórz commit
git commit -m "🚀 Initial commit - Professional Trading Dashboard"

# Zmień branch na main (jeśli potrzeba)
git branch -M main
```

### Krok 7: Połącz z GitHub

```powershell
# Dodaj remote (ZMIEŃ na swój URL!)
git remote add origin https://github.com/TWOJ_USERNAME/trading-bot-pro.git

# Sprawdź remote
git remote -v
```

### Krok 8: Push na GitHub

```powershell
# Wypchnij na GitHub
git push -u origin main
```

**SUKCES!** 🎉 Twój kod jest na GitHub!

---

## 🔐 Logowanie do GitHub

### Opcja A: HTTPS z Personal Access Token (Recommended)

1. Wejdź na: https://github.com/settings/tokens
2. "Generate new token" → "Generate new token (classic)"
3. Zaznacz: `repo` (full access)
4. Wygeneruj token
5. **SKOPIUJ TOKEN** (nie zobaczysz go ponownie!)
6. Przy push używaj tokena jako hasła:
   - Username: twoja_nazwa_github
   - Password: wklej_token

### Opcja B: SSH (Advanced)

```powershell
# Generuj klucz SSH
ssh-keygen -t ed25519 -C "twoj@email.com"

# Kopiuj klucz publiczny
Get-Content ~/.ssh/id_ed25519.pub | Set-Clipboard

# Dodaj na GitHub:
# https://github.com/settings/ssh/new

# Zmień remote na SSH
git remote set-url origin git@github.com:TWOJ_USERNAME/trading-bot-pro.git

# Test połączenia
ssh -T git@github.com
```

---

## 🔄 Aktualizacje (po pierwszym push)

### Dodaj nowe zmiany

```powershell
# Zobacz zmiany
git status

# Dodaj zmienione pliki
git add .

# Lub konkretny plik
git add nazwa_pliku.py

# Commit ze zmianami
git commit -m "opis zmian"

# Push na GitHub
git push
```

### Szybka aktualizacja (one-liner)

```powershell
git add . ; git commit -m "Update"; git push
```

---

## 🚀 Deploy po push na GitHub

### Railway

```powershell
# Zainstaluj CLI
npm i -g @railway/cli

# Login i deploy
railway login
railway init
railway up
```

### Render

1. Wejdź na: https://render.com/
2. "New" → "Web Service"
3. Połącz z GitHub repo
4. Render automatycznie wykryje Dockerfile
5. Kliknij "Create Web Service"

### Vercel (dla frontend)

```powershell
npm i -g vercel
vercel login
vercel
```

---

## ❓ Troubleshooting

### Problem: "Permission denied"

**Rozwiązanie:** Użyj Personal Access Token zamiast hasła

### Problem: "Repository not found"

**Rozwiązanie:**
```powershell
# Sprawdź remote
git remote -v

# Popraw URL (ZMIEŃ na swój!)
git remote set-url origin https://github.com/TWOJ_USERNAME/trading-bot-pro.git
```

### Problem: "Failed to push"

**Rozwiązanie:**
```powershell
# Pull najpierw (jeśli repo nie puste)
git pull origin main --allow-unrelated-histories

# Potem push
git push -u origin main
```

### Problem: "Conflicting files"

**Rozwiązanie:**
```powershell
# Force push (UWAGA: nadpisze remote!)
git push -u origin main --force
```

---

## 📚 Przydatne Komendy Git

```powershell
# Status projektu
git status

# Historia commitów
git log --oneline

# Cofnij ostatni commit (zachowaj zmiany)
git reset --soft HEAD~1

# Zobacz różnice
git diff

# Utwórz branch
git checkout -b feature/nowa-funkcja

# Przełącz branch
git checkout main

# Merge branch
git merge feature/nowa-funkcja

# Usuń branch
git branch -d feature/nowa-funkcja

# Pobierz zmiany z GitHub
git pull

# Clone repo (jako ktoś inny)
git clone https://github.com/USERNAME/repo.git
```

---

## 🎯 Następne Kroki

Po pushie na GitHub:

1. ✅ **Dodaj README badges**: shields.io
2. ✅ **Deploy na serwer**: Zobacz DEPLOYMENT_GUIDE.md
3. ✅ **Ustaw GitHub Pages**: Dla dokumentacji
4. ✅ **Dodaj License**: MIT recommended
5. ✅ **Utwórz Releases**: Tags dla wersji

---

## 🆘 Potrzebujesz pomocy?

- 📖 Dokumentacja Git: https://git-scm.com/doc
- 📖 GitHub Guides: https://guides.github.com/
- 💬 GitHub Community: https://github.community/

**Powodzenia!** 🚀
