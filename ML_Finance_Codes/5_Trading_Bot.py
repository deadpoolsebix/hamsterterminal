#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
5. Bot Tradingowy
Machine Learning in Finance - Przykład
"""

import pandas as pd
import numpy as np
import pickle
import time
from datetime import datetime
import os

print("=" * 60)
print("5. BOT TRADINGOWY")
print("=" * 60)

class TradingBot:
    """Bot tradingowy oparty na ML"""
    
    def __init__(self, model_path='models/best_model.pkl', initial_capital=10000):
        self.model = self._load_model(model_path)
        self.capital = initial_capital
        self.portfolio = {}
        self.trades = []
        self.feature_cols = ['Return', 'Volatility', 'MACD', 'Signal', 
                           'Momentum', 'ROC', 'K%', 'D%', 'ATR', 'CCI']
        
    def _load_model(self, path):
        """Wczytaj model ML"""
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except:
            print("⚠ Model nie znaleziony. Używam model dummy.")
            return None
    
    def predict_signal(self, features):
        """Predykuj sygnał handlowy"""
        if self.model is None:
            return 0
        
        predicted_return = self.model.predict([features])[0]
        
        if predicted_return > 0.01:
            return 1  # BUY
        elif predicted_return < -0.01:
            return -1  # SELL
        else:
            return 0  # HOLD
    
    def execute_trade(self, symbol, signal, price):
        """Wykonaj transakcję"""
        if signal == 1 and self.capital > price:
            # BUY
            quantity = int(self.capital / price * 0.5)  # Use 50% of capital
            cost = quantity * price
            self.portfolio[symbol] = self.portfolio.get(symbol, 0) + quantity
            self.capital -= cost
            
            self.trades.append({
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': 'BUY',
                'quantity': quantity,
                'price': price,
                'total': cost
            })
            print(f"  ✓ BUY {quantity} {symbol} @ ${price:.2f}")
            
        elif signal == -1 and self.portfolio.get(symbol, 0) > 0:
            # SELL
            quantity = self.portfolio[symbol]
            revenue = quantity * price
            self.portfolio[symbol] = 0
            self.capital += revenue
            
            self.trades.append({
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': 'SELL',
                'quantity': quantity,
                'price': price,
                'total': revenue
            })
            print(f"  ✓ SELL {quantity} {symbol} @ ${price:.2f}")
    
    def get_portfolio_value(self, prices):
        """Oblicz wartość portfela"""
        portfolio_value = self.capital
        for symbol, quantity in self.portfolio.items():
            if symbol in prices:
                portfolio_value += quantity * prices[symbol]
        return portfolio_value
    
    def print_status(self):
        """Wyświetl status"""
        print(f"\n{'='*40}")
        print(f"Kapitał dostępny: ${self.capital:,.2f}")
        print(f"Pozycje: {self.portfolio}")
        print(f"Liczba transakcji: {len(self.trades)}")
        print(f"{'='*40}")

# Inicjalizacja bota
print("\n[1] Inicjalizacja bota...")
bot = TradingBot()
bot.print_status()

# Symulacja
print("\n[2] Symulacja handlu...")

# Załaduj dane
try:
    df = pd.read_csv('data/features.csv')
except:
    print("⚠ Brak danych. Tworzę dane sztuczne...")
    df = None

# Symulacja handlu (ostatnie 20 dni)
print("\n[3] Ostatnie 20 sesji handlowych:")
print("-" * 40)

if df is not None and len(df) > 0:
    sample = df.tail(20)
    feature_cols = ['Return', 'Volatility', 'MACD', 'Signal', 
                   'Momentum', 'ROC', 'K%', 'D%', 'ATR', 'CCI']
    
    for idx, row in sample.iterrows():
        price = row['Close']
        
        # Pobierz cechy
        features = []
        for col in feature_cols:
            features.append(row.get(col, 0))
        
        # Predykcja
        signal = bot.predict_signal(features)
        
        # Handel
        if signal != 0:
            action = "BUY" if signal == 1 else "SELL"
            print(f"[{idx}] {action:4} @ ${price:.2f}")
            bot.execute_trade('STOCK', signal, price)

# Finał
print("\n[4] PODSUMOWANIE:")
bot.print_status()

# Zapisz transakcje
if bot.trades:
    trades_df = pd.DataFrame(bot.trades)
    trades_df.to_csv('results/bot_trades.csv', index=False)
    print(f"✓ {len(bot.trades)} transakcji zapisanych do results/bot_trades.csv")

print("\n" + "=" * 60)
print("BOT TRADINGOWY GOTÓW")
print("=" * 60)
print("\nNotatka: To jest DEMO bot. W produkcji wymagane:")
print("  - Połączenie z brokerem (API)")
print("  - Real-time data feed")
print("  - Risk management")
print("  - Stop-loss i Take-profit")
print("=" * 60)
