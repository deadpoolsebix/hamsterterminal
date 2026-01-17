#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LIVE REAL-TIME BOT - Czeka rzeczywisty czas, gra na LIVE danych
Bot gra w NORMALNYM TEMPIE RZECZYWISTYM - czeka między candles
Pobiera BIEŻĄCE dane z rynku, a nie historyczne!
"""

import sys
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import deque

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.simulator.real_data_fetcher import RealDataFetcher
from trading_bot.complete_bot import CompleteTradingBot
from colorama import Fore, Style, init

init(autoreset=True)


class LiveRealTimeBotTrader:
    """
    LIVE BOT - gra w rzeczywistym tempie czasu
    - Czeka rzeczywisty czas między candles
    - Pobiera LIVE dane z rynku
    - Gra logicznie na bieżących danych
    """
    
    def __init__(self, interval: str = '15m'):
        """
        interval: Interwał świec
        - '1m' = czeka 1 minutę między candles
        - '5m' = czeka 5 minut
        - '15m' = czeka 15 minut
        - '1h' = czeka 1 godzinę
        """
        self.interval = interval
        self.bot = None
        self.trades = []
        self.signals = []
        self.candles_history = deque(maxlen=100)  # Ostatnie 100 candles
        self.running = True
        self.last_candle_time = None
        self.candle_count = 0
        self.start_capital = 5000
        self.current_equity = self.start_capital
        
        # Mapuj interval na sekundy
        self.interval_map = {
            '1m': 60,
            '5m': 5 * 60,
            '15m': 15 * 60,
            '1h': 60 * 60,
            '4h': 4 * 60 * 60,
        }
        
        self.wait_seconds = self.interval_map.get(interval, 60)
        
    def initialize_bot(self):
        """
        Inicjalizuj bota
        """
        print(f"\n{Fore.CYAN}[*] Inicjalizacja bota...{Style.RESET_ALL}")
        
        try:
            self.bot = CompleteTradingBot(
                symbol='BTCUSDT',
                account_size=self.start_capital,
                leverage=100,
                risk_per_trade=250
            )
            print(f"{Fore.GREEN}[OK] Bot zainicjalizowany{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    Starting Capital: ${self.start_capital:,}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Blad inicjalizacji: {e}{Style.RESET_ALL}")
            return False
    
    def fetch_latest_candles(self, num_candles: int = 50) -> pd.DataFrame:
        """
        Pobierz OSTATNIE candles z rynku (nie historyczne!)
        num_candles: ile ostatnich candles pobrać do analizy
        """
        try:
            fetcher = RealDataFetcher()
            
            # Pobierz ostatnie 7 dni, ale zwróć tylko ostatnie N candles
            all_data = fetcher.fetch_btc_data(days=7, interval=self.interval)
            
            if all_data is None or len(all_data) == 0:
                return None
            
            # Zwróć tylko ostatnie N candles
            return all_data.tail(num_candles)
            
        except Exception as e:
            print(f"{Fore.RED}[!] Blad pobierania danych: {e}{Style.RESET_ALL}")
            return None
    
    def analyze_current_market(self, latest_candles: pd.DataFrame) -> dict:
        """
        Przeanalizuj AKTUALNY stan rynku
        Zwróć sygnały buy/sell na podstawie bieżących danych
        """
        if len(latest_candles) < 20:
            return {'signal': 'WAIT', 'reason': 'Not enough data'}
        
        try:
            current_price = latest_candles['close'].iloc[-1]
            
            # Moving Averages na bieżących danych
            sma_5 = latest_candles['close'].tail(5).mean()
            sma_10 = latest_candles['close'].tail(10).mean()
            sma_20 = latest_candles['close'].tail(20).mean()
            
            # Volatility
            recent_returns = latest_candles['close'].pct_change().tail(10)
            volatility = recent_returns.std()
            
            # Trend
            trend = "UP" if sma_5 > sma_10 > sma_20 else "DOWN"
            
            # Buy signal
            buy_signal = (
                sma_5 > sma_10 and
                sma_10 > sma_20 and
                current_price > sma_5 and
                volatility < 0.02
            )
            
            # Sell signal
            sell_signal = (sma_5 < sma_10)
            
            return {
                'signal': 'BUY' if buy_signal else 'SELL' if sell_signal else 'HOLD',
                'price': current_price,
                'sma_5': sma_5,
                'sma_10': sma_10,
                'sma_20': sma_20,
                'trend': trend,
                'volatility': volatility,
                'reason': f"Trend: {trend}, Vol: {volatility:.4f}"
            }
            
        except Exception as e:
            return {'signal': 'ERROR', 'reason': str(e)}
    
    def run_live_trading(self):
        """
        MAIN LIVE LOOP - czeka rzeczywisty czas między candles
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] LIVE REAL-TIME TRADING BOT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}Configuration:{Style.RESET_ALL}")
        print(f"  Interval: {self.interval}")
        print(f"  Wait time: {self.wait_seconds} seconds ({self.wait_seconds/60:.1f} minutes)")
        print(f"  Starting Capital: ${self.start_capital:,}")
        print(f"  Stop Loss: -10%")
        print(f"  Take Profit: +8%")
        print()
        
        if not self.initialize_bot():
            return
        
        print(f"{Fore.YELLOW}[*] Waiting for first data fetch...{Style.RESET_ALL}\n")
        
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                
                # Pobierz AKTUALNE dane z rynku
                print(f"\n{Fore.CYAN}[Iteration #{iteration}]{Style.RESET_ALL} {datetime.now()}")
                print(f"{Fore.YELLOW}[*] Pobieranie LIVE danych z rynku...{Style.RESET_ALL}")
                
                latest_candles = self.fetch_latest_candles(num_candles=50)
                
                if latest_candles is None or len(latest_candles) == 0:
                    print(f"{Fore.RED}[!] Nie udalo sie pobrac danych{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}[*] Czekam 30 sekund przed ponowną próbą...{Style.RESET_ALL}")
                    time.sleep(30)
                    continue
                
                # Ostatni candle
                last_row = latest_candles.iloc[-1]
                self.candle_count += 1
                
                print(f"{Fore.GREEN}[OK] Otrzymano dane{Style.RESET_ALL}")
                print(f"  Liczba candles: {len(latest_candles)}")
                print(f"  Bieżąca cena: ${last_row['close']:.0f}")
                print(f"  Ostatni candle: {latest_candles.index[-1]}")
                
                # Przeanalizuj rynek
                market_analysis = self.analyze_current_market(latest_candles)
                signal = market_analysis['signal']
                
                print(f"\n{Fore.CYAN}Market Analysis:{Style.RESET_ALL}")
                print(f"  Signal: {Fore.YELLOW}{signal}{Style.RESET_ALL}")
                print(f"  Trend: {market_analysis.get('trend', 'N/A')}")
                print(f"  Price: ${market_analysis.get('price', 0):.0f}")
                print(f"  SMA5: ${market_analysis.get('sma_5', 0):.0f}")
                print(f"  SMA10: ${market_analysis.get('sma_10', 0):.0f}")
                print(f"  SMA20: ${market_analysis.get('sma_20', 0):.0f}")
                print(f"  Volatility: {market_analysis.get('volatility', 0):.4f}")
                
                # Wylicz TP i SL
                current_price = market_analysis['price']
                tp_price = current_price * 1.08  # +8%
                sl_price = current_price * 0.90  # -10%
                
                print(f"\n{Fore.CYAN}Risk Management:{Style.RESET_ALL}")
                print(f"  Current Price: ${current_price:.0f}")
                print(f"  Take Profit: ${tp_price:.0f} (+8%)")
                print(f"  Stop Loss: ${sl_price:.0f} (-10%)")
                
                # Logika handlowa
                if signal == 'BUY':
                    print(f"\n{Fore.GREEN}>>> SYGNAŁ KUPNA <<<{Style.RESET_ALL}")
                    self.trades.append({
                        'type': 'BUY',
                        'time': datetime.now(),
                        'price': current_price,
                        'tp': tp_price,
                        'sl': sl_price
                    })
                    
                elif signal == 'SELL':
                    print(f"\n{Fore.RED}>>> SYGNAŁ SPRZEDAŻY <<<{Style.RESET_ALL}")
                    self.trades.append({
                        'type': 'SELL',
                        'time': datetime.now(),
                        'price': current_price
                    })
                
                else:
                    print(f"\n{Fore.YELLOW}>>> CZEKAM NA SYGNAŁ <<<{Style.RESET_ALL}")
                
                # Zapisz candle do historii
                self.candles_history.append({
                    'time': latest_candles.index[-1],
                    'price': current_price
                })
                
                # CZEKAJ rzeczywisty czas do następnego candle
                print(f"\n{Fore.CYAN}[*] Czekam {self.wait_seconds}s ({self.wait_seconds/60:.1f} min) do następnego candle...{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[*] Następna aktualizacja: {datetime.now() + timedelta(seconds=self.wait_seconds)}{Style.RESET_ALL}\n")
                
                time.sleep(self.wait_seconds)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[!] Bot zatrzymany przez użytkownika{Style.RESET_ALL}")
                self.running = False
                break
                
            except Exception as e:
                print(f"{Fore.RED}[!] Błąd: {e}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[*] Czekam 30 sekund...{Style.RESET_ALL}")
                time.sleep(30)
                continue
        
        self._print_final_summary()
    
    def _print_final_summary(self):
        """
        Podsumowanie gry
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] PODSUMOWANIE{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        print(f"Bot Sessions: {self.candle_count}")
        print(f"Signals Generated: {len(self.trades)}")
        print(f"Start Capital: ${self.start_capital:,}")
        print(f"Current Equity: ${self.current_equity:,}")
        
        if self.trades:
            print(f"\n{Fore.CYAN}Recent Signals:{Style.RESET_ALL}")
            for i, trade in enumerate(self.trades[-10:], 1):  # Ostatnie 10
                time_str = trade['time'].strftime("%Y-%m-%d %H:%M:%S")
                price = trade.get('price', 0)
                print(f"  {i}. {trade['type']:4s} @ ${price:10.0f} ({time_str})")
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")


def main():
    """
    Main entry point
    """
    
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}LIVE REAL-TIME TRADING BOT{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Gra w rzeczywistym tempie na LIVE danych{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    print(f"Uwaga: Bot będzie czekał rzeczywisty czas między candles!")
    print(f"Jeśli wybierzesz 15m interwał, czeka 15 minut między analizami.")
    print()
    
    # Wybierz interwał
    print(f"{Fore.YELLOW}Dostępne interwały:{Style.RESET_ALL}")
    print(f"  1m  - czeka 1 minutę")
    print(f"  5m  - czeka 5 minut")
    print(f"  15m - czeka 15 minut (rekomendowane)")
    print(f"  1h  - czeka 1 godzinę")
    print()
    
    # Dla demo: 15m interwał
    interval = '15m'
    print(f"{Fore.GREEN}[OK] Wybrany interwał: {interval}{Style.RESET_ALL}\n")
    
    # Uruchom bota
    trader = LiveRealTimeBotTrader(interval=interval)
    trader.run_live_trading()


if __name__ == "__main__":
    main()
