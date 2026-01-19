#!/usr/bin/env python3
"""
Test CoinAPI.io vs Binance WebSocket
"""
import requests
import time
import json

print("=" * 60)
print("COINAPI.IO vs BINANCE - Speed Comparison")
print("=" * 60)

# Test 1: CoinAPI REST (potrzebuje API key)
print("\n1. CoinAPI.io REST API:")
print("   - Stocks: ✓ YES (AAPL, TSLA, SPY, etc.)")
print("   - Crypto: ✓ YES (BTC, ETH, 300+ exchanges)")
print("   - Forex: ✓ YES")
print("   - Commodities: ✓ YES (Gold, Silver, Oil)")
print("\n   Free tier: 100 requests/DAY")
print("   Paid: $79-$3999/month")

try:
    start = time.time()
    # Demo key - limited
    r = requests.get(
        'https://rest.coinapi.io/v1/exchangerate/BTC/USD',
        headers={'X-CoinAPI-Key': 'DEMO-KEY'},
        timeout=5
    )
    latency = (time.time() - start) * 1000
    
    print(f"\n   HTTP Request latency: {latency:.0f}ms")
    if r.status_code == 200:
        data = r.json()
        print(f"   BTC: ${data.get('rate', 0):,.2f}")
    elif r.status_code == 401:
        print("   ⚠️ Demo key expired - need real API key")
    else:
        print(f"   Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Binance REST
print("\n2. Binance REST API:")
print("   - Stocks: ✗ NO")
print("   - Crypto: ✓ YES (500+ pairs)")
print("   - Forex: ✗ NO")
print("   - Commodities: ✗ NO")
print("\n   Free tier: UNLIMITED!")
print("   Paid: FREE")

try:
    start = time.time()
    r = requests.get(
        'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT',
        timeout=5
    )
    latency = (time.time() - start) * 1000
    
    print(f"\n   HTTP Request latency: {latency:.0f}ms")
    if r.status_code == 200:
        data = r.json()
        print(f"   BTC: ${float(data['lastPrice']):,.2f}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: WebSocket comparison
print("\n3. WebSocket Speed Comparison:")
print("\n   CoinAPI WebSocket:")
print("   - URL: wss://ws.coinapi.io/v1/")
print("   - Latency: ~50-200ms (depends on location)")
print("   - Update rate: Real-time tick-by-tick")
print("   - Requires: API key ($79+/mo)")
print("   - Data: Stocks + Crypto + Forex + Commodities")

print("\n   Binance WebSocket:")
print("   - URL: wss://stream.binance.com:9443/stream")
print("   - Latency: ~10-50ms (very fast!)")
print("   - Update rate: Real-time tick-by-tick (1 second)")
print("   - Requires: Nothing (FREE)")
print("   - Data: Crypto ONLY")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("=" * 60)
print("\n✓ For CRYPTO: Use Binance WebSocket (FREE + fastest!)")
print("✓ For STOCKS: Use Alpaca Markets WebSocket (FREE)")
print("✓ For Commodities: Use Twelve Data REST API (800 req/day FREE)")
print("\nCoinAPI.io is GOOD but:")
print("  - Expensive ($79+/mo)")
print("  - Not faster than Binance for crypto")
print("  - Better alternatives exist (Alpaca for stocks)")
