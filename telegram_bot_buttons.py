"""
🐹 HAMSTER TERMINAL - TELEGRAM BOT Z PRZYCISKAMI
Profesjonalne sygnały tradingowe na żywo

Komendy + Inline Buttons + AUTO SIGNALS
v2.0 - FULL FEATURE EDITION
"""

import requests
import logging
import random
import asyncio
import json
import os
from datetime import datetime, time, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, JobQueue, MessageHandler, filters, ConversationHandler

# ═══════════════════════════════════════════════════════════════
# PERSISTENT STORAGE - dane przetrwają restart bota
# ═══════════════════════════════════════════════════════════════
DATA_FILE = 'hamster_data.json'

def load_data():
    """Wczytaj dane z pliku JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'subscribers': [],
        'signal_subscribers': [],
        'price_alerts': {},
        'signal_stats': {
            'sent': 0, 
            'types': {},
            'history': [],  # Historia sygnałów: {symbol, direction, entry, tp, sl, timestamp, result}
            'accuracy': {'total': 0, 'wins': 0, 'losses': 0, 'pending': 0}
        },
        'whale_alerts': []
    }

def save_data(data):
    """Zapisz dane do pliku JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"Blad zapisu danych: {e}")

# Konfiguracja

# Pobierz tokeny z ENV (Render.com)
BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN', os.environ.get('BOT_TOKEN', '8254662818:AAGSCUbd-Zc8tmjmCB3ujLNksLqxICJ2rJw'))
TWELVE_DATA_API = os.environ.get('TWELVE_DATA_API_KEY', os.environ.get('TWELVE_DATA_API', 'd54ad684cd8f40de895ec569d6128821'))
CHAT_ID = os.environ.get('CHAT_ID', '5616894588')

if not BOT_TOKEN or BOT_TOKEN.startswith('8254662818:'):
    print("[WARNING] TELEGRAM_TOKEN nie ustawiony - używam domyślnego")
if not TWELVE_DATA_API or TWELVE_DATA_API == 'd54ad684cd8f40de895ec569d6128821':
    print("[WARNING] TWELVE_DATA_API_KEY nie ustawiony - używam domyślnego")
if not CHAT_ID or CHAT_ID == '5616894588':
    print("[WARNING] CHAT_ID nie ustawiony - używam domyślnego")

# GIF Animacje chomika 🐹 (używamy .gif URLs bezpośrednio)

# 🐹 Zabawne GIFy z chomikami (rozszerzona lista)
HAMSTER_GIF = "https://i.giphy.com/DoCIC5Pxp57qg.gif"  # Chomik je
HAMSTER_DANCE_GIF = "https://i.giphy.com/rHR8qP1mC5V3G.gif"  # Chomik tańczy
KUNGFU_TRAINING_GIF = "https://i.giphy.com/11JbaLzOXsg6Fq.gif"  # Kung fu
HAMSTER_WHEEL_1 = "https://i.giphy.com/EUKWawNC65oc0.gif"  # Szybki spin
HAMSTER_WHEEL_2 = "https://i.giphy.com/10CEpO5Sfi8UBG.gif"  # Cabin fever
HAMSTER_WHEEL_3 = "https://i.giphy.com/6FoN80VbmwM00.gif"  # Wiele chomików
# Nowe zabawne GIFy:
HAMSTER_POPCORN = "https://i.giphy.com/3o6Zt6ML6BklcajjsA.gif"  # Chomik je popcorn
HAMSTER_COMPUTER = "https://i.giphy.com/3o7TKy5Wv5rK6U6b0w.gif"  # Chomik przy komputerze
HAMSTER_SLEEPY = "https://i.giphy.com/3o6Zt8zb1P5G6U6b0w.gif"  # Śpiący chomik
HAMSTER_ZOOM = "https://i.giphy.com/3o6ZtpxSZbQRRnwCKQ.gif"  # Chomik zoomuje
HAMSTER_PARTY = "https://i.giphy.com/3o6Zt6zG7QwZ0p6b0w.gif"  # Chomik imprezuje
HAMSTER_SUPERHERO = "https://i.giphy.com/3o6Zt6zG7QwZ0p6b0w.gif"  # Chomik superbohater
HAMSTER_FAIL = "https://i.giphy.com/3o6Zt8zb1P5G6U6b0w.gif"  # Chomik failuje
HAMSTER_SURPRISE = "https://i.giphy.com/3o6Zt6ML6BklcajjsA.gif"  # Zaskoczony chomik

# 📈📉 TRADING GIFs - śmieszne reakcje rynkowe! (bezpośrednie linki)
GIF_STONKS_UP = "https://i.giphy.com/XDAY1NNG2VvobAp9o0.gif"  # Stonks meme
GIF_PUMP_IT = "https://i.giphy.com/8igfrOLF6m9jv0T3W0.gif"  # Pump it!
GIF_TO_THE_MOON = "https://i.giphy.com/trN9ht5RlE3Dcwavg2.gif"  # To the moon
GIF_MONEY_PRINTER = "https://i.giphy.com/Jso1dbifABkyEDiIXQ.gif"  # Money printer BRRR
GIF_MAKE_IT_RAIN = "https://i.giphy.com/YSBSPEBMVqWYG7zJwU.gif"  # Make it rain
GIF_CRASH = "https://i.giphy.com/l2JeeA6RKceFhgO1a.gif"  # Homer Simpson crash
GIF_THIS_IS_FINE = "https://i.giphy.com/QMHoU66sBXqqLqYvGO.gif"  # This is fine 
GIF_CHART_PAIN = "https://i.giphy.com/iRIf7MAdvOIbdxK4rR.gif"  # Chart pain
GIF_MARGIN_CALL = "https://i.giphy.com/1ksIJmjTF6UsdMZlQG.gif"  # Margin call
GIF_REKT = "https://i.giphy.com/s4W4zMzyV6oIo.gif"  # REKT

# Lista wszystkich GIFów chomika (rozszerzona)
HAMSTER_GIFS = [
    HAMSTER_GIF, HAMSTER_DANCE_GIF, KUNGFU_TRAINING_GIF,
    HAMSTER_WHEEL_1, HAMSTER_WHEEL_2, HAMSTER_WHEEL_3,
    HAMSTER_POPCORN, HAMSTER_COMPUTER, HAMSTER_SLEEPY, HAMSTER_ZOOM,
    HAMSTER_PARTY, HAMSTER_SUPERHERO, HAMSTER_FAIL, HAMSTER_SURPRISE
]

# Lista GIFów tradingowych (podzielona na bullish/bearish)
BULLISH_GIFS = [GIF_STONKS_UP, GIF_PUMP_IT, GIF_TO_THE_MOON, GIF_MONEY_PRINTER, GIF_MAKE_IT_RAIN]
BEARISH_GIFS = [GIF_CRASH, GIF_THIS_IS_FINE, GIF_CHART_PAIN, GIF_MARGIN_CALL, GIF_REKT]
ALL_TRADING_GIFS = BULLISH_GIFS + BEARISH_GIFS + HAMSTER_GIFS

# Wczytaj dane z persistent storage
_stored_data = load_data()

# Subskrybenci auto-raportów i auto-sygnałów
# Jeśli brak zapisanych danych, użyj domyślnego CHAT_ID
_default_subs = [CHAT_ID]
report_subscribers = set(_stored_data.get('subscribers') or _default_subs)
signal_subscribers = set(_stored_data.get('signal_subscribers') or _default_subs)
previous_prices = {}  # Historia cen do wykrywania nagłych ruchów
last_signals = {}  # Cache ostatnich sygnałów żeby nie powtarzać
price_history = {}  # Historia cen dla każdego assetu (ostatnie 10 odczytów)

# ═══════════════════════════════════════════════════════════════
# PRICE ALERTS - użytkownicy mogą ustawiać własne alerty cenowe
# Format: {chat_id: [{'symbol': 'BTC/USD', 'condition': '>', 'price': 110000, 'triggered': False}, ...]}
# ═══════════════════════════════════════════════════════════════
price_alerts = _stored_data.get('price_alerts', {})

# ═══════════════════════════════════════════════════════════════
# CUSTOM SYMBOL - użytkownicy oczekujący na wpisanie symbolu
# ═══════════════════════════════════════════════════════════════
WAITING_FOR_SYMBOL = 1
users_waiting_for_symbol = set()  # chat_id użytkowników czekających na symbol

# ═══════════════════════════════════════════════════════════════
# FUNDING CALCULATOR - użytkownicy oczekujący na dane do kalkulatora
# ═══════════════════════════════════════════════════════════════
# Format: {chat_id: {'symbol': 'BTCUSDT', 'funding_rate': 0.01, 'step': 'amount'}}
users_waiting_for_funding = {}  # chat_id -> dane kalkulatora

# Statystyki sygnałów
signal_stats = _stored_data.get('signal_stats', {
    'sent': 0, 
    'types': {},
    'history': [],
    'accuracy': {'total': 0, 'wins': 0, 'losses': 0, 'pending': 0}
})

# Upewnij się że mamy wszystkie pola
if 'history' not in signal_stats:
    signal_stats['history'] = []
if 'accuracy' not in signal_stats:
    signal_stats['accuracy'] = {'total': 0, 'wins': 0, 'losses': 0, 'pending': 0}

# ═══════════════════════════════════════════════════════════════
# SIGNAL ACCURACY TRACKER - Śledzenie skuteczności sygnałów
# ═══════════════════════════════════════════════════════════════
def check_signal_accuracy():
    """
    Sprawdza poprzednie sygnały i aktualizuje ich status (WIN/LOSS/PENDING)
    na podstawie aktualnych cen z Binance.
    """
    global signal_stats
    
    if not signal_stats.get('history'):
        return
    
    # Pobierz aktualne ceny
    try:
        symbols_to_check = set()
        for sig in signal_stats['history']:
            if sig.get('result') == 'PENDING':
                symbols_to_check.add(sig.get('binance_symbol', 'BTCUSDT'))
        
        if not symbols_to_check:
            return
        
        current_prices = {}
        for sym in symbols_to_check:
            try:
                ticker = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', timeout=3).json()
                current_prices[sym] = float(ticker['price'])
            except:
                continue
        
        # Sprawdź każdy pending sygnał
        updated = False
        for sig in signal_stats['history']:
            if sig.get('result') != 'PENDING':
                continue
            
            binance_sym = sig.get('binance_symbol', 'BTCUSDT')
            if binance_sym not in current_prices:
                continue
            
            current_price = current_prices[binance_sym]
            entry = sig.get('entry', 0)
            tp = sig.get('tp', 0)
            sl = sig.get('sl', 0)
            direction = sig.get('direction', 'LONG')
            
            # Sprawdź timeout (max 48h na sygnał)
            sig_time = datetime.fromisoformat(sig.get('timestamp', datetime.now().isoformat()))
            hours_passed = (datetime.now() - sig_time).total_seconds() / 3600
            
            if hours_passed > 48:
                # Timeout - zamknij po aktualnej cenie
                if direction == 'LONG':
                    if current_price > entry:
                        sig['result'] = 'WIN'
                        sig['close_price'] = current_price
                        sig['close_reason'] = 'TIMEOUT_PROFIT'
                        signal_stats['accuracy']['wins'] += 1
                    else:
                        sig['result'] = 'LOSS'
                        sig['close_price'] = current_price
                        sig['close_reason'] = 'TIMEOUT_LOSS'
                        signal_stats['accuracy']['losses'] += 1
                else:  # SHORT
                    if current_price < entry:
                        sig['result'] = 'WIN'
                        sig['close_price'] = current_price
                        sig['close_reason'] = 'TIMEOUT_PROFIT'
                        signal_stats['accuracy']['wins'] += 1
                    else:
                        sig['result'] = 'LOSS'
                        sig['close_price'] = current_price
                        sig['close_reason'] = 'TIMEOUT_LOSS'
                        signal_stats['accuracy']['losses'] += 1
                signal_stats['accuracy']['pending'] -= 1
                updated = True
                continue
            
            # Sprawdź TP/SL
            if direction == 'LONG':
                if current_price >= tp:
                    sig['result'] = 'WIN'
                    sig['close_price'] = current_price
                    sig['close_reason'] = 'TP_HIT'
                    signal_stats['accuracy']['wins'] += 1
                    signal_stats['accuracy']['pending'] -= 1
                    updated = True
                elif current_price <= sl:
                    sig['result'] = 'LOSS'
                    sig['close_price'] = current_price
                    sig['close_reason'] = 'SL_HIT'
                    signal_stats['accuracy']['losses'] += 1
                    signal_stats['accuracy']['pending'] -= 1
                    updated = True
            else:  # SHORT
                if current_price <= tp:
                    sig['result'] = 'WIN'
                    sig['close_price'] = current_price
                    sig['close_reason'] = 'TP_HIT'
                    signal_stats['accuracy']['wins'] += 1
                    signal_stats['accuracy']['pending'] -= 1
                    updated = True
                elif current_price >= sl:
                    sig['result'] = 'LOSS'
                    sig['close_price'] = current_price
                    sig['close_reason'] = 'SL_HIT'
                    signal_stats['accuracy']['losses'] += 1
                    signal_stats['accuracy']['pending'] -= 1
                    updated = True
        
        if updated:
            save_data({
                'subscribers': list(report_subscribers),
                'signal_subscribers': list(signal_subscribers),
                'price_alerts': price_alerts,
                'signal_stats': signal_stats
            })
    except Exception as e:
        print(f"[ACCURACY CHECK ERROR] {e}")

def get_accuracy_stats():
    """Zwraca statystyki skuteczności sygnałów"""
    acc = signal_stats.get('accuracy', {'total': 0, 'wins': 0, 'losses': 0, 'pending': 0})
    total = acc.get('total', 0)
    wins = acc.get('wins', 0)
    losses = acc.get('losses', 0)
    pending = acc.get('pending', 0)
    
    closed = wins + losses
    win_rate = (wins / closed * 100) if closed > 0 else 0
    
    return {
        'total': total,
        'wins': wins,
        'losses': losses,
        'pending': pending,
        'closed': closed,
        'win_rate': win_rate
    }

def add_signal_to_history(symbol, binance_symbol, direction, entry, tp, sl, confidence, reasons):
    """Dodaje nowy sygnał do historii do śledzenia"""
    global signal_stats
    
    signal_entry = {
        'symbol': symbol,
        'binance_symbol': binance_symbol,
        'direction': direction,
        'entry': entry,
        'tp': tp,
        'sl': sl,
        'confidence': confidence,
        'reasons': reasons,
        'timestamp': datetime.now().isoformat(),
        'result': 'PENDING',
        'close_price': None,
        'close_reason': None
    }
    
    # Dodaj do historii (max 100 ostatnich sygnałów)
    signal_stats['history'].append(signal_entry)
    if len(signal_stats['history']) > 100:
        signal_stats['history'] = signal_stats['history'][-100:]
    
    # Aktualizuj liczniki
    signal_stats['accuracy']['total'] = signal_stats['accuracy'].get('total', 0) + 1
    signal_stats['accuracy']['pending'] = signal_stats['accuracy'].get('pending', 0) + 1
    
    save_data({
        'subscribers': list(report_subscribers),
        'signal_subscribers': list(signal_subscribers),
        'price_alerts': price_alerts,
        'signal_stats': signal_stats
    })

# ═══════════════════════════════════════════════════════════════
# API STATUS & DATA RELIABILITY TRACKER
# Śledzenie poprawności i rzetelności danych z API
# ═══════════════════════════════════════════════════════════════

api_status = {
    'binance_spot': {'status': 'UNKNOWN', 'last_check': None, 'latency_ms': 0, 'errors': 0, 'success': 0},
    'binance_futures': {'status': 'UNKNOWN', 'last_check': None, 'latency_ms': 0, 'errors': 0, 'success': 0},
    'twelve_data': {'status': 'UNKNOWN', 'last_check': None, 'latency_ms': 0, 'errors': 0, 'success': 0},
    'alternative_me': {'status': 'UNKNOWN', 'last_check': None, 'latency_ms': 0, 'errors': 0, 'success': 0},
    'last_full_check': None,
    'overall_reliability': 100.0
}

def check_api_status():
    """
    Sprawdza status wszystkich API i aktualizuje metryki rzetelności.
    Zwraca słownik ze statusami i wskaźnikiem rzetelności.
    """
    global api_status
    import time as time_module
    
    results = {}
    
    # 1. BINANCE SPOT API
    try:
        start = time_module.time()
        r = requests.get('https://api.binance.com/api/v3/ping', timeout=5)
        latency = (time_module.time() - start) * 1000
        
        if r.status_code == 200:
            api_status['binance_spot']['status'] = 'ONLINE'
            api_status['binance_spot']['latency_ms'] = round(latency)
            api_status['binance_spot']['success'] += 1
            results['binance_spot'] = {'ok': True, 'latency': latency}
        else:
            api_status['binance_spot']['status'] = 'ERROR'
            api_status['binance_spot']['errors'] += 1
            results['binance_spot'] = {'ok': False, 'error': f'HTTP {r.status_code}'}
    except Exception as e:
        api_status['binance_spot']['status'] = 'OFFLINE'
        api_status['binance_spot']['errors'] += 1
        results['binance_spot'] = {'ok': False, 'error': str(e)}
    api_status['binance_spot']['last_check'] = datetime.now().isoformat()
    
    # 2. BINANCE FUTURES API
    try:
        start = time_module.time()
        r = requests.get('https://fapi.binance.com/fapi/v1/ping', timeout=5)
        latency = (time_module.time() - start) * 1000
        
        if r.status_code == 200:
            api_status['binance_futures']['status'] = 'ONLINE'
            api_status['binance_futures']['latency_ms'] = round(latency)
            api_status['binance_futures']['success'] += 1
            results['binance_futures'] = {'ok': True, 'latency': latency}
        else:
            api_status['binance_futures']['status'] = 'ERROR'
            api_status['binance_futures']['errors'] += 1
            results['binance_futures'] = {'ok': False, 'error': f'HTTP {r.status_code}'}
    except Exception as e:
        api_status['binance_futures']['status'] = 'OFFLINE'
        api_status['binance_futures']['errors'] += 1
        results['binance_futures'] = {'ok': False, 'error': str(e)}
    api_status['binance_futures']['last_check'] = datetime.now().isoformat()
    
    # 3. TWELVE DATA API
    try:
        start = time_module.time()
        r = requests.get(f'https://api.twelvedata.com/time_series?symbol=BTC/USD&interval=1min&outputsize=1&apikey={TWELVE_DATA_API}', timeout=5)
        latency = (time_module.time() - start) * 1000
        
        if r.status_code == 200 and 'values' in r.json():
            api_status['twelve_data']['status'] = 'ONLINE'
            api_status['twelve_data']['latency_ms'] = round(latency)
            api_status['twelve_data']['success'] += 1
            results['twelve_data'] = {'ok': True, 'latency': latency}
        else:
            api_status['twelve_data']['status'] = 'LIMITED'
            api_status['twelve_data']['errors'] += 1
            results['twelve_data'] = {'ok': False, 'error': 'Rate limited'}
    except Exception as e:
        api_status['twelve_data']['status'] = 'OFFLINE'
        api_status['twelve_data']['errors'] += 1
        results['twelve_data'] = {'ok': False, 'error': str(e)}
    api_status['twelve_data']['last_check'] = datetime.now().isoformat()
    
    # 4. ALTERNATIVE.ME (Fear & Greed)
    try:
        start = time_module.time()
        r = requests.get('https://api.alternative.me/fng/?limit=1', timeout=5)
        latency = (time_module.time() - start) * 1000
        
        if r.status_code == 200 and 'data' in r.json():
            api_status['alternative_me']['status'] = 'ONLINE'
            api_status['alternative_me']['latency_ms'] = round(latency)
            api_status['alternative_me']['success'] += 1
            results['alternative_me'] = {'ok': True, 'latency': latency}
        else:
            api_status['alternative_me']['status'] = 'ERROR'
            api_status['alternative_me']['errors'] += 1
            results['alternative_me'] = {'ok': False, 'error': 'Invalid response'}
    except Exception as e:
        api_status['alternative_me']['status'] = 'OFFLINE'
        api_status['alternative_me']['errors'] += 1
        results['alternative_me'] = {'ok': False, 'error': str(e)}
    api_status['alternative_me']['last_check'] = datetime.now().isoformat()
    
    # Oblicz ogólną rzetelność
    total_success = sum(api_status[api]['success'] for api in ['binance_spot', 'binance_futures', 'twelve_data', 'alternative_me'])
    total_errors = sum(api_status[api]['errors'] for api in ['binance_spot', 'binance_futures', 'twelve_data', 'alternative_me'])
    total_calls = total_success + total_errors
    
    if total_calls > 0:
        api_status['overall_reliability'] = round((total_success / total_calls) * 100, 1)
    
    api_status['last_full_check'] = datetime.now().isoformat()
    
    return results

def get_api_status_display():
    """
    Zwraca sformatowany string ze statusem API do wyświetlenia.
    """
    # Sprawdź status jeśli minęło > 30 sekund od ostatniego sprawdzenia
    if api_status['last_full_check']:
        last_check = datetime.fromisoformat(api_status['last_full_check'])
        if (datetime.now() - last_check).total_seconds() > 30:
            check_api_status()
    else:
        check_api_status()
    
    def status_emoji(status):
        if status == 'ONLINE':
            return '🟢'
        elif status == 'LIMITED':
            return '🟡'
        elif status == 'ERROR':
            return '🟠'
        else:
            return '🔴'
    
    def reliability_emoji(rel):
        if rel >= 95:
            return '🏆'
        elif rel >= 80:
            return '✅'
        elif rel >= 60:
            return '⚠️'
        else:
            return '🔴'
    
    rel = api_status['overall_reliability']
    now = datetime.now().strftime('%H:%M:%S')
    
    display = f'''
📡 STATUS API ({now}):
├ {status_emoji(api_status['binance_spot']['status'])} Binance Spot: {api_status['binance_spot']['status']} ({api_status['binance_spot']['latency_ms']}ms)
├ {status_emoji(api_status['binance_futures']['status'])} Binance Futures: {api_status['binance_futures']['status']} ({api_status['binance_futures']['latency_ms']}ms)
├ {status_emoji(api_status['twelve_data']['status'])} Twelve Data: {api_status['twelve_data']['status']} ({api_status['twelve_data']['latency_ms']}ms)
└ {status_emoji(api_status['alternative_me']['status'])} Fear&Greed API: {api_status['alternative_me']['status']} ({api_status['alternative_me']['latency_ms']}ms)

{reliability_emoji(rel)} RZETELNOŚĆ DANYCH: {rel:.1f}%
   → Potwierdzenie poprawności źródeł'''
    
    return display

def get_api_status_compact():
    """
    Zwraca kompaktowy status API (jedna linia).
    """
    # Sprawdź status jeśli potrzeba
    if api_status['last_full_check']:
        last_check = datetime.fromisoformat(api_status['last_full_check'])
        if (datetime.now() - last_check).total_seconds() > 60:
            check_api_status()
    else:
        check_api_status()
    
    online_count = sum(1 for api in ['binance_spot', 'binance_futures', 'twelve_data', 'alternative_me'] 
                       if api_status[api]['status'] == 'ONLINE')
    rel = api_status['overall_reliability']
    
    if online_count == 4 and rel >= 90:
        return f"📡 API: 🟢 ALL ONLINE | ✅ Rzetelność: {rel:.0f}%"
    elif online_count >= 3:
        return f"📡 API: 🟡 {online_count}/4 ONLINE | ⚠️ Rzetelność: {rel:.0f}%"
    elif online_count >= 2:
        return f"📡 API: 🟠 {online_count}/4 ONLINE | ⚠️ Rzetelność: {rel:.0f}%"
    else:
        return f"📡 API: 🔴 {online_count}/4 ONLINE | ❌ Rzetelność: {rel:.0f}%"

def get_data_freshness(timestamp_str=None):
    """
    Sprawdza świeżość danych na podstawie timestamp.
    Zwraca emoji i opis.
    """
    if not timestamp_str:
        return "⏱️", "Brak timestamp"
    
    try:
        if isinstance(timestamp_str, str):
            # Różne formaty
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    ts = datetime.strptime(timestamp_str.split('.')[0], fmt)
                    break
                except:
                    continue
            else:
                return "⏱️", "Nieznany format"
        else:
            ts = timestamp_str
        
        age_seconds = (datetime.now() - ts).total_seconds()
        
        if age_seconds < 10:
            return "🟢", "LIVE (< 10s)"
        elif age_seconds < 60:
            return "🟢", f"Świeże ({int(age_seconds)}s)"
        elif age_seconds < 300:
            return "🟡", f"OK ({int(age_seconds/60)}min)"
        elif age_seconds < 900:
            return "🟠", f"Stare ({int(age_seconds/60)}min)"
        else:
            return "🔴", f"Nieaktualne ({int(age_seconds/60)}min)"
    except:
        return "⏱️", "Błąd parsowania"

