#!/usr/bin/env python3
"""
🚀 HAMSTER TERMINAL - ENHANCED API SERVER WITH STYLE SWITCHER
Serwuje Bloomberg clean dashboarda z API integration
Obsługuje multiple themes i real-time data
"""

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import requests
import json
import threading
import time
from datetime import datetime, timedelta, timezone
import logging
import os
import random
import pandas as pd
import base64
from io import BytesIO
from gtts import gTTS
from typing import Any, Dict, List, Set

from trading_bot.strategies.smt_killzones import KillzonesManager
from trading_bot.analysis.genius_quant import GeniusQuantEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ TWELVE DATA API CONFIG ============
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'demo')
TWELVE_DATA_BASE_URL = 'https://api.twelvedata.com'

# Flask app
app = Flask(__name__)
CORS(app)

# Cache for market data
cache = {
    'btc_price': 0,
    'btc_change_24h': 0,
    'eth_price': 0,
    'eth_change_24h': 0,
    'btc_volume': 0,
    'btc_market_cap': 0,
    'fear_greed': 0,
    'last_update': None,
    'timestamp': 0,
    'prev_price': 0,
    'prev_volume': 0,
    'stocks': {'AAPL': 0, 'MSFT': 0, 'NVDA': 0},
    'stocks_change': {'AAPL': 0, 'MSFT': 0, 'NVDA': 0},
    'crypto': {'BTCUSDT': 0, 'ETHUSDT': 0},
    'crypto_change': {'BTCUSDT': 0, 'ETHUSDT': 0},
    'indices': {'NASDAQ': 0, 'SP500': 0, 'DAX': 0},
    'indices_change': {'NASDAQ': 0, 'SP500': 0, 'DAX': 0},
    'news_headlines': [],
    'killzone_snapshot': {},
    'sniper_signal': {},
    'last_news_update': None,
    'genius_audio_cache': {}
}

# Genius state for commentary
genius_state = {
    'last_commentary': '',
    'signal': 'NEUTRAL',
    'strength': 'medium',
    'context_memory': [],
    'last_features': {}
}

killzones_manager = KillzonesManager()
genius_quant_engine = GeniusQuantEngine()

KILLZONE_LABELS = {
    'london_open': 'Killzone Londyn',
    'ny_am': 'Killzone Nowy Jork (AM)',
    'ny_pm': 'Killzone Nowy Jork (PM)',
    'asia': 'Killzone Azja'
}

KILLZONE_OVERLAYS = {
    'london_open': {'start': 7.5, 'end': 10.5, 'priority': 'high'},
    'ny_am': {'start': 12.5, 'end': 16.0, 'priority': 'high'},
    'ny_pm': {'start': 18.5, 'end': 21.0, 'priority': 'medium'},
    'asia': {'start': 1.0, 'end': 5.0, 'priority': 'low'}
}

ZONE_NOTE_LABELS = {
    'london_open': 'Londyn',
    'ny_am': 'Nowy Jork (AM)',
    'ny_pm': 'Nowy Jork (PM)',
    'asia': 'Sesja Azja'
}


def format_hour(hour_float: float) -> str:
    hour = int(hour_float)
    minute = int(round((hour_float - hour) * 60))
    if minute == 60:
        hour = (hour + 1) % 24
        minute = 0
    return f"{hour:02d}:{minute:02d}"


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def update_context_memory(entry: str) -> None:
    """Store latest Genius insights for contextual memory"""
    if not entry:
        return
    memory = genius_state.setdefault('context_memory', [])
    memory.append({'note': entry, 'timestamp': datetime.now(timezone.utc).isoformat()})
    if len(memory) > 6:
        del memory[0]


