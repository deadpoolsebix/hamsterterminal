# Zainstalowane Biblioteki - Środowisko Python

## Data: 15 stycznia 2026
## Lokalizacja: c:\Users\sebas\Desktop\finalbot

### Główne Biblioteki Finansowe i Tradingowe

1. **finvizfinance** (1.3.0)
   - Biblioteka do analizy finansowej i danych giełdowych
   - Źródło: https://github.com/lit26/finvizfinance
   - Zastosowanie: Pobieranie danych finansowych, analiza akcji

2. **PyQL** (3.0.0)
   - Wrapper Python dla QuantLib
   - Zastosowanie: Wycena instrumentów finansowych, obliczenia finansowe

3. **tensortrade** (1.0.3)
   - Framework do trenowania modeli uczenia maszynowego do tradingu
   - Zastosowanie: Backtesting, trenowanie botów tradingowych z ML

4. **vollib** (brak - problem z SWIG)
   - Biblioteka do obliczania cen opcji, implied volatility, Greeks
   - Status: Problem z instalacją - wymaga SWIG
   - Alternatiwa: scipy.optimize mogą być używane do podobnych obliczeń

### Biblioteki Naukowe i ML

- **TensorFlow** (2.20.0) - Framework do deep learning
- **Keras** (3.13.1) - API wysokiego poziomu dla TensorFlow
- **numpy** (1.26.4) - Obliczenia numeryczne
- **pandas** (2.3.3) - Analiza danych, szeregi czasowe
- **scipy** (1.17.0) - Obliczenia naukowe
- **matplotlib** (3.10.8) - Wizualizacja danych
- **plotly** (6.5.2) - Interaktywne wykresy
- **gym** (0.26.2) - Framework dla reinforcement learning

### Biblioteki Wspierające

- **requests** (2.32.5) - Pobieranie danych z sieci
- **beautifulsoup4** (4.14.3) - Web scraping
- **lxml** (6.0.2) - Przetwarzanie XML/HTML
- **ipython** (9.9.0) - Interaktywna konsola Python

## Instrukcje Użycia

### Aktywacja środowiska
```bash
cd c:\Users\sebas\Desktop\finalbot
.\venv\Scripts\Activate.ps1
```

### Import bibliotek w Python
```python
import finvizfinance
import pyql
import tensortrade
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
```

## Problem: vollib

Biblioteka `vollib` wymaga SWIG do kompilacji. Aby ją zainstalować:
1. Pobierz SWIG z https://www.swig.org/download.html
2. Rozpakuj do programów
3. Dodaj do PATH
4. Uruchom: `pip install vollib`

Alternatywa: Użyj `scipy` do obliczań opcji.

## Plik requirements.txt

Wszystkie zainstalowane pakiety zostały zapisane w `requirements.txt`.
Aby zainstalować identyczne środowisko na innym komputerze:
```bash
pip install -r requirements.txt
```

## Aktualizacja

Aby zaktualizować wszystkie pakiety:
```bash
pip install --upgrade -r requirements.txt
```
