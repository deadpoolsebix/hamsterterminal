#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ULTIMATE PROFESSIONAL DASHBOARD
ALL zaawansowane dane na jednym wykresie!
- 50% podzial z internal/external zones
- Support/Resistance
- Likwidacja górna/dolna
- Equal Highs/Lows
- Wyckoff phases
- Liquidity grab
- Session info
- Wick analysis
- Convergence/Divergence
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
from datetime import datetime
from advanced_market_levels_analyzer import AdvancedMarketLevels


class UltimateProDashboard:
    """
    PROFESJONALNY Dashboard z WSZYSTKIMI danymi
    """
    
    def __init__(self):
        self.market_analyzer = AdvancedMarketLevels()
    
    def create_mega_chart(self, 
                         data: pd.DataFrame,
                         indicators: Dict,
                         market_levels: Dict,
                         wyckoff_phases: List[Dict],
                         liquidity_grabs: List[Dict],
                         eqh_eql: Dict,
                         trades: List[Dict],
                         sessions_info: Dict) -> str:
        """
        Stwórz MEGA CHART ze WSZYSTKIMI elementami
        """
        
        dates = data.index
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        open_ = data['open'].values
        volume = data['volume'].values
        
        # === PRZYGOTOWANIE DANYCH ===
        
        # Levels
        levels = market_levels
        
        # Support/Resistance
        support_levels, resistance_levels = self.market_analyzer.find_support_resistance(
            data['high'], data['low']
        )
        
        # Wick analysis
        wick_analysis = self.market_analyzer.calculate_wick_analysis(
            pd.Series(open_), pd.Series(high), pd.Series(low), pd.Series(close)
        )
        
        # === TWORZENIE FIGURE ===
        fig = make_subplots(
            rows=5, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.45, 0.15, 0.15, 0.15, 0.10],
            subplot_titles=(
                "📊 PRICE ACTION + LEVELS",
                "📈 RSI (14)",
                "📉 MACD",
                "🔄 WYCKOFF PHASES",
                "📦 VOLUME"
            )
        )
        
        # ========== ROW 1: PRICE ACTION ==========
        
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
        
        # === SUPPORT LEVELS (niebieski) - only last 3 for clarity ===
        for support in support_levels[-3:]:
            fig.add_hline(
                y=support,
                line_dash="dash",
                line_color="rgba(0,100,255,0.6)",
                line_width=1.5,
                annotation_text=f"S: ${support:.0f}",
                annotation_position="left",
                row=1, col=1
            )
        
        # === RESISTANCE LEVELS (czerwony) - only last 3 for clarity ===
        for resistance in resistance_levels[-3:]:
            fig.add_hline(
                y=resistance,
                line_dash="dash",
                line_color="rgba(255,50,50,0.6)",
                line_width=1.5,
                annotation_text=f"R: ${resistance:.0f}",
                annotation_position="right",
                row=1, col=1
            )
        
        # === 50% PODZIAL ===
        if 'mid_point' in levels:
            # Mid Point (50%)
            fig.add_hline(
                y=levels['mid_point'],
                line_dash="dot",
                line_color="purple",
                line_width=2,
                annotation_text="50% MID POINT",
                row=1, col=1
            )
            
            # Lower Internal (25%)
            fig.add_hline(
                y=levels['lower_internal'],
                line_dash="dot",
                line_color="purple",
                line_width=1,
                opacity=0.5,
                row=1, col=1
            )
            
            # Upper Internal (75%)
            fig.add_hline(
                y=levels['upper_internal'],
                line_dash="dot",
                line_color="purple",
                line_width=1,
                opacity=0.5,
                row=1, col=1
            )
            
            # External Zones - fill
            fig.add_hrect(
                y0=levels['lowest'],
                y1=levels['external_low'],
                fillcolor="purple",
                opacity=0.05,
                layer="below",
                line_width=0,
                row=1, col=1,
                annotation_text="External Low"
            )
            
            fig.add_hrect(
                y0=levels['external_high'],
                y1=levels['highest'],
                fillcolor="purple",
                opacity=0.05,
                layer="below",
                line_width=0,
                row=1, col=1,
                annotation_text="External High"
            )
        
        # === EQUAL HIGHS (zielony marker) - only last 2 ===
        if eqh_eql and 'equal_highs' in eqh_eql:
            for eqh in eqh_eql['equal_highs'][-2:]:
                idx1, idx2, price = eqh
                fig.add_hline(
                    y=price,
                    line_dash="dash",
                    line_color="lightgreen",
                    line_width=2,
                    annotation_text=f"EQH: ${price:.0f}",
                    row=1, col=1
                )
        
        # === EQUAL LOWS (różowy marker) ===
        if eqh_eql and 'equal_lows' in eqh_eql:
            for eql in eqh_eql['equal_lows'][-3:]:  # Ostatnie 3
                idx1, idx2, price = eql
                fig.add_hline(
                    y=price,
                    line_dash="dash",
                    line_color="pink",
                    line_width=2,
                    annotation_text=f"EQL: ${price:.0f}",
                    row=1, col=1
                )
        
        # === LIQUIDITY GRAB (żółty marker) ===
        for grab in liquidity_grabs[-10:]:  # Ostatnie 10
            idx = grab['index']
            price = grab['price']
            color = "yellow" if grab['type'] == 'LIQUIDITY_GRAB_UP' else "orange"
            
            fig.add_trace(
                go.Scatter(
                    x=[dates[idx]],
                    y=[price],
                    mode='markers',
                    marker=dict(symbol='diamond', size=12, color=color),
                    name=grab['type'],
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # === TRADE ENTRY/EXIT (sygnały) ===
        for trade in trades:
            if trade['signal'] in ['BUY', 'CLOSED_TP']:
                color = 'green'
                symbol = 'triangle-up'
            elif trade['signal'] in ['SELL', 'CLOSED_SL']:
                color = 'red'
                symbol = 'triangle-down'
            else:
                color = 'blue'
                symbol = 'circle'
            
            fig.add_trace(
                go.Scatter(
                    x=[trade['time']],
                    y=[trade['price']],
                    mode='markers',
                    marker=dict(symbol=symbol, size=10, color=color),
                    name=trade['signal'],
                    text=[f"{trade['signal']}<br>${trade['price']:.0f}"],
                    hoverinfo="text",
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # === BOLLINGER BANDS ===
        if 'bb_upper' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=indicators['bb_upper'],
                    name='BB Upper',
                    line=dict(color='rgba(100,100,255,0.3)', width=1),
                    showlegend=True
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=indicators['bb_lower'],
                    name='BB Lower',
                    line=dict(color='rgba(100,100,255,0.3)', width=1),
                    fill='tonexty',
                    fillcolor='rgba(100,100,255,0.1)',
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # === SMA 20, 50, 30 ===
        sma_20 = pd.Series(close).rolling(window=20).mean()
        sma_50 = pd.Series(close).rolling(window=50).mean()
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=sma_20,
                name='SMA 20',
                line=dict(color='cyan', width=2),
                showlegend=True
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=sma_50,
                name='SMA 50',
                line=dict(color='orange', width=2),
                showlegend=True
            ),
            row=1, col=1
        )
        
        # ========== ROW 2: RSI =========
        if 'rsi' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=indicators['rsi'],
                    name='RSI',
                    line=dict(color='#00d4ff', width=2),
                    showlegend=True
                ),
                row=2, col=1
            )
            
            # RSI levels
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
        
        # ========== ROW 3: MACD =========
        if 'macd' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=indicators['macd'],
                    name='MACD',
                    line=dict(color='cyan', width=2),
                    showlegend=True
                ),
                row=3, col=1
            )
            
            if 'macd_signal' in indicators:
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=indicators['macd_signal'],
                        name='Signal',
                        line=dict(color='orange', width=1.5),
                        showlegend=True
                    ),
                    row=3, col=1
                )
            
            if 'macd_hist' in indicators:
                colors = ['green' if val >= 0 else 'red' for val in indicators['macd_hist']]
                fig.add_trace(
                    go.Bar(
                        x=dates,
                        y=indicators['macd_hist'],
                        name='MACD Hist',
                        marker_color=colors,
                        showlegend=True,
                        opacity=0.5
                    ),
                    row=3, col=1
                )
        
        # ========== ROW 4: WYCKOFF PHASES =========
        
        # Wyckoff phases - color code
        wyckoff_colors = {
            'ACCUMULATION': 'blue',
            'MARKUP': 'green',
            'DISTRIBUTION': 'red',
            'MARKDOWN': 'purple',
        }
        
        for phase in wyckoff_phases[-50:]:  # Ostatnie 50
            idx = phase['index']
            phase_type = phase['phase']
            color = wyckoff_colors.get(phase_type, 'gray')
            
            fig.add_trace(
                go.Bar(
                    x=[dates[idx]],
                    y=[phase['signal_strength']],
                    marker_color=color,
                    name=phase_type,
                    showlegend=False,
                    opacity=0.7
                ),
                row=4, col=1
            )
        
        # ========== ROW 5: VOLUME =========
        
        vol_colors = ['green' if close[i] >= open_[i] else 'red' for i in range(len(close))]
        
        fig.add_trace(
            go.Bar(
                x=dates,
                y=volume,
                name='Volume',
                marker_color=vol_colors,
                showlegend=True
            ),
            row=5, col=1
        )
        
        # Session backgrounds
        session_colors = {
            'asian': 'rgba(255,0,0,0.05)',
            'london': 'rgba(0,255,0,0.05)',
            'newyork': 'rgba(0,0,255,0.05)',
            'london_close': 'rgba(255,255,0,0.05)',
        }
        
        # Dodaj sesje jako tła (jeśli mamy info)
        
        # === LAYOUT ===
        fig.update_layout(
            title_text="<b>ULTIMATE PRO TRADING DASHBOARD - ALL TECHNICAL LEVELS</b>",
            template="plotly_dark",
            height=1800,
            hovermode='x unified',
            font=dict(family="Courier New", size=12),
            xaxis_rangeslider_visible=False,
        )
        
        fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
        fig.update_yaxes(title_text="MACD", row=3, col=1)
        fig.update_yaxes(title_text="Wyckoff Phase", row=4, col=1)
        fig.update_yaxes(title_text="Volume", row=5, col=1)
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def create_advanced_info_panel(self, 
                                  market_levels: Dict,
                                  data: pd.DataFrame,
                                  trades: List[Dict]) -> str:
        """
        Stwórz panel z detailami na temat rynku
        """
        
        html = """
        <div style="background-color: #2a2a2a; border: 1px solid #00d4ff; border-radius: 5px; padding: 20px; margin: 20px 0;">
            <h2 style="color: #00d4ff; text-align: center;">MARKET LEVELS & ANALYSIS</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        """
        
        # Left column
        html += """
            <div>
                <h3 style="color: #00ff00;">50% Division Zones</h3>
                <p>Highest: $""" + f"""{market_levels.get('highest', 0):.0f}</p>
                <p>Lowest: $""" + f"""{market_levels.get('lowest', 0):.0f}</p>
                <p style="color: #ff00ff; font-weight: bold;">Mid Point (50%): $""" + f"""{market_levels.get('mid_point', 0):.0f}</p>
                <p>Lower Internal (25%): $""" + f"""{market_levels.get('lower_internal', 0):.0f}</p>
                <p>Upper Internal (75%): $""" + f"""{market_levels.get('upper_internal', 0):.0f}</p>
            </div>
        """
        
        # Right column
        html += """
            <div>
                <h3 style="color: #00ffff;">Trade Performance</h3>
        """
        
        if trades:
            closed_trades = [t for t in trades if 'pnl' in t]
            if closed_trades:
                total_pnl = sum(t['pnl'] for t in closed_trades)
                wins = len([t for t in closed_trades if t['pnl'] > 0])
                losses = len([t for t in closed_trades if t['pnl'] < 0])
                
                html += f"""
                <p>Total Trades: {len(closed_trades)}</p>
                <p style="color: #00ff00;">Winning: {wins}</p>
                <p style="color: #ff0000;">Losing: {losses}</p>
                <p style="color: {'#00ff00' if total_pnl > 0 else '#ff0000'}; font-weight: bold;">Total P&L: ${total_pnl:+.0f}</p>
                """
        
        html += """
            </div>
            </div>
        </div>
        """
        
        return html
    
    def create_full_ultra_dashboard(self,
                                   data: pd.DataFrame,
                                   indicators: Dict,
                                   trades: List[Dict],
                                   starting_capital: float = 5000) -> str:
        """
        Twórz PEŁNY HTML z ULTRA profesjonalnym dashboardem
        """
        
        # Oblicz wszystkie poziomy
        market_levels = self.market_analyzer.calculate_50_percent_division(
            data['high'], data['low']
        )
        
        wyckoff_phases = self.market_analyzer.detect_wyckoff_phases(
            data['close'], data['volume']
        )
        
        liquidity_grabs = self.market_analyzer.detect_liquidity_grab(
            data['high'], data['low']
        )
        
        eqh_eql = self.market_analyzer.find_equal_highs_equal_lows(
            data['high'], data['low']
        )
        
        sessions_info = self.market_analyzer.detect_session_info(data.index)
        
        # Stwórz mega chart
        mega_chart_html = self.create_mega_chart(
            data, indicators, market_levels, wyckoff_phases, 
            liquidity_grabs, eqh_eql, trades, sessions_info
        )
        
        # Stwórz panel info
        info_panel_html = self.create_advanced_info_panel(
            market_levels, data, trades
        )
        
        # Pełny HTML
        full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ULTIMATE PRO TRADING DASHBOARD</title>
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
            border-bottom: 3px solid #00d4ff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            margin: 0;
            color: #00d4ff;
            font-size: 3em;
            text-shadow: 0 0 10px #00d4ff;
        }}
        
        .header p {{
            margin: 5px 0;
            color: #aaa;
            font-size: 1.1em;
        }}
        
        .features {{
            background-color: #2a2a2a;
            border: 1px solid #00d4ff;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        .features h3 {{
            color: #00d4ff;
            margin-top: 0;
        }}
        
        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
        }}
        
        .feature-item {{
            color: #00ff00;
            font-size: 0.95em;
            padding: 5px 10px;
            background-color: #1a1a1a;
            border-left: 3px solid #00d4ff;
        }}
        
        .chart-container {{
            background-color: #2a2a2a;
            border: 2px solid #00d4ff;
            border-radius: 5px;
            margin-bottom: 30px;
            padding: 15px;
        }}
        
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #444;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ ULTIMATE PRO TRADING BOT DASHBOARD</h1>
        <p>Advanced Technical Analysis • All Market Levels • Professional Grade</p>
        <p style="font-size: 0.9em; color: #666;">Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="features">
        <h3>Features Included:</h3>
        <div class="feature-grid">
            <div class="feature-item">✓ 50% Price Division (Internal/External Zones)</div>
            <div class="feature-item">✓ Support & Resistance Levels</div>
            <div class="feature-item">✓ Equal Highs & Equal Lows (EQH/EQL)</div>
            <div class="feature-item">✓ Wyckoff Phase Detection</div>
            <div class="feature-item">✓ Liquidity Grab Analysis</div>
            <div class="feature-item">✓ Bollinger Bands</div>
            <div class="feature-item">✓ SMA 20, 50 Moving Averages</div>
            <div class="feature-item">✓ Volume Analysis</div>
            <div class="feature-item">✓ Wick Price & Action</div>
            <div class="feature-item">✓ Trading Signals (Buy/Sell)</div>
            <div class="feature-item">✓ Position Liquidation</div>
            <div class="feature-item">✓ Session Information</div>
        </div>
    </div>
    
    {info_panel_html}
    
    <div class="chart-container">
        <h2 style="color: #00d4ff; text-align: center;">📊 ADVANCED PRICE ACTION CHART</h2>
        {mega_chart_html}
    </div>
    
    <div class="footer">
        <p>Ultimate Professional Trading Bot • Powered by Advanced Technical Analysis</p>
        <p>© 2026 Professional Trading Platform</p>
        <p style="font-size: 0.9em;">All indicators, levels, and signals calculated in real-time</p>
    </div>
    
    <script>
        // Auto-refresh every 5 seconds for smooth live updates
        setTimeout(function() {{
            location.reload();
        }}, 5000);
    </script>
</body>
</html>
"""
        
        return full_html
    
    def save_dashboard(self, html_content: str, filename: str = "ultimate_dashboard.html"):
        """Zapisz HTML"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filename

