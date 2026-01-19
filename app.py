from flask import Flask, jsonify, send_from_directory
import requests
import os
import threading
import time
import yfinance as yf
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')

# Cache commodity prices - REAL DATA
prices_cache = {
    'gold': 2650.00,
    'gold_change': 0.0,
    'silver': 32.50,
    'silver_change': 0.0,
    'btc': 95000,
    'eth': 2800,
    'btc_change': 0.0,
    'eth_change': 0.0,
    'oil': 78.50,
    'oil_change': 0.0,
    'last_update': 0
}

def fetch_real_prices():
    """Fetch real commodity prices from yfinance"""
    global prices_cache
    try:
        # Gold (GC=F)
        gold = yf.Ticker("GC=F")
        gold_info = gold.info
        gold_price = gold_info.get('regularMarketPrice', prices_cache['gold'])
        gold_prev = gold_info.get('regularMarketPreviousClose', gold_price)
        prices_cache['gold'] = float(gold_price)
        prices_cache['gold_change'] = ((gold_price - gold_prev) / gold_prev * 100) if gold_prev else 0
        logger.info(f"✅ GOLD: ${prices_cache['gold']:.2f} ({prices_cache['gold_change']:+.2f}%)")
        
        # Silver (SI=F)
        silver = yf.Ticker("SI=F")
        silver_info = silver.info
        silver_price = silver_info.get('regularMarketPrice', prices_cache['silver'])
        silver_prev = silver_info.get('regularMarketPreviousClose', silver_price)
        prices_cache['silver'] = float(silver_price)
        prices_cache['silver_change'] = ((silver_price - silver_prev) / silver_prev * 100) if silver_prev else 0
        logger.info(f"✅ SILVER: ${prices_cache['silver']:.2f} ({prices_cache['silver_change']:+.2f}%)")
        
        # Oil (CL=F)
        oil = yf.Ticker("CL=F")
        oil_info = oil.info
        oil_price = oil_info.get('regularMarketPrice', prices_cache['oil'])
        oil_prev = oil_info.get('regularMarketPreviousClose', oil_price)
        prices_cache['oil'] = float(oil_price)
        prices_cache['oil_change'] = ((oil_price - oil_prev) / oil_prev * 100) if oil_prev else 0
        logger.info(f"✅ OIL: ${prices_cache['oil']:.2f} ({prices_cache['oil_change']:+.2f}%)")
        
        # BTC/ETH from Binance
        btc_data = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', timeout=5).json()
        prices_cache['btc'] = float(btc_data['lastPrice'])
        prices_cache['btc_change'] = float(btc_data['priceChangePercent'])
        logger.info(f"✅ BTC: ${prices_cache['btc']:.2f} ({prices_cache['btc_change']:+.2f}%)")
        
        eth_data = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT', timeout=5).json()
        prices_cache['eth'] = float(eth_data['lastPrice'])
        prices_cache['eth_change'] = float(eth_data['priceChangePercent'])
        logger.info(f"✅ ETH: ${prices_cache['eth']:.2f} ({prices_cache['eth_change']:+.2f}%)")
        
        prices_cache['last_update'] = time.time()
    except Exception as e:
        logger.error(f"❌ Error fetching prices: {e}")

def background_price_update():
    """Update prices every 30 seconds"""
    while True:
        try:
            fetch_real_prices()
            time.sleep(30)
        except:
            time.sleep(30)

# Start background thread
update_thread = threading.Thread(target=background_price_update, daemon=True)
update_thread.start()

# Fetch initial prices
fetch_real_prices()

@app.route('/api/prices', methods=['GET'])
def get_prices():
    """Get current commodity prices"""
    return jsonify({
        'gold': round(prices_cache['gold'], 2),
        'gold_change': round(prices_cache['gold_change'], 2),
        'silver': round(prices_cache['silver'], 2),
        'silver_change': round(prices_cache['silver_change'], 2),
        'oil': round(prices_cache['oil'], 2),
        'oil_change': round(prices_cache['oil_change'], 2),
        'btc': round(prices_cache['btc'], 2),
        'btc_change': round(prices_cache['btc_change'], 2),
        'eth': round(prices_cache['eth'], 2),
        'eth_change': round(prices_cache['eth_change'], 2),
        'timestamp': prices_cache['last_update']
    })

@app.route('/api/commodities', methods=['GET'])
def get_commodities():
    """Get just commodity prices"""
    return jsonify({
        'gold': round(prices_cache['gold'], 2),
        'gold_change': round(prices_cache['gold_change'], 2),
        'silver': round(prices_cache['silver'], 2),
        'silver_change': round(prices_cache['silver_change'], 2),
        'oil': round(prices_cache['oil'], 2),
        'oil_change': round(prices_cache['oil_change'], 2),
    })

@app.route('/<path:filename>')
def serve_files(filename):
    """Serve HTML and other files"""
    if filename == '' or filename == '/':
        filename = 'professional_dashboard_final.html'
    return send_from_directory('.', filename)

@app.route('/')
def index():
    """Serve main dashboard"""
    return send_from_directory('.', 'professional_dashboard_final.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🚀 Starting Hamster Terminal on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
