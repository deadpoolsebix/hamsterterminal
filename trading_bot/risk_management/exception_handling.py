#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exception Handling & Error Recovery
Dla leverage 100x - każdy błąd może kosztować całe konto
"""

import logging
import time
from functools import wraps
from typing import Callable, Any
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIConnectionError(Exception):
    """Błąd połączenia z API"""
    pass


class LiquidationRiskError(Exception):
    """Ryzyko likwidacji zbyt wysokie"""
    pass


class ExtremeVolatilityError(Exception):
    """Ekstremalna zmienność - wstrzymaj trading"""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential: bool = True
):
    """
    Decorator dla retry z exponential backoff
    
    Dla API calls - jeśli giełda 'zamrozi' API
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            delay = base_delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                
                except APIConnectionError as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.critical(f"❌ Max retries reached for {func.__name__}: {e}")
                        raise
                    
                    logger.warning(
                        f"⚠️ Retry {retries}/{max_retries} for {func.__name__} "
                        f"in {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)
                    
                    # Exponential backoff
                    if exponential:
                        delay = min(delay * 2, max_delay)
                    
                except Exception as e:
                    logger.error(f"❌ Unexpected error in {func.__name__}: {e}")
                    raise
            
            return None
        return wrapper
    return decorator


class OrderQueue:
    """
    Kolejka zleceń dla failed orders
    
    Jeśli API zamrozi podczas wysokiej zmienności:
    1. Zapisz zlecenie do kolejki
    2. Retry po powrocie połączenia
    3. Convert to market order jeśli krytyczne
    """
    
    def __init__(self, max_queue_size: int = 100):
        self.queue = []
        self.max_size = max_queue_size
        self.failed_orders = []
        
    def add_order(self, order: dict):
        """Dodaj zlecenie do kolejki"""
        if len(self.queue) >= self.max_size:
            logger.warning("⚠️ Order queue full! Dropping oldest order.")
            self.failed_orders.append(self.queue.pop(0))
        
        order['queued_at'] = time.time()
        self.queue.append(order)
        logger.info(f"📝 Order queued: {order['type']} {order['side']} @ {order.get('price', 'MARKET')}")
    
    def process_queue(self, api_executor: Callable):
        """
        Przetwórz kolejkę po powrocie API
        """
        processed = 0
        failed = 0
        
        while self.queue:
            order = self.queue.pop(0)
            
            try:
                # Check if order still valid
                time_in_queue = time.time() - order['queued_at']
                
                if time_in_queue > 60:  # 1 minute timeout
                    logger.warning(f"⚠️ Order expired in queue: {order}")
                    self.failed_orders.append(order)
                    failed += 1
                    continue
                
                # Critical orders -> convert to market
                if order.get('critical', False):
                    logger.warning(f"🚨 Converting to MARKET order: {order['type']}")
                    order['type'] = 'market'
                    order.pop('price', None)
                
                # Execute
                api_executor(order)
                processed += 1
                logger.info(f"✅ Order executed from queue: {order['side']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to execute queued order: {e}")
                self.failed_orders.append(order)
                failed += 1
        
        logger.info(f"📊 Queue processed: {processed} executed, {failed} failed")
        return processed, failed
    
    def get_critical_orders(self) -> list:
        """Pobierz krytyczne zlecenia (stop loss, liquidation prevention)"""
        return [o for o in self.queue if o.get('critical', False)]


class EmergencyProtocol:
    """
    Emergency protocol dla extreme scenarios
    
    Co robi bot, gdy:
    - API nie odpowiada
    - Wielka zmienność
    - Blisko likwidacji
    - Drawdown przekroczony
    """
    
    def __init__(self):
        self.emergency_active = False
        self.emergency_log = []
        
    def trigger_emergency(
        self,
        reason: str,
        positions: list,
        close_all: bool = False
    ):
        """
        Aktywuj emergency protocol
        """
        self.emergency_active = True
        
        emergency_event = {
            'timestamp': time.time(),
            'reason': reason,
            'positions_count': len(positions),
            'action': 'close_all' if close_all else 'monitor'
        }
        
        self.emergency_log.append(emergency_event)
        
        logger.critical(f"🚨 EMERGENCY TRIGGERED: {reason}")
        logger.critical(f"🚨 Positions at risk: {len(positions)}")
        
        if close_all:
            return self._emergency_close_all(positions)
        else:
            return self._emergency_monitor(positions)
    
    def _emergency_close_all(self, positions: list) -> list:
        """
        Zamknij wszystkie pozycje MARKET orderami
        """
        logger.critical("🚨 CLOSING ALL POSITIONS AT MARKET")
        
        close_orders = []
        for pos in positions:
            order = {
                'type': 'market',
                'side': 'sell' if pos['side'] == 'long' else 'buy',
                'quantity': pos['quantity'],
                'symbol': pos['symbol'],
                'critical': True,
                'emergency': True
            }
            close_orders.append(order)
            logger.warning(f"🚨 Emergency close: {pos['symbol']} {pos['side']}")
        
        return close_orders
    
    def _emergency_monitor(self, positions: list) -> dict:
        """
        Monitoruj pozycje bez zamykania
        """
        logger.warning("⚠️ EMERGENCY MONITORING ACTIVE")
        
        return {
            'mode': 'monitor',
            'positions': positions,
            'recommendations': [
                "Monitor liquidation distance",
                "Reduce leverage if possible",
                "Avoid new positions",
                "Wait for volatility decrease"
            ]
        }
    
    def check_api_health(self, last_response_time: float) -> bool:
        """
        Sprawdź health API
        """
        time_since_response = time.time() - last_response_time
        
        if time_since_response > 10:  # 10s bez odpowiedzi
            logger.error(f"❌ API not responding for {time_since_response:.0f}s")
            return False
        
        return True
    
    def should_halt_trading(
        self,
        api_health: bool,
        current_drawdown: float,
        max_drawdown: float,
        volatility: float,
        max_volatility: float
    ) -> tuple[bool, str]:
        """
        Czy zatrzymać trading?
        """
        reasons = []
        
        if not api_health:
            reasons.append("API connection lost")
        
        if current_drawdown > max_drawdown:
            reasons.append(f"Drawdown {current_drawdown:.1f}% > {max_drawdown:.1f}%")
        
        if volatility > max_volatility:
            reasons.append(f"Volatility {volatility:.1f}% > {max_volatility:.1f}%")
        
        if reasons:
            return True, " | ".join(reasons)
        
        return False, ""


def simulate_api_freeze():
    """
    Demo: Co robi bot podczas API freeze?
    """
    print("\n" + "="*60)
    print("🧪 DEMO: API FREEZE SCENARIO")
    print("="*60)
    
    # Initialize
    order_queue = OrderQueue()
    emergency = EmergencyProtocol()
    
    # Simulate open positions
    positions = [
        {'symbol': 'BTCUSDT', 'side': 'long', 'quantity': 0.1, 'entry': 50000, 'current': 49000},
        {'symbol': 'ETHUSDT', 'side': 'short', 'quantity': 2.0, 'entry': 3000, 'current': 3100}
    ]
    
    print("\n📊 Current Positions:")
    for pos in positions:
        pnl = (pos['current'] - pos['entry']) / pos['entry'] * 100
        if pos['side'] == 'short':
            pnl = -pnl
        print(f"  {pos['symbol']} {pos['side'].upper()}: {pnl:+.1f}% P&L")
    
    # Scenario 1: API freeze during high volatility
    print("\n🔥 Scenario: Giełda 'zamrozi' API podczas dużej zmienności")
    print("⚠️ API connection lost...")
    
    # Try to place stop loss (will fail)
    print("\n📝 Trying to place emergency stop loss...")
    stop_loss_order = {
        'type': 'stop_market',
        'side': 'sell',
        'quantity': 0.1,
        'stop_price': 48500,
        'critical': True
    }
    
    # Add to queue since API is down
    order_queue.add_order(stop_loss_order)
    
    # Check if we should trigger emergency
    api_health = False
    current_drawdown = 15  # 15% drawdown
    volatility = 12  # 12% volatility
    
    should_halt, reason = emergency.should_halt_trading(
        api_health=api_health,
        current_drawdown=current_drawdown,
        max_drawdown=20,
        volatility=volatility,
        max_volatility=10
    )
    
    if should_halt:
        print(f"\n🚨 TRADING HALTED: {reason}")
        
        # Decide action
        if current_drawdown > 10:
            print("🚨 Drawdown critical - attempting emergency close")
            close_orders = emergency.trigger_emergency(
                reason=reason,
                positions=positions,
                close_all=True
            )
            
            for order in close_orders:
                order_queue.add_order(order)
        else:
            print("⚠️ Monitoring positions")
            emergency.trigger_emergency(
                reason=reason,
                positions=positions,
                close_all=False
            )
    
    # Simulate API recovery
    print("\n✅ API connection restored!")
    print("\n📤 Processing order queue...")
    
    # Mock API executor
    def mock_api_executor(order):
        print(f"  ✅ Executed: {order['type']} {order['side']}")
    
    processed, failed = order_queue.process_queue(mock_api_executor)
    
    print(f"\n📊 Queue Results:")
    print(f"  Processed: {processed}")
    print(f"  Failed: {failed}")
    
    print("\n💡 Wnioski:")
    print("- Kolejka zleceń chroni przed utratą orders")
    print("- Critical orders (stop loss) są konwertowane na market")
    print("- Emergency protocol zamyka pozycje przy wysokim drawdown")
    print("- Exponential backoff dla retry API calls")
    print("="*60)


@retry_with_backoff(max_retries=3, base_delay=1.0)
def example_api_call_with_retry():
    """Przykład API call z retry"""
    # Simulate random API failure
    import random
    if random.random() < 0.7:  # 70% failure rate
        raise APIConnectionError("Connection timeout")
    
    return {"status": "success", "data": "Order placed"}


def demo_retry_mechanism():
    """Demo: Retry mechanism"""
    print("\n" + "="*60)
    print("🔄 DEMO: RETRY MECHANISM")
    print("="*60)
    
    print("\nAttempting API call with retry...")
    
    try:
        result = example_api_call_with_retry()
        print(f"✅ Success: {result}")
    except APIConnectionError as e:
        print(f"❌ Failed after retries: {e}")
    
    print("="*60)


if __name__ == "__main__":
    # Demo 1: Retry mechanism
    demo_retry_mechanism()
    
    # Demo 2: API freeze scenario
    simulate_api_freeze()
