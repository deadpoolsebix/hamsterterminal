#!/usr/bin/env python3
"""
Test Finnhub API setup
Sprawdza czy API key działa i pobiera rzeczywiste dane
"""

import requests
import json

print("=" * 60)
print("🔍 FINNHUB API TEST")
print("=" * 60)

print("\n1️⃣ Get FREE API key...")
print("   Go to: https://finnhub.io/register")
print("   ✅ NO documents needed, NO KYC!")
print("   ✅ Get key in 30 seconds!")
print("")

FINNHUB_API_KEY = input("📌 Paste your Finnhub API key (or press Enter to skip): ").strip()

if not FINNHUB_API_KEY:
    print("\n⚠️  Skipping test - no API key provided")
    print("\n📋 NEXT STEPS:")
    print("   1. Go to: https://finnhub.io/register")
    print("   2. Sign up (email only!)")
    print("   3. Get API key from dashboard")
    print("   4. Run this script again and paste the key")
    exit(0)

print("\n2️⃣ Testing API connection...")

# Test with SPY (S&P 500 ETF)
symbols = ['SPY', 'AAPL']
base_url = "https://finnhub.io/api/v1"

for symbol in symbols:
    try:
        # Get last quote
        response = requests.get(
            f"{base_url}/quote",
            params={"symbol": symbol, "token": FINNHUB_API_KEY},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            price = data.get('c', 0)  # current price
            change = data.get('d', 0)  # change
            change_pct = data.get('dp', 0)  # change percent
            
            print(f"   ✅ {symbol}: ${price:.2f} {change:+.2f} ({change_pct:+.2f}%)")
        else:
            print(f"   ❌ {symbol}: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ {symbol}: {e}")

print("\n" + "=" * 60)
print("✅ API KEY READY!")
print("=" * 60)
print(f"\nAPI Key: {FINNHUB_API_KEY[:15]}...")
print("\n📋 NEXT STEP:")
print("   Edit api_pro.py and add:")
print(f"   FINNHUB_API_KEY = '{FINNHUB_API_KEY}'")
print("")
print("Then run: python api_pro.py")
print("=" * 60)
