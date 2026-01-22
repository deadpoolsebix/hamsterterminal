#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMSTER TERMINAL - BLOOMBERG CLEAN API SERVER v2.0 (TEST)
Uruchomienie bez background thread dla debugowania
"""

import sys
sys.path.insert(0, r'C:\Users\sebas\Desktop\finalbot')

print("[STARTUP] Inicjalizacja API...")

# Importy z Flask
from flask import Flask, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import time

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stwórz Flask app
app = Flask(__name__)
CORS(app)

print("[STARTUP] Flask app created")

# Cache globalny
cache = {
    'btc_price': 95123.45,
    'btc_change_24h': 0.0,
    'fear_greed': 32,
    'btc_volume': 28500000000,
    'stocks': {},
    'crypto': {},
    'timestamp': time.time(),
    'last_update': datetime.now().isoformat()
}

print("[STARTUP] Cache initialized")

# Load ML model
try:
    from genius_model import load_model, infer_signal, commentary_for
    GENIUS_MODEL = load_model()
    print("[ML] Model zaladowany pomyslnie!")
except Exception as e:
    GENIUS_MODEL = None
    print(f"[WARNING] Model nie zaladowany: {e}")
    import traceback
    traceback.print_exc()

print("[STARTUP] ML model loaded")

# Genius state
genius_state = {
    'last_commentary': '',
    'signal': 'NEUTRAL',
    'strength': 'medium'
}

print("[STARTUP] Genius state initialized")

# API endpoint
@app.route('/api/genius/commentary')
def genius_commentary():
    """Generate live Genius commentary enhanced by ML when available"""
    try:
        btc = cache['btc_price']
        change = cache['btc_change_24h']
        fear_greed = cache['fear_greed']
        volume = cache['btc_volume']
        prev_vol = cache.get('prev_volume', max(1.0, volume))
        vol_ratio = (volume / prev_vol) if prev_vol else 1.0
        hour = datetime.now().hour
        long_short_ratio = 1.0
        
        # Compose feature dict
        features = {
            'change': change,
            'fear_greed': fear_greed,
            'volume_ratio': vol_ratio,
            'hour': hour,
            'long_short_ratio': long_short_ratio,
        }
        
        # Use ML model if present
        if GENIUS_MODEL is not None:
            signal, strength, score = infer_signal(GENIUS_MODEL, features)
            commentary = commentary_for(signal, strength, features) + f" | ML score {score:.2f}"
        else:
            signal = 'NEUTRAL'
            strength = 'medium'
            commentary = "Model nie zaladowany"
        
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
        logger.error(f"Blad: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

print("[STARTUP] Routes registered")

if __name__ == '__main__':
    print("[STARTUP] Uruchamiam Flask na porcie 5000...")
    print("[DEBUG] Sprawdzam czy port już zajęty...")
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 5000))
        s.close()
        print("[DEBUG] Port 5000 jest wolny")
    except:
        print("[ERROR] Port 5000 już zajęty!")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)
