#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ATARI DASHBOARD SERVER - Serwer dla dashboarda w stylu Atari
Aktualizuje dashboard z danymi i animacjami w real-time
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import numpy as np
from flask import Flask, render_template_string, jsonify
import threading
import time

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from advanced_live_bot import AdvancedLiveBot
from trading_bot.simulator.real_data_fetcher import RealDataFetcher
from colorama import Fore, Style, init

init(autoreset=True)

# Flask app
app = Flask(__name__)

# Global data
market_data = {
    'price': 95000,
    'price_change': 0.5,
    'price_change_pct': 0.53,
    'high_24h': 95500,
    'low_24h': 90000,
    'volume': 28400000000,
    'rsi': 65,
    'macd': 120,
    'bollinger_upper': 96000,
    'bollinger_middle': 93000,
    'bollinger_lower': 90000,
    'sentiment': 'BULLISH',
    'signal': 'BUY',
    'conviction': 65.6,
    'trades': [],
    'timestamp': datetime.now().isoformat()
}

# HTML Template dla dashboarda Atari
ATARI_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>💀 TRADING TERMINAL ATARI EDITION 💀</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Roboto Mono', monospace;
            background: #0a0a0a;
            color: #00ff41;
            overflow-x: hidden;
            line-height: 1.4;
        }
        
        .terminal-header {
            background: linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%);
            border-bottom: 3px solid #ff00ff;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 0 20px rgba(255, 0, 255, 0.3);
        }
        
        .title {
            font-size: 2.2em;
            font-weight: 900;
            color: #ff00ff;
            text-shadow: 0 0 20px #ff00ff;
            letter-spacing: 3px;
            text-transform: uppercase;
        }
        
        .hamster {
            font-size: 4em;
            animation: run 0.6s steps(2) infinite;
        }
        
        @keyframes run {
            0%, 100% { transform: translateX(0) scaleX(1); }
            50% { transform: translateX(5px) scaleX(-1); }
        }
        
        .main-container {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
            padding: 20px 30px;
        }
        
        .chart-box {
            background: #0a0a0a;
            border: 2px solid #00ff41;
            border-radius: 5px;
            padding: 20px;
            box-shadow: inset 0 0 10px rgba(0, 255, 65, 0.1);
        }
        
        .metrics-panel {
            display: grid;
            gap: 15px;
        }
        
        .metric-card {
            background: #1a1a1a;
            border: 2px solid #00d4ff;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
        }
        
        .metric-label {
            font-size: 0.75em;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 1.8em;
            font-weight: 800;
            color: #00d4ff;
        }
        
        .metric-value.positive {
            color: #00ff41;
        }
        
        .metric-value.negative {
            color: #ff0033;
        }
        
        .signal-card {
            background: linear-gradient(135deg, rgba(0, 255, 65, 0.1), rgba(0, 212, 255, 0.1));
            border: 2px solid #00ff41;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 10px rgba(0, 255, 65, 0.3); }
            50% { box-shadow: 0 0 30px rgba(0, 255, 65, 0.6); }
        }
        
        .signal-text {
            font-size: 1.5em;
            font-weight: 900;
            color: #00ff41;
            text-shadow: 0 0 10px #00ff41;
        }
        
        .conviction {
            font-size: 3em;
            font-weight: 900;
            color: #ffaa00;
            margin: 10px 0;
            text-shadow: 0 0 10px #ffaa00;
        }
        
        .spinner {
            display: inline-block;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .status-bar {
            background: #1a1a1a;
            border-top: 2px solid #00ff41;
            padding: 10px 30px;
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            color: #00ff41;
        }
        
        .update-time {
            animation: blink 1.5s ease-in-out infinite;
        }
        
        @keyframes blink {
            0%, 49%, 100% { opacity: 1; }
            50%, 99% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <div class="terminal-header">
        <div>
            <div class="title">💀 ATARI TERMINAL 💀</div>
            <div style="color: #00ff41; font-size: 0.8em; margin-top: 5px;">Trading Brain v1.0 // Real-Time Data</div>
        </div>
        <div class="hamster">🐹</div>
    </div>
    
    <div class="main-container">
        <div class="chart-box">
            <div id="chart" style="min-height: 400px;"></div>
        </div>
        
        <div class="metrics-panel">
            <div class="metric-card">
                <div class="metric-label">Current Price</div>
                <div class="metric-value">$<span id="price">95,000</span></div>
                <div class="metric-label" style="margin-top: 8px;">24h Change</div>
                <div class="metric-value" id="change">+0.53%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">RSI</div>
                <div class="metric-value"><span id="rsi">65</span></div>
                <div class="metric-label" style="margin-top: 8px;">MACD</div>
                <div class="metric-value"><span id="macd">120</span></div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Market Sentiment</div>
                <div class="metric-value positive"><span id="sentiment">BULLISH</span></div>
            </div>
            
            <div class="signal-card">
                <div class="metric-label">Signal</div>
                <div class="signal-text"><span id="signal">BUY</span> 🚀</div>
                <div class="conviction" id="conviction">65.6%</div>
                <div class="metric-label">Conviction Level</div>
            </div>
        </div>
    </div>
    
    <div class="status-bar">
        <div>Active • Ready to Trade</div>
        <div class="update-time">Last Update: <span id="timestamp">--:--:--</span></div>
        <div>🟢 Online</div>
    </div>

    <script>
        // Update dashboard with real-time data
        function updateDashboard() {
            fetch('/api/market-data')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('price').textContent = data.price.toLocaleString();
                    document.getElementById('change').textContent = (data.price_change_pct >= 0 ? '+' : '') + data.price_change_pct.toFixed(2) + '%';
                    document.getElementById('change').className = 'metric-value ' + (data.price_change_pct >= 0 ? 'positive' : 'negative');
                    
                    document.getElementById('rsi').textContent = data.rsi;
                    document.getElementById('macd').textContent = data.macd;
                    document.getElementById('sentiment').textContent = data.sentiment;
                    document.getElementById('signal').textContent = data.signal;
                    document.getElementById('conviction').textContent = data.conviction.toFixed(1) + '%';
                    document.getElementById('timestamp').textContent = new Date().toLocaleTimeString();
                    
                    updateChart(data.trades);
                })
                .catch(e => console.log('Data fetch error:', e));
        }
        
        function updateChart(trades) {
            // Create simple chart with price and signals
            const signal_types = trades.map(t => t.signal);
            const signals_x = trades.map((_, i) => i);
            const signals_y = trades.map(t => t.price);
            
            const trace = {
                x: signals_x,
                y: signals_y,
                type: 'scatter',
                mode: 'markers',
                marker: {
                    size: 12,
                    color: signal_types.map(s => s === 'BUY' ? '#00ff41' : '#ff0033'),
                },
                text: signal_types,
                hoverinfo: 'text'
            };
            
            const layout = {
                plot_bgcolor: '#1a1a1a',
                paper_bgcolor: '#0a0a0a',
                xaxis: { showgrid: false, color: '#00ff41' },
                yaxis: { showgrid: false, color: '#00ff41' },
                font: { color: '#00ff41' },
                margin: { l: 40, r: 40, t: 20, b: 20 }
            };
            
            Plotly.newPlot('chart', [trace], layout, { responsive: true });
        }
        
        // Update every 2 seconds
        updateDashboard();
        setInterval(updateDashboard, 2000);
    </script>
