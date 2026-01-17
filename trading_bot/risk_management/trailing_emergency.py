#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dynamiczny Trailing Stop + Emergency Exit System
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrailingStop:
    """Struktura trailing stop"""
    initial_stop: float
    current_stop: float
    highest_price: float  # dla long
    lowest_price: float   # dla short
    atr_multiplier: float
    last_liquidity_level: float
    trailing_active: bool


class DynamicTrailingStop:
    """
    Dynamiczny Trailing Stop oparty na ATR i poziomach płynności
    
    Zasady:
    - Początkowy stop: 20% od entry (dla leverage 100x)
    - Po osiągnięciu 1:1 R:R -> przesuń stop do breakeven
    - Po osiągnięciu 1:3 R:R -> trailing oparty na ATR
    - Stop zawsze tuż pod/nad ostatnim poziomem płynności
    """
    
    def __init__(self, atr_multiplier: float = 1.5):
        self.atr_multiplier = atr_multiplier
        self.active_stops: Dict[str, TrailingStop] = {}
        
    def initialize_stop(self, symbol: str, entry_price: float,
                       side: str, atr: float,
                       initial_stop_percent: float = 0.20) -> TrailingStop:
        """
        Inicjalizuj trailing stop dla pozycji
        """
        if side == 'long':
            initial_stop = entry_price * (1 - initial_stop_percent)
            highest = entry_price
            lowest = 0
        else:  # short
            initial_stop = entry_price * (1 + initial_stop_percent)
            highest = 0
            lowest = entry_price
        
        stop = TrailingStop(
            initial_stop=initial_stop,
            current_stop=initial_stop,
            highest_price=highest,
            lowest_price=lowest,
            atr_multiplier=self.atr_multiplier,
            last_liquidity_level=entry_price,
            trailing_active=False
        )
        
        self.active_stops[symbol] = stop
        logger.info(f"Initialized stop for {symbol} @ {initial_stop:.2f}")
        return stop
    
    def update_trailing_stop(self, symbol: str, current_price: float,
                            entry_price: float, side: str,
                            atr: float,
                            liquidity_levels: list = None,
                            risk_reward_achieved: float = 0) -> Dict:
        """
        Aktualizuj trailing stop dynamicznie
        
        Args:
            risk_reward_achieved: Aktualne R:R (np. 1.5 oznacza 1:1.5)
        """
        if symbol not in self.active_stops:
            return {'error': 'Stop not initialized'}
        
        stop = self.active_stops[symbol]
        old_stop = stop.current_stop
        new_stop = stop.current_stop
        stop_moved = False
        reason = ""
        
        if side == 'long':
            # Aktualizuj highest price
            if current_price > stop.highest_price:
                stop.highest_price = current_price
            
            # 1. Breakeven gdy R:R >= 1:1
            if risk_reward_achieved >= 1.0 and stop.current_stop < entry_price:
                new_stop = entry_price + (atr * 0.5)  # Breakeven + mały bufor
                reason = "Breakeven achieved (1:1 R:R)"
                stop.trailing_active = True
                stop_moved = True
            
            # 2. Trailing po 1:3 R:R
            elif risk_reward_achieved >= 3.0:
                # ATR-based trailing
                atr_based_stop = current_price - (atr * self.atr_multiplier)
                
                # Liquidity-based trailing
                if liquidity_levels:
                    # Znajdź najbliższy poziom płynności poniżej ceny
                    levels_below = [lv for lv in liquidity_levels if lv < current_price]
                    if levels_below:
                        liquidity_stop = max(levels_below)
                        new_stop = max(atr_based_stop, liquidity_stop)
                        stop.last_liquidity_level = liquidity_stop
                        reason = f"Trailing @ liquidity {liquidity_stop:.2f}"
                    else:
                        new_stop = atr_based_stop
                        reason = f"Trailing @ ATR {atr * self.atr_multiplier:.2f}"
                else:
                    new_stop = atr_based_stop
                    reason = f"Trailing @ ATR {atr * self.atr_multiplier:.2f}"
                
                # Tylko przesuń w górę
                if new_stop > stop.current_stop:
                    stop_moved = True
                else:
                    new_stop = stop.current_stop
            
            # 3. Agresywny trailing dla 1:10+ R:R
            elif risk_reward_achieved >= 10.0:
                # Bardzo wąski trailing (0.5 ATR)
                tight_stop = current_price - (atr * 0.5)
                if tight_stop > stop.current_stop:
                    new_stop = tight_stop
                    reason = "Tight trailing @ 1:10+ R:R"
                    stop_moved = True
        
        else:  # SHORT
            # Aktualizuj lowest price
            if current_price < stop.lowest_price or stop.lowest_price == 0:
                stop.lowest_price = current_price
            
            # Breakeven
            if risk_reward_achieved >= 1.0 and stop.current_stop > entry_price:
                new_stop = entry_price - (atr * 0.5)
                reason = "Breakeven achieved (1:1 R:R)"
                stop.trailing_active = True
                stop_moved = True
            
            # Trailing po 1:3
            elif risk_reward_achieved >= 3.0:
                atr_based_stop = current_price + (atr * self.atr_multiplier)
                
                if liquidity_levels:
                    levels_above = [lv for lv in liquidity_levels if lv > current_price]
                    if levels_above:
                        liquidity_stop = min(levels_above)
                        new_stop = min(atr_based_stop, liquidity_stop)
                        stop.last_liquidity_level = liquidity_stop
                        reason = f"Trailing @ liquidity {liquidity_stop:.2f}"
                    else:
                        new_stop = atr_based_stop
                        reason = f"Trailing @ ATR"
                else:
                    new_stop = atr_based_stop
                    reason = "Trailing @ ATR"
                
                # Tylko przesuń w dół
                if new_stop < stop.current_stop:
                    stop_moved = True
                else:
                    new_stop = stop.current_stop
            
            # Agresywny trailing
            elif risk_reward_achieved >= 10.0:
                tight_stop = current_price + (atr * 0.5)
                if tight_stop < stop.current_stop:
                    new_stop = tight_stop
                    reason = "Tight trailing @ 1:10+ R:R"
                    stop_moved = True
        
        # Aktualizuj stop
        if stop_moved:
            stop.current_stop = new_stop
            logger.info(f"{symbol} Stop moved: {old_stop:.2f} -> {new_stop:.2f} ({reason})")
        
        return {
            'symbol': symbol,
            'old_stop': old_stop,
            'new_stop': new_stop,
            'stop_moved': stop_moved,
            'reason': reason,
            'trailing_active': stop.trailing_active,
            'risk_reward': risk_reward_achieved
        }
    
    def check_stop_hit(self, symbol: str, current_price: float, 
                      side: str) -> bool:
        """
        Sprawdź czy stop został trafiony
        """
        if symbol not in self.active_stops:
            return False
        
        stop = self.active_stops[symbol]
        
        if side == 'long':
            return current_price <= stop.current_stop
        else:  # short
            return current_price >= stop.current_stop


