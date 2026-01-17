#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTML Dashboard z dwoma wykresami:
1. Główny: Cena + Wszystkie wskaźniki (RSI, MACD, Bollinger, etc.)
2. Equity: Performance + Sygnały
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
from datetime import datetime
import json


class AdvancedHTMLDashboard:
    """
    Professional HTML Dashboard z Plotly
    Dwa wykresy: 1) Technical Analysis 2) Equity/Performance
    """
    
    def __init__(self):
        self.trades = []
        
    def create_dual_charts(self, 
                           data: pd.DataFrame,
                           indicators: Dict,
                           trades: List[Dict],
                           starting_capital: float = 5000) -> str:
        """
        Stwórz DWA wykresy w HTML:
        1. Główny wykres z ceną i wskaźnikami
        2. Equity curve z sygnałami
        """
        
        if len(data) == 0:
            return "<h1>No data available</h1>"
        
        # === PRZYGOTOWANIE DANYCH ===
        dates = data.index
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        open_ = data['open'].values
        
        rsi = indicators['rsi']
        momentum = indicators['momentum']
        macd_line = indicators['macd_line']
        signal_line = indicators['signal_line']
        bb_upper = indicators['bb_upper']
        bb_middle = indicators['bb_middle']
        bb_lower = indicators['bb_lower']
        atr = indicators['atr']
        sentiment = indicators['sentiment']
        
        # === TWORZENIE FIGURE Z SUBPLOTS ===
        # 4 rows: 1) Candles+BB 2) RSI 3) MACD 4) Sentiment
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.4, 0.2, 0.2, 0.2],
            subplot_titles=(
                "BTC Price + Bollinger Bands + Sygnały",
                "RSI (14)",
                "MACD",
                "Sentiment"
            )
        )
        
        # === ROW 1: CANDLESTICK + BOLLINGER BANDS + SYGNAŁY ===
        
        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=dates,
                open=open_,
                high=high,
                low=low,
                close=close,
                name='BTC',
                increasing_line_color='green',
                decreasing_line_color='red'
            ),
            row=1, col=1
        )
        
        # Bollinger Bands
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=bb_upper,
                name='BB Upper',
                line=dict(color='rgba(100,100,255,0.3)', width=1),
                showlegend=True
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=bb_middle,
                name='BB Middle',
                line=dict(color='rgba(100,100,255,0.5)', width=1),
                showlegend=True
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=bb_lower,
                name='BB Lower',
                line=dict(color='rgba(100,100,255,0.3)', width=1),
                showlegend=True,
                fill='tonexty',
                fillcolor='rgba(100,100,255,0.1)'
            ),
            row=1, col=1
        )
        
        # === SYGNAŁY NA GŁÓWNYM WYKRESIE ===
        
        # BUY sygnały (zielone strzałki w górę)
        buy_trades = [t for t in trades if t['signal'] == 'BUY']
        if buy_trades:
            buy_dates = [t['time'] for t in buy_trades]
            buy_prices = [t['price'] for t in buy_trades]
            
            fig.add_trace(
                go.Scatter(
                    x=buy_dates,
                    y=buy_prices,
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=15, color='green'),
                    name='BUY',
                    text=['BUY'] * len(buy_dates),
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # SELL sygnały (czerwone strzałki w dół)
        sell_trades = [t for t in trades if t['signal'] == 'SELL']
        if sell_trades:
            sell_dates = [t['time'] for t in sell_trades]
            sell_prices = [t['price'] for t in sell_trades]
            
            fig.add_trace(
                go.Scatter(
                    x=sell_dates,
                    y=sell_prices,
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=15, color='red'),
                    name='SELL',
                    text=['SELL'] * len(sell_dates),
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # BULL TRAP (magenta X)
        bull_traps = [t for t in trades if t['signal'] == 'BULL_TRAP']
        if bull_traps:
            trap_dates = [t['time'] for t in bull_traps]
            trap_prices = [t['price'] for t in bull_traps]
            
            fig.add_trace(
                go.Scatter(
                    x=trap_dates,
                    y=trap_prices,
                    mode='markers',
                    marker=dict(symbol='x', size=12, color='magenta'),
                    name='BULL TRAP',
                    text=['BULL TRAP'] * len(trap_dates),
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # BEAR TRAP (magenta X)
        bear_traps = [t for t in trades if t['signal'] == 'BEAR_TRAP']
        if bear_traps:
            trap_dates = [t['time'] for t in bear_traps]
            trap_prices = [t['price'] for t in bear_traps]
            
            fig.add_trace(
                go.Scatter(
                    x=trap_dates,
                    y=trap_prices,
                    mode='markers',
                    marker=dict(symbol='x', size=12, color='cyan'),
                    name='BEAR TRAP',
                    text=['BEAR TRAP'] * len(trap_dates),
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # === ROW 2: RSI ===
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=rsi,
                name='RSI(14)',
                line=dict(color='orange', width=2),
                showlegend=True
            ),
            row=2, col=1
        )
        
        # Linie referencyjne RSI
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1, annotation_text="Overbought")
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1, annotation_text="Oversold")
        fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
        
        # === ROW 3: MACD ===
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=macd_line,
                name='MACD',
                line=dict(color='blue', width=2),
                showlegend=True
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=signal_line,
                name='Signal',
                line=dict(color='red', width=2),
                showlegend=True
            ),
            row=3, col=1
        )
        
        # MACD Histogram jako kolory
        colors = ['green' if h > 0 else 'red' for h in indicators['macd_histogram']]
        fig.add_trace(
            go.Bar(
                x=dates,
                y=indicators['macd_histogram'],
                name='Histogram',
                marker_color=colors,
                showlegend=True,
                opacity=0.3
            ),
            row=3, col=1
        )
        
        # === ROW 4: SENTIMENT ===
        colors = ['green' if s > 0 else 'red' for s in sentiment]
        fig.add_trace(
            go.Bar(
                x=dates,
                y=sentiment,
                name='Sentiment',
                marker_color=colors,
                showlegend=True,
                opacity=0.5
            ),
            row=4, col=1
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="black", row=4, col=1)
        
        # === LAYOUT ===
        fig.update_layout(
            title_text="<b>ADVANCED LIVE TRADING BOT - Technical Analysis Dashboard</b>",
            template="plotly_dark",
            height=1400,
            hovermode='x unified',
            font=dict(family="Courier New", size=11),
            showlegend=True,
            xaxis_rangeslider_visible=False,
        )
        
        fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1)
        fig.update_yaxes(title_text="MACD", row=3, col=1)
        fig.update_yaxes(title_text="Sentiment", row=4, col=1)
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def create_equity_chart(self, trades: List[Dict], starting_capital: float = 5000) -> str:
        """
        Twórz drugi wykres: Equity curve z P&L
        """
        
        if not trades:
            return "<h1>No trades yet</h1>"
        
        # Oblicz equity curve
        equity = [starting_capital]
        dates = []
        prices = []
        signals_list = []
        
        current_equity = starting_capital
        
        for trade in trades:
            # Symuluj P&L
            if trade['signal'] == 'BUY':
                pnl = trade.get('pnl', 0)
            elif trade['signal'] == 'SELL':
                pnl = trade.get('pnl', 0)
            else:
                pnl = 0
            
            current_equity += pnl
            equity.append(current_equity)
            dates.append(trade['time'])
            prices.append(trade['price'])
            signals_list.append(trade['signal'])
        
        # Createing figure
        fig = go.Figure()
        
        # Equity curve
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=equity,
                mode='lines+markers',
                name='Equity',
                line=dict(color='blue', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(0,0,255,0.1)'
            )
        )
        
        # Sygnały na equity
        for signal_type in ['BUY', 'SELL', 'BULL_TRAP', 'BEAR_TRAP']:
            signal_indices = [i for i, s in enumerate(signals_list) if s == signal_type]
            
            if signal_indices:
                signal_dates = [dates[i] for i in signal_indices]
                signal_equity = [equity[i+1] for i in signal_indices]
                
                color_map = {
                    'BUY': 'green',
                    'SELL': 'red',
                    'BULL_TRAP': 'magenta',
                    'BEAR_TRAP': 'cyan'
                }
                
                fig.add_trace(
                    go.Scatter(
                        x=signal_dates,
                        y=signal_equity,
                        mode='markers',
                        marker=dict(size=12, color=color_map[signal_type]),
                        name=signal_type,
                        text=[signal_type] * len(signal_dates)
                    )
                )
        
        # Reference line - starting capital
        fig.add_hline(y=starting_capital, line_dash="dash", line_color="gray", 
                     annotation_text="Start Capital")
        
        fig.update_layout(
            title_text="<b>Equity Curve - Trade Performance</b>",
            xaxis_title="Time",
            yaxis_title="Equity (USD)",
            template="plotly_dark",
            height=600,
            hovermode='x unified',
            font=dict(family="Courier New", size=11),
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def create_full_dashboard(self, 
                             data: pd.DataFrame,
                             indicators: Dict,
                             trades: List[Dict],
                             starting_capital: float = 5000) -> str:
        """
        Twórz PEŁNY HTML z oboma wykresami
        """
        
        chart1_html = self.create_dual_charts(data, indicators, trades, starting_capital)
        chart2_html = self.create_equity_chart(trades, starting_capital)
        
        # Oblicz statystyki
        stats = self._calculate_stats(trades, starting_capital)
        
        # HTML wrapper
        full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Advanced Live Trading Bot Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background-color: #1a1a1a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 2px solid #00d4ff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            margin: 0;
            color: #00d4ff;
            font-size: 2.5em;
        }}
        
        .header p {{
            margin: 5px 0;
            color: #aaa;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .stat-box {{
            background-color: #2a2a2a;
            border: 1px solid #00d4ff;
            border-radius: 5px;
            padding: 15px;
            text-align: center;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #aaa;
            text-transform: uppercase;
        }}
        
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #00d4ff;
            margin-top: 5px;
        }}
        
        .stat-value.positive {{
            color: #00ff00;
        }}
        
        .stat-value.negative {{
            color: #ff0000;
        }}
        
        .chart-container {{
            background-color: #2a2a2a;
            border: 1px solid #00d4ff;
            border-radius: 5px;
            margin-bottom: 30px;
            padding: 15px;
        }}
        
        .chart-title {{
            color: #00d4ff;
            font-size: 1.3em;
            margin-bottom: 15px;
            font-weight: bold;
        }}
        
        .signals-list {{
            background-color: #2a2a2a;
            border: 1px solid #00d4ff;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 30px;
        }}
        
        .signals-title {{
            color: #00d4ff;
            font-size: 1.3em;
            margin-bottom: 15px;
            font-weight: bold;
        }}
        
        .signal-item {{
            padding: 8px;
            margin-bottom: 5px;
            border-left: 3px solid;
            background-color: #1a1a1a;
        }}
        
        .signal-item.buy {{
            border-left-color: #00ff00;
            color: #00ff00;
        }}
        
        .signal-item.sell {{
            border-left-color: #ff0000;
            color: #ff0000;
        }}
        
        .signal-item.closed_tp {{
            border-left-color: #00ff00;
            color: #00ff00;
        }}
        
        .signal-item.closed_sl {{
            border-left-color: #ff0000;
            color: #ff0000;
        }}
        
        .signal-item.bull_trap {{
            border-left-color: #ff00ff;
            color: #ff00ff;
        }}
        
        .signal-item.bear_trap {{
            border-left-color: #00ffff;
            color: #00ffff;
        }}
        
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #444;
        }}
        
        .auto-refresh {{
            text-align: center;
            color: #00d4ff;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ ADVANCED LIVE TRADING BOT</h1>
        <p>Real-time Analysis with Technical Indicators + Position Liquidation</p>
        <p>RSI • MACD • Bollinger Bands • Sentiment • FVG • Bull/Bear Traps</p>
        <p style="font-size: 0.9em; color: #666;">Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="auto-refresh">
        🔄 Dashboard auto-refreshes every 30 seconds
    </div>
    
    <div class="stats-grid">
        <div class="stat-box">
            <div class="stat-label">Total Signals</div>
            <div class="stat-value">{stats['total_signals']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">BUY Signals</div>
            <div class="stat-value positive">{stats['buy_signals']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">SELL Signals</div>
            <div class="stat-value negative">{stats['sell_signals']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Closed Positions</div>
            <div class="stat-value">{stats['closed_positions']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Winning Trades</div>
            <div class="stat-value positive">{stats['winning_positions']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Losing Trades</div>
            <div class="stat-value negative">{stats['losing_positions']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Win Rate</div>
            <div class="stat-value">{stats['win_rate']:.1f}%</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Total P&L</div>
            <div class="stat-value {'positive' if stats['total_pnl'] >= 0 else 'negative'}">${stats['total_pnl']:,.0f}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Starting Capital</div>
            <div class="stat-value">${stats['starting_capital']:,.0f}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Bull Traps</div>
            <div class="stat-value">{stats['bull_traps']}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Bear Traps</div>
            <div class="stat-value">{stats['bear_traps']}</div>
        </div>
    </div>
    
    <div class="chart-container">
        <div class="chart-title">📈 Technical Analysis Dashboard</div>
        {chart1_html}
    </div>
    
    <div class="chart-container">
        <div class="chart-title">💰 Equity Performance</div>
        {chart2_html}
    </div>
    
    <div class="signals-list">
        <div class="signals-title">📊 Recent Signals & Closed Positions (Last 30)</div>
        {self._generate_signals_html(trades)}
    </div>
    
    <div class="footer">
        <p>Advanced Live Trading Bot with Liquidation System • Powered by Plotly</p>
        <p>© 2026 Trading Analysis Platform</p>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>
"""
        
        return full_html
    
    def _calculate_stats(self, trades: List[Dict], starting_capital: float) -> Dict:
        """Oblicz statystyki"""
        
        # Zamknięte trades (z P&L)
        closed_trades = [t for t in trades if 'pnl' in t and t.get('signal') in ['CLOSED_TP', 'CLOSED_SL']]
        
        if closed_trades:
            total_pnl = sum(t['pnl'] for t in closed_trades)
            wins = len([t for t in closed_trades if t['pnl'] > 0])
            losses = len([t for t in closed_trades if t['pnl'] < 0])
        else:
            total_pnl = 0
            wins = 0
            losses = 0
        
        return {
            'total_signals': len(trades),
            'buy_signals': sum(1 for t in trades if t['signal'] == 'BUY'),
            'sell_signals': sum(1 for t in trades if t['signal'] == 'SELL'),
            'bull_traps': sum(1 for t in trades if t['signal'] == 'BULL_TRAP'),
            'bear_traps': sum(1 for t in trades if t['signal'] == 'BEAR_TRAP'),
            'closed_positions': len(closed_trades),
            'winning_positions': wins,
            'losing_positions': losses,
            'total_pnl': total_pnl,
            'win_rate': (wins / len(closed_trades) * 100) if closed_trades else 0,
            'starting_capital': starting_capital,
        }
    
    def _generate_signals_html(self, trades: List[Dict]) -> str:
        """Generuj HTML z sygnałami i zamkniętymi pozycjami"""
        if not trades:
            return "<p style='color: #666;'>No signals yet...</p>"
        
        html = ""
        
        # Podziel na otwarte sygnały i zamknięte pozycje
        for trade in trades[-30:][::-1]:  # Ostatnie 30, na odwrót
            signal = trade['signal']
            time_str = trade['time'].strftime("%H:%M:%S")
            price = trade.get('price', 0)
            rsi = trade.get('rsi', 'N/A')
            
            # Dodaj P&L dla zamkniętych pozycji
            pnl_str = ""
            if 'pnl' in trade:
                pnl = trade['pnl']
                pnl_pct = trade.get('pnl_pct', 0)
                pnl_color = "green" if pnl > 0 else "red"
                pnl_str = f" | P&L: <span style='color: {pnl_color};'>${pnl:+.0f} ({pnl_pct:+.2f}%)</span>"
            
            # Typ sygna do CSS
            signal_class = signal.lower().replace(' ', '_')
            
            # Dodaj wartość entry price dla zamkniętych pozycji
            entry_price_str = ""
            if 'entry_price' in trade:
                entry_price_str = f" (Entry: ${trade['entry_price']:.0f})"
            
            html += f"""
            <div class="signal-item {signal_class}">
                <strong>{signal}</strong> @ ${price:.0f}{entry_price_str} (RSI: {rsi:.2f if isinstance(rsi, float) else rsi}) - {time_str}{pnl_str}
            </div>
            """
        
        return html
    
    def save_dashboard(self, html_content: str, filename: str = "bot_dashboard.html"):
        """Zapisz HTML do pliku"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filename