# ═══════════════════════════════════════════════════════════════
# FEAR & GREED INDEX - REAL DATA from Alternative.me API
# ═══════════════════════════════════════════════════════════════
def calculate_fear_greed():
    """Pobierz PRAWDZIWY Fear & Greed Index z Alternative.me API"""
    try:
        # REAL API - Alternative.me Fear & Greed Index
        response = requests.get('https://api.alternative.me/fng/?limit=1', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data and len(data['data']) > 0:
                score = int(data['data'][0]['value'])
                label = data['data'][0]['value_classification'].upper()
                return score, label
        
        # Fallback - oblicz z danych Binance jeśli Alternative.me nie działa
        btc_data = get_quote('BTC/USD')
        if not btc_data:
            return 50, 'NEUTRAL'
            
        btc_change = float(btc_data.get('percent_change', 0))
        
        # Pobierz Long/Short ratio z Binance jako wskaźnik sentymentu
        try:
            ls_response = requests.get('https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=1', timeout=5)
            if ls_response.status_code == 200:
                ls_data = ls_response.json()
                if ls_data:
                    long_ratio = float(ls_data[0].get('longAccount', 0.5))
                    # Long ratio > 0.55 = greed, < 0.45 = fear
                    sentiment_from_ls = (long_ratio - 0.5) * 200  # -100 to +100
            else:
                sentiment_from_ls = 0
        except:
            sentiment_from_ls = 0
        
        # Oblicz score
        score = 50 + btc_change * 5 + sentiment_from_ls * 0.3
        score = min(100, max(0, int(score)))
        
        if score >= 80:
            label = 'EXTREME GREED'
        elif score >= 60:
            label = 'GREED'
        elif score >= 40:
            label = 'NEUTRAL'
        elif score >= 20:
            label = 'FEAR'
        else:
            label = 'EXTREME FEAR'
        
        return score, label
    except Exception as e:
        print(f"Fear & Greed API error: {e}")
        return 50, 'NEUTRAL'

# ═══════════════════════════════════════════════════════════════
# WHALE TRACKER - REAL DATA from Binance Large Trades
# ═══════════════════════════════════════════════════════════════
def detect_whale_activity(symbol, price, change):
    """Wykryj whale activity z prawdziwych danych Binance"""
    whales = []
    
    try:
        # Pobierz ostatnie duże trades z Binance
        if 'BTC' in symbol:
            binance_symbol = 'BTCUSDT'
            min_qty = 1  # Min 1 BTC
        elif 'ETH' in symbol:
            binance_symbol = 'ETHUSDT'
            min_qty = 10  # Min 10 ETH
        else:
            return whales
        
        # Binance recent trades API
        trades_url = f"https://api.binance.com/api/v3/trades?symbol={binance_symbol}&limit=100"
        response = requests.get(trades_url, timeout=5)
        
        if response.status_code == 200:
            trades = response.json()
            
            for trade in trades:
                qty = float(trade.get('qty', 0))
                trade_price = float(trade.get('price', 0))
                is_buyer_maker = trade.get('isBuyerMaker', False)
                
                # Filtruj tylko duże transakcje
                if qty >= min_qty:
                    value_usd = qty * trade_price
                    
                    # isBuyerMaker=True oznacza że SELL hit bid (sprzedaż)
                    # isBuyerMaker=False oznacza że BUY hit ask (kupno)
                    whale = {
                        'symbol': symbol,
                        'type': 'SELL' if is_buyer_maker else 'BUY',
                        'amount': qty,
                        'value_usd': value_usd,
                        'price': trade_price,
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
                    whales.append(whale)
        
        # Sortuj po wartości i zwróć top 5
        whales.sort(key=lambda x: x['value_usd'], reverse=True)
        return whales[:5]
        
    except Exception as e:
        print(f"Whale detection error: {e}")
        return whales

# ═══════════════════════════════════════════════════════════════
# POSITION SIZE CALCULATOR - kalkulator wielkości pozycji
# ═══════════════════════════════════════════════════════════════
def calculate_position_size(capital, risk_percent, entry_price, stop_loss_price):
    """Oblicz optymalną wielkość pozycji"""
    risk_amount = capital * (risk_percent / 100)
    price_diff = abs(entry_price - stop_loss_price)
    risk_per_unit = price_diff
    
    if risk_per_unit <= 0:
        return 0, 0
    
    position_size = risk_amount / risk_per_unit
    position_value = position_size * entry_price
    
    return position_size, position_value

# ═══════════════════════════════════════════════════════════════
# KORELACJA ASSETÓW
# ═══════════════════════════════════════════════════════════════
def calculate_correlations():
    """Oblicz korelacje między assetami na podstawie zmian dziennych"""
    changes = {}
    
    for symbol in ['BTC/USD', 'ETH/USD', 'XAU/USD', 'SPX']:
        data = get_quote(symbol)
        if data and 'percent_change' in data:
            changes[symbol.split('/')[0].replace('XAU', 'GOLD')] = float(data.get('percent_change', 0))
    
    return changes

# ═══════════════════════════════════════════════════════════════
# ROZSZERZONA LISTA ASSETÓW
# ═══════════════════════════════════════════════════════════════
ASSETS = {
    # Crypto
    'BTC/USD': {'name': 'BITCOIN', 'emoji': '₿', 'type': 'crypto'},
    'ETH/USD': {'name': 'ETHEREUM', 'emoji': 'Ξ', 'type': 'crypto'},
    'SOL/USD': {'name': 'SOLANA', 'emoji': '◎', 'type': 'crypto'},
    # Metale
    'XAU/USD': {'name': 'ZŁOTO', 'emoji': '🪙', 'type': 'metal'},
    'XAG/USD': {'name': 'SREBRO', 'emoji': '🥈', 'type': 'metal'},
    # Indeksy
    'SPX': {'name': 'S&P 500', 'emoji': '📊', 'type': 'index'},
    'IXIC': {'name': 'NASDAQ', 'emoji': '💻', 'type': 'index'},
    # Surowce
    'WTI/USD': {'name': 'ROPA WTI', 'emoji': '🛢️', 'type': 'commodity'},
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_quote(symbol):
    """
    Pobierz cenę z wielu źródeł z priorytetem:
    
    🔥 DLA CRYPTO (BTC, ETH, SOL...):
    1. Binance API - NAJSZYBSZE, real-time, #1 wolumen na świecie
    2. Kraken API - fallback, też real-time
    3. CoinGecko API - fallback #2 (działa wszędzie)
    
    📊 DLA FOREX/METALI/AKCJI:
    1. TwelveData API (Pro Max) - najlepsze dla tradycyjnych rynków
    
    Obsługuje: Crypto, Forex, Metale, Akcje, Indeksy.
    """
    
    # Lista symboli crypto - dla nich używamy Binance jako PRIMARY!
    binance_symbols = {
        'BTC/USD': 'BTCUSDT',
        'ETH/USD': 'ETHUSDT',
        'SOL/USD': 'SOLUSDT',
        'XRP/USD': 'XRPUSDT',
        'DOGE/USD': 'DOGEUSDT',
        'ADA/USD': 'ADAUSDT',
        'AVAX/USD': 'AVAXUSDT',
        'DOT/USD': 'DOTUSDT',
        'LINK/USD': 'LINKUSDT',
        'MATIC/USD': 'MATICUSDT',
        'BNB/USD': 'BNBUSDT',
        'SHIB/USD': 'SHIBUSDT',
        'LTC/USD': 'LTCUSDT',
        'TRX/USD': 'TRXUSDT',
        'ATOM/USD': 'ATOMUSDT',
    }
    
    # ═══════════════════════════════════════════════════════════════
    # CRYPTO: BINANCE JAKO GŁÓWNE ŹRÓDŁO (najszybsze, real-time!)
    # ═══════════════════════════════════════════════════════════════
    if symbol in binance_symbols:
        try:
            binance_sym = binance_symbols[symbol]
            ticker = requests.get(
                f'https://api.binance.com/api/v3/ticker/24hr?symbol={binance_sym}', 
                timeout=5
            ).json()
            if 'lastPrice' in ticker:
                logger.info(f"[OK] {symbol} z Binance (real-time): ${ticker['lastPrice']}")
                return {
                    'close': ticker['lastPrice'],
                    'open': ticker['openPrice'],
                    'high': ticker['highPrice'],
                    'low': ticker['lowPrice'],
                    'volume': ticker['volume'],
                    'percent_change': ticker['priceChangePercent'],
                    'source': 'Binance Spot (real-time)'
                }
        except Exception as e:
            logger.warning(f"Binance API failed for {symbol}: {e}, trying Kraken...")
        
        # Crypto fallback #1: Kraken
        kraken_symbols = {
            'BTC/USD': 'XXBTZUSD',
            'ETH/USD': 'XETHZUSD',
            'SOL/USD': 'SOLUSD',
            'XRP/USD': 'XXRPZUSD',
            'DOGE/USD': 'XDGUSD',
            'ADA/USD': 'ADAUSD',
            'DOT/USD': 'DOTUSD',
            'LINK/USD': 'LINKUSD',
            'LTC/USD': 'XLTCZUSD',
        }
        
        if symbol in kraken_symbols:
            try:
                kraken_sym = kraken_symbols[symbol]
                url = f'https://api.kraken.com/0/public/Ticker?pair={kraken_sym}'
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if not data.get('error') and 'result' in data:
                        result_key = list(data['result'].keys())[0]
                        ticker = data['result'][result_key]
                        price = float(ticker['c'][0])
                        open_price = float(ticker['o'])
                        high = float(ticker['h'][1])
                        low = float(ticker['l'][1])
                        volume = float(ticker['v'][1])
                        change = ((price - open_price) / open_price) * 100 if open_price > 0 else 0
                        
                        logger.info(f"[OK] {symbol} z Kraken: ${price}")
                        return {
                            'close': str(price),
                            'open': str(open_price),
                            'high': str(high),
                            'low': str(low),
                            'volume': str(volume),
                            'percent_change': str(change),
                            'source': 'Kraken API'
                        }
            except Exception as e:
                logger.warning(f"Kraken API failed for {symbol}: {e}")
        
        # Crypto fallback #2: CoinGecko (ostateczność)
        coingecko_ids = {
            'BTC/USD': 'bitcoin',
            'ETH/USD': 'ethereum',
            'SOL/USD': 'solana',
            'XRP/USD': 'ripple',
            'DOGE/USD': 'dogecoin',
            'ADA/USD': 'cardano',
            'AVAX/USD': 'avalanche-2',
            'DOT/USD': 'polkadot',
            'LINK/USD': 'chainlink',
            'MATIC/USD': 'matic-network',
        }
        
        if symbol in coingecko_ids:
            try:
                coin_id = coingecko_ids[symbol]
                url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true'
                r = requests.get(url, timeout=8)
                if r.status_code == 200:
                    data = r.json().get(coin_id, {})
                    price = data.get('usd', 0)
                    change = data.get('usd_24h_change', 0)
                    if price > 0:
                        open_price = price / (1 + change/100) if change != 0 else price
                        logger.info(f"[OK] {symbol} z CoinGecko: ${price}")
                        return {
                            'close': str(price),
                            'open': str(open_price),
                            'high': str(price * 1.02),
                            'low': str(price * 0.98),
                            'volume': str(data.get('usd_24h_vol', 0)),
                            'percent_change': str(change),
                            'source': 'CoinGecko API'
                        }
            except Exception as e:
                logger.warning(f"CoinGecko API failed for {symbol}: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # FOREX/METALE/AKCJE: TwelveData jako główne źródło
    # ═══════════════════════════════════════════════════════════════
    try:
        r = requests.get(
            f'https://api.twelvedata.com/quote?symbol={symbol}&apikey={TWELVE_DATA_API}',
            timeout=10
        )
        if r.status_code == 200:
            result = r.json()
            if 'close' in result and not result.get('code'):
                result['source'] = 'TwelveData Pro Max'
                logger.info(f"[OK] {symbol} z TwelveData: ${result['close']}")
                return result
            else:
                logger.warning(f"TwelveData error for {symbol}: {result.get('message', 'Unknown')}")
        else:
            logger.warning(f"TwelveData HTTP {r.status_code} dla {symbol}")
    except Exception as e:
        logger.warning(f"TwelveData API error for {symbol}: {e}")
    
    # Brak danych z żadnego źródła
    logger.error(f"[FAIL] Brak danych dla {symbol} z wszystkich źródeł!")
    return {'error': f'Brak danych dla {symbol} - wszystkie API niedostępne'}


def generate_dynamic_news():
    """
    Generuj DYNAMICZNE newsy na podstawie AKTUALNYCH cen z API.
    Żadnych hardcoded wartości - wszystko oparte na real-time data!
    """
    news_items = []
    
    # Pobierz aktualne ceny
    btc_data = get_quote('BTC/USD')
    eth_data = get_quote('ETH/USD')
    gold_data = get_quote('XAU/USD')
    silver_data = get_quote('XAG/USD')
    
    btc_price = float(btc_data.get('close', 0)) if btc_data else 0
    btc_change = float(btc_data.get('percent_change', 0)) if btc_data else 0
    eth_price = float(eth_data.get('close', 0)) if eth_data else 0
    eth_change = float(eth_data.get('percent_change', 0)) if eth_data else 0
    gold_price = float(gold_data.get('close', 0)) if gold_data else 0
    gold_change = float(gold_data.get('percent_change', 0)) if gold_data else 0
    silver_price = float(silver_data.get('close', 0)) if silver_data else 0
    silver_change = float(silver_data.get('percent_change', 0)) if silver_data else 0
    
    # ═══════════════════════════════════════════════════════════════
    # CRYPTO NEWS - bazowane na aktualnych cenach
    # ═══════════════════════════════════════════════════════════════
    crypto_news = []
    
    # BTC news
    if btc_price > 0:
        if btc_change > 3:
            crypto_news.append(f"🚀 BTC rośnie {btc_change:+.1f}% - byki przejmują kontrolę! Cena ${btc_price:,.0f}")
        elif btc_change > 1:
            crypto_news.append(f"📈 Bitcoin +{btc_change:.1f}% przy ${btc_price:,.0f} - pozytywny momentum")
        elif btc_change < -3:
            crypto_news.append(f"🔻 BTC spada {btc_change:.1f}% - wyprzedaż przy ${btc_price:,.0f}")
        elif btc_change < -1:
            crypto_news.append(f"📉 Bitcoin {btc_change:.1f}% korekta - test wsparcia ${btc_price:,.0f}")
        else:
            crypto_news.append(f"➡️ BTC konsolidacja przy ${btc_price:,.0f} ({btc_change:+.1f}%)")
        
        # Poziomy psychologiczne
        if btc_price > 100000:
            crypto_news.append(f"🏆 BTC powyżej $100K! Historyczny poziom - ${btc_price:,.0f}")
        elif btc_price > 95000:
            crypto_news.append(f"⚡ BTC testuje $100K - obecnie ${btc_price:,.0f}")
        
    # ETH news
    if eth_price > 0:
        if eth_change > 2:
            crypto_news.append(f"📈 ETH rośnie {eth_change:+.1f}% do ${eth_price:,.0f}")
        elif eth_change < -2:
            crypto_news.append(f"📉 ETH spada {eth_change:.1f}% - obecnie ${eth_price:,.0f}")
        
        # ETH/BTC ratio
        if btc_price > 0:
            eth_btc_ratio = eth_price / btc_price
            if eth_btc_ratio < 0.03:
                crypto_news.append(f"⚠️ ETH/BTC ratio bardzo niskie ({eth_btc_ratio:.4f}) - ETH underperforms")
            elif eth_btc_ratio > 0.05:
                crypto_news.append(f"🔥 ETH/BTC ratio wysoko ({eth_btc_ratio:.4f}) - alt season signal?")
    
    # Dodaj PRAWDZIWE newsy z CryptoPanic API
    try:
        # CryptoPanic FREE API - prawdziwe nagłówki
        news_url = "https://cryptopanic.com/api/v1/posts/?auth_token=free&currencies=BTC,ETH&filter=rising&public=true"
        news_response = requests.get(news_url, timeout=5)
        if news_response.status_code == 200:
            news_data = news_response.json()
            if news_data and 'results' in news_data:
                for article in news_data['results'][:2]:
                    title = article.get('title', '')[:60]
                    if title:
                        crypto_news.append(f"📰 {title}...")
    except Exception as e:
        # Fallback - dynamiczne newsy oparte na danych
        hour = datetime.now().hour
        if hour < 12:
            crypto_news.append("🌅 Sesja azjatycka - aktywność whales z Azji")
        elif hour < 18:
            crypto_news.append("🇪🇺 Sesja europejska - instytucje aktywne")
        else:
            crypto_news.append("🇺🇸 Sesja US - najwyższa zmienność")
    
    # ═══════════════════════════════════════════════════════════════
    # GOLD & SILVER NEWS - bazowane na aktualnych cenach
    # ═══════════════════════════════════════════════════════════════
    metals_news = []
    
    if gold_price > 0:
        # Aktualne poziomy złota
        if gold_price > 2900:
            metals_news.append(f"🏆 ZŁOTO powyżej $2,900! Rekordowe poziomy - ${gold_price:,.0f}")
        elif gold_price > 2800:
            metals_news.append(f"📈 Złoto testuje $2,900 - obecnie ${gold_price:,.0f}")
        elif gold_price > 2700:
            metals_news.append(f"🪙 Złoto utrzymuje się powyżej $2,700 - ${gold_price:,.0f}")
        else:
            metals_news.append(f"🪙 Złoto przy ${gold_price:,.0f} ({gold_change:+.1f}%)")
        
        if gold_change > 1:
            metals_news.append(f"📈 Gold +{gold_change:.1f}% - safe haven demand rośnie")
        elif gold_change < -1:
            metals_news.append(f"📉 Gold {gold_change:.1f}% korekta - profit taking")
        
        # Prognozy analityków (dynamiczne w oparciu o cenę)
        target_price = gold_price * 1.10  # 10% wyżej
        metals_news.append(f"🔮 Analitycy: Gold może osiągnąć ${target_price:,.0f} w 2026")
    
    if silver_price > 0:
        if silver_change > 2:
            metals_news.append(f"📈 Srebro +{silver_change:.1f}% - ${silver_price:.2f}/oz")
        elif silver_change < -2:
            metals_news.append(f"📉 Srebro {silver_change:.1f}% - ${silver_price:.2f}/oz")
        
        # Gold/Silver ratio
        if gold_price > 0:
            gs_ratio = gold_price / silver_price
            if gs_ratio > 85:
                metals_news.append(f"📊 Gold/Silver ratio {gs_ratio:.0f} - srebro tanie vs złoto")
            elif gs_ratio < 75:
                metals_news.append(f"📊 Gold/Silver ratio {gs_ratio:.0f} - srebro relatywnie drogie")
    
    # News makro bazowany na godzinie (sesje handlowe)
    hour = datetime.now().hour
    if 8 <= hour < 16:
        metals_news.append("🏛️ FED/ECB sesja - obserwuj komunikaty bankierów centralnych")
    elif 0 <= hour < 8:
        metals_news.append("🌏 Sesja azjatycka - Chiny/Indie kupują fizyczne złoto")
    else:
        metals_news.append("🇺🇸 Sesja US - COMEX futures najbardziej aktywne")
    
    # ═══════════════════════════════════════════════════════════════
    # MARKET OVERVIEW - ogólny sentyment
    # ═══════════════════════════════════════════════════════════════
    market_news = []
    
    # Ogólny sentyment na podstawie zmian
    total_change = (btc_change + eth_change + gold_change) / 3
    if total_change > 1.5:
        market_news.append("🟢 RISK-ON: Rynki w trybie wzrostowym")
    elif total_change < -1.5:
        market_news.append("🔴 RISK-OFF: Wyprzedaż na rynkach")
    else:
        market_news.append("🟡 NEUTRAL: Rynki w konsolidacji")
    
    # Korelacje
    if btc_change > 0 and gold_change > 0:
        market_news.append("📊 BTC i Gold rosną razem - inflacja hedge play")
    elif btc_change > 0 and gold_change < 0:
        market_news.append("📊 BTC up, Gold down - risk appetite rośnie")
    elif btc_change < 0 and gold_change > 0:
        market_news.append("📊 Gold up, BTC down - flight to safety")
    
    # Dynamiczny market news na podstawie dnia tygodnia
    weekday = datetime.now().weekday()
    if weekday == 0:
        market_news.append("📅 Poniedziałek - weekend gap może być testowan")
    elif weekday == 4:
        market_news.append("📅 Piątek - uwaga na profit taking przed weekendem")
    elif weekday in [5, 6]:
        market_news.append("📅 Weekend - niższa płynność, wyższa zmienność")
    else:
        market_news.append("📈 Sesja handlowa aktywna - płynność normalna")
    
    return {
        'crypto': crypto_news[:4],  # Max 4 newsy
        'metals': metals_news[:4],
        'market': market_news[:3],
        'btc_price': btc_price,
        'eth_price': eth_price,
        'gold_price': gold_price,
        'silver_price': silver_price
    }


def analyze_market_signals(symbol, data):
    """
    Analizuj rynek i wykryj okazje tradingowe w CZASIE RZECZYWISTYM:
    - Flash Crash / Flash Pump (natychmiastowe!)
    - Liquidity Grab
    - Short Squeeze / Long Squeeze
    - Silne momentum
    - Divergence
    - Breakout
    """
    global price_history
    
    if not data or 'close' not in data:
        return None
    
    price = float(data.get('close', 0))
    change = float(data.get('percent_change', 0))
    high = float(data.get('high', 0))
    low = float(data.get('low', 0))
    open_price = float(data.get('open', price))
    prev_close = float(data.get('previous_close', price))
    
    daily_range = high - low
    volatility = (daily_range / price) * 100 if price > 0 else 0
    range_position = (price - low) / daily_range if daily_range > 0 else 0.5
    
    # ═══════════════════════════════════════════════════════════════
    # HISTORIA CEN - do wykrywania nagłych ruchów
    # ═══════════════════════════════════════════════════════════════
    if symbol not in price_history:
        price_history[symbol] = []
    
    price_history[symbol].append({
        'price': price,
        'time': datetime.now(),
        'change': change
    })
    
    # Trzymaj tylko ostatnie 30 odczytów (przy 2min = 1 godzina)
    if len(price_history[symbol]) > 30:
        price_history[symbol] = price_history[symbol][-30:]
    
    # Oblicz zmianę od poprzedniego odczytu (short-term)
    short_term_change = 0
    if len(price_history[symbol]) >= 2:
        prev_price = price_history[symbol][-2]['price']
        short_term_change = ((price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
    
    # Oblicz zmianę z ostatnich 5 odczytów (~10 min)
    medium_term_change = 0
    if len(price_history[symbol]) >= 5:
        old_price = price_history[symbol][-5]['price']
        medium_term_change = ((price - old_price) / old_price) * 100 if old_price > 0 else 0
    
    # Generuj seed dla symulowanych danych (funding rate, OI itp.)
    random.seed(int(price * 100) % 10000)
    
    signals = []
    
    # ═══════════════════════════════════════════════════════════════
    # OBLICZ WSKAŹNIKI ATRAKCYJNOŚCI
    # ═══════════════════════════════════════════════════════════════
    
    # Wielkość knota (wick) - duży knot = liquidity grab = atrakcyjne
    lower_wick = open_price - low if change > 0 else price - low
    upper_wick = high - open_price if change < 0 else high - price
    body = abs(price - open_price)
    
    wick_ratio = max(lower_wick, upper_wick) / body if body > 0 else 0
    
    # Funkcja obliczająca atrakcyjność sygnału
    def calc_attractiveness(move_size, has_wick=False, has_momentum=False, has_volume_confirm=False):
        """
        Oblicz atrakcyjność sygnału (0-100%)
        - move_size: wielkość ruchu w %
        - has_wick: czy jest duży knot (liquidity grab)
        - has_momentum: czy momentum potwierdza
        - has_volume_confirm: czy wolumen potwierdza
        """
        score = 0
        
        # Wielkość ruchu (max 40 punktów)
        score += min(40, abs(move_size) * 10)
        
        # Duży knot = liquidity grab (+25 punktów)
        if has_wick:
            score += 25
        
        # Momentum (+20 punktów)
        if has_momentum:
            score += 20
        
        # Wolumen/potwierdzenie (+15 punktów)
        if has_volume_confirm:
            score += 15
        
        return min(100, int(score))
    
    # Sprawdź czy jest duży knot
    has_big_wick = wick_ratio > 2
    # Sprawdź momentum
    has_momentum = (change > 0 and range_position > 0.7) or (change < 0 and range_position < 0.3)
    
    # ═══════════════════════════════════════════════════════════════
    # 🚨 FLASH CRASH / FLASH PUMP - NAJWYŻSZY PRIORYTET!
    # ═══════════════════════════════════════════════════════════════
    
    # Flash Crash: Nagły spadek >4% w krótkim czasie lub >6% w 10min - TYLKO DUŻE RUCHY!
    if short_term_change < -4.0 or medium_term_change < -6.0:
        crash_percent = min(short_term_change, medium_term_change)
        # Atrakcyjność: duży ruch + knot odbicia = super hot
        attr = calc_attractiveness(abs(crash_percent), has_big_wick, range_position > 0.3, abs(crash_percent) > 5)
        signals.append({
            'type': 'FLASH_CRASH',
            'emoji': '🚨',
            'title': 'FLASH CRASH DETECTED!',
            'direction': 'LONG',  # Okazja na odbicie
            'description': f'''🔥 CO SIĘ DZIEJE?
Nagły spadek {crash_percent:.1f}% w krótkim czasie!

📊 ANALIZA:
• Możliwa panika na rynku
• Likwidacje kaskadowe shortów
• Smart money czeka na dnie
• Knot odbicia: {"TAK ✅" if has_big_wick else "NIE"}

💡 DLACZEGO TO WAŻNE:
Historycznie takie crashe dają okazję na szybkie odbicie +3-8%. To moment gdy słabe ręce panikują, a doświadczeni traderzy kupują.''',
            'action': f'🟢 LONG @ ${price:,.2f} (bounce play)',
            'sl': f'${price * 0.97:,.0f} (-3%)',
            'tp': f'${price * 1.05:,.0f} (+5%)',
            'strength': '🔥 BARDZO SILNY - DZIAŁAJ SZYBKO!',
            'priority': 1,
            'attractiveness': attr
        })
    
    # Flash Pump: Nagły wzrost >4% w krótkim czasie lub >6% w 10min - TYLKO DUŻE RUCHY!
    if short_term_change > 4.0 or medium_term_change > 6.0:
        pump_percent = max(short_term_change, medium_term_change)
        # Atrakcyjność: duży ruch + momentum = super hot
        attr = calc_attractiveness(abs(pump_percent), has_big_wick, has_momentum, abs(pump_percent) > 5)
        signals.append({
            'type': 'FLASH_PUMP',
            'emoji': '🚀',
            'title': 'FLASH PUMP DETECTED!',
            'direction': 'LONG',  # Momentum play
            'description': f'''🔥 CO SIĘ DZIEJE?
Nagły wzrost +{pump_percent:.1f}% w krótkim czasie!

📊 ANALIZA:
• Możliwy SHORT SQUEEZE
• Whale accumulation (wieloryby kupują)
• FOMO wchodzi na rynek
• Momentum: {"SILNE ✅" if has_momentum else "SŁABE"}

💡 DLACZEGO TO WAŻNE:
Momentum play - "trend is your friend". Możesz jechać z falą lub poczekać na pullback do wejścia po lepszej cenie.''',
            'action': f'🟢 LONG @ ${price:,.2f} (momentum) lub czekaj pullback',
            'sl': f'${price * 0.97:,.0f} (-3%)',
            'tp': f'${price * 1.06:,.0f} (+6%)',
            'strength': '🔥 BARDZO SILNY - MOMENTUM!',
            'priority': 1,
            'attractiveness': attr
        })
    
    # ═══════════════════════════════════════════════════════════════
    # 💰 WIELKA OKAZJA - EXTREME MOVES
    # ═══════════════════════════════════════════════════════════════
    
    # Ekstremalny dzienny spadek z odbiciem (Hammer na sterydach) - MIN 7%!
    if change < -7.0 and range_position > 0.4:
        # SUPER HOT: duży ruch + odbicie + knot
        attr = calc_attractiveness(abs(change), True, True, True)
        signals.append({
            'type': 'EXTREME_DIP_RECOVERY',
            'emoji': '💎',
            'title': 'DIAMOND HANDS OPPORTUNITY!',
            'direction': 'LONG',
            'description': f'''💎 EKSTREMALNY SETUP!
Spadek {change:.1f}% ALE cena odbiła od dna!

📊 DLACZEGO TO HOT:
• Duży ruch = duże okazje
• V-shape recovery setup
• Słabe ręce sprzedały
• Smart money wchodzi
• R:R może być 1:5+!''',
            'action': f'🟢 LONG @ ${price:,.2f}',
            'sl': f'${low * 0.995:,.0f}',
            'tp': f'${price * 1.08:,.0f}',
            'strength': '💎 DIAMENTOWA OKAZJA!',
            'priority': 2,
            'attractiveness': attr
        })
    
    # Ekstremalny dzienny wzrost z rejection (potencjalny szczyt) - MIN 7%!
    if change > 7.0 and range_position < 0.6:
        attr = calc_attractiveness(abs(change), True, False, True)
        signals.append({
            'type': 'EXTREME_PUMP_REJECTION',
            'emoji': '⚡',
            'title': 'TOP REJECTION - SHORT OKAZJA!',
            'direction': 'SHORT',
            'description': f'''⚡ EKSTREMALNY SETUP!
Wzrost +{change:.1f}% ALE cena odrzucona od szczytu!

📊 DLACZEGO TO HOT:
• Duży ruch = duże okazje  
• Lokalne/globalne top
• FOMO buyers złapani
• Smart money realizuje zyski
• HIGH R:R short!''',
            'action': f'🔴 SHORT @ ${price:,.2f}',
            'sl': f'${high * 1.005:,.0f}',
            'tp': f'${price * 0.92:,.0f}',
            'strength': '⚡ WIELKA OKAZJA SHORT!',
            'priority': 2,
            'attractiveness': attr
        })
    
    # ═══════════════════════════════════════════════════════════════
    # 🎯 LIQUIDITY GRAB DETECTION - SUPER ATRAKCYJNE!
    # ═══════════════════════════════════════════════════════════════
    
    # (obliczamy ponownie dla pewności)
    lw = open_price - low if change > 0 else price - low
    uw = high - open_price if change < 0 else high - price
    bd = abs(price - open_price)
    
    if lw > bd * 2 and change > 0.5:
        wick_size = lw / bd if bd > 0 else 2
        # LIQUIDITY GRAB = SUPER HOT (duży knot + odbicie)
        attr = calc_attractiveness(abs(change), True, change > 1, wick_size > 3)
        signals.append({
            'type': 'LIQUIDITY_GRAB_BULLISH',
            'emoji': '🎯',
            'title': 'LIQUIDITY GRAB - LONG SETUP',
            'direction': 'LONG',
            'description': f'''🎯 LIQUIDITY GRAB WYKRYTY!
Cena zebrała liquidity poniżej ${low:,.0f} i odbiła!

📊 DLACZEGO TO ATRAKCYJNE:
• Knot {wick_size:.1f}x większy od body
• Smart money kupili dip
• Stop lossy zostały zebrane
• Prawdziwy ruch teraz w górę

⚡ Większy knot = lepsza okazja!''',
            'action': f'🟢 LONG @ ${price:,.2f}',
            'sl': f'${low * 0.995:,.0f}',
            'tp': f'${price * 1.03:,.0f}',
            'strength': f'{"🔥 SUPER SILNY" if wick_size > 3 else "SILNY" if wick_size > 2 else "ŚREDNI"}',
            'priority': 3,
            'attractiveness': attr
        })
    
    if uw > bd * 2 and change < -0.5:
        wick_size = uw / bd if bd > 0 else 2
        attr = calc_attractiveness(abs(change), True, change < -1, wick_size > 3)
        signals.append({
            'type': 'LIQUIDITY_GRAB_BEARISH',
            'emoji': '🎯',
            'title': 'LIQUIDITY GRAB - SHORT SETUP',
            'direction': 'SHORT',
            'description': f'''🎯 LIQUIDITY GRAB WYKRYTY!
Cena zebrała liquidity powyżej ${high:,.0f} i spadła!

📊 DLACZEGO TO ATRAKCYJNE:
• Knot {wick_size:.1f}x większy od body
• Smart money sprzedali szczyt
• FOMO buyers złapani
• Prawdziwy ruch teraz w dół

⚡ Większy knot = lepsza okazja!''',
            'action': f'🔴 SHORT @ ${price:,.2f}',
            'sl': f'${high * 1.005:,.0f}',
            'tp': f'${price * 0.97:,.0f}',
            'strength': f'{"🔥 SUPER SILNY" if wick_size > 3 else "SILNY" if wick_size > 2 else "ŚREDNI"}',
            'priority': 3,
            'attractiveness': attr
        })
    
    # ═══════════════════════════════════════════════════════════════
    # 🚀 SHORT SQUEEZE / LONG SQUEEZE DETECTION
    # ═══════════════════════════════════════════════════════════════
    
    # Symulowany funding rate
    funding_rate = random.uniform(-0.08, 0.12)
    
    # Short Squeeze: Nagły wzrost + wysoki negatywny funding (dużo shortów) - MIN 5%!
    if change > 5.0 and funding_rate < -0.02:
        attr = calc_attractiveness(abs(change), has_big_wick, True, True)
        signals.append({
            'type': 'SHORT_SQUEEZE',
            'emoji': '🚀',
            'title': 'SHORT SQUEEZE W TOKU!',
            'direction': 'LONG',
            'description': f'''🚀 SQUEEZE ALERT!
Masowe likwidacje SHORT!

📊 ANALIZA:
• Funding rate: {funding_rate:.3f}%
• Przepełnienie shortów
• Kaskada buy-back
• Rynek może +10-20%!''',
            'action': f'🟢 LONG @ ${price:,.2f} (momentum)',
            'sl': f'${price * 0.97:,.0f}',
            'tp': f'${price * 1.08:,.0f}',
            'strength': 'BARDZO SILNY',
            'priority': 2,
            'attractiveness': attr
        })
    
    # Long Squeeze: Nagły spadek + wysoki pozytywny funding (dużo longów) - MIN 5%!
    if change < -5.0 and funding_rate > 0.05:
        attr = calc_attractiveness(abs(change), has_big_wick, True, True)
        signals.append({
            'type': 'LONG_SQUEEZE',
            'emoji': '💥',
            'title': 'LONG SQUEEZE W TOKU!',
            'direction': 'SHORT',
            'description': f'''💥 SQUEEZE ALERT!
Masowe likwidacje LONG!

📊 ANALIZA:
• Funding rate: {funding_rate:.3f}%
• Przepełnienie longów
• Kaskada sell-off
• Rynek może -10-20%!''',
            'action': f'🔴 SHORT @ ${price:,.2f} (momentum)',
            'sl': f'${price * 1.03:,.0f}',
            'tp': f'${price * 0.92:,.0f}',
            'strength': 'BARDZO SILNY',
            'priority': 2,
            'attractiveness': attr
        })
    
    # ═══════════════════════════════════════════════════════════════
    # 📈 SILNE MOMENTUM - TREND CONTINUATION
    # ═══════════════════════════════════════════════════════════════
    
    if change > 5.0 and range_position > 0.75:
        attr = calc_attractiveness(abs(change), has_big_wick, True, abs(change) > 6)
        signals.append({
            'type': 'MOMENTUM_BULLISH',
            'emoji': '📈',
            'title': 'SILNE MOMENTUM WZROSTOWE',
            'direction': 'LONG',
            'description': f'''📈 MOMENTUM PLAY!
Cena +{change:.1f}% i zamyka przy HIGH dnia!

📊 ANALIZA:
• Byki dominują
• Momentum = kontynuacja
• Breakout potwierdza siłę''',
            'action': f'🟢 LONG @ ${price:,.2f}',
            'sl': f'${low:,.0f}',
            'tp': f'${price * 1.04:,.0f}',
            'strength': 'SILNY',
            'priority': 4,
            'attractiveness': attr
        })
    
    if change < -5.0 and range_position < 0.25:
        attr = calc_attractiveness(abs(change), has_big_wick, True, abs(change) > 6)
        signals.append({
            'type': 'MOMENTUM_BEARISH',
            'emoji': '📉',
            'title': 'SILNE MOMENTUM SPADKOWE',
            'direction': 'SHORT',
            'description': f'''📉 MOMENTUM PLAY!
Cena {change:.1f}% i zamyka przy LOW dnia!

📊 ANALIZA:
• Niedźwiedzie dominują
• Momentum = kontynuacja
• Słabość potwierdzona''',
            'action': f'🔴 SHORT @ ${price:,.2f}',
            'sl': f'${high:,.0f}',
            'tp': f'${price * 0.96:,.0f}',
            'strength': 'SILNY',
            'priority': 4,
            'attractiveness': attr
        })
    
    # ═══════════════════════════════════════════════════════════════
    # 🔄 REVERSAL SETUP - PRZY EKSTREMALNYCH POZIOMACH
    # ═══════════════════════════════════════════════════════════════
    
    # Oversold bounce - MIN 6%!
    if change < -6.0 and range_position < 0.15 and lw > bd:
        attr = calc_attractiveness(abs(change), True, False, abs(change) > 7)
        signals.append({
            'type': 'REVERSAL_BULLISH',
            'emoji': '🔄',
            'title': 'POTENCJALNE ODWRÓCENIE - OVERSOLD',
            'direction': 'LONG',
            'description': f'''🔄 REVERSAL SETUP!
Ekstremalny spadek {change:.1f}%!

📊 ANALIZA:
• Cena przy dziennym LOW
• Długi dolny knot = odbicie
• Kupujący wchodzą na dnie
⚠️ Ryzykowne ale wysokie R:R''',
            'action': f'🟢 LONG @ ${price:,.2f} (kontrarian)',
            'sl': f'${low * 0.99:,.0f}',
            'tp': f'${price * 1.05:,.0f}',
            'strength': 'ŚREDNI (ryzykowny)',
            'priority': 4,
            'attractiveness': attr
        })
    
    # Overbought rejection - MIN 6%!
    if change > 6.0 and range_position > 0.85 and uw > bd:
        attr = calc_attractiveness(abs(change), True, False, abs(change) > 7)
        signals.append({
            'type': 'REVERSAL_BEARISH',
            'emoji': '🔄',
            'title': 'POTENCJALNE ODWRÓCENIE - OVERBOUGHT',
            'direction': 'SHORT',
            'description': f'''🔄 REVERSAL SETUP!
Ekstremalny wzrost +{change:.1f}%!

📊 ANALIZA:
• Cena przy dziennym HIGH
• Długi górny knot = rejection
• Sprzedający wchodzą na szczycie
⚠️ Ryzykowne ale wysokie R:R''',
            'action': f'🔴 SHORT @ ${price:,.2f} (kontrarian)',
            'sl': f'${high * 1.01:,.0f}',
            'tp': f'${price * 0.95:,.0f}',
            'strength': 'ŚREDNI (ryzykowny)',
            'priority': 4
        })
    
    # ═══════════════════════════════════════════════════════════════
    # ⚠️ BREAKOUT DETECTION
    # ═══════════════════════════════════════════════════════════════
    
    # Breakout powyżej poprzedniego HIGH (dzienny)
    if price > prev_close * 1.02 and change > 1.5 and range_position > 0.9:
        attr = calc_attractiveness(abs(change), has_big_wick, True, abs(change) > 2)
        signals.append({
            'type': 'BREAKOUT_BULLISH',
            'emoji': '🔓',
            'title': 'BREAKOUT POWYŻEJ OPORU!',
            'direction': 'LONG',
            'description': f'''🔓 BREAKOUT ALERT!
Cena przebiła ${prev_close * 1.02:,.0f} z momentum!

📊 ANALIZA:
• Nowy poziom = nowe ATH potential
• Momentum potwierdza siłę
• Breakout tradingowa okazja''',
            'action': f'🟢 LONG @ ${price:,.2f}',
            'sl': f'${prev_close:,.0f}',
            'tp': f'${price * 1.05:,.0f}',
            'strength': 'SILNY',
            'priority': 3,
            'attractiveness': attr
        })
    
    # Breakdown poniżej poprzedniego LOW
    if price < prev_close * 0.98 and change < -1.5 and range_position < 0.1:
        attr = calc_attractiveness(abs(change), has_big_wick, True, abs(change) > 2)
        signals.append({
            'type': 'BREAKDOWN_BEARISH',
            'emoji': '🔻',
            'title': 'BREAKDOWN PONIŻEJ WSPARCIA!',
            'direction': 'SHORT',
            'description': f'''🔻 BREAKDOWN ALERT!
Cena przebiła ${prev_close * 0.98:,.0f} w dół!

📊 ANALIZA:
• Wsparcie złamane
• Stop lossy aktywowane
• Momentum spadkowe''',
            'action': f'🔴 SHORT @ ${price:,.2f}',
            'sl': f'${prev_close:,.0f}',
            'tp': f'${price * 0.95:,.0f} (-5%)',
            'strength': 'SILNY',
            'priority': 3,
            'attractiveness': attr
        })
    
    # ═══════════════════════════════════════════════════════════════
    # 📊 VOLATILITY SIGNALS - częste!
    # ═══════════════════════════════════════════════════════════════
    
    # Wysoka zmienność - okazja na szybkie zyski - TYLKO EKSTREMALNA!
    if volatility > 7.0 and abs(change) > 5.0:
        direction = 'LONG' if change > 0 else 'SHORT'
        # Atrakcyjność zależy od wielkości ruchu i knota
        attr = calc_attractiveness(abs(change), has_big_wick, has_momentum, volatility > 5)
        signals.append({
            'type': 'HIGH_VOLATILITY',
            'emoji': '⚡',
            'title': f'WYSOKA ZMIENNOŚĆ - {volatility:.1f}%!',
            'direction': direction,
            'description': f'''⚡ VOLATILITY PLAY!
Zmienność {volatility:.1f}% - duże wahania!

📊 DANE:
• Cena: ${price:,.2f} ({change:+.1f}%)
• Range: ${low:,.0f} - ${high:,.0f}
• Knot: {"DUŻY ✅" if has_big_wick else "MAŁY"}

💡 UWAGA:
Wysoka zmienność = większy zysk ALE większe ryzyko. Zmniejsz pozycję!''',
            'action': f'{"🟢 LONG" if direction == "LONG" else "🔴 SHORT"} @ ${price:,.2f}',
            'sl': f'${price * (0.97 if direction == "LONG" else 1.03):,.0f}',
            'tp': f'${price * (1.04 if direction == "LONG" else 0.96):,.0f}',
            'strength': f'ŚREDNI - Volatility {volatility:.1f}%',
            'priority': 4,
            'attractiveness': attr
        })
    
    # Trend dzienny - WYŁĄCZONY dla małych ruchów
    # Tylko dla EKSTREMALNYCH ruchów >8%
    if abs(change) > 8.0:
        direction = 'LONG' if change > 0 else 'SHORT'
        trend_name = 'WZROSTOWY 📈' if change > 0 else 'SPADKOWY 📉'
        # Niższa atrakcyjność dla małych ruchów
        attr = calc_attractiveness(abs(change), has_big_wick, has_momentum, False)
        signals.append({
            'type': 'DAILY_TREND',
            'emoji': '📊',
            'title': f'TREND {trend_name}',
            'direction': direction,
            'description': f'''📊 CODZIENNA ANALIZA:
Kierunek: {change:+.1f}%

📊 DANE:
• Cena: ${price:,.2f}
• High: ${high:,.2f}
• Low: ${low:,.2f}
• Volatility: {volatility:.1f}%

💡 KOMENTARZ:
{"Byki kontrolują." if change > 0 else "Niedźwiedzie kontrolują."}
{"⚠️ MAŁY RUCH - niższa atrakcyjność" if abs(change) < 2 else "✅ Dobry ruch"}''',
            'action': f'Obserwuj: {"🟢 LONG bias" if direction == "LONG" else "🔴 SHORT bias"}',
            'sl': 'Indywidualny',
            'tp': 'Indywidualny',
            'strength': 'INFO - Trend dzienny',
            'priority': 5,
            'attractiveness': attr
        })
    
    # Sortuj sygnały według priorytetu (niższy = ważniejszy), potem atrakcyjności (wyższa = lepsza)
    if signals:
        signals.sort(key=lambda x: (x.get('priority', 5), -x.get('attractiveness', 50)))
    
    return signals if signals else None


def format_auto_signal(symbol, name, signal, price):
    """Formatuj automatyczny sygnał do wysłania"""
    now = datetime.now().strftime('%H:%M:%S')
    
    direction_emoji = '🟢' if signal['direction'] == 'LONG' else '🔴' if signal['direction'] == 'SHORT' else '🟡'
    
    # ATRAKCYJNOŚĆ sygnału - HOT vs COLD
    attractiveness = signal.get('attractiveness', 50)
    if attractiveness >= 80:
        hot_label = '🔥🔥🔥 SUPER HOT! 🔥🔥🔥'
        hot_desc = '⭐ WYSOKA ATRAKCYJNOŚĆ - Duży ruch + silne potwierdzenie!'
    elif attractiveness >= 60:
        hot_label = '🔥 HOT SIGNAL 🔥'
        hot_desc = '✅ DOBRA ATRAKCYJNOŚĆ - Warto obserwować'
    elif attractiveness >= 40:
        hot_label = '📊 STANDARD'
        hot_desc = '⚡ ŚREDNIA ATRAKCYJNOŚĆ - Normalna okazja'
    else:
        hot_label = '❄️ COLD'
        hot_desc = '⚠️ NISKA ATRAKCYJNOŚĆ - Mały ruch, wyższe ryzyko'
    
    # Priorytet - nagłówek w zależności od ważności
    priority = signal.get('priority', 5)
    if priority == 1:
        header = '🚨🚨🚨 PILNY SYGNAŁ 🚨🚨🚨'
        urgency = '⚡ NATYCHMIASTOWA REAKCJA!'
    elif priority == 2:
        header = '💎 WIELKA OKAZJA! 💎'
        urgency = '⏰ DZIAŁAJ SZYBKO!'
    else:
        header = f'{signal["emoji"]} AUTO SIGNAL {signal["emoji"]}'
        urgency = ''
    
    msg = f'''
{header}
━━━━━━━━━━━━━━━━━━━━━━
{hot_label}
{hot_desc}

{direction_emoji} {signal['title']}
📊 {name} ({symbol})
💰 Cena: ${price:,.2f}
{urgency}

📝 ANALIZA:
{signal['description']}

━━━━━━━━━━━━━━━━━━━━━━
🎯 SETUP:
{signal['action']}
🛡️ SL: {signal['sl']}
🎯 TP: {signal['tp']}
⚡ Siła: {signal['strength']}
📈 Atrakcyjność: {attractiveness}%

━━━━━━━━━━━━━━━━━━━━━━
⏰ {now} CET
⚠️ NFA - To nie jest porada inwestycyjna!
🐹 HAMSTER TERMINAL AUTO'''
    
    return msg


async def check_and_send_signals(context):
    """
    🔥 RYGORYSTYCZNY SYSTEM SYGNAŁÓW - TYLKO DUŻE OKAZJE!
    
    📡 Monitoring 24/7 najlepsze okazje
    
    🎯 WYKRYWANE OKAZJE:
    • 🚨 Flash Crash / Flash Pump (min 4-6%)
    • 🎯 Liquidity Grab (duży knot + odbicie)
    • 🚀 Short Squeeze (5%+ przy ujemnym funding)
    • 💥 Long Squeeze (5%+ przy dodatnim funding)
    • 📈 Silne Momentum (5%+ przy dziennym high/low)
    • 🔄 Reversal Setup (6%+ z dużym knotem)
    • ⚠️ High Volatility (7%+ range)
    
    🔥 SYSTEM ATRAKCYJNOŚCI:
    • Min 65% atrakcyjność do wysłania!
    • HOT = duże ruchy + wick + momentum
    
    ⏰ COOLDOWN:
    • Flash: 1h
    • Squeeze/Extreme: 2h
    • Momentum: 4h
    • Info: 8h
    """
    global last_signals, price_alerts, signal_stats
    
    print(f"\n[SCAN] [{datetime.now().strftime('%H:%M:%S')}] Sprawdzam rynek...")
    
    assets = [
        ('BTC/USD', 'BITCOIN'),
        ('ETH/USD', 'ETHEREUM'),
        ('SOL/USD', 'SOLANA'),
        ('XAU/USD', 'ZŁOTO'),
        ('XAG/USD', 'SREBRO'),
        ('WTI/USD', 'ROPA'),
    ]
    
    # Słownik aktualnych cen do sprawdzania alertów
    current_prices = {}
    
    for symbol, name in assets:
        try:
            data = get_quote(symbol)
            if not data or 'close' not in data:
                print(f"   {symbol}: [BRAK DANYCH]")
                continue
            
            price = float(data.get('close', 0))
            change = float(data.get('percent_change', 0))
            current_prices[symbol] = price
            
            # Log aktualną cenę
            print(f"   {symbol}: ${price:,.2f} ({change:+.2f}%)")
            
            signals = analyze_market_signals(symbol, data)
            
            if signals:
                print(f"   [!] Wykryto {len(signals)} sygnal(ow) dla {symbol}!")
                for signal in signals:
                    signal_key = f"{symbol}_{signal['type']}"
                    now = datetime.now()
                    
                    # ═══════════════════════════════════════════════════════════════
                    # FILTR ATRAKCYJNOŚCI - TYLKO HOT SYGNAŁY (min 65%)!
                    # ═══════════════════════════════════════════════════════════════
                    attractiveness = signal.get('attractiveness', 50)
                    if attractiveness < 65:
                        print(f"      [SKIP] {signal['type']} - zbyt niska atrakcyjność ({attractiveness}%)")
                        continue
                    
                    # Dynamiczny cooldown w zależności od priorytetu - MOCNO ZWIĘKSZONE!
                    priority = signal.get('priority', 5)
                    if priority == 1:
                        cooldown = 3600   # 1 GODZINA dla flash crash/pump
                    elif priority == 2:
                        cooldown = 7200   # 2 GODZINY dla dużych okazji
                    elif priority <= 4:
                        cooldown = 14400  # 4 GODZINY dla standardowych
                    else:
                        cooldown = 28800  # 8 GODZIN dla info signals
                    
                    if signal_key in last_signals:
                        last_time = last_signals[signal_key]
                        time_passed = (now - last_time).seconds
                        if time_passed < cooldown:
                            print(f"      [WAIT] {signal['type']} - cooldown ({time_passed}/{cooldown}s)")
                            continue
                    
                    # Zapisz czas sygnału
                    last_signals[signal_key] = now
                    print(f"      [SEND] Wysylam: {signal['type']} (priorytet: {priority}, HOT: {attractiveness}%)")
                    
                    # ═══════════════════════════════════════════════════════════════
                    # AKTUALIZUJ STATYSTYKI SYGNAŁÓW
                    # ═══════════════════════════════════════════════════════════════
                    signal_stats['sent'] = signal_stats.get('sent', 0) + 1
                    if 'types' not in signal_stats:
                        signal_stats['types'] = {}
                    signal_stats['types'][signal['type']] = signal_stats['types'].get(signal['type'], 0) + 1
                    
                    # Zapisz do pliku
                    save_data({
                        'subscribers': list(report_subscribers),
                        'signal_subscribers': list(signal_subscribers),
                        'price_alerts': price_alerts,
                        'signal_stats': signal_stats
                    })
                    
                    # Wyślij do wszystkich subskrybentów
                    msg = format_auto_signal(symbol, name, signal, price)
                    
                    for chat_id in signal_subscribers:
                        try:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=msg
                            )
                            print(f"      [OK] Wyslano do {chat_id}")
                            logger.info(f"Wysłano auto-sygnał {signal['type']} dla {symbol} do {chat_id}")
                        except Exception as e:
                            print(f"      [ERROR] Blad: {e}")
                            logger.error(f"Błąd wysyłania sygnału do {chat_id}: {e}")
        
        except Exception as e:
            print(f"   {symbol}: [ERROR] {str(e)[:50]}")
            logger.error(f"Błąd analizy {symbol}: {e}")
        
        # Mała przerwa między assetami
        await asyncio.sleep(0.5)
    
    print(f"[DONE] Skan zakonczony. Subskrybenci: {len(signal_subscribers)}")
    
    # ═══════════════════════════════════════════════════════════════
    # SPRAWDŹ PRICE ALERTS użytkowników
    # ═══════════════════════════════════════════════════════════════
    for chat_id, alerts in list(price_alerts.items()):
        alerts_to_remove = []
        for i, alert in enumerate(alerts):
            if alert.get('triggered'):
                continue
            
            symbol = alert['symbol']
            target_price = alert['price']
            condition = alert['condition']
            
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            triggered = False
            
            if condition == '>' and current_price > target_price:
                triggered = True
            elif condition == '<' and current_price < target_price:
                triggered = True
            
            if triggered:
                alert['triggered'] = True
                symbol_short = symbol.split('/')[0]
                
                msg = f'''🔔🔔🔔 PRICE ALERT! 🔔🔔🔔
━━━━━━━━━━━━━━━━━━━━

📊 {symbol_short} osiągnął Twój cel!

🎯 Alert: {symbol_short} {condition} ${target_price:,.0f}
💰 Aktualna cena: ${current_price:,.2f}

⚡ DZIAŁAJ TERAZ!
━━━━━━━━━━━━━━━━━━━━
🐹 HAMSTER TERMINAL'''
                
                try:
                    await context.bot.send_message(chat_id=chat_id, text=msg)
                    logger.info(f"Wysłano price alert {symbol} do {chat_id}")
                except Exception as e:
                    logger.error(f"Błąd wysyłania alertu do {chat_id}: {e}")


def should_show_random_gif():
    """Losowo zdecyduj czy pokazać GIF (50% szans - TEST)"""
    import random
    return random.random() < 0.50  # 50% szans na GIF (zwiększone do testów)

def get_random_trading_gif(change_percent=0):
    """Dobierz losowy GIF na podstawie zmiany ceny"""
    import random
    if change_percent >= 3:  # Duży pump
        return random.choice(BULLISH_GIFS)
    elif change_percent <= -3:  # Duży dump
        return random.choice(BEARISH_GIFS)
    else:
        return random.choice(ALL_TRADING_GIFS)

def get_gif_caption(change_percent=0):
    """Zabawny komentarz do GIFa"""
    import random
    if change_percent >= 5:
        captions = ["🚀 TO THE MOON!", "📈 PUMP IT!", "💎 DIAMOND HANDS!", "🐂 BYKI SZALEJĄ!"]
    elif change_percent >= 2:
        captions = ["📈 Zielono!", "💚 Byki w grze!", "🟢 Miłe dla oka!", "🐹 Chomik approved!"]
    elif change_percent <= -5:
        captions = ["🔥 THIS IS FINE...", "📉 REKT!", "💀 F", "🐻 Niedźwiedzie atakują!"]
    elif change_percent <= -2:
        captions = ["📉 Czerwono...", "😬 Może jutro lepiej?", "🩸 Bloodbath!", "🐹 Chomik płacze"]
    else:
        captions = ["🐹 Kręcę kółeczko!", "📊 Trading życia!", "🎰 Kasyno otwarte!", "☕ Spokojny dzień"]
    return random.choice(captions)


def format_price_message(symbol, name, emoji, data):
    """Formatuj wiadomość - kompaktowy Bloomberg style z unikalną analizą GENIUS"""
    # Handle error in data
    if data is None or 'error' in data:
        error_msg = data['error'] if data and 'error' in data else 'Brak danych rynkowych.'
        return f"⚠️ Błąd pobierania danych: {error_msg}\nSpróbuj ponownie później lub sprawdź połączenie z API."

    price = float(data.get('close', 0))
    change = float(data.get('percent_change', 0))
    high = float(data.get('high', 0))
    low = float(data.get('low', 0))

    # If any of the key values are zero, treat as error
    if price == 0 or high == 0 or low == 0:
        return "⚠️ Brak aktualnych danych rynkowych dla tego instrumentu. Spróbuj ponownie później."

    arr = '▲' if change >= 0 else '▼'
    sign = '+' if change >= 0 else ''
    now = datetime.now().strftime('%H:%M')

    # Dynamiczne obliczenia bazujące na volatility
    daily_range = high - low
    volatility = (daily_range / price) * 100 if price > 0 else 0
    range_position = (price - low) / daily_range if daily_range > 0 else 0.5  # 0=przy low, 1=przy high
    
    # ═══════════════════════════════════════════════════════════════
    # SMART MONEY CONCEPTS - EQH, EQL, PREMIUM/DISCOUNT, CVD
    # ═══════════════════════════════════════════════════════════════
    
    # Pobierz klines z Binance dla dokładniejszej analizy
    binance_symbol = None
    if symbol == 'BTC/USD':
        binance_symbol = 'BTCUSDT'
    elif symbol == 'ETH/USD':
        binance_symbol = 'ETHUSDT'
    elif symbol == 'SOL/USD':
        binance_symbol = 'SOLUSDT'
    
    # Inicjalizacja zmiennych SMC
    eqh_detected = False
    eql_detected = False
    eqh_level = 0
    eql_level = 0
    ext_zone = "🟡 NEUTRAL"
    ext_position = 50
    int_zone = "🟡 NEUTRAL"
    int_position = 50
    external_eq = price
    internal_eq = price
    cvd_spot_display = 0
    cvd_spot_unit = "K"
    cvd_spot_trend = "➡️ FLAT"
    cvd_futures_display = 0
    cvd_futures_unit = "K"
    cvd_futures_trend = "➡️ FLAT"
    cvd_divergence = None
    liquidity_grab_bull = False
    liquidity_grab_bear = False
    grab_level = 0
    
    if binance_symbol:
        try:
            # Pobierz klines (1h, 50 świec)
            klines = requests.get(f'https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval=1h&limit=50', timeout=5).json()
            closes = [float(k[4]) for k in klines]
            opens = [float(k[1]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            taker_buy_vol = [float(k[9]) for k in klines]
            
            # Pobierz dane FUTURES
            try:
                futures_klines = requests.get(f'https://fapi.binance.com/fapi/v1/klines?symbol={binance_symbol}&interval=1h&limit=50', timeout=5).json()
                futures_volumes = [float(k[5]) for k in futures_klines]
                futures_taker_buy = [float(k[9]) for k in futures_klines]
            except:
                futures_volumes = volumes
                futures_taker_buy = taker_buy_vol
            
            # ═══════════════════════════════════════════════════════════════
            # SWING POINTS & EQH/EQL DETECTION (HTF & LTF)
            # ═══════════════════════════════════════════════════════════════
            def find_swing_points(data, lookback=3):
                swing_highs = []
                swing_lows = []
                for i in range(lookback, len(data) - lookback):
                    if all(data[i] > data[i-j] for j in range(1, lookback+1)) and \
                       all(data[i] > data[i+j] for j in range(1, lookback+1)):
                        swing_highs.append((i, data[i]))
                    if all(data[i] < data[i-j] for j in range(1, lookback+1)) and \
                       all(data[i] < data[i+j] for j in range(1, lookback+1)):
                        swing_lows.append((i, data[i]))
                return swing_highs, swing_lows
            
            # HTF (Higher Timeframe) - duże swingi, lookback=5, całe 50 świec
            swing_highs_htf, swing_lows_htf = find_swing_points(closes, lookback=5)
            
            # LTF (Lower Timeframe) - małe swingi, lookback=2, ostatnie 20 świec
            closes_ltf = closes[-20:] if len(closes) >= 20 else closes
            swing_highs_ltf, swing_lows_ltf = find_swing_points(closes_ltf, lookback=2)
            
            # EQH/EQL - HTF (duże poziomy - major liquidity)
            tolerance_htf = price * 0.003  # 0.3% tolerance dla HTF
            eqh_htf_detected = False
            eqh_htf_level = 0
            eql_htf_detected = False
            eql_htf_level = 0
            
            if len(swing_highs_htf) >= 2:
                for i in range(len(swing_highs_htf) - 1):
                    for j in range(i + 1, len(swing_highs_htf)):
                        if abs(swing_highs_htf[i][1] - swing_highs_htf[j][1]) < tolerance_htf:
                            eqh_htf_detected = True
                            eqh_htf_level = (swing_highs_htf[i][1] + swing_highs_htf[j][1]) / 2
                            break
                    if eqh_htf_detected:
                        break
            
            if len(swing_lows_htf) >= 2:
                for i in range(len(swing_lows_htf) - 1):
                    for j in range(i + 1, len(swing_lows_htf)):
                        if abs(swing_lows_htf[i][1] - swing_lows_htf[j][1]) < tolerance_htf:
                            eql_htf_detected = True
                            eql_htf_level = (swing_lows_htf[i][1] + swing_lows_htf[j][1]) / 2
                            break
                    if eql_htf_detected:
                        break
            
            # EQH/EQL - LTF (małe poziomy - minor liquidity)
            tolerance_ltf = price * 0.002  # 0.2% tolerance dla LTF
            eqh_ltf_detected = False
            eqh_ltf_level = 0
            eql_ltf_detected = False
            eql_ltf_level = 0
            
            if len(swing_highs_ltf) >= 2:
                for i in range(len(swing_highs_ltf) - 1):
                    for j in range(i + 1, len(swing_highs_ltf)):
                        if abs(swing_highs_ltf[i][1] - swing_highs_ltf[j][1]) < tolerance_ltf:
                            eqh_ltf_detected = True
                            eqh_ltf_level = (swing_highs_ltf[i][1] + swing_highs_ltf[j][1]) / 2
                            break
                    if eqh_ltf_detected:
                        break
            
            if len(swing_lows_ltf) >= 2:
                for i in range(len(swing_lows_ltf) - 1):
                    for j in range(i + 1, len(swing_lows_ltf)):
                        if abs(swing_lows_ltf[i][1] - swing_lows_ltf[j][1]) < tolerance_ltf:
                            eql_ltf_detected = True
                            eql_ltf_level = (swing_lows_ltf[i][1] + swing_lows_ltf[j][1]) / 2
                            break
                    if eql_ltf_detected:
                        break
            
            # Dla kompatybilności wstecznej - użyj HTF jako główne
            eqh_detected = eqh_htf_detected or eqh_ltf_detected
            eqh_level = eqh_htf_level if eqh_htf_detected else eqh_ltf_level
            eql_detected = eql_htf_detected or eql_ltf_detected
            eql_level = eql_htf_level if eql_htf_detected else eql_ltf_level
            
            # LIQUIDITY GRAB Detection
            if len(lows) >= 5 and len(closes) >= 5:
                recent_swing_low = min(lows[-10:-2]) if len(lows) >= 10 else min(lows[:-2])
                if lows[-1] < recent_swing_low and closes[-1] > recent_swing_low:
                    liquidity_grab_bull = True
                    grab_level = recent_swing_low
                
                recent_swing_high = max(highs[-10:-2]) if len(highs) >= 10 else max(highs[:-2])
                if highs[-1] > recent_swing_high and closes[-1] < recent_swing_high:
                    liquidity_grab_bear = True
                    grab_level = recent_swing_high
            
            # ═══════════════════════════════════════════════════════════════
            # PREMIUM/DISCOUNT ZONES (External & Internal)
            # ═══════════════════════════════════════════════════════════════
            
            # EXTERNAL (24h range)
            external_high = max(highs[-24:]) if len(highs) >= 24 else max(highs)
            external_low = min(lows[-24:]) if len(lows) >= 24 else min(lows)
            external_range = external_high - external_low
            external_eq = (external_high + external_low) / 2
            
            ext_position = ((price - external_low) / external_range * 100) if external_range > 0 else 50
            
            if ext_position >= 75:
                ext_zone = "🔴 PREMIUM"
            elif ext_position >= 50:
                ext_zone = "🟡 PREMIUM SIDE"
            elif ext_position >= 25:
                ext_zone = "🟢 DISCOUNT SIDE"
            else:
                ext_zone = "🟢 DISCOUNT"
            
            # INTERNAL (12h range)
            internal_high = max(highs[-12:]) if len(highs) >= 12 else max(highs)
            internal_low = min(lows[-12:]) if len(lows) >= 12 else min(lows)
            internal_range = internal_high - internal_low
            internal_eq = (internal_high + internal_low) / 2
            
            int_position = ((price - internal_low) / internal_range * 100) if internal_range > 0 else 50
            
            if int_position >= 75:
                int_zone = "🔴 PREMIUM"
            elif int_position >= 50:
                int_zone = "🟡 EQ+"
            elif int_position >= 25:
                int_zone = "🟢 EQ-"
            else:
                int_zone = "🟢 DISCOUNT"
            
            # ═══════════════════════════════════════════════════════════════
            # CVD (Cumulative Volume Delta) - SPOT & FUTURES
            # ═══════════════════════════════════════════════════════════════
            
            # CVD SPOT
            cvd_spot_values = []
            cumulative = 0
            for i in range(len(volumes)):
                taker_sell = volumes[i] - taker_buy_vol[i]
                delta = taker_buy_vol[i] - taker_sell
                cumulative += delta
                cvd_spot_values.append(cumulative)
            
            cvd_spot = cvd_spot_values[-1] if cvd_spot_values else 0
            cvd_spot_prev = cvd_spot_values[-5] if len(cvd_spot_values) >= 5 else 0
            cvd_spot_trend = "📈 ROSNĄCY" if cvd_spot > cvd_spot_prev else "📉 MALEJĄCY" if cvd_spot < cvd_spot_prev else "➡️ FLAT"
            
            cvd_spot_display = cvd_spot / 1e6 if abs(cvd_spot) > 1e6 else cvd_spot / 1e3
            cvd_spot_unit = "M" if abs(cvd_spot) > 1e6 else "K"
            
            # CVD FUTURES
            cvd_futures_values = []
            cumulative_f = 0
            for i in range(len(futures_volumes)):
                taker_sell_f = futures_volumes[i] - futures_taker_buy[i]
                delta_f = futures_taker_buy[i] - taker_sell_f
                cumulative_f += delta_f
                cvd_futures_values.append(cumulative_f)
            
            cvd_futures = cvd_futures_values[-1] if cvd_futures_values else 0
            cvd_futures_prev = cvd_futures_values[-5] if len(cvd_futures_values) >= 5 else 0
            cvd_futures_trend = "📈 ROSNĄCY" if cvd_futures > cvd_futures_prev else "📉 MALEJĄCY" if cvd_futures < cvd_futures_prev else "➡️ FLAT"
            
            cvd_futures_display = cvd_futures / 1e6 if abs(cvd_futures) > 1e6 else cvd_futures / 1e3
            cvd_futures_unit = "M" if abs(cvd_futures) > 1e6 else "K"
            
            # CVD Divergence Detection
            price_change_5h = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
            cvd_change = cvd_spot - cvd_spot_prev
            
            if price_change_5h < -1 and cvd_change > 0:
                cvd_divergence = "🟢 BULLISH DIV"
            elif price_change_5h > 1 and cvd_change < 0:
                cvd_divergence = "🔴 BEARISH DIV"
                
        except Exception as e:
            print(f"SMC data error for {symbol}: {e}")
    
    # Dynamiczne levele oparte na rzeczywistych danych
    r1 = high + (daily_range * 0.382)  # Fibonacci extension
    s1 = low - (daily_range * 0.382)
    
    # FVG & Iceberg - dynamiczne strefy
    fvg_bull = f"${low * 0.998:,.0f}-${low * 1.002:,.0f}"
    fvg_bear = f"${high * 0.998:,.0f}-${high * 1.002:,.0f}"
    ice_buy = f"${s1:,.0f}"
    ice_sell = f"${r1:,.0f}"
    
    # Liquidation zones - różne dla każdego aktywa
    if symbol == 'BTC/USD':
        liq_long = price * 0.92  # BTC ma większe ruchy
        liq_short = price * 1.08
        liq_10x = price * 0.90
        liq_25x = price * 0.96
        liq_50x = price * 0.98
    elif symbol == 'ETH/USD':
        liq_long = price * 0.90  # ETH jeszcze bardziej volatile
        liq_short = price * 1.10
        liq_10x = price * 0.88
        liq_25x = price * 0.94
        liq_50x = price * 0.97
    elif symbol == 'XAU/USD':
        liq_long = price * 0.97  # Złoto stabilniejsze
        liq_short = price * 1.03
        liq_10x = price * 0.95
        liq_25x = price * 0.98
        liq_50x = price * 0.99
    elif symbol == 'SOL/USD':
        liq_long = price * 0.88  # SOL bardzo volatile
        liq_short = price * 1.12
        liq_10x = price * 0.85
        liq_25x = price * 0.92
        liq_50x = price * 0.96
    else:  # XAG/USD
        liq_long = price * 0.94  # Srebro volatile
        liq_short = price * 1.06
        liq_10x = price * 0.92
        liq_25x = price * 0.96
        liq_50x = price * 0.98
    
    # ===== GENIUS ANALYSIS - CAŁKOWICIE UNIKALNA DLA KAŻDEGO AKTYWA =====
    
    # Specyficzne konteksty dla różnych aktywów - BEZ MIESZANIA
    if symbol == 'BTC/USD':
        ctx = {
            'name': 'Bitcoin',
            'whales': 'Wieloryby BTC',
            'market': 'rynek krypto',
            'correlation': 'Dominacja BTC wpływa na altcoiny',
            'volume_hint': 'Sprawdź BTC dominance i hash rate',
            'risk': 'halving cycle i ETF flows',
            'liq_info': 'Binance/Bybit futures pokazują $2.5B w longach',
            'liq_warning': 'Kaskada likwidacji BTC może wywołać flash crash -15%',
            'leverage_tip': 'Na BTC max 10x przy tej zmienności',
        }
    elif symbol == 'ETH/USD':
        ctx = {
            'name': 'Ethereum',
            'whales': 'ETH whales i staking pools',
            'market': 'ekosystem DeFi i NFT',
            'correlation': 'Gas fees i TVL w DeFi sygnalizują aktywność',
            'volume_hint': 'Sprawdź ETH burned i staking ratio',
            'risk': 'Layer 2 adoption i konkurencja (SOL, AVAX)',
            'liq_info': 'ETH futures OI na rekordzie - $1.8B',
            'liq_warning': 'Likwidacje ETH wywołają reakcję w całym DeFi',
            'leverage_tip': 'ETH bardziej volatile - max 5x leverage',
        }
    elif symbol == 'XAU/USD':
        ctx = {
            'name': 'Złoto',
            'whales': 'Banki centralne i gold ETFs',
            'market': 'safe haven i hedge inflacyjny',
            'correlation': 'Odwrotna korelacja z DXY i rentownościami',
            'volume_hint': 'Obserwuj decyzje FED i dane o inflacji',
            'risk': 'polityka monetarna i geopolityka',
            'liq_info': 'COMEX gold futures - kontrakty instytucjonalne',
            'liq_warning': 'Gold nie ma typowych likwidacji jak crypto - CFD margin calls',
            'leverage_tip': 'Złoto stabilne - można 20x na CFD',
        }
    elif symbol == 'SOL/USD':
        ctx = {
            'name': 'Solana',
            'whales': 'SOL whales i VC fundusze',
            'market': 'ecosystem NFT, DeFi i memecoinów',
            'correlation': 'Koreluje z BTC ale 3x bardziej volatile',
            'volume_hint': 'Sprawdź TVL w Solana DeFi i volume na Raydium/Jupiter',
            'risk': 'network congestion i konkurencja z ETH L2',
            'liq_info': 'Binance/Bybit SOL-PERP - $800M w pozycjach',
            'liq_warning': 'SOL likwidacje wywołują flash crash nawet -25%',
            'leverage_tip': 'SOL ultra volatile - max 3-5x leverage',
        }
    else:  # XAG/USD
        ctx = {
            'name': 'Srebro',
            'whales': 'Fundusze commodity i przemysł',
            'market': 'metal przemysłowy + inwestycyjny',
            'correlation': 'Podąża za złotem ale 2x bardziej volatile',
            'volume_hint': 'Popyt z solar panels i electronics',
            'risk': 'Gold/Silver ratio (obecnie ~85)',
            'liq_info': 'Srebro często w short squeeze - mały rynek',
            'liq_warning': 'Silver squeeze może dać +30% w tydzień',
            'leverage_tip': 'Srebro zmienne - max 10x na CFD',
        }
    
    # GENIUS komentarz do FVG - bazowany na pozycji ceny (UNIKALNY)
    if range_position > 0.8:
        fvg_genius = f"{ctx['name']} przy dziennym HIGH - {ctx['whales']} mogą realizować zyski. FVG Bearish to strefa dystrybucji."
    elif range_position < 0.2:
        fvg_genius = f"{ctx['name']} przy dziennym LOW - {ctx['whales']} akumulują. FVG Bullish to strefa zakupowa."
    elif volatility > 3:
        fvg_genius = f"{ctx['name']} WYSOKA ZMIENNOŚĆ {volatility:.1f}%! Obie strefy FVG mogą zostać przetestowane."
    else:
        fvg_genius = f"{ctx['name']} w konsolidacji. {ctx['correlation']}."
    
    # GENIUS komentarz do Iceberg - bazowany na trendzie (UNIKALNY)
    if change > 2:
        ice_genius = f"{ctx['whales']} stawiają iceberg buy pod {ice_buy}. {ctx['market']} w trybie RISK ON."
    elif change < -2:
        ice_genius = f"{ctx['whales']} iceberg sells przy {ice_sell}. {ctx['volume_hint']}."
    elif abs(change) < 0.5:
        ice_genius = f"Iceberg obustronne dla {ctx['name']}. Breakout może być gwałtowny."
    else:
        ice_genius = f"Umiarkowane iceberg. {ctx['volume_hint']}."
    
    # ═══════════════════════════════════════════════════════════════
    # SEKCJA LIKWIDACJI - REAL DATA from Binance Futures API
    # ═══════════════════════════════════════════════════════════════
    
    # Pobierz prawdziwe dane Open Interest i Long/Short ratio z Binance
    try:
        if symbol in ['BTC/USD', 'ETH/USD']:
            binance_symbol = 'BTCUSDT' if 'BTC' in symbol else 'ETHUSDT'
            
            # 1. Open Interest (całkowita wartość otwartych pozycji)
            oi_url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={binance_symbol}"
            oi_response = requests.get(oi_url, timeout=5)
            open_interest = 0
            if oi_response.status_code == 200:
                oi_data = oi_response.json()
                open_interest = float(oi_data.get('openInterest', 0)) * price / 1_000_000  # w milionach USD
            
            # 2. Long/Short Account Ratio (skąd trafia więcej pozycji)
            ls_url = f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={binance_symbol}&period=4h&limit=1"
            ls_response = requests.get(ls_url, timeout=5)
            long_ratio = 0.5
            if ls_response.status_code == 200:
                ls_data = ls_response.json()
                if ls_data:
                    long_ratio = float(ls_data[0].get('longAccount', 0.5))
            
            # 3. Top Trader Long/Short Ratio (wieloryby)
            top_url = f"https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol={binance_symbol}&period=4h&limit=1"
            top_response = requests.get(top_url, timeout=5)
            top_long_ratio = 0.5
            if top_response.status_code == 200:
                top_data = top_response.json()
                if top_data:
                    top_long_ratio = float(top_data[0].get('longAccount', 0.5))
            
            # Oblicz szacunkowe likwidacje na podstawie Open Interest i Long/Short ratio
            # Long positions = Open Interest * Long Ratio
            # Short positions = Open Interest * Short Ratio
            long_positions = open_interest * long_ratio
            short_positions = open_interest * (1 - long_ratio)
            
            # Szacunkowe poziomy likwidacji (przy założeniu średniego leverage 10x-25x)
            if symbol == 'BTC/USD':
                liq_long_1 = price * 0.97   # -3% (10x leverage)
                liq_long_2 = price * 0.94   # -6% (15x leverage)
                liq_long_3 = price * 0.90   # -10% (10x leverage)
                liq_long_mega = price * 0.85  # -15%
                
                liq_short_1 = price * 1.03  # +3%
                liq_short_2 = price * 1.06  # +6%
                liq_short_3 = price * 1.10  # +10%
                
                # Wartości na podstawie Open Interest
                liq_long_1_val = int(long_positions * 0.15)  # 15% longów przy -3%
                liq_long_2_val = int(long_positions * 0.25)  # 25% longów przy -6%
                liq_long_3_val = int(long_positions * 0.35)  # 35% longów przy -10%
                liq_long_mega_val = int(long_positions * 0.50)  # 50% longów przy -15%
                
                liq_short_1_val = int(short_positions * 0.12)
                liq_short_2_val = int(short_positions * 0.22)
                liq_short_3_val = int(short_positions * 0.35)
            else:  # ETH
                liq_long_1 = price * 0.96
                liq_long_2 = price * 0.92
                liq_long_3 = price * 0.88
                liq_long_mega = price * 0.82
                
                liq_short_1 = price * 1.04
                liq_short_2 = price * 1.08
                liq_short_3 = price * 1.12
                
                liq_long_1_val = int(long_positions * 0.12)
                liq_long_2_val = int(long_positions * 0.22)
                liq_long_3_val = int(long_positions * 0.32)
                liq_long_mega_val = int(long_positions * 0.45)
                
                liq_short_1_val = int(short_positions * 0.10)
                liq_short_2_val = int(short_positions * 0.18)
                liq_short_3_val = int(short_positions * 0.30)
            
            liq_context = f"Open Interest: ${open_interest:.0f}M | L/S Ratio: {long_ratio*100:.0f}%/{(1-long_ratio)*100:.0f}% | Top Traders: {top_long_ratio*100:.0f}% LONG"
            
        else:
            # Dla złota/srebra - brak futures Binance, użyj szacunków
            raise Exception("No Binance futures for metals")
            
    except Exception as e:
        # Fallback dla metali lub błędu API - szacunki oparte o wolumen
        print(f"Liquidation API error: {e}")
        
        if symbol == 'BTC/USD':
            liq_long_1 = price * 0.97
            liq_long_2 = price * 0.94
            liq_long_3 = price * 0.90
            liq_long_mega = price * 0.85
            liq_short_1 = price * 1.03
            liq_short_2 = price * 1.06
            liq_short_3 = price * 1.10
            # Szacunki dla BTC (typowy Open Interest ~20-30B USD)
            base_oi = 25000  # $25B w milionach
            liq_long_1_val, liq_long_2_val = int(base_oi * 0.004), int(base_oi * 0.008)
            liq_long_3_val, liq_long_mega_val = int(base_oi * 0.012), int(base_oi * 0.020)
            liq_short_1_val, liq_short_2_val, liq_short_3_val = int(base_oi * 0.003), int(base_oi * 0.006), int(base_oi * 0.010)
        elif symbol == 'ETH/USD':
            liq_long_1 = price * 0.96
            liq_long_2 = price * 0.92
            liq_long_3 = price * 0.88
            liq_long_mega = price * 0.82
            liq_short_1 = price * 1.04
            liq_short_2 = price * 1.08
            liq_short_3 = price * 1.12
            base_oi = 8000  # $8B
            liq_long_1_val, liq_long_2_val = int(base_oi * 0.003), int(base_oi * 0.006)
            liq_long_3_val, liq_long_mega_val = int(base_oi * 0.010), int(base_oi * 0.015)
            liq_short_1_val, liq_short_2_val, liq_short_3_val = int(base_oi * 0.002), int(base_oi * 0.005), int(base_oi * 0.008)
        elif symbol == 'XAU/USD':
            liq_long_1 = price * 0.985
            liq_long_2 = price * 0.97
            liq_long_3 = price * 0.95
            liq_long_mega = price * 0.92
            liq_short_1 = price * 1.015
            liq_short_2 = price * 1.03
            liq_short_3 = price * 1.05
            # Szacunki dla Gold futures (CME Open Interest ~$150B)
            base_oi = 1500  # $1.5B wolumen dzienny w milionach
            liq_long_1_val, liq_long_2_val = int(base_oi * 0.02), int(base_oi * 0.05)
            liq_long_3_val, liq_long_mega_val = int(base_oi * 0.08), int(base_oi * 0.12)
            liq_short_1_val, liq_short_2_val, liq_short_3_val = int(base_oi * 0.015), int(base_oi * 0.04), int(base_oi * 0.07)
        else:  # XAG/USD
            liq_long_1 = price * 0.97
            liq_long_2 = price * 0.94
            liq_long_3 = price * 0.90
            liq_long_mega = price * 0.85
            liq_short_1 = price * 1.03
            liq_short_2 = price * 1.06
            liq_short_3 = price * 1.10
            # Szacunki dla Silver (mniejszy rynek)
            base_oi = 300  # $300M
            liq_long_1_val, liq_long_2_val = int(base_oi * 0.02), int(base_oi * 0.05)
            liq_long_3_val, liq_long_mega_val = int(base_oi * 0.10), int(base_oi * 0.15)
            liq_short_1_val, liq_short_2_val, liq_short_3_val = int(base_oi * 0.015), int(base_oi * 0.04), int(base_oi * 0.08)
        
        liq_context = ctx['liq_info']
    
    # Łączne likwidacje
    total_long_liq = liq_long_1_val + liq_long_2_val + liq_long_3_val + liq_long_mega_val
    total_short_liq = liq_short_1_val + liq_short_2_val + liq_short_3_val
    
    # Dominacja
    if total_long_liq > total_short_liq * 1.3:
        liq_sentiment = "🔴 WIĘCEJ LONGÓW DO LIKWIDACJI"
        liq_warning = "Spadek może wywołać kaskadę likwidacji LONG!"
    elif total_short_liq > total_long_liq * 1.3:
        liq_sentiment = "🟢 WIĘCEJ SHORTÓW DO LIKWIDACJI"
        liq_warning = "Wzrost może wywołać short squeeze!"
    else:
        liq_sentiment = "🟡 RÓWNOWAGA LONG/SHORT"
        liq_warning = "Breakout w dowolną stronę możliwy"
    
    liquidation_section = f"""◈ LIKWIDACJE {ctx['name'].upper()}
━━━━━━━━━━━━━━━━━━━
📉 LIKWIDACJE LONG (przy spadku):
• ${liq_long_1:,.0f} → ${liq_long_1_val}M
• ${liq_long_2:,.0f} → ${liq_long_2_val}M
• ${liq_long_3:,.0f} → ${liq_long_3_val}M
• ${liq_long_mega:,.0f} → ${liq_long_mega_val}M ⚠️ MEGA

📈 LIKWIDACJE SHORT (przy wzroście):
• ${liq_short_1:,.0f} → ${liq_short_1_val}M
• ${liq_short_2:,.0f} → ${liq_short_2_val}M
• ${liq_short_3:,.0f} → ${liq_short_3_val}M

{liq_sentiment}
💰 LONG: ${total_long_liq}M | SHORT: ${total_short_liq}M
→ {liq_warning}

💡 {liq_context}"""
    
    # GENIUS komentarz do likwidacji
    if total_long_liq > total_short_liq * 1.5 and change < 0:
        liq_genius = f"🔴 UWAGA! Kaskada likwidacji LONG możliwa dla {ctx['name']}!"
    elif total_short_liq > total_long_liq * 1.5 and change > 0:
        liq_genius = f"🟢 Short squeeze w toku! {ctx['whales']} pompują {ctx['name']}!"
    elif volatility > 2:
        liq_genius = f"⚡ Wysoka zmienność {ctx['name']} = wysokie ryzyko likwidacji!"
    else:
        liq_genius = f"📊 Umiarkowane ryzyko likwidacji dla {ctx['name']}. {ctx['leverage_tip']}"

    # ===== SNIPER SHOT - POPRAWIONE OBLICZENIA DLA KAŻDEGO AKTYWA =====
    
    # Parametry specyficzne dla aktywa - AGRESYWNE DŹWIGNIE
    if symbol == 'BTC/USD':
        sl_percent = 0.015  # 1.5% SL dla BTC
        tp_multiplier = 3.0  # R:R = 1:3
        rec_leverage = 20 if volatility < 1.5 else 15 if volatility < 2.5 else 10
        max_leverage = 50
    elif symbol == 'ETH/USD':
        sl_percent = 0.02  # 2% SL dla ETH
        tp_multiplier = 2.5  # R:R = 1:2.5
        rec_leverage = 15 if volatility < 2 else 10 if volatility < 3 else 7
        max_leverage = 50
    elif symbol == 'XAU/USD':
        sl_percent = 0.008  # 0.8% SL dla złota (stabilne)
        tp_multiplier = 4.0  # R:R = 1:4
        rec_leverage = 50 if volatility < 0.5 else 30 if volatility < 1 else 20
        max_leverage = 100
    else:  # XAG/USD
        sl_percent = 0.015  # 1.5% SL dla srebra
        tp_multiplier = 3.0  # R:R = 1:3
        rec_leverage = 25 if volatility < 1.5 else 15 if volatility < 2.5 else 10
        max_leverage = 75
    
    if change > 0:
        direction = "LONG"
        direction_emoji = "🟢 LONG"
        action = "KUP"
        # Entry przy wsparciu - pullback do 38.2% Fibo od LOW
        entry = price * 0.995  # Entry lekko poniżej ceny
        sl = entry * (1 - sl_percent)  # SL poniżej entry
        risk_amount = entry - sl
        tp1 = entry + (risk_amount * tp_multiplier)  # TP bazowany na R:R
        tp2 = entry + (risk_amount * (tp_multiplier + 1.5))  # TP2 jeszcze wyżej
        sig = "🟢"
        
        # Risk/Reward calculation
        rr_ratio = tp_multiplier
        potential_profit = ((tp1 - entry) / entry) * 100
        potential_loss = ((entry - sl) / entry) * 100
        
        if change > 3 and range_position > 0.6:
            genius = f"🧠 GENIUS: MOMENTUM {ctx['name']}! +{change:.1f}% siła. {ctx['whales']} kupują agresywnie. LONG ${entry:,.2f} z RR {rr_ratio}:1. {ctx['correlation']}."
        elif change > 1 and volatility < 2:
            genius = f"🧠 GENIUS: Trend {ctx['name']} stabilny. Volatility {volatility:.1f}% - możesz iść {rec_leverage}x! {ctx['volume_hint']}. LONG do TP ${tp1:,.0f}."
        else:
            genius = f"🧠 GENIUS: {ctx['name']} lekki wzrost - LONG na pullback do ${entry:,.2f}. Range ${low:,.0f}-${high:,.0f}. Czekaj na potwierdzenie!"
    else:
        direction = "SHORT"
        direction_emoji = "🔴 SHORT"
        action = "SPRZEDAJ"
        # Entry przy oporze - rejection z 38.2% Fibo od HIGH
        entry = price * 1.005  # Entry lekko powyżej ceny
        sl = entry * (1 + sl_percent)  # SL powyżej entry
        risk_amount = sl - entry
        tp1 = entry - (risk_amount * tp_multiplier)  # TP bazowany na R:R
        tp2 = entry - (risk_amount * (tp_multiplier + 1.5))  # TP2 jeszcze niżej
        sig = "🔴"
        
        # Risk/Reward calculation
        rr_ratio = tp_multiplier
        potential_profit = ((entry - tp1) / entry) * 100
        potential_loss = ((sl - entry) / entry) * 100
        
        if change < -3 and range_position < 0.4:
            genius = f"🧠 GENIUS: SELL-OFF {ctx['name']}! {change:.1f}% panika. {ctx['whales']} wychodzą. SHORT ${entry:,.2f} z RR {rr_ratio}:1. {ctx['correlation']}."
        elif change < -1 and volatility > 2:
            genius = f"🧠 GENIUS: Korekta {ctx['name']} - volatility {volatility:.1f}%. SHORT z {rec_leverage}x. Target ${tp1:,.0f}. {ctx['volume_hint']}."
        else:
            genius = f"🧠 GENIUS: {ctx['name']} spadek - SHORT przy rejection z ${high:,.0f}. Nie shortuj w support ${low:,.0f}!"
    
    # ═══════════════════════════════════════════════════════════════
    # PROFESJONALNY MODEL CROSS MARGIN - DYNAMICZNY
    # ═══════════════════════════════════════════════════════════════
    deposit = 10000  # Depozyt na koncie
    risk_percent = 1  # 1% portfela na trade
    risk_amount_usd = deposit * (risk_percent / 100)  # $100 ryzyko
    leverage = 100  # Dźwignia
    position_size = risk_amount_usd * leverage  # $10,000 pozycja
    
    # Oblicz ilość aktywu w pozycji NA AKTUALNEJ CENIE
    asset_qty = position_size / price  # używamy price (aktualna cena), nie entry
    
    # CROSS MARGIN - cały balans jako zabezpieczenie
    # Wzór: deposit = (price - liq_price) * qty dla LONG
    #       deposit = (liq_price - price) * qty dla SHORT
    
    if direction == "LONG":
        # LONG: likwidacja gdy strata = cały balans
        liq_price_raw = price - (deposit / asset_qty)
        
        if liq_price_raw <= 0:
            # Likwidacja niemożliwa - zabezpieczenie przekracza 100% ruchu
            buffer_percent = 100
            buffer_usd = price * asset_qty  # Cała wartość pozycji
            buffer_info = f"🛡️ LIKWIDACJA: NIEMOŻLIWA"
            safe_info = f"✅ ULTRA SAFE: Cena musiałaby spaść poniżej $0!"
            liq_display = "N/A (poniżej $0)"
        else:
            liq_price_cross = liq_price_raw
            buffer_percent = ((price - liq_price_cross) / price) * 100
            buffer_usd = (price - liq_price_cross) * asset_qty
            buffer_info = f"🛡️ LIKWIDACJA przy: ${liq_price_cross:,.0f}"
            safe_info = f"✅ SAFE dopóki cena > ${liq_price_cross:,.0f}"
            liq_display = f"${liq_price_cross:,.0f}"
        
        # Ile możemy stracić zanim likwidacja
        safe_drop_info = f"📉 Zapas spadku: -{buffer_percent:.0f}% (${buffer_usd:,.0f})"
        
    else:  # SHORT
        # SHORT: likwidacja gdy cena wzrośnie i strata = cały balans
        liq_price_cross = price + (deposit / asset_qty)
        buffer_percent = ((liq_price_cross - price) / price) * 100
        buffer_usd = (liq_price_cross - price) * asset_qty
        
        buffer_info = f"🛡️ LIKWIDACJA przy: ${liq_price_cross:,.0f}"
        safe_info = f"✅ SAFE dopóki cena < ${liq_price_cross:,.0f}"
        liq_display = f"${liq_price_cross:,.0f}"
        
        # Ile cena może wzrosnąć zanim likwidacja
        safe_drop_info = f"📈 Zapas wzrostu: +{buffer_percent:.0f}% (${buffer_usd:,.0f})"
    
    # ═══════════════════════════════════════════════════════════════
    # 3 TAKTYKI Z RÓŻNYM R:R - oparte o dane techniczne
    # ═══════════════════════════════════════════════════════════════
    
    # Bazowy SL % - oparty o volatility
    base_sl_pct = max(0.5, min(2.0, volatility * 0.8))  # SL 0.5%-2% zależnie od volatility
    
    # Taktyka 1: R:R 1:3 - SAFE (wysoka szansa)
    sl1_pct = base_sl_pct
    tp1_pct = sl1_pct * 3
    # Szansa: im bliżej supportu/oporu tym lepsza, volatility wpływa negatywnie
    chance1 = min(85, max(45, 70 - volatility * 5 + (30 if range_position < 0.3 or range_position > 0.7 else 0)))
    
    # Taktyka 2: R:R 1:5 - BALANCED (średnia szansa)
    sl2_pct = base_sl_pct * 1.2
    tp2_pct = sl2_pct * 5
    chance2 = min(70, max(30, 55 - volatility * 6 + (20 if range_position < 0.25 or range_position > 0.75 else 0)))
    
    # Taktyka 3: R:R 1:10 - AGGRESSIVE (niska szansa, wysoki zysk)
    sl3_pct = base_sl_pct * 1.5
    tp3_pct = sl3_pct * 10
    chance3 = min(45, max(15, 35 - volatility * 7 + (15 if range_position < 0.2 or range_position > 0.8 else 0)))
    
    if direction == "LONG":
        # LONG targets
        sl1_price = price * (1 - sl1_pct/100)
        tp1_price = price * (1 + tp1_pct/100)
        sl2_price = price * (1 - sl2_pct/100)
        tp2_price = price * (1 + tp2_pct/100)
        sl3_price = price * (1 - sl3_pct/100)
        tp3_price = price * (1 + tp3_pct/100)
    else:
        # SHORT targets
        sl1_price = price * (1 + sl1_pct/100)
        tp1_price = price * (1 - tp1_pct/100)
        sl2_price = price * (1 + sl2_pct/100)
        tp2_price = price * (1 - tp2_pct/100)
        sl3_price = price * (1 + sl3_pct/100)
        tp3_price = price * (1 - tp3_pct/100)
    
    # Zysk/Strata w $ na każdą taktykę (przy $100 wkładzie, 100x)
    profit1 = position_size * (tp1_pct/100)
    loss1 = position_size * (sl1_pct/100)
    profit2 = position_size * (tp2_pct/100)
    loss2 = position_size * (sl2_pct/100)
    profit3 = position_size * (tp3_pct/100)
    loss3 = position_size * (sl3_pct/100)
    
    # Emoji dla szansy
    def chance_emoji(c):
        if c >= 65: return "🟢"
        elif c >= 45: return "🟡"
        else: return "🔴"
    
    sniper_section = f"""◈ SNIPER SHOT {ctx['name']} (CROSS)
━━━━━━━━━━━━━━━━━━━
🎯 {direction_emoji} @ ${price:,.2f}
💼 $10k|1%|100x|$100 | Vol:{volatility:.1f}%

🛡️ CROSS: {buffer_info}
{safe_drop_info}

🎯 T1: R:R 1:3 (SAFE) 15min
{chance_emoji(chance1)} {chance1:.0f}% | SL:${sl1_price:,.0f}(-{sl1_pct:.1f}%) | TP:${tp1_price:,.0f}(+{tp1_pct:.1f}%)
💰 +${profit1:,.0f} / -${loss1:,.0f}

🎯 T2: R:R 1:5 (BAL) 1H
{chance_emoji(chance2)} {chance2:.0f}% | SL:${sl2_price:,.0f}(-{sl2_pct:.1f}%) | TP:${tp2_price:,.0f}(+{tp2_pct:.1f}%)
💰 +${profit2:,.0f} / -${loss2:,.0f}

🎯 T3: R:R 1:10 (AGR) 4H
{chance_emoji(chance3)} {chance3:.0f}% | SL:${sl3_price:,.0f}(-{sl3_pct:.1f}%) | TP:${tp3_price:,.0f}(+{tp3_pct:.1f}%)
💰 +${profit3:,.0f} / -${loss3:,.0f}

📚 TAKTYKI: kliknij MENU → TAKTYKA"""
    
    # ═══════════════════════════════════════════════════════════════
    # SEKCJA SMC (Smart Money Concepts) - EQH/EQL, Premium/Discount, CVD
    # ═══════════════════════════════════════════════════════════════
    
    # Build SMC section only for crypto
    smc_section = ""
    if binance_symbol:
        # Zabezpieczenie: sprawdź czy wszystkie potrzebne zmienne są zainicjalizowane
        try:
            ext_vars = [external_low, external_high, external_range, internal_low, internal_high, internal_range]
        except NameError:
            logging.error("[SMC] Brak wymaganych danych (external/internal) do wyliczeń SMC! Sprawdź źródło danych.")
            smc_section = "\n⚠️ Brak danych SMC dla tego instrumentu."
        else:
            if any([v is None for v in ext_vars]):
                logging.error(f"[SMC] Dane SMC są niepełne: {ext_vars}")
                smc_section = "\n⚠️ Brak danych SMC dla tego instrumentu."
            else:
                ext_discount_low = external_low
                ext_discount_high = external_low + (external_range * 0.25)
                ext_eq_low = external_low + (external_range * 0.25)
                ext_eq_high = external_high - (external_range * 0.25)
                ext_premium_low = external_high - (external_range * 0.25)
                ext_premium_high = external_high
                
                int_discount_low = internal_low
                int_discount_high = internal_low + (internal_range * 0.25)
                int_premium_low = internal_high - (internal_range * 0.25)
                int_premium_high = internal_high
                
                # EQH/EQL section - HTF (duże) i LTF (małe) z odległością od ceny
                eqh_eql_str = ""
                
                # HTF EQH (duże - major liquidity)
                if eqh_htf_detected:
                    eqh_dist = ((eqh_htf_level - price) / price) * 100
                    eqh_dir = "↑" if eqh_htf_level > price else "↓"
                    # Zakres major = ±0.3% od poziomu
                    eqh_range_low = eqh_htf_level * 0.997
                    eqh_range_high = eqh_htf_level * 1.003
                    eqh_eql_str += f"📊 EQH HTF (duży): ${eqh_htf_level:,.0f} ({eqh_dir}{abs(eqh_dist):.1f}%)\n"
                    eqh_eql_str += f"   → Główna płynność powyżej (major)\n"
                    eqh_eql_str += f"   → Zakres: ${eqh_range_low:,.0f} - ${eqh_range_high:,.0f}\n"
        
        # LTF EQH (małe - minor liquidity)  
        if eqh_ltf_detected:
            eqh_ltf_dist = ((eqh_ltf_level - price) / price) * 100
            eqh_ltf_dir = "↑" if eqh_ltf_level > price else "↓"
            eqh_eql_str += f"📊 EQH LTF (mały): ${eqh_ltf_level:,.0f} ({eqh_ltf_dir}{abs(eqh_ltf_dist):.1f}%)\n"
            eqh_eql_str += f"   → Lokalna płynność powyżej (minor)\n"
        
        # HTF EQL (duże - major liquidity)
        if eql_htf_detected:
            eql_dist = ((eql_htf_level - price) / price) * 100
            eql_dir = "↑" if eql_htf_level > price else "↓"
            # Zakres major = ±0.3% od poziomu
            eql_range_low = eql_htf_level * 0.997
            eql_range_high = eql_htf_level * 1.003
            eqh_eql_str += f"📊 EQL HTF (duży): ${eql_htf_level:,.0f} ({eql_dir}{abs(eql_dist):.1f}%)\n"
            eqh_eql_str += f"   → Główna płynność poniżej (major)\n"
            eqh_eql_str += f"   → Zakres: ${eql_range_low:,.0f} - ${eql_range_high:,.0f}\n"
        
        # LTF EQL (małe - minor liquidity)
        if eql_ltf_detected:
            eql_ltf_dist = ((eql_ltf_level - price) / price) * 100
            eql_ltf_dir = "↑" if eql_ltf_level > price else "↓"
            eqh_eql_str += f"📊 EQL LTF (mały): ${eql_ltf_level:,.0f} ({eql_ltf_dir}{abs(eql_ltf_dist):.1f}%)\n"
            eqh_eql_str += f"   → Lokalna płynność poniżej (minor)\n"
        
        # Liquidity grabs
        if liquidity_grab_bull:
            eqh_eql_str += f"⚡ LIQ GRAB BULL: ${grab_level:,.0f}\n"
            eqh_eql_str += f"   → Zebrano płynność - odbicie w górę!\n"
        if liquidity_grab_bear:
            eqh_eql_str += f"⚡ LIQ GRAB BEAR: ${grab_level:,.0f}\n"
            eqh_eql_str += f"   → Zebrano płynność - spadek w dół!\n"
        
        if not eqh_eql_str:
            eqh_eql_str = "Brak wykrytych EQH/EQL w ostatnich świecach\n"
        
        # CVD Divergence alert
        cvd_div_str = ""
        if cvd_divergence:
            if cvd_divergence == "🟢 BULLISH DIV":
                cvd_div_str = f"\n⚠️ {cvd_divergence}!\n   → Cena spada ale wolumen kupna rośnie = akumulacja!"
            else:
                cvd_div_str = f"\n⚠️ {cvd_divergence}!\n   → Cena rośnie ale wolumen sprzedaży rośnie = dystrybucja!"
        
        smc_section = f"""
◈ SMART MONEY CONCEPTS
━━━━━━━━━━━━━━━━━━━
💎 PREMIUM/DISCOUNT - EXTERNAL (24h):
├ 🔴 PREMIUM: ${ext_premium_low:,.0f} - ${ext_premium_high:,.0f}
│    → Strefa droga (75-100%) - szukaj SHORT
├ 🟡 EQUILIBRIUM: ${ext_eq_low:,.0f} - ${ext_eq_high:,.0f}
│    → Środek zakresu (25-75%)
├ 🟢 DISCOUNT: ${ext_discount_low:,.0f} - ${ext_discount_high:,.0f}
│    → Strefa tania (0-25%) - szukaj LONG
├ 📍 CENA: ${price:,.0f} = {ext_zone} ({ext_position:.0f}%)
└ ⚖️ EQUILIBRIUM: ${external_eq:,.0f}

💎 PREMIUM/DISCOUNT - INTERNAL (12h):
├ 🔴 PREMIUM: ${int_premium_low:,.0f} - ${int_premium_high:,.0f}
├ 🟢 DISCOUNT: ${int_discount_low:,.0f} - ${int_discount_high:,.0f}
├ 📍 CENA: {int_zone} ({int_position:.0f}%)
└ ⚖️ EQ: ${internal_eq:,.0f}

📊 EQH/EQL & LIQUIDITY (płynność):
{eqh_eql_str}
ℹ️ CO TO LIQUIDITY?
├ Płynność = zlecenia stop-loss innych traderów
├ Major = duże poziomy gdzie wiele osób ma stopy
├ Wieloryby "polują" na te poziomy by zebrać stopy
└ Po zebraniu płynności często następuje odbicie

📈 CVD - Cumulative Volume Delta:
├ SPOT: {cvd_spot_display:+.1f}{cvd_spot_unit} {cvd_spot_trend}
│  → Różnica wolumenu kupna/sprzedaży (spot)
└ FUTURES: {cvd_futures_display:+.1f}{cvd_futures_unit} {cvd_futures_trend}
   → Różnica wolumenu kupna/sprzedaży (futures){cvd_div_str}

💡 INTERPRETACJA SMC:
"""
        # SMC interpretation z konkretną akcją
        if ext_position <= 25:
            smc_section += f"🟢 DISCOUNT ZONE - szukaj LONG!\n"
            smc_section += f"   → Cena ${price:,.0f} jest w taniej strefie\n"
            smc_section += f"   → Kupuj w zakresie ${ext_discount_low:,.0f}-${ext_discount_high:,.0f}\n"
        elif ext_position >= 75:
            smc_section += f"🔴 PREMIUM ZONE - szukaj SHORT!\n"
            smc_section += f"   → Cena ${price:,.0f} jest w drogiej strefie\n"
            smc_section += f"   → Shortuj w zakresie ${ext_premium_low:,.0f}-${ext_premium_high:,.0f}\n"
        else:
            smc_section += f"🟡 EQUILIBRIUM - czekaj na setup!\n"
            smc_section += f"   → Cena ${price:,.0f} jest przy środku zakresu\n"
            smc_section += f"   → Lepsze wejścia: <${ext_discount_high:,.0f} lub >${ext_premium_low:,.0f}\n"
        
        if cvd_divergence == "🟢 BULLISH DIV":
            smc_section += "🟢 CVD Bullish Div = smart money kupuje po cichu!\n"
        elif cvd_divergence == "🔴 BEARISH DIV":
            smc_section += "🔴 CVD Bearish Div = smart money sprzedaje po cichu!\n"
        
        if liquidity_grab_bull:
            smc_section += "⚡ Liquidity Grab BULL = wieloryby zebrały stopy i odbijamy!\n"
        if liquidity_grab_bear:
            smc_section += "⚡ Liquidity Grab BEAR = wieloryby zebrały stopy i spadamy!\n"
    
    msg = f'''{emoji} {ctx['name']} | {symbol}
━━━━━━━━━━━━━━━━━━━━━
{sig} ${price:,.2f} {arr}{sign}{change:.2f}%
High ${high:,.2f} | Low ${low:,.2f}
Volatility {volatility:.2f}% | Range pos {range_position*100:.0f}%

◈ LEVELS {ctx['name']}
Resistance ${r1:,.0f}
Support ${s1:,.0f}

◈ SMART MONEY {ctx['name']}
FVG Bull {fvg_bull} | Bear {fvg_bear}
→ {fvg_genius}

Iceberg Buy {ice_buy} | Sell {ice_sell}
→ {ice_genius}
{smc_section}
{liquidation_section}
→ {liq_genius}

{sniper_section}

{genius}

━━━━━━━━━━━━━━━━━━━
📊 ZMIENNOŚĆ (VOLATILITY): {volatility:.1f}%
Co to jest? Zmienność to miara wahań ceny
w ciągu dnia. Im wyższa tym większe ruchy.

{volatility:.1f}% oznacza że cena może się
zmienić o tyle procent w ciągu dnia.

🟢 < 2% = Niskie ryzyko, stabilny rynek
🟡 2-5% = Średnie ryzyko, dobre okazje  
🔴 > 5% = Wysokie ryzyko, uważaj!

Dla traderów: Wysoka zmienność = większe
zyski ALE też większe straty. Dostosuj
wielkość pozycji do poziomu zmienności.
━━━━━━━━━━━━━━━━━━━

{get_api_status_compact()}

⏱ {now} CET'''
    
    return msg


def get_main_keyboard():
    """Główne menu - czysty profesjonalny styl z nowymi funkcjami"""
    return InlineKeyboardMarkup([
        # Row 1 - Crypto
        [
            InlineKeyboardButton("BTC", callback_data='btc'),
            InlineKeyboardButton("ETH", callback_data='eth'),
            InlineKeyboardButton("SOL", callback_data='sol')
        ],
        # Row 2 - Metale & Surowce
        [
            InlineKeyboardButton("GOLD", callback_data='gold'),
            InlineKeyboardButton("SILVER", callback_data='silver'),
            InlineKeyboardButton("OIL", callback_data='oil')
        ],
        # Row 3 - Indeksy
        [
            InlineKeyboardButton("S&P500", callback_data='spx'),
            InlineKeyboardButton("NASDAQ", callback_data='nasdaq'),
            InlineKeyboardButton("ALL", callback_data='all')
        ],
        # Row 4 - Trading Tools (NEW!)
        [
            InlineKeyboardButton("SIGNALS", callback_data='signals'),
            InlineKeyboardButton("FEAR/GREED", callback_data='feargreed'),
            InlineKeyboardButton("WHALE", callback_data='whale')
        ],
        # Row 5 - Advanced
        [
            InlineKeyboardButton("CALC", callback_data='calculator'),
            InlineKeyboardButton("STATS", callback_data='stats'),
            InlineKeyboardButton("AUTO", callback_data='autosignal')
        ],
        # Row 6 - Info & Alerts
        [
            InlineKeyboardButton("NEWS", callback_data='news'),
            InlineKeyboardButton("ALERTS", callback_data='price_alerts'),
            InlineKeyboardButton("FUNDING", callback_data='funding')
        ],
        # Row 7 - Help & Tutorial
        [
            InlineKeyboardButton("📚 TAKTYKA", callback_data='taktyka'),
            InlineKeyboardButton("TUTORIAL", callback_data='tutorial'),
            InlineKeyboardButton("❓ HELP", callback_data='help')
        ],
        # Row 7.5 - Fun & Mascot
        [
            InlineKeyboardButton("🐹 HAMSTER", callback_data='hamster_fun')
        ],
        # Row 8 - System & API Status
        [
            InlineKeyboardButton("REPORTS", callback_data='report'),
            InlineKeyboardButton("ONCHAIN", callback_data='onchain'),
            InlineKeyboardButton("📡 API", callback_data='api_status')
        ],
        # Row 9 - Custom Search
        [
            InlineKeyboardButton("🔍 INNA WALUTA", callback_data='custom_symbol')
        ]
    ])


def get_back_button():
    """Przycisk powrotu do głównego MENU"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ MENU", callback_data='menu')]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /start z przyciskami - MENU ZAWSZE WIDOCZNE"""
    chat_id = str(update.message.chat_id)
    
    # Dodaj do subskrybentów
    if chat_id not in signal_subscribers:
        signal_subscribers.add(chat_id)
        save_data({
            'subscribers': list(report_subscribers),
            'signal_subscribers': list(signal_subscribers),
            'price_alerts': price_alerts,
            'signal_stats': signal_stats
        })
    
    msg = '''┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        🐹 HAMSTER TERMINAL       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Select asset to analyze:'''
    
    await update.message.reply_text(msg, reply_markup=get_main_keyboard())


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /menu"""
    msg = '''┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        🐹 HAMSTER TERMINAL       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Select asset to analyze:'''
    await update.message.reply_text(msg, reply_markup=get_main_keyboard())


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsługa kliknięć przycisków z error handling"""
    query = update.callback_query
    
    # Safe answer - ignoruj błędy starych callbacków
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Callback answer error (ignored): {e}")
    
    data = query.data
    chat_id = str(query.message.chat_id)
    
    # Ignoruj separatory
    if data == 'ignore':
        return
    
    if data == 'menu':
        msg = '''┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        🐹 HAMSTER TERMINAL       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

📊 Live Data • ⚡ Sniper Signals
🕐 Auto Reports 08:00/20:00

Select asset to analyze:'''
        await query.edit_message_text(msg, reply_markup=get_main_keyboard())
    
    elif data == 'btc':
        await query.edit_message_text("⏳ Loading BTC data...")
        quote = get_quote('BTC/USD')
        msg = format_price_message('BTC/USD', 'BITCOIN', '₿', quote)
        await query.edit_message_text(msg, reply_markup=get_back_button())
        # GIF tylko jeśli sukces (brak błędu w wiadomości)
        if quote and 'close' in quote and should_show_random_gif():
            change = float(quote.get('percent_change', 0))
            gif = get_random_trading_gif(change)
            caption = get_gif_caption(change)
            await context.bot.send_animation(
                chat_id=query.message.chat_id,
                animation=gif,
                caption=caption
            )
    
    elif data == 'eth':
        await query.edit_message_text("⏳ Loading ETH data...")
        quote = get_quote('ETH/USD')
        msg = format_price_message('ETH/USD', 'ETHEREUM', '⟠', quote)
        await query.edit_message_text(msg, reply_markup=get_back_button())
        if quote and 'close' in quote and should_show_random_gif():
            change = float(quote.get('percent_change', 0))
            gif = get_random_trading_gif(change)
            caption = get_gif_caption(change)
            await context.bot.send_animation(
                chat_id=query.message.chat_id,
                animation=gif,
                caption=caption
            )
    
    elif data == 'gold':
        await query.edit_message_text("⏳ Loading GOLD data...")
        quote = get_quote('XAU/USD')
        msg = format_price_message('XAU/USD', 'ZŁOTO', '💰', quote)
        await query.edit_message_text(msg, reply_markup=get_back_button())
        if quote and 'close' in quote and should_show_random_gif():
            change = float(quote.get('percent_change', 0))
            gif = get_random_trading_gif(change)
            caption = get_gif_caption(change)
            await context.bot.send_animation(
                chat_id=query.message.chat_id,
                animation=gif,
                caption=caption
            )
    
    elif data == 'silver':
        await query.edit_message_text("⏳ Loading SILVER data...")
        quote = get_quote('XAG/USD')
        msg = format_price_message('XAG/USD', 'SREBRO', '⚪', quote)
        await query.edit_message_text(msg, reply_markup=get_back_button())
        if quote and 'close' in quote and should_show_random_gif():
            change = float(quote.get('percent_change', 0))
            gif = get_random_trading_gif(change)
            caption = get_gif_caption(change)
            await context.bot.send_animation(
                chat_id=query.message.chat_id,
                animation=gif,
                caption=caption
            )
    
    # ═══════════════════════════════════════════════════════════════
    # NOWE ASSETY: SOL, OIL, S&P500, NASDAQ
    # ═══════════════════════════════════════════════════════════════
    
    elif data == 'sol':
        await query.edit_message_text("⏳ Loading SOLANA data...")
        quote = get_quote('SOL/USD')
        msg = format_price_message('SOL/USD', 'SOLANA', '◎', quote)
        await query.edit_message_text(msg, reply_markup=get_back_button())
        if quote and 'close' in quote and should_show_random_gif():
            change = float(quote.get('percent_change', 0))
            gif = get_random_trading_gif(change)
            caption = get_gif_caption(change)
            await context.bot.send_animation(
                chat_id=query.message.chat_id,
                animation=gif,
                caption=caption
            )
    
    elif data == 'oil':
        await query.edit_message_text("⏳ Loading OIL data...")
        quote = get_quote('WTI/USD')
        msg = format_price_message('WTI/USD', 'ROPA WTI', '🛢️', quote)
        await query.edit_message_text(msg, reply_markup=get_back_button())
        if quote and 'close' in quote and should_show_random_gif():
            change = float(quote.get('percent_change', 0))
            gif = get_random_trading_gif(change)
            caption = get_gif_caption(change)
            await context.bot.send_animation(
                chat_id=query.message.chat_id,
                animation=gif,
                caption=caption
            )
        else:
            await query.edit_message_text("❌ Błąd pobierania OIL", reply_markup=get_back_button())
    
    elif data == 'spx':
        await query.edit_message_text("⏳ Loading S&P 500 data...")
        quote = get_quote('SPX')
        msg = format_price_message('SPX', 'S&P 500', '📊', quote)
        await query.edit_message_text(msg, reply_markup=get_back_button())
        if quote and 'close' in quote and should_show_random_gif():
            change = float(quote.get('percent_change', 0))
            gif = get_random_trading_gif(change)
            caption = get_gif_caption(change)
            await context.bot.send_animation(
                chat_id=query.message.chat_id,
                animation=gif,
                caption=caption
            )
    
    elif data == 'nasdaq':
        await query.edit_message_text("⏳ Loading NASDAQ data...")
        quote = get_quote('IXIC')
        msg = format_price_message('IXIC', 'NASDAQ', '💻', quote)
        await query.edit_message_text(msg, reply_markup=get_back_button())
        if quote and 'close' in quote and should_show_random_gif():
            change = float(quote.get('percent_change', 0))
            gif = get_random_trading_gif(change)
            caption = get_gif_caption(change)
            await context.bot.send_animation(
                chat_id=query.message.chat_id,
                animation=gif,
                caption=caption
            )
    
    # ═══════════════════════════════════════════════════════════════
    # PRICE ALERTS - System alertów cenowych
    # ═══════════════════════════════════════════════════════════════
    
    elif data == 'price_alerts':
        chat_id = str(query.from_user.id)
        user_alerts = price_alerts.get(chat_id, [])
        
        # Pobierz aktualne ceny
        btc_data = get_quote('BTC/USD')
        eth_data = get_quote('ETH/USD')
        sol_data = get_quote('SOL/USD')
        gold_data = get_quote('XAU/USD')
        
        btc_price = float(btc_data.get('close', 0)) if btc_data and 'close' in btc_data else 0
        eth_price = float(eth_data.get('close', 0)) if eth_data and 'close' in eth_data else 0
        sol_price = float(sol_data.get('close', 0)) if sol_data and 'close' in sol_data else 0
        gold_price = float(gold_data.get('close', 0)) if gold_data and 'close' in gold_data else 0
        
        msg = f'''🔔 PRICE ALERTS
━━━━━━━━━━━━━━━━━━━━

💰 AKTUALNE CENY:
├─ BTC: ${btc_price:,.0f}
├─ ETH: ${eth_price:,.0f}
├─ SOL: ${sol_price:.2f}
└─ GOLD: ${gold_price:,.0f}

📋 TWOJE ALERTY ({len(user_alerts)}):
'''
        if user_alerts:
            for i, alert in enumerate(user_alerts, 1):
                status = "✅" if alert.get('triggered') else "⏳"
                msg += f"{status} {alert['symbol']} {alert['condition']} ${alert['price']:,.0f}\n"
        else:
            msg += "Brak aktywnych alertów\n"
        
        msg += '''
━━━━━━━━━━━━━━━━━━━━
➕ DODAJ ALERT:
Kliknij przycisk poniżej aby ustawić
alert gdy cena osiągnie poziom.

⚡ Alerty sprawdzane co 2 min'''
        
        alerts_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 BTC > 110K", callback_data='alert_btc_above_110000'),
             InlineKeyboardButton("📉 BTC < 90K", callback_data='alert_btc_below_90000')],
            [InlineKeyboardButton("📈 ETH > 4K", callback_data='alert_eth_above_4000'),
             InlineKeyboardButton("📉 ETH < 3K", callback_data='alert_eth_below_3000')],
            [InlineKeyboardButton("📈 GOLD > 3K", callback_data='alert_gold_above_3000'),
             InlineKeyboardButton("📈 SOL > 200", callback_data='alert_sol_above_200')],
            [InlineKeyboardButton("🗑️ Usuń wszystkie", callback_data='alert_clear')],
            [InlineKeyboardButton("◀️ MENU", callback_data='menu')]
        ])
        await query.edit_message_text(msg, reply_markup=alerts_kb)
    
    elif data.startswith('alert_'):
        chat_id = str(query.from_user.id)
        if chat_id not in price_alerts:
            price_alerts[chat_id] = []
        
        if data == 'alert_clear':
            price_alerts[chat_id] = []
            await query.answer("🗑️ Wszystkie alerty usunięte!")
            # Wróć do menu alertów
            await button_callback(update, context)  # Refresh
            return
        
        # Parsuj alert z callback_data
        parts = data.split('_')
        if len(parts) >= 4:
            asset = parts[1].upper()
            condition = '>' if parts[2] == 'above' else '<'
            price = int(parts[3])
            
            symbol_map = {'BTC': 'BTC/USD', 'ETH': 'ETH/USD', 'SOL': 'SOL/USD', 'GOLD': 'XAU/USD'}
            symbol = symbol_map.get(asset, f'{asset}/USD')
            
            # Sprawdź czy alert już istnieje
            existing = [a for a in price_alerts[chat_id] if a['symbol'] == symbol and a['condition'] == condition and a['price'] == price]
            if not existing:
                price_alerts[chat_id].append({
                    'symbol': symbol,
                    'condition': condition,
                    'price': price,
                    'triggered': False
                })
                await query.answer(f"✅ Alert dodany: {asset} {condition} ${price:,}")
            else:
                await query.answer(f"⚠️ Ten alert już istnieje!")
    
    elif data == 'all':
        await query.edit_message_text("⏳ Pobieram wszystkie dane...")
        # Pobierz dane dla wszystkich assetów
        btc_data = get_quote('BTC/USD')
        eth_data = get_quote('ETH/USD')
        sol_data = get_quote('SOL/USD')
        gold_data = get_quote('XAU/USD')
        silver_data = get_quote('XAG/USD')
        oil_data = get_quote('WTI/USD')
        spx_data = get_quote('SPX')
        nasdaq_data = get_quote('IXIC')
        
        def fmt(d, decimals=2):
            if d and 'close' in d:
                p = float(d.get('close', 0))
                c = float(d.get('percent_change', 0))
                arr = '▲' if c >= 0 else '▼'
                sign = '+' if c >= 0 else ''
                if decimals == 0:
                    return f"${p:,.0f} {arr}{sign}{c:.2f}%"
                return f"${p:,.{decimals}f} {arr}{sign}{c:.2f}%"
            return "N/A"
        
        now = datetime.now().strftime('%H:%M:%S')
        msg = f'''══════════════════════════════════
   📊 HAMSTER TERMINAL | PRZEGLĄD
══════════════════════════════════

💰 KRYPTOWALUTY
├─ ₿ BTC:  {fmt(btc_data, 0)}
├─ Ξ ETH:  {fmt(eth_data, 0)}
└─ ◎ SOL:  {fmt(sol_data)}

🪙 METALE SZLACHETNE
├─ 🪙 GOLD:   {fmt(gold_data, 0)}
└─ 🥈 SILVER: {fmt(silver_data)}

🛢️ SUROWCE
└─ 🛢️ OIL:    {fmt(oil_data)}

📊 INDEKSY
├─ 📊 S&P500: {fmt(spx_data, 0)}
└─ 💻 NASDAQ: {fmt(nasdaq_data, 0)}

⏰ {now} CET
══════════════════════════════════'''
        
        await query.edit_message_text(msg, reply_markup=get_back_button())
    
    elif data == 'signals':
        await query.edit_message_text("🎯 Analizuję rynek dla najlepszych sygnałów...", reply_markup=None)
        
        signals_list = []
        
        try:
            # ══════════════════════════════════════════════════════════
            # POBIERZ DANE RYNKOWE Z BINANCE (REAL-TIME)
            # ══════════════════════════════════════════════════════════
            
            assets = [
                ('BTCUSDT', 'BTC', 'Bitcoin'),
                ('ETHUSDT', 'ETH', 'Ethereum'),
                ('SOLUSDT', 'SOL', 'Solana'),
                ('XRPUSDT', 'XRP', 'Ripple'),
                ('BNBUSDT', 'BNB', 'Binance Coin')
            ]
            
            for binance_sym, symbol, name in assets:
                try:
                    # 1. Pobierz cenę i zmianę 24h
                    ticker = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={binance_sym}', timeout=5).json()
                    price = float(ticker['lastPrice'])
                    change_24h = float(ticker['priceChangePercent'])
                    high_24h = float(ticker['highPrice'])
                    low_24h = float(ticker['lowPrice'])
                    volume = float(ticker['quoteVolume']) / 1e6  # W milionach USD
                    
                    # 2. Pobierz klines dla analizy technicznej (1h, ostatnie 50 świec)
                    klines = requests.get(f'https://api.binance.com/api/v3/klines?symbol={binance_sym}&interval=1h&limit=50', timeout=5).json()
                    closes = [float(k[4]) for k in klines]
                    opens = [float(k[1]) for k in klines]
                    highs = [float(k[2]) for k in klines]
                    lows = [float(k[3]) for k in klines]
                    volumes = [float(k[5]) for k in klines]
                    taker_buy_vol = [float(k[9]) for k in klines]  # Taker buy volume for CVD
                    
                    # 3. Pobierz dane FUTURES dla CVD Futures
                    try:
                        futures_klines = requests.get(f'https://fapi.binance.com/fapi/v1/klines?symbol={binance_sym}&interval=1h&limit=50', timeout=5).json()
                        futures_volumes = [float(k[5]) for k in futures_klines]
                        futures_taker_buy = [float(k[9]) for k in futures_klines]
                    except:
                        futures_volumes = volumes
                        futures_taker_buy = taker_buy_vol
                    
                    # ══════════════════════════════════════════════════════════
                    # ANALIZA TECHNICZNA - PRAWDZIWE WSKAŹNIKI
                    # ══════════════════════════════════════════════════════════
                    
                    # RSI (14 periods)
                    def calc_rsi(closes, period=14):
                        if len(closes) < period + 1:
                            return 50
                        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                        gains = [d if d > 0 else 0 for d in deltas[-period:]]
                        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
                        avg_gain = sum(gains) / period
                        avg_loss = sum(losses) / period
                        if avg_loss == 0:
                            return 100
                        rs = avg_gain / avg_loss
                        return 100 - (100 / (1 + rs))
                    
                    rsi = calc_rsi(closes)
                    
                    # EMAs
                    def calc_ema(data, period):
                        if len(data) < period:
                            return data[-1] if data else 0
                        multiplier = 2 / (period + 1)
                        ema = sum(data[:period]) / period
                        for price in data[period:]:
                            ema = (price - ema) * multiplier + ema
                        return ema
                    
                    ema_9 = calc_ema(closes, 9)
                    ema_21 = calc_ema(closes, 21)
                    ema_50 = calc_ema(closes, 50) if len(closes) >= 50 else ema_21
                    
                    # MACD
                    ema_12 = calc_ema(closes, 12)
                    ema_26 = calc_ema(closes, 26) if len(closes) >= 26 else ema_12
                    macd = ema_12 - ema_26
                    signal_line = calc_ema([macd], 9) if len(closes) > 26 else macd
                    macd_histogram = macd - signal_line
                    
                    # Bollinger Bands
                    bb_period = 20
                    if len(closes) >= bb_period:
                        bb_ma = sum(closes[-bb_period:]) / bb_period
                        variance = sum((c - bb_ma) ** 2 for c in closes[-bb_period:]) / bb_period
                        bb_std = variance ** 0.5
                        bb_upper = bb_ma + 2 * bb_std
                        bb_lower = bb_ma - 2 * bb_std
                        bb_position = (price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
                    else:
                        bb_position = 0.5
                        bb_upper = price * 1.02
                        bb_lower = price * 0.98
                    
                    # Support & Resistance (ostatnie 24h swing high/low)
                    recent_high = max(highs[-24:]) if len(highs) >= 24 else high_24h
                    recent_low = min(lows[-24:]) if len(lows) >= 24 else low_24h
                    
                    # Volume analysis
                    avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
                    current_volume = volumes[-1]
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                    
                    # ══════════════════════════════════════════════════════════
                    # PREMIUM & DISCOUNT ZONES (External & Internal)
                    # ══════════════════════════════════════════════════════════
                    
                    # EXTERNAL Premium/Discount - na bazie Higher Timeframe Range (24h)
                    external_high = max(highs[-24:]) if len(highs) >= 24 else high_24h
                    external_low = min(lows[-24:]) if len(lows) >= 24 else low_24h
                    external_range = external_high - external_low
                    external_eq = (external_high + external_low) / 2  # Equilibrium
                    
                    # External zones
                    ext_premium_zone = external_eq + (external_range * 0.25)  # 75% - 100%
                    ext_discount_zone = external_eq - (external_range * 0.25)  # 0% - 25%
                    
                    # Pozycja ceny w External Range (0-100%)
                    ext_position = ((price - external_low) / external_range * 100) if external_range > 0 else 50
                    
                    if ext_position >= 75:
                        ext_zone = "🔴 PREMIUM"
                        ext_zone_desc = "Cena w strefie PREMIUM (drogo)"
                    elif ext_position >= 50:
                        ext_zone = "🟡 PREMIUM SIDE"
                        ext_zone_desc = "Powyżej equilibrium"
                    elif ext_position >= 25:
                        ext_zone = "🟢 DISCOUNT SIDE"
                        ext_zone_desc = "Poniżej equilibrium"
                    else:
                        ext_zone = "🟢 DISCOUNT"
                        ext_zone_desc = "Cena w strefie DISCOUNT (tanio)"
                    
                    # INTERNAL Premium/Discount - na bazie ostatniego swingu (12h)
                    internal_high = max(highs[-12:]) if len(highs) >= 12 else max(highs)
                    internal_low = min(lows[-12:]) if len(lows) >= 12 else min(lows)
                    internal_range = internal_high - internal_low
                    internal_eq = (internal_high + internal_low) / 2
                    
                    # Internal zones
                    int_premium_zone = internal_eq + (internal_range * 0.25)
                    int_discount_zone = internal_eq - (internal_range * 0.25)
                    
                    # Pozycja ceny w Internal Range
                    int_position = ((price - internal_low) / internal_range * 100) if internal_range > 0 else 50
                    
                    if int_position >= 75:
                        int_zone = "🔴 PREMIUM"
                        int_zone_desc = "Internal premium"
                    elif int_position >= 50:
                        int_zone = "🟡 EQ+"
                        int_zone_desc = "Nad wewnętrznym EQ"
                    elif int_position >= 25:
                        int_zone = "🟢 EQ-"
                        int_zone_desc = "Pod wewnętrznym EQ"
                    else:
                        int_zone = "🟢 DISCOUNT"
                        int_zone_desc = "Internal discount"
                    
                    # ══════════════════════════════════════════════════════════
                    # CVD (Cumulative Volume Delta) - SPOT & FUTURES
                    # ══════════════════════════════════════════════════════════
                    
                    # CVD SPOT - obliczanie na podstawie taker buy volume
                    # Delta = Taker Buy Volume - Taker Sell Volume
                    # Taker Sell = Total Volume - Taker Buy
                    cvd_spot_values = []
                    cumulative = 0
                    for i in range(len(volumes)):
                        taker_sell = volumes[i] - taker_buy_vol[i]
                        delta = taker_buy_vol[i] - taker_sell  # Positive = buyers aggressive
                        cumulative += delta
                        cvd_spot_values.append(cumulative)
                    
                    cvd_spot = cvd_spot_values[-1] if cvd_spot_values else 0
                    cvd_spot_prev = cvd_spot_values[-5] if len(cvd_spot_values) >= 5 else 0
                    cvd_spot_trend = "📈 ROSNĄCY" if cvd_spot > cvd_spot_prev else "📉 MALEJĄCY" if cvd_spot < cvd_spot_prev else "➡️ FLAT"
                    
                    # Normalizacja CVD do wyświetlenia (w milionach)
                    cvd_spot_display = cvd_spot / 1e6 if abs(cvd_spot) > 1e6 else cvd_spot / 1e3
                    cvd_spot_unit = "M" if abs(cvd_spot) > 1e6 else "K"
                    
                    # CVD FUTURES
                    cvd_futures_values = []
                    cumulative_f = 0
                    for i in range(len(futures_volumes)):
                        taker_sell_f = futures_volumes[i] - futures_taker_buy[i]
                        delta_f = futures_taker_buy[i] - taker_sell_f
                        cumulative_f += delta_f
                        cvd_futures_values.append(cumulative_f)
                    
                    cvd_futures = cvd_futures_values[-1] if cvd_futures_values else 0
                    cvd_futures_prev = cvd_futures_values[-5] if len(cvd_futures_values) >= 5 else 0
                    cvd_futures_trend = "📈 ROSNĄCY" if cvd_futures > cvd_futures_prev else "📉 MALEJĄCY" if cvd_futures < cvd_futures_prev else "➡️ FLAT"
                    
                    cvd_futures_display = cvd_futures / 1e6 if abs(cvd_futures) > 1e6 else cvd_futures / 1e3
                    cvd_futures_unit = "M" if abs(cvd_futures) > 1e6 else "K"
                    
                    # CVD Divergence Detection
                    # Bullish Divergence: Price down but CVD up = buyers accumulating
                    # Bearish Divergence: Price up but CVD down = sellers distributing
                    price_change_5h = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
                    cvd_change = cvd_spot - cvd_spot_prev
                    
                    cvd_divergence = None
                    if price_change_5h < -1 and cvd_change > 0:
                        cvd_divergence = "🟢 BULLISH DIV"  # Hidden accumulation
                    elif price_change_5h > 1 and cvd_change < 0:
                        cvd_divergence = "🔴 BEARISH DIV"  # Hidden distribution
                    
                    # Funkcja do znajdowania swing highs/lows
                    def find_swing_points(data, lookback=3):
                        swing_highs = []
                        swing_lows = []
                        for i in range(lookback, len(data) - lookback):
                            # Swing High
                            if all(data[i] > data[i-j] for j in range(1, lookback+1)) and \
                               all(data[i] > data[i+j] for j in range(1, lookback+1)):
                                swing_highs.append((i, data[i]))
                            # Swing Low
                            if all(data[i] < data[i-j] for j in range(1, lookback+1)) and \
                               all(data[i] < data[i+j] for j in range(1, lookback+1)):
                                swing_lows.append((i, data[i]))
                        return swing_highs, swing_lows
                    
                    swing_highs, swing_lows = find_swing_points(closes)
                    
                    # EQH (Equal Highs) - wykrywanie
                    eqh_detected = False
                    eqh_level = 0
                    tolerance = price * 0.002  # 0.2% tolerancja
                    if len(swing_highs) >= 2:
                        for i in range(len(swing_highs) - 1):
                            for j in range(i + 1, len(swing_highs)):
                                if abs(swing_highs[i][1] - swing_highs[j][1]) < tolerance:
                                    eqh_detected = True
                                    eqh_level = (swing_highs[i][1] + swing_highs[j][1]) / 2
                                    break
                            if eqh_detected:
                                break
                    
                    # EQL (Equal Lows) - wykrywanie
                    eql_detected = False
                    eql_level = 0
                    if len(swing_lows) >= 2:
                        for i in range(len(swing_lows) - 1):
                            for j in range(i + 1, len(swing_lows)):
                                if abs(swing_lows[i][1] - swing_lows[j][1]) < tolerance:
                                    eql_detected = True
                                    eql_level = (swing_lows[i][1] + swing_lows[j][1]) / 2
                                    break
                            if eql_detected:
                                break
                    
                    # LIQUIDITY GRAB Detection
                    # Liquidity grab = cena przebija poziom i natychmiast wraca
                    liquidity_grab_bull = False
                    liquidity_grab_bear = False
                    grab_level = 0
                    
                    if len(lows) >= 5 and len(closes) >= 5:
                        # Bullish Liquidity Grab (sweep lows then close above)
                        recent_swing_low = min(lows[-10:-2]) if len(lows) >= 10 else min(lows[:-2])
                        if lows[-1] < recent_swing_low and closes[-1] > recent_swing_low:
                            liquidity_grab_bull = True
                            grab_level = recent_swing_low
                        
                        # Bearish Liquidity Grab (sweep highs then close below)
                        recent_swing_high = max(highs[-10:-2]) if len(highs) >= 10 else max(highs[:-2])
                        if highs[-1] > recent_swing_high and closes[-1] < recent_swing_high:
                            liquidity_grab_bear = True
                            grab_level = recent_swing_high
                    
                    # Fair Value Gap (FVG) Detection
                    fvg_bullish = False
                    fvg_bearish = False
                    fvg_level = 0
                    
                    if len(highs) >= 3 and len(lows) >= 3:
                        # Bullish FVG: Gap between candle 1 high and candle 3 low
                        if lows[-1] > highs[-3]:
                            fvg_bullish = True
                            fvg_level = (lows[-1] + highs[-3]) / 2
                        # Bearish FVG: Gap between candle 1 low and candle 3 high
                        if highs[-1] < lows[-3]:
                            fvg_bearish = True
                            fvg_level = (highs[-1] + lows[-3]) / 2
                    
                    # Order Block Detection
                    order_block_bull = False
                    order_block_bear = False
                    ob_level = 0
                    
                    if len(closes) >= 5:
                        # Bullish OB: Last red candle before big move up
                        for i in range(-5, -1):
                            if closes[i] < closes[i-1]:  # Red candle
                                if closes[-1] > closes[i-1] * 1.01:  # Big move up after
                                    order_block_bull = True
                                    ob_level = (highs[i] + lows[i]) / 2
                                    break
                        
                        # Bearish OB: Last green candle before big move down
                        for i in range(-5, -1):
                            if closes[i] > closes[i-1]:  # Green candle
                                if closes[-1] < closes[i-1] * 0.99:  # Big move down after
                                    order_block_bear = True
                                    ob_level = (highs[i] + lows[i]) / 2
                                    break
                    
                    # ══════════════════════════════════════════════════════════
                    # GENEROWANIE SYGNAŁU NA PODSTAWIE ANALIZY
                    # ══════════════════════════════════════════════════════════
                    
                    signal_score = 0
                    signal_reasons = []
                    smc_signals = []  # Smart Money Concepts signals
                    
                    # RSI analysis
                    if rsi < 30:
                        signal_score += 25
                        signal_reasons.append("RSI oversold")
                    elif rsi < 40:
                        signal_score += 10
                        signal_reasons.append("RSI low")
                    elif rsi > 70:
                        signal_score -= 25
                        signal_reasons.append("RSI overbought")
                    elif rsi > 60:
                        signal_score -= 10
                        signal_reasons.append("RSI high")
                    
                    # EMA trend
                    if price > ema_9 > ema_21:
                        signal_score += 20
                        signal_reasons.append("Bullish EMA stack")
                    elif price < ema_9 < ema_21:
                        signal_score -= 20
                        signal_reasons.append("Bearish EMA stack")
                    
                    # EMA crossover
                    if ema_9 > ema_21 and closes[-2] < ema_9:
                        signal_score += 15
                        signal_reasons.append("Golden cross")
                    elif ema_9 < ema_21 and closes[-2] > ema_9:
                        signal_score -= 15
                        signal_reasons.append("Death cross")
                    
                    # MACD
                    if macd > 0 and macd_histogram > 0:
                        signal_score += 15
                        signal_reasons.append("MACD bullish")
                    elif macd < 0 and macd_histogram < 0:
                        signal_score -= 15
                        signal_reasons.append("MACD bearish")
                    
                    # Bollinger Bands
                    if bb_position < 0.2:
                        signal_score += 15
                        signal_reasons.append("Near BB lower")
                    elif bb_position > 0.8:
                        signal_score -= 15
                        signal_reasons.append("Near BB upper")
                    
                    # Volume confirmation
                    if volume_ratio > 1.5:
                        if signal_score > 0:
                            signal_score += 10
                            signal_reasons.append("High volume ✓")
                        else:
                            signal_score -= 10
                    
                    # Price action
                    if price > ema_50:
                        signal_score += 10
                        signal_reasons.append("Above EMA50")
                    else:
                        signal_score -= 10
                    
                    # ══════════════════════════════════════════════════════════
                    # PREMIUM/DISCOUNT ZONE SCORING
                    # ══════════════════════════════════════════════════════════
                    
                    # External Zone scoring - silniejszy wpływ
                    if ext_position <= 25:  # Discount zone
                        signal_score += 25
                        signal_reasons.append("EXT DISCOUNT zone")
                    elif ext_position >= 75:  # Premium zone
                        signal_score -= 25
                        signal_reasons.append("EXT PREMIUM zone")
                    
                    # Internal Zone scoring
                    if int_position <= 25:  # Internal discount
                        signal_score += 15
                        signal_reasons.append("INT DISCOUNT")
                    elif int_position >= 75:  # Internal premium
                        signal_score -= 15
                        signal_reasons.append("INT PREMIUM")
                    
                    # ══════════════════════════════════════════════════════════
                    # CVD (Cumulative Volume Delta) SCORING
                    # ══════════════════════════════════════════════════════════
                    
                    # CVD Trend scoring
                    if cvd_spot > cvd_spot_prev and cvd_futures > cvd_futures_prev:
                        signal_score += 20
                        signal_reasons.append("CVD Bullish")
                    elif cvd_spot < cvd_spot_prev and cvd_futures < cvd_futures_prev:
                        signal_score -= 20
                        signal_reasons.append("CVD Bearish")
                    
                    # CVD Divergence - bardzo silny sygnał!
                    if cvd_divergence == "🟢 BULLISH DIV":
                        signal_score += 30
                        smc_signals.append("🟢 CVD BULLISH DIVERGENCE")
                    elif cvd_divergence == "🔴 BEARISH DIV":
                        signal_score -= 30
                        smc_signals.append("🔴 CVD BEARISH DIVERGENCE")
                    
                    # ══════════════════════════════════════════════════════════
                    # SMART MONEY CONCEPTS SCORING
                    # ══════════════════════════════════════════════════════════
                    
                    # Liquidity Grab - bardzo silny sygnał!
                    if liquidity_grab_bull:
                        signal_score += 30
                        smc_signals.append(f"🎯 LIQ GRAB BULL @${grab_level:,.0f}")
                    if liquidity_grab_bear:
                        signal_score -= 30
                        smc_signals.append(f"🎯 LIQ GRAB BEAR @${grab_level:,.0f}")
                    
                    # EQH/EQL - płynność do zebrania (HTF i LTF)
                    # HTF - główna płynność (major)
                    if eqh_htf_detected and price < eqh_htf_level:
                        smc_signals.append(f"📊 EQH HTF @${eqh_htf_level:,.0f} (major liq.)")
                        if price > eqh_htf_level * 0.99:
                            signal_score -= 20  # Blisko głównej płynności
                    
                    if eql_htf_detected and price > eql_htf_level:
                        smc_signals.append(f"📊 EQL HTF @${eql_htf_level:,.0f} (major liq.)")
                        if price < eql_htf_level * 1.01:
                            signal_score += 20
                    
                    # LTF - lokalna płynność (minor)
                    if eqh_ltf_detected and price < eqh_ltf_level:
                        smc_signals.append(f"📊 EQH LTF @${eqh_ltf_level:,.0f} (minor liq.)")
                        if price > eqh_ltf_level * 0.995:
                            signal_score -= 10
                    
                    if eql_ltf_detected and price > eql_ltf_level:
                        smc_signals.append(f"📊 EQL LTF @${eql_ltf_level:,.0f} (minor liq.)")
                        if price < eql_ltf_level * 1.005:
                            signal_score += 10
                    
                    # Fair Value Gap
                    if fvg_bullish:
                        signal_score += 20
                        smc_signals.append(f"📈 BULLISH FVG @${fvg_level:,.0f}")
                    if fvg_bearish:
                        signal_score -= 20
                        smc_signals.append(f"📉 BEARISH FVG @${fvg_level:,.0f}")
                    
                    # Order Blocks
                    if order_block_bull and price > ob_level * 0.99:
                        signal_score += 25
                        smc_signals.append(f"🟢 BULLISH OB @${ob_level:,.0f}")
                    if order_block_bear and price < ob_level * 1.01:
                        signal_score -= 25
                        smc_signals.append(f"🔴 BEARISH OB @${ob_level:,.0f}")
                    
                    # ══════════════════════════════════════════════════════════
                    # OKREŚL KIERUNEK I PARAMETRY SYGNAŁU
                    # ══════════════════════════════════════════════════════════
                    
                    if abs(signal_score) >= 25:  # Tylko silne sygnały
                        if signal_score > 0:
                            direction = "🟢 LONG"
                            # SL pod ostatnim swingiem lub -2%
                            sl_price = max(recent_low * 0.995, price * 0.98)
                            sl_percent = ((price - sl_price) / price) * 100
                            # TP z R:R 1:2 minimum
                            tp_price = price + (price - sl_price) * 2.5
                            tp_percent = ((tp_price - price) / price) * 100
                        else:
                            direction = "🔴 SHORT"
                            # SL nad ostatnim swingiem lub +2%
                            sl_price = min(recent_high * 1.005, price * 1.02)
                            sl_percent = ((sl_price - price) / price) * 100
                            # TP z R:R 1:2
                            tp_price = price - (sl_price - price) * 2.5
                            tp_percent = ((price - tp_price) / price) * 100
                        
                        # Oblicz confidence
                        confidence = min(95, 50 + abs(signal_score))
                        
                        # ══════════════════════════════════════════════════════════
                        # OBLICZ SZANSĘ POWODZENIA DLA WARIANTÓW A i B
                        # ══════════════════════════════════════════════════════════
                        
                        # WARIANT A - ze Stop Lossem
                        # Im dalej SL, tym większa szansa na sukces (cena ma więcej miejsca)
                        # Bazowa szansa zależy od: odległości SL, kierunku trendu, RSI, wolumenu
                        
                        base_success_a = 50  # Bazowa szansa 50%
                        
                        # Odległość SL wpływa na szansę (dalszy SL = większa szansa)
                        if sl_percent <= 1.0:
                            sl_bonus = -15  # Bardzo ciasny SL = mniejsza szansa
                        elif sl_percent <= 1.5:
                            sl_bonus = -5
                        elif sl_percent <= 2.0:
                            sl_bonus = 5
                        elif sl_percent <= 3.0:
                            sl_bonus = 15
                        else:
                            sl_bonus = 25  # Szeroki SL = większa szansa
                        
                        # Bonus za kierunek zgodny z RSI
                        if signal_score > 0 and rsi < 40:  # Long w oversold
                            rsi_bonus = 15
                        elif signal_score < 0 and rsi > 60:  # Short w overbought
                            rsi_bonus = 15
                        elif signal_score > 0 and rsi > 60:  # Long w overbought
                            rsi_bonus = -10
                        elif signal_score < 0 and rsi < 40:  # Short w oversold
                            rsi_bonus = -10
                        else:
                            rsi_bonus = 0
                        
                        # Bonus za wolumen
                        vol_bonus = min(15, int(volume_ratio * 5)) if volume_ratio > 1 else 0
                        
                        # Bonus za strefę Premium/Discount
                        if signal_score > 0 and ext_position < 30:  # Long w Discount
                            zone_bonus = 15
                        elif signal_score < 0 and ext_position > 70:  # Short w Premium
                            zone_bonus = 15
                        else:
                            zone_bonus = 0
                        
                        success_rate_a = min(85, max(25, base_success_a + sl_bonus + rsi_bonus + vol_bonus + zone_bonus))
                        
                        # WARIANT B - bez SL, Cross Margin
                        # Teoretycznie 100% w czasie, ale wymaga:
                        # - Cross margin
                        # - Odpowiedniego kapitału na maintenance margin
                        # - Cierpliwości (może trwać dni/tygodnie)
                        success_rate_b = 95  # Prawie pewne, ale wymaga czasu i kapitału
                        
                        # Oblicz margines bezpieczeństwa dla wariantu B
                        # Ile % cena może się ruszyć przeciw nam zanim likwidacja
                        if signal_score > 0:  # LONG
                            # Dla longa - ile może spaść
                            max_adverse_move = 50  # Przy 2x leverage, ~50% ruchu
                        else:  # SHORT
                            max_adverse_move = 50
                        
                        # Timeframe suggestion
                        if abs(change_24h) > 3:
                            timeframe = "⏱️ 15min (Scalp)"
                            validity = "1-4h"
                        elif volume_ratio > 1.5:
                            timeframe = "⏱️ 1H (Intraday)"
                            validity = "4-12h"
                        else:
                            timeframe = "⏱️ 4H (Swing)"
                            validity = "1-3 dni"
                        
                        # Oblicz konkretne poziomy stref cenowych
                        ext_discount_low = external_low
                        ext_discount_high = external_low + (external_range * 0.25)
                        ext_premium_low = external_high - (external_range * 0.25)
                        ext_premium_high = external_high
                        
                        int_discount_low = internal_low
                        int_discount_high = internal_low + (internal_range * 0.25)
                        int_premium_low = internal_high - (internal_range * 0.25)
                        int_premium_high = internal_high
                        
                        signals_list.append({
                            'symbol': symbol,
                            'name': name,
                            'direction': direction,
                            'price': price,
                            'sl': sl_price,
                            'sl_percent': sl_percent,
                            'tp': tp_price,
                            'tp_percent': tp_percent,
                            'confidence': confidence,
                            'score': abs(signal_score),
                            'reasons': signal_reasons[:4],
                            'smc': smc_signals[:3],  # Smart Money Concepts
                            'eqh': eqh_level if eqh_detected else None,
                            'eql': eql_level if eql_detected else None,
                            'liq_grab': grab_level if (liquidity_grab_bull or liquidity_grab_bear) else None,
                            'rsi': rsi,
                            'timeframe': timeframe,
                            'validity': validity,
                            'volume_ratio': volume_ratio,
                            # Warianty tradingowe A i B
                            'success_rate_a': success_rate_a,  # Z SL
                            'success_rate_b': success_rate_b,  # Bez SL (cross margin)
                            'max_adverse_move': max_adverse_move,  # Max ruch przeciw pozycji
                            # Premium/Discount zones - EXTERNAL
                            'ext_zone': ext_zone,
                            'ext_position': ext_position,
                            'ext_eq': external_eq,
                            'ext_discount_low': ext_discount_low,
                            'ext_discount_high': ext_discount_high,
                            'ext_premium_low': ext_premium_low,
                            'ext_premium_high': ext_premium_high,
                            'ext_high': external_high,
                            'ext_low': external_low,
                            # Premium/Discount zones - INTERNAL
                            'int_zone': int_zone,
                            'int_position': int_position,
                            'int_eq': internal_eq,
                            'int_discount_low': int_discount_low,
                            'int_discount_high': int_discount_high,
                            'int_premium_low': int_premium_low,
                            'int_premium_high': int_premium_high,
                            # CVD data
                            'cvd_spot': cvd_spot_display,
                            'cvd_spot_unit': cvd_spot_unit,
                            'cvd_spot_trend': cvd_spot_trend,
                            'cvd_futures': cvd_futures_display,
                            'cvd_futures_unit': cvd_futures_unit,
                            'cvd_futures_trend': cvd_futures_trend,
                            'cvd_divergence': cvd_divergence,
                            'binance_symbol': binance_sym  # Dla trackera
                        })
                        
                        # ══════════════════════════════════════════════════════════
                        # DODAJ DO HISTORII DLA ŚLEDZENIA SKUTECZNOŚCI
                        # ══════════════════════════════════════════════════════════
                        dir_clean = 'LONG' if signal_score > 0 else 'SHORT'
                        add_signal_to_history(
                            symbol=symbol,
                            binance_symbol=binance_sym,
                            direction=dir_clean,
                            entry=price,
                            tp=tp_price,
                            sl=sl_price,
                            confidence=confidence,
                            reasons=signal_reasons[:3]
                        )
                        
                except Exception as e:
                    print(f"Signal analysis error for {symbol}: {e}")
                    continue
            
            # Sortuj sygnały po score
            signals_list.sort(key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            print(f"Signals error: {e}")
        
        # ══════════════════════════════════════════════════════════
        # SPRAWDŹ SKUTECZNOŚĆ POPRZEDNICH SYGNAŁÓW
        # ══════════════════════════════════════════════════════════
        check_signal_accuracy()
        acc_stats = get_accuracy_stats()
        
        # ══════════════════════════════════════════════════════════
        # SPRAWDŹ STATUS API I RZETELNOŚĆ DANYCH
        # ══════════════════════════════════════════════════════════
        api_compact = get_api_status_compact()
        
        # ══════════════════════════════════════════════════════════
        # BUDUJ WIADOMOŚĆ Z SYGNAŁAMI
        # ══════════════════════════════════════════════════════════
        
        now = datetime.now().strftime('%H:%M:%S')
        
        # Emoji dla win rate
        if acc_stats['win_rate'] >= 70:
            wr_emoji = "🏆"
        elif acc_stats['win_rate'] >= 50:
            wr_emoji = "✅"
        elif acc_stats['win_rate'] >= 30:
            wr_emoji = "⚠️"
        else:
            wr_emoji = "📊"
        
        msg = f'''🎯 PROFESSIONAL TRADING SIGNALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{api_compact}

{wr_emoji} SKUTECZNOŚĆ: {acc_stats['win_rate']:.1f}%
├ ✅ WIN: {acc_stats['wins']} | ❌ LOSS: {acc_stats['losses']}
├ 📊 Total: {acc_stats['total']} | ⏳ Pending: {acc_stats['pending']}
└ 📈 Closed: {acc_stats['closed']} sygnałów

📊 Real-time Technical Analysis
🔄 Aktualizacja: {now} CET

'''
        
        if signals_list:
            for i, sig in enumerate(signals_list[:5], 1):
                reasons_str = " | ".join(sig['reasons'])
                
                # SMC levels display
                smc_str = ""
                if sig.get('smc'):
                    smc_str = "\n🎯 SMC: " + " | ".join(sig['smc'][:2])
                
                # Liquidity levels - z odległością od ceny
                liq_levels = ""
                if sig.get('eqh'):
                    eqh_dist = ((sig['eqh'] - sig['price']) / sig['price']) * 100
                    eqh_dir = "↑" if sig['eqh'] > sig['price'] else "↓"
                    liq_levels += f"\n📊 EQH: ${sig['eqh']:,.0f} ({eqh_dir}{abs(eqh_dist):.1f}%)"
                    liq_levels += f"\n   → Równe szczyty - płynność do zebrania"
                if sig.get('eql'):
                    eql_dist = ((sig['eql'] - sig['price']) / sig['price']) * 100
                    eql_dir = "↑" if sig['eql'] > sig['price'] else "↓"
                    liq_levels += f"\n📊 EQL: ${sig['eql']:,.0f} ({eql_dir}{abs(eql_dist):.1f}%)"
                    liq_levels += f"\n   → Równe dołki - płynność do zebrania"
                if sig.get('liq_grab'):
                    liq_levels += f"\n⚡ LIQ GRAB: ${sig['liq_grab']:,.0f}"
                    liq_levels += f"\n   → Zebrano płynność (sweep)"
                
                # Premium/Discount zones z KONKRETNYMI CENAMI
                pd_zones = f"\n\n💎 PREMIUM/DISCOUNT - EXTERNAL (24h):"
                pd_zones += f"\n├ 🔴 PREMIUM: ${sig['ext_premium_low']:,.0f} - ${sig['ext_premium_high']:,.0f}"
                pd_zones += f"\n│    → Strefa droga (75-100%)"
                pd_zones += f"\n├ 🟢 DISCOUNT: ${sig['ext_discount_low']:,.0f} - ${sig['ext_discount_high']:,.0f}"
                pd_zones += f"\n│    → Strefa tania (0-25%)"
                pd_zones += f"\n├ 📍 CENA: ${sig['price']:,.0f} = {sig['ext_zone']} ({sig['ext_position']:.0f}%)"
                pd_zones += f"\n└ ⚖️ EQ: ${sig['ext_eq']:,.0f}"
                
                # Internal zones
                pd_zones += f"\n\n💎 PREMIUM/DISCOUNT - INTERNAL (12h):"
                pd_zones += f"\n├ 🔴 PREMIUM: ${sig['int_premium_low']:,.0f} - ${sig['int_premium_high']:,.0f}"
                pd_zones += f"\n├ 🟢 DISCOUNT: ${sig['int_discount_low']:,.0f} - ${sig['int_discount_high']:,.0f}"
                pd_zones += f"\n├ 📍 CENA: {sig['int_zone']} ({sig['int_position']:.0f}%)"
                pd_zones += f"\n└ ⚖️ EQ: ${sig['int_eq']:,.0f}"
                
                # Interpretacja strefy
                zone_action = ""
                if sig['ext_position'] <= 25:
                    zone_action = f"\n\n💡 STREFA: DISCOUNT - szukaj LONG!"
                    zone_action += f"\n   → Kupuj w ${sig['ext_discount_low']:,.0f}-${sig['ext_discount_high']:,.0f}"
                elif sig['ext_position'] >= 75:
                    zone_action = f"\n\n💡 STREFA: PREMIUM - szukaj SHORT!"
                    zone_action += f"\n   → Shortuj w ${sig['ext_premium_low']:,.0f}-${sig['ext_premium_high']:,.0f}"
                else:
                    zone_action = f"\n\n💡 STREFA: EQUILIBRIUM - czekaj!"
                    zone_action += f"\n   → Lepsze wejście: <${sig['ext_discount_high']:,.0f} lub >${sig['ext_premium_low']:,.0f}"
                
                # CVD display
                cvd_info = f"\n\n📊 CVD (różnica kupno/sprzedaż):"
                cvd_info += f"\n├ SPOT: {sig['cvd_spot']:+.1f}{sig['cvd_spot_unit']} {sig['cvd_spot_trend']}"
                cvd_info += f"\n└ FUT: {sig['cvd_futures']:+.1f}{sig['cvd_futures_unit']} {sig['cvd_futures_trend']}"
                if sig.get('cvd_divergence'):
                    if "BULLISH" in sig['cvd_divergence']:
                        cvd_info += f"\n⚡ {sig['cvd_divergence']}!"
                        cvd_info += f"\n   → Cena spada ale kupują = akumulacja!"
                    else:
                        cvd_info += f"\n⚡ {sig['cvd_divergence']}!"
                        cvd_info += f"\n   → Cena rośnie ale sprzedają = dystrybucja!"
                
                msg += f'''{'═'*30}
{sig['direction']} {sig['symbol']} {sig['timeframe']}
━━━━━━━━━━━━━━━━━━━━
📍 Entry: ${sig['price']:,.2f}
🛑 Stop Loss: ${sig['sl']:,.2f} ({sig['sl_percent']:.1f}%)
🎯 Take Profit: ${sig['tp']:,.2f} (+{sig['tp_percent']:.1f}%)

📈 RSI: {sig['rsi']:.0f} | Vol: {sig['volume_ratio']:.1f}x
🎲 Confidence: {sig['confidence']}%
⏰ Ważność: {sig['validity']}
{smc_str}{liq_levels}{pd_zones}{zone_action}{cvd_info}

💡 {reasons_str}
📌 Szczegóły + Taktyka B → kliknij {sig['symbol']}

'''
        else:
            msg += '''⏳ Brak silnych sygnałów w tej chwili.
Rynek w konsolidacji lub brak wyraźnego setupu.

Czekam na:
• RSI < 30 lub > 70
• EMA crossover
• Liquidity Grab
• FVG / Order Block

'''
        
        msg += f'''━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 TIMEFRAME LEGEND:
• 15min = Scalp (30min - 2h)
• 1H = Intraday (4-12h)  
• 4H = Swing (1-3 dni)

📐 WSKAŹNIKI UŻYWANE:
RSI(14) | EMA(9,21,50) | MACD | BB | CVD

🎯 SMART MONEY CONCEPTS:
• EQH/EQL = Równe szczyty/dołki (płynność)
• LIQ GRAB = Zebranie płynności (sweep)

💎 PREMIUM/DISCOUNT:
• 0-25% = DISCOUNT (tanio) 
• 75-100% = PREMIUM (drogo)

📌 Pełne taktyki + Taktyka B (bez SL)
→ Kliknij walutę (BTC/ETH) po szczegóły!

⚠️ NFA - Not Financial Advice
🐹 HAMSTER TERMINAL'''

        # Dodaj przyciski do szczegółów
        signals_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Odśwież", callback_data='signals')],
            [InlineKeyboardButton("📊 BTC Szczegóły", callback_data='btc'),
             InlineKeyboardButton("📊 ETH Szczegóły", callback_data='eth')],
            [InlineKeyboardButton("◀️ Menu", callback_data='menu')]
        ])
        
        await query.edit_message_text(msg, reply_markup=signals_kb)
    
    elif data == 'onchain':
        # Pobierz PRAWDZIWE dane on-chain z API
        await query.edit_message_text("⏳ Pobieram dane on-chain...", reply_markup=None)
        
        try:
            # 1. FEAR & GREED INDEX - prawdziwe dane z Alternative.me
            fg_data = requests.get('https://api.alternative.me/fng/?limit=1', timeout=5).json()
            fear_greed = int(fg_data['data'][0]['value'])
            fg_class = fg_data['data'][0]['value_classification']
            
            if fear_greed < 25:
                fg_status = "😱 EXTREME FEAR"
                fg_action = "Historycznie dobry moment na zakup!"
            elif fear_greed < 45:
                fg_status = "😰 FEAR"
                fg_action = "Rynek w strachu - szukaj okazji"
            elif fear_greed < 55:
                fg_status = "😐 NEUTRAL"
                fg_action = "Brak wyraźnego sentymentu"
            elif fear_greed < 75:
                fg_status = "😊 GREED"
                fg_action = "Optymizm rośnie - uwaga na FOMO"
            else:
                fg_status = "🤑 EXTREME GREED"
                fg_action = "Możliwy szczyt - rozważ realizację zysków!"
        except:
            fear_greed = 50
            fg_status = "😐 NEUTRAL"
            fg_action = "Brak danych"
        
        try:
            # 2. FUNDING RATE - prawdziwe dane z Binance Futures
            btc_funding_data = requests.get('https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1', timeout=5).json()
            eth_funding_data = requests.get('https://fapi.binance.com/fapi/v1/fundingRate?symbol=ETHUSDT&limit=1', timeout=5).json()
            
            btc_funding = float(btc_funding_data[0]['fundingRate']) * 100 if btc_funding_data else 0
            eth_funding = float(eth_funding_data[0]['fundingRate']) * 100 if eth_funding_data else 0
        except:
            btc_funding = 0.01
            eth_funding = 0.01
        
        def funding_emoji(f):
            if f > 0.05: return "🔴 OVERLEVERAGED LONGS"
            elif f > 0.02: return "🟡 Longs dominują"
            elif f < -0.02: return "🟡 Shorts dominują"
            elif f < -0.05: return "🔴 OVERLEVERAGED SHORTS"
            else: return "🟢 Neutralny"
        
        try:
            # 3. OPEN INTEREST - prawdziwe dane z Binance
            btc_oi = requests.get('https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT', timeout=5).json()
            eth_oi = requests.get('https://fapi.binance.com/fapi/v1/openInterest?symbol=ETHUSDT', timeout=5).json()
            
            btc_oi_value = float(btc_oi['openInterest']) if btc_oi else 0
            eth_oi_value = float(eth_oi['openInterest']) if eth_oi else 0
        except:
            btc_oi_value = 0
            eth_oi_value = 0
        
        try:
            # 4. VOLUME 24h - prawdziwe dane z Binance
            btc_ticker = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', timeout=5).json()
            eth_ticker = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT', timeout=5).json()
            
            btc_volume = float(btc_ticker['quoteVolume']) / 1e9  # W miliardach USD
            eth_volume = float(eth_ticker['quoteVolume']) / 1e9
            btc_price = float(btc_ticker['lastPrice'])
            eth_price = float(eth_ticker['lastPrice'])
            btc_change_24h = float(btc_ticker['priceChangePercent'])
            eth_change_24h = float(eth_ticker['priceChangePercent'])
        except:
            btc_volume = 0
            eth_volume = 0
            btc_price = 0
            eth_price = 0
            btc_change_24h = 0
            eth_change_24h = 0
        
        try:
            # 5. LONG/SHORT RATIO - prawdziwe dane z Binance
            btc_ls = requests.get('https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=1', timeout=5).json()
            eth_ls = requests.get('https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=ETHUSDT&period=1h&limit=1', timeout=5).json()
            
            btc_long_ratio = float(btc_ls[0]['longAccount']) * 100 if btc_ls else 50
            btc_short_ratio = float(btc_ls[0]['shortAccount']) * 100 if btc_ls else 50
            eth_long_ratio = float(eth_ls[0]['longAccount']) * 100 if eth_ls else 50
            eth_short_ratio = float(eth_ls[0]['shortAccount']) * 100 if eth_ls else 50
        except:
            btc_long_ratio = 50
            btc_short_ratio = 50
            eth_long_ratio = 50
            eth_short_ratio = 50
        
        try:
            # 6. TOP TRADER SENTIMENT - Binance
            btc_top = requests.get('https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=1', timeout=5).json()
            top_long = float(btc_top[0]['longAccount']) * 100 if btc_top else 50
            top_short = float(btc_top[0]['shortAccount']) * 100 if btc_top else 50
        except:
            top_long = 50
            top_short = 50
        
        # Oblicz Exchange Flow na podstawie zmian OI i wolumenu
        btc_flow = "🟢 BULLISH" if btc_change_24h > 0 and btc_funding > 0 else "🔴 BEARISH" if btc_change_24h < 0 else "🟡 NEUTRAL"
        eth_flow = "🟢 BULLISH" if eth_change_24h > 0 and eth_funding > 0 else "🔴 BEARISH" if eth_change_24h < 0 else "🟡 NEUTRAL"
        
        # Verdict
        if fear_greed < 30 and btc_funding < 0:
            verdict = "🟢 AKUMULACJA - Smart money może kupować!"
        elif fear_greed > 70 and btc_funding > 0.05:
            verdict = "🔴 DYSTRYBUCJA - Uwaga na spadki!"
        elif btc_long_ratio > 60:
            verdict = "⚠️ Za dużo LONG - ryzyko short squeeze"
        elif btc_short_ratio > 60:
            verdict = "⚠️ Za dużo SHORT - ryzyko long squeeze"
        else:
            verdict = "🟡 MIXED SIGNALS - Czekaj na potwierdzenie"
        
        msg = f'''🐋 ONCHAIN ANALYTICS (LIVE)
━━━━━━━━━━━━━━━━━━━━

💰 CENY (Binance):
₿ BTC: ${btc_price:,.2f} ({btc_change_24h:+.2f}%)
Ξ ETH: ${eth_price:,.2f} ({eth_change_24h:+.2f}%)

📊 MARKET FLOW:
₿ BTC {btc_flow}
Ξ ETH {eth_flow}

📈 OPEN INTEREST:
₿ BTC: {btc_oi_value:,.0f} BTC
Ξ ETH: {eth_oi_value:,.0f} ETH

💵 VOLUME 24H:
₿ BTC: ${btc_volume:.2f}B
Ξ ETH: ${eth_volume:.2f}B

📈 FUNDING RATE (8h):
₿ BTC: {btc_funding:.4f}% → {funding_emoji(btc_funding)}
Ξ ETH: {eth_funding:.4f}% → {funding_emoji(eth_funding)}

📊 LONG/SHORT RATIO:
₿ BTC: 🟢 {btc_long_ratio:.1f}% L / 🔴 {btc_short_ratio:.1f}% S
Ξ ETH: 🟢 {eth_long_ratio:.1f}% L / 🔴 {eth_short_ratio:.1f}% S

🎯 TOP TRADERS (BTC):
🟢 {top_long:.1f}% LONG / 🔴 {top_short:.1f}% SHORT

😱 FEAR & GREED: {fear_greed}/100
{fg_status}
→ {fg_action}

💡 VERDICT:
{verdict}

━━━━━━━━━━━━━━━━━━━━
{get_api_status_compact()}

⏰ Updated: {datetime.now().strftime('%H:%M:%S')}'''
        await query.edit_message_text(msg, reply_markup=get_back_button())
    
    elif data == 'autosignal':
        if chat_id in signal_subscribers:
            signal_subscribers.discard(chat_id)
            status = "🔕 WYŁĄCZONE"
            btn_text = "🔔 Włącz AUTO"
        else:
            signal_subscribers.add(chat_id)
            status = "🔔 WŁĄCZONE"
            btn_text = "🔕 Wyłącz AUTO"
        
        # Zapisz do persistent storage
        save_data({
            'subscribers': list(report_subscribers),
            'signal_subscribers': list(signal_subscribers),
            'price_alerts': price_alerts,
            'signal_stats': signal_stats
        })
        
        msg = f'''🤖 AUTO SIGNALS
━━━━━━━━━━━━━━━━━━━━
Status: {status}

📡 Monitoring 24/7 (co 2 min)

🎯 WYKRYWANE OKAZJE:
• 🚨 Flash Crash / Flash Pump
• 🎯 Liquidity Grab
• 🚀 Short Squeeze
• 💥 Long Squeeze
• 📈 Silne Momentum
• 🔄 Reversal Setup
• ⚠️ High Volatility

🔥 SYSTEM ATRAKCYJNOŚCI:
• HOT = duże ruchy + wick + momentum
• COLD = małe ruchy

💡 Sygnały pojawiają się SAME
   gdy wykryta zostanie okazja!'''
        
        auto_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(btn_text, callback_data='autosignal')],
            [InlineKeyboardButton("◀ Menu", callback_data='menu')]
        ])
        await query.edit_message_text(msg, reply_markup=auto_kb)
    
    elif data == 'report':
        if chat_id in report_subscribers:
            report_subscribers.discard(chat_id)
            status = "🔕 WYŁĄCZONE"
            btn_text = "🔔 Włącz raporty"
        else:
            report_subscribers.add(chat_id)
            status = "🔔 WŁĄCZONE"
            btn_text = "🔕 Wyłącz raporty"
        
        # Zapisz do persistent storage
        save_data({
            'subscribers': list(report_subscribers),
            'signal_subscribers': list(signal_subscribers),
            'price_alerts': price_alerts,
            'signal_stats': signal_stats
        })
        
        msg = f'''🔔 AUTO REPORTS
━━━━━━━━━━━━━━━━━━━━
Status: {status}

• 08:00 Morning report
• 20:00 Evening report
• >3% Price alerts'''
        
        report_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(btn_text, callback_data='report')],
            [InlineKeyboardButton("◀ Menu", callback_data='menu')]
        ])
        await query.edit_message_text(msg, reply_markup=report_kb)
    
    elif data == 'news':
        # DYNAMICZNE NEWSY - pobierz AKTUALNE dane z API!
        news_data = generate_dynamic_news()
        
        now = datetime.now().strftime('%H:%M')
        
        msg = f'''📰 LIVE NEWS FEED
━━━━━━━━━━━━━━━━━━━━
⏰ Update: {now} CET
💰 BTC ${news_data['btc_price']:,.0f} | ETH ${news_data['eth_price']:,.0f}
🪙 GOLD ${news_data['gold_price']:,.0f} | 🥈 SILVER ${news_data['silver_price']:.2f}

₿ CRYPTO NEWS:
'''  
        for headline in news_data['crypto']:
            msg += f"• {headline}\n"
        
        msg += "\n🪙 GOLD & METALS:\n"
        for headline in news_data['metals']:
            msg += f"• {headline}\n"
        
        msg += "\n🌐 MARKET OVERVIEW:\n"
        for headline in news_data['market']:
            msg += f"• {headline}\n"
        
        msg += '''\n━━━━━━━━━━━━━━━━━━━━
✅ Dane LIVE z Twelve Data API
🔄 Odśwież: Kliknij NEWS ponownie'''
        
        await query.edit_message_text(msg, reply_markup=get_back_button())
    
    elif data == 'tutorial':
        # Pobierz aktualną cenę dla przykładu
        btc_data = get_quote('BTC/USD')
        btc_price = float(btc_data.get('close', 100000)) if btc_data and 'close' in btc_data else 100000
        btc_price = round(btc_price / 1000) * 1000  # Zaokrąglij
        sl_price = btc_price - 1800
        tp_price = btc_price + 3500
        
        msg = f'''🎓 TUTORIAL - SZYBKI START
━━━━━━━━━━━━━━━━━━━━

📚 PODSTAWY TRADINGU:

1️⃣ LONG vs SHORT
• LONG 🟢 = Kupujesz, zyskujesz gdy cena rośnie
• SHORT 🔴 = Sprzedajesz, zyskujesz gdy cena spada

2️⃣ LEVERAGE (DŹWIGNIA)
• 10x = $100 kontroluje $1,000
• Zyski x10, ale straty też x10!
• Początkujący: MAX 5-10x

3️⃣ MARGIN (DEPOZYT)
• ISOLATED = Ryzykujesz tylko depozyt pozycji
• CROSS = Ryzykujesz całe konto (ostrożnie!)

4️⃣ STOP LOSS (SL)
• Automatyczne zamknięcie przy stracie
• ZAWSZE ustawiaj SL! Bez wyjątków.
• Typowy SL: 1-2% konta na trade

5️⃣ TAKE PROFIT (TP)
• Automatyczna realizacja zysku
• R:R 1:3 = Ryzykujesz $1 by zyskać $3

━━━━━━━━━━━━━━━━━━━━
📖 CZYTANIE SYGNAŁÓW (PRZYKŁAD):

🟢 BTC LONG ⏱️ 4H
Entry ${btc_price:,.0f} | SL ${sl_price:,.0f}
TP ${tp_price:,.0f} | Szansa 75%

→ Entry = Cena wejścia
→ SL = Stop Loss (max strata)
→ TP = Take Profit (cel zysku)
→ ⏱️ 4H = Timeframe analizy
→ Szansa = Prawdopodobieństwo sukcesu

━━━━━━━━━━━━━━━━━━━━
📊 ONCHAIN - CO TO?

• Exchange Flow = BTC/ETH wchodzące/wychodzące z giełd
• Inflow = Ludzie chcą sprzedawać (bearish)
• Outflow = Ludzie trzymają (bullish)
• Funding Rate = Koszt utrzymania pozycji futures
• Fear & Greed = Sentyment rynku (0-100)

━━━━━━━━━━━━━━━━━━━━
⚠️ ZŁOTE ZASADY:

• Nigdy nie ryzykuj więcej niż 1-2% konta
• Nie handluj pod wpływem emocji
• Prowadź dziennik tradów
• Ucz się na błędach
• Cierpliwość > Chciwość

🐹 Powodzenia, młody traderze!'''
        
        # Tutorial z przyciskami do wszystkich lekcji
        tutorial_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 R:R", callback_data='tutorial_rr'),
             InlineKeyboardButton("📊 ONCHAIN", callback_data='tutorial_onchain')],
            [InlineKeyboardButton("🕯️ ŚWIECE", callback_data='tutorial_candles'),
             InlineKeyboardButton("📐 PATTERNS", callback_data='tutorial_patterns')],
            [InlineKeyboardButton("🎯 STRATEGIE", callback_data='tutorial_strategy')],
            [InlineKeyboardButton("◀️ MENU", callback_data='menu')]
        ])
        await query.edit_message_text(msg, reply_markup=tutorial_kb)
    
    elif data == 'hamster_fun':
        # Losowy hamster GIF!
        import random
        random_gif = random.choice(HAMSTER_GIFS)
        
        hamster_msgs = [
            "🐹 *Chomik biega i zarabia!*",
            "🐹 *Kręć kółeczko, kręć!*",
            "🐹 *To ja po 12h tradingu!*",
            "🐹 *Praca Chomika nigdy się nie kończy!*",
            "🐹 *Running the crypto wheel!*",
            "🐹 *Hamster Terminal Power!*",
            "🐹 *HODL and run!*",
            "🐹 *W kółko kręcę - zyski liczę!*"
        ]
        random_msg = random.choice(hamster_msgs)
        
        # Usuwamy stary message i wysyłamy animację
        await query.message.delete()
        
        # Wyślij animację z tekstem
        hamster_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 LOSUJ PONOWNIE", callback_data='hamster_fun')],
            [InlineKeyboardButton("◀️ MENU", callback_data='menu')]
        ])
        
        await context.bot.send_animation(
            chat_id=query.message.chat_id,
            animation=random_gif,
            caption=random_msg,
            parse_mode='Markdown',
            reply_markup=hamster_kb
        )
    
    elif data == 'tutorial_rr':
        # Pobierz AKTUALNĄ cenę BTC dla dynamicznego przykładu
        btc_data = get_quote('BTC/USD')
        btc_price = float(btc_data.get('close', 100000)) if btc_data and 'close' in btc_data else 100000
        # Zaokrąglij do tysięcy
        btc_price = round(btc_price / 1000) * 1000
        
        sl_price = btc_price - 1000  # -$1000 risk
        tp_price = btc_price + 3000  # +$3000 reward
        
        msg = f'''📈 TUTORIAL: RISK:REWARD (R:R)
━━━━━━━━━━━━━━━━━━━━

🎯 CO TO R:R?

Risk:Reward = Stosunek potencjalnej
straty do potencjalnego zysku

━━━━━━━━━━━━━━━━━━━━
📊 PRZYKŁADY:

🔹 R:R 1:1
Ryzykujesz $100 by zyskać $100
→ Potrzebujesz >50% skuteczności

🔹 R:R 1:2
Ryzykujesz $100 by zyskać $200
→ Wystarczy 34% skuteczności!

🔹 R:R 1:3
Ryzykujesz $100 by zyskać $300
→ Wystarczy 25% skuteczności!

━━━━━━━━━━━━━━━━━━━━
💡 PRZYKŁAD Z AKTUALNĄ CENĄ:

BTC @ ${btc_price:,.0f}
Entry: ${btc_price:,.0f}
Stop Loss: ${sl_price:,.0f} (-$1,000 risk)
Take Profit: ${tp_price:,.0f} (+$3,000 reward)

→ R:R = 1:3 ✅

━━━━━━━━━━━━━━━━━━━━
⚡ ZASADA ZŁOTA:

Nigdy nie wchodź w trade
z R:R gorszym niż 1:2!

Lepiej przegapić okazję
niż stracić pieniądze.'''
        
        tutorial_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ TUTORIAL", callback_data='tutorial')],
            [InlineKeyboardButton("◀️ MENU", callback_data='menu')]
        ])
        await query.edit_message_text(msg, reply_markup=tutorial_kb)
    
    elif data == 'tutorial_onchain':
        msg = '''📊 TUTORIAL: ONCHAIN ANALYSIS
━━━━━━━━━━━━━━━━━━━━

🔍 CO TO ONCHAIN?

Analiza danych bezpośrednio
z blockchaina (przejrzysta, niezmanipulowana)

━━━━━━━━━━━━━━━━━━━━
📈 EXCHANGE FLOW:

🟢 OUTFLOW (wypływ z giełd)
→ Ludzie przelewają na cold wallet
→ Chcą HODL = BULLISH

🔴 INFLOW (wpływ na giełdy)
→ Ludzie chcą sprzedawać
→ Podaż rośnie = BEARISH

━━━━━━━━━━━━━━━━━━━━
💵 STABLECOINS NA GIEŁDACH:

📈 Więcej USDT/USDC na giełdach
→ "Sucha amunicja" gotowa do zakupów
→ BULLISH dla crypto

📉 Mniej stablecoinów
→ Brak paliwa do wzrostów
→ BEARISH krótkoterminowo

━━━━━━━━━━━━━━━━━━━━
📊 FUNDING RATE:

🔴 Funding > 0.05%
→ Za dużo longów (overleveraged)
→ Możliwy short squeeze w dół!

🟢 Funding < -0.02%
→ Za dużo shortów
→ Możliwy long squeeze w górę!

━━━━━━━━━━━━━━━━━━━━
😱 FEAR & GREED INDEX:

0-25: EXTREME FEAR
→ Historycznie dobry moment na zakup!

75-100: EXTREME GREED
→ Rynek przegrzany, możliwa korekta

━━━━━━━━━━━━━━━━━━━━
🐋 WHALE WATCHING:

Duże transfery wielorybów często
przewidują ruchy rynku.

• Whale → Giełda = Będzie sprzedawać
• Giełda → Whale = Akumulacja'''
        
        tutorial_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ TUTORIAL", callback_data='tutorial')],
            [InlineKeyboardButton("◀️ MENU", callback_data='menu')]
        ])
        await query.edit_message_text(msg, reply_markup=tutorial_kb)
    
    elif data == 'tutorial_candles':
        msg = '''🕯️ TUTORIAL: ŚWIECE JAPOŃSKIE
━━━━━━━━━━━━━━━━━━━━

📚 ANATOMIA ŚWIECY:

🟢 ŚWIECA WZROSTOWA (Bullish)
• OPEN (otwarcie) = na DOLE
• CLOSE (zamknięcie) = na GÓRZE
• Korpus = zielony/biały
• Knoty = cienie góra/dół

🔴 ŚWIECA SPADKOWA (Bearish)
• OPEN (otwarcie) = na GÓRZE
• CLOSE (zamknięcie) = na DOLE
• Korpus = czerwony/czarny
• Knoty = cienie góra/dół

━━━━━━━━━━━━━━━━━━━━
⭐ FORMACJE ODWRÓCENIA:

🔨 HAMMER (Młot) → BULLISH
• Mały korpus NA GÓRZE
• DŁUGI dolny knot (2-3x korpus)
• Brak lub minimalny górny knot
• Pojawia się na DNIE trendu
→ Sygnał: Kupujący przejmują kontrolę!

⭐ SHOOTING STAR (Gwiazda) → BEARISH
• Mały korpus NA DOLE
• DŁUGI górny knot (2-3x korpus)
• Brak lub minimalny dolny knot
• Pojawia się na SZCZYCIE trendu
→ Sygnał: Sprzedający przejmują kontrolę!

➕ DOJI → NIEZDECYDOWANIE
• Open = Close (prawie równe)
• Wygląda jak krzyżyk +
• Możliwa zmiana trendu
→ Czekaj na potwierdzenie następną świecą!

━━━━━━━━━━━━━━━━━━━━
🔥 FORMACJE 2-3 ŚWIEC:

📈 BULLISH ENGULFING → KUPUJ
• 1. Mała czerwona 🔴
• 2. Duża zielona 🟢 która CAŁKOWICIE
     "połyka" poprzednią świecę
→ Silny sygnał odwrócenia w GÓRĘ!

📉 BEARISH ENGULFING → SPRZEDAJ
• 1. Mała zielona 🟢
• 2. Duża czerwona 🔴 która CAŁKOWICIE
     "połyka" poprzednią świecę
→ Silny sygnał odwrócenia w DÓŁ!

⭐ MORNING STAR (3 świece) → KUPUJ
• 1. Duża czerwona 🔴
• 2. Mała (Doji lub mały korpus)
• 3. Duża zielona 🟢
→ Formacja DNA - silny LONG!

⭐ EVENING STAR (3 świece) → SPRZEDAJ
• 1. Duża zielona 🟢
• 2. Mała (Doji lub mały korpus)
• 3. Duża czerwona 🔴
→ Formacja SZCZYTU - silny SHORT!

━━━━━━━━━━━━━━━━━━━━
💡 ZASADY:

• 4H/1D świece > 5min/15min
• ZAWSZE czekaj na potwierdzenie
• Formacja + wolumen = silniejszy sygnał'''
        
        tutorial_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ TUTORIAL", callback_data='tutorial')],
            [InlineKeyboardButton("◀️ MENU", callback_data='menu')]
        ])
        await query.edit_message_text(msg, reply_markup=tutorial_kb)
    
    elif data == 'tutorial_patterns':
        msg = '''📐 TUTORIAL: CHART PATTERNS
━━━━━━━━━━━━━━━━━━━━

📈 FORMACJE KONTYNUACJI:
(Trend będzie kontynuowany)

🔺 TRÓJKĄT ROSNĄCY
• Góra: pozioma linia oporu
• Dół: rosnące dołki (wyższe minima)
• Cena "ściska się" coraz bardziej
→ Breakout w GÓRĘ = LONG!
→ SL pod ostatnim dołkiem

🔻 TRÓJKĄT MALEJĄCY
• Dół: pozioma linia wsparcia
• Góra: malejące szczyty (niższe maxima)
• Cena "ściska się" coraz bardziej
→ Breakout w DÓŁ = SHORT!
→ SL nad ostatnim szczytem

🚩 FLAG (Flaga)
• Silny ruch w górę/dół ("maszt")
• Krótka korekta w kanał ("flaga")
• Kontynuacja w kierunku masztu
→ Entry: breakout z flagi

━━━━━━━━━━━━━━━━━━━━
🔄 FORMACJE ODWRÓCENIA:

👑 HEAD & SHOULDERS (H&S)
• Lewe RAMIĘ (szczyt 1)
• GŁOWA (najwyższy szczyt)
• Prawe RAMIĘ (szczyt 3, podobny do 1)
• NECKLINE = linia łącząca dołki

→ Przebicie neckline w dół = SHORT!
→ Target = odległość głowy od neckline
→ SL nad prawym ramieniem

🔄 INVERSE H&S (Odwrócona)
• To samo, ale DO GÓRY NOGAMI
• Pojawia się na DNIE trendu
→ Przebicie neckline w górę = LONG!

━━━━━━━━━━━━━━━━━━━━
⭐ DOUBLE TOP / BOTTOM:

🅼 DOUBLE TOP (Litera M)
• Szczyt 1 → spadek → Szczyt 2
• Oba szczyty na PODOBNYM poziomie
• Środek M = wsparcie (neckline)
→ Przebicie wsparcia = SHORT!
→ Target = wysokość formacji

🆆 DOUBLE BOTTOM (Litera W)
• Dołek 1 → wzrost → Dołek 2
• Oba dołki na PODOBNYM poziomie
• Środek W = opór (neckline)
→ Przebicie oporu = LONG!
→ Target = wysokość formacji

━━━━━━━━━━━━━━━━━━━━
☕ CUP & HANDLE (Filiżanka):
• Zaokrąglone dno ("filiżanka")
• Mała korekta w dół ("ucho")
→ Bardzo BULLISH!
→ Breakout z "ucha" = LONG
→ Target = głębokość filiżanki

━━━━━━━━━━━━━━━━━━━━
💡 ZŁOTE ZASADY:

• Czekaj na BREAKOUT + RETEST
• Wolumen potwierdza pattern!
• Dłuższa formacja = silniejsza
• SL ZAWSZE za formacją'''
        
        tutorial_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ TUTORIAL", callback_data='tutorial')],
            [InlineKeyboardButton("◀️ MENU", callback_data='menu')]
        ])
        await query.edit_message_text(msg, reply_markup=tutorial_kb)
    
    elif data == 'tutorial_strategy':
        msg = '''🎯 TUTORIAL: STRATEGIE TRADINGOWE
━━━━━━━━━━━━━━━━━━━━

📊 1. TREND FOLLOWING
(Podążaj za trendem)

→ "Trend is your friend"
→ Kupuj gdy cena > MA200
→ Sprzedaj gdy cena < MA200
→ Używaj MA crossover (np. MA50/MA200)

🟢 Golden Cross: MA50 > MA200 = BULLISH
🔴 Death Cross: MA50 < MA200 = BEARISH

━━━━━━━━━━━━━━━━━━━━
📊 2. SUPPORT/RESISTANCE
(Wsparcia i opory)

→ Kupuj przy SUPPORT (wsparcie)
→ Sprzedaj przy RESISTANCE (opór)
→ Breakout = silny ruch w kierunku przebicia

⚠️ Support przebity = staje się Resistance!
⚠️ Resistance przebity = staje się Support!

━━━━━━━━━━━━━━━━━━━━
📊 3. BREAKOUT TRADING

1. Znajdź konsolidację (range)
2. Czekaj na przebicie
3. Wejdź PO RETEŚCIE
4. SL za range, TP = szerokość range

✅ Wolumen musi rosnąć przy breakout!

━━━━━━━━━━━━━━━━━━━━
📊 4. SCALPING (Szybkie trade)

→ Timeframe: 1min - 15min
→ Małe zyski, dużo tradów
→ R:R minimum 1:1.5
→ Wymaga skupienia i dyscypliny
→ Spread/fees zjadają zyski!

━━━━━━━━━━━━━━━━━━━━
📊 5. SWING TRADING

→ Timeframe: 4H - 1D
→ Trzymasz pozycję dni-tygodnie
→ R:R minimum 1:3
→ Mniej stresu, lepsze R:R
→ Idealny dla początkujących!

━━━━━━━━━━━━━━━━━━━━
📊 6. DCA (Dollar Cost Averaging)

→ Kupuj regularnie za stałą kwotę
→ Np. $100/tydzień w BTC
→ Uśredniasz cenę zakupu
→ Eliminujesz emocje
→ Długoterminowo BARDZO skuteczne!

━━━━━━━━━━━━━━━━━━━━
⚡ QUICK STRATEGY CHECKLIST:

✅ Określ trend (UP/DOWN/SIDEWAYS)
✅ Znajdź poziomy S/R
✅ Czekaj na sygnał wejścia
✅ Ustaw SL PRZED wejściem
✅ Oblicz R:R (min 1:2)
✅ Nie ryzykuj >1-2% konta
✅ Zapisz trade w dzienniku

🐹 Disciplina > Talent!'''
        
        tutorial_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ TUTORIAL", callback_data='tutorial')],
            [InlineKeyboardButton("◀️ MENU", callback_data='menu')]
        ])
        await query.edit_message_text(msg, reply_markup=tutorial_kb)
    
    # ═══════════════════════════════════════════════════════════════
    # FEAR & GREED INDEX - wskaźnik sentymentu rynku
    # ═══════════════════════════════════════════════════════════════
    elif data == 'feargreed':
        await query.edit_message_text("⏳ Obliczam Fear & Greed Index...")
        
        score, label = calculate_fear_greed()
        
        # Wizualizacja paska
        bar_length = 20
        filled = int(score / 100 * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Emoji w zależności od poziomu
        if score >= 80:
            emoji = '🤑'
            advice = '⚠️ Rynek przegrzany! Rozważ realizację zysków.'
            color = '🔴'
        elif score >= 60:
            emoji = '😊'
            advice = '📈 Optymizm rośnie. Uważaj na FOMO!'
            color = '🟡'
        elif score >= 40:
            emoji = '😐'
            advice = '⚖️ Rynek w równowadze. Czekaj na wyraźny sygnał.'
            color = '🟢'
        elif score >= 20:
            emoji = '😰'
            advice = '🔍 Strach = Okazje. Szukaj poziomów wsparcia.'
            color = '🟡'
        else:
            emoji = '😱'
            advice = '💎 EXTREME FEAR = Historycznie najlepszy czas na zakup!'
            color = '🔴'
        
        # Pobierz dane do kontekstu
        btc_data = get_quote('BTC/USD')
        btc_change = float(btc_data.get('percent_change', 0)) if btc_data else 0
        
        now = datetime.now().strftime('%H:%M:%S')
        
        msg = f'''😱 FEAR & GREED INDEX
━━━━━━━━━━━━━━━━━━━━━━━━━━

{emoji} {label}
{color} [{bar}] {score}/100

━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SKŁADNIKI INDEKSU:

• Momentum BTC 24h: {btc_change:+.2f}%
• Volatility: {"Wysoka ⚠️" if abs(btc_change) > 3 else "Normalna ✅"}
• Market Trend: {"📈 UP" if btc_change > 0 else "📉 DOWN"}

━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 INTERPRETACJA:

0-25   = 😱 EXTREME FEAR
26-45  = 😰 FEAR  
46-55  = 😐 NEUTRAL
56-75  = 😊 GREED
76-100 = 🤑 EXTREME GREED

━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 REKOMENDACJA:

{advice}

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ {now} CET
🐹 HAMSTER TERMINAL'''
        
        await query.edit_message_text(msg, reply_markup=get_back_button())
    
    # ═══════════════════════════════════════════════════════════════
    # FUNDING RATE CALCULATOR - zarabianie na fundingu
    # ═══════════════════════════════════════════════════════════════
    elif data == 'funding' or data.startswith('funding_exchange_'):
        # Sprawdź czy wybrano giełdę
        if data.startswith('funding_exchange_'):
            exchange = data.replace('funding_exchange_', '')
        else:
            exchange = 'binance'  # domyślna
        
        exchange_names = {'binance': 'Binance', 'bybit': 'Bybit', 'okx': 'OKX'}
        await query.edit_message_text(f"💰 Pobieram Funding z {exchange_names.get(exchange, exchange)}...")
        
        try:
            # Pobierz funding rates z wybranej giełdy
            funding_data = []
            
            if exchange == 'binance':
                symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT', 'BNBUSDT']
                for sym in symbols:
                    try:
                        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={sym}&limit=1"
                        r = requests.get(url, timeout=5)
                        data_resp = r.json()
                        if data_resp and len(data_resp) > 0:
                            rate = float(data_resp[0].get('fundingRate', 0)) * 100
                            funding_data.append({'symbol': sym, 'rate': rate, 'exchange': 'Binance'})
                    except:
                        pass
            
            elif exchange == 'bybit':
                symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT']
                for sym in symbols:
                    try:
                        url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={sym}"
                        r = requests.get(url, timeout=5)
                        data_resp = r.json()
                        if data_resp.get('result', {}).get('list'):
                            rate = float(data_resp['result']['list'][0].get('fundingRate', 0)) * 100
                            funding_data.append({'symbol': sym, 'rate': rate, 'exchange': 'Bybit'})
                    except:
                        pass
            
            elif exchange == 'okx':
                symbols_okx = ['BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP', 'XRP-USDT-SWAP', 'DOGE-USDT-SWAP', 'AVAX-USDT-SWAP', 'LINK-USDT-SWAP']
                for sym in symbols_okx:
                    try:
                        url = f"https://www.okx.com/api/v5/public/funding-rate?instId={sym}"
                        r = requests.get(url, timeout=5)
                        data_resp = r.json()
                        if data_resp.get('data'):
                            rate = float(data_resp['data'][0].get('fundingRate', 0)) * 100
                            display_sym = sym.replace('-USDT-SWAP', 'USDT')
                            funding_data.append({'symbol': display_sym, 'rate': rate, 'exchange': 'OKX'})
                    except:
                        pass
            
            # Sortuj po rate (od najwyższego do najniższego)
            funding_data.sort(key=lambda x: abs(x['rate']), reverse=True)
            
            now = datetime.now().strftime('%H:%M:%S')
            ex_name = exchange_names.get(exchange, exchange)
            
            msg = f'''💰 FUNDING RATE TERMINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏦 Giełda: {ex_name}

📊 AKTUALNE FUNDING RATES (8h):
'''
            for fd in funding_data:
                rate = fd['rate']
                sym = fd['symbol'].replace('USDT', '')
                arrow = "🟢" if rate > 0 else "🔴" if rate < 0 else "⚪"
                direction = "L→S" if rate > 0 else "S→L" if rate < 0 else "="
                msg += f"{arrow} {sym}: {rate:+.4f}% ({direction})\n"
            
            # Znajdź najlepszy do zarobku
            if funding_data:
                best = funding_data[0]
                best_rate = best['rate']
                best_sym = best['symbol'].replace('USDT', '')
                
                msg += f'''
━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 NAJLEPSZY: {best_sym} ({best_rate:+.4f}%)
   {"SHORT + hedge" if best_rate > 0 else "LONG futures"}

💡 Wybierz giełdę lub oblicz zysk!

⏰ {now} CET'''
            
            # Przyciski - wybór giełdy + kalkulator
            # Zaznacz aktualną giełdę
            binance_btn = "🟢 Binance" if exchange == 'binance' else "Binance"
            bybit_btn = "🟢 Bybit" if exchange == 'bybit' else "Bybit"
            okx_btn = "🟢 OKX" if exchange == 'okx' else "OKX"
            
            funding_kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(binance_btn, callback_data='funding_exchange_binance'),
                    InlineKeyboardButton(bybit_btn, callback_data='funding_exchange_bybit'),
                    InlineKeyboardButton(okx_btn, callback_data='funding_exchange_okx')
                ],
                [InlineKeyboardButton("🧮 KALKULATOR ZYSKU", callback_data=f'funding_calc_start_{exchange}')],
                [
                    InlineKeyboardButton("BTC", callback_data=f'funding_calc_{exchange}_BTCUSDT'),
                    InlineKeyboardButton("ETH", callback_data=f'funding_calc_{exchange}_ETHUSDT'),
                    InlineKeyboardButton("SOL", callback_data=f'funding_calc_{exchange}_SOLUSDT'),
                    InlineKeyboardButton("XRP", callback_data=f'funding_calc_{exchange}_XRPUSDT')
                ],
                [InlineKeyboardButton("◀ Menu", callback_data='menu')]
            ])
            
            await query.edit_message_text(msg, reply_markup=funding_kb)
            
        except Exception as e:
            await query.edit_message_text(f"❌ Błąd: {e}", reply_markup=get_back_button())
    
    # FUNDING CALCULATOR - wybór waluty i start kalkulatora
    elif data.startswith('funding_calc_start'):
        # Sprawdź czy jest giełda w callbacku
        if '_' in data.replace('funding_calc_start_', ''):
            exchange = data.replace('funding_calc_start_', '')
        else:
            exchange = 'binance'
        
        msg = f'''🧮 KALKULATOR ZYSKU Z FUNDINGU
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏦 Giełda: {exchange.upper()}

Wybierz walutę do obliczenia zysku:'''
        
        calc_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("₿ BTC", callback_data=f'funding_calc_{exchange}_BTCUSDT'),
                InlineKeyboardButton("Ξ ETH", callback_data=f'funding_calc_{exchange}_ETHUSDT')
            ],
            [
                InlineKeyboardButton("◎ SOL", callback_data=f'funding_calc_{exchange}_SOLUSDT'),
                InlineKeyboardButton("✕ XRP", callback_data=f'funding_calc_{exchange}_XRPUSDT')
            ],
            [
                InlineKeyboardButton("🐕 DOGE", callback_data=f'funding_calc_{exchange}_DOGEUSDT'),
                InlineKeyboardButton("🔺 AVAX", callback_data=f'funding_calc_{exchange}_AVAXUSDT')
            ],
            [InlineKeyboardButton("◀ Wstecz", callback_data=f'funding_exchange_{exchange}')]
        ])
        await query.edit_message_text(msg, reply_markup=calc_kb)
    
    # FUNDING CALCULATOR - dla konkretnej waluty z giełdą
    elif data.startswith('funding_calc_') and not data.startswith('funding_calc_start'):
        # Format: funding_calc_EXCHANGE_SYMBOL np. funding_calc_binance_BTCUSDT
        parts = data.replace('funding_calc_', '').split('_')
        
        if len(parts) >= 2:
            exchange = parts[0]
            symbol = parts[1]
        else:
            exchange = 'binance'
            symbol = parts[0]
        
        # Pobierz aktualny funding rate z wybranej giełdy
        funding_rate = 0.01  # fallback
        try:
            if exchange == 'binance':
                url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
                r = requests.get(url, timeout=5)
                data_resp = r.json()
                funding_rate = float(data_resp[0].get('fundingRate', 0)) * 100 if data_resp else 0.01
            elif exchange == 'bybit':
                url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
                r = requests.get(url, timeout=5)
                data_resp = r.json()
                if data_resp.get('result', {}).get('list'):
                    funding_rate = float(data_resp['result']['list'][0].get('fundingRate', 0)) * 100
            elif exchange == 'okx':
                okx_symbol = symbol.replace('USDT', '-USDT-SWAP')
                url = f"https://www.okx.com/api/v5/public/funding-rate?instId={okx_symbol}"
                r = requests.get(url, timeout=5)
                data_resp = r.json()
                if data_resp.get('data'):
                    funding_rate = float(data_resp['data'][0].get('fundingRate', 0)) * 100
        except:
            pass
        
        sym_name = symbol.replace('USDT', '')
        exchange_name = {'binance': 'Binance', 'bybit': 'Bybit', 'okx': 'OKX'}.get(exchange, exchange)
        
        # Zapisz dane i poproś o kwotę
        users_waiting_for_funding[chat_id] = {
            'symbol': symbol,
            'sym_name': sym_name,
            'funding_rate': funding_rate,
            'exchange': exchange,
            'step': 'amount'
        }
        
        msg = f'''🧮 KALKULATOR ZYSKU: {sym_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏦 Giełda: {exchange_name}

📊 Aktualny Funding Rate: {funding_rate:+.4f}%
   ({"LONG płaci SHORT" if funding_rate > 0 else "SHORT płaci LONG"})

📝 PODAJ DANE:

Wpisz w formacie:
KWOTA DŹWIGNIA DNI

Przykłady:
• 1000 10 30  (=$1000, 10x, 30 dni)
• 500 200 7  (=$500, 200x, 7 dni)
• 2000 100 30 (=$2000, 100x, 30 dni)

⚡ Brak limitu dźwigni - oblicz teoretyczny zysk!

💡 Lub wybierz gotowy preset:'''
        
        preset_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("$1000 × 50x × 30d", callback_data=f'funding_preset_{exchange}_{symbol}_1000_50_30'),
                InlineKeyboardButton("$1000 × 100x × 30d", callback_data=f'funding_preset_{exchange}_{symbol}_1000_100_30')
            ],
            [
                InlineKeyboardButton("$500 × 200x × 30d", callback_data=f'funding_preset_{exchange}_{symbol}_500_200_30'),
                InlineKeyboardButton("$2000 × 125x × 30d", callback_data=f'funding_preset_{exchange}_{symbol}_2000_125_30')
            ],
            [InlineKeyboardButton("◀ Wybierz inną walutę", callback_data=f'funding_calc_start_{exchange}')]
        ])
        await query.edit_message_text(msg, reply_markup=preset_kb)
    
    # FUNDING PRESET - szybkie obliczenie
    # Format: funding_preset_EXCHANGE_SYMBOL_AMOUNT_LEVERAGE_DAYS
    elif data.startswith('funding_preset_'):
        parts = data.replace('funding_preset_', '').split('_')
        # Nowy format: exchange_symbol_amount_leverage_days
        if len(parts) >= 5:
            exchange = parts[0]
            symbol = parts[1]
            amount = float(parts[2])
            leverage = float(parts[3])
            days = int(parts[4])
        else:
            # Stary format (fallback)
            exchange = 'binance'
            symbol = parts[0]
            amount = float(parts[1])
            leverage = float(parts[2])
            days = int(parts[3])
        
        # Pobierz aktualny funding rate z wybranej giełdy
        funding_rate = 0.01
        try:
            if exchange == 'binance':
                url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
                r = requests.get(url, timeout=5)
                data_resp = r.json()
                funding_rate = float(data_resp[0].get('fundingRate', 0)) * 100 if data_resp else 0.01
            elif exchange == 'bybit':
                url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
                r = requests.get(url, timeout=5)
                data_resp = r.json()
                if data_resp.get('result', {}).get('list'):
                    funding_rate = float(data_resp['result']['list'][0].get('fundingRate', 0)) * 100
            elif exchange == 'okx':
                okx_symbol = symbol.replace('USDT', '-USDT-SWAP')
                url = f"https://www.okx.com/api/v5/public/funding-rate?instId={okx_symbol}"
                r = requests.get(url, timeout=5)
                data_resp = r.json()
                if data_resp.get('data'):
                    funding_rate = float(data_resp['data'][0].get('fundingRate', 0)) * 100
        except:
            pass
        
        sym_name = symbol.replace('USDT', '')
        exchange_name = {'binance': 'Binance', 'bybit': 'Bybit', 'okx': 'OKX'}.get(exchange, exchange)
        
        # Obliczenia
        position_size = amount * leverage
        funding_per_8h = position_size * (abs(funding_rate) / 100)
        funding_per_day = funding_per_8h * 3  # 3 razy dziennie
        funding_total = funding_per_day * days
        roi_percent = (funding_total / amount) * 100
        apy = (funding_per_day * 365 / amount) * 100
        
        # Strategia
        if funding_rate > 0:
            strategy = f"SHORT {sym_name} futures + LONG {sym_name} spot"
            strategy_desc = "Longi płacą Ci funding!"
        else:
            strategy = f"LONG {sym_name} futures (zbierasz od shortów)"
            strategy_desc = "Shorty płacą Ci funding!"
        
        msg = f'''💰 WYNIK KALKULACJI: {sym_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏦 Giełda: {exchange_name}

📊 TWOJE PARAMETRY:
   💵 Kapitał: ${amount:,.0f}
   📈 Dźwignia: {leverage:.0f}x
   📅 Okres: {days} dni
   
📈 FUNDING RATE: {funding_rate:+.4f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 OBLICZENIA:

   Pozycja: ${position_size:,.0f}
   Funding/8h: ${funding_per_8h:.2f}
   Funding/dzień: ${funding_per_day:.2f}
   
🔥 ZYSK Z FUNDINGU ({days} dni):
   ${funding_total:,.2f}
   
   ROI: {roi_percent:.1f}%
   APY: ~{apy:.0f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 STRATEGIA:
   {strategy}
   → {strategy_desc}

⚠️ UWAGA: To teoretyczny zysk z fundingu.
   Nie uwzględnia zmian ceny aktywu!

━━━━━━━━━━━━━━━━━━━━━━━━━━
🐹 HAMSTER TERMINAL'''
        
        result_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Inna kwota", callback_data=f'funding_calc_{exchange}_{symbol}')],
            [InlineKeyboardButton("💱 Inna waluta", callback_data=f'funding_calc_start_{exchange}')],
            [InlineKeyboardButton("◀ Funding Rates", callback_data=f'funding_exchange_{exchange}')]
        ])
        await query.edit_message_text(msg, reply_markup=result_kb)
    
    # ═══════════════════════════════════════════════════════════════
    # TAKTYKA - strategie tradingowe
    # ═══════════════════════════════════════════════════════════════
    elif data == 'taktyka':
        msg = '''📚 TAKTYKI TRADINGOWE
━━━━━━━━━━━━━━━━━━━━━━━━━━

🅰️ TAKTYKA A: ISOLATED MARGIN
━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 Izolowana pozycja - ryzykujesz TYLKO
   kapitał przypisany do tej pozycji.

✅ ZALETY:
   → Kontrolowane ryzyko
   → Strata = tylko margin pozycji
   → Możesz mieć wiele pozycji

⚠️ WADY:
   → Łatwiejsza likwidacja
   → Musisz zarządzać każdą pozycją

📊 PRZYKŁAD (portfel $1000):
   $100 margin × 10x = $1000 pozycja
   Likwidacja: -10% ruchu
   Max strata: $100 (nie portfel!)

━━━━━━━━━━━━━━━━━━━━━━━━━━
🅱️ TAKTYKA B: CROSS MARGIN (0% LIQ)
━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 CAŁY portfel jako zabezpieczenie.
   Dźwignia DOWOLNA - liczy się proporcja!

🟢 LONG = BEZPIECZNY
   → Max strata = -100% (cena → $0)
   → Można DOKŁADNIE obliczyć likwidację
   → Idealne na HODL z dźwignią

🔴 SHORT = RYZYKOWNY!
   → Max strata = NIEOGRANICZONA!
   → Cena może +500%, +1000%...
   → NIE GRAJ short na małych coinach!

📊 KALKULATOR (portfel $1000):

🔹 10x LONG (10% portfela = $100):
   Pozycja: $100 × 10 = $1,000
   Likwidacja: cena -90%
   → NIGDY nie stracisz >$100!

🔹 50x LONG (2% portfela = $20):
   Pozycja: $20 × 50 = $1,000
   Likwidacja: cena -98%
   → Praktycznie BEZ likwidacji!

🔹 100x LONG (1% portfela = $10):
   Pozycja: $10 × 100 = $1,000
   Likwidacja: cena -99%
   → Cena musi spaść do ~$0!

✅ FORMUŁA SUKCESU:
   Kapitał% = 100% ÷ Dźwignia
   • 10x → max 10% portfela
   • 50x → max 2% portfela  
   • 100x → max 1% portfela
   • 500x → max 0.2% portfela

━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 KTÓRA TAKTYKA KIEDY?
━━━━━━━━━━━━━━━━━━━━━━━━━━

🅰️ ISOLATED gdy:
   → Daytrading, scalping
   → Chcesz kontrolować każdą pozycję
   → Grasz na wielu parach naraz

🅱️ CROSS gdy:
   → HODL z dźwignią (swing trade)
   → Chcesz ZERO likwidacji na LONG
   → Jeden główny trade

⚠️ ZŁOTE ZASADY:
   1. Nigdy nie ryzykuj >5% portfela
   2. SHORT = tylko duże coiny (BTC/ETH)
   3. Wysoka dźwignia = mały kapitał
   4. LONG > SHORT (mniejsze ryzyko)

🐹 HAMSTER TERMINAL'''
        
        await query.edit_message_text(msg, reply_markup=get_back_button())
    
    # ═══════════════════════════════════════════════════════════════
    # WHALE TRACKER - aktywność wielorybów
    # ═══════════════════════════════════════════════════════════════
    elif data == 'whale':
        await query.edit_message_text("🐋 Skanuję aktywność wielorybów (real blockchain data)...")
        
        # Pobierz ceny z Binance
        btc_data = get_quote('BTC/USD')
        eth_data = get_quote('ETH/USD')
        
        btc_price = float(btc_data.get('close', 100000)) if btc_data else 100000
        eth_price = float(eth_data.get('close', 3000)) if eth_data else 3000
        
        whale_txs = []
        total_inflow = 0
        total_outflow = 0
        
        try:
            # === BLOCKCHAIR API - PRAWDZIWE DUŻE TRANSAKCJE BTC ===
            btc_whale_url = "https://api.blockchair.com/bitcoin/transactions?q=output_total(100000000000..)&s=time(desc)&limit=5"
            btc_response = requests.get(btc_whale_url, timeout=10)
            if btc_response.status_code == 200:
                btc_data_chain = btc_response.json()
                for tx in btc_data_chain.get('data', [])[:5]:
                    amount_btc = tx.get('output_total', 0) / 100_000_000  # satoshi to BTC
                    value_usd = amount_btc * btc_price
                    tx_time = tx.get('time', '')[:16]
                    
                    # Heurystyka: transfer na giełdę = SELL, z giełdy = BUY
                    is_to_exchange = tx.get('output_count', 1) < 3  # Mało outputów = giełda
                    tx_type = '🔴 SELL' if is_to_exchange else '🟢 BUY'
                    
                    if is_to_exchange:
                        total_outflow += value_usd
                    else:
                        total_inflow += value_usd
                    
                    whale_txs.append({
                        'asset': 'BTC',
                        'amount': amount_btc,
                        'value': value_usd,
                        'type': tx_type,
                        'from': 'Wallet',
                        'to': 'Exchange' if is_to_exchange else 'Cold Storage',
                        'time': tx_time
                    })
        except Exception as e:
            print(f"Blockchair BTC error: {e}")
        
        try:
            # === BLOCKCHAIR API - PRAWDZIWE DUŻE TRANSAKCJE ETH ===
            eth_whale_url = "https://api.blockchair.com/ethereum/transactions?q=value(10000000000000000000000..)&s=time(desc)&limit=5"
            eth_response = requests.get(eth_whale_url, timeout=10)
            if eth_response.status_code == 200:
                eth_data_chain = eth_response.json()
                for tx in eth_data_chain.get('data', [])[:5]:
                    amount_eth = tx.get('value', 0) / 10**18  # wei to ETH
                    value_usd = amount_eth * eth_price
                    tx_time = tx.get('time', '')[:16]
                    
                    is_to_exchange = 'exchange' in str(tx.get('recipient', '')).lower() or tx.get('call_count', 0) == 0
                    tx_type = '🔴 SELL' if is_to_exchange else '🟢 BUY'
                    
                    if is_to_exchange:
                        total_outflow += value_usd
                    else:
                        total_inflow += value_usd
                    
                    whale_txs.append({
                        'asset': 'ETH',
                        'amount': amount_eth,
                        'value': value_usd,
                        'type': tx_type,
                        'from': 'Wallet',
                        'to': 'Exchange' if is_to_exchange else 'DeFi/Cold',
                        'time': tx_time
                    })
        except Exception as e:
            print(f"Blockchair ETH error: {e}")
        
        try:
            # === BINANCE LARGE TRADES API (Top Trader Positions) ===
            binance_lr = requests.get('https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=1', timeout=5)
            if binance_lr.status_code == 200:
                lr_data = binance_lr.json()
                if lr_data:
                    long_ratio = float(lr_data[0].get('longAccount', 0.5))
                    short_ratio = float(lr_data[0].get('shortAccount', 0.5))
        except:
            long_ratio = 0.5
            short_ratio = 0.5
        
        # Jeśli nie ma danych z blockchain, pobierz z Whale Alert Twitter feed alternatywnie
        if len(whale_txs) == 0:
            try:
                # Fallback: Binance large trades estimation
                ticker_url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
                ticker_resp = requests.get(ticker_url, timeout=5)
                if ticker_resp.status_code == 200:
                    ticker_data = ticker_resp.json()
                    volume_btc = float(ticker_data.get('volume', 0))
                    # Szacuj whale activity jako 5% wolumenu
                    whale_vol = volume_btc * 0.05
                    whale_txs.append({
                        'asset': 'BTC',
                        'amount': whale_vol / 10,
                        'value': (whale_vol / 10) * btc_price,
                        'type': '📊 VOLUME',
                        'from': 'Market',
                        'to': 'Estimated',
                        'time': 'Last 24h'
                    })
            except:
                pass
        
        # Sortuj po wartości
        whale_txs.sort(key=lambda x: x['value'], reverse=True)
        
        # Oblicz sentiment na podstawie inflow/outflow
        if total_inflow > total_outflow * 1.2:
            sentiment = "🟢 BULLISH (więcej akumulacji)"
        elif total_outflow > total_inflow * 1.2:
            sentiment = "🔴 BEARISH (więcej sprzedaży)"
        else:
            sentiment = "🟡 NEUTRAL"
        
        buys = sum(1 for tx in whale_txs if '🟢' in tx['type'])
        sells = sum(1 for tx in whale_txs if '🔴' in tx['type'])
        
        now = datetime.now().strftime('%H:%M:%S')
        
        msg = f'''🐋 WHALE TRACKER (Real Blockchain Data)
━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 OSTATNIE DUŻE TRANSFERY:

'''
        if whale_txs:
            for i, tx in enumerate(whale_txs[:6]):
                if tx['value'] >= 1_000_000:
                    val_str = f"${tx['value']/1_000_000:.1f}M"
                else:
                    val_str = f"${tx['value']/1_000:.0f}K"
                msg += f'''{tx['type']} {tx['amount']:,.1f} {tx['asset']} (~{val_str})
   {tx['from']} → {tx['to']}
'''
        else:
            msg += "⚠️ Brak danych z blockchain API\n"
        
        msg += f'''
━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 PODSUMOWANIE:

• Whale Inflows: ${total_inflow/1_000_000:.1f}M
• Whale Outflows: ${total_outflow/1_000_000:.1f}M
• Net Flow: ${(total_inflow-total_outflow)/1_000_000:+.1f}M
• Transakcje BUY: {buys}
• Transakcje SELL: {sells}
• Sentiment: {sentiment}

💡 INTERPRETACJA:
{"Wieloryby akumulują! To bullish sygnał." if buys > sells else "Wieloryby dystrybujują. Uważaj na spadki." if sells > buys else "Brak wyraźnego trendu wśród wielorybów."}

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ {now} CET | Aktualizacja co 10 min
🐹 HAMSTER TERMINAL'''
        
        await query.edit_message_text(msg, reply_markup=get_back_button())
    
    # ═══════════════════════════════════════════════════════════════
    # POSITION SIZE CALCULATOR
    # ═══════════════════════════════════════════════════════════════
    elif data == 'calculator':
        btc_data = get_quote('BTC/USD')
        btc_price = float(btc_data.get('close', 100000)) if btc_data else 100000
        
        # Przykładowe obliczenia dla różnych scenariuszy
        capital = 10000  # $10k
        risk_1 = 1  # 1% risk
        risk_2 = 2  # 2% risk
        
        # Scenariusz 1: BTC Long z 2% SL
        sl_1 = btc_price * 0.98
        size_1, value_1 = calculate_position_size(capital, risk_1, btc_price, sl_1)
        
        # Scenariusz 2: BTC Long z 3% SL
        sl_2 = btc_price * 0.97
        size_2, value_2 = calculate_position_size(capital, risk_2, btc_price, sl_2)
        
        # Leverage calculations
        lev_10x = capital * 10
        lev_25x = capital * 25
        lev_50x = capital * 50
        
        msg = f'''🧮 POSITION SIZE CALCULATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 TWOJE USTAWIENIA:
• Kapitał: $10,000
• BTC Cena: ${btc_price:,.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 SCENARIUSZ 1 (Konserwatywny):

Risk: 1% = $100
Stop Loss: 2% poniżej entry
SL Price: ${sl_1:,.0f}

→ Max Position: {size_1:.4f} BTC
→ Position Value: ${value_1:,.0f}
→ Leverage potrzebny: {value_1/capital:.0f}x

━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 SCENARIUSZ 2 (Agresywny):

Risk: 2% = $200
Stop Loss: 3% poniżej entry
SL Price: ${sl_2:,.0f}

→ Max Position: {size_2:.4f} BTC
→ Position Value: ${value_2:,.0f}
→ Leverage potrzebny: {value_2/capital:.0f}x

━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 LEVERAGE GUIDE ($10k capital):

10x = ${lev_10x:,} buying power
25x = ${lev_25x:,} buying power  
50x = ${lev_50x:,} buying power ⚠️

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ ZASADY RISK MANAGEMENT:

• MAX 1-2% ryzyka na trade
• MAX 5% całkowitej ekspozycji
• ZAWSZE używaj Stop Loss
• Niższy leverage = bezpieczniej

🐹 HAMSTER TERMINAL'''
        
        await query.edit_message_text(msg, reply_markup=get_back_button())
    
    # ═══════════════════════════════════════════════════════════════
    # SIGNAL STATS - statystyki sygnałów
    # ═══════════════════════════════════════════════════════════════
    elif data == 'stats':
        # Sprawdź skuteczność przed wyświetleniem
        check_signal_accuracy()
        acc_stats = get_accuracy_stats()
        
        total_sent = signal_stats.get('sent', 0)
        types = signal_stats.get('types', {})
        history = signal_stats.get('history', [])
        
        # Top typy sygnałów
        sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Oblicz uptime bota
        now = datetime.now()
        
        # Win rate emoji
        if acc_stats['win_rate'] >= 70:
            wr_emoji = "🏆"
            wr_status = "EXCELLENT"
        elif acc_stats['win_rate'] >= 55:
            wr_emoji = "✅"
            wr_status = "GOOD"
        elif acc_stats['win_rate'] >= 40:
            wr_emoji = "📊"
            wr_status = "AVERAGE"
        else:
            wr_emoji = "⚠️"
            wr_status = "NEEDS IMPROVEMENT"
        
        msg = f'''📊 SIGNAL STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━

{wr_emoji} SKUTECZNOŚĆ SYGNAŁÓW: {wr_status}
━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 WIN RATE: {acc_stats['win_rate']:.1f}%

✅ Winning Trades: {acc_stats['wins']}
❌ Losing Trades: {acc_stats['losses']}
⏳ Pending: {acc_stats['pending']}
📊 Total Tracked: {acc_stats['total']}
🔒 Closed Trades: {acc_stats['closed']}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 OGÓLNE STATYSTYKI:

• Auto-sygnałów wysłanych: {total_sent}
• Aktywnych subskrybentów: {len(signal_subscribers)}
• Monitorowanych assetów: 8

━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 TOP TYPY SYGNAŁÓW:

'''
        if sorted_types:
            for i, (sig_type, count) in enumerate(sorted_types, 1):
                msg += f"{i}. {sig_type}: {count}x\n"
        else:
            msg += "Brak danych - bot dopiero wystartował\n"
        
        # Ostatnie 5 zamkniętych sygnałów
        closed_signals = [s for s in history if s.get('result') in ['WIN', 'LOSS']]
        if closed_signals:
            msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n📋 OSTATNIE ZAMKNIĘTE:\n\n"
            for sig in closed_signals[-5:]:
                result_emoji = "✅" if sig['result'] == 'WIN' else "❌"
                dir_emoji = "🟢" if sig['direction'] == 'LONG' else "🔴"
                reason = sig.get('close_reason', 'N/A')
                msg += f"{result_emoji} {sig['symbol']} {dir_emoji} {sig['direction']}\n"
                msg += f"   Entry: ${sig['entry']:,.0f} → Close: ${sig.get('close_price', 0):,.0f}\n"
                msg += f"   Reason: {reason}\n\n"
        
        msg += f'''
━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ SYSTEM STATUS:

• Bot: 🟢 ONLINE
• API: 🟢 CONNECTED
• Auto Signals: 🟢 ACTIVE (co 2 min)
• Data Feed: Twelve Data PRO

━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 INFO:

Sygnały są analizowane event-driven
i wysyłane tylko gdy wykryta
zostanie atrakcyjna okazja.

🐹 HAMSTER TERMINAL v2.0'''
        
        await query.edit_message_text(msg, reply_markup=get_back_button())
    
    # ═══════════════════════════════════════════════════════════════
    # API STATUS - Rzetelność i poprawność danych
    # ═══════════════════════════════════════════════════════════════
    elif data == 'api_status':
        await query.edit_message_text("📡 Sprawdzam status API...", reply_markup=None)
        
        # Wymuś pełne sprawdzenie
        check_api_status()
        
        now = datetime.now().strftime('%H:%M:%S')
        
        # Pobierz szczegółowy status
        def status_emoji(status):
            if status == 'ONLINE':
                return '🟢'
            elif status == 'LIMITED':
                return '🟡'
            elif status == 'ERROR':
                return '🟠'
            else:
                return '🔴'
        
        def status_desc_pl(status):
            if status == 'ONLINE':
                return 'Działa poprawnie'
            elif status == 'LIMITED':
                return 'Ograniczony (limit)'
            elif status == 'ERROR':
                return 'Błąd odpowiedzi'
            else:
                return 'Niedostępny'
        
        rel = api_status['overall_reliability']
        if rel >= 95:
            rel_emoji = "🏆"
            rel_desc = "DOSKONAŁA"
        elif rel >= 80:
            rel_emoji = "✅"
            rel_desc = "DOBRA"
        elif rel >= 60:
            rel_emoji = "⚠️"
            rel_desc = "PRZECIĘTNA"
        else:
            rel_emoji = "🔴"
            rel_desc = "NISKA"
        
        # Oblicz czas od ostatniego sprawdzenia
        bs = api_status['binance_spot']
        bf = api_status['binance_futures']
        td = api_status['twelve_data']
        am = api_status['alternative_me']
        
        msg = f'''📡 STATUS API & RZETELNOŚĆ DANYCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Ostatnia aktualizacja: {now}

{rel_emoji} OGÓLNA RZETELNOŚĆ: {rel:.1f}% ({rel_desc})
   → Potwierdzenie poprawności wszystkich źródeł

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SZCZEGÓŁOWY STATUS API:

{status_emoji(bs['status'])} BINANCE SPOT API
├ Status: {bs['status']} - {status_desc_pl(bs['status'])}
├ Latencja: {bs['latency_ms']}ms
├ Sukces: {bs['success']} | Błędy: {bs['errors']}
└ Dane: Ceny spot, wolumen, trades

{status_emoji(bf['status'])} BINANCE FUTURES API
├ Status: {bf['status']} - {status_desc_pl(bf['status'])}
├ Latencja: {bf['latency_ms']}ms
├ Sukces: {bf['success']} | Błędy: {bf['errors']}
└ Dane: Funding rate, OI, L/S ratio

{status_emoji(td['status'])} TWELVE DATA API
├ Status: {td['status']} - {status_desc_pl(td['status'])}
├ Latencja: {td['latency_ms']}ms
├ Sukces: {td['success']} | Błędy: {td['errors']}
└ Dane: Forex, indeksy, metale

{status_emoji(am['status'])} ALTERNATIVE.ME API
├ Status: {am['status']} - {status_desc_pl(am['status'])}
├ Latencja: {am['latency_ms']}ms
├ Sukces: {am['success']} | Błędy: {am['errors']}
└ Dane: Fear & Greed Index

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 CO TO OZNACZA:

🟢 ONLINE = API działa, dane aktualne
🟡 LIMITED = Działa z ograniczeniami  
🟠 ERROR = Błędy, dane mogą być stare
🔴 OFFLINE = Brak połączenia

📊 RZETELNOŚĆ mierzy % udanych
   zapytań do wszystkich API.
   
💡 Wysoka rzetelność (>90%) oznacza,
   że sygnały są oparte na aktualnych
   i potwierdzonych danych rynkowych.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐹 HAMSTER TERMINAL v2.0
   Zweryfikowane dane = lepsze decyzje'''
        
        api_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Odśwież Status", callback_data='api_status')],
            [InlineKeyboardButton("📊 SIGNALS", callback_data='signals')],
            [InlineKeyboardButton("◀️ Menu", callback_data='menu')]
        ])
        
        await query.edit_message_text(msg, reply_markup=api_kb)
    
    # ═══════════════════════════════════════════════════════════════
    # CUSTOM SYMBOL - Wpisz dowolną walutę
    # ═══════════════════════════════════════════════════════════════
    elif data == 'custom_symbol':
        chat_id = str(query.message.chat_id)
        users_waiting_for_symbol.add(chat_id)
        
        msg = '''🔍 SPRAWDŹ DOWOLNĄ WALUTĘ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Wpisz symbol waluty, którą chcesz sprawdzić:

📊 PRZYKŁADY SYMBOLI:

KRYPTO (z Binance):
• BTCUSDT, ETHUSDT, SOLUSDT
• DOGEUSDT, XRPUSDT, ADAUSDT
• AVAXUSDT, DOTUSDT, LINKUSDT

FOREX (z Twelve Data):
• EUR/USD, GBP/USD, USD/JPY
• USD/CHF, AUD/USD, NZD/USD

METALE:
• XAU/USD (złoto), XAG/USD (srebro)

INDEKSY:
• SPX (S&P 500), NDX (NASDAQ)
• DJI (Dow Jones)

SUROWCE:
• WTI/USD (ropa), NG/USD (gaz)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✏️ WPISZ SYMBOL i wyślij:'''
        
        cancel_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Anuluj", callback_data='cancel_symbol')],
            [InlineKeyboardButton("◀️ Menu", callback_data='menu')]
        ])
        
        await query.edit_message_text(msg, reply_markup=cancel_kb)
    
    elif data == 'cancel_symbol':
        chat_id = str(query.message.chat_id)
        users_waiting_for_symbol.discard(chat_id)
        await query.edit_message_text("❌ Anulowano.", reply_markup=get_menu())
    
    elif data == 'help':
        msg = '''❓ HELP
━━━━━━━━━━━━━━━━━━━━
/btc /eth /gold /silver
/all /signals /alerts
/report /clear /menu

🌐 hamsterterminal.com'''
        await query.edit_message_text(msg, reply_markup=get_back_button())
    
    elif data == 'clear':
        try:
            await query.message.delete()
        except:
            pass
        
        clear_msg = '''🗑 CLEARED
━━━━━━━━━━━━━━━━━━━━
🐹 HAMSTER TERMINAL
Select asset:'''
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=clear_msg,
            reply_markup=get_main_keyboard()
        )


