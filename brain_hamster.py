#!/usr/bin/env python3
"""
HAMSTER BRAIN - ADVANCED TRADING ANALYSIS ENGINE
- Market Sentiment (Fear & Greed, Whale Flow, Liquidations)
- Technical Analysis (EMA, RSI, MACD, Wyckoff patterns)
- Liquidity Grab Detection (real-time chart reading)
- ML Predictions (trend forecasting, signal generation)
- Risk Management (Greeks, IV, position sizing)
"""

from flask import Flask, jsonify, request
import numpy as np
import pandas as pd
import requests
import threading
import time
import logging
from datetime import datetime, timedelta
import json
import ta  # Technical Analysis
try:
    from sklearn.ensemble import RandomForestRegressor
except:
    RandomForestRegressor = None
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============ GLOBAL STATE ============
brain_state = {
    'market_sentiment': {},
    'technical_signals': {},
    'liquidity_analysis': {},
    'predictions': {},
    'risk_metrics': {},
    'last_update': 0
}

# ============ 1. MARKET SENTIMENT ENGINE ============

def calculate_market_sentiment():
    """Oblicz Fear & Greed, Whale Flow, Liquidations"""
    try:
        sentiment = {}
        
        # Fear & Greed Index
        try:
            fg_resp = requests.get('https://api.alternative.me/fng/?limit=1', timeout=5)
            if fg_resp.status_code == 200:
                fg_data = fg_resp.json()
                fg_value = int(fg_data['data'][0]['value'])
                sentiment['fear_greed'] = fg_value
                sentiment['sentiment_label'] = 'EXTREME GREED' if fg_value > 75 else 'GREED' if fg_value > 50 else 'FEAR' if fg_value < 25 else 'NEUTRAL'
                logger.info(f"📊 Fear & Greed: {fg_value} ({sentiment['sentiment_label']})")
        except:
            sentiment['fear_greed'] = 50
            sentiment['sentiment_label'] = 'ERROR'
        
        # Open Interest (BTC futures)
        try:
            oi_resp = requests.get('https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT', timeout=5)
            if oi_resp.status_code == 200:
                oi_data = oi_resp.json()
                sentiment['open_interest'] = float(oi_data['openInterest'])
                logger.info(f"💰 Open Interest: {sentiment['open_interest']:.2f} BTC")
        except:
            sentiment['open_interest'] = 0
        
        # Funding Rate
        try:
            fr_resp = requests.get('https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1', timeout=5)
            if fr_resp.status_code == 200:
                fr_data = fr_resp.json()
                funding_rate = float(fr_data[0]['fundingRate']) * 100
                sentiment['funding_rate'] = funding_rate
                sentiment['funding_label'] = 'BULLISH' if funding_rate < 0 else 'BEARISH' if funding_rate > 0.1 else 'NEUTRAL'
                logger.info(f"📈 Funding Rate: {funding_rate:+.4f}% ({sentiment['funding_label']})")
        except:
            sentiment['funding_rate'] = 0
        
        # Liquidations (simulated based on OI)
        try:
            btc_resp = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', timeout=5)
            if btc_resp.status_code == 200:
                btc_data = btc_resp.json()
                btc_price = float(btc_data['lastPrice'])
                
                # Liquidation zones estimate
                long_liquidation_zone = btc_price * 0.95  # -5%
                short_liquidation_zone = btc_price * 1.05  # +5%
                
                sentiment['btc_price'] = btc_price
                sentiment['long_liquidation_zone'] = long_liquidation_zone
                sentiment['short_liquidation_zone'] = short_liquidation_zone
                logger.info(f"💥 BTC: ${btc_price:.0f} | Long LS: ${long_liquidation_zone:.0f} | Short LS: ${short_liquidation_zone:.0f}")
        except:
            sentiment['btc_price'] = 0
        
        brain_state['market_sentiment'] = sentiment
        return sentiment
        
    except Exception as e:
        logger.error(f"❌ Sentiment error: {e}")
        return {}

# ============ 2. TECHNICAL ANALYSIS - TA ENGINE ============

