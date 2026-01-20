#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Symulacja API bez Flaska - bezpośrednie testowanie ML
"""

import sys
sys.path.insert(0, r'C:\Users\sebas\Desktop\finalbot')

from datetime import datetime
import time

print("[TEST] Symulacja API bez Flaska...\n")

# Załaduj model
try:
    from genius_model import load_model, infer_signal, commentary_for
    model = load_model()
    print("[OK] Model zaladowany\n")
except Exception as e:
    print(f"[ERR] {e}")
    sys.exit(1)

# Symuluj różne scenariusze
scenarios = [
    {'change': 1.5, 'fear_greed': 32, 'volume_ratio': 1.2, 'long_short_ratio': 1.05, 'name': 'Wzrost 1.5%, niska FG'},
    {'change': -2.0, 'fear_greed': 75, 'volume_ratio': 0.8, 'long_short_ratio': 0.95, 'name': 'Spadek 2%, wysoka FG'},
    {'change': 0.1, 'fear_greed': 50, 'volume_ratio': 1.0, 'long_short_ratio': 1.0, 'name': 'Neutralnie, FG srednia'},
]

for scenario in scenarios:
    print(f"\n{'='*60}")
    print(f"Scenariusz: {scenario['name']}")
    print(f"{'='*60}")
    
    features = {
        'change': scenario['change'],
        'fear_greed': scenario['fear_greed'],
        'volume_ratio': scenario['volume_ratio'],
        'hour': 14,
        'long_short_ratio': scenario['long_short_ratio'],
    }
    
    # ML Inference
    signal, strength, score = infer_signal(model, features)
    commentary = commentary_for(signal, strength, features)
    
    print(f"\nML Signal: {signal}")
    print(f"Strength: {strength}")
    print(f"Score: {score:.4f}")
    print(f"\nKomentarz:")
    print(f"  {commentary}")
    print(f"\n[JSON Response]")
    print(f"  {{")
    print(f"    \"commentary\": \"{commentary} | ML score {score:.2f}\",")
    print(f"    \"signal\": \"{signal}\",")
    print(f"    \"strength\": \"{strength}\",")
    print(f"    \"score\": {score:.4f},")
    print(f"    \"timestamp\": {time.time()}")
    print(f"  }}")

print(f"\n{'='*60}")
print("[SUCCESS] Test zakonczony - ML dziala!")
print(f"{'='*60}\n")
