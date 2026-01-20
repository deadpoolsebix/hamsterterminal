import os
import json
import pickle
import numpy as np

# Optional TensorFlow import with safe fallback
TF_AVAILABLE = False
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except Exception:
    pass

# sklearn models as fallback
try:
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'genius_model.pkl')
TF_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'genius_model.h5')


def _normalize_features(features: dict) -> np.ndarray:
    """Map raw cache-derived features into a stable numeric vector."""
    change = float(features.get('change', 0.0))
    fear = float(features.get('fear_greed', 50.0)) / 100.0
    vol_ratio = float(features.get('volume_ratio', 1.0))  # current/prev
    hour = float(features.get('hour', 12)) / 24.0
    ls_ratio = float(features.get('long_short_ratio', 1.0))
    # Clip / bound for stability
    change = np.clip(change, -10.0, 10.0)
    vol_ratio = np.clip(vol_ratio, 0.0, 5.0)
    ls_ratio = np.clip(ls_ratio, 0.2, 5.0)
    return np.array([change, fear, vol_ratio, hour, ls_ratio], dtype=np.float32)


def build_sklearn_model():
    """Create a RandomForest classifier for BULL/BEAR strength."""
    if not SKLEARN_AVAILABLE:
        return None
    return RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)


def load_model(path: str = MODEL_PATH):
    """Load saved model (sklearn pickle or TF h5) if present."""
    # Try sklearn pickle first
    if os.path.exists(path) and SKLEARN_AVAILABLE:
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            pass
    # Try TF model
    if TF_AVAILABLE and os.path.exists(TF_MODEL_PATH):
        try:
            return tf.keras.models.load_model(TF_MODEL_PATH)
        except Exception:
            pass
    return None


def infer_signal(model, features: dict):
    """Return (signal, strength, score) using model or heuristic fallback."""
    x = _normalize_features(features).reshape(1, -1)
    
    # Try sklearn model
    if SKLEARN_AVAILABLE and model is not None and hasattr(model, 'predict_proba'):
        try:
            probs = model.predict_proba(x)[0]
            idx = int(np.argmax(probs))
            score = float(np.max(probs))
            signal = ['BEAR', 'NEUTRAL', 'BULL'][idx]
            strength = 'strong' if score > 0.66 else ('medium' if score > 0.45 else 'weak')
            return signal, strength, score
        except Exception:
            pass
    
    # Try TF model
    if TF_AVAILABLE and model is not None and hasattr(model, 'predict'):
        try:
            probs = model.predict(x, verbose=0)[0]
            idx = int(np.argmax(probs))
            score = float(np.max(probs))
            signal = ['BEAR', 'NEUTRAL', 'BULL'][idx]
            strength = 'strong' if score > 0.66 else ('medium' if score > 0.45 else 'weak')
            return signal, strength, score
        except Exception:
            pass

    # Heuristic fallback when ML is unavailable
    change = features.get('change', 0.0)
    fear = features.get('fear_greed', 50.0)
    vol_ratio = features.get('volume_ratio', 1.0)
    ls_ratio = features.get('long_short_ratio', 1.0)

    bull_score = 0.0
    bear_score = 0.0
    bull_score += max(0.0, change)
    bear_score += max(0.0, -change)
    bull_score += max(0.0, (fear - 50.0) / 10.0)
    bear_score += max(0.0, (50.0 - fear) / 10.0)
    bull_score += max(0.0, (ls_ratio - 1.0) * 2.0)
    bear_score += max(0.0, (1.0 - ls_ratio) * 2.0)
    bull_score *= vol_ratio
    bear_score *= vol_ratio

    if bull_score > bear_score * 1.2:
        signal = 'BULL'
        score = min(0.99, bull_score / (bull_score + bear_score + 1e-5))
    elif bear_score > bull_score * 1.2:
        signal = 'BEAR'
        score = min(0.99, bear_score / (bull_score + bear_score + 1e-5))
    else:
        signal = 'NEUTRAL'
        score = 0.5

    strength = 'strong' if score > 0.66 else ('medium' if score > 0.45 else 'weak')
    return signal, strength, score


def commentary_for(signal: str, strength: str, features: dict) -> str:
    change = features.get('change', 0.0)
    fear_greed = features.get('fear_greed', 50)
    vol_ratio = features.get('volume_ratio', 1.0)
    base = {
        'BULL': f"🟢 Momentum +{change:.2f}% | FG {fear_greed} | Wolumen x{vol_ratio:.2f}",
        'BEAR': f"🔴 Spadek {change:.2f}% | FG {fear_greed} | Wolumen x{vol_ratio:.2f}",
        'NEUTRAL': f"⭕ Konsolidacja {change:.2f}% | FG {fear_greed} | Wolumen x{vol_ratio:.2f}"
    }[signal]
    note = {
        'strong': ' → Siła trendu WYSOKA. Zabezpiecz pozycję, agresywny TP.',
        'medium': ' → Siła ŚREDNIA. Czekaj na retest FVG, scalp.',
        'weak': ' → SŁABA. Unikaj dużych pozycji, hedge.'
    }[strength]
    return base + note
