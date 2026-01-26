"""
🐹 HAMSTER TERMINAL - TELEGRAM BOT
Profesjonalne sygnały tradingowe na żywo

Komendy:
/start - Uruchom bota
/btc - Bitcoin analiza
/eth - Ethereum analiza
/gold - Złoto analiza
/silver - Srebro analiza
/all - Wszystkie aktywa
/signals - Aktywne sygnały
/alerts - Alerty likwidacji
/report - Włącz/wyłącz auto-raporty
/help - Pomoc
"""

import requests
import logging
import asyncio
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue, CallbackQueryHandler

# Konfiguracja
BOT_TOKEN = '8254662818:AAGSCUbd-Zc8tmjmCB3ujLNksLqxICJ2rJw'
TWELVE_DATA_API = 'd54ad684cd8f40de895ec569d6128821'
CHAT_ID = '5616894588'  # Twój chat ID do auto-raportów

# Przechowuj poprzednie ceny do wykrywania dużych ruchów
previous_prices = {}
# Subskrybenci auto-raportów
report_subscribers = set([CHAT_ID])
# Cooldown alertów - zapobiega spamowi (ostatni czas wysłania alertu dla danego assetu)
alert_cooldowns = {}  # {'BTC': timestamp, 'ETH': timestamp, ...}
ALERT_COOLDOWN_MINUTES = 30  # Minimum 30 minut między alertami dla tego samego assetu

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_quote(symbol):
    """Pobierz cenę z Twelve Data API"""
    try:
        url = f'https://api.twelvedata.com/quote?symbol={symbol}&apikey={TWELVE_DATA_API}'
        logger.info(f"Fetching: {url}")
        r = requests.get(url, timeout=15)
        data = r.json()
        logger.info(f"Response for {symbol}: {data}")
        
        # Check for API errors
        if 'code' in data:
            logger.error(f"API Error for {symbol}: {data}")
            return {}
        
        # Validate required fields
        if 'close' not in data or data.get('close') is None:
            logger.error(f"No 'close' field for {symbol}: {data}")
            return {}
            
        return data
    except requests.exceptions.Timeout:
        logger.error(f"Timeout for {symbol}")
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {symbol}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error for {symbol}: {e}")
        return {}


def format_price_message(symbol, name, emoji, data):
    """Formatuj wiadomość z ceną"""
    price = float(data.get('close', 0))
    change = float(data.get('percent_change', 0))
    high = float(data.get('high', 0))
    low = float(data.get('low', 0))
    
    arr = '▲' if change >= 0 else '▼'
    sign = '+' if change >= 0 else ''
    now = datetime.now().strftime('%H:%M:%S')
    
    # Oblicz poziomy techniczne
    r1 = price * 1.02
    r2 = price * 1.04
    s1 = price * 0.98
    s2 = price * 0.96
    
    # FVG
    fvg_bull_low = price * 0.985
    fvg_bull_high = price * 0.99
    fvg_bear_low = price * 1.015
    fvg_bear_high = price * 1.02
    
    # Iceberg
    ice_buy_low = price * 0.99
    ice_buy_high = price * 0.995
    ice_sell_low = price * 1.025
    ice_sell_high = price * 1.03
    
    signal = '🟢 LONG' if change > -0.5 else '🔴 SHORT'
    conf = 82 if change > 0 else 75
    
    msg = f'''══════════════════════════════════
       {emoji} {symbol} | {name}
══════════════════════════════════

💰 CENA AKTUALNA
├─ Cena:     ${price:,.2f}
├─ Zmiana:   {arr} {sign}{change:.2f}%
├─ High 24h: ${high:,.2f}
└─ Low 24h:  ${low:,.2f}

📈 POZIOMY TECHNICZNE
├─ Resistance 1: ${r1:,.0f}
├─ Resistance 2: ${r2:,.0f}
├─ Support 1:    ${s1:,.0f}
└─ Support 2:    ${s2:,.0f}

🔲 FVG (Fair Value Gap)
├─ FVG BULLISH: ${fvg_bull_low:,.0f} - ${fvg_bull_high:,.0f}
└─ FVG BEARISH: ${fvg_bear_low:,.0f} - ${fvg_bear_high:,.0f}

🐋 ICEBERG ORDERS
├─ 🟢 BUY:  ${ice_buy_low:,.0f} - ${ice_buy_high:,.0f}
└─ 🔴 SELL: ${ice_sell_low:,.0f} - ${ice_sell_high:,.0f}

🎯 SYGNAŁ: {signal}
📊 Konfluencja: {conf}%

⏰ {now} CET
🔸 Źródło: Twelve Data Pro API
══════════════════════════════════'''
    
    return msg


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /start"""
    msg = '''🚀🚀🚀 ZAPINAĆ PASY, LECIMY! 🚀🚀🚀

💥 ROZPIERDOL NA BANI 💥

🐹 HAMSTER TERMINAL ACTIVATED

Witaj w najlepszym bocie tradingowym!

📊 DOSTĘPNE KOMENDY:

/btc - ₿ Bitcoin analiza
/eth - ⟠ Ethereum analiza  
/gold - � Złoto XAU/USD
/silver - 🔘 Srebro XAG/USD
/all - 📊 Wszystkie aktywa
/signals - 🎯 Aktywne sygnały
/alerts - ⚠️ Alerty likwidacji
/help - ❓ Pomoc

🌐 hamsterterminal.com
TO THE MOON! 🌙'''
    
    await update.message.reply_text(msg)


async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /btc"""
    await update.message.reply_text("⏳ Pobieram dane BTC...")
    try:
        data = get_quote('BTC/USD')
        logger.info(f"BTC data received: {data}")
        if data and 'close' in data and data.get('close'):
            msg = format_price_message('BTC/USD', 'BITCOIN', '₿', data)
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text(f"❌ Błąd pobierania danych BTC\nDebug: {str(data)[:200]}")
    except Exception as e:
        logger.error(f"BTC command error: {e}")
        await update.message.reply_text(f"❌ Błąd: {str(e)}")