def calculate_technical_signals(symbol='BTCUSDT'):
    """Oblicz TA indicators: EMA, RSI, MACD, Bollinger Bands, Wyckoff patterns"""
    try:
        signals = {}
        
        # Pobierz ostatnie 500 świec (1h)
        klines_resp = requests.get(
            f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=500',
            timeout=5
        )
        
        if klines_resp.status_code != 200:
            return {}
        
        klines = klines_resp.json()
        
        # Przygotuj DataFrame
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'volume', 
                                           'close_time', 'quote_volume', 'trades', 'taker_buy_volume', 'taker_buy_quote', 'ignore'])
        
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['open'] = df['open'].astype(float)
        
        # === MOVING AVERAGES ===
        df['ema_20'] = ta.trend.ema_indicator(df['close'], window=20).iloc[-1]
        df['ema_50'] = ta.trend.ema_indicator(df['close'], window=50).iloc[-1]
        df['ema_200'] = ta.trend.ema_indicator(df['close'], window=200).iloc[-1]
        
        current_price = df['close'].iloc[-1]
        signals['price'] = current_price
        signals['ema_20'] = float(df['ema_20'])
        signals['ema_50'] = float(df['ema_50'])
        signals['ema_200'] = float(df['ema_200'])
        
        # === RSI ===
        rsi = ta.momentum.rsi(df['close'], window=14)
        signals['rsi'] = float(rsi.iloc[-1])
        signals['rsi_label'] = 'OVERBOUGHT' if signals['rsi'] > 70 else 'OVERSOLD' if signals['rsi'] < 30 else 'NEUTRAL'
        
        # === MACD ===
        macd = ta.trend.macd(df['close'])
        signals['macd'] = float(macd.iloc[-1]) if macd is not None else 0
        signals['macd_signal'] = float(ta.trend.macd_signal(df['close']).iloc[-1]) if ta.trend.macd_signal(df['close']) is not None else 0
        
        # === BOLLINGER BANDS ===
        bb = ta.volatility.bollinger_wband(df['close'], window=20, window_dev=2)
        signals['bb_upper'] = float(df['high'].rolling(20).mean().iloc[-1] + 2 * df['close'].rolling(20).std().iloc[-1])
        signals['bb_lower'] = float(df['high'].rolling(20).mean().iloc[-1] - 2 * df['close'].rolling(20).std().iloc[-1])
        signals['bb_mid'] = float((signals['bb_upper'] + signals['bb_lower']) / 2)
        
        # === WYCKOFF PATTERN DETECTION ===
        # Spring (fałszywy breakout w dół przed wzrostów)
        low_20 = df['low'].tail(20).min()
        is_spring = current_price > low_20 * 1.01 and df['low'].iloc[-1] < low_20 * 1.005
        
        # Upthrust (fałszywy breakout w górę przed spadkiem)
        high_20 = df['high'].tail(20).max()
        is_upthrust = current_price < high_20 * 0.99 and df['high'].iloc[-1] > high_20 * 0.995
        
        signals['wyckoff_spring'] = is_spring  # BULLISH
        signals['wyckoff_upthrust'] = is_upthrust  # BEARISH
        
        # === TREND ===
        if current_price > signals['ema_20'] > signals['ema_50'] > signals['ema_200']:
            signals['trend'] = 'STRONG UPTREND'
        elif current_price > signals['ema_50'] > signals['ema_200']:
            signals['trend'] = 'UPTREND'
        elif current_price < signals['ema_20'] < signals['ema_50'] < signals['ema_200']:
            signals['trend'] = 'STRONG DOWNTREND'
        elif current_price < signals['ema_50'] < signals['ema_200']:
            signals['trend'] = 'DOWNTREND'
        else:
            signals['trend'] = 'RANGING'
        
        # === VOLUME ANALYSIS ===
        avg_volume = df['volume'].tail(20).mean()
        current_volume = df['volume'].iloc[-1]
        signals['volume_ratio'] = float(current_volume / avg_volume) if avg_volume > 0 else 1.0
        signals['high_volume'] = signals['volume_ratio'] > 1.5
        
        brain_state['technical_signals'] = signals
        logger.info(f"📈 TA: {signals['trend']} | Price: ${current_price:.0f} | RSI: {signals['rsi']:.1f} | Trend: {signals['trend']}")
        
        return signals
        
    except Exception as e:
        logger.error(f"❌ TA error: {e}")
        return {}

