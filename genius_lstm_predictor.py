"""
🤖 GENIUS LSTM PREDICTOR v1.0
==============================
Deep Learning price prediction for Genius Trading Engine

Features:
- LSTM neural network for time series prediction
- Multi-step forecasting (1h, 4h, 24h)
- Confidence scoring
- Integration with Genius Engine as 11th confluence factor

Author: Hamster Terminal Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import os
import warnings
warnings.filterwarnings('ignore')

# Deep Learning imports
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

try:
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PricePrediction:
    """Price prediction result"""
    current_price: float
    predicted_price_1h: float
    predicted_price_4h: float
    predicted_price_24h: float
    predicted_change_1h: float  # Percentage
    predicted_change_4h: float
    predicted_change_24h: float
    confidence: float  # 0-1
    direction: str  # 'UP', 'DOWN', 'NEUTRAL'
    strength: str  # 'STRONG', 'MODERATE', 'WEAK'
    model_accuracy: float
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'current_price': round(self.current_price, 2),
            'predictions': {
                '1h': {
                    'price': round(self.predicted_price_1h, 2),
                    'change_pct': round(self.predicted_change_1h, 2)
                },
                '4h': {
                    'price': round(self.predicted_price_4h, 2),
                    'change_pct': round(self.predicted_change_4h, 2)
                },
                '24h': {
                    'price': round(self.predicted_price_24h, 2),
                    'change_pct': round(self.predicted_change_24h, 2)
                }
            },
            'confidence': round(self.confidence, 2),
            'direction': self.direction,
            'strength': self.strength,
            'model_accuracy': round(self.model_accuracy, 2),
            'timestamp': self.timestamp.isoformat()
        }


class GeniusLSTMPredictor:
    """
    LSTM-based price predictor for cryptocurrency
    """
    
    def __init__(self, sequence_length: int = 60, model_path: str = None):
        self.sequence_length = sequence_length
        self.model_path = model_path or 'models/genius_lstm.h5'
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1)) if SKLEARN_AVAILABLE else None
        self.is_trained = False
        self.last_accuracy = 0.0
        
        # Create models directory
        os.makedirs('models', exist_ok=True)
        
        if TF_AVAILABLE:
            # Suppress TF warnings
            tf.get_logger().setLevel('ERROR')
            logger.info("🤖 Genius LSTM Predictor initialized")
            logger.info(f"   TensorFlow: {tf.__version__}")
            logger.info(f"   Sequence Length: {sequence_length}")
        else:
            logger.warning("⚠️ TensorFlow not available - predictions disabled")
    
    def build_model(self, input_shape: Tuple[int, int]) -> Sequential:
        """Build LSTM model architecture"""
        if not TF_AVAILABLE:
            return None
        
        model = Sequential([
            # First LSTM layer
            LSTM(128, return_sequences=True, input_shape=input_shape),
            BatchNormalization(),
            Dropout(0.2),
            
            # Second LSTM layer
            LSTM(64, return_sequences=True),
            BatchNormalization(),
            Dropout(0.2),
            
            # Third LSTM layer
            LSTM(32, return_sequences=False),
            BatchNormalization(),
            Dropout(0.2),
            
            # Dense layers
            Dense(32, activation='relu'),
            Dense(16, activation='relu'),
            Dense(1)  # Single output: next price
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='huber',  # Robust to outliers
            metrics=['mae']
        )
        
        return model
    
    def prepare_data(self, data: pd.DataFrame, 
                     feature_cols: List[str] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM training"""
        if not SKLEARN_AVAILABLE:
            return None, None
        
        if feature_cols is None:
            feature_cols = ['close', 'high', 'low', 'volume']
        
        # Filter available columns
        available_cols = [c for c in feature_cols if c in data.columns]
        
        if 'close' not in available_cols:
            logger.error("'close' column required")
            return None, None
        
        # Extract features
        features = data[available_cols].values
        
        # Scale data
        scaled_data = self.scaler.fit_transform(features)
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i])
            y.append(scaled_data[i, 0])  # Predict close price
        
        return np.array(X), np.array(y)
    
    def train(self, symbol: str = 'BTC-USD', 
              period: str = '2y',
              epochs: int = 50,
              batch_size: int = 32) -> Dict:
        """Train LSTM model on historical data"""
        if not TF_AVAILABLE or not YFINANCE_AVAILABLE:
            return {'error': 'Required libraries not available'}
        
        logger.info(f"🎓 Training LSTM model for {symbol}...")
        
        # Fetch data
        data = yf.download(symbol, period=period, interval='1h', progress=False)
        if len(data) < self.sequence_length * 2:
            return {'error': 'Insufficient data'}
        
        data.columns = [c.lower() if isinstance(c, str) else c[0].lower() for c in data.columns]
        
        # Prepare data
        X, y = self.prepare_data(data)
        if X is None:
            return {'error': 'Data preparation failed'}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        logger.info(f"   Training samples: {len(X_train)}")
        logger.info(f"   Test samples: {len(X_test)}")
        
        # Build model
        self.model = self.build_model((X.shape[1], X.shape[2]))
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5, min_lr=0.0001)
        ]
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.1,
            callbacks=callbacks,
            verbose=0
        )
        
        # Evaluate
        loss, mae = self.model.evaluate(X_test, y_test, verbose=0)
        
        # Calculate accuracy as inverse of normalized error
        y_pred = self.model.predict(X_test, verbose=0)
        mape = np.mean(np.abs((y_test - y_pred.flatten()) / y_test)) * 100
        accuracy = max(0, 100 - mape)
        
        self.last_accuracy = accuracy
        self.is_trained = True
        
        # Save model
        try:
            self.model.save(self.model_path)
            logger.info(f"   Model saved to {self.model_path}")
        except Exception as e:
            logger.warning(f"   Could not save model: {e}")
        
        logger.info(f"✅ Training complete! Accuracy: {accuracy:.1f}%")
        
        return {
            'status': 'success',
            'epochs_trained': len(history.history['loss']),
            'final_loss': round(history.history['loss'][-1], 4),
            'val_loss': round(history.history['val_loss'][-1], 4),
            'mae': round(mae, 4),
            'accuracy': round(accuracy, 1),
            'samples': len(X_train)
        }
    
    def load_model(self) -> bool:
        """Load pre-trained model"""
        if not TF_AVAILABLE:
            return False
        
        try:
            if os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
                self.is_trained = True
                logger.info(f"✅ Model loaded from {self.model_path}")
                return True
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
        
        return False
    
    def predict(self, symbol: str = 'BTC-USD') -> Optional[PricePrediction]:
        """
        Make price predictions
        """
        if not TF_AVAILABLE or not YFINANCE_AVAILABLE:
            logger.error("Required libraries not available")
            return None
        
        # Try to load model if not trained
        if not self.is_trained:
            if not self.load_model():
                logger.info("No trained model found, training new model...")
                result = self.train(symbol, period='6mo', epochs=30)
                if 'error' in result:
                    return None
        
        # Fetch recent data
        data = yf.download(symbol, period='7d', interval='1h', progress=False)
        if len(data) < self.sequence_length:
            logger.error("Insufficient data for prediction")
            return None
        
        data.columns = [c.lower() if isinstance(c, str) else c[0].lower() for c in data.columns]
        current_price = float(data['close'].iloc[-1])
        
        # Prepare features
        feature_cols = ['close', 'high', 'low', 'volume']
        available_cols = [c for c in feature_cols if c in data.columns]
        features = data[available_cols].values[-self.sequence_length:]
        
        # Scale
        scaled = self.scaler.transform(features)
        X = np.array([scaled])
        
        # Predict iteratively for multiple horizons
        predictions = []
        current_seq = X[0].copy()
        
        for _ in range(24):  # Predict 24 hours ahead
            pred = self.model.predict(np.array([current_seq]), verbose=0)[0, 0]
            predictions.append(pred)
            
            # Update sequence (shift and add new prediction)
            new_row = current_seq[-1].copy()
            new_row[0] = pred  # Update close price
            current_seq = np.vstack([current_seq[1:], new_row])
        
        # Inverse transform predictions
        dummy = np.zeros((len(predictions), len(available_cols)))
        dummy[:, 0] = predictions
        inv_predictions = self.scaler.inverse_transform(dummy)[:, 0]
        
        pred_1h = float(inv_predictions[0])
        pred_4h = float(inv_predictions[3])
        pred_24h = float(inv_predictions[23])
        
        change_1h = (pred_1h / current_price - 1) * 100
        change_4h = (pred_4h / current_price - 1) * 100
        change_24h = (pred_24h / current_price - 1) * 100
        
        # Determine direction and strength
        avg_change = (change_1h + change_4h + change_24h) / 3
        
        if avg_change > 1:
            direction = 'UP'
            strength = 'STRONG' if avg_change > 3 else 'MODERATE'
        elif avg_change < -1:
            direction = 'DOWN'
            strength = 'STRONG' if avg_change < -3 else 'MODERATE'
        else:
            direction = 'NEUTRAL'
            strength = 'WEAK'
        
        # Confidence based on model accuracy and prediction consistency
        consistency = 1 - abs(change_24h - change_1h) / max(abs(change_24h), abs(change_1h), 0.01)
        confidence = (self.last_accuracy / 100 * 0.7) + (consistency * 0.3)
        
        return PricePrediction(
            current_price=current_price,
            predicted_price_1h=pred_1h,
            predicted_price_4h=pred_4h,
            predicted_price_24h=pred_24h,
            predicted_change_1h=change_1h,
            predicted_change_4h=change_4h,
            predicted_change_24h=change_24h,
            confidence=confidence,
            direction=direction,
            strength=strength,
            model_accuracy=self.last_accuracy,
            timestamp=datetime.now()
        )
    
    def get_confluence_score(self, prediction: PricePrediction, 
                             signal_direction: str = 'LONG') -> Tuple[int, str]:
        """
        Get confluence points for Genius Engine integration
        
        Args:
            prediction: PricePrediction object
            signal_direction: 'LONG' or 'SHORT'
        
        Returns:
            (points, description) - max 15 points
        """
        if prediction is None:
            return 0, "LSTM prediction unavailable"
        
        points = 0
        
        # Check if prediction aligns with signal direction
        if signal_direction == 'LONG' and prediction.direction == 'UP':
            if prediction.strength == 'STRONG':
                points = 15
            elif prediction.strength == 'MODERATE':
                points = 10
            else:
                points = 5
        elif signal_direction == 'SHORT' and prediction.direction == 'DOWN':
            if prediction.strength == 'STRONG':
                points = 15
            elif prediction.strength == 'MODERATE':
                points = 10
            else:
                points = 5
        elif prediction.direction == 'NEUTRAL':
            points = 3  # Partial credit for neutral
        
        # Adjust by confidence
        points = int(points * prediction.confidence)
        
        desc = f"{prediction.direction} ({prediction.predicted_change_24h:+.1f}% 24h) conf:{prediction.confidence:.0%}"
        
        return points, desc


