"""
🧠 LSTM PRICE PREDICTOR - Deep Learning dla Trading
Wykorzystuje TensorFlow/Keras do predykcji cen
Używane przez Two Sigma, Renaissance Technologies
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

# TensorFlow imports
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from sklearn.preprocessing import MinMaxScaler
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

logger = logging.getLogger(__name__)


class LSTMPredictor:
    """
    LSTM-based price prediction
    Architecture used by professional quant funds
    """
    
    def __init__(self, lookback: int = 60, prediction_horizon: int = 1):
        """
        Initialize LSTM predictor
        
        Args:
            lookback: Number of past timesteps to use
            prediction_horizon: How many steps ahead to predict
        """
        self.lookback = lookback
        self.prediction_horizon = prediction_horizon
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1)) if TF_AVAILABLE else None
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
        
        if not TF_AVAILABLE:
            self.logger.warning("⚠️ TensorFlow not available - LSTM disabled")
    
    def prepare_data(self, prices: np.ndarray, 
                    features: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for LSTM training
        
        Args:
            prices: Price array
            features: Additional features (RSI, MACD, volume, etc.)
            
        Returns:
            (X, y) arrays ready for training
        """
        if not TF_AVAILABLE:
            return np.array([]), np.array([])
        
        # Combine price with features
        if features is not None:
            data = np.column_stack([prices, features])
        else:
            data = prices.reshape(-1, 1)
        
        # Normalize
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = [], []
        for i in range(self.lookback, len(scaled_data) - self.prediction_horizon):
            X.append(scaled_data[i - self.lookback:i])
            y.append(scaled_data[i + self.prediction_horizon - 1, 0])  # Predict price
        
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """
        Build LSTM architecture
        Architecture inspired by research papers + fund practices
        
        Args:
            input_shape: (timesteps, features)
            
        Returns:
            Compiled Keras model
        """
        if not TF_AVAILABLE:
            return None
        
        model = Sequential([
            # First LSTM layer with return sequences
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
            Dense(16, activation='relu'),
            Dropout(0.1),
            Dense(1)  # Output: predicted price
        ])
        
        # Use Adam optimizer with learning rate scheduling
        optimizer = keras.optimizers.Adam(learning_rate=0.001)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        self.logger.info(f"🏗️ LSTM Model built: {model.count_params():,} parameters")
        
        return model
    
    def train(self, prices: np.ndarray, features: Optional[np.ndarray] = None,
              epochs: int = 50, batch_size: int = 32, validation_split: float = 0.2) -> Dict:
        """
        Train LSTM model
        
        Args:
            prices: Historical prices
            features: Additional features
            epochs: Training epochs
            batch_size: Batch size
            validation_split: Validation data split
            
        Returns:
            Training history dict
        """
        if not TF_AVAILABLE:
            return {'status': 'tensorflow_not_available'}
        
        try:
            # Prepare data
            X, y = self.prepare_data(prices, features)
            
            if len(X) < 100:
                self.logger.warning("⚠️ Not enough data for training (need 100+)")
                return {'status': 'insufficient_data'}
            
            # Build model
            input_shape = (X.shape[1], X.shape[2])
            self.model = self.build_model(input_shape)
            
            # Callbacks
            early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.00001)
            
            # Train
            self.logger.info(f"🎓 Training LSTM on {len(X)} samples...")
            history = self.model.fit(
                X, y,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                callbacks=[early_stop, reduce_lr],
                verbose=0
            )
            
            self.is_trained = True
            
            final_loss = history.history['loss'][-1]
            final_val_loss = history.history['val_loss'][-1]
            
            self.logger.info(f"✅ LSTM trained! Loss: {final_loss:.6f}, Val Loss: {final_val_loss:.6f}")
            
            return {
                'status': 'success',
                'final_loss': float(final_loss),
                'final_val_loss': float(final_val_loss),
                'epochs_trained': len(history.history['loss'])
            }
            
        except Exception as e:
            self.logger.error(f"❌ LSTM training failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def predict(self, recent_data: np.ndarray, 
                features: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Make prediction using trained model
        
        Args:
            recent_data: Recent prices (lookback period)
            features: Recent features
            
        Returns:
            Dict with prediction and confidence
        """
        if not TF_AVAILABLE or not self.is_trained:
            return {
                'prediction': recent_data[-1] if len(recent_data) > 0 else 0,
                'confidence': 0.0,
                'status': 'model_not_trained'
            }
        
        try:
            # Prepare input
            if features is not None:
                data = np.column_stack([recent_data, features])
            else:
                data = recent_data.reshape(-1, 1)
            
            # Scale
            scaled_data = self.scaler.transform(data)
            
            # Take last lookback period
            X = scaled_data[-self.lookback:].reshape(1, self.lookback, -1)
            
            # Predict
            scaled_prediction = self.model.predict(X, verbose=0)[0][0]
            
            # Inverse transform
            dummy = np.zeros((1, scaled_data.shape[1]))
            dummy[0, 0] = scaled_prediction
            prediction = self.scaler.inverse_transform(dummy)[0, 0]
            
            # Calculate confidence based on recent prediction accuracy
            confidence = self._calculate_confidence(recent_data, prediction)
            
            self.logger.info(f"🔮 LSTM Prediction: ${prediction:.2f} (confidence: {confidence:.1%})")
            
            return {
                'prediction': float(prediction),
                'confidence': float(confidence),
                'current_price': float(recent_data[-1]),
                'predicted_change': float((prediction - recent_data[-1]) / recent_data[-1]),
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Prediction failed: {e}")
            return {
                'prediction': recent_data[-1] if len(recent_data) > 0 else 0,
                'confidence': 0.0,
                'status': 'error'
            }
    
    def _calculate_confidence(self, recent_prices: np.ndarray, prediction: float) -> float:
        """Calculate confidence score based on volatility and trend"""
        if len(recent_prices) < 2:
            return 0.5
        
        # Lower confidence if high volatility
        returns = np.diff(recent_prices) / recent_prices[:-1]
        volatility = np.std(returns)
        
        # Lower confidence if prediction is far from recent prices
        recent_mean = np.mean(recent_prices[-10:])
        deviation = abs(prediction - recent_mean) / recent_mean
        
        # Combine factors
        confidence = max(0.1, min(0.9, 1.0 - volatility * 10 - deviation * 2))
        
        return confidence
    
    def save_model(self, filepath: str):
        """Save trained model"""
        if self.model and TF_AVAILABLE:
            self.model.save(filepath)
            self.logger.info(f"💾 Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model"""
        if TF_AVAILABLE:
            try:
                self.model = load_model(filepath)
                self.is_trained = True
                self.logger.info(f"📂 Model loaded from {filepath}")
            except Exception as e:
                self.logger.error(f"❌ Model loading failed: {e}")


class EnsemblePredictor:
    """
    Ensemble of multiple models for robust predictions
    Technique used by most professional funds
    """
    
    def __init__(self):
        self.lstm_predictor = LSTMPredictor()
        self.logger = logging.getLogger(__name__)
    
    def predict_with_ensemble(self, prices: np.ndarray, 
                             technical_indicators: Dict[str, float]) -> Dict[str, float]:
        """
        Combine LSTM with technical analysis
        
        Args:
            prices: Price history
            technical_indicators: Dict with RSI, MACD, etc.
            
        Returns:
            Combined prediction
        """
        predictions = []
        weights = []
        
        # LSTM prediction
        if self.lstm_predictor.is_trained:
            lstm_result = self.lstm_predictor.predict(prices)
            if lstm_result['status'] == 'success':
                predictions.append(lstm_result['prediction'])
                weights.append(lstm_result['confidence'])
        
        # Technical analysis prediction (simple momentum)
        if len(prices) > 1:
            momentum = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
            ta_prediction = prices[-1] * (1 + momentum * 0.1)  # Conservative
            predictions.append(ta_prediction)
            weights.append(0.3)  # Lower weight for simple TA
        
        # Weighted average
        if len(predictions) > 0 and sum(weights) > 0:
            ensemble_prediction = np.average(predictions, weights=weights)
            ensemble_confidence = np.mean(weights)
        else:
            ensemble_prediction = prices[-1]
            ensemble_confidence = 0.0
        
        return {
            'prediction': float(ensemble_prediction),
            'confidence': float(ensemble_confidence),
            'num_models': len(predictions),
            'lstm_used': self.lstm_predictor.is_trained
        }


# Global instance
lstm_predictor = LSTMPredictor()
ensemble_predictor = EnsemblePredictor()