def build_live_bias_payload(features: dict) -> dict:
    """Compose live-bias metadata using heuristics and stored context"""
    change = features.get('change', 0)
    fear_greed = features.get('fear_greed', 50)
    volume_ratio = features.get('volume_ratio', 1.0)
    hour = features.get('hour', datetime.now(timezone.utc).hour)

    if change >= 1.2:
        primary_bias = 'bullish'
        playbook = 'Trend-Follow Long'
        mtf_focus = ['15m Momentum', '1h Structure', '4h Liquidity']
    elif change <= -1.2:
        primary_bias = 'bearish'
        playbook = 'Breakdown Fade Short'
        mtf_focus = ['15m Breakdown', '1h Supply', '4h Reversal']
    else:
        primary_bias = 'neutral'
        playbook = 'Range Mean Revert'
        mtf_focus = ['5m Range', '15m VWAP', '1h Liquidity Void']

    sentiment_shift = 'neutral'
    if fear_greed >= 65:
        sentiment_shift = 'overheated-greed'
    elif fear_greed <= 35:
        sentiment_shift = 'fear-driven'

    volume_note = 'standard flow'
    if volume_ratio >= 1.3:
        volume_note = 'aggressive buyers'
    elif volume_ratio <= 0.7:
        volume_note = 'exhausted volume'

    session_callout = 'Monitor Asia range rotation'
    if 7 <= hour < 11:
        session_callout = 'London open: szukaj sweepu high/low'
    elif 13 <= hour < 17:
        session_callout = 'New York open: przygotuj callouty delta/imbalances'
    elif 22 <= hour or hour < 2:
        session_callout = 'Sesja późna: uwaga na płytką płynność'

    context_memory = genius_state.get('context_memory', [])[-3:]

    return {
        'primaryBias': primary_bias,
        'playbook': playbook,
        'mtfFocus': mtf_focus,
        'sentimentShift': sentiment_shift,
        'volumeNote': volume_note,
        'sessionCallout': session_callout,
        'recentContext': context_memory
    }


SUPPORTED_TTS_LANGS = {
    'pl': 'pl',
    'en': 'en',
    'de': 'de',
    'sk': 'sk'
}


def synthesize_genius_audio(text: str, lang_code: str) -> str:
    """Generate Base64 audio for commentary using gTTS with caching"""
    if not text:
        raise ValueError('Brak tekstu do syntezy audio.')

    target_lang = SUPPORTED_TTS_LANGS.get(lang_code, 'en')
    cache_key = f"{target_lang}:{hash(text)}"
    audio_cache = cache.setdefault('genius_audio_cache', {})

    cached_audio = audio_cache.get(cache_key)
    if cached_audio:
        return cached_audio

    tts = gTTS(text=text, lang=target_lang)
    buffer = BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    audio_b64 = base64.b64encode(buffer.read()).decode('ascii')

    audio_cache[cache_key] = audio_b64
    # Keep cache from growing indefinitely
    if len(audio_cache) > 20:
        for _ in range(len(audio_cache) - 20):
            audio_cache.pop(next(iter(audio_cache)))

    return audio_b64


def update_news_cache() -> list:
    """Refresh cached news headlines, preferring live Twelve Data feed."""
    headlines = fetch_twelve_data_news()
    if headlines:
        cache['news_headlines'] = headlines
        cache['last_news_update'] = datetime.now(timezone.utc).isoformat()
        return headlines

    price = cache.get('btc_price') or 0
    change = cache.get('btc_change_24h') or 0
    fear = cache.get('fear_greed') or '--'
    now = datetime.now(timezone.utc)

    templates = [
        ('PILNE', f"BTC utrzymuje ${price:,.0f}; ETF w naplywie +{max(change*12, 0):.0f} mln$", 2, 'bullish'),
        ('MAKRO', 'Rentownosci USA cofaja sie po danych PMI, apetyt na ryzyko rosnacy', 5, 'neutral'),
        ('KRYPTO', f"Wolumen perps wzrosl +{max(change, 0):.1f}% vs 24h avg", 8, 'bullish' if change >= 0 else 'neutral'),
        ('FX', 'DXY traci dynamike; EURUSD utrzymuje sie nad 1.09', 11, 'neutral'),
        ('SUROWCE', 'Zloto stabilne przy 2k USD; ropa testuje 83 USD', 14, 'neutral'),
        ('AKCJE', 'Mega capy tech kontynuuja rajd; NVDA i MSFT prowadza', 18, 'bullish'),
        ('SENTYMENT', f"Fear & Greed Index = {fear}; monitoruj reakcje przy NY open", 20, 'neutral')
    ]

    fallback_headlines = []
    for idx, (category, headline, minutes_ago, sentiment) in enumerate(templates):
        fallback_headlines.append({
            'id': idx,
            'category': category,
            'headline': headline,
            'timeAgo': f"{minutes_ago} min temu",
            'ageMinutes': minutes_ago,
            'sentiment': sentiment,
            'timestamp': (now - timedelta(minutes=minutes_ago)).isoformat()
        })

    random.shuffle(fallback_headlines)
    cache['news_headlines'] = fallback_headlines
    cache['last_news_update'] = now.isoformat()
    return fallback_headlines