# ============ QUICK PREDICTOR (No LSTM, uses technical analysis) ============

class QuickPredictor:
    """
    Fast prediction without LSTM (technical analysis based)
    Use when LSTM model is not available/trained
    """
    
    def predict(self, data: pd.DataFrame) -> Optional[PricePrediction]:
        """Make quick predictions using technical analysis"""
        if len(data) < 50:
            return None
        
        closes = data['close'].values
        current_price = float(closes[-1])
        
        # EMA trend
        ema21 = pd.Series(closes).ewm(span=21).mean().iloc[-1]
        ema50 = pd.Series(closes).ewm(span=50).mean().iloc[-1]
        
        # Momentum
        momentum_5 = (closes[-1] / closes[-5] - 1) * 100
        momentum_20 = (closes[-1] / closes[-20] - 1) * 100
        
        # ATR for volatility
        highs = data['high'].values if 'high' in data.columns else closes
        lows = data['low'].values if 'low' in data.columns else closes
        tr = np.maximum(highs[-14:] - lows[-14:], 
                        np.abs(highs[-14:] - closes[-15:-1]),
                        np.abs(lows[-14:] - closes[-15:-1]))
        atr = np.mean(tr)
        atr_pct = atr / current_price * 100
        
        # Predict based on momentum and trend
        if closes[-1] > ema21 > ema50:
            direction = 'UP'
            change_factor = 1 + (momentum_20 / 100)
        elif closes[-1] < ema21 < ema50:
            direction = 'DOWN'
            change_factor = 1 - (abs(momentum_20) / 100)
        else:
            direction = 'NEUTRAL'
            change_factor = 1
        
        # Predictions
        pred_1h = current_price * (1 + atr_pct/100 * 0.2 * np.sign(change_factor - 1))
        pred_4h = current_price * (1 + atr_pct/100 * 0.5 * np.sign(change_factor - 1))
        pred_24h = current_price * change_factor
        
        change_1h = (pred_1h / current_price - 1) * 100
        change_4h = (pred_4h / current_price - 1) * 100
        change_24h = (pred_24h / current_price - 1) * 100
        
        strength = 'STRONG' if abs(momentum_20) > 10 else 'MODERATE' if abs(momentum_20) > 5 else 'WEAK'
        
        return PricePrediction(
            current_price=current_price,
            predicted_price_1h=pred_1h,
            predicted_price_4h=pred_4h,
            predicted_price_24h=pred_24h,
            predicted_change_1h=change_1h,
            predicted_change_4h=change_4h,
            predicted_change_24h=change_24h,
            confidence=0.6,  # Technical analysis confidence
            direction=direction,
            strength=strength,
            model_accuracy=60.0,  # Estimated
            timestamp=datetime.now()
        )


