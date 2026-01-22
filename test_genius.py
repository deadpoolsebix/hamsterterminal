#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\sebas\Desktop\finalbot')

print("[TEST] Testowanie importów Genius ML...")

try:
    from genius_model import load_model, infer_signal, commentary_for
    print("[OK] Importy zaloadowane")
    
    model = load_model()
    print(f"[OK] Model zaladowany: {type(model)}")
    
    features = {
        'change': 1.5,
        'fear_greed': 32,
        'volume_ratio': 1.2,
        'hour': 14,
        'long_short_ratio': 1.05
    }
    
    signal, strength, score = infer_signal(model, features)
    print(f"[OK] Wnioskowanie: signal={signal}, strength={strength}, score={score:.2f}")
    
    commentary = commentary_for(signal, strength, features)
    print(f"[OK] Komentarz: {commentary}")
    
except Exception as e:
    print(f"[BLAD] {e}")
    import traceback
    traceback.print_exc()
