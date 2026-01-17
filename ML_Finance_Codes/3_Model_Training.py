#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
3. Trenowanie Modeli ML
Machine Learning in Finance - Przykład
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import tensorflow as tf
from tensorflow import keras
import os
import warnings

warnings.filterwarnings('ignore')

print("=" * 60)
print("3. TRENOWANIE MODELI MACHINE LEARNING")
print("=" * 60)

# Wczytaj dane
print("\n[1] Wczytywanie danych...")
try:
    df = pd.read_csv('data/features.csv')
    print(f"✓ Wczytano {len(df)} rekordów")
except FileNotFoundError:
    print("⚠ Plik nie znaleziony. Uruchom 1_Data_Collection.py i 2_Feature_Engineering.py")
    exit(1)

# Przygotuj dane
print("\n[2] Przygotowanie danych...")

# Cechy (X) i cel (y)
feature_cols = ['Return', 'Volatility', 'MACD', 'Signal', 'Momentum', 
                'ROC', 'K%', 'D%', 'ATR', 'CCI']
target_col = 'Return'

X = df[feature_cols].fillna(0)
y = df[target_col].fillna(0)

# Podziel dane
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"  Train: {len(X_train)}")
print(f"  Test:  {len(X_test)}")

# Model 1: Linear Regression
print("\n[3] Linear Regression...")
model_lr = LinearRegression()
model_lr.fit(X_train, y_train)

y_pred_lr = model_lr.predict(X_test)
r2_lr = r2_score(y_test, y_pred_lr)
mse_lr = mean_squared_error(y_test, y_pred_lr)

print(f"  R² Score: {r2_lr:.4f}")
print(f"  MSE: {mse_lr:.6f}")

# Model 2: Random Forest
print("\n[4] Random Forest...")
model_rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model_rf.fit(X_train, y_train)

y_pred_rf = model_rf.predict(X_test)
r2_rf = r2_score(y_test, y_pred_rf)
mse_rf = mean_squared_error(y_test, y_pred_rf)

print(f"  R² Score: {r2_rf:.4f}")
print(f"  MSE: {mse_rf:.6f}")

# Feature importance
print("  Top 5 ważne cechy:")
importances = model_rf.feature_importances_
for i, (feat, imp) in enumerate(sorted(
    zip(feature_cols, importances), 
    key=lambda x: x[1], 
    reverse=True
)[:5]):
    print(f"    {i+1}. {feat}: {imp:.4f}")

# Model 3: Gradient Boosting
print("\n[5] Gradient Boosting...")
model_gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
model_gb.fit(X_train, y_train)

y_pred_gb = model_gb.predict(X_test)
r2_gb = r2_score(y_test, y_pred_gb)
mse_gb = mean_squared_error(y_test, y_pred_gb)

print(f"  R² Score: {r2_gb:.4f}")
print(f"  MSE: {mse_gb:.6f}")

# Model 4: Neural Network
print("\n[6] Neural Network (TensorFlow/Keras)...")
model_nn = keras.Sequential([
    keras.layers.Dense(64, activation='relu', input_shape=(len(feature_cols),)),
    keras.layers.Dropout(0.2),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dropout(0.2),
    keras.layers.Dense(16, activation='relu'),
    keras.layers.Dense(1)
])

model_nn.compile(optimizer='adam', loss='mse', metrics=['mae'])
model_nn.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0)

y_pred_nn = model_nn.predict(X_test, verbose=0)
r2_nn = r2_score(y_test, y_pred_nn)
mse_nn = mean_squared_error(y_test, y_pred_nn)

print(f"  R² Score: {r2_nn:.4f}")
print(f"  MSE: {mse_nn:.6f}")

# Porównanie modeli
print("\n[7] PORÓWNANIE MODELI:")
print("-" * 40)
results = {
    'Linear Regression': (r2_lr, mse_lr),
    'Random Forest': (r2_rf, mse_rf),
    'Gradient Boosting': (r2_gb, mse_gb),
    'Neural Network': (r2_nn, mse_nn)
}

for model_name, (r2, mse) in sorted(results.items(), key=lambda x: x[1][0], reverse=True):
    print(f"{model_name:20} | R²: {r2:.4f} | MSE: {mse:.6f}")

# Zapisz najlepszy model
best_model = max(results.items(), key=lambda x: x[1][0])
print(f"\n✓ Najlepszy model: {best_model[0]}")

os.makedirs('models', exist_ok=True)

if best_model[0] == 'Linear Regression':
    import pickle
    with open('models/best_model.pkl', 'wb') as f:
        pickle.dump(model_lr, f)
elif best_model[0] == 'Random Forest':
    import pickle
    with open('models/best_model.pkl', 'wb') as f:
        pickle.dump(model_rf, f)
elif best_model[0] == 'Gradient Boosting':
    import pickle
    with open('models/best_model.pkl', 'wb') as f:
        pickle.dump(model_gb, f)
else:
    model_nn.save('models/best_model.h5')

print("✓ Model zapisany do models/")

print("\n" + "=" * 60)
print("MODELOWANIE ZAKOŃCZONE")
print("=" * 60)
