#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ALPHA TERMINAL - Desktop Professional Trading Application
CustomTkinter GUI with Live Tape, Order Flow, AI Insights
"""

import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yfinance as yf
from datetime import datetime, timedelta
import random
import threading
import time

# Try to import bot modules
try:
    from trading_bot.simulator.real_data_fetcher import RealDataFetcher
    from live_indicators_analyzer import LiveIndicatorsAnalyzer
    HAS_BOT = True
except:
    HAS_BOT = False
    print("[!] Bot modules not found, using simulation mode")


class AlphaTerminalFullStack(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.title("⚡ ALPHA TERMINAL - LIVE TAPE & ORDER FLOW")
        self.geometry("1800x1000")
        self.configure(fg_color="#050505")
        
        # Data storage
        self.current_symbol = "BTC-USD"
        self.current_data = None
        self.is_running = True
        self.tape_entries = []
        
        # Initialize bot modules if available
        if HAS_BOT:
            self.fetcher = RealDataFetcher()
            self.analyzer = LiveIndicatorsAnalyzer()
        
        # Setup UI
        self.setup_ui()
        
        # Start live feed in separate thread
        self.feed_thread = threading.Thread(target=self.live_feed_loop, daemon=True)
        self.feed_thread.start()

    def setup_ui(self):
        """Setup the main UI layout"""
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)  # Chart
        self.grid_columnconfigure(1, weight=1)  # Middle panel
        self.grid_columnconfigure(2, weight=1)  # Tape panel
        
        # --- TOP BAR ---
        self.setup_top_bar()
        
        # --- CHART PANEL (LEFT) ---
        self.setup_chart_panel()
        
        # --- MIDDLE PANEL (CENTER) ---
        self.setup_middle_panel()
        
        # --- TAPE PANEL (RIGHT) ---
        self.setup_tape_panel()

    def setup_top_bar(self):
        """Create top control bar"""
        top_bar = ctk.CTkFrame(self, fg_color="#101214", height=60, corner_radius=0)
        top_bar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 2))
        top_bar.grid_propagate(False)
        
        # Title
        ctk.CTkLabel(
            top_bar, 
            text="⚡ ALPHA TERMINAL", 
            font=("Arial", 24, "bold"),
            text_color="#00d4ff"
        ).pack(side="left", padx=20, pady=10)
        
        # Symbol selector
        ctk.CTkLabel(top_bar, text="Symbol:", text_color="#888").pack(side="left", padx=(50, 5))
        self.symbol_entry = ctk.CTkEntry(top_bar, width=120)
        self.symbol_entry.insert(0, "BTC-USD")
        self.symbol_entry.pack(side="left", padx=5)
        
        # Update button
        ctk.CTkButton(
            top_bar,
            text="🔄 Update",
            command=self.change_symbol,
            fg_color="#00d4ff",
            hover_color="#0099cc",
            width=100
        ).pack(side="left", padx=10)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            top_bar,
            text="● LIVE",
            font=("Arial", 12, "bold"),
            text_color="#00ff41"
        )
        self.status_label.pack(side="right", padx=20)

    def setup_chart_panel(self):
        """Setup chart panel"""
        self.chart_frame = ctk.CTkFrame(self, fg_color="#050505", corner_radius=8)
        self.chart_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Chart title
        chart_header = ctk.CTkFrame(self.chart_frame, fg_color="#101214", height=40)
        chart_header.pack(fill="x", pady=(5, 10), padx=5)
        
        ctk.CTkLabel(
            chart_header,
            text="📈 PRICE CHART WITH FVG & SESSION MARKERS",
            font=("Arial", 14, "bold"),
            text_color="#f0b90b"
        ).pack(pady=8)
        
        # Placeholder for matplotlib chart
        self.chart_container = ctk.CTkFrame(self.chart_frame, fg_color="#050505")
        self.chart_container.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_middle_panel(self):
        """Setup middle panel with metrics and AI"""
        self.mid_panel = ctk.CTkFrame(self, fg_color="#101214", corner_radius=8)
        self.mid_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Header
        ctk.CTkLabel(
            self.mid_panel,
            text="🧠 MARKET INSIGHTS",
            font=("Arial", 16, "bold"),
            text_color="#f0b90b"
        ).pack(pady=10)
        
        # Metrics Frame
        metrics_frame = ctk.CTkFrame(self.mid_panel, fg_color="#050505", corner_radius=8)
        metrics_frame.pack(fill="x", padx=10, pady=10)
        
        # Price metric
        self.price_label = ctk.CTkLabel(
            metrics_frame,
            text="PRICE: $0.00",
            font=("Consolas", 18, "bold"),
            text_color="#00d4ff"
        )
        self.price_label.pack(pady=5)
        
        # Change metric
        self.change_label = ctk.CTkLabel(
            metrics_frame,
            text="24h: +0.00%",
            font=("Consolas", 14),
            text_color="#00ff41"
        )
        self.change_label.pack(pady=5)
        
        # RSI metric
        self.rsi_label = ctk.CTkLabel(
            metrics_frame,
            text="RSI: 50.0",
            font=("Consolas", 12),
            text_color="#888"
        )
        self.rsi_label.pack(pady=5)
        
        # Session info
        self.session_label = ctk.CTkLabel(
            self.mid_panel,
            text="SESSION: Loading...",
            font=("Consolas", 11),
            text_color="#888",
            justify="left"
        )
        self.session_label.pack(pady=10, padx=10)
        
        # AI Insights Box
        ctk.CTkLabel(
            self.mid_panel,
            text="🤖 AI ANALYSIS",
            font=("Arial", 13, "bold"),
            text_color="#ff00ff"
        ).pack(pady=(10, 5))
        
        self.ai_box = ctk.CTkTextbox(
            self.mid_panel,
            height=350,
            fg_color="#050505",
            border_width=1,
            border_color="#333",
            font=("Consolas", 11)
        )
        self.ai_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.ai_box.insert("1.0", "Waiting for market data...\n")

    def setup_tape_panel(self):
        """Setup THE TAPE panel (Time & Sales)"""
        self.tape_panel = ctk.CTkFrame(self, fg_color="#0d0d0d", corner_radius=8)
        self.tape_panel.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        
        # Header
        ctk.CTkLabel(
            self.tape_panel,
            text="📜 THE TAPE (TIME & SALES)",
            font=("Arial", 14, "bold"),
            text_color="#00ff41"
        ).pack(pady=10)
        
        # Column headers
        header_frame = ctk.CTkFrame(self.tape_panel, fg_color="#101214", height=30)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        header_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            header_frame,
            text="TIME",
            width=80,
            font=("Arial", 10, "bold"),
            text_color="#888"
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            header_frame,
            text="PRICE",
            width=100,
            font=("Arial", 10, "bold"),
            text_color="#888"
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            header_frame,
            text="SIZE",
            width=80,
            font=("Arial", 10, "bold"),
            text_color="#888"
        ).pack(side="left", padx=5)
        
        # Tape textbox
        self.tape_box = ctk.CTkTextbox(
            self.tape_panel,
            fg_color="#050505",
            font=("Consolas", 11),
            border_width=1,
            border_color="#333"
        )
        self.tape_box.pack(fill="both", expand=True, padx=10, pady=5)

    def change_symbol(self):
        """Change trading symbol"""
        new_symbol = self.symbol_entry.get().upper().strip()
        if new_symbol:
            self.current_symbol = new_symbol
            self.tape_entries = []
            self.update_status("Updating...", "#ffaa00")
            self.update_ai_box(f"Switching to {new_symbol}...\n")

    def update_status(self, text, color):
        """Update status indicator"""
        self.status_label.configure(text=f"● {text}", text_color=color)

    def update_metrics(self, price, change_pct, rsi):
        """Update metric labels"""
        self.price_label.configure(text=f"PRICE: ${price:,.2f}")
        
        change_color = "#00ff41" if change_pct >= 0 else "#ff0033"
        self.change_label.configure(
            text=f"24h: {change_pct:+.2f}%",
            text_color=change_color
        )
        
        rsi_color = "#ff0033" if rsi > 70 else "#00ff41" if rsi < 30 else "#ffaa00"
        self.rsi_label.configure(
            text=f"RSI: {rsi:.1f}",
            text_color=rsi_color
        )

    def detect_session(self):
        """Detect current market session"""
        hour = datetime.now().hour
        
        if 0 <= hour < 8:
            return "🌏 ASIAN SESSION (TOKYO)", "#ff9500"
        elif 8 <= hour < 16:
            return "🇬🇧 LONDON SESSION (HIGH VOLUME)", "#00d4ff"
        elif 16 <= hour < 24:
            return "🇺🇸 NEW YORK SESSION (WALL STREET)", "#00ff41"
        else:
            return "🌙 AFTER HOURS", "#888"

    def update_session_info(self):
        """Update session label"""
        session_name, color = self.detect_session()
        self.session_label.configure(
            text=f"SESSION: {session_name}\nTime: {datetime.now().strftime('%H:%M:%S')}",
            text_color=color
        )

    def update_tape(self, price):
        """Add entry to THE TAPE"""
        now = datetime.now().strftime("%H:%M:%S")
        size = round(random.uniform(0.05, 5.5), 3)
        
        # Detect whale trade
        is_whale = size > 3.0
        prefix = "🐳 " if is_whale else "   "
        
        entry = f"{prefix}{now}    ${price:,.2f}    {size:.3f}\n"
        
        # Add to tape
        self.tape_box.insert("1.0", entry)
        
        # Keep only last 50 entries
        lines = self.tape_box.get("1.0", "end").split("\n")
        if len(lines) > 50:
            self.tape_box.delete("50.0", "end")

    def update_ai_box(self, text):
        """Update AI insights box"""
        self.ai_box.delete("1.0", "end")
        self.ai_box.insert("1.0", text)

    def generate_ai_insights(self, df, indicators):
        """Generate AI market insights"""
        try:
            rsi = indicators['rsi'].iloc[-1]
            macd = indicators['macd'].iloc[-1]
            sentiment = indicators['sentiment'].iloc[-1]
            
            insights = []
            insights.append("🤖 AI MARKET ANALYSIS\n")
            insights.append("=" * 40 + "\n\n")
            
            # RSI Analysis
            if rsi > 70:
                insights.append("⚠️ OVERBOUGHT ZONE\n")
                insights.append(f"RSI at {rsi:.1f} suggests potential reversal.\n\n")
            elif rsi < 30:
                insights.append("💎 OVERSOLD ZONE\n")
                insights.append(f"RSI at {rsi:.1f} indicates buying opportunity.\n\n")
            else:
                insights.append("⚖️ NEUTRAL ZONE\n")
                insights.append(f"RSI at {rsi:.1f} - market in balance.\n\n")
            
            # MACD Analysis
            if macd > 0:
                insights.append("📈 BULLISH MOMENTUM\n")
                insights.append(f"MACD +{macd:.2f} - buyers in control.\n\n")
            else:
                insights.append("📉 BEARISH MOMENTUM\n")
                insights.append(f"MACD {macd:.2f} - sellers dominating.\n\n")
            
            # Sentiment
            if sentiment > 0.02:
                insights.append("🟢 POSITIVE SENTIMENT\n")
                insights.append("Market showing bullish conviction.\n\n")
            elif sentiment < -0.02:
                insights.append("🔴 NEGATIVE SENTIMENT\n")
                insights.append("Market showing bearish pressure.\n\n")
            
            # Trading suggestion
            insights.append("🎯 STRATEGY SUGGESTION:\n")
            if rsi < 40 and macd > 0:
                insights.append("✅ LONG BIAS - Consider accumulation\n")
            elif rsi > 60 and macd < 0:
                insights.append("❌ SHORT BIAS - Consider distribution\n")
            else:
                insights.append("⏳ WAIT - No clear edge detected\n")
            
            return "".join(insights)
            
        except Exception as e:
            return f"Error generating insights: {e}\n"

    def render_chart(self, df):
        """Render matplotlib chart with FVG and session markers"""
        try:
            # Clear previous chart
            for widget in self.chart_container.winfo_children():
                widget.destroy()
            
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 7), facecolor='#050505')
            ax.set_facecolor('#050505')
            
            # Plot price line
            ax.plot(df.index, df['Close'], color='#00d4ff', linewidth=1.5, alpha=0.8, label='Price')
            
            # Detect and mark FVG (Fair Value Gaps)
            fvg_count = 0
            for i in range(2, len(df)):
                # Bullish FVG
                if df['Low'].iloc[i] > df['High'].iloc[i-2]:
                    ax.axhspan(
                        df['High'].iloc[i-2],
                        df['Low'].iloc[i],
                        xmin=(i-2)/len(df),
                        xmax=i/len(df),
                        color='green',
                        alpha=0.15
                    )
                    fvg_count += 1
                
                # Bearish FVG
                elif df['High'].iloc[i] < df['Low'].iloc[i-2]:
                    ax.axhspan(
                        df['Low'].iloc[i-2],
                        df['High'].iloc[i],
                        xmin=(i-2)/len(df),
                        xmax=i/len(df),
                        color='red',
                        alpha=0.15
                    )
                    fvg_count += 1
            
            # Mark highs and lows
            high_idx = df['High'].idxmax()
            low_idx = df['Low'].idxmin()
            
            ax.scatter(high_idx, df.loc[high_idx, 'High'], color='gold', s=100, zorder=5, label='High')
            ax.scatter(low_idx, df.loc[low_idx, 'Low'], color='purple', s=100, zorder=5, label='Low')
            
            # Styling
            ax.tick_params(colors='#888', labelsize=9)
            ax.spines['bottom'].set_color('#333')
            ax.spines['top'].set_color('#333')
            ax.spines['left'].set_color('#333')
            ax.spines['right'].set_color('#333')
            ax.grid(alpha=0.1, color='#333')
            ax.legend(loc='upper left', fontsize=9, facecolor='#101214', edgecolor='#333')
            
            plt.title(f'{self.current_symbol} - FVG Detection ({fvg_count} gaps found)', 
                     color='#00d4ff', fontsize=12, pad=10)
            plt.tight_layout()
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            plt.close(fig)
            
        except Exception as e:
            print(f"Chart render error: {e}")

    def live_feed_loop(self):
        """Main live feed loop (runs in separate thread)"""
        while self.is_running:
            try:
                # Fetch data
                if HAS_BOT:
                    df = self.fetcher.fetch_data(self.current_symbol, period='2d', interval='15m')
                else:
                    df = yf.download(self.current_symbol, period='2d', interval='15m', progress=False)
                
                if df is not None and len(df) > 50:
                    # Calculate indicators
                    if HAS_BOT:
                        indicators = self.analyzer.calculate_all_indicators(df)
                    else:
                        # Simple indicators fallback
                        indicators = {
                            'rsi': self._calculate_rsi(df['Close'], 14),
                            'macd': self._calculate_simple_momentum(df['Close']),
                            'sentiment': pd.Series([0] * len(df), index=df.index)
                        }
                    
                    # Update UI (must use after to run in main thread)
                    current_price = float(df['Close'].iloc[-1])
                    change_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
                    rsi = float(indicators['rsi'].iloc[-1])
                    
                    self.after(0, self.update_metrics, current_price, change_pct, rsi)
                    self.after(0, self.update_session_info)
                    self.after(0, self.update_tape, current_price)
                    self.after(0, self.render_chart, df)
                    
                    ai_text = self.generate_ai_insights(df, indicators)
                    self.after(0, self.update_ai_box, ai_text)
                    self.after(0, self.update_status, "LIVE", "#00ff41")
                    
                else:
                    self.after(0, self.update_status, "NO DATA", "#ff0033")
                
                # Update every 3 seconds
                time.sleep(3)
                
            except Exception as e:
                print(f"Feed error: {e}")
                self.after(0, self.update_status, "ERROR", "#ff0033")
                time.sleep(5)

    def _calculate_rsi(self, series, period=14):
        """Simple RSI calculation"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_simple_momentum(self, series, period=10):
        """Simple momentum calculation"""
        return series.diff(period)

    def on_closing(self):
        """Handle window close"""
        self.is_running = False
        self.destroy()


if __name__ == "__main__":
    # Set appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Launch app
    app = AlphaTerminalFullStack()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