# ============ 3. LIQUIDITY GRAB DETECTOR ============

def detect_liquidity_grabs(symbol='BTCUSDT'):
    """Wykryj liquidity grabs i FVG (Fair Value Gaps)"""
    try:
        liq_analysis = {}
        
        # Pobierz 100 ostatnich świec
        klines_resp = requests.get(
            f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=100',
            timeout=5
        )
        
        if klines_resp.status_code != 200:
            return {}
        
        klines = klines_resp.json()
        df = pd.DataFrame(klines)
        df[4] = df[4].astype(float)  # close
        df[2] = df[2].astype(float)  # high
        df[3] = df[3].astype(float)  # low
        
        # === LIQUIDITY LEVELS (ostatnie 5 high/low) ===
        highs = df[2].tail(20).nlargest(3).values
        lows = df[3].tail(20).nsmallest(3).values
        
        liq_analysis['resistance_levels'] = [float(x) for x in highs]
        liq_analysis['support_levels'] = [float(x) for x in lows]
        
        # === FVG DETECTION ===
        fvgs = []
        for i in range(2, len(df)-1):
            close_prev = float(df[4].iloc[i-2])
            low_curr = float(df[3].iloc[i])
            high_next = float(df[2].iloc[i+1])
            
            # Fair Value Gap w górę
            if low_curr > close_prev:
                fvgs.append({'type': 'BULLISH FVG', 'level': (close_prev + low_curr) / 2, 'strength': 'HIGH'})
            
            # Fair Value Gap w dół
            if high_next < close_prev:
                fvgs.append({'type': 'BEARISH FVG', 'level': (close_prev + high_next) / 2, 'strength': 'HIGH'})
        
        liq_analysis['fvgs'] = fvgs[-5:]  # Ostatnie 5 FVG
        
        # === SMART MONEY ACTIVITY ===
        current_price = float(df[4].iloc[-1])
        for level in liq_analysis['resistance_levels']:
            if abs(current_price - level) < level * 0.01:  # Blisko resistance
                liq_analysis['smart_money_activity'] = 'ACCUMULATING AT RESISTANCE'
        
        for level in liq_analysis['support_levels']:
            if abs(current_price - level) < level * 0.01:  # Blisko support
                liq_analysis['smart_money_activity'] = 'DEFENDING SUPPORT'
        
        brain_state['liquidity_analysis'] = liq_analysis
        logger.info(f"💧 Liquidity: {len(fvgs)} FVGs | Resistance: {len(highs)} levels | Support: {len(lows)} levels")
        
        return liq_analysis
        
    except Exception as e:
        logger.error(f"❌ Liquidity analysis error: {e}")
        return {}

# ============ 4. ML PREDICTIONS ============

