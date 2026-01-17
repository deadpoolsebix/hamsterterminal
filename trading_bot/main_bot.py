#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🤖 TRADING BOT - Główny System
ICT + Smart Money + ML + Risk Management

Funkcje:
- Multi-timeframe analysis (1m to 1M)
- Liquidity grab detection
- FVG, Order Blocks, EQH/EQL
- Bull/Bear trap detection
- Wyckoff phase detection
- Open Range Breakout
- Leverage 100x risk management
- Pyramiding strategy
- Real-time monitoring
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Import własnych modułów
sys.path.append(os.path.dirname(__file__))
from indicators.technical import TechnicalIndicators, ICTIndicators, VolumeIndicators
from strategies.main_strategy import TradingStrategy, Signal
from risk_management.risk_manager import RiskManager, ScalpingManager


class TradingBot:
    """
    Główny Bot Tradingowy
    """
    
    def __init__(self, account_balance: float = 5000, 
                 leverage: int = 100,
                 symbol: str = 'BTCUSDT'):
        
        self.account_balance = account_balance
        self.leverage = leverage
        self.symbol = symbol
        
        # Initialize modules
        self.tech_indicators = TechnicalIndicators()
        self.ict_indicators = ICTIndicators()
        self.volume_indicators = VolumeIndicators()
        self.strategy = TradingStrategy()
        self.risk_manager = RiskManager(account_balance, leverage)
        self.scalp_manager = ScalpingManager()
        
        # State
        self.is_running = False
        self.current_position = None
        self.trade_history = []
        
        print("=" * 60)
        print("🤖 TRADING BOT INITIALIZED")
        print("=" * 60)
        print(f"💰 Account Balance: ${account_balance:,.2f}")
        print(f"⚡ Max Leverage: {leverage}x")
        print(f"📊 Symbol: {symbol}")
        print("=" * 60)
    
    def analyze_market(self, df: pd.DataFrame, timeframe: str = '1h') -> dict:
        """
        Kompleksowa analiza rynku
        Wszystkie wskaźniki i sygnały
        """
        print(f"\n📊 ANALIZA RYNKU - {timeframe}")
        print("-" * 60)
        
        # 1. Wskaźniki techniczne
        print("[1] Wskaźniki techniczne...")
        rsi = self.tech_indicators.rsi(df['close'])
        momentum = self.tech_indicators.momentum(df['close'])
        sma_20 = self.tech_indicators.sma(df['close'], 20)
        sma_50 = self.tech_indicators.sma(df['close'], 50)
        sma_200 = self.tech_indicators.sma(df['close'], 200)
        atr = self.tech_indicators.atr(df['high'], df['low'], df['close'])
        macd, macd_signal, macd_hist = self.tech_indicators.macd(df['close'])
        
        print(f"  RSI: {rsi.iloc[-1]:.2f}")
        print(f"  Momentum: {momentum.iloc[-1]:.2f}")
        print(f"  SMA 20/50/200: {sma_20.iloc[-1]:.2f} / {sma_50.iloc[-1]:.2f} / {sma_200.iloc[-1]:.2f}")
        print(f"  ATR: {atr.iloc[-1]:.2f}")
        
        # 2. ICT Indicators
        print("\n[2] ICT Analysis...")
        fvg = self.ict_indicators.fair_value_gap(df['high'], df['low'], df['close'])
        print(f"  Fair Value Gaps: {len(fvg)} znaleziono")
        
        order_blocks = self.ict_indicators.order_blocks(
            df['high'], df['low'], df['close'], df['volume']
        )
        print(f"  Order Blocks: {len(order_blocks)} znaleziono")
        
        liquidity = self.ict_indicators.liquidity_levels(df['high'], df['low'])
        print(f"  Equal Highs: {len(liquidity['equal_highs'])}")
        print(f"  Equal Lows: {len(liquidity['equal_lows'])}")
        
        market_structure = self.ict_indicators.market_structure(
            df['high'], df['low'], df['close']
        )
        print(f"  Market Structure: {market_structure.iloc[-1]}")
        
        # 3. Volume Analysis
        print("\n[3] Volume Analysis...")
        cvd = self.volume_indicators.cvd(df['volume'], df['close'])
        obv = self.volume_indicators.on_balance_volume(df['close'], df['volume'])
        
        print(f"  CVD: {cvd.iloc[-1]:.2f}")
        print(f"  OBV: {obv.iloc[-1]:.2f}")
        print(f"  Volume 24h: High={df['volume'].max():.0f}, Low={df['volume'].min():.0f}")
        
        # 4. Strategy Signals
        print("\n[4] Strategy Signals...")
        
        # Liquidity Grab
        liq_grab = self.strategy.detect_liquidity_grab(df, liquidity)
        if liq_grab['count'] > 0:
            print(f"  🎯 Liquidity Grab: {liq_grab['count']} sygnałów")
            for sig in liq_grab['signals']:
                print(f"     - {sig['type']} na ${sig['level']:.2f}")
        
        # FVG Strategy
        fvg_signals = self.strategy.detect_fvg_strategy(df, fvg)
        if fvg_signals:
            print(f"  📍 FVG Signals: {len(fvg_signals)}")
        
        # Bull/Bear Trap
        trap = self.strategy.detect_bull_bear_trap(df)
        if trap.get('trap'):
            print(f"  🪤 {trap['trap']} detected! Confidence: {trap['confidence']}%")
        
        # Wyckoff Phase
        wyckoff = self.strategy.wyckoff_phase_detection(df)
        print(f"  📈 Wyckoff Phase: {wyckoff}")
        
        # Open Range Breakout
        orb = self.strategy.open_range_breakout(df)
        if orb.get('signal'):
            print(f"  🚀 ORB Signal: {orb['signal']} - {orb['reason']}")
        
        # Session Sentiment
        sentiment = self.strategy.calculate_session_sentiment(df)
        print(f"\n[5] Sentyment Sesji:")
        print(f"  {sentiment['komentarz']}")
        
        # Aggregate all indicators
        all_indicators = {
            'rsi': rsi,
            'momentum': momentum,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'sma_200': sma_200,
            'atr': atr,
            'macd': macd,
            'fvg': fvg,
            'order_blocks': order_blocks,
            'liquidity': liquidity,
            'market_structure': market_structure,
            'cvd': cvd,
            'obv': obv,
            'liquidity_grab': liq_grab,
            'fvg_signals': fvg_signals,
            'trap': trap,
            'wyckoff': wyckoff,
            'orb': orb,
            'sentiment': sentiment
        }
        
        return all_indicators
    
    def generate_trading_signal(self, df: pd.DataFrame, 
                               indicators: dict) -> dict:
        """
        Generuj sygnał tradingowy
        """
        print("\n🎯 GENEROWANIE SYGNAŁU...")
        print("-" * 60)
        
        # Użyj strategii do agregacji
        signal = self.strategy.generate_final_signal(
            df, 
            indicators, 
            {'risk_percent': 5}
        )
        
        print(f"Signal: {signal.signal.value}")
        print(f"Confidence: {signal.confidence:.1f}%")
        print(f"Entry: ${signal.entry_price:.2f}")
        if signal.stop_loss:
            print(f"Stop Loss: ${signal.stop_loss:.2f}")
        if signal.take_profit:
            print(f"Take Profit: ${signal.take_profit:.2f}")
        
        print("\nPowody:")
        for i, reason in enumerate(signal.reasons, 1):
            print(f"  {i}. {reason}")
        
        return {
            'signal': signal.signal,
            'confidence': signal.confidence,
            'entry': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'reasons': signal.reasons
        }
    
    def calculate_position(self, signal: dict) -> dict:
        """
        Oblicz wielkość pozycji z risk management
        """
        print("\n💰 RISK MANAGEMENT & POSITION SIZING")
        print("-" * 60)
        
        if signal['signal'] == Signal.NEUTRAL:
            print("⏸️  NEUTRAL signal - Nie otwieraj pozycji")
            return None
        
        # Podstawowa pozycja
        position = self.risk_manager.calculate_position_size(
            entry_price=signal['entry'],
            stop_loss_price=signal['stop_loss'],
            risk_amount=250,  # $250 risk per trade
            leverage=self.leverage
        )
        
        print(f"Margin: ${position['margin']:.2f}")
        print(f"Leverage: {position['leverage']}x")
        print(f"Position Value: ${position['position_value']:.2f}")
        print(f"Quantity: {position['quantity']:.6f} BTC")
        print(f"Liquidation Price: ${position['liquidation_price']:.2f}")
        print(f"Risk:Reward: 1:{position['risk_reward_ratio']:.2f}")
        
        print("\nProfit Scenarios:")
        for scenario, profit in position['profit_scenarios'].items():
            print(f"  {scenario}: ${profit:.2f}")
        
        # Pyramiding strategy
        if signal['confidence'] > 80:
            print("\n📊 PYRAMIDING STRATEGY (High Confidence)")
            pyramids = self.risk_manager.pyramiding_strategy(
                base_entry=signal['entry'],
                num_entries=5,
                total_risk=250,
                leverage=self.leverage
            )
            
            for pyr in pyramids:
                print(f"  Entry {pyr['entry']}: ${pyr['margin']:.2f} @ ${pyr['entry_price']:.2f}")
        
        return position
    
    def run_backtest(self, df: pd.DataFrame):
        """
        Backtesting na danych historycznych
        """
        print("\n🔄 BACKTESTING...")
        print("=" * 60)
        
        # Tutaj implementacja backtestingu
        # Symulacja tradingu na historycznych danych
        
        wins = 0
        losses = 0
        total_profit = 0
        
        # ... logika backtestingu
        
        print(f"\nWyniki Backtestingu:")
        print(f"  Winning trades: {wins}")
        print(f"  Losing trades: {losses}")
        print(f"  Win rate: {(wins/(wins+losses)*100):.1f}%")
        print(f"  Total P&L: ${total_profit:.2f}")
    
    def print_status(self):
        """Wyświetl status bota"""
        status = self.risk_manager.get_portfolio_status()
        
        print("\n" + "=" * 60)
        print("📊 STATUS PORTFELA")
        print("=" * 60)
        print(f"Total Balance: ${status['total_balance']:,.2f}")
        print(f"Available: ${status['available_balance']:,.2f}")
        print(f"Margin Used: ${status['margin_used']:,.2f} ({status['margin_used_percent']:.1f}%)")
        print(f"Open Positions: {status['num_positions']}")
        print("=" * 60)