def build_sniper_levels(seconds_remaining: int) -> dict:
    price = cache.get('btc_price') or 0
    change = cache.get('btc_change_24h') or 0
    bias = 'bullish' if change >= 0 else 'bearish'

    entry_factor = 0.9985 if bias == 'bullish' else 1.0015
    tp1_factor = 1.0120 if bias == 'bullish' else 0.9880
    tp2_factor = 1.0240 if bias == 'bullish' else 0.9760
    stop_factor = 0.9925 if bias == 'bullish' else 1.0075

    sniper = {
        'entry': round(price * entry_factor, 2) if price else None,
        'targets': [
            round(price * tp1_factor, 2) if price else None,
            round(price * tp2_factor, 2) if price else None
        ],
        'stop': round(price * stop_factor, 2) if price else None,
        'bias': bias,
        'timerText': format_duration(seconds_remaining),
        'changePercent': round(change, 2)
    }
    return sniper


def update_killzone_cache() -> dict:
    now = pd.Timestamp.utcnow()
    current_zone = killzones_manager.get_current_killzone(now)
    upcoming_zone = killzones_manager.get_next_killzone(now)

    overlays = []
    for name, meta in KILLZONE_OVERLAYS.items():
        overlays.append({
            'name': name,
            'label': KILLZONE_LABELS.get(name, name.replace('_', ' ').title()),
            'startMinute': int(meta['start'] * 60),
            'endMinute': int(meta['end'] * 60),
            'startTime': format_hour(meta['start']),
            'endTime': format_hour(meta['end']),
            'priority': meta['priority']
        })

    current_overlay = next((item for item in overlays if item['name'] == current_zone['name']), None)
    upcoming_overlay = None
    if upcoming_zone:
        upcoming_overlay = next((item for item in overlays if item['name'] == upcoming_zone['name']), None)

    seconds_into_candle = ((now.minute % 5) * 60) + now.second
    seconds_remaining = 300 - seconds_into_candle
    if seconds_remaining < 0:
        seconds_remaining = 0

    current_hour = now.hour + now.minute / 60.0
    minutes_remaining = None
    if current_overlay:
        end_hour = KILLZONE_OVERLAYS[current_overlay['name']]['end']
        minutes_remaining = max(0, int((end_hour - current_hour) * 60))

    next_start_minutes = None
    if upcoming_overlay:
        start_hour = KILLZONE_OVERLAYS[upcoming_overlay['name']]['start']
        next_start_minutes = max(0, int((start_hour - current_hour) * 60))

    sniper = build_sniper_levels(seconds_remaining)

    ai_zone = ZONE_NOTE_LABELS.get(current_zone['name'], current_zone['name'])
    if current_zone['active']:
        ai_note = f"Killzone {ai_zone} aktywna. Bias {sniper['bias']} - weryfikuj Sniper i momentum."
    else:
        ai_note = f"Poza kluczowymi killzone. Przygotuj wejscia pod {ZONE_NOTE_LABELS.get(upcoming_zone['name'], upcoming_zone['name']) if upcoming_zone else 'kolejna sesje'}."

    snapshot = {
        'timestamp': now.isoformat(),
        'current': {
            'name': current_zone['name'],
            'label': KILLZONE_LABELS.get(current_zone['name'], current_zone['name']),
            'active': current_zone['active'],
            'priority': current_zone['priority'],
            'recommendation': current_zone['recommendation'],
            'startTime': current_overlay['startTime'] if current_overlay else None,
            'endTime': current_overlay['endTime'] if current_overlay else None,
            'minutesRemaining': minutes_remaining
        },
        'upcoming': {
            'name': upcoming_zone['name'],
            'label': KILLZONE_LABELS.get(upcoming_zone['name'], upcoming_zone['name']),
            'priority': upcoming_zone['priority'],
            'startTime': upcoming_overlay['startTime'] if upcoming_overlay else None,
            'minutesUntilStart': next_start_minutes
        } if upcoming_zone else None,
        'overlays': overlays,
        'sessionClock': {
            'candleSecondsRemaining': seconds_remaining,
            'timerText': format_duration(seconds_remaining),
            'interval': '5m'
        },
        'sniper': sniper,
        'aiNote': ai_note
    }

    cache['killzone_snapshot'] = snapshot
    cache['sniper_signal'] = sniper
    return snapshot