class EmergencyExitSystem:
    """
    System awaryjnego wyjścia
    
    Obsługuje:
    - Utrata połączenia API
    - Ekstremalna zmienność
    - Limit drawdown
    - Czas utrzymania pozycji
    """
    
    def __init__(self, max_drawdown: float = 0.50,
                 max_position_duration_hours: int = 24,
                 extreme_volatility_threshold: float = 0.10):
        
        self.max_drawdown = max_drawdown  # 50% max loss
        self.max_position_duration = max_position_duration_hours
        self.extreme_volatility_threshold = extreme_volatility_threshold
        self.emergency_triggered = False
        
    def check_emergency_conditions(self, position: Dict,
                                   current_price: float,
                                   api_status: bool = True,
                                   current_volatility: float = 0) -> Dict:
        """
        Sprawdź warunki awaryjne
        
        Returns: Dict z decyzją i powodem
        """
        emergency = False
        reasons = []
        action = 'HOLD'
        
        # 1. API Connection Lost
        if not api_status:
            emergency = True
            reasons.append("🚨 API CONNECTION LOST!")
            action = 'MARKET_EXIT'
        
        # 2. Drawdown Limit
        entry_price = position['entry_price']
        side = position['side']
        
        if side == 'long':
            pnl_percent = (current_price - entry_price) / entry_price
        else:
            pnl_percent = (entry_price - current_price) / entry_price
        
        if pnl_percent < -self.max_drawdown:
            emergency = True
            reasons.append(f"🚨 MAX DRAWDOWN EXCEEDED! {pnl_percent*100:.1f}%")
            action = 'MARKET_EXIT'
        
        # 3. Extreme Volatility
        if current_volatility > self.extreme_volatility_threshold:
            emergency = True
            reasons.append(f"🚨 EXTREME VOLATILITY! {current_volatility*100:.1f}%")
            action = 'REDUCE_POSITION'
        
        # 4. Max Time in Position
        if 'entry_time' in position:
            time_in_position = (pd.Timestamp.now() - position['entry_time']).total_seconds() / 3600
            if time_in_position > self.max_position_duration:
                emergency = True
                reasons.append(f"⏰ Position held too long ({time_in_position:.1f}h)")
                action = 'CLOSE_POSITION'
        
        # 5. Liquidation Risk
        if 'liquidation_price' in position:
            liq_price = position['liquidation_price']
            distance_to_liq = abs(current_price - liq_price) / current_price
            
            if distance_to_liq < 0.05:  # 5% od likwidacji
                emergency = True
                reasons.append(f"🚨 LIQUIDATION RISK! ${liq_price:.0f}")
                action = 'EMERGENCY_EXIT'
        
        return {
            'emergency': emergency,
            'action': action,
            'reasons': reasons,
            'severity': 'CRITICAL' if action == 'EMERGENCY_EXIT' else 'HIGH' if emergency else 'NORMAL'
        }
    
    def execute_emergency_exit(self, position: Dict) -> Dict:
        """
        Wykonaj awaryjne wyjście z pozycji
        """
        logger.critical(f"🚨 EMERGENCY EXIT for {position['symbol']}!")
        
        # W prawdziwej implementacji:
        # 1. Zamknij pozycję MARKET ORDER
        # 2. Anuluj wszystkie pending orders
        # 3. Zapisz do logów
        # 4. Wyślij alert
        
        return {
            'status': 'executed',
            'exit_type': 'MARKET',
            'timestamp': pd.Timestamp.now(),
            'note': 'Emergency exit executed due to critical conditions'
        }


