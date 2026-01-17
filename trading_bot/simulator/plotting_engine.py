#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Advanced Plotting Engine
Wykresy z wejściami, wyjściami, wskaźnikami
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import numpy as np
from typing import Dict, List


class AdvancedPlotter:
    """
    Zaawansowany engine do wykresów
    - Price chart z wejściami/wyjściami
    - Indicators
    - Equity curve
    - Drawdown
    - Trade statistics
    """
    
    def __init__(self, simulator_data: Dict):
        self.simulator = simulator_data['simulator']
        self.data = simulator_data['data']
        self.trades = self.simulator.trades
        self.signals = self.simulator.signals
        self.equity_curve = self.simulator.equity_curve
    
    def plot_price_with_trades(self):
        """
        Plot: Cena z entry/exit points
        """
        fig, ax = plt.subplots(figsize=(16, 6))
        
        # Plot price
        ax.plot(self.data.index, self.data['close'], label='BTC Price', 
                linewidth=2, color='black', alpha=0.7)
        
        # Fill between high/low
        ax.fill_between(self.data.index, self.data['low'], self.data['high'], 
                       alpha=0.1, color='gray')
        
        # Plot entry points (green)
        for i, trade in enumerate(self.trades):
            entry_time = trade['entry_time']
            entry_price = trade['entry_price']
            
            color = 'green' if trade['side'] == 'bullish' else 'red'
            marker = '^' if trade['side'] == 'bullish' else 'v'
            
            ax.scatter(entry_time, entry_price, color=color, s=200, marker=marker, 
                      zorder=5, label='Entry' if i == 0 else '')
            
            # Draw line from entry to exit
            exit_time = trade['exit_time']
            exit_price = trade['exit_price']
            
            ax.plot([entry_time, exit_time], [entry_price, exit_price], 
                   color=color, linewidth=1, alpha=0.5, linestyle='--')
            
            # Plot exit point
            exit_color = 'darkgreen' if trade['pnl'] > 0 else 'darkred'
            ax.scatter(exit_time, exit_price, color=exit_color, s=150, marker='o', 
                      zorder=5, label='Exit' if i == 0 else '')
            
            # Add profit/loss annotation
            mid_time = entry_time + (exit_time - entry_time) / 2
            mid_price = (entry_price + exit_price) / 2
            pnl_text = f"+${trade['pnl']:.0f}" if trade['pnl'] > 0 else f"-${abs(trade['pnl']):.0f}"
            pnl_color = 'green' if trade['pnl'] > 0 else 'red'
            
            ax.text(mid_time, mid_price, pnl_text, fontsize=8, color=pnl_color,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        
        ax.set_xlabel('Date/Time')
        ax.set_ylabel('Price (USD)')
        ax.set_title('BTC Price with Entry/Exit Points', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_equity_curve(self):
        """
        Plot: Equity curve
        """
        if not self.equity_curve:
            print("No equity curve data")
            return None
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
        
        times = [e['time'] for e in self.equity_curve]
        equities = [e['equity'] for e in self.equity_curve]
        
        # Equity curve
        ax1.plot(times, equities, linewidth=2, color='blue', label='Equity')
        ax1.fill_between(times, 5000, equities, alpha=0.2, color='blue')
        
        # Add peak and current
        peak = max(equities)
        current = equities[-1]
        
        ax1.axhline(y=5000, color='gray', linestyle='--', alpha=0.5, label='Starting Capital')
        ax1.axhline(y=peak, color='green', linestyle='--', alpha=0.5, label=f'Peak: ${peak:,.0f}')
        
        ax1.set_ylabel('Equity (USD)')
        ax1.set_title('Account Equity Curve', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Drawdown
        drawdowns = []
        peak_val = 5000
        for eq in equities:
            peak_val = max(peak_val, eq)
            dd = ((eq - peak_val) / peak_val) * 100
            drawdowns.append(dd)
        
        ax2.fill_between(times, 0, drawdowns, alpha=0.3, color='red')
        ax2.plot(times, drawdowns, linewidth=2, color='red', label='Drawdown')
        ax2.set_xlabel('Date/Time')
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_title('Maximum Drawdown Over Time', fontsize=14, fontweight='bold')
        ax2.legend(loc='lower left')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_trade_statistics(self):
        """
        Plot: Trade statistics
        """
        if not self.trades:
            print("No trades")
            return None
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        
        # 1. P&L distribution
        pnls = [t['pnl'] for t in self.trades]
        colors = ['green' if p > 0 else 'red' for p in pnls]
        
        ax1.bar(range(len(pnls)), pnls, color=colors, alpha=0.7)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax1.set_xlabel('Trade Number')
        ax1.set_ylabel('P&L (USD)')
        ax1.set_title('Trade P&L Distribution', fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. Win rate pie chart
        winning = len([t for t in self.trades if t['pnl'] > 0])
        losing = len([t for t in self.trades if t['pnl'] < 0])
        
        ax2.pie([winning, losing], labels=[f'Winning ({winning})', f'Losing ({losing})'],
               colors=['green', 'red'], autopct='%1.1f%%', startangle=90)
        ax2.set_title('Win Rate', fontweight='bold')
        
        # 3. Trade duration
        durations = [(t['exit_time'] - t['entry_time']).total_seconds() / 3600 
                     for t in self.trades]  # in hours
        
        ax3.hist(durations, bins=15, color='blue', alpha=0.7)
        ax3.set_xlabel('Duration (hours)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Trade Duration Distribution', fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Cumulative P&L
        cumulative_pnl = np.cumsum(pnls)
        
        ax4.plot(range(len(cumulative_pnl)), cumulative_pnl, linewidth=2, color='purple')
        ax4.fill_between(range(len(cumulative_pnl)), 0, cumulative_pnl, alpha=0.2, color='purple')
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.set_xlabel('Trade Number')
        ax4.set_ylabel('Cumulative P&L (USD)')
        ax4.set_title('Cumulative P&L', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_signals_analysis(self):
        """
        Plot: Signal analysis
        """
        if not self.signals:
            print("No signals")
            return None
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 1. Signal confidence distribution
        confidences = [s['confidence'] for s in self.signals]
        
        ax1.hist(confidences, bins=20, color='skyblue', alpha=0.7, edgecolor='black')
        ax1.axvline(x=np.mean(confidences), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {np.mean(confidences):.1f}%')
        ax1.set_xlabel('Confidence (%)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Signal Confidence Distribution', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. Signals by direction
        bullish = len([s for s in self.signals if s['type'] == 'bullish'])
        bearish = len([s for s in self.signals if s['type'] == 'bearish'])
        
        ax2.bar(['Bullish', 'Bearish'], [bullish, bearish], color=['blue', 'red'], alpha=0.7)
        ax2.set_ylabel('Count')
        ax2.set_title('Signals by Direction', fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return fig
    
    def plot_combined_analysis(self):
        """
        Plot: Combined price + indicators + equity
        """
        if not self.data.empty:
            fig = plt.figure(figsize=(18, 12))
            gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1])
            
            # Price chart
            ax1 = fig.add_subplot(gs[0])
            ax1.plot(self.data.index, self.data['close'], linewidth=2, color='black', label='Price')
            ax1.fill_between(self.data.index, self.data['low'], self.data['high'], 
                           alpha=0.1, color='gray')
            
            # Add trades
            for trade in self.trades:
                color = 'green' if trade['side'] == 'bullish' else 'red'
                marker = '^' if trade['side'] == 'bullish' else 'v'
                
                ax1.scatter(trade['entry_time'], trade['entry_price'], color=color, 
                          s=200, marker=marker, zorder=5)
                ax1.scatter(trade['exit_time'], trade['exit_price'], color='gray', 
                          s=150, marker='o', zorder=5)
            
            ax1.set_ylabel('Price (USD)')
            ax1.set_title('7-Day Simulation: Price Chart with Trade Entry/Exit Points', 
                         fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # Equity curve
            if self.equity_curve:
                ax2 = fig.add_subplot(gs[1])
                times = [e['time'] for e in self.equity_curve]
                equities = [e['equity'] for e in self.equity_curve]
                
                ax2.plot(times, equities, linewidth=2, color='blue')
                ax2.fill_between(times, 5000, equities, alpha=0.2, color='blue')
                ax2.axhline(y=5000, color='gray', linestyle='--', alpha=0.5)
                
                ax2.set_ylabel('Equity (USD)')
                ax2.set_title('Equity Curve', fontweight='bold')
                ax2.grid(True, alpha=0.3)
            
            # Volume
            ax3 = fig.add_subplot(gs[2])
            colors = ['green' if self.data['close'].iloc[i] > self.data['open'].iloc[i] 
                     else 'red' for i in range(len(self.data))]
            ax3.bar(self.data.index, self.data['volume'], color=colors, alpha=0.5)
            ax3.set_xlabel('Date/Time')
            ax3.set_ylabel('Volume')
            ax3.set_title('Trading Volume', fontweight='bold')
            ax3.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            return fig
        
        return None
    
    def save_all_plots(self, filename_prefix: str = 'simulation'):
        """
        Zapisz wszystkie wykresy do plików
        """
        print("\n📊 Generating plots...")
        
        figs = []
        
        # Plot 1: Price with trades
        print("   Generating price chart...")
        fig1 = self.plot_price_with_trades()
        if fig1:
            fig1.savefig(f'{filename_prefix}_01_price_trades.png', dpi=300, bbox_inches='tight')
            figs.append(f'{filename_prefix}_01_price_trades.png')
        
        # Plot 2: Equity curve
        print("   Generating equity curve...")
        fig2 = self.plot_equity_curve()
        if fig2:
            fig2.savefig(f'{filename_prefix}_02_equity_drawdown.png', dpi=300, bbox_inches='tight')
            figs.append(f'{filename_prefix}_02_equity_drawdown.png')
        
        # Plot 3: Trade statistics
        print("   Generating trade statistics...")
        fig3 = self.plot_trade_statistics()
        if fig3:
            fig3.savefig(f'{filename_prefix}_03_trade_stats.png', dpi=300, bbox_inches='tight')
            figs.append(f'{filename_prefix}_03_trade_stats.png')
        
        # Plot 4: Signal analysis
        print("   Generating signal analysis...")
        fig4 = self.plot_signals_analysis()
        if fig4:
            fig4.savefig(f'{filename_prefix}_04_signal_analysis.png', dpi=300, bbox_inches='tight')
            figs.append(f'{filename_prefix}_04_signal_analysis.png')
        
        # Plot 5: Combined
        print("   Generating combined analysis...")
        fig5 = self.plot_combined_analysis()
        if fig5:
            fig5.savefig(f'{filename_prefix}_05_combined.png', dpi=300, bbox_inches='tight')
            figs.append(f'{filename_prefix}_05_combined.png')
        
        print(f"\n✅ Plots saved: {', '.join(figs)}")
        
        # Show plots
        plt.show()


if __name__ == "__main__":
    print("Plotting module loaded successfully")