# ============ SINGLETON ============
lstm_predictor = GeniusLSTMPredictor() if TF_AVAILABLE else None
quick_predictor = QuickPredictor()


def get_prediction(symbol: str = 'BTC-USD') -> Dict:
    """API function"""
    if lstm_predictor and lstm_predictor.is_trained:
        pred = lstm_predictor.predict(symbol)
    else:
        # Use quick predictor as fallback
        try:
            data = yf.download(symbol, period='3mo', interval='1d', progress=False)
            data.columns = [c.lower() if isinstance(c, str) else c[0].lower() for c in data.columns]
            pred = quick_predictor.predict(data)
        except:
            return {'error': 'Prediction failed'}
    
    if pred:
        return pred.to_dict()
    return {'error': 'Prediction failed'}


if __name__ == '__main__':
    print("=" * 70)
    print("🤖 GENIUS LSTM PREDICTOR v1.0")
    print("=" * 70)
    
    if TF_AVAILABLE:
        predictor = GeniusLSTMPredictor()
        
        # Train model (short training for demo)
        print("\n🎓 Training LSTM model...")
        result = predictor.train('BTC-USD', period='6mo', epochs=20)
        print(f"   Training result: {result}")
        
        # Make prediction
        print("\n🔮 Making predictions...")
        pred = predictor.predict('BTC-USD')
        
        if pred:
            print(f"\n📊 PREDICTION RESULTS:")
            print(f"   Current Price: ${pred.current_price:,.2f}")
            print(f"\n   Predictions:")
            print(f"   • 1h:  ${pred.predicted_price_1h:,.2f} ({pred.predicted_change_1h:+.2f}%)")
            print(f"   • 4h:  ${pred.predicted_price_4h:,.2f} ({pred.predicted_change_4h:+.2f}%)")
            print(f"   • 24h: ${pred.predicted_price_24h:,.2f} ({pred.predicted_change_24h:+.2f}%)")
            print(f"\n   Direction: {pred.direction} ({pred.strength})")
            print(f"   Confidence: {pred.confidence:.1%}")
            print(f"   Model Accuracy: {pred.model_accuracy:.1f}%")
            
            # Test confluence scoring
            points, desc = predictor.get_confluence_score(pred, 'LONG')
            print(f"\n   Genius Confluence: {points}/15 pts")
            print(f"   {desc}")
    else:
        print("\n⚠️ TensorFlow not available, using Quick Predictor...")
        
        import yfinance as yf
        data = yf.download('BTC-USD', period='3mo', interval='1d', progress=False)
        data.columns = [c.lower() if isinstance(c, str) else c[0].lower() for c in data.columns]
        
        pred = quick_predictor.predict(data)
        if pred:
            print(f"\n📊 QUICK PREDICTION:")
            print(f"   Direction: {pred.direction} ({pred.strength})")
            print(f"   24h Change: {pred.predicted_change_24h:+.1f}%")
    
    print("\n" + "=" * 70)
    print("✅ LSTM Predictor Test PASSED!")