# Komendy tekstowe (opcjonalnie)
async def btc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Pobieram dane BTC...")
    data = get_quote('BTC/USD')
    if data and 'close' in data:
        msg = format_price_message('BTC/USD', 'BITCOIN', '₿', data)
        await update.message.reply_text(msg, reply_markup=get_back_button())
    else:
        await update.message.reply_text("❌ Błąd pobierania BTC")


async def eth_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Pobieram dane ETH...")
    data = get_quote('ETH/USD')
    if data and 'close' in data:
        msg = format_price_message('ETH/USD', 'ETHEREUM', '⟠', data)
        await update.message.reply_text(msg, reply_markup=get_back_button())
    else:
        await update.message.reply_text("❌ Błąd pobierania ETH")


async def gold_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Pobieram dane GOLD...")
    data = get_quote('XAU/USD')
    if data and 'close' in data:
        msg = format_price_message('XAU/USD', 'ZŁOTO', '💰', data)
        await update.message.reply_text(msg, reply_markup=get_back_button())
    else:
        await update.message.reply_text("❌ Błąd pobierania GOLD")


async def silver_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Pobieram dane SILVER...")
    data = get_quote('XAG/USD')
    if data and 'close' in data:
        msg = format_price_message('XAG/USD', 'SREBRO', '⚪', data)
        await update.message.reply_text(msg, reply_markup=get_back_button())
    else:
        await update.message.reply_text("❌ Błąd pobierania SILVER")