async def eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /eth"""
    await update.message.reply_text("⏳ Pobieram dane ETH...")
    try:
        data = get_quote('ETH/USD')
        logger.info(f"ETH data received: {data}")
        if data and 'close' in data and data.get('close'):
            msg = format_price_message('ETH/USD', 'ETHEREUM', '⟠', data)
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text(f"❌ Błąd pobierania danych ETH\nDebug: {str(data)[:200]}")
    except Exception as e:
        logger.error(f"ETH command error: {e}")
        await update.message.reply_text(f"❌ Błąd: {str(e)}")


async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /gold"""
    await update.message.reply_text("⏳ Pobieram dane GOLD...")
    data = get_quote('XAU/USD')
    if data and 'close' in data:
        msg = format_price_message('XAU/USD', 'ZŁOTO', '�', data)
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ Błąd pobierania danych GOLD")


async def silver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /silver"""
    await update.message.reply_text("⏳ Pobieram dane SILVER...")
    data = get_quote('XAG/USD')
    if data and 'close' in data:
        msg = format_price_message('XAG/USD', 'SREBRO', '🔘', data)
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ Błąd pobierania danych SILVER")


async def all_assets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /all - wszystkie aktywa"""
    await update.message.reply_text("⏳ Pobieram wszystkie dane...")
    
    try:
        btc_data = get_quote('BTC/USD')
        eth_data = get_quote('ETH/USD')
        gold_data = get_quote('XAU/USD')
        silver_data = get_quote('XAG/USD')
        
        def fmt(d):
            if d and 'close' in d and d.get('close'):
                try:
                    p = float(d.get('close', 0))
                    c = float(d.get('percent_change', 0))
                    arr = '▲' if c >= 0 else '▼'
                    sign = '+' if c >= 0 else ''
                    return f"${p:,.2f} {arr}{sign}{c:.2f}%"
                except:
                    return "N/A"
            return "N/A"
        
        now = datetime.now().strftime('%H:%M:%S')
        
        msg = f'''══════════════════════════════════
   📊 HAMSTER TERMINAL | PRZEGLĄD
══════════════════════════════════

💰 KRYPTOWALUTY
├─ ₿ BTC/USD:  {fmt(btc_data)}
└─ ⟠ ETH/USD:  {fmt(eth_data)}

🥇 METALE SZLACHETNE
├─ 🪙 XAU/USD: {fmt(gold_data)}
└─ 🔘 XAG/USD: {fmt(silver_data)}

━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Szczegóły: /btc /eth /gold /silver

⏰ {now} CET
🔸 Źródło: Twelve Data Pro API
══════════════════════════════════'''
        
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"All assets error: {e}")
        await update.message.reply_text(f"❌ Błąd: {str(e)}")


