#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Risk Management - Zarządzanie Ryzykiem z Leverage 100x
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class Position:
    """Struktura pozycji"""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    leverage: int
    margin: float
    liquidation_price: float
    stop_loss: float = None
    take_profit: float = None


class RiskManager:
    """
    Zarządzanie Ryzykiem
    - Leverage: 100x
    - Max risk per trade: 20%
    - Pyramiding: max 5 pozycji
    """
    
    def __init__(self, account_balance: float = 5000, 
                 max_leverage: int = 100,
                 max_risk_percent: float = 20.0):
        self.account_balance = account_balance
        self.max_leverage = max_leverage
        self.max_risk_percent = max_risk_percent
        self.positions: Dict[str, Position] = {}
        
    def calculate_position_size(self, entry_price: float, 
                                stop_loss_price: float,
                                risk_amount: float = 250,
                                leverage: int = 100) -> Dict:
        """
        Oblicz wielkość pozycji z uwzględnieniem leverage
        
        Przykład:
        - Depozyt: 5000 USD
        - Ryzyko na transakcję: 250 USD (5%)
        - Leverage: 100x
        - Stop loss: 20% od entry
        
        Returns: Dict z szczegółami pozycji
        """
        # Bezpieczny stop loss (min 20% od ceny dla BTC z leverage 100x)
        stop_distance_percent = abs(entry_price - stop_loss_price) / entry_price
        
        if stop_distance_percent < 0.20:
            print(f"⚠️ OSTRZEŻENIE: Stop loss zbyt blisko dla leverage {leverage}x!")
            stop_distance_percent = 0.20
            stop_loss_price = entry_price * (1 - 0.20) if stop_loss_price < entry_price else entry_price * (1 + 0.20)
        
        # Margin wymagany
        margin = risk_amount
        
        # Wielkość pozycji z leverage
        position_value = margin * leverage
        
        # Ilość kontraktów/monet
        quantity = position_value / entry_price
        
        # Cena likwidacji (przybliżona)
        # Long: liquidation = entry - (margin / quantity)
        # Short: liquidation = entry + (margin / quantity)
        liquidation_price = entry_price - (margin / quantity)
        
        # Potencjalny zysk przy różnych scenariuszach
        profit_scenarios = {
            '1%': (entry_price * 1.01 - entry_price) * quantity,
            '5%': (entry_price * 1.05 - entry_price) * quantity,
            '10%': (entry_price * 1.10 - entry_price) * quantity,
            '100%': (entry_price * 2.0 - entry_price) * quantity,
        }
        
        return {
            'margin': margin,
            'leverage': leverage,
            'position_value': position_value,
            'quantity': quantity,
            'entry_price': entry_price,
            'stop_loss': stop_loss_price,
            'liquidation_price': liquidation_price,
            'risk_reward_ratio': profit_scenarios['10%'] / margin,
            'profit_scenarios': profit_scenarios,
            'max_loss': margin  # Maksymalna strata = margin
        }
    
    def pyramiding_strategy(self, base_entry: float, 
                           num_entries: int = 5,
                           total_risk: float = 250,
                           leverage: int = 100) -> list:
        """
        Strategia piramidowania - 5 doładek po $50
        
        Przykład:
        - Total risk: $250
        - 5 pozycji po $50 każda
        - Leverage: 100x na każdą
        
        Returns: Lista pozycji do otwarcia
        """
        position_size = total_risk / num_entries  # $50 per position
        
        positions = []
        for i in range(num_entries):
            # Każda następna pozycja z małym przesunięciem (0.5%)
            entry_price = base_entry * (1 - (i * 0.005))  # -0.5% za każdą pozycję
            
            pos = self.calculate_position_size(
                entry_price=entry_price,
                stop_loss_price=entry_price * 0.80,  # 20% stop
                risk_amount=position_size,
                leverage=leverage
            )
            
            positions.append({
                'entry': i + 1,
                'entry_price': entry_price,
                'margin': position_size,
                'quantity': pos['quantity'],
                'position_value': pos['position_value'],
                'liquidation': pos['liquidation_price']
            })
        
        return positions
    
    def calculate_liquidation_price(self, entry_price: float, 
                                   margin: float, 
                                   quantity: float,
                                   side: str = 'long') -> float:
        """
        Oblicz cenę likwidacji
        
        Formula:
        Long: Liq Price = Entry - (Margin / Quantity)
        Short: Liq Price = Entry + (Margin / Quantity)
        """
        if side == 'long':
            return entry_price - (margin / quantity)
        else:  # short
            return entry_price + (margin / quantity)
    
    def calculate_take_profit_levels(self, entry_price: float,
                                    side: str = 'long',
                                    risk_reward_ratios: list = [3, 5, 10]) -> Dict:
        """
        Oblicz poziomy Take Profit
        
        Minimum 1:3 (Risk:Reward)
        Preferowane: 1:10 w silnym trendzie
        """
        stop_distance = entry_price * 0.20  # 20% stop
        
        tp_levels = {}
        for ratio in risk_reward_ratios:
            if side == 'long':
                tp_price = entry_price + (stop_distance * ratio)
            else:  # short
                tp_price = entry_price - (stop_distance * ratio)
            
            tp_levels[f'TP_{ratio}'] = {
                'price': tp_price,
                'gain_percent': ((tp_price - entry_price) / entry_price) * 100,
                'risk_reward': ratio
            }
        
        return tp_levels
    
    def open_position(self, symbol: str, side: str, 
                     entry_price: float, quantity: float,
                     leverage: int, margin: float,
                     stop_loss: float = None,
                     take_profit: float = None) -> Position:
        """Otwórz nową pozycję"""
        
        liquidation_price = self.calculate_liquidation_price(
            entry_price, margin, quantity, side
        )
        
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            leverage=leverage,
            margin=margin,
            liquidation_price=liquidation_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[symbol] = position
        self.account_balance -= margin
        
        return position
    
    def close_position(self, symbol: str, exit_price: float) -> Dict:
        """Zamknij pozycję i oblicz P&L"""
        if symbol not in self.positions:
            return {'error': 'Position not found'}
        
        position = self.positions[symbol]
        
        # Oblicz P&L
        if position.side == 'long':
            pnl = (exit_price - position.entry_price) * position.quantity
        else:  # short
            pnl = (position.entry_price - exit_price) * position.quantity
        
        # Zwróć margin + profit
        self.account_balance += position.margin + pnl
        
        # Usuń pozycję
        del self.positions[symbol]
        
        return {
            'symbol': symbol,
            'side': position.side,
            'entry': position.entry_price,
            'exit': exit_price,
            'quantity': position.quantity,
            'pnl': pnl,
            'pnl_percent': (pnl / position.margin) * 100,
            'new_balance': self.account_balance
        }
    
    def get_portfolio_status(self) -> Dict:
        """Status całego portfela"""
        total_margin_used = sum(pos.margin for pos in self.positions.values())
        available_balance = self.account_balance
        total_balance = available_balance + total_margin_used
        
        return {
            'total_balance': total_balance,
            'available_balance': available_balance,
            'margin_used': total_margin_used,
            'margin_used_percent': (total_margin_used / total_balance) * 100,
            'num_positions': len(self.positions),
            'positions': {k: vars(v) for k, v in self.positions.items()}
        }


class ScalpingManager:
    """Manager dla szybkich scalp'ów 5-minutowych"""
    
    def __init__(self, risk_per_scalp: float = 50):
        self.risk_per_scalp = risk_per_scalp
        self.scalp_count = 0
        self.winning_scalps = 0
        self.losing_scalps = 0
        
    def quick_scalp_setup(self, current_price: float, 
                         direction: str = 'long') -> Dict:
        """
        Szybki setup dla scalp 5-min
        
        Target: 0.5-1% zysk
        Stop: 0.3% strata
        """
        if direction == 'long':
            entry = current_price
            take_profit = current_price * 1.01  # 1% zysk
            stop_loss = current_price * 0.997   # 0.3% stop
        else:  # short
            entry = current_price
            take_profit = current_price * 0.99  # 1% zysk
            stop_loss = current_price * 1.003   # 0.3% stop
        
        return {
            'entry': entry,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'risk_amount': self.risk_per_scalp,
            'target_profit': self.risk_per_scalp * 3,  # 1:3 R:R minimum
            'timeframe': '5min'
        }
