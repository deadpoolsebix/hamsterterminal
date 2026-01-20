import os
import pickle
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
except Exception as e:
    print('scikit-learn not available:', e)
    print('Install: python -m pip install scikit-learn')
    raise SystemExit(1)

from genius_model import build_sklearn_model, MODEL_PATH

# Synthetic dataset generator (replace with real historical later)
# Features: [change%, fear_greed/100, volume_ratio, hour/24, long_short_ratio]
# Label: 0=BEAR, 1=NEUTRAL, 2=BULL

def generate_dataset(n=5000, seed=42):
    rng = np.random.default_rng(seed)
    change = rng.normal(0.0, 1.5, size=n)
    fear = rng.uniform(0.0, 1.0, size=n)
    vol_ratio = np.clip(rng.lognormal(mean=0.0, sigma=0.3, size=n), 0.0, 5.0)
    hour = rng.uniform(0.0, 1.0, size=n)
    ls_ratio = np.clip(rng.normal(1.0, 0.3, size=n), 0.2, 5.0)
    X = np.stack([change, fear, vol_ratio, hour, ls_ratio], axis=1).astype(np.float32)
    y = np.zeros(n, dtype=np.int32)
    # Heuristic labels
    bull_mask = (change > 0.6) & (fear > 0.55) & (ls_ratio > 1.05)
    bear_mask = (change < -0.6) & (fear < 0.45) & (ls_ratio < 0.95)
    y[bull_mask] = 2
    y[bear_mask] = 0
    y[~(bull_mask | bear_mask)] = 1
    return X, y


def main():
    print('🧠 Genius Training - RandomForest sklearn model')
    X, y = generate_dataset()
    print(f'Generated {len(X)} samples')
    model = build_sklearn_model()
    print('Training...')
    model.fit(X, y)
    print('Training complete')
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f'✅ Saved model to {MODEL_PATH}')
    # Quick test
    test_features = np.array([[1.2, 0.65, 1.1, 0.5, 1.15]])
    pred = model.predict(test_features)
    prob = model.predict_proba(test_features)[0]
    print(f'Test prediction: {["BEAR","NEUTRAL","BULL"][pred[0]]} | probs {prob}')

if __name__ == '__main__':
    main()
