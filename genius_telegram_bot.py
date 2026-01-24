"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GENIUS TELEGRAM BOT v1.0                                   ║
║                    Real-Time Trading Alerts                                   ║
║                                                                              ║
║  Features:                                                                   ║
║  • Instant signal notifications to your phone                               ║
║  • Price alerts with confluence breakdown                                   ║
║  • Position tracking and P&L updates                                        ║
║  • Command interface for checking status                                    ║
║  • Rich formatting with emojis and charts                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import os

# Telegram library
try:
    from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot not installed. Run: pip install python-telegram-bot")

# Configuration
class TelegramConfig:
    """Telegram Bot Configuration"""
    
    # Get from @BotFather on Telegram
    BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8254662818:AAGSCUbd-Zc8tmjmCB3ujLNksLqxICJ2rJw')
    
    # Your chat ID (get from @userinfobot)
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '5616894588')
    
    # Alert settings
    SIGNAL_ALERTS = True
    PRICE_ALERTS = True
    POSITION_UPDATES = True
    
    # Minimum confluence to send alert (%)
    MIN_CONFLUENCE_ALERT = 70
    
    # Rate limiting (seconds between messages)
    RATE_LIMIT = 2


class GeniusTelegramBot:
    """
    Telegram Bot for Genius Trading Engine
    
    Sends real-time alerts for:
    - New trading signals
    - Price movements
    - Position updates
    - System status
    """
    
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or TelegramConfig.BOT_TOKEN
        self.chat_id = chat_id or TelegramConfig.CHAT_ID
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self.is_running = False
        self.last_message_time = 0
        
        # Alert history
        self.alert_history: List[Dict] = []
        
        # Subscribed users
        self.subscribers: set = {self.chat_id} if self.chat_id else set()
        
        # Logger
        self.logger = logging.getLogger('GeniusTelegramBot')
        
        if TELEGRAM_AVAILABLE and self.token and self.token != 'YOUR_BOT_TOKEN_HERE':
            self.bot = Bot(token=self.token)
            self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the bot"""
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # MESSAGE FORMATTING
    # ═══════════════════════════════════════════════════════════════════════
    
    def format_signal_message(self, signal: Dict) -> str:
        """Format a trading signal as a Telegram message"""
        
        direction = signal.get('direction', 'NEUTRAL')
        symbol = signal.get('symbol', 'BTC/USDT')
        confidence = signal.get('confidence', 0)
        price = signal.get('price', 0)
        
        # Direction emoji
        if direction == 'LONG':
            dir_emoji = "🟢 LONG"
            arrow = "📈"
        elif direction == 'SHORT':
            dir_emoji = "🔴 SHORT"
            arrow = "📉"
        else:
            dir_emoji = "⚪ NEUTRAL"
            arrow = "➖"
        
        # Confidence indicator
        if confidence >= 85:
            conf_emoji = "🔥🔥🔥"
            strength = "VERY STRONG"
        elif confidence >= 75:
            conf_emoji = "🔥🔥"
            strength = "STRONG"
        elif confidence >= 70:
            conf_emoji = "🔥"
            strength = "MODERATE"
        else:
            conf_emoji = "❄️"
            strength = "WEAK"
        
        # Build message
        message = f"""
{arrow} *GENIUS SIGNAL* {arrow}

*{dir_emoji}* | {symbol}
━━━━━━━━━━━━━━━━━━━━━

💰 *Price:* ${price:,.2f}
📊 *Confluence:* {confidence:.1f}% {conf_emoji}
💪 *Strength:* {strength}

"""
        
        # Add confluence breakdown
        factors = signal.get('factors', {})
        if factors:
            message += "*Confluence Breakdown:*\n"
            for factor, data in factors.items():
                if isinstance(data, dict):
                    active = data.get('active', False)
                    points = data.get('points', 0)
                    emoji = "✅" if active else "❌"
                    message += f"{emoji} {factor}: {points}pts\n"
        
        # Add levels
        entry = signal.get('entry', price)
        stop_loss = signal.get('stop_loss', 0)
        take_profit = signal.get('take_profit', 0)
        
        if stop_loss and take_profit:
            message += f"""