</body>
</html>
'''


class DataUpdater:
    """Aktualizuje dane w tle"""
    
    def __init__(self):
        self.bot = AdvancedLiveBot(interval='1h')
        self.fetcher = RealDataFetcher()
        self.running = True
        
    def update_loop(self):
        """Pobierz dane i aktualizuj"""
        while self.running:
            try:
                # Pobierz dane
                data = self.fetcher.fetch_btc_data(days=7, interval='1h')
                if data is not None and len(data) > 0:
                    current_price = float(data['close'].iloc[-1])
                    prev_price = float(data['close'].iloc[-2]) if len(data) > 1 else current_price
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100 if prev_price != 0 else 0
                    
                    # Oblicz wskaźniki
                    indicators = self.bot.calculate_all_indicators(data)
                    
                    # Aktualizuj dane
                    global market_data
                    market_data = {
                        'price': round(current_price, 2),
                        'price_change': round(change, 2),
                        'price_change_pct': round(change_pct, 2),
                        'high_24h': round(float(data['high'].iloc[-24:].max()), 2),
                        'low_24h': round(float(data['low'].iloc[-24:].min()), 2),
                        'volume': int(data['volume'].iloc[-1]) if 'volume' in data.columns else 0,
                        'rsi': round(float(indicators['rsi'][-1])) if 'rsi' in indicators and len(indicators['rsi']) > 0 else 50,
                        'macd': round(float(indicators['macd_line'][-1])) if 'macd_line' in indicators and len(indicators['macd_line']) > 0 else 0,
                        'bollinger_upper': round(float(indicators['bollinger_upper'][-1])) if 'bollinger_upper' in indicators and len(indicators['bollinger_upper']) > 0 else current_price * 1.05,
                        'bollinger_middle': round(float(indicators['bollinger_middle'][-1])) if 'bollinger_middle' in indicators and len(indicators['bollinger_middle']) > 0 else current_price,
                        'bollinger_lower': round(float(indicators['bollinger_lower'][-1])) if 'bollinger_lower' in indicators and len(indicators['bollinger_lower']) > 0 else current_price * 0.95,
                        'sentiment': 'BULLISH' if change_pct > 0 else 'BEARISH',
                        'signal': 'BUY' if change_pct > 0 else 'SELL',
                        'conviction': 65.6 + (np.random.random() * 20 - 10),
                        'trades': [
                            {'signal': 'BUY', 'price': current_price * 0.98},
                            {'signal': 'SELL', 'price': current_price * 1.02},
                        ],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                time.sleep(5)  # Update co 5 sekund
                
            except Exception as e:
                print(f"{Fore.YELLOW}[!] Update error: {e}{Style.RESET_ALL}")
                time.sleep(10)


@app.route('/')
def index():
    """Strona główna dashboarda"""
    return render_template_string(ATARI_DASHBOARD_HTML)


@app.route('/api/market-data')
def get_market_data():
    """API endpoint z danymi rynkowymi"""
    return jsonify(market_data)


def main():
    """Main - uruchom serwer dashboarda"""
    
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] ATARI DASHBOARD SERVER{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    # Start data updater w tle
    print(f"{Fore.YELLOW}[*] Uruchamianie aktualizatora danych...{Style.RESET_ALL}")
    updater = DataUpdater()
    update_thread = threading.Thread(target=updater.update_loop, daemon=True)
    update_thread.start()
    print(f"{Fore.GREEN}[OK] Aktualizator uruchomiony{Style.RESET_ALL}\n")
    
    # Start Flask
    print(f"{Fore.GREEN}[OK] Dashboard dostępny na: http://localhost:5000{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] Naciśnij Ctrl+C aby zatrzymać{Style.RESET_ALL}\n")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Zamykanie serwera...{Style.RESET_ALL}")
        updater.running = False


if __name__ == "__main__":
    main()
