#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[ML] HAMSTER TERMINAL - API SERVER z ML GENIUS
Uproszczona wersja do testowania ML modelu
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os
import threading
import time
from datetime import datetime

sys.path.insert(0, r'C:\Users\sebas\Desktop\finalbot')

# Logowanie startowe
print("[BOOT] Inicjalizacja...")

app = Flask(__name__)
CORS(app)

# Cache
cache = {
    'btc_price': 95123.45,
    'btc_change_24h': 0.0,
    'fear_greed': 32,
    'btc_volume': 28500000000,
    'timestamp': time.time(),
    'last_update': datetime.now().isoformat()
}

print("[BOOT] Flask app created")

# ML model
GENIUS_MODEL = None
try:
    from genius_model import load_model, infer_signal, commentary_for
    GENIUS_MODEL = load_model()
    print("[ML] Model zaladowany OK!")
except Exception as e:
    print(f"[ERR] Model: {e}")

# Route 1: Health check
@app.route('/')
def home():
    return jsonify({'status': 'OK', 'model': 'LOADED' if GENIUS_MODEL else 'NONE'})

# Route 2: Genius commentary
@app.route('/api/genius/commentary')
def genius():
    features = {
        'change': cache.get('btc_change_24h', 0),
        'fear_greed': cache.get('fear_greed', 50),
        'volume_ratio': 1.2,
        'hour': datetime.now().hour,
        'long_short_ratio': 1.05,
    }
    
    if GENIUS_MODEL:
        signal, strength, score = infer_signal(GENIUS_MODEL, features)
        text = commentary_for(signal, strength, features) + f" | ML score {score:.2f}"
    else:
        signal = 'NEUTRAL'
        strength = 'medium'
        text = "No model"
        score = 0.0
    
    return jsonify({
        'commentary': text,
        'signal': signal,
        'strength': strength,
        'score': score,
        'btc_price': cache['btc_price'],
        'timestamp': time.time()
    })

print("[BOOT] Routes registered")

if __name__ == '__main__':
    print("[BOOT] Starting Flask on 127.0.0.1:5000...")
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"[ERR] Flask: {e}")
        import traceback
        traceback.print_exc()
