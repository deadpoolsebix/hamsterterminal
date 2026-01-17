"""
💰 FUNDING RATE CALCULATOR
Oblicza funding rate dla pozycji w kryptowalutach
Uwzględnia: koszt pozycji, czas holdowania, realne rynkowe opłaty
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class FundingRateCalculator:
    """
    Kalkulator funding rate dla pozycji na kontraktach perpetual futures
    """
    
    def __init__(self):
        # Średnie funding raty z głównych giełd
        self.exchange_rates = {
            'binance': 0.0001,      # 0.01% average
            'bybit': 0.00005,       # 0.005% average
            'okx': 0.0001,          # 0.01% average
            'dydx': 0.00015,        # 0.015% average
            'hyperliquid': 0.0002,  # 0.02% average
        }
        
        # Risk premium - zależy od volatilności
        self.volatility_multipliers = {
            'low': 0.5,      # volatility < 20%
            'medium': 1.0,   # volatility 20-50%
            'high': 1.5,     # volatility 50-100%
            'extreme': 2.5   # volatility > 100%
        }
        
    def estimate_daily_funding_rate(self, exchange: str = 'binance', 
                                   volatility_level: str = 'medium') -> float:
        """
        Szacuj dzienny funding rate
        
        Args:
            exchange: nazwa giełdy
            volatility_level: level volatilności (low, medium, high, extreme)
        
        Returns:
            Dzienny funding rate jako ułamek (0.0001 = 0.01%)
        """
        base_rate = self.exchange_rates.get(exchange, 0.0001)
        multiplier = self.volatility_multipliers.get(volatility_level, 1.0)
        
        return base_rate * multiplier
    
    def calculate_funding_cost_position(
        self,
        position_size_usdt: float,
        entry_price: float,
        exit_price: float,
        entry_time: datetime,
        exit_time: datetime,
        position_type: str = 'LONG',
        exchange: str = 'binance',
        leverage: int = 1,
        volatility_level: str = 'medium'
    ) -> Dict:
        """
        Oblicz kompletny koszt finansowania dla pozycji
        
        Args:
            position_size_usdt: wielkość pozycji w USDT
            entry_price: cena wejścia
            exit_price: cena wyjścia
            entry_time: czas wejścia w pozycję
            exit_time: czas wyjścia z pozycji
            position_type: 'LONG' lub 'SHORT'
            exchange: giełda (binance, bybit, etc)
            leverage: leverage użyty (1-125)
            volatility_level: level volatilności
        
        Returns:
            Dict z całością kosztów i profitów
        """
        
        # Wylicz hold time w godzinach
        hold_duration = exit_time - entry_time
        hold_hours = hold_duration.total_seconds() / 3600
        hold_days = hold_hours / 24
        
        # Wylicz ilość coina (dla BTC, ETH, etc)
        position_quantity = position_size_usdt / entry_price
        
        # Wylicz funding rate
        daily_funding_rate = self.estimate_daily_funding_rate(exchange, volatility_level)
        
        # Dla SHORT pozycji funding rate jest zwykle negatywny
        if position_type == 'SHORT':
            daily_funding_rate *= -1
        
        # Wylicz funding cost
        funding_hours_rate = daily_funding_rate / 24
        funding_cost = position_size_usdt * funding_hours_rate * hold_hours
        
        # Fees (maker/taker)
        maker_fee = 0.0002  # 0.02%
        taker_fee = 0.0004  # 0.04%
        entry_fee = position_size_usdt * taker_fee
        exit_fee = position_size_usdt * taker_fee
        total_fees = entry_fee + exit_fee
        
        # Oblicz P&L
        if position_type == 'LONG':
            pnl = (exit_price - entry_price) * position_quantity
        else:  # SHORT
            pnl = (entry_price - exit_price) * position_quantity
        
        # ROI
        roi = (pnl - total_fees - funding_cost) / (position_size_usdt / leverage) * 100
        
        return {
            'position_size_usdt': position_size_usdt,
            'quantity_coins': round(position_quantity, 8),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_type': position_type,
            'leverage': leverage,
            'hold_time_hours': round(hold_hours, 2),
            'hold_time_days': round(hold_days, 4),
            'daily_funding_rate': daily_funding_rate,
            'funding_hours_rate': funding_hours_rate,
            'total_funding_cost': round(funding_cost, 2),
            'entry_fee': round(entry_fee, 2),
            'exit_fee': round(exit_fee, 2),
            'total_fees': round(total_fees, 2),
            'pnl_gross': round(pnl, 2),
            'pnl_net': round(pnl - total_fees - funding_cost, 2),
            'roi_percent': round(roi, 2),
            'exchange': exchange,
            'volatility_level': volatility_level,
            'calculation_datetime': datetime.now()
        }
    
    def calculate_funding_break_even(
        self,
        position_size_usdt: float,
        entry_price: float,
        position_type: str = 'LONG',
        leverage: int = 1,
        exchange: str = 'binance',
        volatility_level: str = 'medium',
        hold_hours: float = 1.0
    ) -> Dict:
        """
        Oblicz break-even point dla pozycji (cena która pokryje fees i funding)
        
        Args:
            position_size_usdt: wielkość pozycji
            entry_price: cena wejścia
            position_type: LONG lub SHORT
            leverage: leverage
            exchange: giełda
            volatility_level: level volatilności
            hold_hours: szacunkowy czas holdowania
        
        Returns:
            Dict z break-even ceną i informacjami
        """
        
        position_quantity = position_size_usdt / entry_price
        
        # Fees
        taker_fee = 0.0004
        entry_fee = position_size_usdt * taker_fee
        exit_fee = position_size_usdt * taker_fee
        total_fees = entry_fee + exit_fee
        
        # Funding cost
        daily_funding_rate = self.estimate_daily_funding_rate(exchange, volatility_level)
        funding_hours_rate = daily_funding_rate / 24
        funding_cost = position_size_usdt * funding_hours_rate * hold_hours
        
        # Total cost to recover
        total_cost = total_fees + funding_cost
        cost_per_coin = total_cost / position_quantity
        
        # Break-even price
        if position_type == 'LONG':
            break_even_price = entry_price + cost_per_coin
        else:  # SHORT
            break_even_price = entry_price - cost_per_coin
        
        # Oblicz ile % trzeba ruchu do break-even
        price_diff = abs(break_even_price - entry_price)
        price_move_percent = (price_diff / entry_price) * 100
        
        return {
            'entry_price': entry_price,
            'break_even_price': round(break_even_price, 2),
            'price_difference': round(price_diff, 2),
            'move_needed_percent': round(price_move_percent, 4),
            'total_fees': round(total_fees, 2),
            'funding_cost': round(funding_cost, 2),
            'total_cost_to_recover': round(total_cost, 2),
            'position_type': position_type,
            'hold_hours': hold_hours
        }
    
    def calculate_position_analysis(
        self,
        symbol: str,
        position_size_usdt: float,
        entry_price: float,
        current_price: float,
        position_type: str = 'LONG',
        leverage: int = 1,
        entry_time: datetime = None,
        exchange: str = 'binance',
        volatility_level: str = 'medium',
        coin_name: str = 'BTC'
    ) -> Dict:
        """
        Kompleksowa analiza pozycji - aktualne stany
        
        Args:
            symbol: symbol (BTCUSDT, ETHUSDT, etc)
            position_size_usdt: wielkość pozycji
            entry_price: cena wejścia
            current_price: aktualna cena
            position_type: LONG lub SHORT
            leverage: leverage
            entry_time: czas wejścia
            exchange: giełda
            volatility_level: level volatilności
            coin_name: nazwa coina (BTC, ETH, etc)
        
        Returns:
            Kompletna analiza pozycji
        """
        
        if entry_time is None:
            entry_time = datetime.now()
        
        current_time = datetime.now()
        hold_duration = current_time - entry_time
        hold_hours = hold_duration.total_seconds() / 3600
        
        # Ilość coina
        coin_quantity = position_size_usdt / entry_price
        
        # Aktualna P&L
        if position_type == 'LONG':
            unrealized_pnl = (current_price - entry_price) * coin_quantity
        else:  # SHORT
            unrealized_pnl = (entry_price - current_price) * coin_quantity
        
        # Funding cost
        daily_funding_rate = self.estimate_daily_funding_rate(exchange, volatility_level)
        if position_type == 'SHORT':
            daily_funding_rate *= -1
        funding_hours_rate = daily_funding_rate / 24
        accumulated_funding_cost = position_size_usdt * funding_hours_rate * hold_hours
        
        # Fees zapłacone (only entry fee za teraz)
        taker_fee = 0.0004
        entry_fee = position_size_usdt * taker_fee
        
        # Szacunkowa fee przy wyjściu
        exit_fee_estimate = position_size_usdt * taker_fee
        
        # Net P&L
        net_pnl = unrealized_pnl - accumulated_funding_cost - entry_fee
        
        # ROI
        roi = (net_pnl / (position_size_usdt / leverage)) * 100
        
        # Liquidation price
        if position_type == 'LONG':
            liquidation_price = entry_price * (1 - (1 / leverage))
        else:  # SHORT
            liquidation_price = entry_price * (1 + (1 / leverage))
        
        # Distance to liquidation
        distance_to_liquidation = abs(current_price - liquidation_price)
        distance_percent = (distance_to_liquidation / current_price) * 100
        
        # Break-even analysis
        break_even_data = self.calculate_funding_break_even(
            position_size_usdt, entry_price, position_type, 
            leverage, exchange, volatility_level, hold_hours
        )
        
        return {
            'symbol': symbol,
            'coin_name': coin_name,
            'position_type': position_type,
            'position_size_usdt': position_size_usdt,
            'coin_quantity': round(coin_quantity, 8),
            'leverage': leverage,
            'entry_price': entry_price,
            'current_price': current_price,
            'price_move': round(current_price - entry_price, 2),
            'price_move_percent': round(((current_price - entry_price) / entry_price) * 100, 4),
            'hold_hours': round(hold_hours, 2),
            'hold_days': round(hold_hours / 24, 4),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'accumulated_funding_cost': round(accumulated_funding_cost, 2),
            'entry_fee': round(entry_fee, 2),
            'exit_fee_estimate': round(exit_fee_estimate, 2),
            'net_pnl_current': round(net_pnl, 2),
            'roi_percent': round(roi, 2),
            'daily_funding_rate': round(daily_funding_rate * 100, 4),  # as %
            'exchange': exchange,
            'volatility_level': volatility_level,
            'liquidation_price': round(liquidation_price, 2),
            'distance_to_liquidation': round(distance_to_liquidation, 2),
            'distance_to_liquidation_percent': round(distance_percent, 2),
            'break_even_price': break_even_data['break_even_price'],
            'timestamp': current_time
        }
    
    def simulate_position_scenarios(
        self,
        position_size_usdt: float,
        entry_price: float,
        position_type: str = 'LONG',
        leverage: int = 1,
        hold_hours: float = 8.0,
        exchange: str = 'binance',
        volatility_level: str = 'medium',
        price_scenarios: List[float] = None
    ) -> Dict:
        """
        Symuluj pozycję dla różnych scenariuszy ceny
        
        Args:
            position_size_usdt: wielkość pozycji
            entry_price: cena wejścia
            position_type: LONG lub SHORT
            leverage: leverage
            hold_hours: czas holdowania
            exchange: giełda
            volatility_level: level volatilności
            price_scenarios: lista cen do przetestowania
        
        Returns:
            Scenariusze P&L
        """
        
        if price_scenarios is None:
            # Default scenarios: -5%, -2%, -1%, 0%, +1%, +2%, +5%, +10%
            price_scenarios = [
                entry_price * (1 - 0.05),
                entry_price * (1 - 0.02),
                entry_price * (1 - 0.01),
                entry_price,
                entry_price * (1 + 0.01),
                entry_price * (1 + 0.02),
                entry_price * (1 + 0.05),
                entry_price * (1 + 0.10),
            ]
        
        coin_quantity = position_size_usdt / entry_price
        
        # Funding cost
        daily_funding_rate = self.estimate_daily_funding_rate(exchange, volatility_level)
        if position_type == 'SHORT':
            daily_funding_rate *= -1
        funding_hours_rate = daily_funding_rate / 24
        funding_cost = position_size_usdt * funding_hours_rate * hold_hours
        
        # Fees
        taker_fee = 0.0004
        total_fees = position_size_usdt * taker_fee * 2
        
        scenarios = []
        for price in price_scenarios:
            if position_type == 'LONG':
                pnl = (price - entry_price) * coin_quantity
            else:  # SHORT
                pnl = (entry_price - price) * coin_quantity
            
            net_pnl = pnl - total_fees - funding_cost
            roi = (net_pnl / (position_size_usdt / leverage)) * 100
            
            scenarios.append({
                'exit_price': round(price, 2),
                'price_move_percent': round(((price - entry_price) / entry_price) * 100, 2),
                'gross_pnl': round(pnl, 2),
                'fees': round(total_fees, 2),
                'funding_cost': round(funding_cost, 2),
                'net_pnl': round(net_pnl, 2),
                'roi_percent': round(roi, 2),
                'profitable': net_pnl > 0
            })
        
        return {
            'entry_price': entry_price,
            'position_type': position_type,
            'hold_hours': hold_hours,
            'leverage': leverage,
            'daily_funding_rate': round(daily_funding_rate * 100, 4),
            'scenarios': scenarios
        }
    
    def print_position_report(self, position_data: Dict):
        """
        Wydrukuj szczegółowy raport pozycji
        """
        print("\n" + "="*80)
        print("📊 POSITION ANALYSIS REPORT")
        print("="*80)
        
        print(f"\n🎯 POSITION INFO:")
        print(f"   Symbol: {position_data.get('symbol', 'N/A')}")
        print(f"   Type: {position_data.get('position_type', 'N/A')}")
        print(f"   Size: ${position_data.get('position_size_usdt', 0):,.2f}")
        print(f"   Quantity: {position_data.get('coin_quantity', 0):.8f}")
        print(f"   Leverage: {position_data.get('leverage', 1)}x")
        
        print(f"\n💰 PRICE INFO:")
        print(f"   Entry Price: ${position_data.get('entry_price', 0):,.2f}")
        print(f"   Current Price: ${position_data.get('current_price', 0):,.2f}")
        print(f"   Price Move: ${position_data.get('price_move', 0):,.2f} ({position_data.get('price_move_percent', 0):.2f}%)")
        
        print(f"\n⏱️  TIME INFO:")
        print(f"   Hold Time: {position_data.get('hold_hours', 0):.2f}h ({position_data.get('hold_days', 0):.4f}d)")
        
        print(f"\n📈 P&L INFO:")
        print(f"   Unrealized P&L: ${position_data.get('unrealized_pnl', 0):,.2f}")
        print(f"   Funding Cost: ${position_data.get('accumulated_funding_cost', 0):,.2f}")
        print(f"   Entry Fee: ${position_data.get('entry_fee', 0):,.2f}")
        print(f"   Exit Fee (est): ${position_data.get('exit_fee_estimate', 0):,.2f}")
        print(f"   Net P&L: ${position_data.get('net_pnl_current', 0):,.2f}")
        print(f"   ROI: {position_data.get('roi_percent', 0):.2f}%")
        
        print(f"\n⚠️  RISK INFO:")
        print(f"   Daily Funding Rate: {position_data.get('daily_funding_rate', 0):.4f}%")
        print(f"   Liquidation Price: ${position_data.get('liquidation_price', 0):,.2f}")
        print(f"   Distance to Liquidation: ${position_data.get('distance_to_liquidation', 0):,.2f} ({position_data.get('distance_to_liquidation_percent', 0):.2f}%)")
        print(f"   Break-Even Price: ${position_data.get('break_even_price', 0):,.2f}")
        
        print("\n" + "="*80)


# Example usage
if __name__ == "__main__":
    calculator = FundingRateCalculator()
    
    # Test 1: Calculate position cost
    print("\n[1] POSITION COST CALCULATION")
    entry_time = datetime.now() - timedelta(hours=2)
    exit_time = datetime.now()
    
    position = calculator.calculate_funding_cost_position(
        position_size_usdt=5000,
        entry_price=95000,
        exit_price=96000,
        entry_time=entry_time,
        exit_time=exit_time,
        position_type='LONG',
        leverage=10,
        exchange='binance',
        volatility_level='medium'
    )
    
    print(f"\nPosition Size: ${position['position_size_usdt']:,}")
    print(f"Quantity: {position['quantity_coins']:.8f} BTC")
    print(f"Hold Time: {position['hold_time_hours']:.2f} hours")
    print(f"Funding Cost: ${position['total_funding_cost']:.2f}")
    print(f"Total Fees: ${position['total_fees']:.2f}")
    print(f"Gross P&L: ${position['pnl_gross']:.2f}")
    print(f"Net P&L: ${position['pnl_net']:.2f}")
    print(f"ROI: {position['roi_percent']:.2f}%")
    
    # Test 2: Break-even analysis
    print("\n[2] BREAK-EVEN ANALYSIS")
    break_even = calculator.calculate_funding_break_even(
        position_size_usdt=5000,
        entry_price=95000,
        position_type='LONG',
        leverage=10,
        hold_hours=2
    )
    
    print(f"\nEntry Price: ${break_even['entry_price']:,}")
    print(f"Break-Even Price: ${break_even['break_even_price']:,}")
    print(f"Price Move Needed: {break_even['move_needed_percent']:.4f}%")
    print(f"Total Cost to Recover: ${break_even['total_cost_to_recover']:.2f}")
    
    # Test 3: Current position analysis
    print("\n[3] CURRENT POSITION ANALYSIS")
    analysis = calculator.calculate_position_analysis(
        symbol='BTCUSDT',
        position_size_usdt=5000,
        entry_price=95000,
        current_price=96200,
        position_type='LONG',
        leverage=10,
        exchange='binance',
        coin_name='BTC'
    )
    
    calculator.print_position_report(analysis)
    
    # Test 4: Position scenarios
    print("\n[4] PRICE SCENARIOS")
    scenarios = calculator.simulate_position_scenarios(
        position_size_usdt=5000,
        entry_price=95000,
        position_type='LONG',
        leverage=10,
        hold_hours=8
    )
    
    print(f"\nEntry Price: ${scenarios['entry_price']:,}")
    print(f"Daily Funding Rate: {scenarios['daily_funding_rate']:.4f}%\n")
    print(f"{'Exit Price':<15} {'Move %':<12} {'Gross P&L':<15} {'Fees':<10} {'Funding':<10} {'Net P&L':<15} {'ROI %':<10}")
    print("-" * 110)
    
    for scenario in scenarios['scenarios']:
        print(f"${scenario['exit_price']:<14.2f} {scenario['price_move_percent']:>10.2f}% ${scenario['gross_pnl']:<14.2f} ${scenario['fees']:<9.2f} ${scenario['funding_cost']:<9.2f} ${scenario['net_pnl']:<14.2f} {scenario['roi_percent']:>8.2f}%")
