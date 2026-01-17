#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Użycie FFN - Analiza Finansowa i Metryki Ryzyka
Machine Learning Bot - Część 3
"""

import numpy as np
import pandas as pd

print("=" * 60)
print("FFN - ANALIZA FINANSOWA I METRYKI RYZYKA")
print("=" * 60)

try:
    import ffn
    print("\n✓ FFN załadowany")
    
    # Generuj sztuczne dane
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=252, freq='D')
    returns = np.random.normal(0.0005, 0.02, 252)
    prices = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'Date': dates,
        'Price': prices,
        'Return': returns
    })
    
    print("\n[1] PODSTAWOWE METRYKI")
    print("-" * 40)
    
    # Zwrot całkowity
    total_return = (prices[-1] - prices[0]) / prices[0]
    print(f"  Zwrot całkowity: {total_return*100:.2f}%")
    
    # Zwrot średni
    avg_return = returns.mean()
    print(f"  Średni zwrot dzienny: {avg_return*100:.4f}%")
    
    # Zmienność
    volatility = returns.std()
    annual_volatility = volatility * np.sqrt(252)
    print(f"  Zmienność dzienna: {volatility*100:.2f}%")
    print(f"  Zmienność roczna: {annual_volatility*100:.2f}%")
    
    print("\n[2] METRYKI RYZYKA")
    print("-" * 40)
    
    # Sharpe Ratio
    risk_free_rate = 0.02
    excess_return = returns.mean() - risk_free_rate / 252
    sharpe_ratio = excess_return / volatility * np.sqrt(252)
    print(f"  Sharpe Ratio: {sharpe_ratio:.4f}")
    
    # Sortino Ratio
    downside_returns = returns[returns < 0]
    downside_volatility = downside_returns.std()
    sortino_ratio = excess_return / downside_volatility * np.sqrt(252) if len(downside_returns) > 0 else 0
    print(f"  Sortino Ratio: {sortino_ratio:.4f}")
    
    # Maximum Drawdown
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    print(f"  Maximum Drawdown: {max_drawdown*100:.2f}%")
    
    # Value at Risk (VaR)
    var_95 = np.percentile(returns, 5)
    print(f"  Value at Risk (95%): {var_95*100:.2f}%")
    
    # Conditional Value at Risk (CVaR)
    cvar_95 = returns[returns <= var_95].mean()
    print(f"  Conditional VaR (95%): {cvar_95*100:.2f}%")
    
    print("\n[3] ANALIZA ZWROTÓW")
    print("-" * 40)
    
    try:
        # Cumulative returns
        cum_returns = ffn.to_cumulative_returns(returns)
        print(f"  ✓ Skumulowane zwroty obliczone")
        print(f"    Początek: {cum_returns.iloc[0]:.4f}")
        print(f"    Koniec: {cum_returns.iloc[-1]:.4f}")
    except:
        print("  ⚠ Błąd w obliczeniach ffn")
    
    # Monthly returns
    df['Return'] = returns
    df.set_index('Date', inplace=True)
    monthly_returns = df['Return'].resample('M').sum()
    print(f"\n  Zwroty miesięczne:")
    print(f"    Min: {monthly_returns.min()*100:.2f}%")
    print(f"    Max: {monthly_returns.max()*100:.2f}%")
    print(f"    Mean: {monthly_returns.mean()*100:.2f}%")
    
    print("\n[4] PORÓWNANIE STRATEGII")
    print("-" * 40)
    
    # Strategia 1: Buy & Hold
    buy_hold = total_return
    
    # Strategia 2: Mean Reversion
    signal = np.where(returns < returns.mean(), 1, -1)
    strategy_returns = signal[:-1] * returns[1:]
    strategy_performance = (1 + strategy_returns).prod() - 1
    
    print(f"  Buy & Hold: {buy_hold*100:.2f}%")
    print(f"  Mean Reversion: {strategy_performance*100:.2f}%")
    print(f"  ✓ Strategia Mean Reversion jest {'LEPSZA' if strategy_performance > buy_hold else 'GORSZA'}")
    
    print("\n" + "=" * 60)
    print("FFN GOTOWY DO UŻYTKU")
    print("=" * 60)

except ImportError:
    print("\n⚠ FFN nie zainstalowany")
    print("Instalacja: pip install ffn")
