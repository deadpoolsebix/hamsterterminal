"""
🔬 BACKTESTING ENGINE - Walidacja sygnałów na danych historycznych
HamsterTerminal Pro v3.0

Funkcje:
- Pobieranie danych historycznych z Twelve Data
- Generowanie sygnałów historycznych (RSI+MACD+BB+SMA)
- Symulacja tradów z TP/SL
- Statystyki: Win Rate, Profit Factor, Max Drawdown, Sharpe Ratio
- Raportowanie wyników
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests

# Konfiguracja
TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY', 'd54ad684cd8f40de895ec569d6128821')
BACKTEST_DATA_DIR = 'backtest_data'
BACKTEST_RESULTS_DIR = 'backtest_results'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Utwórz foldery jeśli nie istnieją
os.makedirs(BACKTEST_DATA_DIR, exist_ok=True)
os.makedirs(BACKTEST_RESULTS_DIR, exist_ok=True)


@dataclass
class Trade:
    """Pojedynczy trade w backteście"""
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    direction: str  # 'LONG' or 'SHORT'
    signal_type: str  # 'STRONG_BUY', 'BUY', 'SELL', 'STRONG_SELL'
    tp_price: float
    sl_price: float
    result: str  # 'WIN', 'LOSS', 'BREAKEVEN'
    pnl_percent: float
    pnl_usd: float
    exit_reason: str  # 'TP', 'SL', 'SIGNAL_CHANGE', 'TIMEOUT'
    confidence: float
    indicators: Dict


@dataclass
class BacktestResult:
    """Wyniki backtestu"""
    symbol: str
    interval: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    avg_trade_pnl: float
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    avg_holding_time: str
    trades: List[Dict]
    equity_curve: List[float]


def get_historical_data(
    symbol: str,
    interval: str = '1h',
    outputsize: int = 5000,
    start_date: str = None,
    end_date: str = None
) -> Optional[List[Dict]]:
    """
    Pobierz dane historyczne z Twelve Data.
    
    Args:
        symbol: Symbol (np. 'BTC/USD', 'AAPL')
        interval: '1min', '5min', '15min', '1h', '4h', '1day'
        outputsize: Liczba świec (max 5000)
        start_date: Data początkowa (YYYY-MM-DD)
        end_date: Data końcowa (YYYY-MM-DD)
    
    Returns:
        Lista świec OHLCV
    """
    cache_file = os.path.join(
        BACKTEST_DATA_DIR, 
        f"{symbol.replace('/', '_')}_{interval}_{outputsize}.json"
    )
    
    # Sprawdź cache (ważny 24h)
    if os.path.exists(cache_file):
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if file_age < timedelta(hours=24):
            with open(cache_file, 'r') as f:
                logger.info(f"📁 Loading cached data: {symbol}")
                return json.load(f)
    
    logger.info(f"📥 Downloading historical data: {symbol} ({interval}, {outputsize} candles)")
    
    try:
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize,
            'apikey': TWELVE_DATA_API_KEY
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        resp = requests.get(
            'https://api.twelvedata.com/time_series',
            params=params,
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            if 'values' in data:
                # Odwróć kolejność (najstarsze najpierw)
                values = list(reversed(data['values']))
                
                # Konwertuj wartości
                for v in values:
                    v['open'] = float(v['open'])
                    v['high'] = float(v['high'])
                    v['low'] = float(v['low'])
                    v['close'] = float(v['close'])
                    v['volume'] = float(v.get('volume', 0))
                
                # Zapisz do cache
                with open(cache_file, 'w') as f:
                    json.dump(values, f)
                
                logger.info(f"✅ Downloaded {len(values)} candles for {symbol}")
                return values
                
    except Exception as e:
        logger.error(f"❌ Error downloading data for {symbol}: {e}")
    
    return None


def calculate_indicators(data: List[Dict], index: int) -> Dict:
    """
    Oblicz wskaźniki techniczne dla danego indeksu.
    
    Args:
        data: Lista świec OHLCV
        index: Indeks aktualnej świecy
    
    Returns:
        Dict ze wskaźnikami
    """
    if index < 200:  # Potrzebujemy min 200 świec dla SMA200
        return None
    
    closes = [d['close'] for d in data[:index+1]]
    highs = [d['high'] for d in data[:index+1]]
    lows = [d['low'] for d in data[:index+1]]
    
    # === RSI (14) ===
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
    
    # === EMA ===
    def calc_ema(prices, period):
        if len(prices) < period:
            return prices[-1]
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    # === SMA ===
    def calc_sma(prices, period):
        if len(prices) < period:
            return prices[-1]
        return sum(prices[-period:]) / period
    
    # === MACD ===
    ema_12 = calc_ema(closes, 12)
    ema_26 = calc_ema(closes, 26)
    macd_line = ema_12 - ema_26
    
    # Signal line (9-period EMA of MACD)
    macd_values = []
    for i in range(max(26, index-50), index+1):
        if i >= 26:
            e12 = calc_ema(closes[:i+1], 12)
            e26 = calc_ema(closes[:i+1], 26)
            macd_values.append(e12 - e26)
    
    signal_line = calc_ema(macd_values, 9) if len(macd_values) >= 9 else macd_line
    macd_hist = macd_line - signal_line
    
    # Previous MACD histogram
    prev_macd_hist = 0
    if index > 26:
        prev_e12 = calc_ema(closes[:-1], 12)
        prev_e26 = calc_ema(closes[:-1], 26)
        prev_macd = prev_e12 - prev_e26
        prev_macd_values = macd_values[:-1] if macd_values else [prev_macd]
        prev_signal = calc_ema(prev_macd_values, 9) if len(prev_macd_values) >= 9 else prev_macd
        prev_macd_hist = prev_macd - prev_signal
    
    # === Bollinger Bands (20, 2) ===
    sma_20 = calc_sma(closes, 20)
    std_20 = (sum((p - sma_20) ** 2 for p in closes[-20:]) / 20) ** 0.5
    bb_upper = sma_20 + (2 * std_20)
    bb_lower = sma_20 - (2 * std_20)
    bb_position = (closes[-1] - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
    
    # === SMAs ===
    sma_50 = calc_sma(closes, 50)
    sma_200 = calc_sma(closes, 200)
    
    current_price = closes[-1]
    prev_rsi = calc_rsi(closes[:-1]) if len(closes) > 15 else 50
    
    return {
        'rsi': calc_rsi(closes),
        'prev_rsi': prev_rsi,
        'macd_line': macd_line,
        'macd_signal': signal_line,
        'macd_hist': macd_hist,
        'prev_macd_hist': prev_macd_hist,
        'bb_upper': bb_upper,
        'bb_middle': sma_20,
        'bb_lower': bb_lower,
        'bb_position': bb_position,
        'bb_width': (bb_upper - bb_lower) / sma_20 * 100,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'sma_200': sma_200,
        'price': current_price,
        'golden_cross': sma_20 > sma_50 > sma_200,
        'death_cross': sma_20 < sma_50 < sma_200
    }


def generate_signal(indicators: Dict) -> Tuple[str, int, float, List[str]]:
    """
    Generuj sygnał na podstawie wskaźników.
    
    Returns:
        (signal_type, score, confidence, reasons)
    """
    if not indicators:
        return ('HOLD', 0, 0, [])
    
    score = 0
    reasons = []
    
    rsi = indicators['rsi']
    prev_rsi = indicators['prev_rsi']
    macd_hist = indicators['macd_hist']
    prev_macd_hist = indicators['prev_macd_hist']
    bb_position = indicators['bb_position']
    price = indicators['price']
    sma_20 = indicators['sma_20']
    sma_50 = indicators['sma_50']
    
    # RSI Analysis (±3)
    if rsi <= 20:
        score += 3
        reasons.append(f"RSI Extremely Oversold ({rsi:.1f})")
    elif rsi <= 30:
        score += 2
        reasons.append(f"RSI Oversold ({rsi:.1f})")
    elif rsi >= 80:
        score -= 3
        reasons.append(f"RSI Extremely Overbought ({rsi:.1f})")
    elif rsi >= 70:
        score -= 2
        reasons.append(f"RSI Overbought ({rsi:.1f})")
    elif rsi > prev_rsi and rsi > 50:
        score += 1
        reasons.append(f"RSI Rising ({rsi:.1f})")
    elif rsi < prev_rsi and rsi < 50:
        score -= 1
        reasons.append(f"RSI Falling ({rsi:.1f})")
    
    # MACD Analysis (±3)
    if macd_hist > 0 and prev_macd_hist <= 0:
        score += 3
        reasons.append("MACD Bullish Crossover")
    elif macd_hist < 0 and prev_macd_hist >= 0:
        score -= 3
        reasons.append("MACD Bearish Crossover")
    elif macd_hist > 0:
        score += 1
        reasons.append("MACD Positive")
    elif macd_hist < 0:
        score -= 1
        reasons.append("MACD Negative")
    
    # Bollinger Bands (±2)
    if bb_position <= 0:
        score += 2
        reasons.append("Price at Lower BB")
    elif bb_position >= 1:
        score -= 2
        reasons.append("Price at Upper BB")
    elif bb_position < 0.3:
        score += 1
        reasons.append("Price near Lower BB")
    elif bb_position > 0.7:
        score -= 1
        reasons.append("Price near Upper BB")
    
    # SMA Trend (±2)
    if indicators['golden_cross'] and price > sma_50:
        score += 2
        reasons.append("Golden Cross + Above SMA50")
    elif indicators['death_cross'] and price < sma_50:
        score -= 2
        reasons.append("Death Cross + Below SMA50")
    elif price > sma_20 and price > sma_50:
        score += 1
        reasons.append("Above SMA20 & SMA50")
    elif price < sma_20 and price < sma_50:
        score -= 1
        reasons.append("Below SMA20 & SMA50")
    
    # Determine signal
    confidence = min(abs(score) / 10 * 100, 100)
    
    if score >= 5:
        signal = 'STRONG_BUY'
    elif score >= 2:
        signal = 'BUY'
    elif score <= -5:
        signal = 'STRONG_SELL'
    elif score <= -2:
        signal = 'SELL'
    else:
        signal = 'HOLD'
    
    return (signal, score, confidence, reasons)


def calculate_tp_sl(price: float, signal: str, bb_width: float) -> Tuple[float, float]:
    """Oblicz TP i SL na podstawie volatility (BB width)"""
    volatility = bb_width / 100  # jako decimal
    
    if signal in ['STRONG_BUY', 'BUY']:
        tp = price * (1 + volatility * 1.5)
        sl = price * (1 - volatility)
    elif signal in ['STRONG_SELL', 'SELL']:
        tp = price * (1 - volatility * 1.5)
        sl = price * (1 + volatility)
    else:
        tp = price * 1.02
        sl = price * 0.98
    
    return (tp, sl)


def run_backtest(
    symbol: str,
    interval: str = '1h',
    initial_capital: float = 10000,
    position_size_pct: float = 10,
    max_trades: int = None,
    min_confidence: float = 30,
    use_trailing_sl: bool = False
) -> BacktestResult:
    """
    🔬 Uruchom backtest dla danego symbolu.
    
    Args:
        symbol: Symbol do testowania
        interval: Interwał czasowy
        initial_capital: Kapitał początkowy ($)
        position_size_pct: Wielkość pozycji (% kapitału)
        max_trades: Limit tradów (None = bez limitu)
        min_confidence: Minimalna pewność sygnału do otwarcia
        use_trailing_sl: Czy używać trailing stop loss
    
    Returns:
        BacktestResult z pełnymi statystykami
    """
    logger.info(f"🔬 Starting backtest: {symbol} ({interval})")
    
    # Pobierz dane
    data = get_historical_data(symbol, interval, 5000)
    if not data or len(data) < 250:
        logger.error(f"❌ Insufficient data for {symbol}")
        return None
    
    logger.info(f"📊 Data range: {data[0]['datetime']} to {data[-1]['datetime']}")
    
    # Inicjalizacja
    capital = initial_capital
    equity_curve = [capital]
    trades: List[Trade] = []
    open_trade = None
    max_capital = capital
    
    # Iteruj przez dane
    for i in range(200, len(data)):
        candle = data[i]
        indicators = calculate_indicators(data, i)
        
        if not indicators:
            continue
        
        signal, score, confidence, reasons = generate_signal(indicators)
        price = indicators['price']
        
        # === Sprawdź otwartą pozycję ===
        if open_trade:
            high = candle['high']
            low = candle['low']
            
            exit_price = None
            exit_reason = None
            
            if open_trade['direction'] == 'LONG':
                # Check SL
                if low <= open_trade['sl']:
                    exit_price = open_trade['sl']
                    exit_reason = 'SL'
                # Check TP
                elif high >= open_trade['tp']:
                    exit_price = open_trade['tp']
                    exit_reason = 'TP'
                # Signal change
                elif signal in ['STRONG_SELL', 'SELL'] and confidence >= min_confidence:
                    exit_price = price
                    exit_reason = 'SIGNAL_CHANGE'
            
            else:  # SHORT
                # Check SL
                if high >= open_trade['sl']:
                    exit_price = open_trade['sl']
                    exit_reason = 'SL'
                # Check TP
                elif low <= open_trade['tp']:
                    exit_price = open_trade['tp']
                    exit_reason = 'TP'
                # Signal change
                elif signal in ['STRONG_BUY', 'BUY'] and confidence >= min_confidence:
                    exit_price = price
                    exit_reason = 'SIGNAL_CHANGE'
            
            # Zamknij pozycję
            if exit_price:
                if open_trade['direction'] == 'LONG':
                    pnl_pct = ((exit_price - open_trade['entry_price']) / open_trade['entry_price']) * 100
                else:
                    pnl_pct = ((open_trade['entry_price'] - exit_price) / open_trade['entry_price']) * 100
                
                pnl_usd = open_trade['position_size'] * (pnl_pct / 100)
                capital += pnl_usd
                
                result = 'WIN' if pnl_pct > 0 else 'LOSS' if pnl_pct < 0 else 'BREAKEVEN'
                
                trade = Trade(
                    entry_time=open_trade['entry_time'],
                    exit_time=candle['datetime'],
                    entry_price=open_trade['entry_price'],
                    exit_price=exit_price,
                    direction=open_trade['direction'],
                    signal_type=open_trade['signal'],
                    tp_price=open_trade['tp'],
                    sl_price=open_trade['sl'],
                    result=result,
                    pnl_percent=pnl_pct,
                    pnl_usd=pnl_usd,
                    exit_reason=exit_reason,
                    confidence=open_trade['confidence'],
                    indicators=open_trade['indicators']
                )
                trades.append(trade)
                open_trade = None
                
                logger.debug(f"  📈 Closed {trade.direction}: {trade.result} {trade.pnl_percent:.2f}%")
        
        # === Otwórz nową pozycję ===
        if not open_trade and signal != 'HOLD' and confidence >= min_confidence:
            if max_trades and len(trades) >= max_trades:
                continue
            
            position_size = capital * (position_size_pct / 100)
            tp, sl = calculate_tp_sl(price, signal, indicators['bb_width'])
            
            direction = 'LONG' if signal in ['STRONG_BUY', 'BUY'] else 'SHORT'
            
            open_trade = {
                'entry_time': candle['datetime'],
                'entry_price': price,
                'direction': direction,
                'signal': signal,
                'tp': tp,
                'sl': sl,
                'position_size': position_size,
                'confidence': confidence,
                'indicators': {
                    'rsi': indicators['rsi'],
                    'macd_hist': indicators['macd_hist'],
                    'bb_position': indicators['bb_position']
                }
            }
            
            logger.debug(f"  🎯 Opened {direction} at ${price:.2f} (TP: ${tp:.2f}, SL: ${sl:.2f})")
        
        # Update equity curve
        equity_curve.append(capital)
        max_capital = max(max_capital, capital)
    
    # Zamknij otwartą pozycję na końcu
    if open_trade:
        last_price = data[-1]['close']
        if open_trade['direction'] == 'LONG':
            pnl_pct = ((last_price - open_trade['entry_price']) / open_trade['entry_price']) * 100
        else:
            pnl_pct = ((open_trade['entry_price'] - last_price) / open_trade['entry_price']) * 100
        
        pnl_usd = open_trade['position_size'] * (pnl_pct / 100)
        capital += pnl_usd
        
        trade = Trade(
            entry_time=open_trade['entry_time'],
            exit_time=data[-1]['datetime'],
            entry_price=open_trade['entry_price'],
            exit_price=last_price,
            direction=open_trade['direction'],
            signal_type=open_trade['signal'],
            tp_price=open_trade['tp'],
            sl_price=open_trade['sl'],
            result='WIN' if pnl_pct > 0 else 'LOSS',
            pnl_percent=pnl_pct,
            pnl_usd=pnl_usd,
            exit_reason='END_OF_DATA',
            confidence=open_trade['confidence'],
            indicators=open_trade['indicators']
        )
        trades.append(trade)
    
    # === Oblicz statystyki ===
    winning_trades = [t for t in trades if t.result == 'WIN']
    losing_trades = [t for t in trades if t.result == 'LOSS']
    
    win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
    
    total_wins = sum(t.pnl_usd for t in winning_trades)
    total_losses = abs(sum(t.pnl_usd for t in losing_trades))
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    # Max Drawdown
    peak = initial_capital
    max_dd = 0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        max_dd = max(max_dd, dd)
    
    # Sharpe Ratio (simplified)
    returns = []
    for i in range(1, len(equity_curve)):
        ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
        returns.append(ret)
    
    if returns:
        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0  # Annualized
    else:
        sharpe = 0
    
    result = BacktestResult(
        symbol=symbol,
        interval=interval,
        start_date=data[200]['datetime'],
        end_date=data[-1]['datetime'],
        initial_capital=initial_capital,
        final_capital=capital,
        total_trades=len(trades),
        winning_trades=len(winning_trades),
        losing_trades=len(losing_trades),
        win_rate=win_rate,
        profit_factor=profit_factor,
        total_return_pct=((capital - initial_capital) / initial_capital) * 100,
        max_drawdown_pct=max_dd,
        sharpe_ratio=sharpe,
        avg_trade_pnl=sum(t.pnl_percent for t in trades) / len(trades) if trades else 0,
        avg_win=sum(t.pnl_percent for t in winning_trades) / len(winning_trades) if winning_trades else 0,
        avg_loss=sum(t.pnl_percent for t in losing_trades) / len(losing_trades) if losing_trades else 0,
        best_trade=max(t.pnl_percent for t in trades) if trades else 0,
        worst_trade=min(t.pnl_percent for t in trades) if trades else 0,
        avg_holding_time='N/A',  # TODO: Calculate
        trades=[asdict(t) for t in trades],
        equity_curve=equity_curve
    )
    
    # Zapisz wyniki
    result_file = os.path.join(
        BACKTEST_RESULTS_DIR,
        f"backtest_{symbol.replace('/', '_')}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(result_file, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    
    logger.info(f"✅ Backtest complete: {len(trades)} trades, {win_rate:.1f}% win rate, {result.total_return_pct:.2f}% return")
    
    return result


def format_backtest_report(result: BacktestResult) -> str:
    """Formatuj raport backtestu do tekstu"""
    
    # Emoji na podstawie wyników
    if result.total_return_pct > 20:
        perf_emoji = "🚀"
    elif result.total_return_pct > 0:
        perf_emoji = "📈"
    elif result.total_return_pct > -10:
        perf_emoji = "📉"
    else:
        perf_emoji = "💀"
    
    wr_emoji = "✅" if result.win_rate > 50 else "⚠️"
    pf_emoji = "✅" if result.profit_factor > 1.5 else "⚠️" if result.profit_factor > 1 else "❌"
    dd_emoji = "✅" if result.max_drawdown_pct < 20 else "⚠️" if result.max_drawdown_pct < 30 else "❌"
    
    report = f"""
{'═' * 50}
🔬 BACKTEST REPORT: {result.symbol}
{'═' * 50}