def demo_trailing_emergency():
    """Demo Trailing Stop i Emergency Exit"""
    
    print("=" * 60)
    print("🛡️ TRAILING STOP & EMERGENCY EXIT - DEMO")
    print("=" * 60)
    
    # Symulacja pozycji LONG
    entry_price = 100000  # BTC
    current_price = 110000  # +10% zysk
    atr = 2000
    
    trailing = DynamicTrailingStop(atr_multiplier=1.5)
    
    print("\n[1] INICJALIZACJA TRAILING STOP")
    print("-" * 60)
    
    stop = trailing.initialize_stop(
        symbol='BTCUSDT',
        entry_price=entry_price,
        side='long',
        atr=atr
    )
    
    print(f"Entry: ${entry_price:,.0f}")
    print(f"Initial Stop: ${stop.initial_stop:,.0f}")
    print(f"Stop Distance: {((entry_price - stop.initial_stop) / entry_price * 100):.1f}%")
    
    # Symulacja wzrostu ceny
    print("\n[2] SYMULACJA RUCHU CENY")
    print("-" * 60)
    
    price_scenarios = [
        (102000, 1.0, "1:1 R:R - Breakeven"),
        (106000, 3.0, "1:3 R:R - Start Trailing"),
        (110000, 5.0, "1:5 R:R - Active Trailing"),
        (120000, 10.0, "1:10 R:R - Tight Trailing"),
    ]
    
    for price, rr, desc in price_scenarios:
        update = trailing.update_trailing_stop(
            symbol='BTCUSDT',
            current_price=price,
            entry_price=entry_price,
            side='long',
            atr=atr,
            risk_reward_achieved=rr
        )
        
        print(f"\n{desc}")
        print(f"  Price: ${price:,.0f}")
        print(f"  Stop: ${update['new_stop']:,.0f}")
        if update['stop_moved']:
            print(f"  ✅ {update['reason']}")
    
    # Emergency System
    print("\n[3] EMERGENCY EXIT SYSTEM")
    print("-" * 60)
    
    emergency = EmergencyExitSystem()
    
    position = {
        'symbol': 'BTCUSDT',
        'side': 'long',
        'entry_price': entry_price,
        'liquidation_price': 80000,
        'entry_time': pd.Timestamp.now() - pd.Timedelta(hours=25)
    }
    
    # Scenariusz 1: Normalna sytuacja
    check1 = emergency.check_emergency_conditions(
        position=position,
        current_price=110000,
        api_status=True,
        current_volatility=0.02
    )
    
    print(f"\nScenariusz 1: Normalna sytuacja")
    print(f"  Emergency: {check1['emergency']}")
    print(f"  Action: {check1['action']}")
    
    # Scenariusz 2: Utrata połączenia
    check2 = emergency.check_emergency_conditions(
        position=position,
        current_price=110000,
        api_status=False
    )
    
    print(f"\nScenariusz 2: Utrata API")
    print(f"  Emergency: {check2['emergency']}")
    print(f"  Action: {check2['action']}")
    print(f"  Reasons: {', '.join(check2['reasons'])}")
    
    # Scenariusz 3: Blisko likwidacji
    check3 = emergency.check_emergency_conditions(
        position=position,
        current_price=82000,  # Blisko likwidacji!
        api_status=True
    )
    
    print(f"\nScenariusz 3: Ryzyko likwidacji")
    print(f"  Emergency: {check3['emergency']}")
    print(f"  Severity: {check3['severity']}")
    print(f"  Reasons: {', '.join(check3['reasons'])}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_trailing_emergency()