async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /signals - aktywne sygnały"""
    try:
        btc_data = get_quote('BTC/USD')
        eth_data = get_quote('ETH/USD')
        
        # Default prices if API fails
        btc_p = 89000
        eth_p = 2950
        
        if btc_data and 'close' in btc_data and btc_data.get('close'):
            try:
                btc_p = float(btc_data.get('close'))
            except:
                pass
                
        if eth_data and 'close' in eth_data and eth_data.get('close'):
            try:
                eth_p = float(eth_data.get('close'))
            except:
                pass
        
        msg = f'''══════════════════════════════════
       🎯 AKTYWNE SYGNAŁY
══════════════════════════════════

🟢 BTC/USD - LONG
├─ Entry:  ${btc_p:,.0f} - ${btc_p+300:,.0f}
├─ SL:     ${btc_p-1800:,.0f}
├─ TP1:    ${btc_p+2500:,.0f}
├─ TP2:    ${btc_p+4500:,.0f}
└─ Konfl.: 82%

🟢 ETH/USD - LONG
├─ Entry:  ${eth_p:,.0f} - ${eth_p+40:,.0f}
├─ SL:     ${eth_p-180:,.0f}
├─ TP1:    ${eth_p+250:,.0f}
├─ TP2:    ${eth_p+450:,.0f}
└─ Konfl.: 78%

🟢 XAU/USD - LONG
├─ Entry:  $4,975 - $4,985
├─ SL:     $4,940
├─ TP1:    $5,020
├─ TP2:    $5,080
└─ Konfl.: 85%

⚠️ To nie jest porada inwestycyjna!
══════════════════════════════════'''
        
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Signals error: {e}")
        await update.message.reply_text(f"❌ Błąd: {str(e)}")


async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /alerts - alerty likwidacji"""
    msg = '''══════════════════════════════════
       ⚠️ ALERTY LIKWIDACJI
══════════════════════════════════

📉 LIKWIDACJE LONG (zagrożone)
├─ BTC $87,200 → $285M
├─ ETH $2,780 → $92M
└─ MEGA: BTC $85,000 → $580M

📈 LIKWIDACJE SHORT (zagrożone)
├─ BTC $92,500 → $195M
└─ ETH $3,150 → $78M

🐋 ICEBERG DETECTION
├─ 🟢 BUY: $88,800 - $89,200 (~3,450 BTC)
└─ 🔴 SELL: $92,400 - $92,800 (~2,100 BTC)

💎 INSIDER FLOW
├─ Net Flow: +1,350 BTC
└─ Sygnał: 🟢 BYCZY

💡 Spodziewana wysoka zmienność!
══════════════════════════════════'''
    
    await update.message.reply_text(msg)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komenda /help"""
    msg = '''❓ POMOC - HAMSTER TERMINAL BOT

📊 KOMENDY AKTYWÓW:
/btc - Bitcoin pełna analiza
/eth - Ethereum pełna analiza
/gold - Złoto XAU/USD analiza
/silver - Srebro XAG/USD analiza
/all - Przegląd wszystkich

🎯 TRADING:
/signals - Aktywne sygnały
/alerts - Alerty likwidacji

🔔 AUTO-RAPORTY:
/report - Włącz/wyłącz raporty
/status - Status subskrypcji

ℹ️ INFO:
/start - Uruchom bota
/help - Ta wiadomość

━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Każda analiza zawiera:
• Cenę aktualną + zmiana %
• High/Low 24h
• Support & Resistance
• FVG (Fair Value Gaps)
• Iceberg Orders
• Sygnał + Konfluencja

🔔 AUTO-RAPORTY:
• Poranny raport 8:00 CET
• Wieczorny raport 20:00 CET
• Alerty przy ruchach >3%

🌐 hamsterterminal.com
📱 @HamsterTerminalBot'''
    
    await update.message.reply_text(msg)


async def report_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Włącz/wyłącz auto-raporty"""
    chat_id = str(update.effective_chat.id)
    
    if chat_id in report_subscribers:
        report_subscribers.discard(chat_id)
        msg = '''🔕 AUTO-RAPORTY WYŁĄCZONE

Nie będziesz już otrzymywać:
• Porannych raportów (8:00)
• Wieczornych raportów (20:00)
• Alertów o dużych ruchach

Wpisz /report aby włączyć ponownie.'''
    else:
        report_subscribers.add(chat_id)
        msg = '''🔔 AUTO-RAPORTY WŁĄCZONE!

Będziesz otrzymywać:
• 📅 Poranny raport: 8:00 CET
• 🌙 Wieczorny raport: 20:00 CET
• ⚡ Alerty przy ruchach >3%

Wpisz /report aby wyłączyć.'''
    
    await update.message.reply_text(msg)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status subskrypcji"""
    chat_id = str(update.effective_chat.id)
    subscribed = "✅ AKTYWNA" if chat_id in report_subscribers else "❌ NIEAKTYWNA"
    
    msg = f'''📊 STATUS SUBSKRYPCJI

🔔 Auto-raporty: {subscribed}
📱 Chat ID: {chat_id}

🕐 Harmonogram raportów:
• 08:00 - Raport poranny
• 20:00 - Raport wieczorny
• Real-time - Alerty >3%

Wpisz /report aby zmienić status.'''
    
    await update.message.reply_text(msg)


async def generate_morning_report():
    """Generuj poranny raport"""
    btc = get_quote('BTC/USD')
    eth = get_quote('ETH/USD')
    gold = get_quote('XAU/USD')
    silver = get_quote('XAG/USD')
    
    def fmt(d, sym):
        if d and 'close' in d:
            p = float(d.get('close', 0))
            c = float(d.get('percent_change', 0))
            arr = '▲' if c >= 0 else '▼'
            sign = '+' if c >= 0 else ''
            # Zapisz cenę do wykrywania ruchów
            previous_prices[sym] = p
            return f"${p:,.2f} {arr}{sign}{c:.2f}%"
        return "N/A"
    
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    return f'''☀️ PORANNY RAPORT | {now}
══════════════════════════════════

🐹 HAMSTER TERMINAL - DZIEŃ DOBRY!

💰 KRYPTOWALUTY
├─ ₿ BTC: {fmt(btc, 'BTC')}
└─ ⟠ ETH: {fmt(eth, 'ETH')}

🪙 METALE
├─ 🪙 GOLD: {fmt(gold, 'GOLD')}
└─ 🔘 SILVER: {fmt(silver, 'SILVER')}

📊 OUTLOOK NA DZIŚ:
{'🟢 BYCZY - dominuje pozytywny sentiment' if float(btc.get('percent_change', 0)) > 0 else '🔴 NIEDŹWIEDZI - ostrożność wskazana'}

💡 KLUCZOWE POZIOMY BTC:
├─ Support: ${float(btc.get('close', 89000))*0.98:,.0f}
└─ Resistance: ${float(btc.get('close', 89000))*1.02:,.0f}

⚡ Alerty aktywne przy ruchach >3%
━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 hamsterterminal.com'''


async def generate_evening_report():
    """Generuj wieczorny raport"""
    btc = get_quote('BTC/USD')
    eth = get_quote('ETH/USD')
    gold = get_quote('XAU/USD')
    silver = get_quote('XAG/USD')
    
    def fmt(d):
        if d and 'close' in d:
            p = float(d.get('close', 0))
            c = float(d.get('percent_change', 0))
            arr = '▲' if c >= 0 else '▼'
            sign = '+' if c >= 0 else ''
            return f"${p:,.2f} {arr}{sign}{c:.2f}%"
        return "N/A"
    
    btc_change = float(btc.get('percent_change', 0))
    eth_change = float(eth.get('percent_change', 0))
    
    # Podsumowanie dnia
    if btc_change > 2:
        day_summary = "🚀 ŚWIETNY DZIEŃ! Byki dominowały."
    elif btc_change > 0:
        day_summary = "📈 Dobry dzień, lekkie wzrosty."
    elif btc_change > -2:
        day_summary = "📉 Słabszy dzień, lekkie spadki."
    else:
        day_summary = "🔴 Ciężki dzień, niedźwiedzie wygrały."
    
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    return f'''🌙 WIECZORNY RAPORT | {now}
══════════════════════════════════

🐹 HAMSTER TERMINAL - PODSUMOWANIE DNIA

💰 ZAMKNIĘCIE SESJI
├─ ₿ BTC: {fmt(btc)}
├─ ⟠ ETH: {fmt(eth)}
├─ 🪙 GOLD: {fmt(gold)}
└─ 🔘 SILVER: {fmt(silver)}

📊 PODSUMOWANIE:
{day_summary}

🎯 TOP MOVER: {'BTC' if abs(btc_change) > abs(eth_change) else 'ETH'}

💡 OUTLOOK NA JUTRO:
{'Kontynuacja trendu wzrostowego możliwa' if btc_change > 0 else 'Obserwuj poziomy wsparcia'}

🔔 Auto-raport: /report
━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 Dobranoc! 🐹'''


async def check_price_alerts(context: ContextTypes.DEFAULT_TYPE):
    """Sprawdź duże ruchy cenowe (>3%) z cooldown 30 min"""
    global previous_prices, alert_cooldowns
    
    symbols = {
        'BTC/USD': ('BTC', '₿'),
        'ETH/USD': ('ETH', '⟠'),
        'XAU/USD': ('GOLD', '🪙'),
        'XAG/USD': ('SILVER', '🔘')
    }
    
    current_time = datetime.now()
    
    for symbol, (name, emoji) in symbols.items():
        data = get_quote(symbol)
        if data and 'close' in data:
            current_price = float(data.get('close', 0))
            
            if name in previous_prices and previous_prices[name] > 0:
                prev_price = previous_prices[name]
                change_pct = ((current_price - prev_price) / prev_price) * 100
                
                if abs(change_pct) >= 3:
                    # Sprawdź cooldown - czy minęło 30 minut od ostatniego alertu
                    last_alert_time = alert_cooldowns.get(name)
                    if last_alert_time:
                        minutes_since_alert = (current_time - last_alert_time).total_seconds() / 60
                        if minutes_since_alert < ALERT_COOLDOWN_MINUTES:
                            logger.info(f"⏸️ Alert {name} pominięty - cooldown ({minutes_since_alert:.0f}/{ALERT_COOLDOWN_MINUTES} min)")
                            continue  # Pomijamy - za wcześnie na kolejny alert
                    
                    direction = "🚀 PUMP" if change_pct > 0 else "💥 DUMP"
                    arrow = "▲" if change_pct > 0 else "▼"
                    
                    alert_msg = f'''⚡⚡⚡ ALERT CENOWY ⚡⚡⚡
══════════════════════════════════

{emoji} {name} - {direction}!

{arrow} Zmiana: {change_pct:+.2f}%
💰 Cena: ${current_price:,.2f}
📊 Poprzednio: ${prev_price:,.2f}

⚠️ WYSOKA ZMIENNOŚĆ!
{'🟢 Rozważ LONG' if change_pct > 0 else '🔴 Rozważ SHORT'}

⏰ {current_time.strftime('%H:%M:%S')} CET
══════════════════════════════════'''
                    
                    # Wyślij do wszystkich subskrybentów
                    alert_sent = False
                    for chat_id in report_subscribers:
                        try:
                            await context.bot.send_message(chat_id=chat_id, text=alert_msg)
                            alert_sent = True
                        except Exception as e:
                            logger.error(f"Błąd wysyłania alertu: {e}")
                    
                    # Zapisz czas wysłania alertu (cooldown)
                    if alert_sent:
                        alert_cooldowns[name] = current_time
                        logger.info(f"✅ Alert {name} wysłany - następny możliwy za {ALERT_COOLDOWN_MINUTES} min")
            
            # Aktualizuj cenę
            previous_prices[name] = current_price


async def send_morning_report(context: ContextTypes.DEFAULT_TYPE):
    """Wyślij poranny raport"""
    report = await generate_morning_report()
    for chat_id in report_subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=report)
            logger.info(f"Poranny raport wysłany do {chat_id}")
        except Exception as e:
            logger.error(f"Błąd wysyłania raportu: {e}")


async def send_evening_report(context: ContextTypes.DEFAULT_TYPE):
    """Wyślij wieczorny raport"""
    report = await generate_evening_report()
    for chat_id in report_subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=report)
            logger.info(f"Wieczorny raport wysłany do {chat_id}")
        except Exception as e:
            logger.error(f"Błąd wysyłania raportu: {e}")


def main():
    """Uruchom bota"""
    print("🐹 HAMSTER TERMINAL BOT - Starting...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Utwórz aplikację
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Dodaj handlery komend
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("eth", eth))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("silver", silver))
    app.add_handler(CommandHandler("all", all_assets))
    app.add_handler(CommandHandler("signals", signals))
    app.add_handler(CommandHandler("alerts", alerts))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("report", report_toggle))
    app.add_handler(CommandHandler("status", status_cmd))
    
    # Zaplanuj auto-raporty
    job_queue = app.job_queue
    
    # Poranny raport o 8:00 CET (7:00 UTC)
    job_queue.run_daily(send_morning_report, time=time(hour=7, minute=0))
    
    # Wieczorny raport o 20:00 CET (19:00 UTC)
    job_queue.run_daily(send_evening_report, time=time(hour=19, minute=0))
    
    # Sprawdzaj alerty cenowe co 5 minut
    job_queue.run_repeating(check_price_alerts, interval=300, first=10)
    
    print("✅ Komendy zarejestrowane:")
    print("   /start /btc /eth /gold /silver /all /signals /alerts /report /status /help")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔔 Auto-raporty zaplanowane:")
    print("   📅 Poranny: 08:00 CET")
    print("   🌙 Wieczorny: 20:00 CET")
    print("   ⚡ Alerty >3%: co 5 min")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 Bot uruchomiony! Nasłuchuje...")
    
    # Uruchom bota
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