📅 Period: {result.start_date[:10]} → {result.end_date[:10]}
⏰ Interval: {result.interval}

{'─' * 50}
💰 PERFORMANCE {perf_emoji}
{'─' * 50}
Initial Capital:  ${result.initial_capital:,.2f}
Final Capital:    ${result.final_capital:,.2f}
Total Return:     {result.total_return_pct:+.2f}%

{'─' * 50}
📊 TRADE STATISTICS
{'─' * 50}
Total Trades:     {result.total_trades}
Winning:          {result.winning_trades} ({result.win_rate:.1f}%) {wr_emoji}
Losing:           {result.losing_trades}

Profit Factor:    {result.profit_factor:.2f} {pf_emoji}
Avg Trade P&L:    {result.avg_trade_pnl:+.2f}%
Avg Win:          {result.avg_win:+.2f}%
Avg Loss:         {result.avg_loss:.2f}%
Best Trade:       {result.best_trade:+.2f}%
Worst Trade:      {result.worst_trade:.2f}%

{'─' * 50}
⚠️ RISK METRICS
{'─' * 50}
Max Drawdown:     {result.max_drawdown_pct:.2f}% {dd_emoji}
Sharpe Ratio:     {result.sharpe_ratio:.2f}

{'─' * 50}
📈 ANALYSIS
{'─' * 50}
"""
    
    if result.win_rate >= 50 and result.profit_factor >= 1.5:
        report += "✅ PROFITABLE STRATEGY - Consider for live trading\n"
    elif result.win_rate >= 45 and result.profit_factor >= 1.2:
        report += "⚠️ MARGINAL STRATEGY - Needs optimization\n"
    else:
        report += "❌ UNPROFITABLE - Do not use in current form\n"
    
    if result.max_drawdown_pct > 30:
        report += "⚠️ HIGH DRAWDOWN - Reduce position size\n"
    
    if result.total_trades < 30:
        report += "⚠️ LOW SAMPLE SIZE - Results may not be statistically significant\n"
    
    report += f"""
{'═' * 50}
📡 HamsterTerminal Backtesting Engine v1.0
{'═' * 50}
"""
    
    return report


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🔬 HAMSTER TERMINAL - BACKTESTING ENGINE")
    print("=" * 60)
    
    # Default test
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTC/USD'
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    
    print(f"\n🎯 Running backtest for {symbol} ({interval})...")
    
    result = run_backtest(
        symbol=symbol,
        interval=interval,
        initial_capital=10000,
        position_size_pct=10,
        min_confidence=30
    )
    
    if result:
        print(format_backtest_report(result))
    else:
        print("❌ Backtest failed")