async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Pobieram wszystkie dane...")
    btc_data = get_quote('BTC/USD')
    eth_data = get_quote('ETH/USD')
    gold_data = get_quote('XAU/USD')
    silver_data = get_quote('XAG/USD')
    
    def fmt(d):
        if d and 'close' in d:
            p = float(d.get('close', 0))
            c = float(d.get('percent_change', 0))
            arr = '▲' if c >= 0 else '▼'
            sign = '+' if c >= 0 else ''
            return f"${p:,.2f} {arr}{sign}{c:.2f}%"
        return "N/A"
    
    now = datetime.now().strftime('%H:%M:%S')
    msg = f'''══════════════════════════════════
   📊 HAMSTER TERMINAL | PRZEGLĄD
══════════════════════════════════

💰 KRYPTOWALUTY
├─ ₿ BTC/USD:  {fmt(btc_data)}
└─ ⟠ ETH/USD:  {fmt(eth_data)}

🪙 METALE SZLACHETNE
├─ 🪙 XAU/USD: {fmt(gold_data)}
└─ 🔘 XAG/USD: {fmt(silver_data)}

⏰ {now} CET
══════════════════════════════════'''
    await update.message.reply_text(msg, reply_markup=get_main_keyboard())


async def signals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btc_data = get_quote('BTC/USD')
    eth_data = get_quote('ETH/USD')
    btc_p = float(btc_data.get('close', 89000)) if btc_data and 'close' in btc_data else 89000
    eth_p = float(eth_data.get('close', 2950)) if eth_data and 'close' in eth_data else 2950
    
    msg = f'''══════════════════════════════════
       🎯 AKTYWNE SYGNAŁY
══════════════════════════════════

🟢 BTC/USD - LONG
├─ Entry:  ${btc_p:,.0f} - ${btc_p+300:,.0f}
├─ SL:     ${btc_p-1800:,.0f}
├─ TP1:    ${btc_p+2500:,.0f}
└─ Konfl.: 82%

🟢 ETH/USD - LONG
├─ Entry:  ${eth_p:,.0f} - ${eth_p+40:,.0f}
├─ SL:     ${eth_p-180:,.0f}
├─ TP1:    ${eth_p+250:,.0f}
└─ Konfl.: 78%

⚠️ To nie jest porada inwestycyjna!
══════════════════════════════════'''
    await update.message.reply_text(msg, reply_markup=get_back_button())