# Optional ML model for Genius
try:
    from genius_model import load_model, infer_signal, commentary_for
    GENIUS_MODEL = load_model()
    print("[ML] Model zaladowany pomyslnie!")
except Exception as e:
    GENIUS_MODEL = None
    print(f"[WARNING] Model nie zaladowany: {e}")
    import traceback
    traceback.print_exc()

# ========== DATA FETCHERS ==========

def fetch_binance_data():
    """Fetch real-time data from Binance"""
    try:
        # BTC Price
        btc_resp = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr',
            params={'symbol': 'BTCUSDT'},
            timeout=5
        )
        if btc_resp.status_code == 200:
            btc_data = btc_resp.json()
            cache['btc_price'] = float(btc_data['lastPrice'])
            cache['btc_change_24h'] = float(btc_data['priceChangePercent'])
            cache['btc_volume'] = float(btc_data['quoteAssetVolume'])
            logger.info(f"✅ BTC: ${cache['btc_price']:,.2f} ({cache['btc_change_24h']:+.2f}%)")
        
        # Market cap (from CoinGecko)
        cg_resp = requests.get(
            'https://api.coingecko.com/api/v3/simple/data',
            params={
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_market_cap': 'true'
            },
            timeout=5
        )
        if cg_resp.status_code == 200:
            cg_data = cg_resp.json()
            if 'bitcoin' in cg_data and 'usd_market_cap' in cg_data['bitcoin']:
                cache['btc_market_cap'] = cg_data['bitcoin']['usd_market_cap']
        
        # ETH Price
        eth_resp = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr',
            params={'symbol': 'ETHUSDT'},
            timeout=5
        )
        if eth_resp.status_code == 200:
            eth_data = eth_resp.json()
            cache['eth_price'] = float(eth_data['lastPrice'])
        
        return True
    except Exception as e:
        logger.error(f"❌ Binance fetch error: {e}")
        return False

