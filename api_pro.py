#!/usr/bin/env python3
"""
HAMSTER TERMINAL - PROFESSIONAL API
WebSocket real-time:
- Binance: BTC/ETH (FREE, <1s latency)
- Alpaca Markets: US Stocks (FREE paper trading)
"""

from flask import Flask, jsonify
import json
import threading
import time
import logging
from datetime import datetime
import os

try:
    import websocket
    WS_OK = True
except:
    WS_OK = False

try:
    from alpaca.data.live import StockDataStream
    from alpaca.data.models import Trade
    ALPACA_SDK = True
except:
    ALPACA_SDK = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ALPACA API KEYS (ustaw w zmiennych środowiskowych lub tutaj)
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', 'YOUR_KEY_HERE')
ALPACA_SECRET = os.getenv('ALPACA_SECRET', 'YOUR_SECRET_HERE')

# Alpaca WebSocket stream (will be initialized if keys are set)
alpaca_stream = None

# CACHE - real-time WebSocket data
cache = {
    'BTC': {'price': 93000, 'change': 0, 'timestamp': datetime.now().isoformat()},
    'ETH': {'price': 3200, 'change': 0, 'timestamp': datetime.now().isoformat()},
    'SPY': {'price': 550, 'change': 0, 'timestamp': datetime.now().isoformat()},  # S&P 500 ETF
    'AAPL': {'price': 220, 'change': 0, 'timestamp': datetime.now().isoformat()},  # Apple
    'GOLD': {'price': 4675, 'change': 0, 'timestamp': datetime.now().isoformat()},
    'SILVER': {'price': 93, 'change': 0, 'timestamp': datetime.now().isoformat()},
    'OIL': {'price': 59, 'change': 0, 'timestamp': datetime.now().isoformat()},
    'status': 'connecting',
    'binance_status': 'connecting',
    'alpaca_status': 'connecting'
}

def binance_stream():
    """Binance WebSocket - LIVE TICK-BY-TICK (UPDATE ~1s)"""
    def on_message(ws, message):
        try:
            data = json.loads(message)
            if 'data' in data:
                data = data['data']
            
            symbol = data.get('s', '')
            price = float(data.get('c', 0))
            change = float(data.get('P', 0))
            
            if symbol == 'BTCUSDT':
                cache['BTC'] = {
                    'price': price,
                    'change': change,
                    'change_percent': change,
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"🔴 BTC ${price:,.2f} ({change:+.2f}%)")
            
            elif symbol == 'ETHUSDT':
                cache['ETH'] = {
                    'price': price,
                    'change': change,
                    'change_percent': change,
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"🔵 ETH ${price:,.2f} ({change:+.2f}%)")
            
            cache['binance_status'] = 'live'
            cache['status'] = 'live'
        except Exception as e:
            logger.error(f"Parse error: {e}")
    
    def on_error(ws, error):
        logger.warning(f"Binance WS Error: {error}")
        cache['binance_status'] = 'error'
    
    def on_close(ws, code, msg):
        logger.warning("Binance WS Closed - reconnecting in 5s...")
        cache['binance_status'] = 'reconnecting'
        time.sleep(5)
        binance_stream()
    
    def on_open(ws):
        logger.info("✅ BINANCE WEBSOCKET LIVE! (Updates every ~1 second)")
        cache['binance_status'] = 'live'
    
    if not WS_OK:
        logger.error("websocket-client missing!")
        return
    
    # Binance multi-stream - realtime co ~1 sekundę
    url = "wss://stream.binance.com:9443/stream?streams=btcusdt@ticker/ethusdt@ticker"
    ws = websocket.WebSocketApp(url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    ws.run_forever(ping_interval=30, ping_timeout=10)

# ============ ALPACA MARKETS WEBSOCKET (FREE STOCKS) ============

def alpaca_stream():
    """
    Alpaca Markets WebSocket using official SDK - US STOCKS REAL-TIME
    Requires FREE paper trading account from https://alpaca.markets
    """
    if not ALPACA_SDK:
        logger.error("alpaca-py SDK missing! Run: pip install alpaca-py")
        return
    
    if ALPACA_API_KEY == 'YOUR_KEY_HERE':
        logger.warning("⚠️ ALPACA API KEY not set - stocks disabled")
        logger.warning("   Get free keys at: https://alpaca.markets (Paper Trading)")
        return
    
    import asyncio
    
    try:
        # Initialize Alpaca WebSocket stream
        stream = StockDataStream(ALPACA_API_KEY, ALPACA_SECRET)
        
        # Handler for trade updates
        async def trade_handler(trade: Trade):
            symbol = trade.symbol
            price = float(trade.price)
            
            if symbol in ['SPY', 'AAPL']:
                # Calculate % change
                old_price = cache.get(symbol, {}).get('price', price)
                change = ((price - old_price) / old_price * 100) if old_price else 0
                
                cache[symbol] = {
                    'price': price,
                    'change': change,
                    'change_percent': change,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'live'
                }
                logger.info(f"📈 {symbol} ${price:,.2f} ({change:+.2f}%)")
            
            cache['alpaca_status'] = 'live'
            cache['status'] = 'live'
        
        # Subscribe to trades
        stream.subscribe_trades(trade_handler, 'SPY', 'AAPL')
        
        logger.info("✅ ALPACA SDK WEBSOCKET READY!")
        logger.info("📊 Subscribed: SPY, AAPL")
        
        # Start streaming - run() is blocking
        stream.run()
        
    except Exception as e:
        logger.error(f"Alpaca stream error: {e}")
        cache['alpaca_status'] = 'error'
        time.sleep(5)
        alpaca_stream()  # Reconnect

# ========== API ROUTES ==========

@app.route('/api/prices', methods=['GET'])
def get_prices():
    """All prices - dashboard format"""
    resp = jsonify(cache)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route('/api/status', methods=['GET'])
def get_status():
    """Server status"""
    resp = jsonify({
        'status': cache['status'],
        'message': 'WebSocket streaming active' if cache['status'] == 'live' else 'Connecting...'
    })
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/')
def index():
    return "<h1>🐹 Hamster Terminal API</h1><p>WebSocket Streaming Active</p><p>GET <a href='/api/prices'>/api/prices</a></p>"

# ========== START ==========

if __name__ == '__main__':
    logger.info("🚀 HAMSTER TERMINAL PROFESSIONAL API")
    logger.info("=" * 60)
    logger.info("📡 Starting WebSocket streams...")
    
    # Start Binance WebSocket (BTC/ETH)
    binance_thread = threading.Thread(target=binance_stream, daemon=True)
    binance_thread.start()
    
    # Start Alpaca WebSocket (Stocks) - if keys configured
    if ALPACA_API_KEY != 'YOUR_KEY_HERE':
        alpaca_thread = threading.Thread(target=alpaca_stream, daemon=True)
        alpaca_thread.start()
    else:
        logger.warning("⚠️ Alpaca disabled - set API keys to enable stocks")
    
    time.sleep(3)  # Wait for connections
    
    logger.info("")
    logger.info("✅ READY!")
    logger.info("=" * 60)
    logger.info("🌐 Dashboard: http://localhost:8000")
    logger.info("📊 API: http://localhost:8000/api/prices")
    logger.info("")
    logger.info("Live streams:")
    logger.info("  • Binance: BTC, ETH (updates every ~1 second)")
    if ALPACA_API_KEY != 'YOUR_KEY_HERE':
        logger.info("  • Alpaca: SPY, AAPL (real-time trades)")
    logger.info("=" * 60)
    logger.info("")
    
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