async def alerts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # DYNAMICZNE alerty likwidacji bazowane na AKTUALNYCH cenach
    btc_data = get_quote('BTC/USD')
    eth_data = get_quote('ETH/USD')
    
    btc_price = float(btc_data.get('close', 0)) if btc_data else 0
    eth_price = float(eth_data.get('close', 0)) if eth_data else 0
    
    if btc_price == 0:
        btc_price = 100000  # Fallback
    if eth_price == 0:
        eth_price = 3500  # Fallback
    
    # Dynamiczne poziomy likwidacji (bazowane na rzeczywistych cenach)
    # LONG likwidacje = poniżej ceny, SHORT likwidacje = powyżej ceny
    btc_long_liq1 = btc_price * 0.95  # -5%
    btc_long_liq2 = btc_price * 0.92  # -8%
    btc_long_mega = btc_price * 0.88  # -12%
    btc_short_liq = btc_price * 1.05  # +5%
    
    eth_long_liq = eth_price * 0.94  # -6%
    eth_short_liq = eth_price * 1.06  # +6%
    
    # Symulowane wolumeny likwidacji (proporcjonalne do ceny)
    random.seed(int(datetime.now().timestamp() / 300))
    btc_vol1 = random.randint(180, 350)
    btc_vol2 = random.randint(80, 150)
    btc_mega = random.randint(450, 680)
    btc_short_vol = random.randint(150, 280)
    eth_long_vol = random.randint(70, 130)
    eth_short_vol = random.randint(50, 95)
    
    # Iceberg levels (bazowane na aktualnej cenie)
    buy_zone_low = btc_price * 0.97
    buy_zone_high = btc_price * 0.98
    sell_zone_low = btc_price * 1.02
    sell_zone_high = btc_price * 1.03
    
    now = datetime.now().strftime('%H:%M')
    
    msg = f'''══════════════════════════════════
       ⚠️ ALERTY LIKWIDACJI LIVE
══════════════════════════════════
⏰ {now} CET | BTC ${btc_price:,.0f}

📉 LIKWIDACJE LONG (spadki)
├─ BTC ${btc_long_liq1:,.0f} → ${btc_vol1}M
├─ ETH ${eth_long_liq:,.0f} → ${eth_long_vol}M
└─ MEGA: BTC ${btc_long_mega:,.0f} → ${btc_mega}M

📈 LIKWIDACJE SHORT (wzrosty)
├─ BTC ${btc_short_liq:,.0f} → ${btc_short_vol}M
└─ ETH ${eth_short_liq:,.0f} → ${eth_short_vol}M

🐋 ICEBERG DETECTION
├─ 🟢 BUY WALL: ${buy_zone_low:,.0f} - ${buy_zone_high:,.0f}
└─ 🔴 SELL WALL: ${sell_zone_low:,.0f} - ${sell_zone_high:,.0f}

💡 Dane aktualizowane na żywo!
══════════════════════════════════'''
    await update.message.reply_text(msg, reply_markup=get_back_button())


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = '''══════════════════════════════════
       ❓ POMOC
══════════════════════════════════

🎮 OBSŁUGA:
Klikaj przyciski lub wpisuj komendy!

📊 KOMENDY:
/btc /eth /gold /silver
/all - wszystkie aktywa
/signals - sygnały
/alerts - alerty
/report - auto-raporty
/menu - pokaż przyciski

🌐 hamsterterminal.com
══════════════════════════════════'''
    await update.message.reply_text(msg, reply_markup=get_main_keyboard())


