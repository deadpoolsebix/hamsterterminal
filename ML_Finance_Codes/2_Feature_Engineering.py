#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2. Feature Engineering
Machine Learning in Finance - Przykład
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

print("=" * 60)
print("2. INŻYNIERIA CECH (FEATURE ENGINEERING)")
print("=" * 60)

# Wczytaj dane
print("\n[1] Wczytywanie danych...")
try:
    df = pd.read_csv('data/training_data.csv')
    print(f"✓ Wczytano {len(df)} rekordów")
except FileNotFoundError:
    print("⚠ Plik nie znaleziony. Uruchom najpierw 1_Data_Collection.py")
    exit(1)

# Techniczne wskaźniki
print("\n[2] Dodawanie wskaźników technicznych...")

# MACD (Moving Average Convergence Divergence)
df['EMA_12'] = df['Close'].ewm(span=12).mean()
df['EMA_26'] = df['Close'].ewm(span=26).mean()
df['MACD'] = df['EMA_12'] - df['EMA_26']
df['Signal'] = df['MACD'].ewm(span=9).mean()
df['MACD_Hist'] = df['MACD'] - df['Signal']
print("  ✓ MACD")

# Bollinger Bands
sma = df['Close'].rolling(window=20).mean()
std = df['Close'].rolling(window=20).std()
df['BB_Upper'] = sma + (std * 2)
df['BB_Lower'] = sma - (std * 2)
df['BB_Middle'] = sma
print("  ✓ Bollinger Bands")

# ATR (Average True Range)
df['TR'] = np.maximum(
    df['High'] - df['Low'],
    np.maximum(
        abs(df['High'] - df['Close'].shift(1)),
        abs(df['Low'] - df['Close'].shift(1))
    )
)
df['ATR'] = df['TR'].rolling(window=14).mean()
print("  ✓ ATR (Average True Range)")

# Stochastic Oscillator
df['Lowest_Low'] = df['Low'].rolling(window=14).min()
df['Highest_High'] = df['High'].rolling(window=14).max()
df['K%'] = 100 * ((df['Close'] - df['Lowest_Low']) / 
                  (df['Highest_High'] - df['Lowest_Low']))
df['D%'] = df['K%'].rolling(window=3).mean()
print("  ✓ Stochastic Oscillator")

# Wskaźniki fundamentalne
print("\n[3] Dodawanie wskaźników fundamentalnych...")

# Momentum
df['Momentum'] = df['Close'] - df['Close'].shift(10)
print("  ✓ Momentum")

# Rate of Change (ROC)
df['ROC'] = ((df['Close'] - df['Close'].shift(12)) / 
             df['Close'].shift(12) * 100)
print("  ✓ Rate of Change")

# CCI (Commodity Channel Index)
typical_price = (df['High'] + df['Low'] + df['Close']) / 3
sma_tp = typical_price.rolling(window=20).mean()
mad = typical_price.rolling(window=20).apply(
    lambda x: abs(x - x.mean()).mean()
)
df['CCI'] = (typical_price - sma_tp) / (0.015 * mad)
print("  ✓ CCI (Commodity Channel Index)")

# Normalizacja
print("\n[4] Normalizacja cech...")
scaler = StandardScaler()

features_to_scale = ['Return', 'Volatility', 'MACD', 'Signal', 
                     'Momentum', 'ROC', 'K%', 'D%', 'CCI']

for feature in features_to_scale:
    if feature in df.columns:
        df[f'{feature}_Scaled'] = scaler.fit_transform(
            df[[feature]].fillna(0)
        )

print("  ✓ Cechy znormalizowane")

# Usuń NaN
df_clean = df.dropna()

print(f"\n[5] Czyszczenie...")
print(f"  Usunięto {len(df) - len(df_clean)} wierszy z NaN")
print(f"  Pozostało: {len(df_clean)} rekordów")

# Zapisz
output_file = 'data/features.csv'
df_clean.to_csv(output_file, index=False)
print(f"✓ Cechy zapisane: {output_file}")

print("\n[6] Statystyka cech:")
print(df_clean[['Return', 'Volatility', 'MACD', 'Momentum', 'K%']].describe())

print("\n" + "=" * 60)
print("CECHY GOTOWE DO TRENOWANIA MODELU")
print("=" * 60)
