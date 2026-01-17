#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Live Dashboard - Real-time terminal display
Aktualizuje się w real-time podczas symulacji
"""

import os
import sys
from datetime import datetime
from typing import Dict, List
import time
from colorama import Fore, Back, Style, init

init(autoreset=True)


class LiveDashboard:
    """
    Live dashboard w terminalu
    - Account status
    - Active positions
    - Recent signals
    - Performance metrics
    """
    
    def __init__(self):
        self.last_equity = 5000
        self.peak_equity = 5000
        
    def clear_screen(self):
        """Wyczyść ekran"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print header"""
        print("\n" + "="*80)
        print(f"{Fore.CYAN}🤖 ADVANCED TRADING BOT - 7 DAY LIVE SIMULATION{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print("="*80)
    
    def print_account_section(self, equity: float, peak: float, pnl: float):
        """Print account info"""
        pnl_pct = (pnl / 5000) * 100
        
        print(f"\n{Fore.YELLOW}💰 ACCOUNT STATUS{Style.RESET_ALL}")
        print(f"   Starting Capital:  ${5000:>10,.0f}")
        print(f"   Current Equity:    ${equity:>10,.0f} {Fore.GREEN}✓{Style.RESET_ALL}")
        print(f"   Peak Equity:       ${peak:>10,.0f}")
        print(f"   Total P&L:         ${pnl:>10,.0f}  {Fore.GREEN if pnl > 0 else Fore.RED}{pnl_pct:+.2f}%{Style.RESET_ALL}")
        
        drawdown = ((peak - equity) / peak) * 100
        color = Fore.RED if drawdown > 20 else Fore.YELLOW if drawdown > 10 else Fore.GREEN
        print(f"   Max Drawdown:      {color}{drawdown:>9.2f}%{Style.RESET_ALL}")
    
    def print_trades_section(self, trades: List[Dict]):
        """Print recent trades"""
        print(f"\n{Fore.YELLOW}📊 TRADING ACTIVITY{Style.RESET_ALL}")
        
        if not trades:
            print("   No trades yet")
            return
        
        print(f"   Total Trades: {len(trades)}")
        
        winning = [t for t in trades if t['pnl'] > 0]
        losing = [t for t in trades if t['pnl'] < 0]
        
        win_rate = (len(winning) / len(trades) * 100) if trades else 0
        
        print(f"   Winning:      {Fore.GREEN}{len(winning)}{Style.RESET_ALL} ({win_rate:.1f}%)")
        print(f"   Losing:       {Fore.RED}{len(losing)}{Style.RESET_ALL} ({100-win_rate:.1f}%)")
        
        # Last 3 trades
        print(f"\n   {Fore.CYAN}Recent Trades:{Style.RESET_ALL}")
        for trade in trades[-3:]:
            side_color = Fore.BLUE if trade['side'] == 'bullish' else Fore.MAGENTA
            pnl_color = Fore.GREEN if trade['pnl'] > 0 else Fore.RED
            
            print(f"      {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} → " +
                  f"{trade['exit_time'].strftime('%H:%M')} | " +
                  f"{side_color}{trade['side'].upper()[:4]}{Style.RESET_ALL} | " +
                  f"${trade['entry_price']:,.0f} → ${trade['exit_price']:,.0f} | " +
                  f"{pnl_color}{trade['pnl']:+.0f} ({trade['pnl_pct']:+.2f}%){Style.RESET_ALL} | " +
                  f"{trade['reason']}")
    
    def print_signals_section(self, signals: List[Dict]):
        """Print recent signals"""
        print(f"\n{Fore.YELLOW}📡 RECENT SIGNALS{Style.RESET_ALL}")
        
        if not signals:
            print("   No signals yet")
            return
        
        print(f"   Total Signals: {len(signals)}")
        
        # Last 5 signals
        print(f"\n   {Fore.CYAN}Latest Signals:{Style.RESET_ALL}")
        for sig in signals[-5:]:
            direction_color = Fore.BLUE if sig['type'] == 'bullish' else Fore.MAGENTA
            confidence_color = Fore.GREEN if sig['confidence'] > 75 else Fore.YELLOW if sig['confidence'] > 60 else Fore.RED
            
            print(f"      {sig['time'].strftime('%Y-%m-%d %H:%M')} | " +
                  f"{direction_color}{sig['type'].upper()[:4]}{Style.RESET_ALL} | " +
                  f"Price: ${sig['price']:,.0f} | " +
                  f"Entry: ${sig['entry']:,.0f} | " +
                  f"Confidence: {confidence_color}{sig['confidence']:.0f}%{Style.RESET_ALL} | " +
                  f"R:R {sig['rr']:.1f}:1")
    
    def print_active_positions_section(self, positions: List[Dict]):
        """Print active positions"""
        print(f"\n{Fore.YELLOW}📍 ACTIVE POSITIONS{Style.RESET_ALL}")
        
        if not positions:
            print("   No active positions")
            return
        
        print(f"   Total Positions: {len(positions)}")
        for pos in positions:
            side_color = Fore.BLUE if pos['side'] == 'long' else Fore.MAGENTA
            print(f"      {side_color}{pos['symbol']} {pos['side'].upper()}{Style.RESET_ALL} | " +
                  f"Entry: ${pos['entry']:,.0f} | " +
                  f"TP: ${pos['tp']:,.0f} | " +
                  f"SL: ${pos['sl']:,.0f}")
    
    def print_killzone_section(self, killzone_info: Dict):
        """Print killzone info"""
        print(f"\n{Fore.YELLOW}⏰ KILLZONE STATUS{Style.RESET_ALL}")
        
        zone = killzone_info.get('current_zone', 'Unknown')
        priority = killzone_info.get('priority', 'Unknown')
        should_trade = killzone_info.get('should_trade', False)
        
        priority_color = Fore.GREEN if priority == 'High' else Fore.YELLOW if priority == 'Medium' else Fore.RED
        trade_status = f"{Fore.GREEN}✓ TRADE{Style.RESET_ALL}" if should_trade else f"{Fore.RED}✗ WAIT{Style.RESET_ALL}"
        
        print(f"   Current Zone:     {zone}")
        print(f"   Priority:         {priority_color}{priority}{Style.RESET_ALL}")
        print(f"   Status:           {trade_status}")
    
    def print_footer(self):
        """Print footer"""
        print("\n" + "="*80)
        print(f"{Fore.CYAN}Updates every 5 seconds | Press Ctrl+C to stop{Style.RESET_ALL}")
        print("="*80 + "\n")
    
    def display(self, sim_data: Dict):
        """
        Display full dashboard
        """
        self.clear_screen()
        self.print_header()
        
        simulator = sim_data['simulator']
        
        # Calculate current stats
        if simulator.equity_curve:
            current_equity = simulator.equity_curve[-1]['equity']
            self.peak_equity = max(self.peak_equity, current_equity)
        else:
            current_equity = simulator.account_size
            self.peak_equity = simulator.account_size
        
        pnl = current_equity - simulator.account_size
        
        self.print_account_section(current_equity, self.peak_equity, pnl)
        self.print_trades_section(simulator.trades)
        self.print_signals_section(simulator.signals)
        self.print_active_positions_section(simulator.positions)
        
        # Placeholder for killzone (would need real data)
        killzone_info = {
            'current_zone': 'NY AM',
            'priority': 'High',
            'should_trade': True
        }
        self.print_killzone_section(killzone_info)
        
        self.print_footer()


def run_live_monitoring(simulator_data: Dict):
    """
    Run live monitoring dashboard
    Aktualizuje się co 5 sekund
    """
    dashboard = LiveDashboard()
    
    print(f"{Fore.CYAN}Starting live monitoring...{Style.RESET_ALL}")
    time.sleep(2)
    
    try:
        while True:
            dashboard.display(simulator_data)
            time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Monitoring stopped by user{Style.RESET_ALL}")


if __name__ == "__main__":
    print("Dashboard module loaded successfully")
