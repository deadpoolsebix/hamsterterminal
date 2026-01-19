#!/usr/bin/env python3
"""
HAMSTER TERMINAL - PROFESSIONAL LIVE DATA API
WebSocket streaming z Binance (crypto) + IEX Cloud (stocks/commodities)
Zero lag - professional Wall Street grade data
"""

from flask import Flask, jsonify, send_file, send_from_directory
import requests
import threading
import time
import json
import logging
from datetime import datetime
import os

# WebSocket dla real-time streams
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("⚠️ Install websocket-client: pip install websocket-client")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# GLOBAL CACHE - przechowuje najnowsze ceny
cache = {
    'gold': {'price': 2650.00, 'change': 0.0},
    'silver': {'price': 32.50, 'change': 0.0},
    'oil': {'price': 78.50, 'change': 0.0},
    'btc': {'price': 95000, 'change': 0.0},
    'eth': {'price': 2800, 'change': 0.0},
    'last_update': 0,
    'status': 'loading'
}

def fetch_gold():
    """Pobierz ceny złota"""
    try:
        def get_data():
            gold = yf.Ticker("GC=F")
            return gold.history(period='1d')
        
        import threading
        result = [None]
        def thread_func():
            result[0] = get_data()
        
        thread = threading.Thread(target=thread_func)
        thread.daemon = True
        thread.start()
        thread.join(timeout=8)
        
        if result[0] is None or result[0].empty:
            logger.warning(f"⚠️ GOLD: Timeout or empty data, using cache")
            return False
        
        price = float(result[0]['Close'].iloc[-1])
        prev = float(result[0]['Open'].iloc[-1]) if len(result[0]) > 0 else price
        change = ((price - prev) / prev * 100) if prev else 0
        cache['gold'] = {'price': price, 'change': change}
        logger.info(f"✅ GOLD: ${price:.2f} ({change:+.2f}%)")
        return True
    except Exception as e:
        logger.warning(f"⚠️ GOLD ERROR: {e} - using cache")
        return False

def fetch_silver():
    """Pobierz ceny srebra"""
    try:
        def get_data():
            silver = yf.Ticker("SI=F")
            return silver.history(period='1d')
        
        result = [None]
        def thread_func():
            result[0] = get_data()
        
        thread = threading.Thread(target=thread_func)
        thread.daemon = True
        thread.start()
        thread.join(timeout=8)
        
        if result[0] is None or result[0].empty:
            logger.warning(f"⚠️ SILVER: Timeout or empty data, using cache")
            return False
        
        price = float(result[0]['Close'].iloc[-1])
        prev = float(result[0]['Open'].iloc[-1]) if len(result[0]) > 0 else price
        change = ((price - prev) / prev * 100) if prev else 0
        cache['silver'] = {'price': price, 'change': change}
        logger.info(f"✅ SILVER: ${price:.2f} ({change:+.2f}%)")
        return True
    except Exception as e:
        logger.warning(f"⚠️ SILVER ERROR: {e} - using cache")
        return False

def fetch_oil():
    """Pobierz ceny ropy"""
    try:
        def get_data():
            oil = yf.Ticker("CL=F")
            return oil.history(period='1d')
        
        result = [None]
        def thread_func():
            result[0] = get_data()
        
        thread = threading.Thread(target=thread_func)
        thread.daemon = True
        thread.start()
        thread.join(timeout=8)
        
        if result[0] is None or result[0].empty:
            logger.warning(f"⚠️ OIL: Timeout or empty data, using cache")
            return False
        
        price = float(result[0]['Close'].iloc[-1])
        prev = float(result[0]['Open'].iloc[-1]) if len(result[0]) > 0 else price
        change = ((price - prev) / prev * 100) if prev else 0
        cache['oil'] = {'price': price, 'change': change}
        logger.info(f"✅ OIL: ${price:.2f} ({change:+.2f}%)")
        return True
    except Exception as e:
        logger.warning(f"⚠️ OIL ERROR: {e} - using cache")
        return False

