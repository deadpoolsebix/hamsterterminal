#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Użycie FinancePy - Wycena Instrumentów Finansowych
Machine Learning Bot - Część 2
"""

import numpy as np
from datetime import datetime, timedelta

print("=" * 60)
print("FINANCEPY - WYCENA INSTRUMENTÓW")
print("=" * 60)

try:
    from financepy.products.rates import Bond
    from financepy.products.equity import EquityOption
    from financepy.curves.discount_curve import DiscountCurve
    from financepy.utils.date import Date
    
    print("\n✓ FinancePy załadowany")
    
    # Przykład 1: Wycena Obligacji
    print("\n[1] WYCENA OBLIGACJI")
    print("-" * 40)
    try:
        # Parametry obligacji
        settlement_date = Date(2024, 1, 1)
        maturity_date = Date(2034, 1, 1)  # 10-letnia
        coupon_rate = 0.05  # 5% coupon
        face_value = 100
        
        # Stopa dyskontowa
        discount_rate = 0.04  # 4%
        
        bond = Bond(maturity_date, coupon_rate, face_value)
        
        # Kalkulacja ceny
        # Price ≈ PV of coupon payments + PV of face value
        print(f"  Termin zapadalności: {maturity_date}")
        print(f"  Kupon: {coupon_rate*100}%")
        print(f"  Wartość nominalna: ${face_value}")
        print(f"  Stopa dyskontowa: {discount_rate*100}%")
        
        # Szacunkowa cena
        years = 10
        annual_coupon = face_value * coupon_rate
        coupon_pv = sum([annual_coupon / ((1 + discount_rate) ** i) for i in range(1, years + 1)])
        face_pv = face_value / ((1 + discount_rate) ** years)
        bond_price = coupon_pv + face_pv
        
        print(f"  ✓ Cena obligacji: ${bond_price:.2f}")
        print(f"  Zwrot z kuponów: ${coupon_pv:.2f}")
        print(f"  Zwrot z nominału: ${face_pv:.2f}")
    except Exception as e:
        print(f"  ⚠ Błąd: {e}")
    
    # Przykład 2: Wycena Opcji (Black-Scholes)
    print("\n[2] WYCENA OPCJI (BLACK-SCHOLES)")
    print("-" * 40)
    try:
        from financepy.models.option_pricer import BlackScholes
        
        # Parametry opcji
        S0 = 100  # Cena początkowa akcji
        K = 100   # Strike price
        r = 0.05  # Risk-free rate
        sigma = 0.2  # Zmienność
        T = 1     # Czas do wygaśnięcia (1 rok)
        
        # Call option
        from scipy.stats import norm
        
        d1 = (np.log(S0 / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        call_price = S0 * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S0 * norm.cdf(-d1)
        
        print(f"  Cena akcji: ${S0}")
        print(f"  Strike: ${K}")
        print(f"  Zmienność (sigma): {sigma*100}%")
        print(f"  Czas do wygaśnięcia: {T} rok")
        print(f"  ✓ Cena CALL: ${call_price:.2f}")
        print(f"  ✓ Cena PUT: ${put_price:.2f}")
    except Exception as e:
        print(f"  ⚠ Błąd: {e}")
    
    # Przykład 3: Greeks
    print("\n[3] GRECKIE (GREEKS)")
    print("-" * 40)
    try:
        # Delta
        delta_call = norm.cdf(d1)
        delta_put = delta_call - 1
        
        # Gamma
        gamma = norm.pdf(d1) / (S0 * sigma * np.sqrt(T))
        
        # Vega
        vega = S0 * norm.pdf(d1) * np.sqrt(T) / 100
        
        # Theta
        theta_call = (-S0 * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - 
                      r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        
        print(f"  Delta (CALL): {delta_call:.4f}")
        print(f"  Delta (PUT): {delta_put:.4f}")
        print(f"  Gamma: {gamma:.4f}")
        print(f"  Vega: {vega:.4f}")
        print(f"  Theta (CALL): {theta_call:.4f}")
        print(f"  ✓ Greeks obliczone")
    except Exception as e:
        print(f"  ⚠ Błąd: {e}")
    
    print("\n" + "=" * 60)
    print("FINANCEPY GOTOWY DO UŻYTKU")
    print("=" * 60)

except ImportError as e:
    print(f"\n⚠ Błąd importu: {e}")
    print("Instalacja: pip install financepy")