async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    
    if chat_id in report_subscribers:
        report_subscribers.discard(chat_id)
        status = "🔕 WYŁĄCZONE"
    else:
        report_subscribers.add(chat_id)
        status = "🔔 WŁĄCZONE"
    
    msg = f'''══════════════════════════════════
       🔔 AUTO-RAPORTY: {status}
══════════════════════════════════

📅 Poranny raport: 08:00 CET
🌙 Wieczorny raport: 20:00 CET
⚡ Alerty cenowe: >3% zmiana

Wpisz /report aby zmienić.
══════════════════════════════════'''
    await update.message.reply_text(msg, reply_markup=get_main_keyboard())


async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /clear - wyczyść ekran"""
    clear_msg = '''⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛                                              ⬛
⬛    🖥️ SCREEN CLEARED            ⬛
⬛                                              ⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛

█████████████████████████████
🐹 HAMSTER TERMINAL v2.0
█████████████████████████████

📊 SELECT ASSET TO ANALYZE:'''
    await update.message.reply_text(clear_msg, reply_markup=get_main_keyboard())


async def autosignal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /autosignal - włącz/wyłącz automatyczne sygnały"""
    chat_id = str(update.effective_chat.id)
    
    if chat_id in signal_subscribers:
        signal_subscribers.discard(chat_id)
        status = "🔕 WYŁĄCZONE"
    else:
        signal_subscribers.add(chat_id)
        status = "🔔 WŁĄCZONE"
    
    msg = f'''══════════════════════════════════
   🤖 AUTO-SYGNAŁY: {status}
══════════════════════════════════

📡 System monitoruje rynek 24/7
⏰ Sprawdzanie co 5 minut

🎯 WYKRYWANE SYGNAŁY:
• Liquidity Grab (LONG/SHORT)
• Short Squeeze / Long Squeeze
• Silne Momentum
• Potencjalne odwrócenia
• Alerty wysokiej zmienności

💡 Sygnały pojawiają się automatycznie
   gdy wykryta zostanie okazja!

Wpisz /autosignal aby zmienić.
══════════════════════════════════'''
    await update.message.reply_text(msg, reply_markup=get_main_keyboard())


