#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
24-Hour Real-Time Bot with HTML Live Dashboard
Bot gra 24h - wszystko widać na interaktywnym wykresiech HTML
"""

import sys
import time
import webbrowser
import threading
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.simulator.realtime_bot_sim import RealTimeBotSimulator
from trading_bot.simulator.html_dashboard import HTMLLiveDashboard, create_summary_stats
from colorama import Fore, Style, init

init(autoreset=True)


class BotWith24hDashboard:
    """
    Bot z HTML live dashboardem do 24h gry
    """
    
    def __init__(self, days: int = 1, interval: str = '15m'):
        """
        days: ile dni danych (dla 24h gry use days=1, interval='15m' = 96 candles)
        interval: '1m', '5m', '15m', '1h', '4h', '1d'
        """
        self.days = days
        self.interval = interval
        self.simulator = RealTimeBotSimulator(days=days, interval=interval)
        self.dashboard = HTMLLiveDashboard()
        self.html_file = "bot_dashboard_24h.html"
        
    def run_with_live_dashboard(self):
        """
        Uruchom bota z live HTML dashboardem
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] 24-HOUR BOT WITH LIVE HTML DASHBOARD{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # Pobierz dane
        if not self.simulator.fetch_real_data():
            return
        
        # Inicjalizuj bota
        if not self.simulator.initialize_bot():
            return
        
        print(f"\n{Fore.YELLOW}[*] Starting 24h simulation with {len(self.simulator.data)} candles...{Style.RESET_ALL}\n")
        
        # Thread do aktualizacji dashboardu
        dashboard_thread = threading.Thread(
            target=self._update_dashboard_loop,
            daemon=True
        )
        dashboard_thread.start()
        
        # Main simulation loop
        candle_times = []
        
        for idx, (timestamp, candle) in enumerate(self.simulator.data.iterrows()):
            try:
                self.simulator.process_candle(idx, candle)
                candle_times.append(timestamp)
                
                # Update dashboard co 5 candles
                if (idx + 1) % 5 == 0:
                    self._update_dashboard_now()
                
                # Symuluj real-time delay (szybciej niż 1 sec - dla demo)
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[!] Simulation stopped by user{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
                continue
        
        # Finalna aktualizacja
        self._update_dashboard_now()
        
        # Podsumowanie
        self._print_summary()
        
        # Otwórz HTML
        self._open_dashboard()
    
    def _update_dashboard_now(self):
        """
        Aktualizuj dashboard teraz
        """
        try:
            if len(self.simulator.data) > 0 and len(self.simulator.trades) > 0:
                html_chart = self.dashboard.create_interactive_chart(
                    data=self.simulator.data,
                    trades=self.simulator.trades,
                    equity_curve=self.simulator.equity_curve
                )
                
                self.dashboard.save_html(html_chart, self.html_file)
                
        except Exception as e:
            print(f"{Fore.RED}[!] Dashboard update error: {e}{Style.RESET_ALL}")
    
    def _update_dashboard_loop(self):
        """
        Thread loop - aktualizuj dashboard co 10 sekund
        """
        while True:
            time.sleep(10)
            self._update_dashboard_now()
    
    def _print_summary(self):
        """
        Wydrukuj podsumowanie
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] SIMULATION SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # Data info
        print(f"{Fore.CYAN}Data:{Style.RESET_ALL}")
        print(f"  Candles: {len(self.simulator.data)}")
        print(f"  Period: {self.simulator.data.index[0]} to {self.simulator.data.index[-1]}")
        print()
        
        # Trades
        print(f"{Fore.CYAN}Trades:{Style.RESET_ALL}")
        print(f"  Total: {len(self.simulator.trades)}")
        
        if self.simulator.trades:
            stats = create_summary_stats(self.simulator.trades)
            
            print(f"  Winning: {stats['winning_trades']}")
            print(f"  Losing: {stats['losing_trades']}")
            print(f"  Win Rate: {stats['win_rate']:.1f}%")
            print()
            
            print(f"{Fore.CYAN}Performance:{Style.RESET_ALL}")
            pnl_color = Fore.GREEN if stats['total_pnl'] > 0 else Fore.RED
            print(f"  Total P&L: {pnl_color}${stats['total_pnl']:.0f}{Style.RESET_ALL} ({stats['total_pnl_pct']:.2f}%)")
            print(f"  Largest Win: ${stats['largest_win']:.0f}")
            print(f"  Largest Loss: ${stats['largest_loss']:.0f}")
        else:
            print(f"  {Fore.YELLOW}No trades executed{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    def _open_dashboard(self):
        """
        Otwórz HTML dashboard w przeglądarce
        """
        print(f"{Fore.YELLOW}[*] Opening HTML dashboard...{Style.RESET_ALL}")
        
        try:
            file_path = Path(self.html_file).resolve()
            webbrowser.open(f'file://{file_path}')
            print(f"{Fore.GREEN}[OK] Dashboard opened: {self.html_file}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] Could not open browser: {e}{Style.RESET_ALL}")
            print(f"    Open manually: {Path(self.html_file).resolve()}")


def main():
    """
    Main entry point
    """
    
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}BOT 24H LIVE DASHBOARD{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print()
    print(f"Configuration:")
    print(f"  - 24h mode: 1 day of data")
    print(f"  - Interval: 15-minute candles (96 candles)")
    print(f"  - Stop Loss: -10% (loose SL para wiecej space)")
    print(f"  - Take Profit: +8%")
    print(f"  - HTML Dashboard: bot_dashboard_24h.html")
    print(f"  - Auto-refresh: Every 10 seconds")
    print()
    
    # 24h mode: 1 day z 15m interwałem = 96 candles
    bot = BotWith24hDashboard(days=1, interval='15m')
    bot.run_with_live_dashboard()


if __name__ == "__main__":
    main()
