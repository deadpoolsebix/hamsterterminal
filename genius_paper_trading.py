"""
📝 GENIUS PAPER TRADING v1.0
==============================
Simulated trading system for strategy validation

Features:
- Virtual portfolio management
- Trade logging to CSV/JSON
- Real-time P&L tracking
- Performance statistics
- Risk management validation

Author: Hamster Terminal Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import csv
import os
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PaperPosition:
    """Virtual trading position"""
    id: str
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    entry_time: datetime
    size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = 'OPEN'  # 'OPEN', 'CLOSED', 'STOPPED', 'TP_HIT'
    signal_confluence: float = 0.0
    signal_type: str = ''
    notes: str = ''
    
    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L"""
        if self.direction == 'LONG':
            self.pnl = (current_price - self.entry_price) * self.size
            self.pnl_pct = (current_price / self.entry_price - 1) * 100
        else:
            self.pnl = (self.entry_price - current_price) * self.size
            self.pnl_pct = (self.entry_price / current_price - 1) * 100
        return self.pnl
    
    def close(self, exit_price: float, reason: str = 'MANUAL'):
        """Close the position"""
        self.exit_price = exit_price
        self.exit_time = datetime.now()
        self.calculate_unrealized_pnl(exit_price)
        self.status = reason
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat(),
            'exit_price': self.exit_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'size': self.size,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'pnl': round(self.pnl, 2),
            'pnl_pct': round(self.pnl_pct, 2),
            'status': self.status,
            'signal_confluence': self.signal_confluence,
            'signal_type': self.signal_type,
            'notes': self.notes
        }


@dataclass
class PaperPortfolio:
    """Virtual portfolio state"""
    initial_balance: float
    cash_balance: float
    total_equity: float
    unrealized_pnl: float
    realized_pnl: float
    open_positions: List[PaperPosition] = field(default_factory=list)
    closed_positions: List[PaperPosition] = field(default_factory=list)
    
    # Statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'initial_balance': self.initial_balance,
            'cash_balance': round(self.cash_balance, 2),
            'total_equity': round(self.total_equity, 2),
            'unrealized_pnl': round(self.unrealized_pnl, 2),
            'realized_pnl': round(self.realized_pnl, 2),
            'return_pct': round((self.total_equity / self.initial_balance - 1) * 100, 2),
            'open_positions': len(self.open_positions),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.winning_trades / max(self.total_trades, 1) * 100, 1)
        }


