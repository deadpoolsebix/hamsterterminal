#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Real-Time Bot Simulator
Bot gra na realnych danych w tempie rzeczywistym
"""

import sys
import os
import time
import threading
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from trading_bot.simulator.real_data_fetcher import RealDataFetcher
from trading_bot.complete_bot import CompleteTradingBot
from colorama import Fore, Style, init

init(autoreset=True)


class RealTimeBotSimulator:
    """
    Symulator bota w RZECZYWISTYM TEMPIE na realnych danych
    """
    
    def __init__(self, days: int = 7, interval: str = '1h'):
        self.days = days
        self.interval = interval
        self.data = None
        self.bot = None
        self.trades = []
        self.equity_curve = [5000]
        self.current_position = None
        self.candle_count = 0
        self.running = True
        
    def fetch_real_data(self) -> bool:
        """
        Pobierz realne dane BTC
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] POBIERANIE REALNYCH DANYCH{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        try:
            fetcher = RealDataFetcher()
            self.data = fetcher.fetch_btc_data(days=self.days, interval=self.interval)
            
            if self.data is None or len(self.data) == 0:
                print(f"{Fore.RED}[!] Nie udalo sie pobrac danych{Style.RESET_ALL}")
                return False
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Blad: {e}{Style.RESET_ALL}")
            return False
    
    def initialize_bot(self):
        """
        Inicjalizuj bota
        """
        print(f"\n{Fore.CYAN}[*] Inicjalizacja bota...{Style.RESET_ALL}")
        
        try:
            self.bot = CompleteTradingBot(
                symbol='BTCUSDT',
                account_size=5000,
                leverage=100,
                risk_per_trade=250
            )
            print(f"{Fore.GREEN}[OK] Bot zainicjalizowany{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Blad inicjalizacji: {e}{Style.RESET_ALL}")
            return False
    
    def process_candle(self, candle_idx: int, candle_data: pd.Series):
        """
        Przetwórz pojedynczy candle
        """
        self.candle_count += 1
        
        timestamp = candle_data.name
        open_price = candle_data['open']
        high = candle_data['high']
        low = candle_data['low']
        close = candle_data['close']
        volume = candle_data['volume']
        
        print(f"\n{Fore.CYAN}[Candle #{self.candle_count}]{Style.RESET_ALL} {timestamp}")
        print(f"  Cena: {Fore.YELLOW}${open_price:.0f}{Style.RESET_ALL} -> {Fore.YELLOW}${close:.0f}{Style.RESET_ALL} (H: ${high:.0f}, L: ${low:.0f})")
        print(f"  Volume: {volume:,.0f}")
        
        if candle_idx > 5:
            self.simulate_trade_decision(candle_idx, close)
        
        self.equity_curve.append(5000)
    
    def simulate_trade_decision(self, candle_idx: int, current_price: float):
        """
        Symuluj decyzje tradera
        """
        try:
            prev_data = self.data.iloc[max(0, candle_idx-30):candle_idx]
            
            if len(prev_data) < 5:
                return
            
            sma_short = prev_data['close'].tail(5).mean()
            sma_medium = prev_data['close'].tail(10).mean()
            sma_long = prev_data['close'].tail(20).mean()
            
            recent_returns = prev_data['close'].pct_change().tail(10)
            volatility = recent_returns.std()
            
            buy_condition = (
                sma_short > sma_medium and 
                sma_medium > sma_long and
                current_price > sma_short and
                volatility < 0.02 and
                self.current_position is None
            )
            
            sell_condition = (
                sma_short < sma_medium and
                self.current_position is not None
            )
            
            if buy_condition:
                self.execute_buy(current_price, candle_idx, volatility * 100)
            
            elif sell_condition:
                self.execute_sell(current_price, candle_idx, volatility * 100)
            
        except Exception as e:
            print(f"{Fore.RED}Blad: {e}{Style.RESET_ALL}")
    
    def execute_buy(self, price: float, candle_idx: int, volatility: float):
        """
        Wykonaj kupno
        """
        self.current_position = {
            'side': 'LONG',
            'entry_price': price,
            'entry_time': self.data.index[candle_idx],
            'volatility': volatility,
            'take_profit': price * 1.08,  # TP +8%
            'stop_loss': price * 0.90     # SL -10% (wiecej space)
        }
        
        print(f"{Fore.GREEN}[BUY] KUPNO (LONG){Style.RESET_ALL}")
        print(f"   Entry: ${price:.0f}")
        print(f"   TP: ${self.current_position['take_profit']:.0f}")
        print(f"   SL: ${self.current_position['stop_loss']:.0f}")
    
    def execute_sell(self, price: float, candle_idx: int, volatility: float):
        """
        Wykonaj sprzedaz
        """
        if self.current_position is None:
            return
        
        entry = self.current_position['entry_price']
        pnl = price - entry
        pnl_pct = (pnl / entry) * 100
        
        exit_reason = 'TAKE_PROFIT' if price >= self.current_position['take_profit'] else 'STOP_LOSS'
        
        trade = {
            'entry_time': self.current_position['entry_time'],
            'exit_time': self.data.index[candle_idx],
            'entry_price': entry,
            'exit_price': price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': exit_reason
        }
        
        self.trades.append(trade)
        
        color = Fore.GREEN if pnl > 0 else Fore.RED
        print(f"{Fore.RED}[SELL] SPRZEDAZ (EXIT){Style.RESET_ALL}")
        print(f"   Exit: ${price:.0f}")
        print(f"   P&L: {color}${pnl:.0f} ({pnl_pct:.2f}%){Style.RESET_ALL}")
        print(f"   Reason: {exit_reason}")
        
        self.current_position = None
    
    def run_simulation(self):
        """
        Uruchom pelna symulacje
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] URUCHAMIANIE SYMULATORA REAL-TIME{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        if not self.fetch_real_data():
            return False
        
        if not self.initialize_bot():
            return False
        
        print(f"\n{Fore.YELLOW}[*] Poczatek symulacji...{Style.RESET_ALL}\n")
        
        for idx, (timestamp, candle) in enumerate(self.data.iterrows()):
            try:
                self.process_candle(idx, candle)
                time.sleep(0.3)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[!] Przerwane{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}[!] Blad: {e}{Style.RESET_ALL}")
                continue
        
        self.print_summary()
        return True
    
    def print_summary(self):
        """
        Podsumowanie
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] PODSUMOWANIE{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        print(f"  Candles: {self.candle_count}")
        print(f"  Transakcji: {len(self.trades)}")
        
        if not self.trades:
            print(f"\n{Fore.YELLOW}[!] Brak transakcji{Style.RESET_ALL}\n")
            return
        
        winning = [t for t in self.trades if t['pnl'] > 0]
        losing = [t for t in self.trades if t['pnl'] < 0]
        
        print(f"  Zyski: {len(winning)}")
        print(f"  Straty: {len(losing)}")
        print(f"  Win rate: {(len(winning) / len(self.trades) * 100):.1f}%")
        
        total_pnl = sum([t['pnl'] for t in self.trades])
        total_pnl_pct = (total_pnl / 5000) * 100
        
        color = Fore.GREEN if total_pnl > 0 else Fore.RED
        print(f"  Total P&L: {color}${total_pnl:.0f}{Style.RESET_ALL} ({total_pnl_pct:.2f}%)")
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")


def main():
    simulator = RealTimeBotSimulator(days=7, interval='1h')
    simulator.run_simulation()


if __name__ == "__main__":
    main()
