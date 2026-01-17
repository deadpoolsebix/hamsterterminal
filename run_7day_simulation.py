#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
7-Day Bot Simulation with Live Dashboard and Charts
Główny skrypt do uruchomienia pełnej symulacji
"""

import sys
import os
import threading
import time
from datetime import datetime
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from trading_bot.simulator.bot_simulator_7days import BotSimulator7Days
from trading_bot.simulator.live_dashboard import LiveDashboard
from trading_bot.simulator.plotting_engine import AdvancedPlotter
from colorama import Fore, Style, init

init(autoreset=True)


class SimulationRunner:
    """
    Główny runner do pełnej symulacji z dashboardem i chartami
    """
    
    def __init__(self):
        self.simulator = None
        self.data = None
        self.dashboard = None
        self.running = True
        self.simulation_complete = False
    
    def run_simulation(self):
        """
        Uruchom pełną 7-dniową symulację
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚡ STARTING 7-DAY BOT SIMULATION{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # Initialize simulator
        print(f"{Fore.CYAN}📊 Initializing simulator...{Style.RESET_ALL}")
        self.simulator = BotSimulator7Days(
            account_size=5000,
            risk_per_trade=250
        )
        
        # Generate 7-day realistic data
        print(f"{Fore.CYAN}📈 Generating 7 days of realistic price data...{Style.RESET_ALL}")
        self.data = self.simulator.generate_realistic_data(days=7)
        print(f"{Fore.GREEN}✓ Generated {len(self.data)} candles{Style.RESET_ALL}")
        print(f"   Date range: {self.data.index[0]} to {self.data.index[-1]}\n")
        
        # Run simulation
        print(f"{Fore.CYAN}🤖 Running trading simulation...{Style.RESET_ALL}")
        results = self.simulator.simulate_trading_cycle(self.data)
        
        self.simulation_complete = True
        
        return results
    
    def display_live_dashboard_thread(self):
        """
        Thread do wyświetlania live dashboardu
        """
        try:
            self.dashboard = LiveDashboard()
            self.dashboard.run_live_monitoring({
                'simulator': self.simulator,
                'data': self.data
            })
        except KeyboardInterrupt:
            self.running = False
    
    def print_summary(self, results):
        """
        Wydrukuj podsumowanie wyników
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 SIMULATION RESULTS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # Account Summary
        print(f"{Fore.CYAN}{'Account Summary:':<50}{Style.RESET_ALL}")
        print(f"  Starting Capital:        ${results['starting_capital']:>15,.2f}")
        print(f"  Final Equity:            ${results['final_equity']:>15,.2f}")
        print(f"  Total P&L:               ${results['total_pnl']:>15,.2f}")
        print(f"  Return %:                {results['total_pnl_pct']:>15.2f}%")
        print(f"  Max Drawdown:            {results['max_drawdown']:>15.2f}%")
        print()
        
        # Trading Activity
        print(f"{Fore.CYAN}{'Trading Activity:':<50}{Style.RESET_ALL}")
        print(f"  Total Trades:            {results['total_trades']:>20}")
        print(f"  Winning Trades:          {results['winning_trades']:>20}")
        print(f"  Losing Trades:           {results['losing_trades']:>20}")
        print(f"  Win Rate:                {results['win_rate']:>20.2f}%")
        print(f"  Average Trade P&L:       ${results['avg_trade_pnl']:>15,.2f}")
        print()
        
        # Trade Performance
        print(f"{Fore.CYAN}{'Trade Performance:':<50}{Style.RESET_ALL}")
        print(f"  Largest Win:             ${results['largest_win']:>15,.2f}")
        print(f"  Largest Loss:            ${results['largest_loss']:>15,.2f}")
        print(f"  Profit Factor:           {results['profit_factor']:>20.2f}")
        print()
        
        # Risk Metrics
        print(f"{Fore.CYAN}{'Risk Metrics:':<50}{Style.RESET_ALL}")
        print(f"  Sharpe Ratio:            {results['sharpe_ratio']:>20.2f}")
        print(f"  Sortino Ratio:           {results['sortino_ratio']:>20.2f}")
        print(f"  Risk/Reward Ratio:       {results['avg_win'] / abs(results['avg_loss']) if results['avg_loss'] != 0 else 0:>20.2f}")
        print()
        
        # Equity Summary
        print(f"{Fore.CYAN}{'Equity Summary:':<50}{Style.RESET_ALL}")
        print(f"  Peak Equity:             ${results['peak_equity']:>15,.2f}")
        print(f"  Lowest Equity:           ${results['lowest_equity']:>15,.2f}")
        print(f"  Days in Profit:          {results['days_in_profit']:>20}")
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    def print_trade_details(self):
        """
        Wydrukuj szczegóły każdej transakcji
        """
        if not self.simulator.trades:
            print(f"{Fore.YELLOW}No trades executed{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📋 DETAILED TRADE LOG{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        for i, trade in enumerate(self.simulator.trades, 1):
            side_color = Fore.GREEN if trade['side'] == 'bullish' else Fore.RED
            pnl_color = Fore.GREEN if trade['pnl'] > 0 else Fore.RED
            
            print(f"{Fore.CYAN}Trade #{i}{Style.RESET_ALL}")
            print(f"  Entry Time:     {trade['entry_time']}")
            print(f"  Side:           {side_color}{trade['side'].upper()}{Style.RESET_ALL}")
            print(f"  Entry Price:    ${trade['entry_price']:.2f}")
            print(f"  Take Profit:    ${trade['take_profit']:.2f}")
            print(f"  Stop Loss:      ${trade['stop_loss']:.2f}")
            print(f"  Exit Time:      {trade['exit_time']}")
            print(f"  Exit Price:     ${trade['exit_price']:.2f}")
            print(f"  Exit Reason:    {trade['exit_reason']}")
            print(f"  P&L:            {pnl_color}${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%){Style.RESET_ALL}")
            print()
    
    def run_full_simulation(self):
        """
        Uruchom pełną symulację z dashboardem i chartami
        """
        try:
            # Step 1: Run simulation
            results = self.run_simulation()
            
            # Step 2: Print results
            self.print_summary(results)
            
            # Step 3: Print trade details
            self.print_trade_details()
            
            # Step 4: Generate plots
            self.generate_plots()
            
            # Step 5: Optional - Live dashboard
            self.show_dashboard_option()
            
            print(f"{Fore.GREEN}\n✅ Simulation completed successfully!{Style.RESET_ALL}\n")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}⚠️  Simulation interrupted by user{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"{Fore.RED}❌ Error during simulation: {str(e)}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
    
    def generate_plots(self):
        """
        Wygeneruj wszystkie wykresy
        """
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 GENERATING VISUALIZATION{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        plotter = AdvancedPlotter({
            'simulator': self.simulator,
            'data': self.data
        })
        
        plotter.save_all_plots(filename_prefix='simulation_7day')
    
    def show_dashboard_option(self):
        """
        Pokaż opcję dashboardu
        """
        print(f"\n{Fore.YELLOW}💡 Live Dashboard available!{Style.RESET_ALL}")
        print(f"   Press Enter to view live dashboard (Ctrl+C to exit)")
        
        try:
            input()
            
            print(f"\n{Fore.CYAN}Starting live dashboard...{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}(Real-time updates every 5 seconds){Style.RESET_ALL}\n")
            
            self.dashboard = LiveDashboard()
            self.dashboard.run_live_monitoring({
                'simulator': self.simulator,
                'data': self.data
            })
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Dashboard stopped{Style.RESET_ALL}")


def main():
    """
    Main entry point
    """
    runner = SimulationRunner()
    runner.run_full_simulation()


if __name__ == "__main__":
    main()
