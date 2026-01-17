#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
4. Backtesting
Machine Learning in Finance - Przykład
"""

import pandas as pd
import numpy as np
import pickle
import os

print("=" * 60)
print("4. BACKTESTING STRATEGII")
print("=" * 60)

# Wczytaj dane
print("\n[1] Wczytywanie danych...")
try:
    df = pd.read_csv('data/features.csv')
    print(f"✓ Wczytano {len(df)} rekordów")
except FileNotFoundError:
    print("⚠ Brak danych. Uruchom 1_Data_Collection.py")
    exit(1)

# Wczytaj model
print("\n[2] Wczytywanie modelu...")
try:
    with open('models/best_model.pkl', 'rb') as f:
        model = pickle.load(f)
    print("✓ Model wczytany")
except FileNotFoundError:
    print("⚠ Brak modelu. Uruchom 3_Model_Training.py")
    exit(1)

# Przygotuj dane
print("\n[3] Przygotowanie danych do backtestingu...")
feature_cols = ['Return', 'Volatility', 'MACD', 'Signal', 'Momentum', 
                'ROC', 'K%', 'D%', 'ATR', 'CCI']

X = df[feature_cols].fillna(0)

# Predykcje
print("\n[4] Generowanie predykcji...")
df['Predicted_Return'] = model.predict(X)

# Strategia handlowa
print("\n[5] Generowanie sygnałów handlowych...")
df['Signal'] = 0

# Kup gdy predicted return > 0
df.loc[df['Predicted_Return'] > 0, 'Signal'] = 1
# Sprzedaj gdy predicted return < 0
df.loc[df['Predicted_Return'] < 0, 'Signal'] = -1

signal_counts = df['Signal'].value_counts()
print(f"  Buy signals (1):  {signal_counts.get(1, 0)}")
print(f"  Sell signals (-1): {signal_counts.get(-1, 0)}")
print(f"  Neutral (0):      {signal_counts.get(0, 0)}")

# Oblicz zyski
print("\n[6] Obliczanie zysków...")
initial_capital = 10000
position_size = initial_capital / len(df)

df['Position_Return'] = df['Signal'].shift(1) * df['Return']
df['Portfolio_Value'] = initial_capital * (1 + df['Position_Return'].cumsum())

# Metryki
total_return = (df['Portfolio_Value'].iloc[-1] - initial_capital) / initial_capital * 100
yearly_return = total_return
max_drawdown = ((df['Portfolio_Value'].cummax() - df['Portfolio_Value']) / 
                df['Portfolio_Value'].cummax()).max() * 100
win_rate = (df['Position_Return'] > 0).sum() / (df['Position_Return'] != 0).sum() * 100
sharpe_ratio = df['Position_Return'].mean() / df['Position_Return'].std() * np.sqrt(252)

print(f"\n[7] REZULTATY BACKTESTINGU:")
print("-" * 40)
print(f"Kapitał początkowy:    ${initial_capital:,.2f}")
print(f"Kapitał końcowy:       ${df['Portfolio_Value'].iloc[-1]:,.2f}")
print(f"Zwrot całkowity:       {total_return:.2f}%")
print(f"Max Drawdown:          {max_drawdown:.2f}%")
print(f"Win Rate:              {win_rate:.2f}%")
print(f"Sharpe Ratio (annualized): {sharpe_ratio:.4f}")
print(f"Liczba transakcji:     {(df['Signal'] != df['Signal'].shift(1)).sum()}")

# Zapisz wyniki
os.makedirs('results', exist_ok=True)

# CSV
results_df = df[['Date', 'Close', 'Return', 'Predicted_Return', 
                 'Signal', 'Portfolio_Value']].copy()
results_df.to_csv('results/backtest_results.csv', index=False)
print("\n✓ Wyniki zapisane: results/backtest_results.csv")

# Raport
report = f"""
RAPORT BACKTESTINGU
===================

Data raportu: 2026-01-15
Liczba dni testowania: {len(df)}
Kapitał początkowy: ${initial_capital:,.2f}

REZULTATY:
---------
Kapitał końcowy: ${df['Portfolio_Value'].iloc[-1]:,.2f}
Zwrot całkowity: {total_return:.2f}%
Maximum Drawdown: {max_drawdown:.2f}%
Win Rate: {win_rate:.2f}%
Sharpe Ratio: {sharpe_ratio:.4f}

METRYKI TRANSAKCJI:
-------------------
Liczba Buy Signals: {signal_counts.get(1, 0)}
Liczba Sell Signals: {signal_counts.get(-1, 0)}
Liczba zmian sygnałów: {(df['Signal'] != df['Signal'].shift(1)).sum()}

PORADY:
------
- Sharpe Ratio > 1.0 jest uważany za dobry
- Max Drawdown < 20% jest akceptowalny
- Win Rate > 50% wskazuje na rentowną strategię
"""

with open('results/backtest_report.txt', 'w') as f:
    f.write(report)
print("✓ Raport zapisany: results/backtest_report.txt")

print("\n" + "=" * 60)
print("BACKTESTING ZAKOŃCZONY")
print("=" * 60)