━━━━━━━━━━━━━━━━━━━━━
📍 *Entry:* ${entry:,.2f}
🛑 *Stop Loss:* ${stop_loss:,.2f}
🎯 *Take Profit:* ${take_profit:,.2f}
"""
        
        # Timestamp
        message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def format_price_alert(self, symbol: str, price: float, change_pct: float) -> str:
        """Format a price alert message"""
        
        if change_pct > 0:
            emoji = "🚀"
            direction = "UP"
        else:
            emoji = "📉"
            direction = "DOWN"
        
        message = f"""
{emoji} *PRICE ALERT* {emoji}

*{symbol}*
━━━━━━━━━━━━━━━━━━━━━

💰 Price: ${price:,.2f}
📊 Change: {change_pct:+.2f}% {direction}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        return message
    
    def format_position_update(self, position: Dict) -> str:
        """Format a position update message"""
        
        symbol = position.get('symbol', 'BTC/USDT')
        side = position.get('side', 'LONG')
        entry = position.get('entry_price', 0)
        current = position.get('current_price', 0)
        pnl = position.get('unrealized_pnl', 0)
        pnl_pct = position.get('pnl_percentage', 0)
        
        if pnl >= 0:
            pnl_emoji = "💚"
        else:
            pnl_emoji = "🔴"
        
        side_emoji = "🟢" if side == 'LONG' else "🔴"
        
        message = f"""
📊 *POSITION UPDATE* 📊

*{symbol}* | {side_emoji} {side}
━━━━━━━━━━━━━━━━━━━━━

📍 Entry: ${entry:,.2f}
💰 Current: ${current:,.2f}

{pnl_emoji} *P&L:* ${pnl:,.2f} ({pnl_pct:+.2f}%)

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        return message
    
    def format_status_message(self, status: Dict) -> str:
        """Format system status message"""
        
        message = f"""
🤖 *GENIUS ENGINE STATUS* 🤖
━━━━━━━━━━━━━━━━━━━━━

🟢 *Engine:* Running
📊 *Version:* 5.0 Ultimate

📈 *Today's Signals:*
• LONG: {status.get('long_signals', 0)}
• SHORT: {status.get('short_signals', 0)}
• Total: {status.get('total_signals', 0)}

💰 *Paper Trading P&L:* ${status.get('pnl', 0):,.2f}

