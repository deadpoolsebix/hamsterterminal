#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
1. Pobieranie i Przygotowanie Danych
Machine Learning in Finance - Przykład
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import os

# Tworzenie katalogów
os.makedirs('data', exist_ok=True)

print("=" * 60)
print("1. POBIERANIE I PRZYGOTOWANIE DANYCH")
print("=" * 60)

# Przykład 1: Dane finansowe
print("\n[1] Pobieranie danych finansowych...")

try:
    from finvizfinance.quote import Quote
    
    # Pobierz dane dla kilku akcji
    stocks = ['AAPL', 'MSFT', 'GOOGL']
    
    for stock in stocks:
        try:
            quote = Quote(stock)
            data = quote.get_general()
            print(f"✓ {stock}: {data.get('Price', 'N/A')}")
        except Exception as e:
            print(f"⚠ {stock}: {e}")
            
except ImportError:
    print("⚠ finvizfinance niedostępna")

# Przykład 2: Generowanie sztucznych danych
print("\n[2] Generowanie danych sztucznych...")

np.random.seed(42)
dates = pd.date_range(start='2023-01-01', periods=252, freq='D')

# Symulacja cen akcji
returns = np.random.normal(0.0005, 0.02, 252)
prices = 100 * np.exp(np.cumsum(returns))

data = pd.DataFrame({
    'Date': dates,
    'Close': prices,
    'Volume': np.random.randint(1000000, 10000000, 252),
    'High': prices * (1 + np.abs(np.random.normal(0, 0.01, 252))),
    'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, 252))),
})

print(f"✓ Wygenerowano {len(data)} rekordów")
print(data.head())

def calculate_rsi(prices, period=14):
    """Oblicz Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Przykład 3: Feature Engineering
print("\n[3] Inżynieria cech...")

data['Return'] = data['Close'].pct_change()
data['MA_5'] = data['Close'].rolling(5).mean()
data['MA_20'] = data['Close'].rolling(20).mean()
data['Volatility'] = data['Return'].rolling(20).std()
data['RSI'] = calculate_rsi(data['Close'])

print("✓ Dodane cechy:")
print(f"  - Return (zwrot)")
print(f"  - MA_5, MA_20 (średnie kroczące)")
print(f"  - Volatility (zmienność)")
print(f"  - RSI (Relative Strength Index)")

# Przykład 4: Czyszczenie danych
print("\n[4] Czyszczenie danych...")

data_clean = data.dropna()
print(f"✓ Usunięto wiersze z NaN: {len(data) - len(data_clean)}")

# Zapisz dane
data_clean.to_csv('data/training_data.csv', index=False)
print("✓ Dane zapisane: data/training_data.csv")

print("\n" + "=" * 60)
print("DANE GOTOWE DO TRENOWANIA MODELU")
print("=" * 60)
