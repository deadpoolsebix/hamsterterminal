#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTML Live Dashboard - Plotly Interactive Charts
Bot gra na realnych danych - widać wszystko na wykresiach
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class HTMLLiveDashboard:
    """
    HTML Dashboard z Plotly - live updating charts
    """
    
    def __init__(self, title: str = "Real-Time Trading Bot Dashboard"):
        self.title = title
        self.trades = []
        self.candles = []
        self.equity_history = []
        
    def create_interactive_chart(self, data: pd.DataFrame, trades: list, equity_curve: list = None) -> str:
        """
        Stwórz interaktywny chart z Plotly
        Pokazuje: cena, entry/exit points, TP, SL linie
        """
        
        # Subplots: 2 wykresy (cena + equity)
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.12,
            row_heights=[0.7, 0.3],
            subplot_titles=("Cena BTC z Entry/Exit", "Account Equity")
        )
        
        # 1. CANDLESTICK CHART
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name='BTC Price',
                increasing_line_color='green',
                decreasing_line_color='red'
            ),
            row=1, col=1
        )
        
        # 2. ENTRY POINTS (zielone trójkąty)
        entry_times = []
        entry_prices = []
        
        for trade in trades:
            entry_times.append(trade['entry_time'])
            entry_prices.append(trade['entry_price'])
        
        fig.add_trace(
            go.Scatter(
                x=entry_times,
                y=entry_prices,
                mode='markers+text',
                marker=dict(size=12, color='green', symbol='triangle-up'),
                text=['BUY'] * len(entry_times),
                textposition="top center",
                name='Entry (BUY)',
                showlegend=True
            ),
            row=1, col=1
        )
        
        # 3. EXIT POINTS (czerwone X dla SL, zielone dla TP)
        for trade in trades:
            exit_time = trade['exit_time']
            exit_price = trade['exit_price']
            pnl = trade['pnl']
            
            # Kolor: zielony dla zysku, czerwony dla straty
            color = 'darkgreen' if pnl > 0 else 'darkred'
            symbol = 'x'
            
            fig.add_trace(
                go.Scatter(
                    x=[exit_time],
                    y=[exit_price],
                    mode='markers+text',
                    marker=dict(size=10, color=color, symbol=symbol),
                    text=[f"SELL ${pnl:+.0f}"],
                    textposition="bottom center",
                    name=f'Exit ({trade["exit_reason"]})',
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # 4. TP/SL LINES (dla każdej otwartej/zamkniętej pozycji)
        for trade in trades:
            entry_time = trade['entry_time']
            exit_time = trade['exit_time']
            
            # TP line (zielona)
            fig.add_hline(
                y=trade['entry_price'] * 1.08,
                line_dash="dash",
                line_color="green",
                annotation_text=f"TP +8%",
                annotation_position="right",
                row=1, col=1,
                opacity=0.5
            )
            
            # SL line (czerwona)
            fig.add_hline(
                y=trade['entry_price'] * 0.90,
                line_dash="dash",
                line_color="red",
                annotation_text=f"SL -10%",
                annotation_position="right",
                row=1, col=1,
                opacity=0.5
            )
        
        # 5. EQUITY CURVE
        if equity_curve:
            times = [e['time'] if isinstance(e, dict) else datetime.now() for e in equity_curve]
            equities = [e['equity'] if isinstance(e, dict) else e for e in equity_curve]
            
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=equities,
                    name='Account Equity',
                    line=dict(color='blue', width=2),
                    fill='tozeroy'
                ),
                row=2, col=1
            )
        
        # 6. LAYOUT
        fig.update_layout(
            title=self.title,
            template='plotly_dark',
            height=900,
            hovermode='x unified',
            xaxis_rangeslider_visible=False,
        )
        
        fig.update_yaxes(title_text="Cena (USD)", row=1, col=1)
        fig.update_yaxes(title_text="Equity (USD)", row=2, col=1)
        fig.update_xaxes(title_text="Czas", row=2, col=1)
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def save_html(self, html_content: str, filename: str = "bot_dashboard.html"):
        """
        Zapisz HTML do pliku
        """
        full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Bot Trading Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #ffffff;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            color: #00ff00;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-box {{
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #00ff00;
        }}
        .stat-box.negative {{
            border-left-color: #ff0000;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #00ff00;
        }}
        .stat-box.negative .stat-value {{
            color: #ff0000;
        }}
        .stat-label {{
            font-size: 12px;
            color: #999;
            margin-top: 8px;
        }}
        .chart-container {{
            background: #2a2a2a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .trades-table {{
            background: #2a2a2a;
            border-radius: 8px;
            padding: 20px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #1a1a1a;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #444;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #444;
        }}
        tr:hover {{
            background: #3a3a3a;
        }}
        .positive {{
            color: #00ff00;
        }}
        .negative {{
            color: #ff0000;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>BOT TRADING DASHBOARD</h1>
        <p>Real-Time Simulation - 24h Mode</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="chart-container">
        {html_content}
    </div>
    
    <script>
        // Auto-refresh co 5 sekund
        setTimeout(function() {{
            location.reload();
        }}, 5000);
    </script>
</body>
</html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print(f"[OK] HTML Dashboard zapisany: {filename}")
        return filename


def create_summary_stats(trades: list, starting_capital: float = 5000) -> dict:
    """
    Oblicz statystyki podsumowujące
    """
    if not trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'total_pnl_pct': 0,
            'largest_win': 0,
            'largest_loss': 0,
        }
    
    winning = [t for t in trades if t['pnl'] > 0]
    losing = [t for t in trades if t['pnl'] < 0]
    
    total_pnl = sum([t['pnl'] for t in trades])
    total_pnl_pct = (total_pnl / starting_capital) * 100
    
    return {
        'total_trades': len(trades),
        'winning_trades': len(winning),
        'losing_trades': len(losing),
        'win_rate': (len(winning) / len(trades) * 100) if trades else 0,
        'total_pnl': total_pnl,
        'total_pnl_pct': total_pnl_pct,
        'largest_win': max([t['pnl'] for t in winning], default=0),
        'largest_loss': min([t['pnl'] for t in losing], default=0),
    }


if __name__ == "__main__":
    print("[*] HTML Dashboard Module Loaded")