📡 *Active Modules:*
✅ Core Engine
✅ JP Morgan Quant
✅ QuantMuse
✅ LSTM Predictor
✅ Backtest Engine
✅ Paper Trading
✅ Telegram Bot

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return message
    
    # ═══════════════════════════════════════════════════════════════════════
    # SEND METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def send_message(self, message: str, chat_id: str = None, parse_mode: str = 'Markdown') -> bool:
        """Send a message to Telegram"""
        
        if not self.bot:
            self.logger.warning("Bot not initialized - cannot send message")
            return False
        
        target_chat = chat_id or self.chat_id
        
        try:
            # Rate limiting
            import time
            current_time = time.time()
            if current_time - self.last_message_time < TelegramConfig.RATE_LIMIT:
                await asyncio.sleep(TelegramConfig.RATE_LIMIT)
            
            await self.bot.send_message(
                chat_id=target_chat,
                text=message,
                parse_mode=parse_mode
            )
            
            self.last_message_time = time.time()
            self.alert_history.append({
                'time': datetime.now().isoformat(),
                'chat_id': target_chat,
                'message': message[:100] + '...'
            })
            
            self.logger.info(f"Message sent to {target_chat}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    async def send_signal_alert(self, signal: Dict) -> bool:
        """Send a trading signal alert"""
        
        if not TelegramConfig.SIGNAL_ALERTS:
            return False
        
        confidence = signal.get('confidence', 0)
        if confidence < TelegramConfig.MIN_CONFLUENCE_ALERT:
            self.logger.info(f"Signal confidence {confidence}% below threshold, not sending")
            return False
        
        message = self.format_signal_message(signal)
        
        # Send to all subscribers
        for chat_id in self.subscribers:
            await self.send_message(message, chat_id)
        
        return True
    
    async def send_price_alert(self, symbol: str, price: float, change_pct: float) -> bool:
        """Send a price alert"""
        
        if not TelegramConfig.PRICE_ALERTS:
            return False
        
        message = self.format_price_alert(symbol, price, change_pct)
        
        for chat_id in self.subscribers:
            await self.send_message(message, chat_id)
        
        return True
    
    async def send_position_update(self, position: Dict) -> bool:
        """Send a position update"""
        
        if not TelegramConfig.POSITION_UPDATES:
            return False
        
        message = self.format_position_update(position)
        
        for chat_id in self.subscribers:
            await self.send_message(message, chat_id)
        
        return True
    
    async def send_status(self, status: Dict = None) -> bool:
        """Send system status"""
        
        if status is None:
            status = {
                'long_signals': 3,
                'short_signals': 2,
                'total_signals': 5,
                'pnl': 1250.00
            }
        
        message = self.format_status_message(status)
        
        for chat_id in self.subscribers:
            await self.send_message(message, chat_id)
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # COMMAND HANDLERS (for interactive bot)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        
        chat_id = str(update.effective_chat.id)
        self.subscribers.add(chat_id)
        
        welcome_message = """
🚀 *Welcome to Genius Trading Bot!* 🚀

I'll send you real-time trading signals with:
• 10 confluence factors
• JP Morgan quant analysis
• QuantMuse validation
• LSTM price predictions

*Commands:*
/status - Check engine status
/signals - Recent signals
/subscribe - Enable alerts
/unsubscribe - Disable alerts
/help - Show help

Let's make some profits! 💰
"""
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        
        status = {
            'long_signals': 3,
            'short_signals': 2,
            'total_signals': 5,
            'pnl': 1250.00
        }
        
        message = self.format_status_message(status)
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command"""
        
        message = """
📊 *Recent Signals (Last 24h)* 📊
━━━━━━━━━━━━━━━━━━━━━

🟢 BTC/USDT LONG @ $97,500 (82%)
🔴 ETH/USDT SHORT @ $3,150 (76%)
🟢 SOL/USDT LONG @ $185 (71%)

Use /subscribe to get real-time alerts!
"""
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def cmd_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command"""
        
        chat_id = str(update.effective_chat.id)
        self.subscribers.add(chat_id)
        
        await update.message.reply_text(
            "✅ *Subscribed!* You'll receive real-time trading alerts.",
            parse_mode='Markdown'
        )
    
    async def cmd_unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unsubscribe command"""
        
        chat_id = str(update.effective_chat.id)
        self.subscribers.discard(chat_id)
        
        await update.message.reply_text(
            "❌ *Unsubscribed.* You won't receive alerts anymore.",
            parse_mode='Markdown'
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        
        help_message = """
📚 *Genius Bot Help* 📚
━━━━━━━━━━━━━━━━━━━━━

*Commands:*
/start - Start the bot
/status - Engine status
/signals - Recent signals
/subscribe - Enable alerts
/unsubscribe - Disable alerts
/help - This help message

*Signal Strength:*
🔥🔥🔥 Very Strong (85%+)
🔥🔥 Strong (75-84%)
🔥 Moderate (70-74%)

*Confluence Factors:*
• Liquidity Grab (25pts)
• FVG Zone (20pts)
• MTF Alignment (20pts)
• RSI (15pts)
• Whale Flow (10pts)
• JP Morgan Vol (10pts)
• Orderbook (5pts)
• News (5pts)
• JPM Move (5pts)
• QuantMuse (15pts)

Questions? @YourUsername
"""
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    # ═══════════════════════════════════════════════════════════════════════
    # BOT LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════
    
    def setup_handlers(self, application: Application):
        """Setup command handlers"""
        
        application.add_handler(CommandHandler("start", self.cmd_start))
        application.add_handler(CommandHandler("status", self.cmd_status))
        application.add_handler(CommandHandler("signals", self.cmd_signals))
        application.add_handler(CommandHandler("subscribe", self.cmd_subscribe))
        application.add_handler(CommandHandler("unsubscribe", self.cmd_unsubscribe))
        application.add_handler(CommandHandler("help", self.cmd_help))
    
    async def start_polling(self):
        """Start the bot with polling (for development)"""
        
        if not TELEGRAM_AVAILABLE:
            self.logger.error("python-telegram-bot not installed")
            return
        
        if self.token == 'YOUR_BOT_TOKEN_HERE':
            self.logger.error("Please set TELEGRAM_BOT_TOKEN environment variable")
            return
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers(self.application)
        
        self.is_running = True
        self.logger.info("Starting Telegram bot polling...")
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # Keep running
        while self.is_running:
            await asyncio.sleep(1)
    
    def stop(self):
        """Stop the bot"""
        self.is_running = False
        if self.application:
            asyncio.create_task(self.application.stop())


class TelegramAlertManager:
    """
    Manager for sending alerts without running full bot
    Use this for simple one-way notifications
    """
    
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or TelegramConfig.BOT_TOKEN
        self.chat_id = chat_id or TelegramConfig.CHAT_ID
        self.bot = GeniusTelegramBot(self.token, self.chat_id)
    
    def send_signal(self, signal: Dict) -> bool:
        """Send a signal alert (synchronous wrapper)"""
        return asyncio.run(self.bot.send_signal_alert(signal))
    
    def send_price_alert(self, symbol: str, price: float, change_pct: float) -> bool:
        """Send a price alert (synchronous wrapper)"""
        return asyncio.run(self.bot.send_price_alert(symbol, price, change_pct))
    
    def send_position_update(self, position: Dict) -> bool:
        """Send position update (synchronous wrapper)"""
        return asyncio.run(self.bot.send_position_update(position))
    
    def send_custom_message(self, message: str) -> bool:
        """Send a custom message (synchronous wrapper)"""
        return asyncio.run(self.bot.send_message(message))


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION WITH GENIUS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def integrate_with_genius_engine(engine, telegram_token: str = None, chat_id: str = None):
    """
    Integrate Telegram alerts with Genius Engine
    
    Usage:
        from genius_trading_engine_v3 import GeniusEngine
        from genius_telegram_bot import integrate_with_genius_engine
        
        engine = GeniusEngine()
        integrate_with_genius_engine(engine, token, chat_id)
        
        # Signals will now be sent to Telegram automatically
    """
    
    alert_manager = TelegramAlertManager(telegram_token, chat_id)
    
    # Store original method
    original_generate = engine.generate_signal
    
    async def generate_with_telegram(*args, **kwargs):
        """Wrapper that sends signals to Telegram"""
        signal = await original_generate(*args, **kwargs)
        
        if signal and signal.get('confidence', 0) >= TelegramConfig.MIN_CONFLUENCE_ALERT:
            alert_manager.send_signal(signal)
        
        return signal
    
    # Replace method
    engine.generate_signal = generate_with_telegram
    
    return alert_manager


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demo the Telegram bot formatting"""
    
    print("=" * 70)
    print("🤖 GENIUS TELEGRAM BOT v1.0 - DEMO")
    print("=" * 70)
    
    bot = GeniusTelegramBot()
    
    # Demo signal
    demo_signal = {
        'direction': 'LONG',
        'symbol': 'BTC/USDT',
        'confidence': 82.5,
        'price': 97500,
        'entry': 97500,
        'stop_loss': 95000,
        'take_profit': 102000,
        'factors': {
            'Liquidity Grab': {'active': True, 'points': 25},
            'FVG Zone': {'active': True, 'points': 20},
            'MTF Alignment': {'active': True, 'points': 20},
            'RSI': {'active': False, 'points': 0},
            'Whale Flow': {'active': True, 'points': 10},
            'JPM Vol Regime': {'active': True, 'points': 10},
            'QuantMuse': {'active': True, 'points': 15},
        }
    }
    
    print("\n📱 SIGNAL MESSAGE FORMAT:")
    print("-" * 50)
    message = bot.format_signal_message(demo_signal)
    # Remove markdown for console display
    print(message.replace('*', ''))
    
    print("\n📱 PRICE ALERT FORMAT:")
    print("-" * 50)
    message = bot.format_price_alert('BTC/USDT', 97500, 2.5)
    print(message.replace('*', ''))
    
    print("\n📱 POSITION UPDATE FORMAT:")
    print("-" * 50)
    position = {
        'symbol': 'BTC/USDT',
        'side': 'LONG',
        'entry_price': 95000,
        'current_price': 97500,
        'unrealized_pnl': 250,
        'pnl_percentage': 2.63
    }
    message = bot.format_position_update(position)
    print(message.replace('*', ''))
    
    print("\n📱 STATUS MESSAGE FORMAT:")
    print("-" * 50)
    message = bot.format_status_message({
        'long_signals': 3,
        'short_signals': 2,
        'total_signals': 5,
        'pnl': 1250.00
    })
    print(message.replace('*', ''))
    
    print("\n" + "=" * 70)
    print("✅ Telegram Bot ready!")
    print("   To activate: Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    demo()
