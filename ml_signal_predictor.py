"""
🤖 ML SIGNAL PREDICTOR - Machine Learning dla sygnałów tradingowych
HamsterTerminal Pro v3.0

Funkcje:
- Feature engineering z wskaźników technicznych
- RandomForest / XGBoost / LightGBM modele
- Trenowanie na danych historycznych
- Predykcja prawdopodobieństwa sukcesu sygnału
- Model persistence i versioning
"""

import os
import json
import pickle
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np

# Konfiguracja
MODEL_DIR = 'ml_models'
os.makedirs(MODEL_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sprawdź dostępność bibliotek ML
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("⚠️ scikit-learn not installed. Run: pip install scikit-learn")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("⚠️ XGBoost not installed. Run: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("⚠️ LightGBM not installed. Run: pip install lightgbm")


class FeatureEngineer:
    """
    🔧 Feature Engineering dla danych tradingowych
    
    Tworzy features z surowych danych OHLCV i wskaźników technicznych.
    """
    
    @staticmethod
    def create_features(data: List[Dict], lookback: int = 20) -> List[Dict]:
        """
        Utwórz features dla każdego punktu danych.
        
        Args:
            data: Lista świec OHLCV
            lookback: Ile świec wstecz analizować
        
        Returns:
            Lista feature vectors
        """
        features_list = []
        
        for i in range(max(200, lookback), len(data) - 5):  # -5 bo potrzebujemy label z przyszłości
            try:
                candle = data[i]
                closes = [d['close'] for d in data[i-lookback:i+1]]
                highs = [d['high'] for d in data[i-lookback:i+1]]
                lows = [d['low'] for d in data[i-lookback:i+1]]
                volumes = [d.get('volume', 0) for d in data[i-lookback:i+1]]
                
                # Podstawowe cechy cenowe
                price = candle['close']
                price_change = (price - closes[-2]) / closes[-2] * 100 if closes[-2] > 0 else 0
                price_change_5 = (price - closes[-6]) / closes[-6] * 100 if closes[-6] > 0 else 0
                price_change_10 = (price - closes[-11]) / closes[-11] * 100 if len(closes) > 10 and closes[-11] > 0 else 0
                
                # Volatility
                returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
                volatility = np.std(returns) * 100 if returns else 0
                
                # Range features
                range_pct = (candle['high'] - candle['low']) / price * 100 if price > 0 else 0
                avg_range = np.mean([(h - l) / l for h, l in zip(highs, lows) if l > 0]) * 100
                
                # RSI
                def calc_rsi(prices, period=14):
                    if len(prices) < period + 1:
                        return 50
                    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
                    gains = [d if d > 0 else 0 for d in deltas[-period:]]
                    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
                    avg_gain = sum(gains) / period
                    avg_loss = sum(losses) / period
                    if avg_loss == 0:
                        return 100
                    rs = avg_gain / avg_loss
                    return 100 - (100 / (1 + rs))
                
                rsi = calc_rsi(closes)
                rsi_prev = calc_rsi(closes[:-1])
                rsi_change = rsi - rsi_prev
                
                # MACD
                def calc_ema(prices, period):
                    if len(prices) < period:
                        return prices[-1]
                    multiplier = 2 / (period + 1)
                    ema = sum(prices[:period]) / period
                    for p in prices[period:]:
                        ema = (p - ema) * multiplier + ema
                    return ema
                
                ema_12 = calc_ema(closes, 12)
                ema_26 = calc_ema(closes, 26)
                macd = ema_12 - ema_26
                macd_normalized = macd / price * 100 if price > 0 else 0
                
                # Bollinger Bands
                sma_20 = np.mean(closes[-20:])
                std_20 = np.std(closes[-20:])
                bb_upper = sma_20 + 2 * std_20
                bb_lower = sma_20 - 2 * std_20
                bb_position = (price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
                bb_width = (bb_upper - bb_lower) / sma_20 * 100 if sma_20 > 0 else 0
                
                # SMAs
                sma_5 = np.mean(closes[-5:])
                sma_10 = np.mean(closes[-10:])
                sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma_20
                sma_200_data = [d['close'] for d in data[max(0, i-199):i+1]]
                sma_200 = np.mean(sma_200_data) if len(sma_200_data) >= 200 else sma_50
                
                price_to_sma_5 = (price - sma_5) / sma_5 * 100 if sma_5 > 0 else 0
                price_to_sma_20 = (price - sma_20) / sma_20 * 100 if sma_20 > 0 else 0
                price_to_sma_50 = (price - sma_50) / sma_50 * 100 if sma_50 > 0 else 0
                sma_5_to_sma_20 = (sma_5 - sma_20) / sma_20 * 100 if sma_20 > 0 else 0
                
                # Volume
                avg_volume = np.mean(volumes) if volumes else 0
                volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
                
                # Momentum
                momentum_5 = (closes[-1] - closes[-6]) / closes[-6] * 100 if closes[-6] > 0 else 0
                momentum_10 = (closes[-1] - closes[-11]) / closes[-11] * 100 if len(closes) > 10 and closes[-11] > 0 else 0
                
                # === LABEL: Czy cena wzrośnie w następnych 5 świecach o >1%? ===
                future_price = data[i + 5]['close']
                future_return = (future_price - price) / price * 100
                
                # 3 klasy: 0 = spadek (< -1%), 1 = neutralny (-1% to 1%), 2 = wzrost (> 1%)
                if future_return > 1.5:
                    label = 2  # BUY
                elif future_return < -1.5:
                    label = 0  # SELL
                else:
                    label = 1  # HOLD
                
                features = {
                    # Price features
                    'price_change_1': price_change,
                    'price_change_5': price_change_5,
                    'price_change_10': price_change_10,
                    'volatility': volatility,
                    'range_pct': range_pct,
                    'avg_range': avg_range,
                    
                    # Technical indicators
                    'rsi': rsi,
                    'rsi_change': rsi_change,
                    'macd_normalized': macd_normalized,
                    'bb_position': bb_position,
                    'bb_width': bb_width,
                    
                    # Trend features
                    'price_to_sma_5': price_to_sma_5,
                    'price_to_sma_20': price_to_sma_20,
                    'price_to_sma_50': price_to_sma_50,
                    'sma_5_to_sma_20': sma_5_to_sma_20,
                    'golden_cross': 1 if sma_5 > sma_20 > sma_50 else 0,
                    'death_cross': 1 if sma_5 < sma_20 < sma_50 else 0,
                    
                    # Volume
                    'volume_ratio': volume_ratio,
                    
                    # Momentum
                    'momentum_5': momentum_5,
                    'momentum_10': momentum_10,
                    
                    # Meta
                    'datetime': candle['datetime'],
                    'price': price,
                    'label': label,
                    'future_return': future_return
                }
                
                features_list.append(features)
                
            except Exception as e:
                logger.error(f"Feature engineering error at index {i}: {e}")
                continue
        
        return features_list


class MLSignalPredictor:
    """
    🤖 ML Signal Predictor
    
    Trenuje modele ML do przewidywania sukcesu sygnałów tradingowych.
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Args:
            model_type: 'random_forest', 'gradient_boosting', 'xgboost', 'lightgbm'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.feature_columns = None
        self.model_info = {}
    
    def _get_model(self):
        """Zwróć odpowiedni model ML"""
        if self.model_type == 'random_forest' and SKLEARN_AVAILABLE:
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting' and SKLEARN_AVAILABLE:
            return GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
            return xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss'
            )
        elif self.model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
            return lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
                verbose=-1
            )
        else:
            logger.warning(f"Model {self.model_type} not available, using RandomForest")
            return RandomForestClassifier(n_estimators=100, random_state=42)
    
    def prepare_data(self, features_list: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Przygotuj dane do treningu"""
        # Kolumny do użycia jako features
        self.feature_columns = [
            'price_change_1', 'price_change_5', 'price_change_10',
            'volatility', 'range_pct', 'avg_range',
            'rsi', 'rsi_change', 'macd_normalized',
            'bb_position', 'bb_width',
            'price_to_sma_5', 'price_to_sma_20', 'price_to_sma_50',
            'sma_5_to_sma_20', 'golden_cross', 'death_cross',
            'volume_ratio', 'momentum_5', 'momentum_10'
        ]
        
        X = []
        y = []
        
        for f in features_list:
            try:
                row = [f[col] for col in self.feature_columns]
                X.append(row)
                y.append(f['label'])
            except KeyError as e:
                logger.warning(f"Missing feature: {e}")
                continue
        
        return np.array(X), np.array(y)
    
    def train(self, features_list: List[Dict], test_size: float = 0.2) -> Dict:
        """
        Trenuj model na danych.
        
        Args:
            features_list: Lista features z FeatureEngineer
            test_size: Część danych na test
        
        Returns:
            Dict z metrykami
        """
        if not SKLEARN_AVAILABLE:
            logger.error("❌ scikit-learn not available")
            return {'error': 'scikit-learn not installed'}
        
        logger.info(f"🔧 Training {self.model_type} model with {len(features_list)} samples...")
        
        # Przygotuj dane
        X, y = self.prepare_data(features_list)
        
        if len(X) < 100:
            logger.error("❌ Insufficient data for training")
            return {'error': 'Insufficient data'}
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = self._get_model()
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        # Metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision_macro': precision_score(y_test, y_pred, average='macro', zero_division=0),
            'recall_macro': recall_score(y_test, y_pred, average='macro', zero_division=0),
            'f1_macro': f1_score(y_test, y_pred, average='macro', zero_division=0),
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'class_distribution': {
                'SELL (0)': int(np.sum(y == 0)),
                'HOLD (1)': int(np.sum(y == 1)),
                'BUY (2)': int(np.sum(y == 2))
            }
        }
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            importance = dict(zip(self.feature_columns, self.model.feature_importances_))
            metrics['feature_importance'] = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        self.model_info = {
            'model_type': self.model_type,
            'trained_at': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        logger.info(f"✅ Training complete: Accuracy={metrics['accuracy']:.3f}, F1={metrics['f1_macro']:.3f}")
        
        return metrics
    
    def predict(self, features: Dict) -> Dict:
        """
        Przewiduj sygnał dla pojedynczych features.
        
        Args:
            features: Dict z features
        
        Returns:
            Dict z predykcją i prawdopodobieństwami
        """
        if not self.model or not self.feature_columns:
            return {'error': 'Model not trained'}
        
        try:
            # Przygotuj input
            X = np.array([[features[col] for col in self.feature_columns]])
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            labels = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
            
            return {
                'prediction': labels[prediction],
                'prediction_code': int(prediction),
                'probabilities': {
                    'SELL': float(probabilities[0]),
                    'HOLD': float(probabilities[1]),
                    'BUY': float(probabilities[2])
                },
                'confidence': float(max(probabilities)) * 100,
                'model_type': self.model_type
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {'error': str(e)}
    
    def predict_batch(self, features_list: List[Dict]) -> List[Dict]:
        """Przewiduj dla wielu próbek naraz"""
        return [self.predict(f) for f in features_list]
    
    def save_model(self, filename: str = None) -> str:
        """Zapisz model do pliku"""
        if not self.model:
            logger.error("No model to save")
            return None
        
        if not filename:
            filename = f"ml_model_{self.model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        
        filepath = os.path.join(MODEL_DIR, filename)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'model_info': self.model_info
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"✅ Model saved: {filepath}")
        return filepath
    
    def load_model(self, filepath: str) -> bool:
        """Wczytaj model z pliku"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.model_info = model_data['model_info']
            self.model_type = self.model_info.get('model_type', 'unknown')
            
            logger.info(f"✅ Model loaded: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False


def format_ml_report(metrics: Dict) -> str:
    """Formatuj raport z treningu ML"""
    
    acc = metrics.get('accuracy', 0)
    acc_emoji = "✅" if acc > 0.55 else "⚠️" if acc > 0.45 else "❌"
    
    report = f"""
{'═' * 50}
🤖 ML MODEL TRAINING REPORT
{'═' * 50}

📊 PERFORMANCE METRICS
{'─' * 50}
Accuracy:         {metrics.get('accuracy', 0):.1%} {acc_emoji}
Precision:        {metrics.get('precision_macro', 0):.1%}
Recall:           {metrics.get('recall_macro', 0):.1%}
F1 Score:         {metrics.get('f1_macro', 0):.1%}

Cross-Validation: {metrics.get('cv_mean', 0):.1%} (±{metrics.get('cv_std', 0):.1%})

📈 DATA STATISTICS
{'─' * 50}
Training samples: {metrics.get('train_samples', 0):,}
Test samples:     {metrics.get('test_samples', 0):,}

Class Distribution:
"""
    
    for cls, count in metrics.get('class_distribution', {}).items():
        report += f"  • {cls}: {count:,}\n"
    
    report += f"""
{'─' * 50}
🎯 TOP FEATURES
{'─' * 50}
"""
    
    importance = metrics.get('feature_importance', {})
    for i, (feature, imp) in enumerate(list(importance.items())[:10], 1):
        bar = '█' * int(imp * 50)
        report += f"{i:2}. {feature:20s} {imp:.3f} {bar}\n"
    
    report += f"""
{'═' * 50}
💡 INTERPRETATION
{'─' * 50}
"""
    
    if acc > 0.55:
        report += "✅ Model shows predictive power above random chance\n"
        report += "   Consider using for signal confirmation\n"
    elif acc > 0.45:
        report += "⚠️ Model performance is marginal\n"
        report += "   May need more data or feature engineering\n"
    else:
        report += "❌ Model does not show predictive power\n"
        report += "   Consider different features or model type\n"
    
    report += f"""
{'═' * 50}
📡 HamsterTerminal ML Engine v1.0
{'═' * 50}
"""
    
    return report


# ═══════════════════════════════════════════════════════════════
# INTEGRATION WITH BACKTESTING
# ═══════════════════════════════════════════════════════════════

def train_from_backtest_data(symbol: str, interval: str = '1h') -> MLSignalPredictor:
    """
    Trenuj model ML na danych z backtestingu.
    
    Args:
        symbol: Symbol (np. 'BTC/USD')
        interval: Interwał czasowy
    
    Returns:
        Wytrenowany MLSignalPredictor
    """
    # Import backtesting module
    from backtesting_engine import get_historical_data
    
    logger.info(f"🤖 Training ML model for {symbol} ({interval})...")
    
    # Pobierz dane
    data = get_historical_data(symbol, interval, 5000)
    if not data:
        logger.error(f"❌ Failed to get data for {symbol}")
        return None
    
    # Feature engineering
    logger.info(f"🔧 Engineering features from {len(data)} candles...")
    features = FeatureEngineer.create_features(data)
    
    if len(features) < 200:
        logger.error(f"❌ Insufficient features: {len(features)}")
        return None
    
    logger.info(f"✅ Created {len(features)} feature vectors")
    
    # Trenuj model
    predictor = MLSignalPredictor(model_type='random_forest')
    metrics = predictor.train(features)
    
    if 'error' not in metrics:
        # Zapisz model
        predictor.save_model(f"ml_{symbol.replace('/', '_')}_{interval}.pkl")
        print(format_ml_report(metrics))
    
    return predictor


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🤖 HAMSTER TERMINAL - ML SIGNAL PREDICTOR")
    print("=" * 60)
    
    if not SKLEARN_AVAILABLE:
        print("❌ Please install scikit-learn: pip install scikit-learn")
        sys.exit(1)
    
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTC/USD'
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    
    print(f"\n🎯 Training ML model for {symbol} ({interval})...")
    
    predictor = train_from_backtest_data(symbol, interval)
    
    if predictor:
        print("\n✅ Model training complete!")
    else:
        print("\n❌ Model training failed")