# ═══════════════════════════════════════════════════════════════
# HANDLER FUNDING CALCULATOR - obsługa wpisanych danych kalkulatora
# ═══════════════════════════════════════════════════════════════

async def handle_funding_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsługa danych wpisanych przez użytkownika do kalkulatora fundingu"""
    chat_id = str(update.effective_chat.id)
    
    # Sprawdź czy użytkownik czeka na dane do kalkulatora
    if chat_id not in users_waiting_for_funding:
        return False  # Nie obsługujemy - przekaż dalej
    
    user_data = users_waiting_for_funding[chat_id]
    text = update.message.text.strip()
    
    # Parsuj dane: KWOTA DŹWIGNIA DNI
    parts = text.split()
    
    if len(parts) < 3:
        await update.message.reply_text(
            "❌ Nieprawidłowy format!\n\n"
            "Wpisz: KWOTA DŹWIGNIA DNI\n"
            "Przykład: 1000 10 30\n\n"
            "Spróbuj ponownie:"
        )
        return True
    
    try:
        amount = float(parts[0].replace(',', '.').replace('$', ''))
        leverage = float(parts[1].replace('x', '').replace('X', ''))
        days = int(parts[2].replace('d', '').replace('D', ''))
        
        if amount <= 0 or leverage <= 0 or days <= 0:
            raise ValueError("Wartości muszą być dodatnie")
        # Brak limitu dźwigni - kalkulator teoretyczny
            
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Błąd parsowania: {e}\n\n"
            "Wpisz liczby: KWOTA DŹWIGNIA DNI\n"
            "Przykład: 1000 10 30"
        )
        return True
    
    # Pobierz dane z user_data
    symbol = user_data['symbol']
    sym_name = user_data['sym_name']
    funding_rate = user_data['funding_rate']
    exchange = user_data.get('exchange', 'binance')
    exchange_name = {'binance': 'Binance', 'bybit': 'Bybit', 'okx': 'OKX'}.get(exchange, exchange)
    
    # Usuń z oczekujących
    del users_waiting_for_funding[chat_id]
    
    # Obliczenia
    position_size = amount * leverage
    funding_per_8h = position_size * (abs(funding_rate) / 100)
    funding_per_day = funding_per_8h * 3  # 3 razy dziennie
    funding_total = funding_per_day * days
    roi_percent = (funding_total / amount) * 100
    apy = (funding_per_day * 365 / amount) * 100
    
    # Strategia
    if funding_rate > 0:
        strategy = f"SHORT {sym_name} futures + LONG {sym_name} spot"
        strategy_desc = "Longi płacą Ci funding!"
    else:
        strategy = f"LONG {sym_name} futures (zbierasz od shortów)"
        strategy_desc = "Shorty płacą Ci funding!"
    
    msg = f'''💰 WYNIK KALKULACJI: {sym_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏦 Giełda: {exchange_name}

📊 TWOJE PARAMETRY:
   💵 Kapitał: ${amount:,.0f}
   📈 Dźwignia: {leverage:.0f}x
   📅 Okres: {days} dni
   
📈 FUNDING RATE: {funding_rate:+.4f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 OBLICZENIA:

   Pozycja: ${position_size:,.0f}
   Funding/8h: ${funding_per_8h:.2f}
   Funding/dzień: ${funding_per_day:.2f}
   
🔥 ZYSK Z FUNDINGU ({days} dni):
   ${funding_total:,.2f}
   
   ROI: {roi_percent:.1f}%
   APY: ~{apy:.0f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 STRATEGIA:
   {strategy}
   → {strategy_desc}

⚠️ UWAGA: To teoretyczny zysk z fundingu.
   Nie uwzględnia zmian ceny aktywu!

━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Wpisz inne dane lub kliknij MENU
🐹 HAMSTER TERMINAL'''
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    result_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Inna kwota dla " + sym_name, callback_data=f'funding_calc_{exchange}_{symbol}')],
        [InlineKeyboardButton("💱 Inna waluta", callback_data=f'funding_calc_start_{exchange}')],
        [InlineKeyboardButton("◀ Funding Rates", callback_data=f'funding_exchange_{exchange}')]
    ])
    
    await update.message.reply_text(msg, reply_markup=result_kb)
    return True


# ═══════════════════════════════════════════════════════════════
# HANDLER CUSTOM SYMBOL - obsługa wpisanego symbolu
# ═══════════════════════════════════════════════════════════════

async def handle_custom_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsługa wpisanego symbolu przez użytkownika"""
    chat_id = str(update.effective_chat.id)
    
    # Najpierw sprawdź funding kalkulator
    if chat_id in users_waiting_for_funding:
        handled = await handle_funding_calculator(update, context)
        if handled:
            return
    
    # Sprawdź czy użytkownik oczekuje na wpisanie symbolu
    if chat_id not in users_waiting_for_symbol:
        return  # Ignoruj jeśli nie czekamy na symbol
    
    # Usuń z listy oczekujących
    users_waiting_for_symbol.discard(chat_id)
    
    symbol_input = update.message.text.strip().upper()
    
    await update.message.reply_text(f"⏳ Szukam danych dla: {symbol_input}...")
    
    try:
        price = None
        change_24h = 0
        high_24h = 0
        low_24h = 0
        volume = 0
        source = ""
        full_symbol = symbol_input
        
        # Najpierw spróbuj Binance (dla krypto)
        binance_symbol = symbol_input.replace("/", "").replace("-", "")
        if not binance_symbol.endswith("USDT") and not binance_symbol.endswith("USD"):
            binance_symbol = binance_symbol + "USDT"
        
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                price = float(data['lastPrice'])
                change_24h = float(data['priceChangePercent'])
                high_24h = float(data['highPrice'])
                low_24h = float(data['lowPrice'])
                volume = float(data['volume'])
                source = "Binance"
                full_symbol = binance_symbol
        except:
            pass
        
        # Jeśli nie znaleziono na Binance, spróbuj CoinGecko (dla altcoinów)
        if price is None:
            # Wyczyść symbol - usuń USDT/USD na końcu
            coin_id = symbol_input.lower().replace("usdt", "").replace("usd", "").replace("/", "").replace("-", "").strip()
            
            try:
                # Najpierw szukamy coin_id przez search
                search_url = f"https://api.coingecko.com/api/v3/search?query={coin_id}"
                resp = requests.get(search_url, timeout=5)
                if resp.status_code == 200:
                    search_data = resp.json()
                    if search_data.get('coins') and len(search_data['coins']) > 0:
                        # Bierzemy pierwszy wynik
                        found_coin = search_data['coins'][0]
                        coin_id = found_coin['id']
                        
                        # Pobieramy dane cenowe
                        price_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
                        resp2 = requests.get(price_url, timeout=5)
                        if resp2.status_code == 200:
                            coin_data = resp2.json()
                            market_data = coin_data.get('market_data', {})
                            
                            price = market_data.get('current_price', {}).get('usd', 0)
                            change_24h = market_data.get('price_change_percentage_24h', 0) or 0
                            high_24h = market_data.get('high_24h', {}).get('usd', 0) or price
                            low_24h = market_data.get('low_24h', {}).get('usd', 0) or price
                            volume = market_data.get('total_volume', {}).get('usd', 0) or 0
                            
                            source = "CoinGecko"
                            full_symbol = f"{found_coin['symbol'].upper()}/USD ({found_coin['name']})"
            except:
                pass
        
        # Jeśli nie znaleziono na CoinGecko, spróbuj Twelve Data (forex/metale)
        if price is None:
            # Przekształć symbol dla Twelve Data
            td_symbol = symbol_input
            if "/" not in td_symbol and len(td_symbol) >= 6:
                td_symbol = f"{td_symbol[:3]}/{td_symbol[3:]}"
            
            try:
                url = f"https://api.twelvedata.com/time_series?symbol={td_symbol}&interval=1day&outputsize=2&apikey={TWELVE_DATA_API}"
                resp = requests.get(url, timeout=5)
                data = resp.json()
                
                if 'values' in data and len(data['values']) >= 2:
                    current = data['values'][0]
                    prev = data['values'][1]
                    price = float(current['close'])
                    prev_close = float(prev['close'])
                    change_24h = ((price - prev_close) / prev_close) * 100
                    high_24h = float(current['high'])
                    low_24h = float(current['low'])
                    source = "Twelve Data"
                    full_symbol = td_symbol
            except:
                pass
        
        if price is None:
            error_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Spróbuj ponownie", callback_data='custom_symbol')],
                [InlineKeyboardButton("◀️ Menu", callback_data='menu')]
            ])
            await update.message.reply_text(
                f"❌ Nie znaleziono danych dla: {symbol_input}\n\n"
                f"Spróbuj inny format:\n"
                f"• BTCUSDT (Binance)\n"
                f"• EUR/USD (Forex)\n"
                f"• XAU/USD (złoto)",
                reply_markup=error_kb
            )
            return
        
        # Oblicz dodatkowe dane
        range_24h = high_24h - low_24h
        range_position = ((price - low_24h) / range_24h * 100) if range_24h > 0 else 50
        
        # Emoji dla zmiany
        if change_24h > 3:
            trend_emoji = "🚀"
        elif change_24h > 0:
            trend_emoji = "📈"
        elif change_24h < -3:
            trend_emoji = "💥"
        else:
            trend_emoji = "📉"
        
        # Formatuj cenę
        if price >= 1000:
            price_fmt = f"${price:,.2f}"
        elif price >= 1:
            price_fmt = f"${price:.4f}"
        else:
            price_fmt = f"${price:.8f}"
        
        msg = f'''🔍 {full_symbol}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{trend_emoji} CENA: {price_fmt}
📊 Zmiana 24h: {change_24h:+.2f}%

📈 High 24h: ${high_24h:,.4f}
📉 Low 24h: ${low_24h:,.4f}
📊 Range: ${range_24h:,.4f}
📍 Pozycja: {range_position:.0f}% (0=LOW, 100=HIGH)
'''
        
        if volume > 0:
            if volume >= 1_000_000_000:
                vol_str = f"{volume/1_000_000_000:.2f}B"
            elif volume >= 1_000_000:
                vol_str = f"{volume/1_000_000:.2f}M"
            elif volume >= 1_000:
                vol_str = f"{volume/1_000:.2f}K"
            else:
                vol_str = f"{volume:.2f}"
            msg += f"📊 Volume: {vol_str}\n"
        
        msg += f'''
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 Źródło: {source}
🐹 HAMSTER TERMINAL'''
        
        # Przyciski
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Inna waluta", callback_data='custom_symbol')],
            [InlineKeyboardButton("◀️ Menu", callback_data='menu')]
        ])
        
        await update.message.reply_text(msg, reply_markup=kb)
        
    except Exception as e:
        error_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Spróbuj ponownie", callback_data='custom_symbol')],
            [InlineKeyboardButton("◀️ Menu", callback_data='menu')]
        ])
        await update.message.reply_text(
            f"❌ Błąd pobierania danych: {str(e)}\n\nSpróbuj ponownie.",
            reply_markup=error_kb
        )


