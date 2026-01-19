#!/usr/bin/env python3
"""
Test Alpaca SDK setup
Sprawdza czy SDK jest zainstalowane i klucze działają
"""

print("=" * 60)
print("🔍 ALPACA SDK TEST")
print("=" * 60)

# Test 1: Check if SDK is installed
print("\n1️⃣ Checking alpaca-py installation...")
try:
    from alpaca.data.live import StockDataStream
    from alpaca.data.models import Trade
    print("   ✅ alpaca-py installed!")
except ImportError as e:
    print(f"   ❌ alpaca-py NOT installed: {e}")
    print("   Run: pip install alpaca-py")
    exit(1)

# Test 2: Check API keys
print("\n2️⃣ Checking API keys...")
import os

ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', 'YOUR_KEY_HERE')
ALPACA_SECRET = os.getenv('ALPACA_SECRET', 'YOUR_SECRET_HERE')

if ALPACA_API_KEY == 'YOUR_KEY_HERE':
    print("   ⚠️  API keys NOT set")
    print("   ")
    print("   📌 HOW TO GET KEYS:")
    print("   1. Go to: https://alpaca.markets")
    print("   2. Sign up for FREE Paper Trading account")
    print("   3. Dashboard → API Keys → Generate new key")
    print("   4. Copy API Key ID and Secret Key")
    print("   5. Edit api_pro.py:")
    print("      ALPACA_API_KEY = 'PK...'")
    print("      ALPACA_SECRET = '...'")
    print("")
else:
    print(f"   ✅ API Key: {ALPACA_API_KEY[:10]}...")
    print(f"   ✅ Secret: {'*' * 20}")

# Test 3: Try to connect (if keys are set)
if ALPACA_API_KEY != 'YOUR_KEY_HERE':
    print("\n3️⃣ Testing connection...")
    try:
        from alpaca.trading.client import TradingClient
        
        client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET, paper=True)
        account = client.get_account()
        
        print(f"   ✅ Connection successful!")
        print(f"   📊 Account status: {account.status}")
        print(f"   💰 Buying power: ${float(account.buying_power):,.2f}")
        print(f"   🏦 Portfolio: ${float(account.equity):,.2f}")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("   Check if your keys are correct")
else:
    print("\n3️⃣ Skipping connection test (no keys set)")

print("\n" + "=" * 60)
print("📋 NEXT STEPS:")
if ALPACA_API_KEY == 'YOUR_KEY_HERE':
    print("→ Get API keys from https://alpaca.markets")
    print("→ Update api_pro.py with your keys")
else:
    print("→ Start the server: python api_pro.py")
    print("→ Open dashboard: docs/index.html")
print("=" * 60)
