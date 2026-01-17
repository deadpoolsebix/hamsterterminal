#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ALPHA TERMINAL - Professional Bloomberg-Style Dashboard with AI
Streamlit Web Application
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. KONFIGURACJA W STYLU BLOOMBERG
st.set_page_config(page_title="ALPHA TERMINAL AI", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0b0e11; }
    .stMetric { background-color: #1e222d; padding: 15px; border-radius: 10px; border: 1px solid #363a45; }
    h1, h2, h3 { color: #00d4ff; font-family: 'Roboto Mono', monospace; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e222d;
        border-radius: 8px;
        padding: 10px 20px;
        color: #00d4ff;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00d4ff;
        color: #0b0e11;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ ALPHA TERMINAL: MARKET INSIGHTS & AI")
st.markdown("**Professional Grade Analysis • Powered by Bloomberg Engine**")

# SIDEBAR - KONTROLA OPERACYJNA
st.sidebar.header("🕹️ PANEL STEROWANIA")
symbol = st.sidebar.text_input("INSTRUMENT", "BTC-USD")
timeframe = st.sidebar.selectbox("INTERWAŁ", ["1h", "4h", "1d"])
history_days = st.sidebar.slider("DANE HISTORYCZNE (DNI)", 30, 365, 90)

# Advanced Options
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Zaawansowane")
show_fvg = st.sidebar.checkbox("Pokaż Fair Value Gaps", value=True)
show_macd = st.sidebar.checkbox("Pokaż MACD", value=True)
show_volume = st.sidebar.checkbox("Pokaż Volume Profile", value=True)

# POBIERANIE DANYCH
@st.cache_data
def load_data(ticker, days, interval):
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        data = yf.download(ticker, start=start, end=end, interval=interval)
        return data
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return None

df = load_data(symbol, history_days, timeframe)

if df is None or len(df) == 0:
    st.error("Brak danych do wyświetlenia. Sprawdź symbol i spróbuj ponownie.")
    st.stop()

# --- 2. ANALIZA MOMENTUM & CORE METRICS ---
# Obliczamy RSI, MACD i SMI (Stochastic Momentum Index)
df['RSI'] = ta.rsi(df['Close'], length=14)
macd = ta.macd(df['Close'])
df = pd.concat([df, macd], axis=1)
df['Momentum'] = ta.mom(df['Close'], length=10)

# Bollinger Bands
bbands = ta.bbands(df['Close'], length=20)
df = pd.concat([df, bbands], axis=1)

# --- 3. ANALIZA HISTORYCZNA (BACKTESTING LITE) ---
avg_volatility = df['High'].sub(df['Low']).mean()
all_time_high = df['High'].max()
all_time_low = df['Low'].min()
performance = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100

# --- 4. MODUŁ AI INSIGHTS (SYMULACJA LOGIKI) ---
def get_ai_insight(rsi, mom, perf, macd_val):
    insights = []
    
    # RSI Analysis
    if rsi > 70:
        if mom > 0:
            insights.append("⚠️ **DYWERGENCJA**: Rynek przegrzany, ale trend silny. Możliwa pułapka na byki.")
        else:
            insights.append("🔴 **OVERBOUGHT**: RSI > 70. Wysoka szansa na korektę.")
    elif rsi < 30:
        insights.append("💎 **OKAZJA**: Wyprzedanie historyczne. Algorytmy sugerują akumulację.")
    
    # Performance Analysis
    if perf > 20:
        insights.append("📈 **STRONG RALLY**: Trend wzrostowy powyżej +20%. Szukaj wejść w lukach FVG.")
    elif perf > 10:
        insights.append("📈 **RALLY**: Silny trend wzrostowy. Kontynuacja prawdopodobna.")
    elif perf < -10:
        insights.append("📉 **CORRECTION**: Spadek powyżej -10%. Sprawdź wsparcia.")
    
    # MACD Analysis
    if macd_val > 0:
        insights.append("🟢 **MOMENTUM BULLISH**: MACD powyżej zera - presja kupujących.")
    else:
        insights.append("🔴 **MOMENTUM BEARISH**: MACD poniżej zera - presja sprzedających.")
    
    # Default
    if not insights:
        insights.append("⚖️ **KONSOLIDACJA**: Brak wyraźnego kierunku. Czekaj na wybicie.")
    
    return "\n\n".join(insights)

# Calculate current values
current_rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
current_mom = df['Momentum'].iloc[-1] if not pd.isna(df['Momentum'].iloc[-1]) else 0
current_macd = df['MACD_12_26_9'].iloc[-1] if 'MACD_12_26_9' in df.columns and not pd.isna(df['MACD_12_26_9'].iloc[-1]) else 0

ai_comment = get_ai_insight(current_rsi, current_mom, performance, current_macd)

# --- 5. INTERFEJS UŻYTKOWNIKA ---
# Top Metrics
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

with col_m1:
    st.metric(
        "💰 AKTUALNA CENA", 
        f"${df['Close'].iloc[-1]:.2f}", 
        f"{performance:.2f}%",
        delta_color="normal" if performance > 0 else "inverse"
    )

with col_m2:
    st.metric(
        "📊 MOMENTUM (10)", 
        f"{current_mom:.2f}",
        "Bullish" if current_mom > 0 else "Bearish"
    )

with col_m3:
    rsi_status = "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"
    st.metric(
        "📉 RSI (14)", 
        f"{current_rsi:.1f}",
        rsi_status
    )

with col_m4:
    st.metric(
        "📈 VOLATILITY (AVG)", 
        f"${avg_volatility:.2f}",
        f"High: ${all_time_high:.2f}"
    )

with col_m5:
    vol_change = ((df['Volume'].iloc[-1] - df['Volume'].mean()) / df['Volume'].mean()) * 100
    st.metric(
        "📦 VOLUME", 
        f"{df['Volume'].iloc[-1]:,.0f}",
        f"{vol_change:+.1f}% vs avg"
    )

st.markdown("---")

# GŁÓWNY WYKRES Z FVG I MOMENTUM
tab1, tab2, tab3, tab4 = st.tabs(["📊 Wykres Pro", "🧠 AI Insights", "📜 Dane Historyczne", "📰 Market News"])

with tab1:
    st.subheader("Professional Chart with FVG Detection")
    
    fig = go.Figure()
    
    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index, 
        open=df['Open'], 
        high=df['High'], 
        low=df['Low'], 
        close=df['Close'], 
        name="Price"
    ))
    
    # Bollinger Bands
    if 'BBL_20_2.0' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df['BBU_20_2.0'], 
            line=dict(color='rgba(0, 212, 255, 0.3)', width=1),
            name="BB Upper"
        ))
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df['BBL_20_2.0'], 
            line=dict(color='rgba(0, 212, 255, 0.3)', width=1),
            fill='tonexty',
            fillcolor='rgba(0, 212, 255, 0.05)',
            name="BB Lower"
        ))
    
    # Detekcja FVG (Fair Value Gaps)
    if show_fvg:
        fvg_count = 0
        for i in range(2, len(df)):
            # Bull FVG (Bullish Fair Value Gap)
            if df['Low'].iloc[i] > df['High'].iloc[i-2]:
                fig.add_shape(
                    type="rect", 
                    x0=df.index[i-2], 
                    x1=df.index[i], 
                    y0=df['High'].iloc[i-2], 
                    y1=df['Low'].iloc[i], 
                    fillcolor="rgba(0, 255, 65, 0.15)", 
                    line_width=0,
                    layer="below"
                )
                fvg_count += 1
            
            # Bear FVG (Bearish Fair Value Gap)
            elif df['High'].iloc[i] < df['Low'].iloc[i-2]:
                fig.add_shape(
                    type="rect", 
                    x0=df.index[i-2], 
                    x1=df.index[i], 
                    y0=df['Low'].iloc[i-2], 
                    y1=df['High'].iloc[i], 
                    fillcolor="rgba(255, 0, 51, 0.15)", 
                    line_width=0,
                    layer="below"
                )
                fvg_count += 1
        
        st.info(f"🎯 Wykryto **{fvg_count}** Fair Value Gaps (FVG)")
    
    fig.update_layout(
        template="plotly_dark", 
        height=600, 
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        plot_bgcolor='#0b0e11',
        paper_bgcolor='#0b0e11'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # MACD Chart
    if show_macd and 'MACD_12_26_9' in df.columns:
        st.subheader("MACD Histogram")
        fig_macd = go.Figure()
        
        fig_macd.add_trace(go.Bar(
            x=df.index,
            y=df['MACDh_12_26_9'],
            marker_color=['green' if x > 0 else 'red' for x in df['MACDh_12_26_9']],
            name='MACD Histogram'
        ))
        
        fig_macd.add_trace(go.Scatter(
            x=df.index,
            y=df['MACD_12_26_9'],
            line=dict(color='#00d4ff', width=2),
            name='MACD'
        ))
        
        fig_macd.add_trace(go.Scatter(
            x=df.index,
            y=df['MACDs_12_26_9'],
            line=dict(color='#ff00ff', width=2),
            name='Signal'
        ))
        
        fig_macd.update_layout(
            template="plotly_dark",
            height=300,
            plot_bgcolor='#0b0e11',
            paper_bgcolor='#0b0e11'
        )
        
        st.plotly_chart(fig_macd, use_container_width=True)
    
    # Volume Profile
    if show_volume:
        st.subheader("Volume Analysis")
        fig_vol = go.Figure()
        
        colors = ['green' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'red' for i in range(len(df))]
        
        fig_vol.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            marker_color=colors,
            name='Volume'
        ))
        
        fig_vol.update_layout(
            template="plotly_dark",
            height=250,
            plot_bgcolor='#0b0e11',
            paper_bgcolor='#0b0e11'
        )
        
        st.plotly_chart(fig_vol, use_container_width=True)

