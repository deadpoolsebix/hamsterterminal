#!/usr/bin/env python
"""Utility helpers for advanced ML/RL integrations (TensorFlow & TensorTrade).

The routines exposed here are designed to be resilient: if optional
libraries are missing, the helpers will degrade gracefully and surface
clear status messages so the rest of the system can keep operating.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

try:  # TensorFlow / Keras stack
    import tensorflow as tf  # type: ignore

    TF_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    tf = None  # type: ignore
    TF_AVAILABLE = False

try:  # TensorTrade RL framework
    import tensortrade  # type: ignore

    TENSORTRADE_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    tensortrade = None  # type: ignore
    TENSORTRADE_AVAILABLE = False


@dataclass
class TensorTradeReport:
    """Structured output returned by the training helper."""

    status: str
    prediction: Optional[float]
    expected_move_pct: Optional[float]
    direction: Optional[str]
    confidence: Optional[float]
    notes: List[str]
    framework: str
    tensortrade_ready: bool

    def as_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "prediction": self.prediction,
            "expected_move_pct": self.expected_move_pct,
            "direction": self.direction,
            "confidence": self.confidence,
            "notes": self.notes,
            "framework": self.framework,
            "tensortrade_ready": self.tensortrade_ready,
        }


def is_tensortrade_available() -> bool:
    """Return True if the TensorTrade package is importable."""

    return TENSORTRADE_AVAILABLE


def is_tensorflow_available() -> bool:
    """Return True if TensorFlow is importable."""

    return TF_AVAILABLE


def _build_lstm_model(window_size: int) -> "tf.keras.Model":  # pragma: no cover - requires TF
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(window_size, 1)),
            tf.keras.layers.LSTM(32, activation="tanh"),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1, activation="linear"),
        ]
    )
    model.compile(optimizer="adam", loss="mse")
    return model


def _prepare_sequences(prices: np.ndarray, window_size: int) -> (np.ndarray, np.ndarray):
    x, y = [], []
    for idx in range(len(prices) - window_size):
        window = prices[idx : idx + window_size]
        target = prices[idx + window_size]
        x.append(window)
        y.append(target)
    x_arr = np.array(x, dtype="float32").reshape(-1, window_size, 1)
    y_arr = np.array(y, dtype="float32").reshape(-1, 1)
    return x_arr, y_arr


def run_tensortrade_training(
    closes: List[float],
    window_size: int = 24,
    epochs: int = 5,
) -> Dict[str, object]:
    """
    Train a lightweight sequence model on recent price closes.

    - Uses TensorFlow/Keras when available to produce an actionable forecast.
    - Exposes TensorTrade availability so the caller can escalate to more
      advanced RL workflows (TensorTrade typically requires a richer data feed
      and longer training runs, which are outside this helper's scope).
    """

    closes_array = np.asarray(closes, dtype="float32")
    closes_array = closes_array[~np.isnan(closes_array)]

    report = TensorTradeReport(
        status="unavailable",
        prediction=None,
        expected_move_pct=None,
        direction=None,
        confidence=None,
        notes=[],
        framework="tensorflow" if TF_AVAILABLE else "",
        tensortrade_ready=TENSORTRADE_AVAILABLE,
    )

    if closes_array.size <= window_size:
        report.status = "insufficient_data"
        report.notes.append(
            f"Need at least {window_size + 10} candles, got {closes_array.size}."
        )
        return report.as_dict()

    last_price = float(closes_array[-1])

    if not TF_AVAILABLE:
        report.status = "tensorflow_missing"
        report.notes.append("TensorFlow not installed - install tensorflow to enable modelling.")
        return report.as_dict()

    try:
        x_train, y_train = _prepare_sequences(closes_array, window_size)
        model = _build_lstm_model(window_size)
        model.fit(x_train, y_train, epochs=epochs, batch_size=16, verbose=0)

        last_sequence = closes_array[-window_size:].reshape(1, window_size, 1)
        prediction = float(model.predict(last_sequence, verbose=0)[0][0])

        expected_move_pct = (prediction - last_price) / last_price * 100
        direction = "BULLISH" if prediction >= last_price else "BEARISH"
        confidence = float(min(abs(expected_move_pct) * 2, 95.0))

        report.status = "trained"
        report.prediction = prediction
        report.expected_move_pct = expected_move_pct
        report.direction = direction
        report.confidence = confidence

        if TENSORTRADE_AVAILABLE:
            report.notes.append(
                "TensorTrade detected: configure a dedicated RL pipeline to complement the LSTM forecast."
            )
        else:
            report.notes.append(
                "TensorTrade not installed - install tensortrade to unlock RL-based strategies."
            )
        report.notes.append(
            "LSTM trained on windowed closes; short horizon forecast suitable for bias confirmation."
        )
        return report.as_dict()
    except Exception as exc:  # pragma: no cover - defensive
        report.status = "error"
        report.notes.append(f"TensorFlow training error: {exc}")
        return report.as_dict()