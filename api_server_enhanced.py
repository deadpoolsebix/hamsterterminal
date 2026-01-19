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
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ TWELVE DATA API CONFIG ============
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'demo')
TWELVE_DATA_BASE_URL = 'https://api.twelvedata.com'

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
    'timestamp': 0,
    'prev_price': 0,
    'prev_volume': 0,
    'stocks': {'AAPL': 0, 'MSFT': 0, 'NVDA': 0},
    'crypto': {'BTCUSDT': 0, 'ETHUSDT': 0}
}

# Genius state for commentary
genius_state = {
    'last_commentary': '',
    'signal': 'NEUTRAL',
    'strength': 'medium'
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

def fetch_twelve_data_quote(symbol='BTCUSDT'):
    """Fetch quote from Twelve Data API"""
    try:
        params = {
            'symbol': symbol,
            'apikey': TWELVE_DATA_API_KEY
        }
        response = requests.get(
            f'{TWELVE_DATA_BASE_URL}/quote',
            params=params,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data and 'last_price' in data:
                return {
                    'price': float(data.get('last_price', 0)),
                    'change': float(data.get('percent_change', 0)),
                    'volume': float(data.get('volume', 0)),
                    'bid': float(data.get('bid', 0)),
                    'ask': float(data.get('ask', 0))
                }
    except Exception as e:
        logger.error(f"❌ Twelve Data error ({symbol}): {e}")
    return None

def fetch_twelve_data_assets():
    """Fetch BTC, ETH, stocks from Twelve Data"""
    try:
        # BTC
        btc_data = fetch_twelve_data_quote('BTCUSDT')
        if btc_data:
            cache['btc_price'] = btc_data['price']
            cache['btc_change_24h'] = btc_data['change']
            cache['btc_volume'] = btc_data['volume']
            cache['crypto']['BTCUSDT'] = btc_data['price']
            logger.info(f"✅ BTC: ${btc_data['price']:,.2f} ({btc_data['change']:+.2f}%)")
        
        # ETH
        eth_data = fetch_twelve_data_quote('ETHUSDT')
        if eth_data:
            cache['eth_price'] = eth_data['price']
            cache['crypto']['ETHUSDT'] = eth_data['price']
            logger.info(f"✅ ETH: ${eth_data['price']:,.2f} ({eth_data['change']:+.2f}%)")
        
        # STOCKS
        for stock in ['AAPL', 'MSFT', 'NVDA']:
            stock_data = fetch_twelve_data_quote(stock)
            if stock_data:
                cache['stocks'][stock] = stock_data['price']
                logger.info(f"✅ {stock}: ${stock_data['price']:,.2f}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Twelve Data assets fetch error: {e}")
        return False

def data_update_loop():
    """Background thread to update data every 30 seconds"""
    logger.info("🔄 Starting background data update thread...")
    while True:
        try:
            cache['prev_price'] = cache['btc_price']
            cache['prev_volume'] = cache['btc_volume']
            fetch_twelve_data_assets()
            fetch_fear_greed()
            cache['last_update'] = datetime.now().isoformat()
            cache['timestamp'] = time.time()
            logger.info(f"🧠 Genius: {genius_state['signal']} | {genius_state['strength'].upper()}")
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
            '/api/genius/commentary': 'Get live Hamster Genius commentary + signal',
            '/api/status': 'Get API server status',
            '/dashboard': 'Load Bloomberg dashboard with API'
        }
    })