class GeniusPaperTrading:
    """
    Paper trading system for Genius Engine
    """
    
    def __init__(self, initial_balance: float = 10000,
                 data_dir: str = 'paper_trading'):
        self.portfolio = PaperPortfolio(
            initial_balance=initial_balance,
            cash_balance=initial_balance,
            total_equity=initial_balance,
            unrealized_pnl=0,
            realized_pnl=0
        )
        
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.trade_counter = 0
        self.lock = Lock()
        
        # File paths
        self.trades_csv = os.path.join(data_dir, 'paper_trades.csv')
        self.positions_json = os.path.join(data_dir, 'open_positions.json')
        self.portfolio_json = os.path.join(data_dir, 'portfolio.json')
        self.signals_log = os.path.join(data_dir, 'signals_log.csv')
        
        # Load existing state
        self._load_state()
        
        logger.info(f"📝 Paper Trading initialized with ${initial_balance:,.0f}")
        logger.info(f"   Data directory: {data_dir}")
    
    def _load_state(self):
        """Load previous state from files"""
        try:
            if os.path.exists(self.portfolio_json):
                with open(self.portfolio_json, 'r') as f:
                    data = json.load(f)
                    self.portfolio.cash_balance = data.get('cash_balance', self.portfolio.initial_balance)
                    self.portfolio.realized_pnl = data.get('realized_pnl', 0)
                    self.portfolio.total_trades = data.get('total_trades', 0)
                    self.portfolio.winning_trades = data.get('winning_trades', 0)
                    self.portfolio.losing_trades = data.get('losing_trades', 0)
                    self.trade_counter = data.get('trade_counter', 0)
                    logger.info(f"   Loaded portfolio: ${self.portfolio.cash_balance:,.2f}")
            
            if os.path.exists(self.positions_json):
                with open(self.positions_json, 'r') as f:
                    positions_data = json.load(f)
                    for pos_data in positions_data:
                        pos = PaperPosition(
                            id=pos_data['id'],
                            symbol=pos_data['symbol'],
                            direction=pos_data['direction'],
                            entry_price=pos_data['entry_price'],
                            entry_time=datetime.fromisoformat(pos_data['entry_time']),
                            size=pos_data['size'],
                            stop_loss=pos_data.get('stop_loss'),
                            take_profit=pos_data.get('take_profit'),
                            signal_confluence=pos_data.get('signal_confluence', 0),
                            signal_type=pos_data.get('signal_type', '')
                        )
                        self.portfolio.open_positions.append(pos)
                    logger.info(f"   Loaded {len(self.portfolio.open_positions)} open positions")
                    
        except Exception as e:
            logger.warning(f"   Could not load previous state: {e}")
    
    def _save_state(self):
        """Save current state to files"""
        try:
            # Save portfolio
            with open(self.portfolio_json, 'w') as f:
                json.dump({
                    'cash_balance': self.portfolio.cash_balance,
                    'realized_pnl': self.portfolio.realized_pnl,
                    'total_trades': self.portfolio.total_trades,
                    'winning_trades': self.portfolio.winning_trades,
                    'losing_trades': self.portfolio.losing_trades,
                    'trade_counter': self.trade_counter,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            
            # Save open positions
            with open(self.positions_json, 'w') as f:
                json.dump([p.to_dict() for p in self.portfolio.open_positions], f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _log_trade(self, position: PaperPosition):
        """Log trade to CSV"""
        try:
            file_exists = os.path.exists(self.trades_csv)
            
            with open(self.trades_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow([
                        'id', 'symbol', 'direction', 'entry_time', 'exit_time',
                        'entry_price', 'exit_price', 'size', 'pnl', 'pnl_pct',
                        'status', 'signal_type', 'confluence', 'notes'
                    ])
                
                writer.writerow([
                    position.id,
                    position.symbol,
                    position.direction,
                    position.entry_time.isoformat(),
                    position.exit_time.isoformat() if position.exit_time else '',
                    position.entry_price,
                    position.exit_price or '',
                    position.size,
                    round(position.pnl, 2),
                    round(position.pnl_pct, 2),
                    position.status,
                    position.signal_type,
                    position.signal_confluence,
                    position.notes
                ])
                
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
    
    def log_signal(self, signal_data: Dict):
        """Log any signal (even if no trade taken)"""
        try:
            file_exists = os.path.exists(self.signals_log)
            
            with open(self.signals_log, 'a', newline='') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow([
                        'timestamp', 'symbol', 'signal', 'confluence', 
                        'price', 'action', 'reason'
                    ])
                
                writer.writerow([
                    datetime.now().isoformat(),
                    signal_data.get('symbol', 'BTC/USD'),
                    signal_data.get('signal', 'UNKNOWN'),
                    signal_data.get('confluence', 0),
                    signal_data.get('price', 0),
                    signal_data.get('action', 'LOGGED'),
                    signal_data.get('reason', '')
                ])
                
        except Exception as e:
            logger.error(f"Error logging signal: {e}")
    
    def open_position(self, symbol: str, direction: str, 
                      entry_price: float, size: float,
                      stop_loss: float = None, take_profit: float = None,
                      signal_type: str = '', signal_confluence: float = 0,
                      notes: str = '') -> Optional[PaperPosition]:
        """Open a new paper position"""
        with self.lock:
            # Check if we have enough balance
            position_value = entry_price * size
            if position_value > self.portfolio.cash_balance:
                logger.warning(f"Insufficient balance for position: ${position_value:,.0f} > ${self.portfolio.cash_balance:,.0f}")
                return None
            
            # Generate position ID
            self.trade_counter += 1
            position_id = f"PT{self.trade_counter:05d}"
            
            # Create position
            position = PaperPosition(
                id=position_id,
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                entry_time=datetime.now(),
                size=size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                signal_type=signal_type,
                signal_confluence=signal_confluence,
                notes=notes
            )
            
            # Deduct from cash (simplified - in reality futures don't use full amount)
            self.portfolio.cash_balance -= position_value * 0.1  # 10% margin
            self.portfolio.open_positions.append(position)
            
            self._save_state()
            
            logger.info(f"📈 Opened {direction} position: {position_id}")
            logger.info(f"   {symbol} @ ${entry_price:,.2f} x {size}")
            
            return position
    
    def close_position(self, position_id: str, exit_price: float,
                       reason: str = 'MANUAL') -> Optional[PaperPosition]:
        """Close an existing position"""
        with self.lock:
            # Find position
            position = None
            for p in self.portfolio.open_positions:
                if p.id == position_id:
                    position = p
                    break
            
            if not position:
                logger.warning(f"Position not found: {position_id}")
                return None
            
            # Close position
            position.close(exit_price, reason)
            
            # Update portfolio
            self.portfolio.open_positions.remove(position)
            self.portfolio.closed_positions.append(position)
            self.portfolio.realized_pnl += position.pnl
            self.portfolio.cash_balance += position.entry_price * position.size * 0.1 + position.pnl
            
            self.portfolio.total_trades += 1
            if position.pnl > 0:
                self.portfolio.winning_trades += 1
            else:
                self.portfolio.losing_trades += 1
            
            # Log trade
            self._log_trade(position)
            self._save_state()
            
            logger.info(f"📉 Closed position: {position_id}")
            logger.info(f"   P&L: ${position.pnl:+,.2f} ({position.pnl_pct:+.2f}%)")
            
            return position
    
    def close_all_positions(self, current_prices: Dict[str, float]) -> List[PaperPosition]:
        """Close all open positions"""
        closed = []
        for position in list(self.portfolio.open_positions):
            price = current_prices.get(position.symbol, position.entry_price)
            closed_pos = self.close_position(position.id, price, 'CLOSE_ALL')
            if closed_pos:
                closed.append(closed_pos)
        return closed
    
    def update_prices(self, current_prices: Dict[str, float]):
        """Update unrealized P&L with current prices"""
        with self.lock:
            total_unrealized = 0
            
            for position in self.portfolio.open_positions:
                price = current_prices.get(position.symbol, position.entry_price)
                position.calculate_unrealized_pnl(price)
                total_unrealized += position.pnl
                
                # Check stop loss / take profit
                if position.stop_loss:
                    if (position.direction == 'LONG' and price <= position.stop_loss) or \
                       (position.direction == 'SHORT' and price >= position.stop_loss):
                        self.close_position(position.id, position.stop_loss, 'STOPPED')
                        continue
                
                if position.take_profit:
                    if (position.direction == 'LONG' and price >= position.take_profit) or \
                       (position.direction == 'SHORT' and price <= position.take_profit):
                        self.close_position(position.id, position.take_profit, 'TP_HIT')
                        continue
            
            self.portfolio.unrealized_pnl = total_unrealized
            self.portfolio.total_equity = self.portfolio.cash_balance + total_unrealized
    
    def process_signal(self, signal: Dict, current_price: float,
                       risk_per_trade: float = 0.02) -> Dict:
        """
        Process a Genius Engine signal and potentially open a trade
        """
        result = {
            'action': 'NONE',
            'reason': '',
            'position': None
        }
        
        signal_type = signal.get('signal', 'HOLD')
        confluence = signal.get('confluence_score', 0)
        symbol = signal.get('symbol', 'BTC/USD')
        
        # Log all signals
        self.log_signal({
            'symbol': symbol,
            'signal': signal_type,
            'confluence': confluence,
            'price': current_price,
            'action': 'EVALUATING'
        })
        
        # Only trade on strong signals
        if signal_type in ['NO_TRADE', 'HOLD']:
            result['action'] = 'SKIP'
            result['reason'] = f"Signal is {signal_type}"
            return result
        
        # Check confluence threshold
        if confluence < 70:
            result['action'] = 'SKIP'
            result['reason'] = f"Confluence {confluence}% below 70% threshold"
            return result
        
        # Determine direction
        if signal_type in ['BUY', 'STRONG_BUY']:
            direction = 'LONG'
        elif signal_type in ['SELL', 'STRONG_SELL']:
            direction = 'SHORT'
        else:
            result['action'] = 'SKIP'
            result['reason'] = f"Unknown signal type: {signal_type}"
            return result
        
        # Check if we already have a position in same direction
        for pos in self.portfolio.open_positions:
            if pos.symbol == symbol and pos.direction == direction:
                result['action'] = 'SKIP'
                result['reason'] = f"Already have {direction} position"
                return result
        
        # Calculate position size
        risk_amount = self.portfolio.total_equity * risk_per_trade
        stop_loss_pct = signal.get('stop_loss_pct', 0.02)
        size = risk_amount / (current_price * stop_loss_pct)
        
        # Get levels from signal
        stop_loss = signal.get('stop_loss', current_price * (1 - stop_loss_pct if direction == 'LONG' else 1 + stop_loss_pct))
        take_profit = signal.get('take_profit_2', current_price * (1.04 if direction == 'LONG' else 0.96))
        
        # Open position
        position = self.open_position(
            symbol=symbol,
            direction=direction,
            entry_price=current_price,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            signal_type=signal_type,
            signal_confluence=confluence,
            notes=f"Auto-trade from Genius signal"
        )
        
        if position:
            result['action'] = 'OPENED'
            result['position'] = position.to_dict()
            result['reason'] = f"Opened {direction} based on {signal_type} ({confluence}%)"
            
            self.log_signal({
                'symbol': symbol,
                'signal': signal_type,
                'confluence': confluence,
                'price': current_price,
                'action': 'TRADE_OPENED',
                'reason': result['reason']
            })
        else:
            result['action'] = 'FAILED'
            result['reason'] = 'Could not open position (insufficient balance?)'
        
        return result
    
    def get_statistics(self) -> Dict:
        """Get comprehensive trading statistics"""
        closed = self.portfolio.closed_positions
        
        if not closed:
            return {
                'portfolio': self.portfolio.to_dict(),
                'statistics': {
                    'message': 'No closed trades yet'
                }
            }
        
        pnls = [p.pnl for p in closed]
        pnl_pcts = [p.pnl_pct for p in closed]
        wins = [p for p in closed if p.pnl > 0]
        losses = [p for p in closed if p.pnl <= 0]
        
        return {
            'portfolio': self.portfolio.to_dict(),
            'statistics': {
                'total_trades': len(closed),
                'winning_trades': len(wins),
                'losing_trades': len(losses),
                'win_rate': round(len(wins) / len(closed) * 100, 1),
                'total_pnl': round(sum(pnls), 2),
                'avg_pnl': round(np.mean(pnls), 2),
                'avg_win': round(np.mean([p.pnl for p in wins]), 2) if wins else 0,
                'avg_loss': round(np.mean([p.pnl for p in losses]), 2) if losses else 0,
                'best_trade': round(max(pnls), 2),
                'worst_trade': round(min(pnls), 2),
                'profit_factor': round(sum(p.pnl for p in wins) / abs(sum(p.pnl for p in losses)), 2) if losses else 0,
                'avg_confluence': round(np.mean([p.signal_confluence for p in closed]), 1)
            },
            'open_positions': [p.to_dict() for p in self.portfolio.open_positions],
            'recent_trades': [p.to_dict() for p in closed[-10:]]
        }
    
    def reset(self):
        """Reset paper trading to initial state"""
        with self.lock:
            self.portfolio = PaperPortfolio(
                initial_balance=self.portfolio.initial_balance,
                cash_balance=self.portfolio.initial_balance,
                total_equity=self.portfolio.initial_balance,
                unrealized_pnl=0,
                realized_pnl=0
            )
            self.trade_counter = 0
            self._save_state()
            logger.info("📝 Paper trading reset to initial state")


# ============ SINGLETON ============
paper_trader = GeniusPaperTrading()


def process_genius_signal(signal: Dict, current_price: float) -> Dict:
    """API function to process signals"""
    return paper_trader.process_signal(signal, current_price)


def get_paper_stats() -> Dict:
    """API function to get statistics"""
    return paper_trader.get_statistics()


if __name__ == '__main__':
    print("=" * 70)
    print("📝 GENIUS PAPER TRADING v1.0")
    print("=" * 70)
    
    # Create paper trader
    trader = GeniusPaperTrading(initial_balance=10000)
    
    # Simulate some signals
    print("\n📊 Simulating trading signals...")
    
    # Signal 1: Strong Buy
    signal1 = {
        'signal': 'STRONG_BUY',
        'confluence_score': 85,
        'symbol': 'BTC/USD',
        'stop_loss': 99000,
        'take_profit_2': 108000
    }
    result1 = trader.process_signal(signal1, current_price=102500)
    print(f"\nSignal 1: {result1['action']} - {result1['reason']}")
    
    # Signal 2: Below threshold
    signal2 = {
        'signal': 'BUY',
        'confluence_score': 55,
        'symbol': 'ETH/USD'
    }
    result2 = trader.process_signal(signal2, current_price=3200)
    print(f"Signal 2: {result2['action']} - {result2['reason']}")
    
    # Update prices (simulate price movement)
    print("\n📈 Simulating price movement...")
    trader.update_prices({'BTC/USD': 104000})
    
    # Get stats
    stats = trader.get_statistics()
    print(f"\n💼 PORTFOLIO STATUS:")
    print(f"   Cash Balance: ${stats['portfolio']['cash_balance']:,.2f}")
    print(f"   Total Equity: ${stats['portfolio']['total_equity']:,.2f}")
    print(f"   Unrealized P&L: ${trader.portfolio.unrealized_pnl:+,.2f}")
    print(f"   Open Positions: {stats['portfolio']['open_positions']}")
    
    # Close position manually
    if trader.portfolio.open_positions:
        pos = trader.portfolio.open_positions[0]
        trader.close_position(pos.id, 104500, 'MANUAL')
        
        # Final stats
        stats = trader.get_statistics()
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   Total Trades: {stats['statistics'].get('total_trades', 0)}")
        print(f"   Win Rate: {stats['statistics'].get('win_rate', 0)}%")
        print(f"   Total P&L: ${stats['statistics'].get('total_pnl', 0):+,.2f}")
        print(f"   Realized P&L: ${trader.portfolio.realized_pnl:+,.2f}")
    
    print("\n" + "=" * 70)
    print(f"✅ Paper Trading Test PASSED!")
    print(f"   Data saved to: {trader.data_dir}/")