def fetch_fear_greed():
    """Fetch Fear & Greed Index"""
    try:
        resp = requests.get(
            'https://api.alternative.me/fng/?limit=1',
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data['data'] and len(data['data']) > 0:
                cache['fear_greed'] = int(data['data'][0]['value'])
                logger.info(f"✅ Fear & Greed: {cache['fear_greed']}")
                return True
    except Exception as e:
        logger.error(f"❌ Fear & Greed fetch error: {e}")
    return False

def fetch_twelve_data_quote(symbol='BTCUSDT'):
    """Fetch quote from Twelve Data API"""
    try:
        params = {
            'symbol': symbol,
            'apikey': TWELVE_DATA_API_KEY
        }
        response = requests.get(
            f'{TWELVE_DATA_BASE_URL}/quote',
            params=params,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'error' not in data:
                def _to_float(value: Any) -> float:
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        return 0.0

                price = _to_float(data.get('last_price') or data.get('close') or data.get('price'))
                change = _to_float(data.get('percent_change') or data.get('change_percent') or data.get('change'))
                volume = _to_float(data.get('volume') or data.get('average_volume') or data.get('rolling_volume'))
                bid = _to_float(data.get('bid'))
                ask = _to_float(data.get('ask'))

                if price != 0.0 or change != 0.0:
                    return {
                        'price': price,
                        'change': change,
                        'volume': volume,
                        'bid': bid,
                        'ask': ask
                    }
    except Exception as e:
        logger.error(f"❌ Twelve Data error ({symbol}): {e}")
    return None

def fetch_twelve_data_assets():
    """Fetch BTC, ETH, and select equities from Twelve Data."""
    try:
        # BTC
        btc_data = fetch_twelve_data_quote('BTC/USD')
        if btc_data:
            cache['btc_price'] = btc_data['price']
            cache['btc_change_24h'] = btc_data['change']
            cache['btc_volume'] = btc_data['volume']
            cache['crypto']['BTCUSDT'] = btc_data['price']
            cache['crypto_change']['BTCUSDT'] = btc_data['change']
            logger.info(f"[DATA] BTC: ${btc_data['price']:,.2f} ({btc_data['change']:+.2f}%)")

        # ETH
        eth_data = fetch_twelve_data_quote('ETH/USD')
        if eth_data:
            cache['eth_price'] = eth_data['price']
            cache['eth_change_24h'] = eth_data['change']
            cache['crypto']['ETHUSDT'] = eth_data['price']
            cache['crypto_change']['ETHUSDT'] = eth_data['change']
            logger.info(f"[DATA] ETH: ${eth_data['price']:,.2f} ({eth_data['change']:+.2f}%)")

        # STOCKS
        for stock in ['AAPL', 'MSFT', 'NVDA']:
            stock_data = fetch_twelve_data_quote(stock)
            if stock_data:
                cache['stocks'][stock] = stock_data['price']
                cache['stocks_change'][stock] = stock_data['change']
                logger.info(f"[DATA] {stock}: ${stock_data['price']:,.2f} ({stock_data['change']:+.2f}%)")

        return True
    except Exception as e:
        logger.error(f"[ERROR] Twelve Data asset fetch error: {e}")
        return False
def fetch_twelve_data_news(symbols=None, per_symbol_limit=3):
    """Fetch latest news from Twelve Data for a basket of symbols."""
    if symbols is None:
        symbols = ['BTC/USD', 'ETH/USD', 'AAPL', 'MSFT', 'SPX']

    collected: List[Dict[str, Any]] = []
    seen_titles: Set[str] = set()
    now = datetime.now(timezone.utc)

    for symbol in symbols:
        try:
            params = {
                'symbol': symbol,
                'limit': per_symbol_limit,
                'apikey': TWELVE_DATA_API_KEY
            }
            response = requests.get(
                f'{TWELVE_DATA_BASE_URL}/news',
                params=params,
                timeout=5
            )
            if response.status_code != 200:
                continue
            payload = response.json()
            items = payload.get('data') if isinstance(payload, dict) else None
            if not items:
                continue
            for item in items:
                title = item.get('title') or item.get('headline') or ''
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                published_raw = item.get('datetime') or item.get('date') or item.get('published_at')
                published_dt = None
                if isinstance(published_raw, str):
                    raw = published_raw.strip()
                    try:
                        published_dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
                    except ValueError:
                        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):  # noqa: E241
                            try:
                                published_dt = datetime.strptime(raw[:19], fmt)
                                break
                            except ValueError:
                                continue
                if published_dt is None:
                    published_dt = now

                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)

                minutes_ago = max(0, int((now - published_dt).total_seconds() // 60)) if published_dt else None
                time_label = f"{minutes_ago} min temu" if minutes_ago is not None else '--'

                collected.append({
                    'category': item.get('source', symbol) or symbol,
                    'headline': title,
                    'timeAgo': time_label,
                    'ageMinutes': minutes_ago if minutes_ago is not None else 0,
                    'sentiment': item.get('sentiment', '').lower() if isinstance(item.get('sentiment'), str) else 'neutral',
                    'symbol': symbol,
                    'url': item.get('url') or item.get('link')
                })
        except Exception as news_exc:  # pragma: no cover - network errors
            logger.warning(f"[WARN] Twelve Data news fetch error ({symbol}): {news_exc}")
            continue

    # Sort by recency and cap total volume
    collected.sort(key=lambda x: x.get('ageMinutes', 9999))
    top_items = collected[:20]
    for idx, item in enumerate(top_items):
        item['id'] = idx
    return top_items

    

def data_update_loop() -> None:
    """Background loop keeping market data and news fresh."""
    while True:
        try:
            fetch_twelve_data_assets()
            fetch_fear_greed()
            update_news_cache()
            update_killzone_cache()
            cache['last_update'] = datetime.now(timezone.utc).isoformat()
            cache['timestamp'] = time.time()
            logger.info(
                f"[LOOP] Genius signal: {genius_state.get('signal', '--')} "
                f"({genius_state.get('strength', '--')})"
            )
            time.sleep(30)
        except Exception as loop_exc:  # pragma: no cover - resilience against runtime issues
            logger.error(f"[ERROR] Update loop error: {loop_exc}")
            time.sleep(30)

# ========== API ENDPOINTS ==========

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'Hamster Terminal - Bloomberg Clean API',
        'version': '2.0',
        'status': 'active',
        'endpoints': {
            '/api/binance/summary': 'Get BTC/ETH prices and market data',
            '/api/fear-greed': 'Get Fear & Greed Index',
            '/api/genius/commentary': 'Get live Hamster Genius commentary + signal',
            '/api/status': 'Get API server status',
            '/dashboard': 'Load Bloomberg dashboard with API'
        }
    })

