#!/usr/bin/env python3
"""
🚀 HAMSTER TERMINAL - REAL-TIME API SERVER
Serwuje rzeczywiste dane z Binance, CoinGecko, Alternative.me
Endpoints dla dashboarda (localhost:5000)
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
import threading
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all endpoints

# ============ CACHE SYSTEM ============
cache = {
    'btc_price': 95501.20,
    'btc_change': 2.45,
    'eth_price': 2845.32,
    'eth_change': 1.80,
    'fear_greed': 62,
    'volume_24h': 24500000000,
    'funding_rate': 0.0082,
    'open_interest': 12400000000,
    'last_update': None,
    'timestamp': 0
}

# ============ BINANCE API FUNCTIONS ============

def fetch_binance_prices():
    """Fetch real BTC and ETH prices from Binance"""
    try:
        # Get BTC/USDT
        btc_response = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT',
            timeout=5
        )
        if btc_response.status_code == 200:
            btc_data = btc_response.json()
            cache['btc_price'] = float(btc_data['lastPrice'])
            cache['btc_change'] = float(btc_data['priceChangePercent'])
            
            # Get 24h volume (using 'volume' key which is base asset volume)
            cache['volume_24h'] = float(btc_data.get('volume', 0)) * cache['btc_price']
            
        # Get ETH/USDT
        eth_response = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT',
            timeout=5
        )
        if eth_response.status_code == 200:
            eth_data = eth_response.json()
            cache['eth_price'] = float(eth_data['lastPrice'])
            cache['eth_change'] = float(eth_data['priceChangePercent'])
            
        logger.info(f"✅ Binance: BTC ${cache['btc_price']:,.2f} ({cache['btc_change']:+.2f}%)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Binance fetch error: {e}")
        return False


def fetch_funding_rate():
    """Fetch BTC Futures funding rate from Binance"""
    try:
        response = requests.get(
            'https://api.binance.com/api/v3/fundingRate?symbol=BTCUSDT&limit=1',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                cache['funding_rate'] = float(data[0]['fundingRate']) * 100
                logger.info(f"✅ Funding rate: {cache['funding_rate']:.4f}%")
                return True
    except Exception as e:
        logger.error(f"❌ Funding rate error: {e}")
    return False


def fetch_open_interest():
    """Fetch BTC Futures open interest from Binance"""
    try:
        response = requests.get(
            'https://api.binance.com/api/v3/openInterest?symbol=BTCUSDT',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data:
                oi_contracts = float(data['openInterest'])
                cache['open_interest'] = oi_contracts * cache['btc_price']
                logger.info(f"✅ Open Interest: ${cache['open_interest']:,.0f}")
                return True
    except Exception as e:
        logger.error(f"❌ Open interest error: {e}")
    return False


# ============ COINGECKO API FUNCTIONS ============

def fetch_fear_greed():
    """Fetch Fear & Greed Index from Alternative.me"""
    try:
        response = requests.get(
            'https://api.alternative.me/fng/?limit=1',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data['data'] and len(data['data']) > 0:
                cache['fear_greed'] = int(data['data'][0]['value'])
                logger.info(f"✅ Fear & Greed: {cache['fear_greed']}")
                return True
    except Exception as e:
        logger.error(f"❌ Fear & Greed error: {e}")
    return False


def fetch_coingecko_data():
    """Fetch crypto data from CoinGecko"""
    try:
        response = requests.get(
            'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if 'bitcoin' in data:
                cache['btc_price'] = data['bitcoin']['usd']
                cache['btc_change'] = data['bitcoin'].get('usd_24h_change', 0)
            if 'ethereum' in data:
                cache['eth_price'] = data['ethereum']['usd']
                cache['eth_change'] = data['ethereum'].get('usd_24h_change', 0)
            logger.info(f"✅ CoinGecko: BTC ${cache['btc_price']:,.2f}")
            return True
    except Exception as e:
        logger.error(f"❌ CoinGecko error: {e}")
    return False


# ============ BACKGROUND UPDATE THREAD ============

def update_data_loop():
    """Background thread to update data every 30 seconds"""
    logger.info("🔄 Starting background data update thread...")
    while True:
        try:
            # Try Binance first (most reliable)
            fetch_binance_prices()
            fetch_funding_rate()
            fetch_open_interest()
            
            # Try Fear & Greed
            fetch_fear_greed()
            
            # Update timestamp
            cache['last_update'] = datetime.now().isoformat()
            cache['timestamp'] = time.time()
            
            time.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            logger.error(f"❌ Update loop error: {e}")
            time.sleep(30)


# Start background thread
update_thread = threading.Thread(target=update_data_loop, daemon=True)
update_thread.start()

# Initial data fetch
logger.info("📡 Fetching initial data...")
fetch_binance_prices()
fetch_funding_rate()
fetch_open_interest()
fetch_fear_greed()

# ============ API ENDPOINTS ============

@app.route('/api/binance/summary', methods=['GET'])
def binance_summary():
    """Get BTC/ETH prices and basic data"""
    return jsonify({
        'ok': True,
        'btcPrice': round(cache['btc_price'], 2),
        'btcChange24h': round(cache['btc_change'], 2),
        'btcVolume24h': int(cache['volume_24h']),
        'ethPrice': round(cache['eth_price'], 2),
        'ethChange24h': round(cache['eth_change'], 2),
        'lastUpdate': cache['last_update']
    })


@app.route('/api/binance/funding', methods=['GET'])
def binance_funding():
    """Get BTC futures funding rate"""
    return jsonify({
        'ok': True,
        'lastFundingRate': cache['funding_rate'] / 100,
        'fundingRatePercent': round(cache['funding_rate'], 4)
    })


@app.route('/api/binance/oi', methods=['GET'])
def binance_oi():
    """Get BTC futures open interest"""
    return jsonify({
        'ok': True,
        'openInterest': cache['open_interest'] / cache['btc_price'],
        'openInterestValue': round(cache['open_interest'], 0)
    })


@app.route('/api/fng', methods=['GET'])
def fear_greed_index():
    """Get Fear & Greed Index"""
    return jsonify({
        'ok': True,
        'data': {
            'data': [
                {
                    'value': str(cache['fear_greed']),
                    'value_classification': 'Greed' if cache['fear_greed'] > 50 else 'Fear',
                    'timestamp': int(cache['timestamp'])
                }
            ]
        }
    })


@app.route('/api/coingecko/simple', methods=['GET'])
def coingecko_simple():
    """Get crypto prices from CoinGecko cache"""
    return jsonify({
        'ok': True,
        'data': {
            'bitcoin': {
                'usd': round(cache['btc_price'], 2),
                'usd_24h_change': round(cache['btc_change'], 2)
            },
            'ethereum': {
                'usd': round(cache['eth_price'], 2),
                'usd_24h_change': round(cache['eth_change'], 2)
            }
        }
    })


@app.route('/api/status', methods=['GET'])
def status():
    """Get API server status"""
    return jsonify({
        'ok': True,
        'status': 'running',
        'last_update': cache['last_update'],
        'cache': {
            'btcPrice': round(cache['btc_price'], 2),
            'btcChange24h': round(cache['btc_change'], 2),
            'ethPrice': round(cache['eth_price'], 2),
            'ethChange24h': round(cache['eth_change'], 2),
            'fearGreed': cache['fear_greed'],
            'fundingRate': round(cache['funding_rate'], 4),
            'volume24h': int(cache['volume_24h'])
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'api-server'}), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint info"""
    return jsonify({
        'name': '🚀 Hamster Terminal API Server',
        'version': '1.0',
        'endpoints': {
            '/api/binance/summary': 'Get BTC/ETH prices',
            '/api/binance/funding': 'Get funding rate',
            '/api/binance/oi': 'Get open interest',
            '/api/fng': 'Get Fear & Greed Index',
            '/api/coingecko/simple': 'Get crypto prices',
            '/api/status': 'Server status',
            '/health': 'Health check'
        }
    })


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 HAMSTER TERMINAL API SERVER")
    print("=" * 80)
    print("Server starting on http://0.0.0.0:5000")
    print("Real-time data fetching from:")
    print("  • Binance API")
    print("  • CoinGecko API")
    print("  • Alternative.me Fear & Greed")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
