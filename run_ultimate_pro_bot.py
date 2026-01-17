#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RUN ULTIMATE PRO BOT
Bot z MEGA dashboardem zawierającym WSZYSTKIE dane!
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
from ultimate_pro_dashboard import UltimateProDashboard
from trading_bot.simulator.real_data_fetcher import RealDataFetcher
from colorama import Fore, Style, init

init(autoreset=True)


class UltimateProfessionalBot:
    """
    ULTIMATE BOT z MEGA dashboardem
    """
    
    def __init__(self, interval: str = '15m', update_frequency: int = 60):
        self.interval = interval
        self.update_frequency = update_frequency
        self.bot = AdvancedLiveBot(interval=interval)
        self.dashboard = UltimateProDashboard()
        self.running = True
        self.dashboard_thread = None
        
    def update_dashboard_loop(self):
        """
        Background thread - aktualizuj dashboard
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
                
                # Stwórz ULTIMATE dashboard
                html = self.dashboard.create_full_ultra_dashboard(
                    data=data,
                    indicators=indicators,
                    trades=all_trades,
                    starting_capital=self.bot.start_capital
                )
                
                # Zapisz
                filename = "ultimate_dashboard_live.html"
                self.dashboard.save_dashboard(html, filename)
                
                print(f"{Fore.GREEN}[OK] Ultimate Dashboard zaktualizowany{Style.RESET_ALL}")
                
                time.sleep(self.update_frequency)
                
            except Exception as e:
                print(f"{Fore.RED}[!] Błąd dashboard: {e}{Style.RESET_ALL}")
                time.sleep(10)
    
    def run(self):
        """
        Uruchom ULTIMATE bota
        """
        
        print_mega_banner()
        
        print(f"{Fore.YELLOW}Inicjalizacja...{Style.RESET_ALL}\n")
        
        # Konfiguracja
        interval = '15m'
        dashboard_update_freq = 60  # sekundy
        
        print(f"{Fore.GREEN}Konfiguracja:{Style.RESET_ALL}")
        print(f"  Interval: {interval}")
        print(f"  Dashboard Update: co {dashboard_update_freq}s")
        print(f"  Mode: ULTIMATE PROFESSIONAL\n")
        
        # Uruchom background thread
        print(f"{Fore.YELLOW}[*] Uruchamianie Ultimate Dashboard thread...{Style.RESET_ALL}")
        self.dashboard_thread = threading.Thread(target=self.update_dashboard_loop, daemon=True)
        self.dashboard_thread.start()
        
        print(f"{Fore.GREEN}[OK] Dashboard thread uruchomiony\n{Style.RESET_ALL}")
        
        try:
            # Uruchom bota
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
        Otwórz ostatni ULTIMATE dashboard
        """
        try:
            print(f"\n{Fore.YELLOW}[*] Generowanie final dashboarda...{Style.RESET_ALL}")
            
            # Pobierz ostatnie dane
            fetcher = RealDataFetcher()
            data = fetcher.fetch_btc_data(days=7, interval=self.interval)
            
            if data is not None and len(data) > 0:
                data = data.tail(200)
                
                # Oblicz wskaźniki
                indicators = self.bot.calculate_all_indicators(data)
                
                if indicators is not None:
                    # Połącz wszystkie dane
                    all_trades = self.bot.trades + self.bot.closed_positions
                    
                    # Stwórz ULTIMATE dashboard
                    html = self.dashboard.create_full_ultra_dashboard(
                        data=data,
                        indicators=indicators,
                        trades=all_trades,
                        starting_capital=self.bot.start_capital
                    )
                    
                    # Zapisz
                    filename = "ultimate_dashboard_final.html"
                    self.dashboard.save_dashboard(html, filename)
                    
                    print(f"{Fore.GREEN}[OK] Final dashboard: {filename}{Style.RESET_ALL}")
                    
                    # Otwórz
                    webbrowser.open(f"file://{Path(filename).absolute()}")
                    print(f"{Fore.GREEN}[OK] Otwieranie dashboarda w przeglądarce...{Style.RESET_ALL}\n")
                    
        except Exception as e:
            print(f"{Fore.RED}[!] Błąd: {e}{Style.RESET_ALL}")


def print_mega_banner():
    """Mega banner"""
    print(f"\n{Fore.CYAN}")
    print("""
    ╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                    ULTIMATE PROFESSIONAL TRADING BOT DASHBOARD                                           ║
    ║                                                                                                            ║
    ║  🚀 MEGA Features - WSZYSTKIE dane na jednym wykresie:                                                    ║
    ║                                                                                                            ║
    ║  📊 PRICE ACTION ANALYSIS:                                                                               ║
    ║     ✓ 50% Price Division (Internal/External Zones)     ✓ Support & Resistance                           ║
    ║     ✓ Equal Highs & Equal Lows (EQH/EQL)              ✓ Wyckoff Phase Detection                          ║
    ║     ✓ Liquidity Grab Detection                         ✓ Bollinger Bands                                 ║
    ║     ✓ SMA 20, 50 Moving Averages                       ✓ Wick Price & Action Analysis                   ║
    ║                                                                                                            ║
    ║  🎯 TRADING MANAGEMENT:                                                                                  ║
    ║     ✓ Real-time Position Tracking                      ✓ Automatic Liquidation (TP/SL)                  ║
    ║     ✓ Win/Loss Statistics                              ✓ P&L Performance Metrics                        ║
    ║     ✓ Session Information (Asian/London/NY)            ✓ Volume Analysis                                 ║
    ║                                                                                                            ║
    ║  🔧 TECHNICAL INDICATORS:                                                                                ║
    ║     ✓ RSI (14)                                         ✓ MACD + Signal Line                              ║
    ║     ✓ Momentum Indicator                               ✓ Sentiment Analysis                              ║
    ║     ✓ ATR                                              ✓ CVD (Cumulative Volume Delta)                   ║
    ║                                                                                                            ║
    ║  💡 INTELLIGENT ENTRY/EXIT:                                                                              ║
    ║     ✓ Bull Trap Detection                              ✓ Bear Trap Detection                             ║
    ║     ✓ Convergence/Divergence Signals                   ✓ Smart Money Technique (ICT)                    ║
    ║     ✓ Open Range Breakout (ORB)                        ✓ FVG (Fair Value Gap)                            ║
    ║                                                                                                            ║
    ║  Configuration:                                                                                          ║
    ║     Interval: 15 minutes                                                                                 ║
    ║     Mode: LIVE REAL-TIME TRADING                                                                        ║
    ║     Stop Loss: -10%  |  Take Profit: +8%                                                                ║
    ║     Dashboard Update: Every 60 seconds                                                                   ║
    ║                                                                                                            ║
    ║  Output Files:                                                                                           ║
    ║     ultimate_dashboard_live.html - Live updates every 60 seconds                                        ║
    ║     ultimate_dashboard_final.html - Final comprehensive report                                          ║
    ║                                                                                                            ║
    ║  ⚠️  DISCLAIMER: This is a sophisticated trading tool for educational purposes only.                     ║
    ║     Always test on paper trading before using with real capital.                                        ║
    ║                                                                                                            ║
    ╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
    """)
    print(Style.RESET_ALL)


def main():
    """
    Entry point
    """
    bot_runner = UltimateProfessionalBot(
        interval='15m',
        update_frequency=60
    )
    
    bot_runner.run()


if __name__ == "__main__":
    main()
