"""
💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀
Public Dashboard - Works 24/7!

Najprostsze rozwiązanie - tylko Python, bez dodatkowych instalacji!
"""

from flask import Flask, send_file, send_from_directory, jsonify, request
import os
import time
import requests

# Lazy import for optional dependency
_yf = None

def _get_yf():
    global _yf
    if _yf is None:
        try:
            import yfinance as yf
            _yf = yf
        except Exception as e:
            _yf = e  # store exception to report cleanly
    return _yf

app = Flask(__name__, static_folder='.')


def _http_json(url, params=None, timeout=6):
    """Small helper to fetch JSON with timeout and clear error reporting."""
    try:
        res = requests.get(url, params=params or {}, timeout=timeout)
        res.raise_for_status()
        return res.json(), None
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    return send_file('professional_dashboard_final.html')

@app.route('/professional_dashboard_final.html')
def dashboard():
    return send_file('professional_dashboard_final.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/commodities')
def api_commodities():
    """Return live Gold (XAU) and Silver (XAG) prices from Yahoo Finance.

    Symbols used:
    - Gold Futures: GC=F
    - Silver Futures: SI=F
    """
    yf = _get_yf()
    if isinstance(yf, Exception):
        return jsonify({
            "ok": False,
            "error": "yfinance not available",
            "detail": str(yf)
        }), 500

    try:
        gold = yf.Ticker("GC=F")
        silver = yf.Ticker("SI=F")

        # Method 1: fast_info (CORRECT KEYS: lastPrice, previousClose)
        gp = None
        gprev = None
        sp = None
        sprev = None
        
        if hasattr(gold, "fast_info"):
            gp = gold.fast_info.get("lastPrice")  # NOT "last_price"
            gprev = gold.fast_info.get("previousClose")  # NOT "previous_close"
        
        if hasattr(silver, "fast_info"):
            sp = silver.fast_info.get("lastPrice")
            sprev = silver.fast_info.get("previousClose")
        
        # Method 2: .info fallback
        if gp is None:
            gp = gold.info.get("regularMarketPrice")
        if sp is None:
            sp = silver.info.get("regularMarketPrice")
        if gprev is None:
            gprev = gold.info.get("regularMarketPreviousClose", gp)
        if sprev is None:
            sprev = silver.info.get("regularMarketPreviousClose", sp)

        # Method 3: history fallback (most reliable for futures)
        if gp is None:
            try:
                gh = gold.history(period="5d")
                if not gh.empty:
                    gp = float(gh['Close'].iloc[-1])
                    if len(gh) > 1:
                        gprev = float(gh['Close'].iloc[-2])
            except:
                pass
        
        if sp is None:
            try:
                sh = silver.history(period="5d")
                if not sh.empty:
                    sp = float(sh['Close'].iloc[-1])
                    if len(sh) > 1:
                        sprev = float(sh['Close'].iloc[-2])
            except:
                pass

        # Validate numeric
        gold_price = float(gp) if gp is not None else None
        silver_price = float(sp) if sp is not None else None
        gold_prev = float(gprev) if gprev is not None else gold_price
        silver_prev = float(sprev) if sprev is not None else silver_price

        if gold_price is None or silver_price is None:
            return jsonify({
                "ok": False,
                "error": "Missing price data after all fallbacks",
                "gold": gold_price,
                "silver": silver_price
            }), 502

        return jsonify({
            "ok": True,
            "gold": gold_price,
            "gold_previous": gold_prev,
            "silver": silver_price,
            "silver_previous": silver_prev,
            "source": "yfinance",
            "ts": int(time.time())
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": "fetch_failed",
            "detail": str(e)
        }), 500


# =====================
# PROXY: BINANCE + COINGECKO + FNG (CORS SAFE)
# =====================