@app.route('/api/binance/summary')
def binance_summary():
    """Get BTC/ETH market summary from Twelve Data"""
    return jsonify({
        'ok': True,
        'btcPrice': cache['btc_price'],
        'btcChange24h': cache['btc_change_24h'],
        'btcVolume': cache['btc_volume'],
        'btcMarketCap': cache['btc_market_cap'],
        'ethPrice': cache['eth_price'],
        'ethChange24h': cache['eth_change_24h'],
        'stocks': cache['stocks'],
        'stocksChange': cache['stocks_change'],
        'crypto': cache['crypto'],
        'cryptoChange': cache['crypto_change'],
        'indices': cache['indices'],
        'indicesChange': cache['indices_change'],
        'fearGreed': cache['fear_greed'],
        'timestamp': cache['timestamp'],
        'lastUpdate': cache['last_update']
    })

@app.route('/api/fear-greed')
def fear_greed():
    """Get Fear & Greed Index"""
    return jsonify({
        'ok': True,
        'fear_greed': cache['fear_greed'],
        'timestamp': cache['timestamp']
    })

@app.route('/api/genius/commentary')
def genius_commentary():
    """Generate live Genius commentary enhanced by ML when available"""
    try:
        btc = cache['btc_price']
        change = cache['btc_change_24h']
        fear_greed = cache['fear_greed']
        volume = cache['btc_volume']
        prev_vol = cache.get('prev_volume', max(1.0, volume))
        vol_ratio = (volume / prev_vol) if prev_vol else 1.0
        hour = datetime.now().hour
        # Optional extra flow features if analytics computed
        long_short_ratio = 1.0
        
        # Compose feature dict
        features = {
            'change': change,
            'fear_greed': fear_greed,
            'volume_ratio': vol_ratio,
            'hour': hour,
            'long_short_ratio': long_short_ratio,
        }
        
        # Quant insight
        quant_symbol = request.args.get('symbol', 'BTCUSDT')
        quant_report: Dict[str, Any]
        try:
            quant_report = genius_quant_engine.analyze_market(quant_symbol)
            cache['genius_quant'] = quant_report
        except Exception as quant_exc:  # pragma: no cover - safe guard for runtime failures
            logger.error(f"❌ Genius quant engine error: {quant_exc}")
            quant_report = {'ok': False, 'error': str(quant_exc)}

        # Use ML model if present, else heuristics
        if GENIUS_MODEL is not None:
            signal, strength, score = infer_signal(GENIUS_MODEL, features)
            commentary = commentary_for(signal, strength, features) + f" | ML score {score:.2f}"
        else:
            # Fallback to previous rule-based logic
            signal = 'NEUTRAL'
            strength = 'medium'
            commentary = ''
            if change > 1.5:
                signal = 'BULL'; strength = 'strong'
                commentary = f"🟢 BTC momentum strong (+{change:.2f}%). Byki dominują. Utrzymaj longa, podnieś SL pod 95.1k."
            elif change > 0.5:
                signal = 'BULL'; strength = 'medium'
                commentary = f"🟢 Lekki wzrost (+{change:.2f}%). Trend pozytywny. Czekaj na retest 95.2k FVG."
            elif change < -1.5:
                signal = 'BEAR'; strength = 'strong'
                commentary = f"🔴 Spadek ostry ({change:.2f}%). Bieżnie protect longs. Czekaj na support 94.8k."
            elif change < -0.5:
                signal = 'BEAR'; strength = 'medium'
                commentary = f"🔴 Pullback ({change:.2f}%). Zmiana nastroju. Uważaj na poziom 95k."
            else:
                commentary = "⭕ Konsolidacja. RSI likely 45-55. Scalp opportunity w FVG."
            if fear_greed > 70:
                commentary += f" | Fear&Greed {fear_greed} (GREED) → rezerwuj 30% TP na 97.4k."
            elif fear_greed < 30:
                commentary += f" | Fear&Greed {fear_greed} (FEAR) → trzymaj hedgi, czekaj na reversal."
            if vol_ratio > 1.2 and strength == 'medium':
                strength = 'strong'
                commentary += " | Wolumen +20% → potwierdzenie trendu. Zwiększ pozycję."
            if 8 <= hour < 11:
                commentary += " | LONDON OPEN: szukaj sweepu. Volatilność OK."
            elif 14 <= hour < 17:
                commentary += " | NEW YORK OPEN: watch liquidity sweep. Trend może przyspieszyć."
        
        genius_state['last_commentary'] = commentary
        genius_state['signal'] = signal
        genius_state['strength'] = strength
        genius_state['last_features'] = features
        update_context_memory(commentary)
        live_bias = build_live_bias_payload(features)
        
        return jsonify({
            'ok': True,
            'commentary': commentary,
            'signal': signal,
            'strength': strength,
            'btc_price': btc,
            'change_24h': change,
            'fear_greed': fear_greed,
            'timestamp': cache['timestamp'],
            'liveBias': live_bias,
            'quant': quant_report
        })
    except Exception as e:
        logger.error(f"❌ Genius commentary error: {e}")
        return jsonify({
            'ok': False,
            'commentary': '⭕ Genius loading...',
            'error': str(e)
        }), 500


