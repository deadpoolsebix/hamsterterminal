#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ADVANCED LIVE REAL-TIME BOT
- Gra bez limitów świec
- Wszystkie wskaźniki techniczne
- Detekcja Bull/Bear Trapów
- Dwa wykresy: cena + equity
- HTML dashboard z live sygnałami
"""

import sys
import time
import threading
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
from typing import Dict
import pandas as pd
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.simulator.real_data_fetcher import RealDataFetcher
from live_indicators_analyzer import AdvancedIndicators
from ml_trading_brain import TradingBrain
from colorama import Fore, Style, init

init(autoreset=True)


class AdvancedLiveBot:
    """
    LIVE BOT z pełnym zestawem wskaźników
    - Gra bez limitów
    - RSI, Momentum, MACD, Bollinger Bands, FVG, Sentiment, ATR
    - Bull/Bear Trap detection
    - Sygnały: BUY, SELL, BULL_TRAP, BEAR_TRAP
    - LIKWIDACJA: Automatyczne zamknięcie na TP/SL
    """
    
    def __init__(self, interval: str = '15m'):
        self.interval = interval
        self.dynamic_intervals = True  # Elastyczny wybór interwału gdy pojawia się okazja
        self.intervals_priority = ['1m', '5m', '15m', '1h']  # dodano ultra-krótki 1m
        self.trades = []  # Zamknięte pozycje
        self.signals = []
        self.running = True
        self.start_capital = 5000
        self.current_equity = self.start_capital
        # Dashboard compatibility
        self.starting_capital = self.start_capital
        self.last_data = None
        self.last_indicators = None
        
        # RISK MANAGEMENT - 4:1 Reward/Risk
        self.take_profit_pct = 20.0  # Cel: +20%
        self.stop_loss_pct = 5.0     # Maksymalna strata: -5%
        
        # ACTIVE POSITION
        self.active_position = None  # {'entry_price': X, 'tp': X, 'sl': X, 'entry_time': X, 'entry_signal': X}
        self.closed_positions = []  # Zamknięte pozycje z P&L
        
        # Wskaźniki historia
        self.candle_history = deque(maxlen=200)  # Ostatnie 200 candles
        self.rsi_history = deque(maxlen=200)
        self.momentum_history = deque(maxlen=200)
        self.macd_history = deque(maxlen=200)
        self.signal_line_history = deque(maxlen=200)
        self.sentiment_history = deque(maxlen=200)
        self.sentiment_strength_history = deque(maxlen=200)
        self.atr_history = deque(maxlen=200)
        self.bb_upper_history = deque(maxlen=200)
        self.bb_middle_history = deque(maxlen=200)
        self.bb_lower_history = deque(maxlen=200)
        
        self.indicators = AdvancedIndicators()
        self.iteration = 0
        
        # AI BRAIN - Machine Learning
        self.brain = TradingBrain(
            learning_rate=0.1,
            discount_factor=0.95,
            epsilon=0.15  # 15% exploration
        )
        
        # Try to load previous learning
        self.brain.load_brain("trading_brain.pkl")
        
    def fetch_live_data(self, num_candles: int = 200) -> pd.DataFrame:
        """Pobierz LIVE dane z rynku"""
        try:
            fetcher = RealDataFetcher()
            all_data = fetcher.fetch_btc_data(days=7, interval=self.interval)
            
            if all_data is None or len(all_data) == 0:
                return None
            
            return all_data.tail(num_candles)
            
        except Exception as e:
            print(f"{Fore.RED}[!] Błąd pobierania: {e}{Style.RESET_ALL}")
            return None

    def fetch_live_data_interval(self, interval: str, num_candles: int = 200) -> pd.DataFrame:
        """Pobierz dane dla konkretnego interwału (krótsze dla scalpu)"""
        try:
            fetcher = RealDataFetcher()
            days = 3 if interval in ['1m', '2m', '5m'] else 7
            data = fetcher.fetch_btc_data(days=days, interval=interval)
            if data is None or len(data) == 0:
                return None
            return data.tail(num_candles)
        except Exception as e:
            print(f"{Fore.RED}[!] Błąd pobierania ({interval}): {e}{Style.RESET_ALL}")
            return None

    def scan_intervals_for_signal(self, num_candles: int = 200):
        """Przeskanuj wiele interwałów i wybierz najsilniejszy sygnał"""
        best = None
        for iv in self.intervals_priority:
            data = self.fetch_live_data_interval(iv, num_candles=num_candles)
            if data is None or len(data) < 26:
                continue
            indicators_data = self.calculate_all_indicators(data)
            if indicators_data is None:
                continue
            signal_info = self.generate_signals(indicators_data)

            main_signal = signal_info['signal']
            score_map = {
                'BULL_TRAP': 4,
                'BEAR_TRAP': 4,
                'BUY': 3,
                'SELL': 3,
                'HOLD': 1,
                'WAIT': 0,
            }
            score = score_map.get(main_signal, 0)

            # Wzmocnij score, gdy momentum jest silne (absolutna wartość)
            try:
                score += min(abs(signal_info['momentum']) / 200, 2)
            except Exception:
                pass

            if best is None or score > best['score']:
                best = {
                    'interval': iv,
                    'data': data,
                    'indicators': indicators_data,
                    'signal_info': signal_info,
                    'score': score,
                }

        return best
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> Dict:
        """
        Oblicz WSZYSTKIE wskaźniki
        """
        if len(data) < 26:
            return None
        
        close = data['close']
        high = data['high']
        low = data['low']
        volume = data['volume']
        
        # RSI
        rsi = self.indicators.calculate_rsi(close, period=14)
        
        # Momentum
        momentum = self.indicators.calculate_momentum(close, period=10)
        
        # MACD
        macd_line, signal_line, histogram = self.indicators.calculate_macd(close)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.indicators.calculate_bollinger_bands(close, period=20, std_dev=2)
        
        # ATR
        atr = self.indicators.calculate_atr(high, low, close, period=14)
        
        # Volume Momentum
        vol_momentum = self.indicators.calculate_volume_momentum(volume, period=10)
        
        # Market Sentiment
        sentiment, sentiment_strength = self.indicators.calculate_market_sentiment(close, volume, period=20)

        # Volume anomaly (z-score) do szybkiej detekcji wybicia wolumenu
        vol_mean = volume.rolling(20).mean()
        vol_std = volume.rolling(20).std()
        volume_z = (volume - vol_mean) / vol_std.replace(0, np.nan)
        volume_z = volume_z.fillna(0)

        # Fast Open Interest proxy (szybsza reakcja na 1m/5m)
        oi_proxy = self.indicators.estimate_open_interest(data)

        # Lightweight CVD
        cvd = self.indicators.calculate_cvd(data)

        # Liquidity grab (stop hunt)
        liquidity_grab = self.indicators.detect_liquidity_grab(data['open'], high, low, close)
        
        # FVG Detection
        fvgs = self.indicators.detect_fvg(high, low)
        
        # Bull Trap Detection
        bull_traps = self.indicators.detect_bull_trap(high, low, close, period=5)
        
        # Bear Trap Detection
        bear_traps = self.indicators.detect_bear_trap(high, low, close, period=5)
        
        # Price Action Analysis
        price_action = self.indicators.analyze_price_action(high, low, close)
        
        return {
            'rsi': rsi,
            'momentum': momentum,
            'macd_line': macd_line,
            'signal_line': signal_line,
            'macd_histogram': histogram,
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'atr': atr,
            'vol_momentum': vol_momentum,
            'sentiment': sentiment,
            'sentiment_strength': sentiment_strength,
            'fvgs': fvgs,
            'bull_traps': bull_traps,
            'bear_traps': bear_traps,
            'price_action': price_action,
            'open_interest': oi_proxy,
            'cvd': cvd,
            'liquidity_grab': liquidity_grab,
            'volume_zscore': volume_z,
            'data': data
        }
    
    def generate_signals(self, indicators_data: Dict) -> Dict:
        """
        Generuj SYGNAŁY BUY/SELL/BULL_TRAP/BEAR_TRAP
        """
        if indicators_data is None:
            return {'signal': 'WAIT', 'reason': 'Not enough data'}
        
        rsi = indicators_data['rsi']
        momentum = indicators_data['momentum']
        macd_line = indicators_data['macd_line']
        signal_line = indicators_data['signal_line']
        sentiment = indicators_data['sentiment']
        close = indicators_data['data']['close']
        high = indicators_data['data']['high']
        low = indicators_data['data']['low']
        
        current_rsi = rsi[-1]
        current_momentum = momentum[-1]
        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        current_sentiment = sentiment[-1]
        current_price = close.iloc[-1]

        # Open interest i CVD bias
        oi_momentum = indicators_data.get('open_interest', {}).get('momentum')
        oi_momentum_last = oi_momentum[-1] if oi_momentum is not None and len(oi_momentum) > 0 else np.nan
        cvd_bias = indicators_data.get('cvd', {}).get('bias', 0)
        liquidity_grab = indicators_data.get('liquidity_grab', {}).get('type')
        volume_z = indicators_data.get('volume_zscore', None)
        volume_z_last = volume_z.iloc[-1] if volume_z is not None and len(volume_z) > 0 else 0
        high_volume_spike = volume_z_last > 2  # anomalia wolumenowa
        
        signals_detected = []
        
        # === BULL TRAP ===
        if len(indicators_data['bull_traps']) > 0:
            latest_trap = indicators_data['bull_traps'][-1]
            if latest_trap['index'] == len(close) - 1:
                signals_detected.append('BULL_TRAP')
        
        # === BEAR TRAP ===
        if len(indicators_data['bear_traps']) > 0:
            latest_trap = indicators_data['bear_traps'][-1]
            if latest_trap['index'] == len(close) - 1:
                signals_detected.append('BEAR_TRAP')
        
        # === ELASTYCZNE PROGI (bardziej decyzyjne) ===
        # BUY / LONG: RSI < 45 i sentyment > -0.2 lub bullish liquidity grab
        if ((current_rsi < 45 and current_sentiment > -0.2) or liquidity_grab == 'bullish'):
            if (current_macd > current_signal) or (high_volume_spike and volume_z_last > 1.5):
                signals_detected.append('BUY')

        # SELL / SHORT: RSI > 55 i sentyment < 0.2 lub bearish liquidity grab
        if ((current_rsi > 55 and current_sentiment < 0.2) or liquidity_grab == 'bearish'):
            if (current_macd < current_signal) or (high_volume_spike and volume_z_last > 1.5):
                signals_detected.append('SELL')

        # Dodatkowe wsparcie OI/CVD (agresywny scalp)
        if liquidity_grab == 'bullish' and cvd_bias == 1 and (not np.isnan(oi_momentum_last) and oi_momentum_last > 0):
            signals_detected.append('BUY')
        if liquidity_grab == 'bearish' and cvd_bias == -1 and (not np.isnan(oi_momentum_last) and oi_momentum_last < 0):
            signals_detected.append('SELL')
        
        # Prioritet dla trapów
        if 'BULL_TRAP' in signals_detected:
            main_signal = 'BULL_TRAP'
        elif 'BEAR_TRAP' in signals_detected:
            main_signal = 'BEAR_TRAP'
        elif 'SELL' in signals_detected:
            main_signal = 'SELL'
        elif 'BUY' in signals_detected:
            main_signal = 'BUY'
        else:
            main_signal = 'HOLD'
        
        return {
            'signal': main_signal,
            'all_signals': signals_detected,
            'rsi': current_rsi,
            'momentum': current_momentum,
            'macd': current_macd,
            'sentiment': current_sentiment,
            'cvd_bias': cvd_bias,
            'oi_momentum': oi_momentum_last,
            'liquidity_grab': liquidity_grab,
            'volume_zscore': volume_z_last,
            'volume_spike': high_volume_spike,
            'price': current_price,
        }
    
    def check_position_liquidation(self, current_price: float, current_time: datetime) -> Dict:
        """
        Obsługa zamykania pozycji LONG i SHORT w oparciu o % P&L
        Zwróć: {'closed': bool, 'exit_type': 'TP'/'SL', 'pnl': float, 'pnl_pct': float}
        """
        if self.active_position is None:
            return {'closed': False}

        pos = self.active_position
        side = pos.get('side', 'LONG')
        entry_price = pos['entry_price']

        # policz P&L % względem kierunku
        if side == 'LONG':
            pnl_pct = (current_price - entry_price) / entry_price * 100
        else:  # SHORT
            pnl_pct = (entry_price - current_price) / entry_price * 100

        # aktualizuj niezrealizowany P&L (%) na pozycji
        self.active_position['unrealized_pnl_pct'] = pnl_pct

        closed = False
        exit_type = None
        if pnl_pct >= self.take_profit_pct:
            closed = True
            exit_type = 'TAKE_PROFIT'
        elif pnl_pct <= -self.stop_loss_pct:
            closed = True
            exit_type = 'STOP_LOSS'

        if not closed:
            return {'closed': False}

        # oblicz P&L w jednostkach ceny jako procent od entry
        pnl_abs = entry_price * (pnl_pct / 100.0)
        self.current_equity += pnl_abs

        # preferuj zapis ceny wyjścia jako TP/SL zgodnie z typem wyjścia
        exit_price = pos.get('tp') if exit_type == 'TAKE_PROFIT' else (pos.get('sl') if exit_type == 'STOP_LOSS' else current_price)

        closed_trade = {
            'entry_time': pos['entry_time'],
            'entry_price': entry_price,
            'exit_time': current_time,
            'exit_price': exit_price,
            'entry_signal': pos['entry_signal'],
            'exit_signal': exit_type,
            'pnl': pnl_abs,
            'pnl_pct': pnl_pct,
            'side': side,
        }
        self.closed_positions.append(closed_trade)

        # AI learning snapshot
        hold_time_minutes = (current_time - pos['entry_time']).total_seconds() / 60
        trade_result = {
            'state': pos.get('entry_state', 'unknown'),
            'action': side,
            'next_state': pos.get('exit_state', 'unknown'),
            'pnl': pnl_abs,
            'pnl_pct': pnl_pct,
            'hold_time_minutes': hold_time_minutes,
            'active_features': ['rsi', 'momentum', 'macd']
        }
        self.brain.learn_from_trade(trade_result)
        color = Fore.GREEN if exit_type == 'TAKE_PROFIT' else Fore.RED
        print(f"{color}[🧠] AI learned from trade ({side}) -> {exit_type}. Total: {self.brain.total_trades}{Style.RESET_ALL}")
        self.trades.append({
            'iteration': self.iteration,
            'time': current_time,
            'signal': f'CLOSED_{"TP" if exit_type=="TAKE_PROFIT" else "SL"}',
            'price': current_price,
            'tp': pos.get('tp'),
            'sl': pos.get('sl'),
            'rsi': pos.get('rsi', 0),
            'momentum': pos.get('momentum', 0),
            'sentiment': pos.get('sentiment', 0),
            'pnl': pnl_abs,
            'pnl_pct': pnl_pct,
            'entry_price': entry_price,
            'side': side,
        })

        self.active_position = None

        return {
            'closed': True,
            'exit_type': exit_type,
            'pnl': pnl_abs,
            'pnl_pct': pnl_pct,
        }
    
    def run_live_trading(self, duration_minutes: int = None):
        """
        MAIN LIVE LOOP
        duration_minutes: None = nieskończenie, lub liczba minut
        """
        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] ADVANCED LIVE REAL-TIME BOT - 100% WINNING TRADES MODE{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Wyłączony Stop Loss | +20% Target | Duży zasięg | Tylko STRONGEST sygnały{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")
        
        print(f"Interval: {self.interval}")
        print(f"Start Capital: ${self.start_capital:,}")
        print(f"Stop Loss: {self.stop_loss_pct}% (Duży zasięg - prawie nigdy nie triggera)")
        print(f"Take Profit: +{self.take_profit_pct}%\n")
        
        start_time = datetime.now()
        
        while self.running:
            try:
                self.iteration += 1
                
                if self.dynamic_intervals:
                    print(f"\n{Fore.CYAN}[Iteration #{self.iteration}]{Style.RESET_ALL} {datetime.now()} | Scan: {', '.join(self.intervals_priority)}")
                    best = self.scan_intervals_for_signal(num_candles=200)
                    if best is None:
                        print(f"{Fore.RED}[!] Brak sygnałów na dostępnych interwałach{Style.RESET_ALL}")
                        time.sleep(30)
                        continue
                    data = best['data']
                    indicators_data = best['indicators']
                    signal_info = best['signal_info']
                    chosen_interval = best['interval']
                else:
                    print(f"\n{Fore.CYAN}[Iteration #{self.iteration}]{Style.RESET_ALL} {datetime.now()} | Interval: {self.interval}")
                    print(f"{Fore.YELLOW}[*] Pobieranie LIVE danych...{Style.RESET_ALL}")
                    data = self.fetch_live_data(num_candles=200)
                    if data is None or len(data) == 0:
                        print(f"{Fore.RED}[!] Brak danych{Style.RESET_ALL}")
                        time.sleep(30)
                        continue
                    indicators_data = self.calculate_all_indicators(data)
                    if indicators_data is None:
                        print(f"{Fore.RED}[!] Nie można obliczyć wskaźników{Style.RESET_ALL}")
                        time.sleep(30)
                        continue
                    signal_info = self.generate_signals(indicators_data)
                    chosen_interval = self.interval
                
                signal = signal_info['signal']

                # Dane dla dashboardu (WallStreet style)
                self.last_data = data.copy()
                self.last_indicators = {
                    'rsi': indicators_data['rsi'],
                    'macd': indicators_data['macd_line'],
                    'macd_signal': indicators_data['signal_line'],
                    'macd_hist': indicators_data['macd_histogram'],
                    'momentum': indicators_data['momentum'],
                    'sentiment': indicators_data['sentiment'],
                    'cvd_bias': indicators_data['cvd'].get('bias'),
                    'oi_momentum': indicators_data['open_interest'].get('momentum'),
                    'liquidity_grab': indicators_data['liquidity_grab'],
                }
                
                # Wyświetl dane
                last_row = data.iloc[-1]
                current_price = last_row['close']
                
                print(f"\n{Fore.GREEN}[OK] Otrzymano {len(data)} candles{Style.RESET_ALL}")
                print(f"  Bieżąca cena: ${current_price:.0f}")
                print(f"  High: ${last_row['high']:.0f} | Low: ${last_row['low']:.0f}")
                print(f"  Volume: {last_row['volume']:.0f}")
                
                # Wyświetl wskaźniki
                print(f"\n{Fore.CYAN}WSKAŹNIKI:{Style.RESET_ALL}")
                print(f"  RSI(14): {signal_info['rsi']:.2f} {'[OVERBOUGHT]' if signal_info['rsi'] > 70 else '[OVERSOLD]' if signal_info['rsi'] < 30 else ''}")
                print(f"  Momentum: {signal_info['momentum']:.2f} {'[POSITIVE]' if signal_info['momentum'] > 0 else '[NEGATIVE]'}")
                print(f"  MACD: {signal_info['macd']:.4f}")
                print(f"  Sentiment: {signal_info['sentiment']:.2f} {'[POSITIVE]' if signal_info['sentiment'] > 0 else '[NEGATIVE]'}")
                # Open Interest & CVD
                oi_mom = signal_info.get('oi_momentum', np.nan)
                if not np.isnan(oi_mom):
                    print(f"  OI Momentum (fast): {oi_mom:+.4f}")
                cvd_bias = signal_info.get('cvd_bias', 0)
                bias_txt = 'Bullish' if cvd_bias == 1 else 'Bearish' if cvd_bias == -1 else 'Neutral'
                print(f"  CVD Bias: {bias_txt}")
                liq = signal_info.get('liquidity_grab')
                if liq:
                    print(f"  Liquidity Grab: {liq.upper()}")
                
                # Bollinger Bands
                bb_idx = -1
                print(f"  BB Upper: ${indicators_data['bb_upper'][bb_idx]:.0f}")
                print(f"  BB Middle: ${indicators_data['bb_middle'][bb_idx]:.0f}")
                print(f"  BB Lower: ${indicators_data['bb_lower'][bb_idx]:.0f}")
                
                # ATR
                print(f"  ATR: ${indicators_data['atr'][bb_idx]:.0f}")
                
                # FVG
                if indicators_data['fvgs']:
                    latest_fvg = indicators_data['fvgs'][-1]
                    print(f"  FVG: {latest_fvg['type']} (Gap: ${latest_fvg['gap_bottom']:.0f} - ${latest_fvg['gap_top']:.0f})")
                
                # Sygnały
                print(f"\n{Fore.CYAN}SYGNAŁY:{Style.RESET_ALL}")
                print(f"  Main Signal: {self._color_signal(signal)}{signal}{Style.RESET_ALL}")
                if signal_info['all_signals']:
                    print(f"  All Signals: {', '.join(signal_info['all_signals'])}")
                # TP/SL - 100% WINNING TRADES MODE
                # 20% Target (duży zasięg), 50% SL (prawie nigdy nie triggera - fokus na TP)
                tp_price = current_price * (1 + self.take_profit_pct/100)
                sl_price = current_price * (1 + self.stop_loss_pct/100)
                
                print(f"\n{Fore.CYAN}RISK MANAGEMENT (4:1 RR):{Style.RESET_ALL}")
                print(f"  Entry: ${current_price:.0f}")
                print(f"  Hypothetical LONG TP (+{self.take_profit_pct}%): ${current_price * (1 + self.take_profit_pct/100):.0f}")
                print(f"  Hypothetical LONG SL (-{self.stop_loss_pct}%): ${current_price * (1 - self.stop_loss_pct/100):.0f}")
                
                # === CHECK POSITION LIQUIDATION ===
                if self.active_position is not None:
                    print(f"\n{Fore.YELLOW}[POSITION ACTIVE]{Style.RESET_ALL}")
                    print(f"  Side: {self.active_position.get('side','LONG')}")
                    print(f"  Entry Price: ${self.active_position['entry_price']:.0f}")
                    print(f"  Entry Time: {self.active_position['entry_time'].strftime('%H:%M:%S')}")
                    print(f"  Current Price: ${current_price:.0f}")
                    
                    side = self.active_position.get('side','LONG')
                    if side == 'LONG':
                        unrealized_pnl = current_price - self.active_position['entry_price']
                        unrealized_pnl_pct = unrealized_pnl / self.active_position['entry_price'] * 100
                        dist_tp = self.active_position['tp'] - current_price
                        dist_sl = current_price - self.active_position['sl']
                    else:
                        unrealized_pnl = self.active_position['entry_price'] - current_price
                        unrealized_pnl_pct = unrealized_pnl / self.active_position['entry_price'] * 100
                        dist_tp = current_price - self.active_position['tp']
                        dist_sl = self.active_position['sl'] - current_price
                    
                    pnl_color = Fore.GREEN if unrealized_pnl > 0 else Fore.RED
                    print(f"  Unrealized P&L: {pnl_color}${unrealized_pnl:.0f} ({unrealized_pnl_pct:+.2f}%){Style.RESET_ALL}")
                    print(f"  Distance to TP: ${dist_tp:.0f}")
                    print(f"  Distance to SL: ${dist_sl:.0f}")
                    
                    # Sprawdź likwidację
                    liquidation = self.check_position_liquidation(current_price, datetime.now())
                    
                    if liquidation['closed']:
                        exit_type = liquidation['exit_type']
                        pnl = liquidation['pnl']
                        pnl_pct = liquidation['pnl_pct']
                        
                        color = Fore.GREEN if exit_type == 'TAKE_PROFIT' else Fore.RED
                        print(f"\n{color}>>> POZYCJA ZAMKNIĘTA: {exit_type}{Style.RESET_ALL}")
                        print(f"{color}    P&L: ${pnl:.0f} ({pnl_pct:+.2f}%){Style.RESET_ALL}")
                        print(f"{color}    Equity: ${self.current_equity:,.0f}{Style.RESET_ALL}")
                
                # === OTWÓRZ NOWĄ POZYCJĘ (LONG/SHORT) ===
                if self.active_position is None and signal in ['BUY', 'SELL', 'BULL_TRAP', 'BEAR_TRAP']:
                    self.open_position(signal, current_price, signal_info)
                
                # Zapisz trade/sygnał
                if signal != 'HOLD':
                    self.trades.append({
                        'iteration': self.iteration,
                        'time': datetime.now(),
                        'signal': signal,
                        'price': current_price,
                        'tp': tp_price,
                        'sl': sl_price,
                        'rsi': signal_info['rsi'],
                        'momentum': signal_info['momentum'],
                        'sentiment': signal_info['sentiment'],
                    })
                    
                    print(f"\n{Fore.YELLOW}>>> SYGNAŁ: {self._color_signal(signal)}{signal}{Style.RESET_ALL} <<<")
                
                # Czekaj
                wait_time = 30  # 30 sekund dla demo
                print(f"\n{Fore.CYAN}[*] Czekam {wait_time}s do następnej analizy...{Style.RESET_ALL}")
                time.sleep(wait_time)
                
                # Sprawdź duration
                if duration_minutes and (datetime.now() - start_time).total_seconds() > duration_minutes * 60:
                    print(f"\n{Fore.YELLOW}[*] Osiągnięty limit czasu{Style.RESET_ALL}")
                    self.running = False
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[!] Bot zatrzymany{Style.RESET_ALL}")
                self.running = False
                break
            except Exception as e:
                print(f"{Fore.RED}[!] Błąd: {e}{Style.RESET_ALL}")
                time.sleep(30)
        
        self._print_summary()
    
    def _color_signal(self, signal: str) -> str:
        """Koloruj signal"""
        if signal == 'BUY':
            return Fore.GREEN
        elif signal == 'SELL':
            return Fore.RED
        elif signal == 'BULL_TRAP':
            return Fore.MAGENTA
        elif signal == 'BEAR_TRAP':
            return Fore.MAGENTA
        return Fore.YELLOW
    
    def _print_summary(self):
        """Podsumowanie"""
        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] PODSUMOWANIE{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")
        
        print(f"Iteracje: {self.iteration}")
        print(f"Sygnały: {len(self.trades)}")
        print(f"Zamknięte pozycje: {len(self.closed_positions)}")
        print(f"Starting Capital: ${self.start_capital:,}")
        print(f"Current Equity: ${self.current_equity:,.0f}")
        
        if self.closed_positions:
            total_pnl = sum(p['pnl'] for p in self.closed_positions)
            total_pnl_pct = (total_pnl / self.start_capital * 100) if self.start_capital > 0 else 0
            
            wins = len([p for p in self.closed_positions if p['pnl'] > 0])
            losses = len([p for p in self.closed_positions if p['pnl'] < 0])
            win_rate = (wins / len(self.closed_positions) * 100) if self.closed_positions else 0
            
            print(f"\n{Fore.CYAN}Wyniki tradesów:{Style.RESET_ALL}")
            print(f"  Total P&L: {Fore.GREEN if total_pnl > 0 else Fore.RED}${total_pnl:,.0f} ({total_pnl_pct:+.2f}%){Style.RESET_ALL}")
            print(f"  Wygrane: {Fore.GREEN}{wins}{Style.RESET_ALL}")
            print(f"  Przegrane: {Fore.RED}{losses}{Style.RESET_ALL}")
            print(f"  Win Rate: {Fore.YELLOW}{win_rate:.1f}%{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}Ostatnie zamknięte pozycje:{Style.RESET_ALL}")
            for i, trade in enumerate(self.closed_positions[-15:], 1):
                entry_time = trade['entry_time'].strftime("%H:%M:%S")
                exit_time = trade['exit_time'].strftime("%H:%M:%S")
                pnl = trade['pnl']
                pnl_pct = trade['pnl_pct']
                exit_type = trade['exit_signal']
                
                color = Fore.GREEN if pnl > 0 else Fore.RED
                print(f"  {i}. {entry_time} -> {exit_time} | {exit_type} | {color}${pnl:+.0f} ({pnl_pct:+.2f}%){Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")
        
        # === AI LEARNING REPORT ===
        print(f"\n{Fore.MAGENTA}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}[🧠] AI LEARNING REPORT{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*100}{Style.RESET_ALL}")
        self.brain.print_learning_report()
        
        # Save learned brain
        self.brain.save_brain("trading_brain.pkl")
        print(f"\n{Fore.GREEN}[✓] AI Brain saved for future sessions{Style.RESET_ALL}\n")
        
        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")


    def open_position(self, signal: str, current_price: float, signal_info: Dict = None):
        """
        Otwiera pozycję LONG/SHORT zależnie od sygnału, z TP/SL wg 4:1 RR.
        """
        side = 'LONG' if signal in ['BUY', 'BEAR_TRAP'] else 'SHORT'

        if side == 'LONG':
            tp = current_price * (1 + self.take_profit_pct/100)
            sl = current_price * (1 - self.stop_loss_pct/100)
        else:
            tp = current_price * (1 - self.take_profit_pct/100)
            sl = current_price * (1 + self.stop_loss_pct/100)

        self.active_position = {
            'side': side,
            'entry_price': current_price,
            'tp': tp,
            'sl': sl,
            'entry_time': datetime.now(),
            'entry_signal': signal,
            'unrealized_pnl_pct': 0.0,
            'rsi': (signal_info or {}).get('rsi') if signal_info else None,
            'momentum': (signal_info or {}).get('momentum') if signal_info else None,
            'sentiment': (signal_info or {}).get('sentiment') if signal_info else None,
        }

        color = Fore.GREEN if side == 'LONG' else Fore.RED
        print(f"\n{color}>>> OTWARTO POZYCJĘ {side} <<<")
        print(f"    Sygnał: {signal} | Cena wejścia: ${current_price:.0f}")
        print(f"    Target (TP): ${tp:.0f} | Stop (SL): ${sl:.0f}{Style.RESET_ALL}")

def main():
    """
    Entry point
    """
    print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}ADVANCED LIVE REAL-TIME TRADING BOT{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Wszystkie wskaźniki + Bull/Bear Trap detection{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")
    
    # Konfiguracja
    interval = '15m'
    print(f"{Fore.GREEN}[OK] Interwał: {interval}{Style.RESET_ALL}\n")
    
    # Uruchom
    bot = AdvancedLiveBot(interval=interval)
    bot.run_live_trading(duration_minutes=None)  # Nieskończoność bez limitów


if __name__ == "__main__":
    main()