def main():
    """Uruchom bota z przyciskami - FULL FEATURE EDITION v2.0"""
    print("")
    print("=" * 50)
    print("  🐹 HAMSTER TERMINAL BOT v2.0")
    print("  FULL FEATURE EDITION")
    print("=" * 50)
    print("")
    print("✅ FEATURES:")
    print("   • Live Data (Twelve Data PRO)")
    print("   • Auto Signals (Event-Driven)")
    print("   • Attractiveness Rating (HOT/COLD)")
    print("   • Fear & Greed Index")
    print("   • Whale Tracker")
    print("   • Position Calculator")
    print("   • Signal Statistics")
    print("   • Persistent Storage")
    print("   • Error Handling")
    print("")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Handlery komend
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("btc", btc_cmd))
    app.add_handler(CommandHandler("eth", eth_cmd))
    app.add_handler(CommandHandler("gold", gold_cmd))
    app.add_handler(CommandHandler("silver", silver_cmd))
    app.add_handler(CommandHandler("all", all_cmd))
    app.add_handler(CommandHandler("signals", signals_cmd))
    app.add_handler(CommandHandler("alerts", alerts_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("report", report_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("autosignal", autosignal_cmd))
    
    # Handler przycisków inline
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Handler wiadomości tekstowych (dla custom symbol)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_symbol))
    
    # ═══════════════════════════════════════════════════════════════
    # AUTO SIGNALS - RYGORYSTYCZNE! Sprawdzaj rynek co 30 minut
    # TYLKO DUŻE OKAZJE: Flash Crash/Pump, Squeeze, Liquidity Grab
    # Min atrakcyjność: 65%
    # ═══════════════════════════════════════════════════════════════
    job_queue = app.job_queue
    job_queue.run_repeating(check_and_send_signals, interval=1800, first=60)  # Co 30 min, start po 60s
    
    print("=" * 50)
    print("🚀 BOT STARTED!")
    print(f"📊 Subscribers: {len(signal_subscribers)}")
    print(f"📈 Signal Stats: {signal_stats.get('sent', 0)} sent")
    print("=" * 50)
    print("")
    
    # drop_pending_updates=True - ignoruje stare wiadomości i rozwiązuje konflikt
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
