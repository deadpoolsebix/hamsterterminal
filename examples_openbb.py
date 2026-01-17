#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Użycie OpenBB - Pobieranie Danych Finansowych
Machine Learning Bot - Część 1
"""

print("=" * 60)
print("OPENBB - POBIERANIE DANYCH FINANSOWYCH")
print("=" * 60)

try:
    from openbb import obb
    print("\n✓ OpenBB załadowany")
    
    # Konfiguracja
    print("\n[1] Pobieranie danych akcji (AAPL)...")
    try:
        stocks_data = obb.equity.price.historical(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        print(f"✓ Pobrano {len(stocks_data)} rekordów AAPL")
        if hasattr(stocks_data, 'head'):
            print(stocks_data.head())
    except Exception as e:
        print(f"⚠ Błąd AAPL: {e}")
    
    # Kryptowaluty
    print("\n[2] Pobieranie danych kryptowalut (BTC)...")
    try:
        crypto_data = obb.crypto.price.historical(
            symbol="BTC",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        print(f"✓ Pobrano {len(crypto_data)} rekordów BTC")
    except Exception as e:
        print(f"⚠ Błąd BTC: {e}")
    
    # Forex
    print("\n[3] Pobieranie danych walut (EURUSD)...")
    try:
        forex_data = obb.forex.price.historical(
            symbol="EURUSD",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        print(f"✓ Pobrano {len(forex_data)} rekordów EURUSD")
    except Exception as e:
        print(f"⚠ Błąd EURUSD: {e}")
    
    # Wiadomości
    print("\n[4] Pobieranie wiadomości finansowych...")
    try:
        news = obb.news.world(limit=5)
        print(f"✓ Pobrano {len(news)} wiadomości")
        for i, article in enumerate(news, 1):
            print(f"  {i}. {article[:60]}...")
    except Exception as e:
        print(f"⚠ Błąd news: {e}")
    
    # Dane ekonomiczne
    print("\n[5] Pobieranie danych ekonomicznych (GDP USA)...")
    try:
        gdp = obb.economy.gdp_growth(provider="fred")
        print(f"✓ Dane ekonomiczne dostępne")
    except Exception as e:
        print(f"⚠ Błąd economy: {e}")
    
    print("\n" + "=" * 60)
    print("OPENBB GOTOWY DO UŻYTKU")
    print("=" * 60)

except ImportError:
    print("\n⚠ OpenBB nie zainstalowany")
    print("Instalacja: pip install openbb")