@app.route('/api/binance/summary')
def api_binance_summary():
    symbol_btc = request.args.get('btc', 'BTCUSDT')
    symbol_eth = request.args.get('eth', 'ETHUSDT')

    base = 'https://api.binance.com/api/v3'

    btc24, err = _http_json(f"{base}/ticker/24hr", params={'symbol': symbol_btc})
    if err:
        print(f"❌ BTC24h error: {err}")
        return jsonify({"ok": False, "error": "btc24", "detail": err}), 502

    btc_price, err = _http_json(f"{base}/ticker/price", params={'symbol': symbol_btc})
    if err:
        print(f"❌ BTC price error: {err}")
        return jsonify({"ok": False, "error": "btc_price", "detail": err}), 502

    eth24, err = _http_json(f"{base}/ticker/24hr", params={'symbol': symbol_eth})
    if err:
        print(f"❌ ETH24h error: {err}")
        return jsonify({"ok": False, "error": "eth24", "detail": err}), 502

    eth_price, err = _http_json(f"{base}/ticker/price", params={'symbol': symbol_eth})
    if err:
        print(f"❌ ETH price error: {err}")
        return jsonify({"ok": False, "error": "eth_price", "detail": err}), 502

    try:
        payload = {
            "ok": True,
            "btcPrice": float(btc_price.get('price', 0)),
            "btcChange24h": float(btc24.get('priceChangePercent', 0)),
            "btcVolume24h": float(btc24.get('quoteVolume', 0)),
            "ethPrice": float(eth_price.get('price', 0)),
            "ethChange24h": float(eth24.get('priceChangePercent', 0)),
            "ethVolume24h": float(eth24.get('quoteVolume', 0)),
        }
        print(f"✅ BTC: ${payload['btcPrice']:.2f} ({payload['btcChange24h']:+.2f}%) | ETH: ${payload['ethPrice']:.2f}")
        return jsonify(payload)
    except Exception as e:
        print(f"❌ Parse error: {str(e)}")
        return jsonify({"ok": False, "error": "parse", "detail": str(e)}), 500


@app.route('/api/binance/price')
def api_binance_price():
    symbol = request.args.get('symbol', 'BTCUSDT')
    data, err = _http_json('https://api.binance.com/api/v3/ticker/price', params={'symbol': symbol})
    if err:
        return jsonify({"ok": False, "error": err}), 502
    try:
        return jsonify({"ok": True, "price": float(data.get('price', 0))})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/binance/funding')
def api_binance_funding():
    symbol = request.args.get('symbol', 'BTCUSDT')
    data, err = _http_json('https://api.binance.com/fapi/v1/premiumIndex', params={'symbol': symbol})
    if err:
        return jsonify({"ok": False, "error": err}), 502
    try:
        return jsonify({
            "ok": True,
            "lastFundingRate": float(data.get('lastFundingRate', 0)),
            "nextFundingTime": data.get('nextFundingTime')
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/binance/oi')
def api_binance_oi():
    symbol = request.args.get('symbol', 'BTCUSDT')
    data, err = _http_json('https://api.binance.com/fapi/v1/openInterest', params={'symbol': symbol})
    if err:
        return jsonify({"ok": False, "error": err}), 502
    try:
        return jsonify({"ok": True, "openInterest": float(data.get('openInterest', 0))})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/coingecko/simple')
def api_coingecko_simple():
    params = {
        'ids': 'bitcoin,ethereum',
        'vs_currencies': 'usd',
        'include_market_cap': 'true',
        'include_24hr_vol': 'true',
        'include_24hr_change': 'true'
    }
    data, err = _http_json('https://api.coingecko.com/api/v3/simple/price', params=params)
    if err:
        return jsonify({"ok": False, "error": err}), 502
    return jsonify({"ok": True, "data": data})


@app.route('/api/fng')
def api_fng():
    data, err = _http_json('https://api.alternative.me/fng/', params={'limit': 1})
    if err:
        return jsonify({"ok": False, "error": err}), 502
    return jsonify({"ok": True, "data": data})

@app.route('/health')
def health():
    return jsonify({"ok": True, "status": "running"})

if __name__ == '__main__':
    print("=" * 70)
    print("💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀".center(70))
    print("=" * 70)
    print()
    print("✅ Dashboard Server is RUNNING!")
    print()
    print("📱 ACCESS OPTIONS:")
    print("-" * 70)
    print()
    print("1️⃣  ON THIS COMPUTER:")
    print("    http://localhost:8080")
    print()
    print("2️⃣  ON YOUR PHONE/TABLET (same WiFi):")
    print("    http://192.168.1.132:8080")
    print()
    print("3️⃣  PUBLIC ACCESS (anyone, anywhere):")
    print("    Follow these steps:")
    print()
    print("    A) Keep this window OPEN")
    print("    B) Open NEW terminal and run:")
    print("       ssh -R 80:localhost:8080 serveo.net")
    print()
    print("    C) You'll get a PUBLIC URL like:")
    print("       https://xyz123.serveo.net")
    print()
    print("    D) Share that URL with anyone!")
    print()
    print("=" * 70)
    print("⚠️  KEEP THIS WINDOW OPEN to keep dashboard running")
    print("    Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    # Run Flask
    port = int(os.environ.get('PORT', '8080'))
    app.run(host='0.0.0.0', port=port, debug=False)
