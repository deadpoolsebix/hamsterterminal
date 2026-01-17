#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Advanced Backtesting Engine
Test bota podczas crashów, krachu 2024, extreme volatility
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Single backtest trade"""
    entry_time: datetime
    entry_price: float
    exit_time: datetime = None
    exit_price: float = 0.0
    side: str = 'long'  # 'long' or 'short'
    position_size_usd: float = 0.0
    leverage: int = 100
    stop_loss: float = 0.0
    take_profit: float = 0.0
    liquidation_price: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    exit_reason: str = ''  # 'tp', 'sl', 'liquidated', 'emergency', 'timeout'
    was_liquidated: bool = False
    max_drawdown_reached: float = 0.0


@dataclass
class BacktestResult:
    """Backtest results"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    liquidated_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    avg_trade_duration: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    survival_rate: float = 0.0  # % trades that didn't get liquidated


class AdvancedBacktest:
    """
    Zaawansowany backtesting engine
    
    Features:
    - Testowanie podczas crashów (Black Swan events)
    - Symulacja liquidacji przy 100x leverage
    - Testowanie 20% safety buffer
    - Slippage simulation
    - Emergency exit testing
    - Drawdown analysis
    """
    
    def __init__(
        self,
        initial_capital: float = 5000,
        leverage: int = 100,
        safety_buffer_percent: float = 20,
        max_position_duration_hours: float = 24,
        max_drawdown_percent: float = 50
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.leverage = leverage
        self.safety_buffer = safety_buffer_percent / 100
        self.max_position_duration = timedelta(hours=max_position_duration_hours)
        self.max_drawdown_limit = max_drawdown_percent / 100
        
        self.trades: List[BacktestTrade] = []
        self.equity_curve = []
        self.peak_capital = initial_capital
        
    def calculate_liquidation_price(
        self,
        entry_price: float,
        side: str,
        position_size_usd: float
    ) -> float:
        """
        Oblicz cenę likwidacji
        
        Z safety buffer 20%:
        - Margin = Position Size / Leverage
        - Usable Margin = Margin * (1 - safety_buffer)
        - Liquidation Distance = Usable Margin / (Position Size / Entry Price)
        """
        margin = position_size_usd / self.leverage
        usable_margin = margin * (1 - self.safety_buffer)
        quantity = position_size_usd / entry_price
        liquidation_distance = usable_margin / quantity
        
        if side == 'long':
            liq_price = entry_price - liquidation_distance
        else:  # short
            liq_price = entry_price + liquidation_distance
        
        return liq_price
    
    def simulate_trade(
        self,
        data: pd.DataFrame,
        entry_idx: int,
        side: str,
        stop_loss_pct: float,
        take_profit_pct: float,
        position_size_pct: float = 5.0
    ) -> BacktestTrade:
        """
        Symuluj pojedynczy trade
        
        Parameters:
        - data: OHLCV DataFrame
        - entry_idx: Index wejścia
        - side: 'long' or 'short'
        - stop_loss_pct: % stop loss
        - take_profit_pct: % take profit
        - position_size_pct: % kapitału na trade
        """
        entry_row = data.iloc[entry_idx]
        entry_price = entry_row['close']
        entry_time = entry_row.name
        
        # Position size
        position_size_usd = self.current_capital * (position_size_pct / 100)
        
        # Calculate levels
        if side == 'long':
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
            take_profit = entry_price * (1 + take_profit_pct / 100)
        else:  # short
            stop_loss = entry_price * (1 + stop_loss_pct / 100)
            take_profit = entry_price * (1 - take_profit_pct / 100)
        
        liquidation_price = self.calculate_liquidation_price(
            entry_price, side, position_size_usd
        )
        
        trade = BacktestTrade(
            entry_time=entry_time,
            entry_price=entry_price,
            side=side,
            position_size_usd=position_size_usd,
            leverage=self.leverage,
            stop_loss=stop_loss,
            take_profit=take_profit,
            liquidation_price=liquidation_price
        )
        
        # Simulate forward
        max_drawdown = 0
        
        for i in range(entry_idx + 1, len(data)):
            current_row = data.iloc[i]
            current_time = current_row.name
            high = current_row['high']
            low = current_row['low']
            close = current_row['close']
            
            # Check liquidation FIRST (most critical)
            if side == 'long' and low <= liquidation_price:
                trade.exit_price = liquidation_price
                trade.exit_time = current_time
                trade.exit_reason = 'liquidated'
                trade.was_liquidated = True
                trade.pnl = -position_size_usd / self.leverage  # Lose all margin
                break
            
            elif side == 'short' and high >= liquidation_price:
                trade.exit_price = liquidation_price
                trade.exit_time = current_time
                trade.exit_reason = 'liquidated'
                trade.was_liquidated = True
                trade.pnl = -position_size_usd / self.leverage
                break
            
            # Check stop loss
            if side == 'long' and low <= stop_loss:
                trade.exit_price = stop_loss
                trade.exit_time = current_time
                trade.exit_reason = 'stop_loss'
                break
            
            elif side == 'short' and high >= stop_loss:
                trade.exit_price = stop_loss
                trade.exit_time = current_time
                trade.exit_reason = 'stop_loss'
                break
            
            # Check take profit
            if side == 'long' and high >= take_profit:
                trade.exit_price = take_profit
                trade.exit_time = current_time
                trade.exit_reason = 'take_profit'
                break
            
            elif side == 'short' and low <= take_profit:
                trade.exit_price = take_profit
                trade.exit_time = current_time
                trade.exit_reason = 'take_profit'
                break
            
            # Track max drawdown
            if side == 'long':
                unrealized_pnl_pct = ((close - entry_price) / entry_price) * self.leverage
            else:
                unrealized_pnl_pct = ((entry_price - close) / entry_price) * self.leverage
            
            max_drawdown = min(max_drawdown, unrealized_pnl_pct)
            
            # Emergency exit on max drawdown
            if abs(max_drawdown) > self.max_drawdown_limit * 100:
                trade.exit_price = close
                trade.exit_time = current_time
                trade.exit_reason = 'emergency_drawdown'
                break
            
            # Timeout
            if current_time - entry_time > self.max_position_duration:
                trade.exit_price = close
                trade.exit_time = current_time
                trade.exit_reason = 'timeout'
                break
        
        # Calculate final PnL
        if trade.exit_price > 0:
            if side == 'long':
                price_change_pct = (trade.exit_price - entry_price) / entry_price
            else:
                price_change_pct = (entry_price - trade.exit_price) / entry_price
            
            trade.pnl = position_size_usd * price_change_pct * self.leverage
            trade.pnl_percent = (trade.pnl / position_size_usd) * 100
            trade.max_drawdown_reached = abs(max_drawdown)
            
            # Update capital
            self.current_capital += trade.pnl
            
            # Track equity
            self.equity_curve.append({
                'time': trade.exit_time,
                'equity': self.current_capital,
                'trade_pnl': trade.pnl
            })
            
            # Update peak
            self.peak_capital = max(self.peak_capital, self.current_capital)
        
        return trade
    
    def run_crash_test(
        self,
        crash_data: pd.DataFrame,
        crash_name: str = "Unknown Crash"
    ) -> BacktestResult:
        """
        Test podczas crash event
        
        Crash data powinien zawierać:
        - Extreme volatility
        - Rapid price drops
        - Liquidation cascades
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔥 CRASH TEST: {crash_name}")
        logger.info(f"{'='*60}")
        
        self.trades = []
        self.equity_curve = []
        self.current_capital = self.initial_capital
        self.peak_capital = self.initial_capital
        
        # Simulate trades during crash
        # Strategy: Enter on -5% drops with tight stops
        for i in range(100, len(crash_data) - 50):
            row = crash_data.iloc[i]
            
            # Simple strategy: buy dips
            if i > 0:
                prev_close = crash_data.iloc[i-1]['close']
                current_close = row['close']
                drop_pct = ((current_close - prev_close) / prev_close) * 100
                
                # Enter on -5% drop
                if drop_pct < -5:
                    trade = self.simulate_trade(
                        crash_data,
                        entry_idx=i,
                        side='long',
                        stop_loss_pct=2,  # Tight 2% stop
                        take_profit_pct=6,  # 1:3 R:R
                        position_size_pct=5
                    )
                    self.trades.append(trade)
                    
                    # Stop if capital depleted
                    if self.current_capital < self.initial_capital * 0.3:
                        logger.warning("⚠️ Capital critically low. Stopping backtest.")
                        break
        
        # Calculate results
        result = self._calculate_results()
        self._print_crash_results(result, crash_name)
        
        return result
    
    def _calculate_results(self) -> BacktestResult:
        """Oblicz wyniki backtestu"""
        if not self.trades:
            return BacktestResult()
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        liquidated = [t for t in self.trades if t.was_liquidated]
        
        total_profit = sum(t.pnl for t in winning_trades)
        total_loss = abs(sum(t.pnl for t in losing_trades))
        
        durations = [
            (t.exit_time - t.entry_time).total_seconds() / 3600
            for t in self.trades if t.exit_time
        ]
        
        # Sharpe ratio
        returns = [t.pnl_percent for t in self.trades]
        sharpe = (np.mean(returns) / np.std(returns)) if np.std(returns) > 0 else 0
        
        # Max drawdown
        max_dd = 0
        if self.equity_curve:
            peak = self.initial_capital
            for point in self.equity_curve:
                peak = max(peak, point['equity'])
                dd = (point['equity'] - peak) / peak
                max_dd = min(max_dd, dd)
        
        return BacktestResult(
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            liquidated_trades=len(liquidated),
            win_rate=len(winning_trades) / len(self.trades) * 100,
            total_pnl=self.current_capital - self.initial_capital,
            total_pnl_percent=((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
            max_drawdown=max_dd * self.initial_capital,
            max_drawdown_percent=abs(max_dd) * 100,
            sharpe_ratio=sharpe,
            profit_factor=total_profit / total_loss if total_loss > 0 else 0,
            avg_trade_duration=np.mean(durations) if durations else 0,
            largest_win=max([t.pnl for t in self.trades]),
            largest_loss=min([t.pnl for t in self.trades]),
            survival_rate=(len(self.trades) - len(liquidated)) / len(self.trades) * 100
        )
    
    def _print_crash_results(self, result: BacktestResult, crash_name: str):
        """Wydrukuj wyniki crash testu"""
        print(f"\n📊 WYNIKI - {crash_name}")
        print("=" * 60)
        print(f"Capital początkowy:     ${self.initial_capital:,.0f}")
        print(f"Capital końcowy:        ${self.current_capital:,.0f}")
        print(f"P&L:                    ${result.total_pnl:+,.0f} ({result.total_pnl_percent:+.1f}%)")
        print(f"\nTrades:")
        print(f"  Total:                {result.total_trades}")
        print(f"  Winning:              {result.winning_trades} ({result.win_rate:.1f}%)")
        print(f"  Losing:               {result.losing_trades}")
        print(f"  ⚠️ LIQUIDATED:         {result.liquidated_trades}")
        print(f"\nRisk Metrics:")
        print(f"  Max Drawdown:         ${result.max_drawdown:,.0f} ({result.max_drawdown_percent:.1f}%)")
        print(f"  Survival Rate:        {result.survival_rate:.1f}%")
        print(f"  Sharpe Ratio:         {result.sharpe_ratio:.2f}")
        print(f"  Profit Factor:        {result.profit_factor:.2f}")
        print(f"\nTrade Stats:")
        print(f"  Largest Win:          ${result.largest_win:+,.0f}")
        print(f"  Largest Loss:         ${result.largest_loss:+,.0f}")
        print(f"  Avg Duration:         {result.avg_trade_duration:.1f}h")
        print("=" * 60)
        
        # Verdict
        if result.liquidated_trades > 0:
            print("🚨 WARNING: Liquidations occurred! 20% buffer insufficient during extreme volatility.")
        
        if result.survival_rate < 90:
            print("⚠️ Low survival rate. Consider reducing leverage or increasing buffer.")
        
        if result.total_pnl > 0:
            print("✅ Strategy profitable during crash.")
        else:
            print("❌ Strategy unprofitable. Avoid trading during crashes.")


def generate_crash_scenario(
    base_price: float = 50000,
    crash_percent: float = -30,
    duration_hours: int = 24,
    volatility_multiplier: float = 3.0
) -> pd.DataFrame:
    """
    Generuj syntetyczny crash scenario
    
    Symuluje:
    - Nagły spadek ceny
    - Zwiększoną zmienność
    - Liquidation cascades
    - Bounce attempts
    """
    periods = duration_hours * 12  # 5-minute candles
    
    # Base trend (crash down)
    trend = np.linspace(0, crash_percent, periods)
    
    # Add extreme volatility
    volatility = np.random.randn(periods) * volatility_multiplier
    
    # Add liquidation cascades (sharp drops)
    cascades = np.zeros(periods)
    cascade_points = np.random.choice(periods, size=5, replace=False)
    cascades[cascade_points] = -5  # -5% instant drops
    
    # Combine
    price_changes = trend + volatility + cascades
    prices = base_price * (1 + price_changes / 100).cumprod()
    
    # Generate OHLCV
    data = []
    start_time = pd.Timestamp('2024-01-01')
    
    for i, close in enumerate(prices):
        # Add realistic OHLC spreads
        candle_range = abs(volatility[i]) * 0.5
        open_price = prices[i-1] if i > 0 else base_price
        high = close * (1 + abs(candle_range) / 100)
        low = close * (1 - abs(candle_range) / 100)
        
        # Adjust for direction
        if close < open_price:
            high = max(high, open_price)
            low = min(low, close)
        else:
            high = max(high, close)
            low = min(low, open_price)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.uniform(100, 1000)
        })
    
    df = pd.DataFrame(data)
    df.index = pd.date_range(start_time, periods=periods, freq='5T')
    
    return df


def demo_crash_tests():
    """Demo: Test podczas różnych crashów"""
    
    print("\n" + "="*60)
    print("🔥 ADVANCED BACKTESTING - CRASH SCENARIOS")
    print("="*60)
    
    bt = AdvancedBacktest(
        initial_capital=5000,
        leverage=100,
        safety_buffer_percent=20,
        max_position_duration_hours=24,
        max_drawdown_percent=50
    )
    
    # Test 1: Moderate crash (-20%)
    print("\n🧪 Test 1: Moderate Crash (-20%)")
    crash1 = generate_crash_scenario(
        base_price=50000,
        crash_percent=-20,
        duration_hours=12,
        volatility_multiplier=2.0
    )
    result1 = bt.run_crash_test(crash1, "Moderate Crash -20%")
    
    # Reset
    bt.current_capital = 5000
    
    # Test 2: Severe crash (-40%, extreme volatility)
    print("\n🧪 Test 2: Severe Crash (-40%)")
    crash2 = generate_crash_scenario(
        base_price=50000,
        crash_percent=-40,
        duration_hours=24,
        volatility_multiplier=5.0
    )
    result2 = bt.run_crash_test(crash2, "Severe Crash -40%")
    
    # Summary
    print("\n" + "="*60)
    print("📋 CRASH TEST SUMMARY")
    print("="*60)
    print(f"Moderate Crash:  Survival {result1.survival_rate:.0f}% | P&L {result1.total_pnl:+.0f}")
    print(f"Severe Crash:    Survival {result2.survival_rate:.0f}% | P&L {result2.total_pnl:+.0f}")
    print("\n💡 Wnioski:")
    print("- Buffer 20% pomaga, ale nie gwarantuje 100% przetrwania")
    print("- Podczas crashów leverage 100x = extreme risk")
    print("- Emergency exits są KLUCZOWE")
    print("- Rozważ redukcję leverage podczas wysokiej zmienności")
    print("="*60)


if __name__ == "__main__":
    demo_crash_tests()
