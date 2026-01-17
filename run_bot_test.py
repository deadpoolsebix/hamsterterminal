#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Real-Time Bot Test with CSV Report
Symulacja bota na realnych danych z raportem wynikow
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.simulator.realtime_bot_sim import RealTimeBotSimulator
from colorama import Fore, Style, init

init(autoreset=True)


def save_trade_report(simulator, filename: str = "bot_trades.csv"):
    """
    Zapisz wszystkie transakcje do CSV
    """
    if not simulator.trades:
        print(f"{Fore.YELLOW}[!] Brak transakcji do zapisania{Style.RESET_ALL}")
        return
    
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Liczba', 'Entry Time', 'Entry Price', 'Exit Time', 'Exit Price',
                'P&L (USD)', 'P&L (%)', 'Exit Reason', 'Duration (min)'
            ])
            
            # Trades
            for idx, trade in enumerate(simulator.trades, 1):
                duration_min = (trade['exit_time'] - trade['entry_time']).total_seconds() / 60
                
                writer.writerow([
                    idx,
                    trade['entry_time'],
                    f"${trade['entry_price']:.2f}",
                    trade['exit_time'],
                    f"${trade['exit_price']:.2f}",
                    f"${trade['pnl']:.2f}",
                    f"{trade['pnl_pct']:.2f}%",
                    trade['exit_reason'],
                    f"{duration_min:.0f}"
                ])
        
        print(f"{Fore.GREEN}[OK] Raporty zapisane: {filename}{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}[!] Blad zapisu: {e}{Style.RESET_ALL}")


def main():
    """
    Main - uruchom test z raportem
    """
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] REAL-TIME BOT TEST WITH CSV REPORT{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    # Konfiguracja
    print(f"{Fore.YELLOW}[*] Configuration:{Style.RESET_ALL}")
    print(f"    - Days: 7")
    print(f"    - Interval: 1h")
    print(f"    - Starting Capital: $5,000")
    print(f"    - Risk per Trade: $250\n")
    
    # Uruchom symulację
    simulator = RealTimeBotSimulator(days=7, interval='1h')
    simulator.run_simulation()
    
    # Zapisz raport
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"bot_trades_{timestamp}.csv"
    
    print(f"\n{Fore.CYAN}[*] Saving report...{Style.RESET_ALL}")
    save_trade_report(simulator, report_file)
    
    # Wydrukuj summary
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] FINAL SUMMARY{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}[*] Total trades: {len(simulator.trades)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Report file: {report_file}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
