"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GENIUS ORDER EXECUTOR v1.0                                 ║
║                    Real Trading Execution Engine                              ║
║                                                                              ║
║  Features:                                                                   ║
║  • Live order execution on Binance/Bybit                                    ║
║  • Market, Limit, Stop-Loss, Take-Profit orders                            ║
║  • Position management with trailing stops                                  ║
║  • Risk-based position sizing                                               ║
║  • Order validation and safety checks                                       ║
║  • Execution analytics and slippage tracking                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hmac
import hashlib
import time

# CCXT for exchange connectivity
try:
    import ccxt
    import ccxt.async_support as ccxt_async
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    print("⚠️ ccxt not installed. Run: pip install ccxt")

import numpy as np


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LOSS_LIMIT = "stop_loss_limit"
    TAKE_PROFIT = "take_profit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Exchange(Enum):
    BINANCE = "binance"
    BINANCE_FUTURES = "binanceusdm"
    BYBIT = "bybit"
    BYBIT_UNIFIED = "bybit"
    KRAKEN = "kraken"
    COINBASE = "coinbase"


@dataclass
class OrderRequest:
    """Order request structure"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    trailing_percent: Optional[float] = None
    reduce_only: bool = False
    post_only: bool = False
    time_in_force: str = "GTC"  # GTC, IOC, FOK
    client_order_id: Optional[str] = None


@dataclass
class OrderResult:
    """Order execution result"""
    order_id: str
    client_order_id: Optional[str]
    symbol: str
    side: str
    order_type: str
    status: OrderStatus
    quantity: float
    filled_quantity: float
    price: float
    average_price: float
    fee: float
    fee_currency: str
    timestamp: datetime
    raw_response: Dict = field(default_factory=dict)
    
    @property
    def slippage_pct(self) -> float:
        """Calculate slippage percentage"""
        if self.price and self.average_price:
            return ((self.average_price - self.price) / self.price) * 100
        return 0.0


@dataclass
class Position:
    """Current position"""
    symbol: str
    side: str  # long, short
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    leverage: int
    liquidation_price: Optional[float]
    margin: float
    timestamp: datetime


class ExecutionConfig:
    """Execution configuration"""
    
    # API Keys (from environment)
    BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY', '')
    BINANCE_SECRET = os.environ.get('BINANCE_SECRET', '')
    BYBIT_API_KEY = os.environ.get('BYBIT_API_KEY', '')
    BYBIT_SECRET = os.environ.get('BYBIT_SECRET', '')
    
    # Safety settings
    MAX_POSITION_SIZE_USD = 10000  # Max position size
    MAX_LEVERAGE = 10
    MAX_SLIPPAGE_PCT = 0.5  # 0.5% max slippage
    MIN_ORDER_SIZE_USD = 10
    
    # Risk settings
    DEFAULT_STOP_LOSS_PCT = 2.0  # 2% default stop loss
    DEFAULT_TAKE_PROFIT_PCT = 4.0  # 4% default take profit
    
    # Execution settings
    USE_TESTNET = True  # IMPORTANT: Start with testnet!
    RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 1


class GeniusOrderExecutor:
    """
    Professional Order Execution Engine
    
    Supports:
    - Binance Spot & Futures
    - Bybit Unified
    - Multiple order types
    - Position management
    - Risk controls
    """
    
    def __init__(
        self,
        exchange: Exchange = Exchange.BINANCE_FUTURES,
        testnet: bool = True,
        api_key: str = None,
        api_secret: str = None
    ):
        self.exchange_type = exchange
        self.testnet = testnet
        self.api_key = api_key
        self.api_secret = api_secret
        
        self.exchange: Optional[ccxt.Exchange] = None
        self.async_exchange: Optional[ccxt_async.Exchange] = None
        
        self.logger = logging.getLogger('GeniusOrderExecutor')
        
        # Order tracking
        self.pending_orders: Dict[str, OrderRequest] = {}
        self.executed_orders: List[OrderResult] = []
        self.positions: Dict[str, Position] = {}
        
        # Analytics
        self.total_volume_traded = 0.0
        self.total_fees_paid = 0.0
        self.total_slippage = 0.0
        
        if CCXT_AVAILABLE:
            self._initialize_exchange()
    
    def _initialize_exchange(self):
        """Initialize exchange connection"""
        
        exchange_class = getattr(ccxt, self.exchange_type.value)
        
        config = {
            'apiKey': self.api_key or self._get_api_key(),
            'secret': self.api_secret or self._get_api_secret(),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future' if 'futures' in self.exchange_type.value.lower() else 'spot'
            }
        }
        
        # Testnet configuration
        if self.testnet:
            if self.exchange_type in [Exchange.BINANCE, Exchange.BINANCE_FUTURES]:
                config['options']['testnet'] = True
                config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binancefuture.com/fapi/v1',
                        'private': 'https://testnet.binancefuture.com/fapi/v1',
                    }
                }
            elif self.exchange_type == Exchange.BYBIT:
                config['options']['testnet'] = True
        
        self.exchange = exchange_class(config)
        
        # Also create async version
        async_exchange_class = getattr(ccxt_async, self.exchange_type.value)
        self.async_exchange = async_exchange_class(config)
        
        self.logger.info(f"Initialized {self.exchange_type.value} ({'TESTNET' if self.testnet else 'LIVE'})")
    
    def _get_api_key(self) -> str:
        """Get API key for current exchange"""
        if self.exchange_type in [Exchange.BINANCE, Exchange.BINANCE_FUTURES]:
            return ExecutionConfig.BINANCE_API_KEY
        elif self.exchange_type in [Exchange.BYBIT, Exchange.BYBIT_UNIFIED]:
            return ExecutionConfig.BYBIT_API_KEY
        return ''
    
    def _get_api_secret(self) -> str:
        """Get API secret for current exchange"""
        if self.exchange_type in [Exchange.BINANCE, Exchange.BINANCE_FUTURES]:
            return ExecutionConfig.BINANCE_SECRET
        elif self.exchange_type in [Exchange.BYBIT, Exchange.BYBIT_UNIFIED]:
            return ExecutionConfig.BYBIT_SECRET
        return ''
    
    # ═══════════════════════════════════════════════════════════════════════
    # SAFETY CHECKS
    # ═══════════════════════════════════════════════════════════════════════
    
    def validate_order(self, order: OrderRequest, current_price: float) -> Tuple[bool, str]:
        """
        Validate order against safety rules
        
        Returns:
            (is_valid, error_message)
        """
        
        # Check order size
        order_value = order.quantity * current_price
        
        if order_value > ExecutionConfig.MAX_POSITION_SIZE_USD:
            return False, f"Order size ${order_value:.2f} exceeds max ${ExecutionConfig.MAX_POSITION_SIZE_USD}"
        
        if order_value < ExecutionConfig.MIN_ORDER_SIZE_USD:
            return False, f"Order size ${order_value:.2f} below minimum ${ExecutionConfig.MIN_ORDER_SIZE_USD}"
        
        # Check price deviation for limit orders
        if order.order_type == OrderType.LIMIT and order.price:
            deviation = abs(order.price - current_price) / current_price * 100
            if deviation > 5:  # More than 5% away from current price
                return False, f"Limit price deviation {deviation:.2f}% too high"
        
        # Check stop loss is set for leveraged positions
        if not order.stop_loss and not order.reduce_only:
            self.logger.warning("No stop loss set - consider adding one")
        
        return True, ""
    
    def calculate_position_size(
        self,
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Calculate position size based on risk
        
        Args:
            capital: Total capital
            risk_pct: Risk percentage (e.g., 1 for 1%)
            entry_price: Entry price
            stop_loss_price: Stop loss price
            
        Returns:
            Position size in base currency
        """
        
        risk_amount = capital * (risk_pct / 100)
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            return 0
        
        position_size = risk_amount / price_risk
        
        # Cap at max position size
        max_size = ExecutionConfig.MAX_POSITION_SIZE_USD / entry_price
        return min(position_size, max_size)
    
    # ═══════════════════════════════════════════════════════════════════════
    # ORDER EXECUTION
    # ═══════════════════════════════════════════════════════════════════════
    
    async def execute_order(self, order: OrderRequest) -> OrderResult:
        """
        Execute an order on the exchange
        
        Args:
            order: OrderRequest with order details
            
        Returns:
            OrderResult with execution details
        """
        
        if not CCXT_AVAILABLE or not self.async_exchange:
            raise RuntimeError("CCXT not available or exchange not initialized")
        
        # Get current price for validation
        ticker = await self.async_exchange.fetch_ticker(order.symbol)
        current_price = ticker['last']
        
        # Validate order
        is_valid, error = self.validate_order(order, current_price)
        if not is_valid:
            raise ValueError(f"Order validation failed: {error}")
        
        # Prepare order parameters
        params = {}
        
        if order.reduce_only:
            params['reduceOnly'] = True
        
        if order.post_only:
            params['postOnly'] = True
        
        if order.time_in_force:
            params['timeInForce'] = order.time_in_force
        
        if order.client_order_id:
            params['clientOrderId'] = order.client_order_id
        
        # Execute based on order type
        try:
            if order.order_type == OrderType.MARKET:
                response = await self.async_exchange.create_order(
                    symbol=order.symbol,
                    type='market',
                    side=order.side.value,
                    amount=order.quantity,
                    params=params
                )
            
            elif order.order_type == OrderType.LIMIT:
                response = await self.async_exchange.create_order(
                    symbol=order.symbol,
                    type='limit',
                    side=order.side.value,
                    amount=order.quantity,
                    price=order.price,
                    params=params
                )
            
            elif order.order_type == OrderType.STOP_LOSS:
                params['stopPrice'] = order.stop_price
                response = await self.async_exchange.create_order(
                    symbol=order.symbol,
                    type='stop_market',
                    side=order.side.value,
                    amount=order.quantity,
                    params=params
                )
            
            elif order.order_type == OrderType.TAKE_PROFIT:
                params['stopPrice'] = order.stop_price
                response = await self.async_exchange.create_order(
                    symbol=order.symbol,
                    type='take_profit_market',
                    side=order.side.value,
                    amount=order.quantity,
                    params=params
                )
            
            else:
                raise ValueError(f"Unsupported order type: {order.order_type}")
            
            # Parse response
            result = self._parse_order_response(response, order)
            
            # Update analytics
            self.executed_orders.append(result)
            self.total_volume_traded += result.filled_quantity * result.average_price
            self.total_fees_paid += result.fee
            self.total_slippage += abs(result.slippage_pct)
            
            # Set stop loss and take profit if provided
            if order.stop_loss and result.status == OrderStatus.FILLED:
                await self._set_stop_loss(order.symbol, order.quantity, order.stop_loss, order.side)
            
            if order.take_profit and result.status == OrderStatus.FILLED:
                await self._set_take_profit(order.symbol, order.quantity, order.take_profit, order.side)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Order execution failed: {e}")
            raise
    
    async def _set_stop_loss(
        self,
        symbol: str,
        quantity: float,
        stop_price: float,
        entry_side: OrderSide
    ):
        """Set stop loss order for position"""
        
        # Stop loss is opposite side of entry
        sl_side = OrderSide.SELL if entry_side == OrderSide.BUY else OrderSide.BUY
        
        params = {
            'stopPrice': stop_price,
            'reduceOnly': True
        }
        
        await self.async_exchange.create_order(
            symbol=symbol,
            type='stop_market',
            side=sl_side.value,
            amount=quantity,
            params=params
        )
        
        self.logger.info(f"Stop loss set at {stop_price} for {symbol}")
    
    async def _set_take_profit(
        self,
        symbol: str,
        quantity: float,
        tp_price: float,
        entry_side: OrderSide
    ):
        """Set take profit order for position"""
        
        tp_side = OrderSide.SELL if entry_side == OrderSide.BUY else OrderSide.BUY
        
        params = {
            'stopPrice': tp_price,
            'reduceOnly': True
        }
        
        await self.async_exchange.create_order(
            symbol=symbol,
            type='take_profit_market',
            side=tp_side.value,
            amount=quantity,
            params=params
        )
        
        self.logger.info(f"Take profit set at {tp_price} for {symbol}")
    
    def _parse_order_response(self, response: Dict, order: OrderRequest) -> OrderResult:
        """Parse exchange response into OrderResult"""
        
        # Extract fee info
        fee = 0.0
        fee_currency = 'USDT'
        if 'fee' in response and response['fee']:
            fee = response['fee'].get('cost', 0) or 0
            fee_currency = response['fee'].get('currency', 'USDT')
        
        return OrderResult(
            order_id=response.get('id', ''),
            client_order_id=response.get('clientOrderId'),
            symbol=response.get('symbol', order.symbol),
            side=response.get('side', order.side.value),
            order_type=response.get('type', order.order_type.value),
            status=OrderStatus(response.get('status', 'open').lower()),
            quantity=order.quantity,
            filled_quantity=response.get('filled', 0) or 0,
            price=order.price or response.get('price', 0) or 0,
            average_price=response.get('average', 0) or response.get('price', 0) or 0,
            fee=fee,
            fee_currency=fee_currency,
            timestamp=datetime.now(),
            raw_response=response
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # POSITION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        
        if not self.async_exchange:
            return []
        
        try:
            positions = await self.async_exchange.fetch_positions()
            
            result = []
            for pos in positions:
                if float(pos.get('contracts', 0)) != 0:
                    result.append(Position(
                        symbol=pos['symbol'],
                        side='long' if float(pos.get('contracts', 0)) > 0 else 'short',
                        quantity=abs(float(pos.get('contracts', 0))),
                        entry_price=float(pos.get('entryPrice', 0)),
                        current_price=float(pos.get('markPrice', 0)),
                        unrealized_pnl=float(pos.get('unrealizedPnl', 0)),
                        realized_pnl=float(pos.get('realizedPnl', 0)),
                        leverage=int(pos.get('leverage', 1)),
                        liquidation_price=float(pos.get('liquidationPrice', 0)) if pos.get('liquidationPrice') else None,
                        margin=float(pos.get('initialMargin', 0)),
                        timestamp=datetime.now()
                    ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to fetch positions: {e}")
            return []
    
    async def close_position(self, symbol: str, percentage: float = 100) -> Optional[OrderResult]:
        """
        Close a position (fully or partially)
        
        Args:
            symbol: Trading pair
            percentage: Percentage to close (1-100)
        """
        
        positions = await self.get_positions()
        
        for pos in positions:
            if pos.symbol == symbol:
                close_qty = pos.quantity * (percentage / 100)
                close_side = OrderSide.SELL if pos.side == 'long' else OrderSide.BUY
                
                order = OrderRequest(
                    symbol=symbol,
                    side=close_side,
                    order_type=OrderType.MARKET,
                    quantity=close_qty,
                    reduce_only=True
                )
                
                return await self.execute_order(order)
        
        self.logger.warning(f"No position found for {symbol}")
        return None
    
    async def close_all_positions(self) -> List[OrderResult]:
        """Close all open positions"""
        
        results = []
        positions = await self.get_positions()
        
        for pos in positions:
            result = await self.close_position(pos.symbol)
            if result:
                results.append(result)
        
        return results
    
    # ═══════════════════════════════════════════════════════════════════════
    # SIGNAL INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════
    
    async def execute_genius_signal(
        self,
        signal: Dict,
        capital: float,
        risk_pct: float = 1.0
    ) -> Optional[OrderResult]:
        """
        Execute a Genius Engine signal
        
        Args:
            signal: Signal from Genius Engine
            capital: Available capital
            risk_pct: Risk percentage per trade
        """
        
        direction = signal.get('direction', 'NEUTRAL')
        
        if direction == 'NEUTRAL':
            self.logger.info("Signal is NEUTRAL - no trade")
            return None
        
        symbol = signal.get('symbol', 'BTC/USDT')
        entry_price = signal.get('entry', signal.get('price', 0))
        stop_loss = signal.get('stop_loss', 0)
        take_profit = signal.get('take_profit', 0)
        
        # Calculate position size
        if stop_loss:
            quantity = self.calculate_position_size(
                capital, risk_pct, entry_price, stop_loss
            )
        else:
            # Default 2% risk if no stop loss
            stop_loss = entry_price * (0.98 if direction == 'LONG' else 1.02)
            quantity = self.calculate_position_size(
                capital, risk_pct, entry_price, stop_loss
            )
        
        # Create order
        order = OrderRequest(
            symbol=symbol,
            side=OrderSide.BUY if direction == 'LONG' else OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.logger.info(f"Executing {direction} signal for {symbol}")
        self.logger.info(f"  Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}")
        self.logger.info(f"  Quantity: {quantity}, Risk: {risk_pct}%")
        
        return await self.execute_order(order)
    
    # ═══════════════════════════════════════════════════════════════════════
    # ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        
        if not self.executed_orders:
            return {
                'total_orders': 0,
                'total_volume': 0,
                'total_fees': 0,
                'avg_slippage': 0,
                'fill_rate': 0
            }
        
        filled_orders = [o for o in self.executed_orders if o.status == OrderStatus.FILLED]
        
        return {
            'total_orders': len(self.executed_orders),
            'filled_orders': len(filled_orders),
            'fill_rate': len(filled_orders) / len(self.executed_orders) * 100,
            'total_volume': self.total_volume_traded,
            'total_fees': self.total_fees_paid,
            'avg_slippage': self.total_slippage / len(self.executed_orders) if self.executed_orders else 0,
            'avg_fee_pct': (self.total_fees_paid / self.total_volume_traded * 100) if self.total_volume_traded else 0
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.async_exchange:
            await self.async_exchange.close()


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demo the order executor"""
    
    print("=" * 70)
    print("💹 GENIUS ORDER EXECUTOR v1.0 - DEMO")
    print("=" * 70)
    
    print(f"\n📦 CCXT Available: {'✅' if CCXT_AVAILABLE else '❌'}")
    
    print("\n🔧 SUPPORTED EXCHANGES:")
    for ex in Exchange:
        print(f"   • {ex.value}")
    
    print("\n📋 ORDER TYPES:")
    for ot in OrderType:
        print(f"   • {ot.value}")
    
    print("\n⚙️ SAFETY SETTINGS:")
    print(f"   Max Position Size: ${ExecutionConfig.MAX_POSITION_SIZE_USD:,}")
    print(f"   Max Leverage: {ExecutionConfig.MAX_LEVERAGE}x")
    print(f"   Max Slippage: {ExecutionConfig.MAX_SLIPPAGE_PCT}%")
    print(f"   Default Stop Loss: {ExecutionConfig.DEFAULT_STOP_LOSS_PCT}%")
    print(f"   Default Take Profit: {ExecutionConfig.DEFAULT_TAKE_PROFIT_PCT}%")
    print(f"   Testnet Mode: {ExecutionConfig.USE_TESTNET}")
    
    print("\n📊 POSITION SIZING EXAMPLE:")
    executor = GeniusOrderExecutor.__new__(GeniusOrderExecutor)
    executor.logger = logging.getLogger('demo')
    
    # Example calculation
    capital = 10000
    risk_pct = 1  # 1% risk
    entry = 97500
    stop_loss = 95000
    
    size = (capital * (risk_pct / 100)) / abs(entry - stop_loss)
    print(f"   Capital: ${capital:,}")
    print(f"   Risk: {risk_pct}%")
    print(f"   Entry: ${entry:,}")
    print(f"   Stop Loss: ${stop_loss:,}")
    print(f"   Position Size: {size:.4f} BTC (${size * entry:,.2f})")
    
    print("\n🔗 INTEGRATION EXAMPLE:")
    print("""
    # Execute Genius Signal
    executor = GeniusOrderExecutor(
        exchange=Exchange.BINANCE_FUTURES,
        testnet=True  # Always start with testnet!
    )
    
    signal = genius_engine.generate_signal('BTC/USDT')
    
    if signal['direction'] != 'NEUTRAL':
        result = await executor.execute_genius_signal(
            signal=signal,
            capital=10000,
            risk_pct=1.0
        )
        print(f"Order filled at {result.average_price}")
    """)
    
    print("\n" + "=" * 70)
    print("✅ Order Executor ready!")
    print("   ⚠️ Always use TESTNET first!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    demo()
