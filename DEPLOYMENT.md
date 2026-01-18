# Deployment Guide - Hamster Terminal Dashboard

## Status: ✅ LIVE

**Domain:** https://hamsterterminal.com  
**GitHub Repo:** https://github.com/deadpoolsebix/hamsterterminal  
**Source:** `/docs` folder (GitHub Pages)

---

## Setup Instructions

### 1. GitHub Pages Configuration (wykonaj raz)
1. Przejdź na: https://github.com/deadpoolsebix/hamsterterminal/settings/pages
2. **Source:** 
   - Branch: `main`
   - Folder: `/docs`
3. **Custom Domain:** `hamsterterminal.com`
4. **Enforce HTTPS:** ✓ (włączyć)
5. Kliknij **Save**

### 2. Cloudflare DNS (już skonfigurowano)
- CNAME record: `hamsterterminal.com` → `deadpoolsebix.github.io`
- Proxy: Cloudflare (orange cloud)

---

## Aktualizacja Dashboard

Każdy commit na `main` → **automatyczne wdrożenie na** https://hamsterterminal.com

**Workflow:**
```bash
# 1. Modyfikuj dashboard
# vim professional_dashboard_final.html

# 2. Skopiuj do docs/
cp professional_dashboard_final.html docs/index.html

# 3. Zacommit i push
git add -A
git commit -m "Update: [opis zmian]"
git push origin main

# Dashboard live za ~1 min 🚀
```

---

## Pliki do wdrażania

- `docs/index.html` ← Dashboard (główny plik)
- `docs/plotly.min.js` ← Biblioteka do wykresów
- `docs/.nojekyll` ← Flagga (GitHub Pages bez Jekyll)

---

## Monitorowanie

- **Live:** https://hamsterterminal.com
- **GitHub Deployments:** https://github.com/deadpoolsebix/hamsterterminal/deployments

---

**Last Deploy:** 18.01.2026 (Entry Zone Calculator + Trading Signals)