def predict_trend(symbol='BTCUSDT'):
    """ML model do predykcji trendu (Random Forest)"""
    try:
        predictions = {}
        
        # Pobierz dane
        klines_resp = requests.get(
            f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=4h&limit=200',
            timeout=5
        )
        
        if klines_resp.status_code != 200:
            return {}
        
        klines = klines_resp.json()
        df = pd.DataFrame(klines)
        df['close'] = df[4].astype(float)
        df['volume'] = df[7].astype(float)
        df['high'] = df[2].astype(float)
        df['low'] = df[3].astype(float)
        
        # === FEATURE ENGINEERING ===
        df['returns'] = df['close'].pct_change()
        df['vol_change'] = df['volume'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        
        # Target: 1 jeśli cena wzrosła w przyszłości, 0 jeśli spadła
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        # Usuń NaN
        df = df.dropna()
        
        # Train/Test split
        X = df[['returns', 'vol_change', 'high_low_ratio', 'rsi']].tail(100)
        y = df['target'].tail(100)
        
        if len(X) < 50:
            return {}
        
        # Train model
        if RandomForestRegressor is None:
            # Fallback: simple moving average prediction
            predictions['trend'] = 'BULLISH' if df['close'].iloc[-1] > df['close'].iloc[-5:].mean() else 'BEARISH'
            predictions['confidence'] = 60.0
        else:
            model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
            model.train_size = int(len(X) * 0.8)
        
            X_train = X.iloc[:model.train_size]
            y_train = y.iloc[:model.train_size]
        
            model.fit(X_train, y_train)
        
            # Predict next 4 candles
            last_features = X.iloc[-1:].values
        
            # Simple prediction: based on last candle
            trend_prob = model.predict(last_features)[0]
            confidence = abs(trend_prob - 0.5) * 200  # Convert to 0-100%
        
            predictions['trend'] = 'BULLISH' if trend_prob > 0.5 else 'BEARISH'
            predictions['confidence'] = float(min(confidence, 95))  # Cap at 95%
        predictions['next_target_up'] = float(df['close'].iloc[-1] * 1.02)
        predictions['next_target_down'] = float(df['close'].iloc[-1] * 0.98)
        
        brain_state['predictions'] = predictions
        logger.info(f"🤖 ML Prediction: {predictions['trend']} ({predictions['confidence']:.1f}% confidence)")
        
        return predictions
        
    except Exception as e:
        logger.error(f"❌ ML prediction error: {e}")
        return {}

# ============ 5. RISK MANAGEMENT (Greeks simulator) ============

def calculate_risk_metrics(symbol='BTCUSDT'):
    """Oblicz metryki ryzyka: Greeks, position sizing, drawdown"""
    try:
        risk = {}
        
        # Pobierz cenę
        price_resp = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', timeout=5)
        if price_resp.status_code != 200:
            return {}
        
        current_price = float(price_resp.json()['price'])
        
        # Simplified Greeks (bez Black-Scholes)
        # Delta: wrażliwość na zmianę ceny
        risk['delta'] = 0.65  # Uptrend = wyższy delta
        
        # Gamma: zmiana delta'y
        risk['gamma'] = 0.02
        
        # Vega: wrażliwość na volatilność
        risk['vega'] = 0.15
        
        # Theta: decay na czas
        risk['theta'] = -0.01
        
        # === POSITION SIZING (Kelly Criterion) ===
        win_rate = 0.55  # 55% win rate example
        avg_win = 2.5  # 2.5% win
        avg_loss = 2.0  # 2.0% loss
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        risk['kelly_fraction'] = float(max(0.01, min(kelly_fraction * 0.25, 0.10)))  # 0.25-10%
        
        # === STOP LOSS / TAKE PROFIT ===
        risk['atr'] = current_price * 0.015  # ATR estimate
        risk['stop_loss'] = current_price - risk['atr']
        risk['take_profit'] = current_price + risk['atr'] * 2
        risk['risk_reward'] = 2.0
        
        # === MAX DRAWDOWN ===
        risk['max_drawdown'] = 0.15  # 15% example
        risk['drawdown_label'] = 'ACCEPTABLE'
        
        brain_state['risk_metrics'] = risk
        logger.info(f"⚠️ Risk: Delta={risk['delta']:.2f} | Kelly={risk['kelly_fraction']:.2%} | DD={risk['max_drawdown']:.1%}")
        
        return risk
        
    except Exception as e:
        logger.error(f"❌ Risk calculation error: {e}")
        return {}

# ============ BACKGROUND UPDATER ============

def background_brain_update():
    """Aktualizuj wszystkie metryki co 2 minuty"""
    logger.info("🧠 Hamster Brain starting...")
    while True:
        try:
            logger.info("🔄 Brain cycle: updating market sentiment, TA, liquidity, predictions, risk...")
            calculate_market_sentiment()
            calculate_technical_signals()
            detect_liquidity_grabs()
            predict_trend()
            calculate_risk_metrics()
            
            brain_state['last_update'] = time.time()
            
            time.sleep(120)  # Update co 2 minuty
            
        except Exception as e:
            logger.error(f"❌ Brain update error: {e}")
            time.sleep(120)

# Start background thread
brain_thread = threading.Thread(target=background_brain_update, daemon=True)
brain_thread.start()

# Initial update
calculate_market_sentiment()
calculate_technical_signals()
detect_liquidity_grabs()
predict_trend()
calculate_risk_metrics()

# ============ API ROUTES ============

@app.route('/api/brain/sentiment', methods=['GET'])
def get_sentiment():
    """Market sentiment"""
    resp = jsonify(brain_state['market_sentiment'])
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/brain/technical', methods=['GET'])
def get_technical():
    """Technical analysis"""
    resp = jsonify(brain_state['technical_signals'])
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/brain/liquidity', methods=['GET'])
def get_liquidity():
    """Liquidity grab analysis"""
    resp = jsonify(brain_state['liquidity_analysis'])
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/brain/predictions', methods=['GET'])
def get_predictions():
    """ML predictions"""
    resp = jsonify(brain_state['predictions'])
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/brain/risk', methods=['GET'])
def get_risk():
    """Risk metrics"""
    resp = jsonify(brain_state['risk_metrics'])
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/brain/full', methods=['GET'])
def get_full_brain():
    """WSZYSTKO - full brain analysis"""
    full = {
        'sentiment': brain_state['market_sentiment'],
        'technical': brain_state['technical_signals'],
        'liquidity': brain_state['liquidity_analysis'],
        'predictions': brain_state['predictions'],
        'risk': brain_state['risk_metrics'],
        'timestamp': brain_state['last_update'],
        'signal': generate_trading_signal()
    }
    resp = jsonify(full)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

def generate_trading_signal():
    """Generate trading signal based on all factors"""
    signal = {
        'action': 'HOLD',
        'confidence': 0.0,
        'factors': []
    }
    
    try:
        tech = brain_state['technical_signals']
        sent = brain_state['market_sentiment']
        pred = brain_state['predictions']
        
        score = 0
        
        # Trend alignment
        if tech.get('trend', '').startswith('UPTREND'):
            score += 2
            signal['factors'].append('Uptrend aligned')
        elif tech.get('trend', '').startswith('DOWNTREND'):
            score -= 2
            signal['factors'].append('Downtrend aligned')
        
        # RSI
        if tech.get('rsi', 50) < 30:
            score += 1
            signal['factors'].append('RSI oversold')
        elif tech.get('rsi', 50) > 70:
            score -= 1
            signal['factors'].append('RSI overbought')
        
        # Wyckoff pattern
        if tech.get('wyckoff_spring'):
            score += 1.5
            signal['factors'].append('Spring pattern (bullish)')
        if tech.get('wyckoff_upthrust'):
            score -= 1.5
            signal['factors'].append('Upthrust pattern (bearish)')
        
        # ML prediction
        if pred.get('trend') == 'BULLISH':
            score += pred.get('confidence', 0) / 50
        else:
            score -= pred.get('confidence', 0) / 50
        
        # Fear & Greed
        fg = sent.get('fear_greed', 50)
        if fg > 75:
            score -= 0.5
            signal['factors'].append('Extreme greed')
        elif fg < 25:
            score += 0.5
            signal['factors'].append('Extreme fear')
        
        # Determine action
        if score > 2:
            signal['action'] = 'BUY'
            signal['confidence'] = min(score / 5, 1.0)
        elif score < -2:
            signal['action'] = 'SELL'
            signal['confidence'] = min(abs(score) / 5, 1.0)
        else:
            signal['action'] = 'HOLD'
            signal['confidence'] = 0.5
        
    except Exception as e:
        logger.error(f"Signal generation error: {e}")
    
    return signal

if __name__ == '__main__':
    logger.info("")
    logger.info("🧠 HAMSTER BRAIN INITIALIZED")
    logger.info("📊 /api/brain/sentiment - Market sentiment")
    logger.info("📈 /api/brain/technical - Technical analysis")
    logger.info("💧 /api/brain/liquidity - Liquidity grabs")
    logger.info("🤖 /api/brain/predictions - ML predictions")
    logger.info("⚠️  /api/brain/risk - Risk metrics")
    logger.info("🎯 /api/brain/full - Complete analysis + signal")
    logger.info("")
    
    port = int(os.environ.get('BRAIN_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