@app.route('/api/genius/live-bias')
def genius_live_bias():
    """Expose Genius live-bias details and context memory"""
    try:
        features = genius_state.get('last_features') or {}
        payload = build_live_bias_payload(features)
        return jsonify({
            'ok': True,
            'signal': genius_state.get('signal', 'NEUTRAL'),
            'strength': genius_state.get('strength', 'medium'),
            'liveBias': payload,
            'timestamp': cache.get('timestamp')
        })
    except Exception as e:
        logger.error(f"❌ Genius live-bias error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/genius/audio')
def genius_audio():
    """Serve audio commentary in requested language"""
    try:
        lang = request.args.get('lang', 'pl').lower()
        commentary_text = request.args.get('text') or genius_state.get('last_commentary')
        if not commentary_text:
            return jsonify({'ok': False, 'error': 'Brak komentarza do odczytania.'}), 400

        audio_b64 = synthesize_genius_audio(commentary_text, lang)
        return jsonify({
            'ok': True,
            'language': lang,
            'audioBase64': audio_b64,
            'mimeType': 'audio/mpeg'
        })
    except Exception as e:
        logger.error(f"❌ Genius audio error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/news/headlines')
def news_headlines():
    """Return curated news headlines for Bloomberg ticker"""
    try:
        if not cache.get('news_headlines'):
            update_news_cache()
        return jsonify({
            'ok': True,
            'timestamp': cache.get('last_news_update'),
            'headlines': cache.get('news_headlines', [])
        })
    except Exception as e:
        logger.error(f"❌ News endpoint error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/killzones/overview')
def killzones_overview():
    """Return session killzone snapshot for overlay"""
    try:
        if not cache.get('killzone_snapshot'):
            update_killzone_cache()
        snapshot = cache.get('killzone_snapshot', {})
        return jsonify({'ok': True, **snapshot})
    except Exception as e:
        logger.error(f"❌ Killzone endpoint error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

# ========== ERROR HANDLERS ==========

@app.route('/api/status')
def status():
    """Get API server status"""
    return jsonify({
        'ok': True,
        'status': 'active',
        'timestamp': cache['timestamp'],
        'lastUpdate': cache['last_update'],
        'dataPoints': {
            'btc': cache['btc_price'],
            'eth': cache['eth_price'],
            'fear_greed': cache['fear_greed']
        }
    })

@app.route('/api/analytics')
def analytics():
    """Get advanced analytics data for radar, heatmaps, flow analysis"""
    try:
        btc = cache['btc_price']
        change = cache['btc_change_24h']
        fear_greed = cache['fear_greed']
        
        # Calculate derived metrics
        volatility_24h = abs(change) * random.uniform(0.8, 1.2)  # Mock volatility
        liquidation_long = random.uniform(40, 50)  # Mock liquidation
        liquidation_short = random.uniform(15, 25)
        
        # Correlation mock data (could integrate with real sources)
        correlations = {
            'btc_eth': 0.75 + random.uniform(-0.15, 0.15),
            'btc_aapl': 0.35 + random.uniform(-0.15, 0.15),
            'btc_dxy': -0.42 + random.uniform(-0.15, 0.15),
            'btc_vix': -0.28 + random.uniform(-0.15, 0.15),
            'btc_nasdaq': 0.58 + random.uniform(-0.15, 0.15)
        }
        
        return jsonify({
            'ok': True,
            'timestamp': cache['timestamp'],
            'radar': {
                'fvg': {
                    '1h': {'low': btc * 0.996, 'high': btc * 1.002, 'type': 'BUY'},
                    '4h': {'low': btc * 1.008, 'high': btc * 1.018, 'type': 'SELL'},
                    '1d': {'low': btc * 0.971, 'high': btc * 0.980, 'type': 'DEMAND'}
                },
                'eql_eqh': {
                    'eql': btc * 0.985,
                    'eqh': btc * 1.020,
                    'range': btc * 0.035
                },
                'premium_index': {
                    'spot_perps': 0.12 + random.uniform(-0.05, 0.05),
                    'funding': 0.008 + random.uniform(-0.003, 0.003)
                },
                'liquidations': {
                    'long_count': liquidation_long,
                    'short_count': liquidation_short,
                    'total_24h': liquidation_long + liquidation_short
                },
                'signal_strength': {
                    'bullish': 55 + random.randint(-10, 10),
                    'bearish': 45 + random.randint(-10, 10)
                }
            },
            'heatmaps': {
                'correlations': correlations,
                'volume_profile': [0.052, 0.087, 0.091, 0.063, 0.041],
                'microstructure': {
                    'bid_ask_spread': 0.12,
                    'order_imbalance': 1.34,
                    'vwap_deviation': 0.08,
                    'momentum': 'STRONG',
                    'order_flow': 'POSITIVE'
                }
            },
            'flow': {
                'whale_accumulation': 2300 + random.randint(-500, 500),
                'exchange_inflows': -120 + random.randint(-30, 30),
                'dark_pool_flow': 680 + random.randint(-100, 100),
                'order_flow_imbalance': 58 + random.randint(-5, 5),
                'long_short_ratio': 1.18 + random.uniform(-0.1, 0.1),
                'open_interest': 14200 + random.randint(-500, 500),
                'skew_index': -0.12 + random.uniform(-0.05, 0.05),
                'cascade_risk': 'MEDIUM'
            },
            'fear_greed': fear_greed,
            'btc_price': btc,
            'btc_change_24h': change,
            'volatility_24h': volatility_24h
        })
    except Exception as e:
        logger.error(f"❌ Analytics endpoint error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ========== MAIN ==========

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 HAMSTER TERMINAL - BLOOMBERG CLEAN API SERVER v2.0")
    print("=" * 80)
    print(f"Server: http://0.0.0.0:5000")
    print(f"Dashboard: http://localhost:5000/dashboard")
    print(f"API Docs: http://localhost:5000/")
    print("")
    print("📡 Real-time data sources:")
    print("  • Twelve Data API (BTC/ETH, STOCKS, FOREX)")
    print("  • Alternative.me (Fear & Greed Index)")
    print("")
    print("🔄 Data update interval: 30 seconds")
    print("=" * 80)
    print("")
    
    # Start background data updater
    update_thread = threading.Thread(target=data_update_loop, daemon=True)
    update_thread.start()
    
    # Initial data fetch
    fetch_twelve_data_assets()
    fetch_fear_greed()
    update_news_cache()
    update_killzone_cache()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
