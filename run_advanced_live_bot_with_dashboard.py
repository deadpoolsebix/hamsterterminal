#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MAIN RUNNER: Advanced Live Bot + HTML Dashboard
Gra bez limitów na LIVE danych z wykresami
"""

import sys
import time
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
import pandas as pd

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from advanced_live_bot import AdvancedLiveBot
from advanced_html_dashboard import AdvancedHTMLDashboard
from trading_bot.simulator.real_data_fetcher import RealDataFetcher
from colorama import Fore, Style, init

init(autoreset=True)


class LiveBotWithDashboard:
    """
    Bot z HTML Dashboard - dwa wykresy
    """
    
    def __init__(self, interval: str = '15m', update_frequency: int = 30):
        self.interval = interval
        self.update_frequency = update_frequency  # sekundy
        self.bot = AdvancedLiveBot(interval=interval)
        self.dashboard = AdvancedHTMLDashboard()
        self.running = True
        self.dashboard_thread = None
        
    def update_dashboard_loop(self):
        """
        Background thread - aktualizuj dashboard co X sekund
        """
        while self.running and len(self.bot.trades) > 0:
            try:
                # Pobierz dane
                fetcher = RealDataFetcher()
                data = fetcher.fetch_btc_data(days=7, interval=self.interval)
                
                if data is None or len(data) == 0:
                    time.sleep(10)
                    continue
                
                data = data.tail(200)
                
                # Oblicz wskaźniki
                indicators = self.bot.calculate_all_indicators(data)
                
                if indicators is None:
                    time.sleep(10)
                    continue
                
                # Połącz zamknięte pozycje z sygnałami
                all_trades = self.bot.trades + self.bot.closed_positions
                
                # Stwórz dashboard
                html = self.dashboard.create_full_dashboard(
                    data=data,
                    indicators=indicators,
                    trades=all_trades,
                    starting_capital=self.bot.start_capital
                )
                
                # Zapisz
                filename = "bot_dashboard_live.html"
                self.dashboard.save_dashboard(html, filename)
                
                print(f"{Fore.GREEN}[OK] Dashboard zaktualizowany: {filename}{Style.RESET_ALL}")
                
                time.sleep(self.update_frequency)
                
            except Exception as e:
                print(f"{Fore.RED}[!] Błąd dashboard: {e}{Style.RESET_ALL}")
                time.sleep(10)
    
    def run(self, demo_mode: bool = False):
        """
        Uruchom bota z dashboardem
        demo_mode: jeśli True, gra przez 5 iteracji, inaczej nieskończoność
        """
        
        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] ADVANCED LIVE BOT WITH HTML DASHBOARD{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")
        
        # Uruchom background thread dla dashboarda
        print(f"{Fore.YELLOW}[*] Uruchamianie background thread dla dashboarda...{Style.RESET_ALL}")
        self.dashboard_thread = threading.Thread(target=self.update_dashboard_loop, daemon=True)
        self.dashboard_thread.start()
        
        print(f"{Fore.GREEN}[OK] Dashboard thread uruchomiony{Style.RESET_ALL}\n")
        
        try:
            # Uruchom bota
            if demo_mode:
                print(f"{Fore.YELLOW}[*] DEMO MODE - 5 iteracji{Style.RESET_ALL}\n")
                
                # Hack: zmień running na False po 5 iteracjach
                iteration_count = 0
                original_iteration = self.bot.iteration
                
                while self.bot.running and iteration_count < 5:
                    self.bot.run_live_trading(duration_minutes=None)
                    break
                    
            else:
                # Normalny tryb - nieskończoność
                self.bot.run_live_trading(duration_minutes=None)
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Bot zatrzymany{Style.RESET_ALL}")
        finally:
            self.running = False
            
            # Czekaj na thread
            if self.dashboard_thread:
                self.dashboard_thread.join(timeout=5)
            
            # Otwórz ostatni dashboard
            self._open_final_dashboard()
    
    def _open_final_dashboard(self):
        """
        Otwórz ostatni dashboard w przeglądarce
        """
        try:
            # Pobierz ostatnie dane
            fetcher = RealDataFetcher()
            data = fetcher.fetch_btc_data(days=7, interval=self.interval)
            
            if data is not None and len(data) > 0:
                data = data.tail(200)
                
                # Oblicz wskaźniki
                indicators = self.bot.calculate_all_indicators(data)
                
                if indicators is not None:
                    # Połącz zamknięte pozycje z sygnałami
                    all_trades = self.bot.trades + self.bot.closed_positions
                    
                    # Stwórz final dashboard
                    html = self.dashboard.create_full_dashboard(
                        data=data,
                        indicators=indicators,
                        trades=all_trades,
                        starting_capital=self.bot.start_capital
                    )
                    
                    # Zapisz
                    filename = "bot_dashboard_final.html"
                    self.dashboard.save_dashboard(html, filename)
                    
                    print(f"\n{Fore.GREEN}[OK] Final dashboard: {filename}{Style.RESET_ALL}")
                    
                    # Otwórz
                    import webbrowser
                    webbrowser.open(f"file://{Path(filename).absolute()}")
                    print(f"{Fore.GREEN}[OK] Otwieranie dashboarda w przeglądarce...{Style.RESET_ALL}\n")
                    
        except Exception as e:
            print(f"{Fore.RED}[!] Błąd przy otwieraniu dashboarda: {e}{Style.RESET_ALL}")


def print_banner():
    """Wydrukuj banner"""
    print(f"\n{Fore.CYAN}")
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                   ADVANCED LIVE REAL-TIME TRADING BOT                                              ║
    ║                                                                                                      ║
    ║  Features:                                                                                           ║
    ║  ✓ Live Trading bez limitów świec                                                                   ║
    ║  ✓ Wszystkie wskaźniki: RSI, MACD, Bollinger Bands, Sentiment, ATR, Momentum, Volume                ║
    ║  ✓ FVG (Fair Value Gap) Detection                                                                   ║
    ║  ✓ Bull Trap & Bear Trap Detection                                                                  ║
    ║  ✓ Dwa profesjonalne wykresy: Technical Analysis + Equity Curve                                     ║
    ║  ✓ HTML Dashboard z Plotly                                                                          ║
    ║  ✓ BUY, SELL, BULL_TRAP, BEAR_TRAP Sygnały                                                          ║
    ║  ✓ Real-time data z Yahoo Finance                                                                   ║
    ║  ✓ Auto-refresh dashboarda co 30 sekund                                                             ║
    ║                                                                                                      ║
    ║  Interval: 15m (czeka 15 minut między candles)                                                      ║
    ║  Stop Loss: -10%  |  Take Profit: +8%                                                               ║
    ║                                                                                                      ║
    ║  HTML Files: bot_dashboard_live.html (live) | bot_dashboard_final.html (final)                     ║
    ║                                                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
    """)
    print(Style.RESET_ALL)


def main():
    """
    Entry point
    """
    print_banner()
    
    print(f"{Fore.YELLOW}Inicjalizacja...{Style.RESET_ALL}\n")
    
    # Konfiguracja
    interval = '15m'
    dashboard_update_freq = 30  # sekundy
    
    print(f"{Fore.GREEN}Konfiguracja:{Style.RESET_ALL}")
    print(f"  Interval: {interval}")
    print(f"  Dashboard Update: co {dashboard_update_freq}s")
    print(f"  Mode: LIVE TRADING (bez limitów)\n")
    
    # Stwórz i uruchom
    bot_runner = LiveBotWithDashboard(
        interval=interval,
        update_frequency=dashboard_update_freq
    )
    
    bot_runner.run(demo_mode=False)


if __name__ == "__main__":
    main()