def main():
    """Główna funkcja - Demo"""
    
    # Inicjalizacja bota
    bot = TradingBot(
        account_balance=5000,
        leverage=100,
        symbol='BTCUSDT'
    )
    
    # Generuj przykładowe dane
    print("\n📥 Ładowanie danych...")
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=1000, freq='1H')
    
    # Symulacja cen BTC
    returns = np.random.normal(0.0001, 0.02, 1000)
    prices = 100000 * np.exp(np.cumsum(returns))  # Start at $100k
    
    df = pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, 1000)),
        'high': prices * (1 + np.abs(np.random.uniform(0, 0.02, 1000))),
        'low': prices * (1 - np.abs(np.random.uniform(0, 0.02, 1000))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 1000)
    }, index=dates)
    
    print(f"✓ Załadowano {len(df)} świec")
    print(f"  Price range: ${df['close'].min():,.2f} - ${df['close'].max():,.2f}")
    
    # Analiza rynku
    indicators = bot.analyze_market(df.tail(200), timeframe='1h')
    
    # Generuj sygnał
    signal = bot.generate_trading_signal(df.tail(200), indicators)
    
    # Oblicz pozycję
    if signal['signal'] != Signal.NEUTRAL:
        position = bot.calculate_position(signal)
    
    # Status
    bot.print_status()
    
    print("\n✅ BOT GOTOWY DO DZIAŁANIA!")
    print("=" * 60)


if __name__ == "__main__":
    main()