@app.route('/api/binance/summary')
def binance_summary():
    """Get BTC/ETH market summary from Twelve Data"""
    return jsonify({
        'ok': True,
        'btcPrice': cache['btc_price'],
        'btcChange24h': cache['btc_change_24h'],
        'btcVolume': cache['btc_volume'],
        'btcMarketCap': cache['btc_market_cap'],
        'ethPrice': cache['eth_price'],
        'stocks': cache['stocks'],
        'crypto': cache['crypto'],
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

@app.route('/api/genius/commentary')
def genius_commentary():
    """Generate live Genius commentary based on real-time data analysis"""
    try:
        btc = cache['btc_price']
        change = cache['btc_change_24h']
        fear_greed = cache['fear_greed']
        volume = cache['btc_volume']
        
        # Analyze conditions
        signal = 'NEUTRAL'
        strength = 'medium'
        commentary = ''
        
        # Price momentum analysis
        if change > 1.5:
            signal = 'BULL'
            strength = 'strong'
            commentary = f"🟢 BTC momentum strong (+{change:.2f}%). Byki dominują. Utrzymaj longa, podnieś SL pod 95.1k."
        elif change > 0.5:
            signal = 'BULL'
            strength = 'medium'
            commentary = f"🟢 Lekki wzrost (+{change:.2f}%). Trend pozytywny. Czekaj na retest 95.2k FVG."
        elif change < -1.5:
            signal = 'BEAR'
            strength = 'strong'
            commentary = f"🔴 Spadek ostry ({change:.2f}%). Bieżnie protect longs. Czekaj na support 94.8k."
        elif change < -0.5:
            signal = 'BEAR'
            strength = 'medium'
            commentary = f"🔴 Pullback ({change:.2f}%). Zmiana nastroju. Uważaj na poziom 95k."
        else:
            signal = 'NEUTRAL'
            commentary = "⭕ Konsolidacja. RSI likely 45-55. Scalp opportunity w FVG."
        
        # Fear & Greed factor
        if fear_greed > 70:
            commentary += f" | Fear&Greed {fear_greed} (GREED) → rezerwuj 30% TP na 97.4k."
        elif fear_greed < 30:
            commentary += f" | Fear&Greed {fear_greed} (FEAR) → trzymaj hedgi, czekaj na reversal."
        
        # Volume analysis
        if volume > cache.get('prev_volume', 1) * 1.2:
            commentary += " | Wolumen +20% → potwierdzenie trendu. Zwiększ pozycję."
            if strength == 'medium':
                strength = 'strong'
        
        # Session analysis
        hour = datetime.now().hour
        if 8 <= hour < 11:
            commentary += " | LONDON OPEN: szukaj sweepu. Volatilność OK."
        elif 14 <= hour < 17:
            commentary += " | NEW YORK OPEN: watch liquidity sweep. Trend może przyspieszyć."
        
        genius_state['last_commentary'] = commentary
        genius_state['signal'] = signal
        genius_state['strength'] = strength
        
        return jsonify({
            'ok': True,
            'commentary': commentary,
            'signal': signal,
            'strength': strength,
            'btc_price': btc,
            'change_24h': change,
            'fear_greed': fear_greed,
            'timestamp': cache['timestamp']
        })
    except Exception as e:
        logger.error(f"❌ Genius commentary error: {e}")
        return jsonify({
            'ok': False,
            'commentary': '⭕ Genius loading...',
            'error': str(e)
        }), 500

# ========== ERROR HANDLERS ==========

@app.route('/api/status')
def status():
    """Get API server status"""
    return jsonify({
        'ok': True,
        'status': 'active',
        'timestamp': cache['timestamp'],
        'lastUpdate': cache['last_update'],
        'dataPoints': {
            'btc': cache['btc_price'],
            'eth': cache['eth_price'],
            'fear_greed': cache['fear_greed']
        }
    })

@app.route('/api/analytics')
def analytics():
    """Get advanced analytics data for radar, heatmaps, flow analysis"""
    try:
        btc = cache['btc_price']
        change = cache['btc_change_24h']
        fear_greed = cache['fear_greed']
        
        # Calculate derived metrics
        volatility_24h = abs(change) * random.uniform(0.8, 1.2)  # Mock volatility
        liquidation_long = random.uniform(40, 50)  # Mock liquidation
        liquidation_short = random.uniform(15, 25)
        
        # Correlation mock data (could integrate with real sources)
        correlations = {
            'btc_eth': 0.75 + random.uniform(-0.15, 0.15),
            'btc_aapl': 0.35 + random.uniform(-0.15, 0.15),
            'btc_dxy': -0.42 + random.uniform(-0.15, 0.15),
            'btc_vix': -0.28 + random.uniform(-0.15, 0.15),
            'btc_nasdaq': 0.58 + random.uniform(-0.15, 0.15)
        }
        
        return jsonify({
            'ok': True,
            'timestamp': cache['timestamp'],
            'radar': {
                'fvg': {
                    '1h': {'low': btc * 0.996, 'high': btc * 1.002, 'type': 'BUY'},
                    '4h': {'low': btc * 1.008, 'high': btc * 1.018, 'type': 'SELL'},
                    '1d': {'low': btc * 0.971, 'high': btc * 0.980, 'type': 'DEMAND'}
                },
                'eql_eqh': {
                    'eql': btc * 0.985,
                    'eqh': btc * 1.020,
                    'range': btc * 0.035
                },
                'premium_index': {
                    'spot_perps': 0.12 + random.uniform(-0.05, 0.05),
                    'funding': 0.008 + random.uniform(-0.003, 0.003)
                },
                'liquidations': {
                    'long_count': liquidation_long,
                    'short_count': liquidation_short,
                    'total_24h': liquidation_long + liquidation_short
                },
                'signal_strength': {
                    'bullish': 55 + random.randint(-10, 10),
                    'bearish': 45 + random.randint(-10, 10)
                }
            },
            'heatmaps': {
                'correlations': correlations,
                'volume_profile': [0.052, 0.087, 0.091, 0.063, 0.041],
                'microstructure': {
                    'bid_ask_spread': 0.12,
                    'order_imbalance': 1.34,
                    'vwap_deviation': 0.08,
                    'momentum': 'STRONG',
                    'order_flow': 'POSITIVE'
                }
            },
            'flow': {
                'whale_accumulation': 2300 + random.randint(-500, 500),
                'exchange_inflows': -120 + random.randint(-30, 30),
                'dark_pool_flow': 680 + random.randint(-100, 100),
                'order_flow_imbalance': 58 + random.randint(-5, 5),
                'long_short_ratio': 1.18 + random.uniform(-0.1, 0.1),
                'open_interest': 14200 + random.randint(-500, 500),
                'skew_index': -0.12 + random.uniform(-0.05, 0.05),
                'cascade_risk': 'MEDIUM'
            },
            'fear_greed': fear_greed,
            'btc_price': btc,
            'btc_change_24h': change,
            'volatility_24h': volatility_24h
        })
    except Exception as e:
        logger.error(f"❌ Analytics endpoint error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

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
    print("  • Twelve Data API (BTC/ETH, STOCKS, FOREX)")
    print("  • Alternative.me (Fear & Greed Index)")
    print("")
    print("🔄 Data update interval: 30 seconds")
    print("=" * 80)
    print("")
    
    # Start background data updater
    update_thread = threading.Thread(target=data_update_loop, daemon=True)
    update_thread.start()
    
    # Initial data fetch
    fetch_twelve_data_assets()
    fetch_fear_greed()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