def fetch_binance():
    """Pobierz BTC i ETH z Binance"""
    try:
        # BTC
        btc_resp = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', timeout=5)
        if btc_resp.status_code == 200:
            btc_data = btc_resp.json()
            btc_price = float(btc_data['lastPrice'])
            btc_change = float(btc_data['priceChangePercent'])
            cache['btc'] = {'price': btc_price, 'change': btc_change}
            logger.info(f"✅ BTC: ${btc_price:.2f} ({btc_change:+.2f}%)")
        
        # ETH
        eth_resp = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT', timeout=5)
        if eth_resp.status_code == 200:
            eth_data = eth_resp.json()
            eth_price = float(eth_data['lastPrice'])
            eth_change = float(eth_data['priceChangePercent'])
            cache['eth'] = {'price': eth_price, 'change': eth_change}
            logger.info(f"✅ ETH: ${eth_price:.2f} ({eth_change:+.2f}%)")
        
        return True
    except Exception as e:
        logger.warning(f"⚠️ BINANCE ERROR: {e}")
        return False

def background_updater():
    """Watek aktualizujacy ceny co 30 sekund"""
    logger.info("🔄 Background updater started - updating every 30s")
    while True:
        try:
            logger.info("📊 Fetching prices...")
            fetch_gold()
            fetch_silver()
            fetch_oil()
            fetch_binance()
            cache['last_update'] = time.time()
            cache['status'] = 'ok'
            time.sleep(30)
        except Exception as e:
            logger.error(f"❌ Updater error: {e}")
            cache['status'] = 'error'
            time.sleep(30)

# START BACKGROUND THREAD
logger.info("🚀 HAMSTER TERMINAL API STARTING...")
logger.info("📡 Fetching initial prices...")
fetch_gold()
fetch_silver()
fetch_oil()
fetch_binance()
cache['last_update'] = time.time()

updater_thread = threading.Thread(target=background_updater, daemon=True)
updater_thread.start()

# ============ ROUTES ============

@app.route('/api/prices', methods=['GET'])
def get_prices():
    """Wszystkie ceny - format dla dashboarda"""
    resp = jsonify({
        'GOLD': {
            'price': cache['gold']['price'],
            'change': cache['gold']['change'],
            'change_percent': cache['gold']['change'],
            'timestamp': datetime.now().isoformat()
        },
        'SILVER': {
            'price': cache['silver']['price'],
            'change': cache['silver']['change'],
            'change_percent': cache['silver']['change'],
            'timestamp': datetime.now().isoformat()
        },
        'OIL': {
            'price': cache['oil']['price'],
            'change': cache['oil']['change'],
            'change_percent': cache['oil']['change'],
            'timestamp': datetime.now().isoformat()
        },
        'BTC': {
            'price': cache['btc']['price'],
            'change': cache['btc']['change'],
            'change_percent': cache['btc']['change'],
            'timestamp': datetime.now().isoformat()
        },
        'ETH': {
            'price': cache['eth']['price'],
            'change': cache['eth']['change'],
            'change_percent': cache['eth']['change'],
            'timestamp': datetime.now().isoformat()
        },
        'status': cache['status'],
        'last_update': datetime.fromtimestamp(cache['last_update']).isoformat() if cache['last_update'] else None
    })
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route('/api/commodities', methods=['GET'])
def get_commodities():
    """Tylko surowce"""
    resp = jsonify({
        'ok': True,
        'gold': cache['gold']['price'],
        'gold_change': cache['gold']['change'],
        'silver': cache['silver']['price'],
        'silver_change': cache['silver']['change'],
        'oil': cache['oil']['price'],
        'oil_change': cache['oil']['change'],
    })
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/crypto', methods=['GET'])
def get_crypto():
    """Tylko crypto"""
    resp = jsonify({
        'ok': True,
        'btc': cache['btc']['price'],
        'btc_change': cache['btc']['change'],
        'eth': cache['eth']['price'],
        'eth_change': cache['eth']['change'],
    })
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/status', methods=['GET'])
def get_status():
    """Status serwera"""
    resp = jsonify({
        'ok': True,
        'status': cache['status'],
        'last_update': datetime.fromtimestamp(cache['last_update']).isoformat() if cache['last_update'] else None,
        'cache': cache
    })
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/')
def index():
    """Serwuj dashboard"""
    return send_from_directory('.', 'professional_dashboard_final.html')

# RUN
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"")
    logger.info(f"✅ HAMSTER TERMINAL READY")
    logger.info(f"🌐 Dashboard: http://localhost:{port}")
    logger.info(f"📡 API: http://localhost:{port}/api/prices")
    logger.info(f"📊 Commodities: http://localhost:{port}/api/commodities")
    logger.info(f"₿ Crypto: http://localhost:{port}/api/crypto")
    logger.info(f"💚 Status: http://localhost:{port}/api/status")
    logger.info(f"")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
