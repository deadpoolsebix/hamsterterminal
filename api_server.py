#!/usr/bin/env python3
"""
🚀 HAMSTER TERMINAL - REAL-TIME API SERVER
Serwuje rzeczywiste dane z Twelve Data (crypto, stock, forex)
WebSocket support dla real-time bez lagów
Endpoints dla dashboarda (localhost:5000)
Enhanced with AI Sentiment Analysis & LLM Integration
"""

from flask import Flask, jsonify, request, render_template_string, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
import json
import threading
import time
from datetime import datetime, timedelta
import logging
import os
import websockets
import numpy as np
import asyncio
import random

# AI/ML Modules Integration
try:
    from sentiment_analyzer import SentimentAnalyzer
    from news_processor import NewsProcessor
    from llm_genius_integration import LLMGeniusIntegration
    AI_MODULES_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ AI Modules loaded successfully!")
except ImportError as e:
    AI_MODULES_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ AI Modules not available: {e}")

# Advanced Quant Modules
try:
    from portfolio_optimizer import portfolio_optimizer
    from lstm_predictor import lstm_predictor, ensemble_predictor
    from exchange_manager import exchange_manager
    from backtest_engine import backtest_engine
    QUANT_MODULES_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Quant Modules loaded (Portfolio, LSTM, Exchange, Backtest)!")
except ImportError as e:
    QUANT_MODULES_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Quant Modules not available: {e}")

# JP Morgan Quant Methods (Twelve Data Pro)
try:
    from jpmorgan_quant_methods import (
        twelve_data, live_analyzer, options_pricer, volatility_analyzer,
        credit_analyzer, financial_ratios, risk_metrics, crypto_risk,
        TwelveDataClient, LiveMarketAnalyzer, OptionsPricer, CryptoRiskAnalyzer
    )
    JPMORGAN_MODULES_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ JP Morgan Quant Methods loaded (Options, Volatility, Z-Score, Risk)!")
except ImportError as e:
    JPMORGAN_MODULES_AVAILABLE = False
    twelve_data = None
    live_analyzer = None
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ JP Morgan Quant Methods not available: {e}")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ API CONFIG ============
# Twelve Data - stocks, crypto, forex (Pro plan)
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'demo')
TWELVE_DATA_BASE_URL = 'https://api.twelvedata.com'
TWELVE_DATA_WS_URL = 'wss://ws.twelvedata.com/v1/quotes/price'

# CryptoPanic - free crypto news
CRYPTOPANIC_API_URL = 'https://cryptopanic.com/api/v1/posts/'
CRYPTOPANIC_AUTH_TOKEN = os.getenv('CRYPTOPANIC_TOKEN', 'free')  # 'free' works for basic access

# NewsAPI - general market news
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')
NEWSAPI_BASE_URL = 'https://newsapi.org/v2'

app = Flask(__name__)
CORS(app)  # Enable CORS for all endpoints
socketio = SocketIO(app, cors_allowed_origins="*")

# ============ AI MODULES INITIALIZATION ============
if AI_MODULES_AVAILABLE:
    sentiment_analyzer = SentimentAnalyzer()
    news_processor = NewsProcessor()
    llm_genius = LLMGeniusIntegration()
    logger.info("🧠 Genius Hamster AI Brain activated!")
else:
    sentiment_analyzer = None
    news_processor = None
    llm_genius = None
    logger.warning("🐹 Genius Hamster running in basic mode (no AI)")

# ============ CACHE SYSTEM ============
cache = {
    'btc_price': 89237.00,
    'btc_change': -0.38,
    'eth_price': 3145.32,
    'eth_change': -0.50,
    # Additional cryptos
    'sol_price': 185.50,
    'sol_change': 3.2,
    'xrp_price': 2.45,
    'xrp_change': 1.5,
    'bnb_price': 685.00,
    'bnb_change': 0.8,
    'ada_price': 0.92,
    'ada_change': 2.1,
    'doge_price': 0.385,
    'doge_change': 4.5,
    'avax_price': 38.50,
    'avax_change': 2.8,
    'dot_price': 7.50,
    'dot_change': 1.8,
    'link_price': 15.80,
    'link_change': 1.2,
    'uni_price': 8.45,
    'uni_change': 0.9,
    'atom_price': 9.20,
    'atom_change': 1.5,
    'ltc_price': 105.50,
    'ltc_change': 0.7,
    'fear_greed': 62,
    'volume_24h': 24500000000,
    'funding_rate': 0.0082,
    'open_interest': 12400000000,
    'last_update': None,
    'timestamp': 0,
    # Stock data
    'spy_price': 470.00,
    'spy_change': 0.8,
    'aapl_price': 235.50,
    'aapl_change': 0.5,
    'msft_price': 425.75,
    'msft_change': 0.3,
    'nvda_price': 145.20,
    'nvda_change': 1.2,
    'tsla_price': 248.50,
    'tsla_change': 1.8,
    'amzn_price': 185.20,
    'amzn_change': 0.6,
    'googl_price': 175.80,
    'googl_change': 0.4,
    'meta_price': 485.30,
    'meta_change': 1.1,
    # Indices
    'nasdaq_price': 17850.00,
    'nasdaq_change': 0.9,
    'dax_price': 19420.00,
    'dax_change': 0.5,
    'dow_price': 38650.00,
    'dow_change': 0.3,
    # Forex data
    'eurusd_price': 1.0850,
    'eurusd_change': 0.2,
    'gbpusd_price': 1.2650,
    'gbpusd_change': -0.1,
    # Additional market data
    'gold_price': 2650.00,
    'gold_change': 0.5,
    'silver_price': 30.50,
    'silver_change': 0.3,
    'dxy_price': 103.50,
    'dxy_change': -0.2,
    'news_headlines': [],
    'last_news_update': None,
    'genius_commentary': '',
    'genius_signal': 'NEUTRAL',
    'genius_strength': 'medium',
    'genius_timestamp': None,
    'genius_context': [],
    'analytics_snapshot': None,
    'analytics_timestamp': None,
    'killzone_snapshot': None,
    'session_clock': {
        'timerText': '--:--'
    }
}

# ============ TWELVE DATA API FUNCTIONS ============