with tab2:
    st.subheader("🤖 AI Market Sentiment & Analysis")
    st.markdown(ai_comment)
    
    st.markdown("---")
    
    # Technical Summary
    col_ai1, col_ai2 = st.columns(2)
    
    with col_ai1:
        st.markdown("### 📊 Technical Summary")
        st.write(f"**Symbol:** {symbol}")
        st.write(f"**Timeframe:** {timeframe}")
        st.write(f"**Period Performance:** {performance:+.2f}%")
        st.write(f"**All-Time High:** ${all_time_high:.2f}")
        st.write(f"**All-Time Low:** ${all_time_low:.2f}")
        st.write(f"**Current from ATH:** {((df['Close'].iloc[-1] - all_time_high) / all_time_high * 100):.2f}%")
    
    with col_ai2:
        st.markdown("### 🎯 Trading Signals")
        
        # Buy/Sell Signals based on indicators
        signals = []
        
        if current_rsi < 30:
            signals.append("🟢 **BUY SIGNAL**: RSI Oversold")
        elif current_rsi > 70:
            signals.append("🔴 **SELL SIGNAL**: RSI Overbought")
        
        if current_macd > 0 and current_mom > 0:
            signals.append("🟢 **BULLISH**: MACD & Momentum pozytywne")
        elif current_macd < 0 and current_mom < 0:
            signals.append("🔴 **BEARISH**: MACD & Momentum negatywne")
        
        if not signals:
            signals.append("⚪ **NEUTRAL**: Brak silnych sygnałów")
        
        for signal in signals:
            st.markdown(signal)

with tab3:
    st.subheader("📊 Statystyki Zakresu Ruchu")
    st.dataframe(df.describe(), use_container_width=True)
    
    st.subheader("📈 RSI History")
    st.line_chart(df['RSI'])
    
    st.subheader("📉 Recent Price Action (Last 20 bars)")
    st.dataframe(df[['Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'Momentum']].tail(20), use_container_width=True)

with tab4:
    st.subheader("📰 Latest Market News")
    
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if news and len(news) > 0:
            for n in news[:5]:
                with st.container():
                    st.markdown(f"### {n.get('title', 'No Title')}")
                    st.markdown(f"**Publisher:** {n.get('publisher', 'Unknown')}")
                    st.markdown(f"**Link:** [{n.get('link', '#')}]({n.get('link', '#')})")
                    st.markdown("---")
        else:
            st.info("Brak dostępnych newsów dla tego symbolu.")
    except Exception as e:
        st.warning(f"Nie udało się pobrać newsów: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    <p>🚀 <strong>ALPHA TERMINAL</strong> - Professional Trading Intelligence</p>
    <p>Powered by Bloomberg Engine • Real-time Data via Yahoo Finance</p>
    </div>
    """, 
    unsafe_allow_html=True
)
