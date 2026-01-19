#!/usr/bin/env python3
"""
🚀 HAMSTER TERMINAL - ENHANCED API SERVER WITH STYLE SWITCHER
Serwuje Bloomberg clean dashboarda z API integration
Obsługuje multiple themes i real-time data
"""

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import requests
import json
import threading
import time
from datetime import datetime
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Cache for market data
cache = {
    'btc_price': 0,
    'btc_change_24h': 0,
    'eth_price': 0,
    'btc_volume': 0,
    'btc_market_cap': 0,
    'fear_greed': 0,
    'last_update': None,
    'timestamp': 0
}

# ========== DATA FETCHERS ==========

def fetch_binance_data():
    """Fetch real-time data from Binance"""
    try:
        # BTC Price
        btc_resp = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr',
            params={'symbol': 'BTCUSDT'},
            timeout=5
        )
        if btc_resp.status_code == 200:
            btc_data = btc_resp.json()
            cache['btc_price'] = float(btc_data['lastPrice'])
            cache['btc_change_24h'] = float(btc_data['priceChangePercent'])
            cache['btc_volume'] = float(btc_data['quoteAssetVolume'])
            logger.info(f"✅ BTC: ${cache['btc_price']:,.2f} ({cache['btc_change_24h']:+.2f}%)")
        
        # Market cap (from CoinGecko)
        cg_resp = requests.get(
            'https://api.coingecko.com/api/v3/simple/data',
            params={
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_market_cap': 'true'
            },
            timeout=5
        )
        if cg_resp.status_code == 200:
            cg_data = cg_resp.json()
            if 'bitcoin' in cg_data and 'usd_market_cap' in cg_data['bitcoin']:
                cache['btc_market_cap'] = cg_data['bitcoin']['usd_market_cap']
        
        # ETH Price
        eth_resp = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr',
            params={'symbol': 'ETHUSDT'},
            timeout=5
        )
        if eth_resp.status_code == 200:
            eth_data = eth_resp.json()
            cache['eth_price'] = float(eth_data['lastPrice'])
        
        return True
    except Exception as e:
        logger.error(f"❌ Binance fetch error: {e}")
        return False

def fetch_fear_greed():
    """Fetch Fear & Greed Index"""
    try:
        resp = requests.get(
            'https://api.alternative.me/fng/?limit=1',
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data['data'] and len(data['data']) > 0:
                cache['fear_greed'] = int(data['data'][0]['value'])
                logger.info(f"✅ Fear & Greed: {cache['fear_greed']}")
                return True
    except Exception as e:
        logger.error(f"❌ Fear & Greed fetch error: {e}")
    return False

def data_update_loop():
    """Background thread to update data every 30 seconds"""
    logger.info("🔄 Starting background data update thread...")
    while True:
        try:
            fetch_binance_data()
            fetch_fear_greed()
            cache['last_update'] = datetime.now().isoformat()
            cache['timestamp'] = time.time()
            time.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"❌ Update loop error: {e}")
            time.sleep(30)

# ========== API ENDPOINTS ==========

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'Hamster Terminal - Bloomberg Clean API',
        'version': '2.0',
        'status': 'active',
        'endpoints': {
            '/api/binance/summary': 'Get BTC/ETH prices and market data',
            '/api/fear-greed': 'Get Fear & Greed Index',
            '/api/status': 'Get API server status',
            '/dashboard': 'Load Bloomberg dashboard with API'
        }
    })

@app.route('/api/binance/summary')
def binance_summary():
    """Get BTC/ETH market summary"""
    return jsonify({
        'ok': True,
        'btcPrice': cache['btc_price'],
        'btcChange24h': cache['btc_change_24h'],
        'btcVolume': cache['btc_volume'],
        'btcMarketCap': cache['btc_market_cap'],
        'ethPrice': cache['eth_price'],
        'timestamp': cache['timestamp'],
        'lastUpdate': cache['last_update']
    })

@app.route('/api/fear-greed')
def fear_greed():
    """Get Fear & Greed Index"""
    return jsonify({
        'ok': True,
        'fear_greed': cache['fear_greed'],
        'timestamp': cache['timestamp']
    })

@app.route('/api/status')
def status():
    """Get API server status"""
    return jsonify({
        'ok': True,
        'status': 'running',
        'cache': cache,
        'uptime_seconds': int(time.time() - cache['timestamp']) if cache['timestamp'] else 0
    })

@app.route('/dashboard')
def dashboard():
    """Serve the Bloomberg dashboard HTML"""
    try:
        with open('demo_bloomberg_with_api.html', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "Dashboard file not found", 404

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ========== MAIN ==========

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 HAMSTER TERMINAL - BLOOMBERG CLEAN API SERVER v2.0")
    print("=" * 80)
    print(f"Server: http://0.0.0.0:5000")
    print(f"Dashboard: http://localhost:5000/dashboard")
    print(f"API Docs: http://localhost:5000/")
    print("")
    print("📡 Real-time data sources:")
    print("  • Binance API (BTC/ETH prices, volume)")
    print("  • CoinGecko API (Market cap)")
    print("  • Alternative.me (Fear & Greed Index)")
    print("")
    print("🔄 Data update interval: 30 seconds")
    print("=" * 80)
    print("")
    
    # Start background data updater
    update_thread = threading.Thread(target=data_update_loop, daemon=True)
    update_thread.start()
    
    # Initial data fetch
    fetch_binance_data()
    fetch_fear_greed()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