def fetch_twelve_data_crypto(symbol='BTCUSDT'):
    """Fetch crypto price from Twelve Data"""
    try:
        params = {
            'symbol': symbol,
            'apikey': TWELVE_DATA_API_KEY
        }
        response = requests.get(
            f'{TWELVE_DATA_BASE_URL}/quote',
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Twelve Data response for {symbol}: {data}")
            if 'error' not in data and 'code' not in data:
                # Twelve Data returns: close, open, high, low, previous_close, change, percent_change, volume
                price = float(data.get('close', 0) or 0)
                prev_close = float(data.get('previous_close', 0) or 0)
                # percent_change may be string like "1.25" or number
                pct_change_raw = data.get('percent_change', 0)
                if pct_change_raw is None or pct_change_raw == '':
                    # Calculate from previous_close if percent_change missing
                    if prev_close > 0 and price > 0:
                        pct_change = ((price - prev_close) / prev_close) * 100
                    else:
                        pct_change = 0
                else:
                    pct_change = float(pct_change_raw)
                volume = float(data.get('volume', 0) or 0)
                logger.info(f"📊 {symbol}: ${price:,.2f} ({pct_change:+.2f}%)")
                return {
                    'price': price,
                    'change': pct_change,
                    'previous_close': prev_close,
                    'volume': volume
                }
            else:
                logger.warning(f"⚠️ Twelve Data API error for {symbol}: {data}")
    except Exception as e:
        logger.error(f"❌ Twelve Data crypto error ({symbol}): {e}")
    return None


def fetch_twelve_data_stock(symbol='AAPL'):
    """Fetch stock price from Twelve Data"""
    try:
        params = {
            'symbol': symbol,
            'apikey': TWELVE_DATA_API_KEY
        }
        response = requests.get(
            f'{TWELVE_DATA_BASE_URL}/quote',
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data and 'code' not in data:
                price = float(data.get('close', 0) or 0)
                prev_close = float(data.get('previous_close', 0) or 0)
                pct_change_raw = data.get('percent_change', 0)
                if pct_change_raw is None or pct_change_raw == '':
                    if prev_close > 0 and price > 0:
                        pct_change = ((price - prev_close) / prev_close) * 100
                    else:
                        pct_change = 0
                else:
                    pct_change = float(pct_change_raw)
                volume = float(data.get('volume', 0) or 0)
                return {
                    'price': price,
                    'change': pct_change,
                    'previous_close': prev_close,
                    'volume': volume
                }
            else:
                logger.warning(f"⚠️ Twelve Data API error for {symbol}: {data}")
    except Exception as e:
        logger.error(f"❌ Twelve Data stock error ({symbol}): {e}")
    return None


def fetch_twelve_data_forex(pair='EUR/USD'):
    """Fetch forex/metals price from Twelve Data"""
    try:
        params = {
            'symbol': pair,
            'apikey': TWELVE_DATA_API_KEY
        }
        response = requests.get(
            f'{TWELVE_DATA_BASE_URL}/quote',
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data and 'code' not in data:
                price = float(data.get('close', 0) or 0)
                prev_close = float(data.get('previous_close', 0) or 0)
                pct_change_raw = data.get('percent_change', 0)
                if pct_change_raw is None or pct_change_raw == '':
                    if prev_close > 0 and price > 0:
                        pct_change = ((price - prev_close) / prev_close) * 100
                    else:
                        pct_change = 0
                else:
                    pct_change = float(pct_change_raw)
                return {
                    'price': price,
                    'change': pct_change,
                    'previous_close': prev_close
                }
            else:
                logger.warning(f"⚠️ Twelve Data API error for {pair}: {data}")
    except Exception as e:
        logger.error(f"❌ Twelve Data forex error ({pair}): {e}")
    return None


# ============ CRYPTOPANIC NEWS (Free Crypto News) ============

def fetch_cryptopanic_news(limit=10):
    """Fetch crypto news from CryptoPanic (free API)"""
    try:
        params = {
            'auth_token': CRYPTOPANIC_AUTH_TOKEN,
            'public': 'true',
            'kind': 'news',
            'filter': 'hot',  # hot, rising, bullish, bearish, important
        }
        response = requests.get(
            CRYPTOPANIC_API_URL,
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            news_items = []
            for item in data.get('results', [])[:limit]:
                # Parse published date
                pub_date = item.get('published_at', '')
                try:
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    age_minutes = int((datetime.now(dt.tzinfo) - dt).total_seconds() / 60)
                except:
                    age_minutes = 0
                
                # Determine sentiment from votes
                votes = item.get('votes', {})
                positive = votes.get('positive', 0) + votes.get('liked', 0)
                negative = votes.get('negative', 0) + votes.get('disliked', 0)
                if positive > negative + 2:
                    sentiment = 'bullish'
                elif negative > positive + 2:
                    sentiment = 'bearish'
                else:
                    sentiment = 'neutral'
                
                news_items.append({
                    'id': item.get('id'),
                    'category': 'KRYPTO',
                    'headline': item.get('title', '')[:120],
                    'timeAgo': f"{age_minutes} min temu" if age_minutes < 60 else f"{age_minutes // 60}h temu",
                    'ageMinutes': age_minutes,
                    'sentiment': sentiment,
                    'timestamp': pub_date,
                    'url': item.get('url', ''),
                    'source': item.get('source', {}).get('title', 'CryptoPanic')
                })
            
            logger.info(f"✅ Fetched {len(news_items)} news from CryptoPanic")
            return news_items
    except Exception as e:
        logger.error(f"❌ CryptoPanic error: {e}")
    return []


def fetch_newsapi_headlines(category='business', limit=5):
    """Fetch general market news from NewsAPI"""
    if not NEWSAPI_KEY:
        return []
    try:
        params = {
            'apiKey': NEWSAPI_KEY,
            'category': category,
            'language': 'en',
            'pageSize': limit
        }
        response = requests.get(
            f'{NEWSAPI_BASE_URL}/top-headlines',
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            news_items = []
            for idx, item in enumerate(data.get('articles', [])[:limit], start=100):
                pub_date = item.get('publishedAt', '')
                try:
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    age_minutes = int((datetime.now(dt.tzinfo) - dt).total_seconds() / 60)
                except:
                    age_minutes = 0
                
                news_items.append({
                    'id': idx,
                    'category': 'MAKRO',
                    'headline': item.get('title', '')[:120],
                    'timeAgo': f"{age_minutes} min temu" if age_minutes < 60 else f"{age_minutes // 60}h temu",
                    'ageMinutes': age_minutes,
                    'sentiment': 'neutral',
                    'timestamp': pub_date,
                    'url': item.get('url', ''),
                    'source': item.get('source', {}).get('name', 'NewsAPI')
                })
            
            logger.info(f"✅ Fetched {len(news_items)} news from NewsAPI")
            return news_items
    except Exception as e:
        logger.error(f"❌ NewsAPI error: {e}")
    return []


def fetch_crypto_prices():
    """Fetch BTC, ETH and altcoins from Twelve Data (Pro plan)"""
    try:
        # BTC/USD from Twelve Data
        btc_data = fetch_twelve_data_crypto('BTC/USD')
        # ETH/USD from Twelve Data
        eth_data = fetch_twelve_data_crypto('ETH/USD')

        if btc_data and btc_data.get('price', 0) > 0:
            cache['btc_price'] = btc_data['price']
            cache['btc_change'] = btc_data['change']
            cache['btc_prev_close'] = btc_data.get('previous_close', 0)
            cache['volume_24h'] = btc_data.get('volume', 0) * btc_data['price']
        else:
            logger.warning("⚠️ Twelve Data BTC returned zero, keeping cached value")
            
        if eth_data and eth_data.get('price', 0) > 0:
            cache['eth_price'] = eth_data['price']
            cache['eth_change'] = eth_data['change']
            cache['eth_prev_close'] = eth_data.get('previous_close', 0)
        else:
            logger.warning("⚠️ Twelve Data ETH returned zero, keeping cached value")
        
        # Fetch additional altcoins
        altcoins = [
            ('SOL/USD', 'sol_price', 'sol_change'),
            ('XRP/USD', 'xrp_price', 'xrp_change'),
            ('BNB/USD', 'bnb_price', 'bnb_change'),
            ('ADA/USD', 'ada_price', 'ada_change'),
            ('DOGE/USD', 'doge_price', 'doge_change'),
            ('AVAX/USD', 'avax_price', 'avax_change'),
            ('DOT/USD', 'dot_price', 'dot_change'),
            ('LINK/USD', 'link_price', 'link_change'),
            ('UNI/USD', 'uni_price', 'uni_change'),
            ('ATOM/USD', 'atom_price', 'atom_change'),
            ('LTC/USD', 'ltc_price', 'ltc_change'),
        ]
        
        for symbol, price_key, change_key in altcoins:
            data = fetch_twelve_data_crypto(symbol)
            if data and data.get('price', 0) > 0:
                cache[price_key] = data['price']
                cache[change_key] = data['change']
            
        logger.info(f"✅ Crypto (Twelve Data): BTC ${cache['btc_price']:,.2f} ({cache['btc_change']:+.2f}%) | ETH ${cache['eth_price']:,.2f} ({cache['eth_change']:+.2f}%) | SOL ${cache['sol_price']:.2f}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Crypto prices fetch error: {e}")
        return False


def fetch_stock_prices():
    """Fetch stock prices from Twelve Data"""
    try:
        stocks = [
            ('SPY', 'spy_price', 'spy_change', 'spy_prev_close'),
            ('AAPL', 'aapl_price', 'aapl_change', 'aapl_prev_close'),
            ('MSFT', 'msft_price', 'msft_change', 'msft_prev_close'),
            ('NVDA', 'nvda_price', 'nvda_change', 'nvda_prev_close')
        ]
        
        for ticker, price_key, change_key, prev_key in stocks:
            data = fetch_twelve_data_stock(ticker)
            if data:
                cache[price_key] = data['price']
                cache[change_key] = data['change']
                cache[prev_key] = data.get('previous_close', 0)
        
        logger.info(f"✅ Twelve Data (Stocks): SPY ${cache['spy_price']:,.2f} | AAPL ${cache['aapl_price']:,.2f} | MSFT ${cache['msft_price']:,.2f} | NVDA ${cache['nvda_price']:,.2f}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Stock prices fetch error: {e}")
        return False


def fetch_forex_prices():
    """Fetch forex prices from Twelve Data"""
    try:
        pairs = [
            ('EUR/USD', 'eurusd_price', 'eurusd_change', 'eurusd_prev_close'),
            ('GBP/USD', 'gbpusd_price', 'gbpusd_change', 'gbpusd_prev_close')
        ]
        
        for pair, price_key, change_key, prev_key in pairs:
            data = fetch_twelve_data_forex(pair)
            if data:
                cache[price_key] = data['price']
                cache[change_key] = data['change']
                cache[prev_key] = data.get('previous_close', 0)
        
        logger.info(f"✅ Twelve Data (Forex): EUR/USD {cache['eurusd_price']:.4f} | GBP/USD {cache['gbpusd_price']:.4f}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Forex prices fetch error: {e}")
        return False


def fetch_market_data():
    """Fetch additional market data from Twelve Data"""
    try:
        # Gold - Twelve Data uses XAU/USD
        gold_data = fetch_twelve_data_forex('XAU/USD')
        if gold_data and gold_data.get('price', 0) > 0:
            cache['gold_price'] = gold_data['price']
            cache['gold_change'] = gold_data['change']
        
        # Silver - Twelve Data uses XAG/USD
        silver_data = fetch_twelve_data_forex('XAG/USD')
        if silver_data and silver_data.get('price', 0) > 0:
            cache['silver_price'] = silver_data['price']
            cache['silver_change'] = silver_data['change']
        
        # Additional stocks for indices
        extra_stocks = [
            ('TSLA', 'tsla_price', 'tsla_change'),
            ('AMZN', 'amzn_price', 'amzn_change'),
            ('GOOGL', 'googl_price', 'googl_change'),
            ('META', 'meta_price', 'meta_change'),
        ]
        for ticker, price_key, change_key in extra_stocks:
            data = fetch_twelve_data_stock(ticker)
            if data and data.get('price', 0) > 0:
                cache[price_key] = data['price']
                cache[change_key] = data['change']
        
        # Indices - NASDAQ, DAX, DOW
        indices = [
            ('IXIC', 'nasdaq_price', 'nasdaq_change'),  # NASDAQ
            ('DJI', 'dow_price', 'dow_change'),         # DOW Jones
        ]
        for symbol, price_key, change_key in indices:
            data = fetch_twelve_data_stock(symbol)
            if data and data.get('price', 0) > 0:
                cache[price_key] = data['price']
                cache[change_key] = data['change']
        
        logger.info(f"✅ Markets: GOLD ${cache['gold_price']:,.2f} | SILVER ${cache['silver_price']:.2f} | NASDAQ {cache['nasdaq_price']:,.0f}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Market data fetch error: {e}")
        return False


def fetch_fear_greed():
    """Fetch Fear & Greed Index from Alternative.me (free source)"""
    try:
        response = requests.get(
            'https://api.alternative.me/fng/?limit=1',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data['data'] and len(data['data']) > 0:
                cache['fear_greed'] = int(data['data'][0]['value'])
                logger.info(f"✅ Fear & Greed: {cache['fear_greed']}")
                return True
    except Exception as e:
        logger.error(f"❌ Fear & Greed error: {e}")
    return False


def _format_timer(seconds_remaining: float) -> str:
    seconds = max(0, int(seconds_remaining))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def update_session_clock():
    now = datetime.utcnow()
    next_quarter = ((now.minute // 15) + 1) * 15
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    if next_quarter < 60:
        target = now.replace(minute=next_quarter, second=0, microsecond=0)
    else:
        target = next_hour
    remaining = (target - now).total_seconds()
    cache['session_clock'] = {'timerText': _format_timer(remaining)}
    return cache['session_clock']


def update_news_cache():
    """Update news cache with AI-powered news fetching"""
    now = datetime.utcnow()
    headlines = []
    
    # 1. Fetch crypto news from CryptoPanic (free)
    crypto_news = fetch_cryptopanic_news(limit=7)
    headlines.extend(crypto_news)
    
    # 2. Fetch general market news from NewsAPI
    market_news = fetch_newsapi_headlines(category='business', limit=3)
    headlines.extend(market_news)
    
    # 3. Fallback to template news if no external news
    if not headlines:
        btc_price = cache.get('btc_price', 0)
        btc_change = cache.get('btc_change', 0)
        fear = cache.get('fear_greed', 0)
        templates = [
            ('MAKRO', 'Fed monitoruje inflację usług; rynek liczy na cięcia w Q2', 4, 'neutral'),
            ('KRYPTO', f'BTC utrzymuje {btc_price:,.0f} USD, zmiana {btc_change:+.2f}%', 7, 'bullish' if btc_change >= 0 else 'bearish'),
            ('AKCJE', 'Tech mega-caps ciągną NASDAQ w górę, popyt na AI rośnie', 11, 'bullish'),
            ('FX', 'EUR/USD stabilny przed publikacją PMI; DXY w konsolidacji', 15, 'neutral'),
            ('SENTYMENT', f'Fear & Greed na poziomie {fear} – apetyt na ryzyko umiarkowany', 20, 'neutral'),
        ]
        for idx, (category, headline, age_min, sentiment) in enumerate(templates, start=1):
            headlines.append({
                'id': idx,
                'category': category,
                'headline': headline,
                'timeAgo': f"{age_min} min temu",
                'ageMinutes': age_min,
                'sentiment': sentiment,
                'timestamp': (now - timedelta(minutes=age_min)).isoformat(),
                'source': 'Fallback News',
                'url': f'https://example.com/news/{idx-1}'
            })
    
    # Sort by age (newest first)
    headlines.sort(key=lambda x: x.get('ageMinutes', 999))
    cache['news_headlines'] = headlines
    cache['last_news_update'] = now.isoformat()
    logger.info(f"📰 News cache updated: {len(headlines)} items (CryptoPanic + NewsAPI)")
    return headlines


def build_genius_payload():
    """Build Genius Hamster commentary with AI enhancement"""
    btc_price = cache.get('btc_price', 0)
    btc_change = cache.get('btc_change', 0)
    fear = cache.get('fear_greed', 0)
    volume = cache.get('volume_24h', 0)
    
    # Try to use AI for enhanced commentary
    if AI_MODULES_AVAILABLE and llm_genius:
        try:
            # Prepare market data for AI
            market_data = {
                'price': btc_price,
                'rsi': cache.get('rsi', 50),
                'macd': cache.get('macd', 0),
                'volume_ratio': volume / 24e9 if volume > 0 else 1.0,
                'trend': 'uptrend' if btc_change > 0 else 'downtrend',
                'fear_greed': fear
            }
            
            # Get sentiment data if available
            sentiment_data = None
            if sentiment_analyzer and cache.get('news_headlines'):
                try:
                    # Analyze recent news
                    news_texts = [item.get('headline', '') for item in cache['news_headlines'][:3]]
                    sentiment_results = []
                    for text in news_texts:
                        sentiment = sentiment_analyzer.analyze_text_sentiment(text, 'BTC')
                        sentiment_results.append(sentiment)
                    
                    sentiment_data = sentiment_analyzer.calculate_market_sentiment(sentiment_results, 'BTC')
                except Exception as e:
                    logger.error(f"Sentiment analysis error: {e}")
            
            # Get AI-powered analysis
            ai_result = llm_genius.analyze_market_data(market_data, sentiment_data)
            
            commentary = ai_result.get('commentary', '')
            signal = ai_result.get('signal', 'NEUTRAL')
            confidence = ai_result.get('confidence', 50)
            strength = 'strong' if confidence > 70 else 'medium' if confidence > 40 else 'weak'
            
            context_notes = [
                ai_result.get('reasoning', 'Multiple factors considered'),
                'AI-powered market analysis',
                f"Confidence: {confidence}%"
            ]
            
            logger.info(f"🧠 AI Genius: {signal} ({confidence}%) - {commentary[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ AI Genius analysis failed: {e}")
            # Fallback to rule-based
            ai_result = None
    else:
        ai_result = None
    
    # Fallback to rule-based commentary if AI not available
    if not ai_result or not ai_result.get('commentary'):
        bias = 'BULL' if btc_change >= 0 else 'BEAR'
        strength = 'strong' if abs(btc_change) > 1.5 else 'medium'
        sentiment_note = 'Greed rośnie' if fear > 70 else 'Neutralnie' if fear >= 30 else 'Fear dominuje'
        commentary = (
            f"{'🟢' if bias == 'BULL' else '🔴'} BTC {btc_price:,.0f} USD, zmiana {btc_change:+.2f}% 24h. "
            f"Wolumen {volume/1e9:.2f}B. {sentiment_note}."
        )
        signal = bias
        context_notes = [
            'Monitoruj reakcję na strefę 4h FVG',
            'London fix może dodać zmienności',
            'Utrzymaj trailing stop pod lokalnym swingiem'
        ]
    
    payload = {
        'ok': True,
        'commentary': commentary,
        'signal': signal,
        'strength': strength,
        'btc_price': btc_price,
        'change_24h': btc_change,
        'fear_greed': fear,
        'timestamp': time.time(),
        'ai_powered': AI_MODULES_AVAILABLE and ai_result is not None,
        'liveBias': {
            'primaryBias': 'bullish' if 'BULL' in signal or 'BUY' in signal else 'bearish' if 'BEAR' in signal or 'SELL' in signal else 'neutral',
            'playbook': 'NY Open Sweep',
            'mtfFocus': ['1H Trend', '15M Liquidity'],
            'sentimentShift': f"Fear & Greed: {fear}",
            'volumeNote': f"{volume/1e9:.2f}B vs 24h avg",
            'sessionCallout': 'Patrz na NY lunch fade',
            'recentContext': context_notes
        },
        'quant': {
            'ok': True,
            'insights': {
                'performance': {
                    'daily_volatility': abs(btc_change) / 100,
                    'sharpe_like': 1.8,
                    'sortino_like': 2.1
                },
                'risk': {
                    'value_at_risk': 0.023
                },
                'ffn': {
                    'cagr': 0.27
                },
                'options': {
                    'btc_call': {
                        'price': max(0.0, btc_price * 0.015)
                    }
                }
            },
            'warnings': ['Wysoka zmienność w oknie US'],
            'generated_at': time.time()
        }
    }
    cache['genius_commentary'] = payload['commentary']
    cache['genius_signal'] = payload['signal']
    cache['genius_strength'] = payload['strength']
    cache['genius_timestamp'] = payload['timestamp']
    cache['genius_context'] = context_notes
    return payload


def build_analytics_snapshot():
    btc_price = cache.get('btc_price', 0)
    btc_change = cache.get('btc_change', 0)
    fear = cache.get('fear_greed', 0)
    volatility = abs(btc_change) * random.uniform(0.8, 1.6)
    liquidation_long = random.uniform(35, 55)
    liquidation_short = random.uniform(15, 35)
    snapshot = {
        'ok': True,
        'timestamp': time.time(),
        'radar': {
            'fvg': {
                '1h': {'low': btc_price * 0.996, 'high': btc_price * 1.002, 'type': 'BUY'},
                '4h': {'low': btc_price * 1.008, 'high': btc_price * 1.018, 'type': 'SELL'},
                '1d': {'low': btc_price * 0.971, 'high': btc_price * 0.980, 'type': 'DEMAND'}
            },
            'eql_eqh': {
                'eql': btc_price * 0.985,
                'eqh': btc_price * 1.02,
                'range': btc_price * 0.035
            },
            'liquidations': {
                'long_count': liquidation_long,
                'short_count': liquidation_short,
                'total_24h': liquidation_long + liquidation_short
            },
            'signal_strength': {
                'bullish': 55 + random.randint(-10, 10),
                'bearish': 45 + random.randint(-10, 10)
            },
            'premium_index': {
                'spot_perps': 0.12 + random.uniform(-0.05, 0.05),
                'funding': 0.008 + random.uniform(-0.003, 0.003)
            }
        },
        'heatmaps': {
            'correlations': {
                'btc_eth': 0.75 + random.uniform(-0.1, 0.1),
                'btc_aapl': 0.35 + random.uniform(-0.1, 0.1),
                'btc_dxy': -0.42 + random.uniform(-0.1, 0.1),
                'btc_vix': -0.28 + random.uniform(-0.1, 0.1),
                'btc_nasdaq': 0.58 + random.uniform(-0.1, 0.1)
            },
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
            'whale_accumulation': 2300 + random.randint(-400, 400),
            'exchange_inflows': -120 + random.randint(-25, 25),
            'dark_pool_flow': 680 + random.randint(-80, 80),
            'order_flow_imbalance': 58 + random.randint(-6, 6),
            'long_short_ratio': 1.18 + random.uniform(-0.1, 0.1),
            'open_interest': 14200 + random.randint(-500, 500),
            'skew_index': -0.12 + random.uniform(-0.05, 0.05),
            'cascade_risk': 'MEDIUM'
        },
        'btc_price': btc_price,
        'fear_greed': fear,
        'volatility_24h': volatility
    }
    cache['analytics_snapshot'] = snapshot
    cache['analytics_timestamp'] = snapshot['timestamp']
    return snapshot


def update_killzone_snapshot():
    now = datetime.utcnow()
    zones = [
        {
            'name': 'asia',
            'label': 'Asia Range',
            'start_hour': 0,
            'end_hour': 6,
            'priority': 'low'
        },
        {
            'name': 'london',
            'label': 'London Open',
            'start_hour': 7,
            'end_hour': 10,
            'priority': 'high'
        },
        {
            'name': 'newyork_am',
            'label': 'NY Open',
            'start_hour': 13,
            'end_hour': 16,
            'priority': 'high'
        },
        {
            'name': 'newyork_pm',
            'label': 'NY PM Sweep',
            'start_hour': 19,
            'end_hour': 21,
            'priority': 'medium'
        }
    ]

    overlays = []
    current_zone = None
    upcoming_zone = None
    minutes_now = now.hour * 60 + now.minute

    for zone in zones:
        start_minute = zone['start_hour'] * 60
        end_minute = zone['end_hour'] * 60
        overlays.append({
            'name': zone['name'],
            'label': zone['label'],
            'startTime': f"{zone['start_hour']:02d}:00",
            'endTime': f"{zone['end_hour']:02d}:00",
            'startMinute': start_minute,
            'endMinute': end_minute,
            'priority': zone['priority']
        })
        if start_minute <= minutes_now < end_minute:
            current_zone = overlays[-1]
        elif minutes_now < start_minute and upcoming_zone is None:
            upcoming_zone = overlays[-1]

    snapshot = {
        'ok': True,
        'current': current_zone,
        'upcoming': upcoming_zone,
        'overlays': overlays,
        'sessionClock': update_session_clock()
    }
    cache['killzone_snapshot'] = snapshot
    return snapshot


# ============ WEBSOCKET HANDLERS ============

# Track connected WebSocket clients
ws_clients = set()
ws_thread = None

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket client connection"""
    logger.info(f"✅ Client connected: {request.sid}")
    emit('status', {'data': 'Connected to Hamster Terminal API'})
    start_websocket_stream()

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket client disconnection"""
    logger.info(f"❌ Client disconnected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle subscription to real-time prices"""
    symbols = data.get('symbols', ['BTC/USD', 'AAPL', 'EUR/USD'])
    logger.info(f"📡 Client {request.sid} subscribed to: {symbols}")
    emit('subscription', {'symbols': symbols, 'status': 'subscribed'})

def broadcast_price_update(symbol, price, change):
    """Broadcast price update to all connected clients"""
    socketio.emit('price_update', {
        'symbol': symbol,
        'price': price,
        'change': change,
        'timestamp': datetime.now().isoformat()
    })

async def websocket_stream():
    """Connect to Twelve Data WebSocket for real-time prices"""
    try:
        symbols = "BTC/USD,AAPL,MSFT,NVDA,SPY,EUR/USD,GBP/USD"
        ws_url = f"{TWELVE_DATA_WS_URL}?apikey={TWELVE_DATA_API_KEY}"
        
        # Use ping_interval=None to avoid connection drops with Twelve Data
        async with websockets.connect(ws_url, ping_interval=None) as websocket:
            logger.info("✅ Connected to Twelve Data WebSocket")
            
            # Subscribe to symbols
            subscribe_msg = {
                "action": "subscribe",
                "params": {"symbols": symbols}
            }
            await websocket.send(json.dumps(subscribe_msg))
            logger.info(f"📡 Subscribed to: {symbols}")
            
            # Listen for price updates
            while True:
                try:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    
                    if 'price' in data:
                        symbol = data.get('symbol', 'UNKNOWN')
                        price = float(data.get('price', 0))
                        
                        # Twelve Data WebSocket doesn't send percent_change
                        # Get change from cached REST API data, or calculate from previous close
                        change = 0
                        cache_key = None
                        prev_key = None
                        
                        # Update cache and get change
                        if symbol == 'BTC/USD':
                            cache_key, prev_key = 'btc_price', 'btc_prev_close'
                            change = cache.get('btc_change', 0)
                        elif symbol == 'ETH/USD':
                            cache_key, prev_key = 'eth_price', 'eth_prev_close'
                            change = cache.get('eth_change', 0)
                        elif symbol == 'AAPL':
                            cache_key, prev_key = 'aapl_price', 'aapl_prev_close'
                            change = cache.get('aapl_change', 0)
                        elif symbol == 'MSFT':
                            cache_key, prev_key = 'msft_price', 'msft_prev_close'
                            change = cache.get('msft_change', 0)
                        elif symbol == 'NVDA':
                            cache_key, prev_key = 'nvda_price', 'nvda_prev_close'
                            change = cache.get('nvda_change', 0)
                        elif symbol == 'SPY':
                            cache_key, prev_key = 'spy_price', 'spy_prev_close'
                            change = cache.get('spy_change', 0)
                        elif symbol == 'EUR/USD':
                            cache_key, prev_key = 'eurusd_price', 'eurusd_prev_close'
                            change = cache.get('eurusd_change', 0)
                        elif symbol == 'GBP/USD':
                            cache_key, prev_key = 'gbpusd_price', 'gbpusd_prev_close'
                            change = cache.get('gbpusd_change', 0)
                        
                        # Update price cache
                        if cache_key:
                            cache[cache_key] = price
                            
                            # If we have previous close, recalculate change from current price
                            prev_close = cache.get(prev_key)
                            if prev_close and prev_close > 0:
                                change = ((price - prev_close) / prev_close) * 100
                        
                        # Broadcast to all connected clients
                        broadcast_price_update(symbol, price, change)
                        
                        logger.info(f"📊 {symbol}: ${price:,.2f} ({change:+.2f}%)")
                    
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    logger.error(f"❌ WebSocket message error: {e}")
                    
    except Exception as e:
        logger.error(f"❌ WebSocket connection error: {e}")
        logger.info("⏳ Retrying WebSocket connection in 10 seconds...")
        await asyncio.sleep(10)

def start_websocket_stream():
    """Start WebSocket stream in background thread"""
    global ws_thread
    if ws_thread is None or not ws_thread.is_alive():
        ws_thread = threading.Thread(target=lambda: asyncio.run(websocket_stream()), daemon=True)
        ws_thread.start()
        logger.info("🔄 WebSocket stream started")


def update_data_loop():
    """Background thread to update data every 30 seconds"""
    logger.info("🔄 Starting background data update thread...")
    while True:
        try:
            # Fetch all data from Twelve Data
            fetch_crypto_prices()
            fetch_stock_prices()
            fetch_forex_prices()
            fetch_market_data()
            fetch_fear_greed()

            # Refresh fallback caches
            update_news_cache()
            build_genius_payload()
            build_analytics_snapshot()
            update_killzone_snapshot()
            
            # Update timestamp
            cache['last_update'] = datetime.now().isoformat()
            cache['timestamp'] = time.time()
            
            time.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            logger.error(f"❌ Update loop error: {e}")
            time.sleep(30)


# Start background thread
update_thread = threading.Thread(target=update_data_loop, daemon=True)
update_thread.start()

# Initial data fetch - DISABLED to prevent Gunicorn timeout
logger.info("📡 Initial fetch handled by background thread...")
# fetch_crypto_prices()
# fetch_stock_prices()
# fetch_forex_prices()
# fetch_market_data()
# fetch_fear_greed()
# update_news_cache()
# build_genius_payload()
# build_analytics_snapshot()
# update_killzone_snapshot()

# ============ API ENDPOINTS ============

def get_crypto_summary():
    """Internal: Get crypto/stocks/indices from Twelve Data"""
    return {
        'ok': True,
        'btcPrice': round(cache['btc_price'], 2),
        'btcChange24h': round(cache['btc_change'], 2),
        'btcVolume24h': int(cache['volume_24h']),
        'ethPrice': round(cache['eth_price'], 2),
        'ethChange24h': round(cache['eth_change'], 2),
        # Additional cryptos
        'cryptos': {
            'SOL': round(cache['sol_price'], 2),
            'XRP': round(cache['xrp_price'], 4),
            'BNB': round(cache['bnb_price'], 2),
            'ADA': round(cache['ada_price'], 4),
            'DOGE': round(cache['doge_price'], 5),
            'AVAX': round(cache['avax_price'], 2),
            'DOT': round(cache['dot_price'], 2),
            'LINK': round(cache['link_price'], 2),
            'UNI': round(cache['uni_price'], 2),
            'ATOM': round(cache['atom_price'], 2),
            'LTC': round(cache['ltc_price'], 2)
        },
        'cryptosChange': {
            'SOL': round(cache['sol_change'], 2),
            'XRP': round(cache['xrp_change'], 2),
            'BNB': round(cache['bnb_change'], 2),
            'ADA': round(cache['ada_change'], 2),
            'DOGE': round(cache['doge_change'], 2),
            'AVAX': round(cache['avax_change'], 2),
            'DOT': round(cache['dot_change'], 2),
            'LINK': round(cache['link_change'], 2),
            'UNI': round(cache['uni_change'], 2),
            'ATOM': round(cache['atom_change'], 2),
            'LTC': round(cache['ltc_change'], 2)
        },
        'lastUpdate': cache['last_update'],
        'source': 'Twelve Data Pro',
        'commodities': {
            'GOLD': round(cache['gold_price'], 2),
            'SILVER': round(cache['silver_price'], 2)
        },
        'commoditiesChange': {
            'GOLD': round(cache['gold_change'], 2),
            'SILVER': round(cache['silver_change'], 2)
        },
        'stocks': {
            'SPY': round(cache['spy_price'], 2),
            'AAPL': round(cache['aapl_price'], 2),
            'MSFT': round(cache['msft_price'], 2),
            'NVDA': round(cache['nvda_price'], 2),
            'TSLA': round(cache['tsla_price'], 2),
            'AMZN': round(cache['amzn_price'], 2),
            'GOOGL': round(cache['googl_price'], 2),
            'META': round(cache['meta_price'], 2)
        },
        'stocksChange': {
            'SPY': round(cache['spy_change'], 2),
            'AAPL': round(cache['aapl_change'], 2),
            'MSFT': round(cache['msft_change'], 2),
            'NVDA': round(cache['nvda_change'], 2),
            'TSLA': round(cache['tsla_change'], 2),
            'AMZN': round(cache['amzn_change'], 2),
            'GOOGL': round(cache['googl_change'], 2),
            'META': round(cache['meta_change'], 2)
        },
        'indices': {
            'NASDAQ': round(cache['nasdaq_price'], 0),
            'SP500': round(cache['spy_price'], 2),
            'DAX': round(cache['dax_price'], 0),
            'DOW': round(cache['dow_price'], 0)
        },
        'indicesChange': {
            'NASDAQ': round(cache['nasdaq_change'], 2),
            'SP500': round(cache['spy_change'], 2),
            'DAX': round(cache['dax_change'], 2),
            'DOW': round(cache['dow_change'], 2)
        },
        'fearGreed': cache['fear_greed']
    }

@app.route('/api/crypto/summary', methods=['GET'])
def crypto_summary():
    """Get BTC/ETH prices (via Twelve Data Pro)"""
    return jsonify(get_crypto_summary())

# Backward compatibility - keep /api/binance/summary working
@app.route('/api/binance/summary', methods=['GET'])
def binance_summary():
    """Legacy endpoint - redirects to Twelve Data"""
    return jsonify(get_crypto_summary())


@app.route('/api/stocks', methods=['GET'])
def stocks():
    """Get stock prices"""
    return jsonify({
        'ok': True,
        'spy': {
            'price': round(cache['spy_price'], 2),
            'change': round(cache['spy_change'], 2)
        },
        'aapl': {
            'price': round(cache['aapl_price'], 2),
            'change': round(cache['aapl_change'], 2)
        },
        'msft': {
            'price': round(cache['msft_price'], 2),
            'change': round(cache['msft_change'], 2)
        },
        'nvda': {
            'price': round(cache['nvda_price'], 2),
            'change': round(cache['nvda_change'], 2)
        }
    })


@app.route('/api/forex', methods=['GET'])
def forex():
    """Get forex prices"""
    return jsonify({
        'ok': True,
        'eurusd': {
            'price': round(cache['eurusd_price'], 4),
            'change': round(cache['eurusd_change'], 2)
        },
        'gbpusd': {
            'price': round(cache['gbpusd_price'], 4),
            'change': round(cache['gbpusd_change'], 2)
        }
    })


@app.route('/api/binance/funding', methods=['GET'])
def binance_funding():
    """Get BTC futures funding rate (fallback data)"""
    return jsonify({
        'ok': True,
        'lastFundingRate': cache['funding_rate'] / 100,
        'fundingRatePercent': round(cache['funding_rate'], 4),
        'note': 'For real funding rates, use Binance API directly'
    })


@app.route('/api/binance/oi', methods=['GET'])
def binance_oi():
    """Get BTC futures open interest (fallback data)"""
    return jsonify({
        'ok': True,
        'openInterest': cache['open_interest'] / cache['btc_price'],
        'openInterestValue': round(cache['open_interest'], 0),
        'note': 'For real OI, use Binance API directly'
    })


@app.route('/api/fng', methods=['GET'])
def fear_greed_index():
    """Get Fear & Greed Index"""
    return jsonify({
        'ok': True,
        'data': {
            'data': [
                {
                    'value': str(cache['fear_greed']),
                    'value_classification': 'Greed' if cache['fear_greed'] > 50 else 'Fear',
                    'timestamp': int(cache['timestamp'])
                }
            ]
        }
    })


@app.route('/api/chart-data', methods=['GET'])
def chart_data():
    """Get chart data for SVG charts - uses Twelve Data time series"""
    try:
        symbol = request.args.get('symbol', 'BTC/USD')
        interval = request.args.get('interval', '1h')
        outputsize = int(request.args.get('outputsize', 24))
        
        # Fetch time series from Twelve Data
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize,
            'apikey': TWELVE_DATA_API_KEY
        }
        response = requests.get(f'{TWELVE_DATA_BASE_URL}/time_series', params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if 'values' in data:
                values = data['values']
                # Calculate price range for chart scaling
                prices = [float(v['close']) for v in values if v.get('close')]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    current_price = prices[0]  # Most recent
                    
                    # Calculate support/resistance levels
                    price_range = max_price - min_price
                    support = min_price - (price_range * 0.02)
                    resistance = max_price + (price_range * 0.02)
                    
                    # Format for chart
                    chart_points = []
                    for i, v in enumerate(reversed(values)):  # Oldest to newest
                        chart_points.append({
                            'x': i,
                            'close': float(v.get('close', 0)),
                            'high': float(v.get('high', 0)),
                            'low': float(v.get('low', 0)),
                            'open': float(v.get('open', 0)),
                            'datetime': v.get('datetime', '')
                        })
                    
                    return jsonify({
                        'ok': True,
                        'symbol': symbol,
                        'interval': interval,
                        'current_price': current_price,
                        'min_price': min_price,
                        'max_price': max_price,
                        'support': round(support, 2),
                        'resistance': round(resistance, 2),
                        'points': chart_points,
                        'count': len(chart_points)
                    })
            
            return jsonify({'ok': False, 'error': 'No chart data available'}), 404
        
        return jsonify({'ok': False, 'error': f'Twelve Data error: {response.status_code}'}), 500
        
    except Exception as e:
        logger.error(f"Chart data error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/coingecko/simple', methods=['GET'])
def coingecko_simple():
    """Get crypto prices from Twelve Data cache"""
    return jsonify({
        'ok': True,
        'data': {
            'bitcoin': {
                'usd': round(cache['btc_price'], 2),
                'usd_24h_change': round(cache['btc_change'], 2)
            },
            'ethereum': {
                'usd': round(cache['eth_price'], 2),
                'usd_24h_change': round(cache['eth_change'], 2)
            }
        }
    })


@app.route('/api/commodities', methods=['GET'])
def commodities():
    """Get commodities data (Gold, Silver, Oil)"""
    return jsonify({
        'ok': True,
        'gold': {
            'price': round(cache.get('gold_price', 2650.0), 2),
            'change': round(cache.get('gold_change', 0.5), 2)
        },
        'silver': {
            'price': round(cache.get('silver_price', 31.5), 2),
            'change': round(cache.get('silver_change', 0.3), 2)
        },
        'oil': {
            'price': round(cache.get('oil_price', 75.0), 2),
            'change': round(cache.get('oil_change', -0.2), 2)
        }
    })


@app.route('/api/binance/price', methods=['GET'])
def binance_price():
    """Get single crypto price"""
    symbol = request.args.get('symbol', 'BTCUSDT').upper()
    
    # Map symbols to cache keys
    if 'BTC' in symbol:
        price = cache.get('btc_price', 0)
        change = cache.get('btc_change', 0)
    elif 'ETH' in symbol:
        price = cache.get('eth_price', 0)
        change = cache.get('eth_change', 0)
    elif 'SOL' in symbol:
        price = cache.get('sol_price', 0)
        change = cache.get('sol_change', 0)
    elif 'BNB' in symbol:
        price = cache.get('bnb_price', 0)
        change = cache.get('bnb_change', 0)
    elif 'XRP' in symbol:
        price = cache.get('xrp_price', 0)
        change = cache.get('xrp_change', 0)
    else:
        price = 0
        change = 0
    
    return jsonify({
        'ok': True,
        'symbol': symbol,
        'price': round(price, 2),
        'change': round(change, 2)
    })


@app.route('/api/markets', methods=['GET'])
def markets():
    """Get additional market data (GOLD, SPY, DXY)"""
    return jsonify({
        'ok': True,
        'gold': {
            'price': round(cache['gold_price'], 2),
            'change': round(cache['gold_change'], 2)
        },
        'spy': {
            'price': round(cache['spy_price'], 2),
            'change': round(cache['spy_change'], 2)
        },
        'dxy': {
            'price': round(cache['dxy_price'], 2),
            'change': round(cache['dxy_change'], 2)
        }
    })


# ============ NEW TWELVE DATA ENDPOINTS ============

@app.route('/api/market-movers', methods=['GET'])
def market_movers():
    """Get top gainers/losers for crypto and stocks from Twelve Data"""
    market = request.args.get('market', 'crypto')  # 'crypto', 'stocks', 'etf', 'forex'
    direction = request.args.get('direction', 'gainers')  # 'gainers' or 'losers'
    
    try:
        params = {
            'direction': direction,
            'outputsize': 10,
            'apikey': TWELVE_DATA_API_KEY
        }
        
        response = requests.get(
            f'{TWELVE_DATA_BASE_URL}/market_movers/{market}',
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            movers = data.get('values', [])
            
            return jsonify({
                'ok': True,
                'market': market,
                'direction': direction,
                'count': len(movers),
                'movers': movers,
                'source': 'Twelve Data Pro'
            })
        else:
            return jsonify({'ok': False, 'error': 'Failed to fetch market movers'}), 500
            
    except Exception as e:
        logger.error(f"Market movers error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/market-state', methods=['GET'])
def market_state():
    """Get market open/close status for exchanges from Twelve Data"""
    try:
        params = {
            'apikey': TWELVE_DATA_API_KEY
        }
        
        response = requests.get(
            f'{TWELVE_DATA_BASE_URL}/market_state',
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Filter for major US exchanges
            us_exchanges = ['NYSE', 'NASDAQ']
            states = {}
            
            for market in data if isinstance(data, list) else []:
                if market.get('name') in us_exchanges:
                    states[market.get('name')] = {
                        'is_open': market.get('is_market_open', False),
                        'time_after_open': market.get('time_after_open', ''),
                        'time_to_open': market.get('time_to_open', ''),
                        'time_to_close': market.get('time_to_close', '')
                    }
            
            return jsonify({
                'ok': True,
                'markets': states,
                'crypto_always_open': True,
                'source': 'Twelve Data'
            })
        else:
            return jsonify({'ok': False, 'error': 'Failed to fetch market state'}), 500
            
    except Exception as e:
        logger.error(f"Market state error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/insider-transactions', methods=['GET'])
def insider_transactions():
    """Get insider transactions for a stock from Twelve Data"""
    symbol = request.args.get('symbol', 'AAPL')
    
    try:
        params = {
            'symbol': symbol,
            'apikey': TWELVE_DATA_API_KEY
        }
        
        response = requests.get(
            f'{TWELVE_DATA_BASE_URL}/insider_transactions',
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            transactions = data.get('insider_transactions', [])[:20]  # Limit to 20 most recent
            
            return jsonify({
                'ok': True,
                'symbol': symbol,
                'count': len(transactions),
                'transactions': transactions,
                'meta': data.get('meta', {}),
                'source': 'Twelve Data Pro'
            })
        else:
            return jsonify({'ok': False, 'error': 'Failed to fetch insider transactions'}), 500
            
    except Exception as e:
        logger.error(f"Insider transactions error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/technical-indicators', methods=['GET'])
def technical_indicators():
    """Get technical indicators (RSI, MACD, Bollinger Bands) from Twelve Data"""
    symbol = request.args.get('symbol', 'BTC/USD')
    interval = request.args.get('interval', '1day')
    
    try:
        indicators = {}
        
        # RSI
        rsi_params = {
            'symbol': symbol,
            'interval': interval,
            'time_period': 14,
            'outputsize': 1,
            'apikey': TWELVE_DATA_API_KEY
        }
        rsi_resp = requests.get(f'{TWELVE_DATA_BASE_URL}/rsi', params=rsi_params, timeout=10)
        if rsi_resp.status_code == 200:
            rsi_data = rsi_resp.json()
            if rsi_data.get('values'):
                indicators['rsi'] = float(rsi_data['values'][0].get('rsi', 0))
        
        # MACD
        macd_params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': 1,
            'apikey': TWELVE_DATA_API_KEY
        }
        macd_resp = requests.get(f'{TWELVE_DATA_BASE_URL}/macd', params=macd_params, timeout=10)
        if macd_resp.status_code == 200:
            macd_data = macd_resp.json()
            if macd_data.get('values'):
                indicators['macd'] = {
                    'macd': float(macd_data['values'][0].get('macd', 0)),
                    'signal': float(macd_data['values'][0].get('macd_signal', 0)),
                    'histogram': float(macd_data['values'][0].get('macd_hist', 0))
                }
        
        # Bollinger Bands
        bb_params = {
            'symbol': symbol,
            'interval': interval,
            'time_period': 20,
            'outputsize': 1,
            'apikey': TWELVE_DATA_API_KEY
        }
        bb_resp = requests.get(f'{TWELVE_DATA_BASE_URL}/bbands', params=bb_params, timeout=10)
        if bb_resp.status_code == 200:
            bb_data = bb_resp.json()
            if bb_data.get('values'):
                indicators['bollinger'] = {
                    'upper': float(bb_data['values'][0].get('upper_band', 0)),
                    'middle': float(bb_data['values'][0].get('middle_band', 0)),
                    'lower': float(bb_data['values'][0].get('lower_band', 0))
                }
        
        # EMA (Exponential Moving Average)
        ema_params = {
            'symbol': symbol,
            'interval': interval,
            'time_period': 21,
            'outputsize': 1,
            'apikey': TWELVE_DATA_API_KEY
        }
        ema_resp = requests.get(f'{TWELVE_DATA_BASE_URL}/ema', params=ema_params, timeout=10)
        if ema_resp.status_code == 200:
            ema_data = ema_resp.json()
            if ema_data.get('values'):
                indicators['ema21'] = float(ema_data['values'][0].get('ema', 0))
        
        return jsonify({
            'ok': True,
            'symbol': symbol,
            'interval': interval,
            'indicators': indicators,
            'source': 'Twelve Data Pro'
        })
        
    except Exception as e:
        logger.error(f"Technical indicators error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/quote', methods=['GET'])
def get_quote():
    """Get detailed quote for any symbol from Twelve Data"""
    symbol = request.args.get('symbol', 'AAPL')
    
    try:
        params = {
            'symbol': symbol,
            'apikey': TWELVE_DATA_API_KEY
        }
        
        response = requests.get(
            f'{TWELVE_DATA_BASE_URL}/quote',
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            return jsonify({
                'ok': True,
                'symbol': data.get('symbol', symbol),
                'name': data.get('name', ''),
                'exchange': data.get('exchange', ''),
                'price': float(data.get('close', 0)),
                'open': float(data.get('open', 0)),
                'high': float(data.get('high', 0)),
                'low': float(data.get('low', 0)),
                'volume': int(data.get('volume', 0) or 0),
                'change': float(data.get('change', 0)),
                'percent_change': float(data.get('percent_change', 0)),
                'previous_close': float(data.get('previous_close', 0)),
                'source': 'Twelve Data Pro'
            })
        else:
            return jsonify({'ok': False, 'error': 'Failed to fetch quote'}), 500
            
    except Exception as e:
        logger.error(f"Quote error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============ GENIUS TRADING ENGINE API v3.0 RIGOROUS ============

@app.route('/api/genius/signal', methods=['GET'])
def genius_live_signal():
    """
    Get RIGOROUS trading signal from Genius AI Engine v3.0
    Features:
    - STRICT liquidity grab detection (wick ratio, volume confirmation)
    - FVG zones with gap fill analysis
    - Multi-timeframe confluence (minimum 2 TF alignment required)
    - Insider/whale flow data
    - On-chain blockchain metrics
    - News sentiment integration
    - Minimum 70% confluence required for signal
    """
    symbol = request.args.get('symbol', 'BTC/USD')
    
    try:
        # Try v3 RIGOROUS engine first
        from genius_trading_engine_v3 import get_rigorous_signal
        signal = get_rigorous_signal(symbol)
        return jsonify({
            'ok': True,
            'signal': signal,
            'source': 'Genius Trading Engine v3.0 RIGOROUS',
            'features': [
                'Strict liquidity grab detection',
                'FVG zone analysis',
                'Multi-timeframe confluence',
                'Whale/insider flow',
                'Blockchain metrics',
                'News sentiment'
            ]
        })
    except ImportError:
        # Fallback to v2
        try:
            from genius_trading_engine import genius_engine
            signal = genius_engine.generate_live_signal(symbol)
            return jsonify({
                'ok': True,
                'signal': signal.to_dict(),
                'source': 'Genius Trading Engine v2.0 (fallback)'
            })
        except ImportError:
            return jsonify({
                'ok': False,
                'error': 'Genius Trading Engine not available'
            }), 500
    except Exception as e:
        logger.error(f"Genius signal error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/genius/analysis', methods=['GET'])
def genius_full_analysis():
    """Get comprehensive market analysis from Genius AI"""
    symbol = request.args.get('symbol', 'BTC/USD')
    
    try:
        from genius_trading_engine import genius_engine
        
        # Fetch all data
        quote = genius_engine.fetch_quote(symbol)
        indicators = genius_engine.fetch_technical_indicators(symbol, '1h')
        df = genius_engine.fetch_time_series(symbol, '1h', 100)
        liquidity = genius_engine.detect_liquidity_zones(df) if df is not None else {}
        
        # Generate signal
        signal = genius_engine.generate_live_signal(symbol)
        
        return jsonify({
            'ok': True,
            'symbol': symbol,
            'price': quote.get('price', 0),
            'change_24h': quote.get('change', 0),
            'signal': signal.to_dict(),
            'indicators': {
                'rsi': indicators.get('rsi', [None])[0] if indicators.get('rsi') else None,
                'macd': indicators.get('macd', [{}])[0] if indicators.get('macd') else None,
                'ema21': indicators.get('ema21'),
                'ema50': indicators.get('ema50'),
                'ema200': indicators.get('ema200'),
                'bollinger': indicators.get('bollinger'),
                'atr': indicators.get('atr'),
                'adx': indicators.get('adx'),
                'stoch': indicators.get('stoch')
            },
            'liquidity': {
                'support_levels': liquidity.get('support_levels', []),
                'resistance_levels': liquidity.get('resistance_levels', []),
                'fvg_count': len(liquidity.get('fvg_zones', [])),
                'liquidity_grabs': len(liquidity.get('liquidity_grabs', [])),
                'equal_highs': len(liquidity.get('equal_highs', [])),
                'equal_lows': len(liquidity.get('equal_lows', []))
            },
            'source': 'Genius Trading Engine v2.0'
        })
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return jsonify({
            'ok': False,
            'error': 'Genius Trading Engine not available'
        }), 500
    except Exception as e:
        logger.error(f"Genius analysis error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/genius/tactics', methods=['GET'])
def genius_tactics():
    """Get trading tactics for current market conditions"""
    symbol = request.args.get('symbol', 'BTC/USD')
    
    try:
        from genius_trading_engine import genius_engine
        signal = genius_engine.generate_live_signal(symbol)
        
        return jsonify({
            'ok': True,
            'symbol': symbol,
            'signal_type': signal.signal.value,
            'confidence': signal.confidence,
            'entry_zone': signal.entry_zone,
            'stop_loss': signal.stop_loss,
            'take_profits': [signal.take_profit_1, signal.take_profit_2, signal.take_profit_3],
            'risk_reward': signal.risk_reward,
            'tactics': signal.tactics,
            'reasoning': signal.reasoning
        })
    except Exception as e:
        logger.error(f"Genius tactics error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/news/headlines', methods=['GET'])
def news_headlines():
    """Return curated news headlines"""
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


@app.route('/api/news/twitter', methods=['GET'])
def twitter_news():
    """Return Twitter/X crypto news feed"""
    try:
        # Import Twitter fetcher
        try:
            from twitter_news_fetcher import TwitterNewsFetcher
            fetcher = TwitterNewsFetcher()
            
            # Get limit from query params (default 10)
            limit = int(request.args.get('limit', 10))
            
            # Fetch tweets
            tweets = fetcher.fetch_crypto_tweets(limit=limit)
            
            return jsonify({
                'ok': True,
                'timestamp': datetime.now().isoformat(),
                'count': len(tweets),
                'tweets': tweets,
                'source': 'twitter_fetcher'
            })
        except ImportError:
            # Fallback if twitter_news_fetcher not available
            return jsonify({
                'ok': True,
                'timestamp': datetime.now().isoformat(),
                'count': 3,
                'tweets': [
                    {
                        'text': '🚀 Bitcoin momentum building! Bulls taking control.',
                        'author': 'CryptoWhale',
                        'created_at': datetime.now().isoformat(),
                        'url': 'https://twitter.com/demo',
                        'engagement': 1250,
                        'source': 'fallback'
                    },
                    {
                        'text': '📊 Ethereum showing strength. Watch for breakout!',
                        'author': 'DeFi_Pro',
                        'created_at': datetime.now().isoformat(),
                        'url': 'https://twitter.com/demo',
                        'engagement': 856,
                        'source': 'fallback'
                    },
                    {
                        'text': '⚠️ Market Alert: Major support level holding strong.',
                        'author': 'TechnicalTrader',
                        'created_at': datetime.now().isoformat(),
                        'url': 'https://twitter.com/demo',
                        'engagement': 645,
                        'source': 'fallback'
                    }
                ],
                'source': 'fallback'
            })
    except Exception as e:
        logger.error(f"❌ Twitter news error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/genius/commentary', methods=['GET'])
def genius_commentary():
    """Return Genius commentary payload"""
    try:
        payload = build_genius_payload()
        return jsonify(payload)
    except Exception as e:
        logger.error(f"❌ Genius commentary error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/genius/audio', methods=['GET'])
def genius_audio():
    """Return TTS audio for Genius commentary (placeholder - requires TTS service)"""
    try:
        lang = request.args.get('lang', 'en')
        # Get current commentary
        payload = build_genius_payload()
        commentary = payload.get('commentary', 'Market analysis in progress.')
        
        # For now return a placeholder response
        # In production, integrate with TTS service like Google Cloud TTS, ElevenLabs, etc.
        return jsonify({
            'ok': False,
            'error': 'TTS service not configured. Audio feature coming soon!',
            'text': commentary,
            'language': lang,
            'note': 'Configure ELEVENLABS_API_KEY or GOOGLE_TTS_KEY for audio'
        })
    except Exception as e:
        logger.error(f"❌ Genius audio error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/analytics', methods=['GET'])
def analytics():
    """Return analytics snapshot"""
    try:
        snapshot = cache.get('analytics_snapshot') or build_analytics_snapshot()
        return jsonify(snapshot)
    except Exception as e:
        logger.error(f"❌ Analytics endpoint error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/killzones/overview', methods=['GET'])
def killzones_overview():
    """Return session killzone overview"""
    try:
        snapshot = cache.get('killzone_snapshot') or update_killzone_snapshot()
        return jsonify(snapshot)
    except Exception as e:
        logger.error(f"❌ Killzones endpoint error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Get API server status"""
    return jsonify({
        'ok': True,
        'status': 'running',
        'data_source': 'Twelve Data (crypto, stocks, forex)',
        'last_update': cache['last_update'],
        'cache': {
            'btcPrice': round(cache['btc_price'], 2),
            'btcChange24h': round(cache['btc_change'], 2),
            'ethPrice': round(cache['eth_price'], 2),
            'ethChange24h': round(cache['eth_change'], 2),
            'spyPrice': round(cache['spy_price'], 2),
            'aaplPrice': round(cache['aapl_price'], 2),
            'msftPrice': round(cache['msft_price'], 2),
            'nvdaPrice': round(cache['nvda_price'], 2),
            'eurusd': round(cache['eurusd_price'], 4),
            'gbpusd': round(cache['gbpusd_price'], 4),
            'fearGreed': cache['fear_greed'],
            'goldPrice': round(cache['gold_price'], 2),
            'dxyPrice': round(cache['dxy_price'], 2)
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'api-server'}), 200

@app.route('/', methods=['GET'])
def serve_dashboard():
    # Ensure correct static folder path (absolute path for Render compatibility)
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
    return send_from_directory(static_folder, 'index.html')


def serve_static(filename):
    if filename.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
    return send_from_directory(static_folder, filename)


# Avoid duplicate endpoint registration when the module is imported multiple times
if 'serve_static' not in app.view_functions:
    app.add_url_rule('/<path:filename>', view_func=serve_static)


def root_moved():
    """Root endpoint info"""
    return jsonify({
        'name': '🚀 Hamster Terminal API Server',
        'version': '2.0 - Twelve Data Edition',
        'data_sources': 'Twelve Data (crypto, stocks, forex) + Alternative.me (Fear & Greed)',
        'setup': {
            'api_key': 'Get free key at https://twelvedata.com/docs',
            'env_variable': 'TWELVE_DATA_API_KEY',
            'current_key_status': 'demo' if TWELVE_DATA_API_KEY == 'demo' else '✅ configured'
        },
        'endpoints': {
            '/api/binance/summary': 'Get BTC/ETH prices (from Twelve Data)',
            '/api/stocks': 'Get stock prices (AAPL, MSFT, NVDA, SPY)',
            '/api/forex': 'Get forex pairs (EUR/USD, GBP/USD)',
            '/api/markets': 'Get GOLD, SPY, DXY prices',
            '/api/fng': 'Get Fear & Greed Index',
            '/api/news/headlines': 'Curated market headlines feed',
            '/api/genius/commentary': 'AI commentary fallback payload',
            '/api/analytics': 'Advanced analytics snapshot',
            '/api/killzones/overview': 'Session killzone overlay data',
            '/api/status': 'Server status with all cached data',
            '/health': 'Health check',
            # Advanced Quant Endpoints
            '/api/portfolio/optimize': 'Portfolio optimization (POST)',
            '/api/lstm/predict': 'LSTM price prediction',
            '/api/exchanges/prices': 'Multi-exchange price comparison',
            '/api/exchanges/arbitrage': 'Arbitrage opportunities',
            '/api/backtest/run': 'Run strategy backtest (POST)'
        }
    })


# ============ ADVANCED QUANT ENDPOINTS ============

@app.route('/api/portfolio/optimize', methods=['POST'])
def portfolio_optimize():
    """
    Optimize portfolio weights using Modern Portfolio Theory
    Method: sharpe, min_variance, risk_parity
    """
    if not QUANT_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'Quant modules not available'})
    
    try:
        data = request.get_json()
        returns_data = data.get('returns')  # Dict of asset returns
        method = data.get('method', 'sharpe')
        
        if not returns_data:
            return jsonify({'ok': False, 'error': 'No returns data provided'})
        
        # Convert to DataFrame
        import pandas as pd
        returns_df = pd.DataFrame(returns_data)
        
        # Optimize
        weights = portfolio_optimizer.optimize_portfolio_weights(returns_df, method)
        
        return jsonify({
            'ok': True,
            'weights': weights,
            'method': method,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Portfolio optimization error: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/api/lstm/predict', methods=['GET'])
def lstm_predict():
    """Get LSTM price prediction for BTC"""
    if not QUANT_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'LSTM not available'})
    
    try:
        # Get recent prices from cache (simulated)
        recent_prices = np.array([cache['btc_price']] * 60)  # Placeholder
        
        # Make prediction
        prediction = ensemble_predictor.predict_with_ensemble(
            recent_prices,
            {
                'rsi': cache.get('rsi', 50),
                'macd': cache.get('macd', 0)
            }
        )
        
        return jsonify({
            'ok': True,
            'prediction': prediction,
            'current_price': float(cache['btc_price']),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"LSTM prediction error: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/api/exchanges/prices', methods=['GET'])
def exchange_prices():
    """Get BTC price from multiple exchanges"""
    if not QUANT_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'Exchange manager not available'})
    
    try:
        symbol = request.args.get('symbol', 'BTC/USDT')
        
        # Get prices from all connected exchanges
        prices = exchange_manager.get_all_prices(symbol)
        
        return jsonify({
            'ok': True,
            'symbol': symbol,
            'prices': prices,
            'connected_exchanges': exchange_manager.get_connected_exchanges(),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Exchange prices error: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/api/exchanges/arbitrage', methods=['GET'])
def exchange_arbitrage():
    """Find arbitrage opportunities across exchanges"""
    if not QUANT_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'Exchange manager not available'})
    
    try:
        symbol = request.args.get('symbol', 'BTC/USDT')
        min_spread = float(request.args.get('min_spread', 0.005))
        
        # Find arbitrage
        opportunity = exchange_manager.find_arbitrage_opportunity(symbol, min_spread)
        
        return jsonify({
            'ok': True,
            'opportunity': opportunity,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Arbitrage search error: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    """Run strategy backtest"""
    if not QUANT_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'Backtest engine not available'})
    
    try:
        data = request.get_json()
        ohlcv_data = data.get('data')  # OHLCV DataFrame as dict
        
        if not ohlcv_data:
            return jsonify({'ok': False, 'error': 'No OHLCV data provided'})
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(ohlcv_data)
        
        # Ensure datetime index
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        
        # Run backtest
        results = backtest_engine.run_backtest(df)
        
        return jsonify({
            'ok': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/api/performance/metrics', methods=['POST'])
def performance_metrics():
    """Calculate performance metrics using empyrical"""
    if not QUANT_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'Portfolio optimizer not available'})
    
    try:
        data = request.get_json()
        returns = data.get('returns')  # List of returns
        
        if not returns:
            return jsonify({'ok': False, 'error': 'No returns provided'})
        
        # Convert to Series
        import pandas as pd
        returns_series = pd.Series(returns)
        
        # Calculate metrics
        metrics = portfolio_optimizer.calculate_performance_metrics(returns_series)
        
        return jsonify({
            'ok': True,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        return jsonify({'ok': False, 'error': str(e)})


# ============ GENIUS AI CHAT ENDPOINTS ============
@app.route('/api/genius/chat', methods=['POST'])
def genius_chat():
    """Live chat with Genius AI - multi-language support with voice"""
    try:
        data = request.json or {}
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '')
        language = data.get('language', 'en')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        # Demo response for now
        return jsonify({
            'response': f'🤖 Genius AI: Received "{message}". Full AI chat coming soon with Pro Plus deployment!',
            'mode': 'demo',
            'timestamp': datetime.now().isoformat()
        })
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        # Demo response for now
        return jsonify({
            'response': f'🤖 Genius AI: Received "{message}". Full AI chat coming soon with Pro Plus deployment!',
            'mode': 'demo',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Genius chat error: {e}")
        return jsonify({
            'response': '🤖 AI chat temporarily unavailable. Try again later.',
            'mode': 'error',
            'error': str(e)
        })


# ============ ON-CHAIN DATA ENDPOINTS ============
@app.route('/api/onchain/trending', methods=['GET'])
def onchain_trending():
    """Get trending coins from CoinGecko"""
    try:
        from onchain_data import get_onchain_provider
        provider = get_onchain_provider()
        data = provider.get_trending_coins()
        return jsonify(data)
    except Exception as e:
        logger.error(f"On-chain trending error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/onchain/global', methods=['GET'])
def onchain_global():
    """Get global crypto market metrics"""
    try:
        from onchain_data import get_onchain_provider
        provider = get_onchain_provider()
        data = provider.get_global_metrics()
        return jsonify(data)
    except Exception as e:
        logger.error(f"On-chain global error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/onchain/defi', methods=['GET'])
def onchain_defi():
    """Get DeFi protocol metrics"""
    try:
        from onchain_data import get_onchain_provider
        provider = get_onchain_provider()
        data = provider.get_defi_metrics()
        return jsonify(data)
    except Exception as e:
        logger.error(f"On-chain DeFi error: {e}")
        return jsonify({'error': str(e)}), 500


# ============ SMART ALERTS ENDPOINTS ============
@app.route('/api/alerts/create', methods=['POST'])
def create_alert():
    """Create new smart alert"""
    try:
        from smart_alerts import get_alerts_system
        
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        symbol = data.get('symbol', 'BTC').upper()
        condition = data.get('condition', 'above')
        value = float(data.get('value', 0))
        alert_type = data.get('type', 'price')
        
        alerts = get_alerts_system()
        alert_id = alerts.add_alert(user_id, symbol, condition, value, alert_type)
        
        return jsonify({
            'ok': True,
            'alert_id': alert_id,
            'message': f'Alert created: {symbol} {condition} {value}'
        })
        
    except Exception as e:
        logger.error(f"Create alert error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/alerts/list', methods=['GET'])
def list_alerts():
    """Get user's alerts"""
    try:
        from smart_alerts import get_alerts_system
        
        user_id = request.args.get('user_id', 'anonymous')
        alerts = get_alerts_system()
        user_alerts = alerts.get_user_alerts(user_id)
        
        return jsonify({
            'ok': True,
            'alerts': user_alerts,
            'count': len(user_alerts)
        })
        
    except Exception as e:
        logger.error(f"List alerts error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/alerts/delete/<alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete alert"""
    try:
        from smart_alerts import get_alerts_system
        
        alerts = get_alerts_system()
        success = alerts.remove_alert(alert_id)
        
        return jsonify({
            'ok': success,
            'message': 'Alert deleted' if success else 'Alert not found'
        })
        
    except Exception as e:
        logger.error(f"Delete alert error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/alerts/suggest', methods=['GET'])
def suggest_alerts():
    """Get suggested alert levels"""
    try:
        from smart_alerts import get_alerts_system
        
        symbol = request.args.get('symbol', 'BTC').upper()
        price = float(request.args.get('price', cache.get('btc_price', 95000)))
        
        alerts = get_alerts_system()
        suggestions = alerts.suggest_alerts(symbol, price)
        
        return jsonify({
            'ok': True,
            'symbol': symbol,
            'current_price': price,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Suggest alerts error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============ NEWS INTELLIGENCE ENDPOINTS ============
@app.route('/api/news/intelligence', methods=['GET'])
def news_intelligence():
    """Get latest news with sentiment analysis"""
    try:
        from news_intelligence import get_news_intelligence
        
        limit = int(request.args.get('limit', 20))
        news = get_news_intelligence()
        articles = news.get_latest_news(limit=limit)
        
        return jsonify({
            'ok': True,
            'articles': articles,
            'count': len(articles)
        })
        
    except Exception as e:
        logger.error(f"News intelligence error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/news/sentiment', methods=['GET'])
def news_sentiment():
    """Get overall market sentiment from news"""
    try:
        from news_intelligence import get_news_intelligence
        
        timeframe = request.args.get('timeframe', '24h')
        news = get_news_intelligence()
        sentiment = news.get_sentiment_summary(timeframe=timeframe)
        
        return jsonify({
            'ok': True,
            **sentiment
        })
        
    except Exception as e:
        logger.error(f"News sentiment error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/news/top-stories', methods=['GET'])
def top_stories():
    """Get top 3 stories with Genius commentary"""
    try:
        from news_intelligence import get_news_intelligence
        
        limit = int(request.args.get('limit', 3))
        news = get_news_intelligence()
        stories = news.get_top_stories(limit=limit)
        
        return jsonify({
            'ok': True,
            'stories': stories
        })
        
    except Exception as e:
        logger.error(f"Top stories error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============ PORTFOLIO HEALTH ENDPOINTS ============
@app.route('/api/portfolio/health', methods=['POST'])
def portfolio_health():
    """Analyze portfolio health"""
    try:
        from portfolio_health import get_portfolio_health
        
        data = request.json
        positions = data.get('positions', [])
        prices = data.get('prices', {})
        
        if not positions:
            return jsonify({'ok': False, 'error': 'No positions provided'}), 400
        
        health = get_portfolio_health()
        analysis = health.analyze_portfolio(positions, prices)
        
        return jsonify({
            'ok': True,
            **analysis
        })
        
    except Exception as e:
        logger.error(f"Portfolio health error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============ JP MORGAN QUANT METHODS (TWELVE DATA PRO) ============

@app.route('/api/jpmorgan/quote', methods=['GET'])
def jpmorgan_quote():
    """Get real-time quote from Twelve Data Pro"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbol = request.args.get('symbol', 'BTC/USD')
        quote = twelve_data.get_quote(symbol)
        
        if quote:
            return jsonify({'ok': True, **quote})
        return jsonify({'ok': False, 'error': f'No data for {symbol}'}), 404
        
    except Exception as e:
        logger.error(f"JP Morgan quote error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/multi-quote', methods=['GET'])
def jpmorgan_multi_quote():
    """Get quotes for multiple symbols"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbols = request.args.get('symbols', 'BTC/USD,ETH/USD,AAPL,SPY')
        symbol_list = [s.strip() for s in symbols.split(',')]
        quotes = twelve_data.get_multiple_quotes(symbol_list)
        
        return jsonify({
            'ok': True,
            'quotes': quotes,
            'count': len(quotes)
        })
        
    except Exception as e:
        logger.error(f"JP Morgan multi-quote error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/volatility', methods=['GET'])
def jpmorgan_volatility():
    """Get live volatility analysis"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbol = request.args.get('symbol', 'BTC/USD')
        days = int(request.args.get('days', 30))
        
        analysis = live_analyzer.get_live_volatility_analysis(symbol, days)
        
        if analysis:
            return jsonify({'ok': True, **analysis})
        return jsonify({'ok': False, 'error': f'Insufficient data for {symbol}'}), 404
        
    except Exception as e:
        logger.error(f"JP Morgan volatility error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/risk-metrics', methods=['GET'])
def jpmorgan_risk_metrics():
    """Get VaR, Sharpe, Sortino, Max Drawdown"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbol = request.args.get('symbol', 'SPY')
        days = int(request.args.get('days', 100))
        
        analysis = live_analyzer.get_live_risk_metrics(symbol, days)
        
        if analysis:
            return jsonify({'ok': True, **analysis})
        return jsonify({'ok': False, 'error': f'Insufficient data for {symbol}'}), 404
        
    except Exception as e:
        logger.error(f"JP Morgan risk metrics error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/straddle', methods=['GET'])
def jpmorgan_straddle():
    """Calculate straddle pricing and expected move"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbol = request.args.get('symbol', 'BTC/USD')
        days = int(request.args.get('days', 30))
        implied_vol = request.args.get('implied_vol')
        
        if implied_vol:
            implied_vol = float(implied_vol)
        
        analysis = live_analyzer.get_live_straddle_analysis(symbol, implied_vol, days)
        
        if analysis:
            return jsonify({'ok': True, **analysis})
        return jsonify({'ok': False, 'error': f'Could not calculate straddle for {symbol}'}), 404
        
    except Exception as e:
        logger.error(f"JP Morgan straddle error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/z-score', methods=['GET'])
def jpmorgan_z_score():
    """Calculate Altman Z-Score for credit risk"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbol = request.args.get('symbol', 'AAPL')
        
        analysis = live_analyzer.get_live_z_score(symbol)
        
        if analysis:
            return jsonify({'ok': True, **analysis})
        return jsonify({'ok': False, 'error': f'Insufficient financial data for {symbol}'}), 404
        
    except Exception as e:
        logger.error(f"JP Morgan Z-Score error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/technical', methods=['GET'])
def jpmorgan_technical():
    """Get technical analysis snapshot (RSI, MACD, Bollinger, ATR)"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbol = request.args.get('symbol', 'BTC/USD')
        
        analysis = live_analyzer.get_technical_snapshot(symbol)
        
        if analysis:
            return jsonify({'ok': True, **analysis})
        return jsonify({'ok': False, 'error': f'Could not get technical data for {symbol}'}), 404
        
    except Exception as e:
        logger.error(f"JP Morgan technical error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/multi-asset', methods=['GET'])
def jpmorgan_multi_asset():
    """Get snapshot of all major asset classes"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        snapshot = live_analyzer.get_multi_asset_snapshot()
        return jsonify({'ok': True, **snapshot})
        
    except Exception as e:
        logger.error(f"JP Morgan multi-asset error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/position-size', methods=['POST'])
def jpmorgan_position_size():
    """Calculate volatility-adjusted position size"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        data = request.json or {}
        account_size = float(data.get('account_size', 100000))
        risk_pct = float(data.get('risk_pct', 0.02))
        stop_loss_pct = float(data.get('stop_loss_pct', 0.03))
        symbol = data.get('symbol', 'BTC/USD')
        
        # Get live volatility
        vol_analysis = live_analyzer.get_live_volatility_analysis(symbol, 30)
        volatility = vol_analysis['volatility_annual'] if vol_analysis else 0.5
        
        # Calculate position size
        sizing = crypto_risk.position_size_by_volatility(
            account_size=account_size,
            risk_pct=risk_pct,
            stop_loss_pct=stop_loss_pct,
            volatility=volatility
        )
        
        return jsonify({
            'ok': True,
            'symbol': symbol,
            'current_volatility': volatility,
            **sizing
        })
        
    except Exception as e:
        logger.error(f"JP Morgan position size error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/options-price', methods=['POST'])
def jpmorgan_options_price():
    """Calculate Black-Scholes options prices"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        data = request.json or {}
        S = float(data.get('spot_price', 100))
        K = float(data.get('strike_price', 100))
        T = float(data.get('time_to_expiry', 0.25))  # years
        r = float(data.get('risk_free_rate', 0.05))
        sigma = float(data.get('volatility', 0.2))
        
        call_price = options_pricer.black_scholes_call(S, K, T, r, sigma)
        put_price = options_pricer.black_scholes_put(S, K, T, r, sigma)
        straddle_cf = options_pricer.straddle_price_closed_form(vol=sigma, time=T, forward=S)
        
        return jsonify({
            'ok': True,
            'inputs': {
                'spot_price': S,
                'strike_price': K,
                'time_to_expiry': T,
                'risk_free_rate': r,
                'volatility': sigma
            },
            'call_price': round(call_price, 4),
            'put_price': round(put_price, 4),
            'straddle_approximation': round(straddle_cf, 4),
            'straddle_usd': round(straddle_cf * S, 2)
        })
        
    except Exception as e:
        logger.error(f"JP Morgan options price error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/time-series', methods=['GET'])
def jpmorgan_time_series():
    """Get historical OHLCV data"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbol = request.args.get('symbol', 'BTC/USD')
        interval = request.args.get('interval', '1day')
        outputsize = int(request.args.get('outputsize', 100))
        
        df = twelve_data.get_time_series(symbol, interval, outputsize)
        
        if df is not None and len(df) > 0:
            return jsonify({
                'ok': True,
                'symbol': symbol,
                'interval': interval,
                'count': len(df),
                'data': df.to_dict(orient='records')
            })
        return jsonify({'ok': False, 'error': f'No data for {symbol}'}), 404
        
    except Exception as e:
        logger.error(f"JP Morgan time-series error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/indicator/<indicator>', methods=['GET'])
def jpmorgan_indicator(indicator):
    """Get technical indicator (rsi, macd, bbands, atr, sma, ema, etc.)"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbol = request.args.get('symbol', 'BTC/USD')
        interval = request.args.get('interval', '1day')
        time_period = int(request.args.get('time_period', 14))
        
        df = twelve_data.get_technical_indicator(
            symbol, indicator, interval, time_period=time_period
        )
        
        if df is not None and len(df) > 0:
            return jsonify({
                'ok': True,
                'symbol': symbol,
                'indicator': indicator,
                'interval': interval,
                'count': len(df),
                'latest': df.iloc[-1].to_dict(),
                'data': df.tail(50).to_dict(orient='records')
            })
        return jsonify({'ok': False, 'error': f'No {indicator} data for {symbol}'}), 404
        
    except Exception as e:
        logger.error(f"JP Morgan indicator error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/jpmorgan/full-analysis', methods=['GET'])
def jpmorgan_full_analysis():
    """Complete analysis for a symbol (volatility, risk, technical, straddle)"""
    if not JPMORGAN_MODULES_AVAILABLE:
        return jsonify({'ok': False, 'error': 'JP Morgan modules not available'}), 500
    
    try:
        symbol = request.args.get('symbol', 'BTC/USD')
        
        # Gather all analyses
        quote = twelve_data.get_quote(symbol)
        volatility = live_analyzer.get_live_volatility_analysis(symbol, 30)
        risk = live_analyzer.get_live_risk_metrics(symbol, 100)
        technical = live_analyzer.get_technical_snapshot(symbol)
        straddle = live_analyzer.get_live_straddle_analysis(symbol, days_to_expiry=30)
        
        return jsonify({
            'ok': True,
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'quote': quote,
            'volatility_analysis': volatility,
            'risk_metrics': risk,
            'technical_analysis': technical,
            'straddle_analysis': straddle
        })
        
    except Exception as e:
        logger.error(f"JP Morgan full analysis error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# Start WebSocket stream (ensures it runs in Gunicorn)
start_websocket_stream()

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 HAMSTER TERMINAL API SERVER v5.0 - JP MORGAN QUANT EDITION")
    print("=" * 80)
    print("Server starting on http://0.0.0.0:5000")
    print("")
    print("🧠 AI/ML Stack:")
    if AI_MODULES_AVAILABLE:
        print("  ✅ Sentiment Analysis (OpenAI GPT + TextBlob)")
        print("  ✅ News Processing (NewsAPI + Alpha Vantage)")
        print("  ✅ LLM Genius Brain (GPT-powered commentary)")
    else:
        print("  ⚠️  AI modules in fallback mode")
    
    print("")
    print("📊 Quant Modules:")
    if QUANT_MODULES_AVAILABLE:
        print("  ✅ Portfolio Optimization (Mean-Variance, Risk Parity, Sharpe)")
        print("  ✅ LSTM Price Prediction (TensorFlow/Keras)")
        print("  ✅ Multi-Exchange Integration (ccxt - 70+ exchanges)")
        print("  ✅ Professional Backtesting (backtrader framework)")
        print("  ✅ Performance Metrics (empyrical, statsmodels)")
    else:
        print("  ⚠️  Quant modules not loaded")
    
    print("")
    print("🏦 JP Morgan Quant Methods (NEW!):")
    if JPMORGAN_MODULES_AVAILABLE:
        print("  ✅ Twelve Data Pro API - Real-time market data")
        print("  ✅ Options Pricing (Black-Scholes, Monte Carlo, Straddle)")
        print("  ✅ Volatility Analysis (5d/10d/21d, Regime Detection)")
        print("  ✅ Risk Metrics (VaR, Expected Shortfall, Sharpe, Sortino)")
        print("  ✅ Credit Analysis (Altman Z-Score, Credit Ratings)")
        print("  ✅ Technical Indicators (RSI, MACD, Bollinger, ATR)")
        print("  ✅ Position Sizing (Volatility-adjusted)")
    else:
        print("  ⚠️  JP Morgan modules not loaded")
    
    print("")
    print("📡 Real-time data sources:")
    print("  🔴 Twelve Data Pro (PRIMARY) - Real-time prices")
    print("     Crypto: BTC/USD, ETH/USD, SOL/USD, XRP/USD")
    print("     Stocks: AAPL, MSFT, NVDA, TSLA, SPY, QQQ")
    print("     Forex: EUR/USD, GBP/USD, USD/JPY")
    print("     Commodities: XAU/USD (Gold), XAG/USD (Silver)")
    print("  📊 REST API (BACKUP) - Every 30 seconds")
    print("  😨 Alternative.me - Fear & Greed Index")
    print("")
    if TWELVE_DATA_API_KEY == 'demo':
        print("⚠️  USING DEMO KEY - LIMITED TO 800 CALLS/MIN")
        print("    Setup: https://twelvedata.com")
        print("    Set env: $env:TWELVE_DATA_API_KEY='your_key'")
    else:
        print("✅ Twelve Data API Key configured")
    print("")
    print("🎯 JP Morgan Quant Endpoints (NEW!):")
    print("  GET  /api/jpmorgan/quote?symbol=BTC/USD")
    print("  GET  /api/jpmorgan/multi-quote?symbols=BTC/USD,AAPL,SPY")
    print("  GET  /api/jpmorgan/volatility?symbol=BTC/USD&days=30")
    print("  GET  /api/jpmorgan/risk-metrics?symbol=SPY&days=100")
    print("  GET  /api/jpmorgan/straddle?symbol=BTC/USD&days=30")
    print("  GET  /api/jpmorgan/z-score?symbol=AAPL")
    print("  GET  /api/jpmorgan/technical?symbol=BTC/USD")
    print("  GET  /api/jpmorgan/multi-asset")
    print("  GET  /api/jpmorgan/time-series?symbol=BTC/USD&interval=1day")
    print("  GET  /api/jpmorgan/indicator/rsi?symbol=BTC/USD")
    print("  GET  /api/jpmorgan/full-analysis?symbol=BTC/USD")
    print("  POST /api/jpmorgan/position-size")
    print("  POST /api/jpmorgan/options-price")
    print("")
    print("🌐 WebSocket Connection:")
    print("  Client: ws://localhost:5000/socket.io/?transport=websocket")
    print("  Events: connect, subscribe, price_update, disconnect")
    print("")
    print("=" * 80)
    
    # Start WebSocket stream
    # start_websocket_stream() - Moved to module level for Gunicorn support
    
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
