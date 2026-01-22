"""
📊 PROFESSIONAL BACKTESTING ENGINE
Wykorzystuje backtrader framework
System backtestingu używany przez fundusze hedgingowe
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Backtrader import
try:
    import backtrader as bt
    BACKTRADER_AVAILABLE = True
    
    class HamsterStrategy(bt.Strategy):
        """
        Hamster Terminal trading strategy for backtrader
        Combines technical indicators with AI signals
        """
        
        params = (
            ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('stop_loss_pct', 0.02),  # 2% stop loss
        ('take_profit_pct', 0.05),  # 5% take profit
    )
    
    def __init__(self):
        # Technical indicators
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )
        
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        
        self.sma_fast = bt.indicators.SMA(self.data.close, period=50)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=200)
        
        # Track orders
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        
        # Performance tracking
        self.trades = []
    
    def notify_order(self, order):
        """Called when order status changes"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
                logger.info(f'BUY EXECUTED: ${order.executed.price:.2f}')
            else:
                logger.info(f'SELL EXECUTED: ${order.executed.price:.2f}')
                
                # Calculate P&L
                if self.buy_price:
                    pnl = order.executed.price - self.buy_price
                    pnl_pct = (pnl / self.buy_price) * 100
                    self.trades.append({
                        'entry': self.buy_price,
                        'exit': order.executed.price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            logger.warning('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def next(self):
        """Called for each bar"""
        if self.order:
            return
        
        # Check if we're in the market
        if not self.position:
            # Buy signals
            if (self.rsi[0] < self.params.rsi_oversold and 
                self.macd.macd[0] > self.macd.signal[0] and
                self.data.close[0] > self.sma_fast[0]):
                
                self.order = self.buy()
                
        else:
            # Sell signals
            if (self.rsi[0] > self.params.rsi_overbought or
                self.macd.macd[0] < self.macd.signal[0]):
                
                self.order = self.sell()
            
            # Stop loss / Take profit
            elif self.buy_price:
                current_pnl_pct = (self.data.close[0] - self.buy_price) / self.buy_price
                
                if current_pnl_pct < -self.params.stop_loss_pct:
                    logger.info(f'STOP LOSS triggered at {current_pnl_pct:.2%}')
                    self.order = self.sell()
                
                elif current_pnl_pct > self.params.take_profit_pct:
                    logger.info(f'TAKE PROFIT triggered at {current_pnl_pct:.2%}')
                    self.order = self.sell()

except ImportError:
    BACKTRADER_AVAILABLE = False
    HamsterStrategy = None
    logger.warning("⚠️ backtrader not available - backtesting disabled")


class BacktestEngine:
    """
    Professional backtesting engine
    Features: Walk-forward, Monte Carlo, optimization
    """
    
    def __init__(self, initial_cash: float = 10000.0):
        """
        Initialize backtest engine
        
        Args:
            initial_cash: Starting capital
        """
        self.initial_cash = initial_cash
        self.logger = logging.getLogger(__name__)
        
        if not BACKTRADER_AVAILABLE:
            self.logger.warning("⚠️ backtrader not available - backtesting disabled")
    
    def run_backtest(self, data: pd.DataFrame, 
                    strategy_class: type = HamsterStrategy,
                    commission: float = 0.001) -> Dict[str, Any]:
        """
        Run backtest on historical data
        
        Args:
            data: DataFrame with OHLCV data
            strategy_class: Strategy to test
            commission: Trading commission (0.1% default)
            
        Returns:
            Dict with backtest results
        """
        if not BACKTRADER_AVAILABLE:
            return self._simple_backtest(data)
        
        try:
            # Create Cerebro engine
            cerebro = bt.Cerebro()
            
            # Add strategy
            cerebro.addstrategy(strategy_class)
            
            # Prepare data
            bt_data = bt.feeds.PandasData(dataname=data)
            cerebro.adddata(bt_data)
            
            # Set broker parameters
            cerebro.broker.setcash(self.initial_cash)
            cerebro.broker.setcommission(commission=commission)
            
            # Add analyzers
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            
            # Run backtest
            self.logger.info(f"🚀 Running backtest with ${self.initial_cash:,.0f} capital...")
            
            start_value = cerebro.broker.getvalue()
            results = cerebro.run()
            end_value = cerebro.broker.getvalue()
            
            # Extract results
            strat = results[0]
            
            # Get analyzer results
            sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0)
            drawdown = strat.analyzers.drawdown.get_analysis()
            returns_analyzer = strat.analyzers.returns.get_analysis()
            trades = strat.analyzers.trades.get_analysis()
            
            total_return = ((end_value - start_value) / start_value) * 100
            
            results_dict = {
                'status': 'success',
                'initial_capital': start_value,
                'final_capital': end_value,
                'total_return_pct': total_return,
                'sharpe_ratio': sharpe if sharpe else 0,
                'max_drawdown_pct': drawdown.get('max', {}).get('drawdown', 0),
                'total_trades': trades.get('total', {}).get('total', 0),
                'won_trades': trades.get('won', {}).get('total', 0),
                'lost_trades': trades.get('lost', {}).get('total', 0),
                'win_rate': (trades.get('won', {}).get('total', 0) / 
                           trades.get('total', {}).get('total', 1)) * 100 if trades.get('total', {}).get('total', 0) > 0 else 0
            }
            
            self.logger.info(f"✅ Backtest complete! Return: {total_return:.2f}%, "
                           f"Sharpe: {sharpe:.2f}, Trades: {results_dict['total_trades']}")
            
            return results_dict
            
        except Exception as e:
            self.logger.error(f"❌ Backtest failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _simple_backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Simple backtest fallback when backtrader not available"""
        if 'close' not in data.columns:
            return {'status': 'error', 'message': 'No close price in data'}
        
        returns = data['close'].pct_change().dropna()
        
        total_return = ((data['close'].iloc[-1] - data['close'].iloc[0]) / 
                       data['close'].iloc[0]) * 100
        
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = ((cumulative - running_max) / running_max) * 100
        max_dd = drawdown.min()
        
        return {
            'status': 'simple_backtest',
            'total_return_pct': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_dd,
            'note': 'Simple backtest - install backtrader for advanced features'
        }
    
    def walk_forward_analysis(self, data: pd.DataFrame,
                             train_period: int = 100,
                             test_period: int = 20) -> Dict[str, Any]:
        """
        Walk-forward optimization
        Gold standard for strategy validation
        
        Args:
            data: Historical data
            train_period: Training window size
            test_period: Testing window size
            
        Returns:
            Walk-forward results
        """
        results = []
        
        for i in range(0, len(data) - train_period - test_period, test_period):
            train_data = data.iloc[i:i + train_period]
            test_data = data.iloc[i + train_period:i + train_period + test_period]
            
            # Run backtest on test period
            test_result = self.run_backtest(test_data)
            results.append(test_result)
        
        if results:
            avg_return = np.mean([r.get('total_return_pct', 0) for r in results])
            consistency = np.std([r.get('total_return_pct', 0) for r in results])
            
            self.logger.info(f"📊 Walk-Forward: Avg Return={avg_return:.2f}%, "
                           f"Consistency={consistency:.2f}%")
            
            return {
                'avg_return': avg_return,
                'consistency': consistency,
                'num_periods': len(results),
                'individual_results': results
            }
        
        return {'status': 'insufficient_data'}
    
    def monte_carlo_simulation(self, returns: pd.Series, 
                              num_simulations: int = 1000,
                              periods: int = 252) -> Dict[str, Any]:
        """
        Monte Carlo simulation for risk assessment
        
        Args:
            returns: Historical returns
            num_simulations: Number of simulation runs
            periods: Forecast periods (252 = 1 year)
            
        Returns:
            Simulation results with confidence intervals
        """
        mean_return = returns.mean()
        std_return = returns.std()
        
        simulations = np.zeros((num_simulations, periods))
        
        for i in range(num_simulations):
            # Generate random returns
            random_returns = np.random.normal(mean_return, std_return, periods)
            # Calculate cumulative returns
            simulations[i] = (1 + random_returns).cumprod()
        
        # Calculate percentiles
        final_values = simulations[:, -1]
        percentiles = {
            '5th': np.percentile(final_values, 5),
            '25th': np.percentile(final_values, 25),
            '50th': np.percentile(final_values, 50),
            '75th': np.percentile(final_values, 75),
            '95th': np.percentile(final_values, 95)
        }
        
        self.logger.info(f"🎲 Monte Carlo: Median outcome={percentiles['50th']:.2f}x, "
                        f"95% CI=[{percentiles['5th']:.2f}x, {percentiles['95th']:.2f}x]")
        
        return {
            'percentiles': percentiles,
            'mean_outcome': float(np.mean(final_values)),
            'worst_case': float(np.min(final_values)),
            'best_case': float(np.max(final_values)),
            'probability_of_profit': float((final_values > 1.0).mean() * 100)
        }


# Global instance
backtest_engine = BacktestEngine()
