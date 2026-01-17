#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
7-Day Bot Simulator
Pełna symulacja bota z real-time dashboardem i wykresami
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotSimulator7Days:
    """
    Symulator bota na 7 dni
    - Real-like OHLCV data
    - Trading cycle dla każdego candle
    - Tracking all trades, entries, exits
    - Performance metrics
    """
    
    def __init__(
        self,
        account_size: float = 5000,
        leverage: int = 100,
        risk_per_trade: float = 250
    ):
        self.account_size = account_size
        self.leverage = leverage
        self.risk_per_trade = risk_per_trade
        self.current_equity = account_size
        
        # Trading history
        self.trades = []
        self.equity_curve = []
        self.signals = []
        self.positions = []
        
        logger.info("🤖 Bot Simulator 7-Days initialized")
        logger.info(f"   Account: ${account_size:,.0f}")
        logger.info(f"   Leverage: {leverage}x")
        logger.info(f"   Risk/Trade: ${risk_per_trade:,.0f}")
    
    def generate_realistic_data(self, days: int = 7) -> pd.DataFrame:
        """
        Generuj realistyczne OHLCV data na 7 dni
        - 4H candles (42 candles = 7 dni)
        - Realistic volatility
        - Trends, pullbacks, momentum
        """
        periods = days * 6  # 6 candles per day (4H)
        start_price = 50000
        
        # Generate price with trend + volatility + momentum
        np.random.seed(42)
        
        # Trend: uptrend przez pierwsze 2 dni, pullback, recovery
        first_part = int(periods * 0.28)  # 12 candles
        second_part = int(periods * 0.28)  # 12 candles
        third_part = periods - first_part - second_part  # remaining
        
        trend = np.concatenate([
            np.linspace(0, 0.08, first_part),      # +8% first 2 days
            np.linspace(0.08, 0.01, second_part),  # -7% pullback
            np.linspace(0.01, 0.15, third_part)    # +14% recovery
        ])
        
        # Volatility: higher during NY session (must match period length)
        volatility = 0.015 + np.random.randn(periods) * 0.005
        
        # Price path
        returns = trend + volatility
        prices = start_price * (1 + returns).cumprod()
        
        # Generate OHLCV
        data = []
        start_time = datetime.now() - timedelta(days=7)
        
        for i, close_price in enumerate(prices):
            candle_open = prices[i-1] if i > 0 else start_price
            
            # Realistic OHLC
            high = close_price * 1.003 + np.abs(np.random.randn()) * 50
            low = close_price * 0.997 - np.abs(np.random.randn()) * 50
            
            # Ensure OHLC validity
            high = max(high, close_price, candle_open)
            low = min(low, close_price, candle_open)
            
            volume = np.random.uniform(500, 2000)
            
            data.append({
                'time': start_time + timedelta(hours=4*i),
                'open': candle_open,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('time', inplace=True)
        
        logger.info(f"✅ Generated {len(df)} candles (7 days)")
        logger.info(f"   Price range: ${df['low'].min():,.0f} - ${df['high'].max():,.0f}")
        
        return df
    
    def simulate_trading_cycle(self, df: pd.DataFrame) -> Dict:
        """
        Symuluj pełny cykl tradingowy dla każdego candle
        """
        logger.info("\n" + "="*70)
        logger.info("🤖 STARTING 7-DAY TRADING SIMULATION")
        logger.info("="*70)
        
        # Import bot modules
        from trading_bot.complete_bot import CompleteTradingBot
        from trading_bot.indicators.technical import TechnicalIndicators
        from trading_bot.strategies.smt_killzones import SMTAnalyzer, KillzonesManager
        
        bot = CompleteTradingBot(
            symbol='BTCUSDT',
            account_size=self.account_size,
            leverage=self.leverage,
            risk_per_trade=self.risk_per_trade
        )
        
        tech = TechnicalIndicators()
        
        # Calculate indicators on full dataset first
        df_with_indicators = tech.calculate_all(df)
        
        # Simulated BTC/ETH for SMT
        btc_df = df_with_indicators.copy()
        eth_prices = df_with_indicators['close'] * 0.06
        eth_df = pd.DataFrame({'close': eth_prices}, index=df.index)
        
        # Trading loop
        for i in range(50, len(df)):  # Start after 50 candles (indicators need history)
            current_time = df.index[i]
            current_data = df_with_indicators.iloc[:i+1]
            
            try:
                # Run trading cycle
                result = bot.run_trading_cycle({
                    'main': current_data,
                    'btc': btc_df.iloc[:i+1],
                    'eth': eth_df.iloc[:i+1]
                })
                
                # Extract signal
                signal = result.get('signal', {})
                
                if signal.get('signal'):
                    final_signal = signal['signal']
                    current_price = df.iloc[i]['close']
                    
                    # Record signal
                    sig_data = {
                        'time': current_time,
                        'type': final_signal.direction,
                        'price': current_price,
                        'confidence': final_signal.confidence,
                        'entry': final_signal.entry_price,
                        'tp': final_signal.take_profit,
                        'sl': final_signal.stop_loss,
                        'rr': final_signal.risk_reward
                    }
                    
                    self.signals.append(sig_data)
                    
                    # Simulate trade execution
                    self._execute_trade_simulation(sig_data, df, i)
                
                # Track equity
                self.equity_curve.append({
                    'time': current_time,
                    'equity': self.current_equity,
                    'price': current_price
                })
                
            except Exception as e:
                logger.error(f"Error in cycle at {current_time}: {e}")
                continue
        
        return self._calculate_results()
    
    def _execute_trade_simulation(self, signal: Dict, df: pd.DataFrame, start_idx: int):
        """
        Symuluj wykonanie trade - szukaj TP/SL w przyszłości
        """
        entry_price = signal['entry']
        tp = signal['tp']
        sl = signal['sl']
        trade_side = signal['type']
        
        # Track trade through next candles
        for j in range(start_idx + 1, min(start_idx + 100, len(df))):  # Max 100 candles (17 godzin)
            candle = df.iloc[j]
            candle_high = candle['high']
            candle_low = candle['low']
            candle_close = candle['close']
            
            # Check TP/SL hit
            exit_price = None
            exit_reason = None
            
            if trade_side == 'bullish':
                if candle_high >= tp:
                    exit_price = tp
                    exit_reason = 'take_profit'
                elif candle_low <= sl:
                    exit_price = sl
                    exit_reason = 'stop_loss'
            else:  # bearish
                if candle_low <= tp:
                    exit_price = tp
                    exit_reason = 'take_profit'
                elif candle_high >= sl:
                    exit_price = sl
                    exit_reason = 'stop_loss'
            
            # If closed, record trade
            if exit_price:
                pnl = (exit_price - entry_price) if trade_side == 'bullish' else (entry_price - exit_price)
                pnl_pct = (pnl / entry_price) * 100 * self.leverage
                
                # Apply to account
                self.current_equity += pnl * (self.risk_per_trade / entry_price)
                
                trade = {
                    'entry_time': signal['time'],
                    'exit_time': df.index[j],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'side': trade_side,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'reason': exit_reason,
                    'tp': tp,
                    'sl': sl
                }
                
                self.trades.append(trade)
                break
    
    def _calculate_results(self) -> Dict:
        """
        Oblicz wyniki symulacji
        """
        if not self.trades:
            return {'total_trades': 0}
        
        trades = self.trades
        winning = [t for t in trades if t['pnl'] > 0]
        losing = [t for t in trades if t['pnl'] < 0]
        
        total_pnl = sum(t['pnl'] for t in trades)
        total_pnl_pct = (total_pnl / self.account_size) * 100
        
        win_rate = (len(winning) / len(trades) * 100) if trades else 0
        
        returns = [t['pnl_pct'] for t in trades]
        sharpe = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        max_drawdown = 0
        peak = self.account_size
        for eq in self.equity_curve:
            peak = max(peak, eq['equity'])
            dd = (eq['equity'] - peak) / peak
            max_drawdown = min(max_drawdown, dd)
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'max_drawdown': max_drawdown * 100,
            'sharpe_ratio': sharpe,
            'final_equity': self.current_equity,
            'largest_win': max([t['pnl'] for t in winning]) if winning else 0,
            'largest_loss': min([t['pnl'] for t in losing]) if losing else 0,
            'avg_trade_pnl': np.mean([t['pnl'] for t in trades]) if trades else 0
        }


def run_7day_simulation():
    """
    Uruchom pełną 7-dniową symulację
    """
    print("\n" + "="*70)
    print("🤖 FULL 7-DAY BOT SIMULATION")
    print("="*70)
    
    sim = BotSimulator7Days(
        account_size=5000,
        leverage=100,
        risk_per_trade=250
    )
    
    # Generate realistic data
    df = sim.generate_realistic_data(days=7)
    
    # Run simulation
    results = sim.simulate_trading_cycle(df)
    
    # Print results
    print("\n" + "="*70)
    print("📊 7-DAY SIMULATION RESULTS")
    print("="*70)
    
    print(f"\n💰 Account:")
    print(f"   Starting: ${sim.account_size:,.0f}")
    print(f"   Ending: ${results['final_equity']:,.0f}")
    print(f"   P&L: ${results['total_pnl']:+,.0f} ({results['total_pnl_pct']:+.2f}%)")
    
    print(f"\n📊 Trades:")
    print(f"   Total: {results['total_trades']}")
    print(f"   Winning: {results['winning_trades']} ({results['win_rate']:.1f}%)")
    print(f"   Losing: {results['losing_trades']}")
    
    print(f"\n📈 Performance:")
    print(f"   Largest Win: ${results['largest_win']:+,.0f}")
    print(f"   Largest Loss: ${results['largest_loss']:+,.0f}")
    print(f"   Avg Trade: ${results['avg_trade_pnl']:+,.0f}")
    print(f"   Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"   Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    
    print("\n" + "="*70)
    
    # Return data for plotting
    return {
        'simulator': sim,
        'data': df,
        'results': results
    }


if __name__ == "__main__":
    run_7day_simulation()
