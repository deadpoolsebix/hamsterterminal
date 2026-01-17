#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fees & Slippage Management
Obsługuje prowizje i poślizg cenowy w kalkulacji P&L
"""

import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeesAndSlippageManager:
    """
    Zarządzanie prowizjami i poślizgiem
    
    Ważne: Przy 5 dokładkach i scalpie 5-minutowym,
    prowizje mogą zjadać zysk!
    """
    
    def __init__(
        self,
        maker_fee: float = 0.0001,  # 0.01% maker (Binance)
        taker_fee: float = 0.0002,  # 0.02% taker (Binance)
        max_slippage_pct: float = 0.1  # Max 0.1% slippage
    ):
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.max_slippage = max_slippage_pct / 100
        
        logger.info(f"Fees configured: Maker {maker_fee*100:.3f}%, Taker {taker_fee*100:.3f}%")
        logger.info(f"Max slippage allowed: {max_slippage_pct:.2f}%")
    
    def calculate_entry_cost(
        self,
        quantity: float,
        entry_price: float,
        is_maker: bool = False
    ) -> Dict:
        """
        Oblicz całkowity koszt wejścia (z prowizją)
        """
        fee = self.maker_fee if is_maker else self.taker_fee
        position_value = quantity * entry_price
        fee_amount = position_value * fee
        total_cost = position_value + fee_amount
        
        return {
            'position_value': position_value,
            'fee_amount': fee_amount,
            'total_cost': total_cost,
            'fee_pct': fee * 100
        }
    
    def calculate_exit_proceeds(
        self,
        quantity: float,
        exit_price: float,
        is_maker: bool = False
    ) -> Dict:
        """
        Oblicz przychód z wyjścia (minus prowizja)
        """
        fee = self.maker_fee if is_maker else self.taker_fee
        position_value = quantity * exit_price
        fee_amount = position_value * fee
        net_proceeds = position_value - fee_amount
        
        return {
            'position_value': position_value,
            'fee_amount': fee_amount,
            'net_proceeds': net_proceeds,
            'fee_pct': fee * 100
        }
    
    def calculate_true_pnl(
        self,
        entry_price: float,
        exit_price: float,
        quantity: float,
        leverage: int = 1,
        is_maker_entry: bool = False,
        is_maker_exit: bool = False,
        slippage_realized: float = 0.0
    ) -> Dict:
        """
        Oblicz PRAWDZIWY P&L z uwzględnieniem:
        - Prowizji wejścia
        - Prowizji wyjścia
        - Realized slippage
        - Leverage
        """
        # Entry
        entry = self.calculate_entry_cost(quantity, entry_price, is_maker_entry)
        
        # Exit
        exit_with_slippage = exit_price * (1 - slippage_realized)
        exit_calc = self.calculate_exit_proceeds(quantity, exit_with_slippage, is_maker_exit)
        
        # Net P&L
        gross_pnl = exit_calc['net_proceeds'] - entry['position_value']
        total_fees = entry['fee_amount'] + exit_calc['fee_amount']
        net_pnl = gross_pnl - (total_fees / leverage)  # Fees don't scale with leverage
        
        pnl_pct = (net_pnl / (entry['position_value'] / leverage)) * 100
        
        return {
            'entry_cost': entry,
            'exit_proceeds': exit_calc,
            'gross_pnl': gross_pnl,
            'total_fees': total_fees,
            'net_pnl': net_pnl,
            'pnl_pct': pnl_pct,
            'slippage_cost': entry['position_value'] * slippage_realized,
            'breakeven_price': entry_price * (1 + (total_fees / entry['position_value']))
        }
    
    def calculate_target_price_with_fees(
        self,
        entry_price: float,
        target_pnl_pct: float,
        quantity: float,
        leverage: int = 1,
        is_maker: bool = True
    ) -> float:
        """
        Oblicz cenę Target uwzględniając prowizje
        
        Przykład:
        - Entry: $50,000
        - Chcę 1% netto P&L
        - Z prowizjami: muszę wyjść wyżej!
        """
        entry = self.calculate_entry_cost(quantity, entry_price, is_maker)
        
        # Prowizja wyjścia (zakładaj maker)
        exit_fee = self.maker_fee if is_maker else self.taker_fee
        
        # Reverse calculation
        # net_pnl = (exit_price * quantity * (1 - exit_fee)) - entry['total_cost']
        # Rozwiązując dla exit_price:
        
        position_value = quantity * entry_price
        target_profit = position_value * (target_pnl_pct / 100) * leverage
        
        # exit_price * quantity * (1 - exit_fee) = position_value + target_profit + entry_fee
        numerator = position_value + target_profit + entry['fee_amount']
        denominator = quantity * (1 - exit_fee)
        
        target_price = numerator / denominator
        
        # Verify
        verify = self.calculate_true_pnl(
            entry_price, target_price, quantity, leverage, 
            is_maker, is_maker
        )
        
        logger.info(f"Target price calculated: ${target_price:,.2f}")
        logger.info(f"Verification - Net P&L: {verify['pnl_pct']:.2f}%")
        
        return target_price
    
    def check_slippage_acceptable(
        self,
        intended_price: float,
        actual_price: float
    ) -> Dict:
        """
        Sprawdź czy slippage jest zaakceptowalny
        """
        slippage_pct = abs(actual_price - intended_price) / intended_price
        
        acceptable = slippage_pct <= self.max_slippage
        
        logger.warning(f"Slippage: {slippage_pct*100:.3f}% {'✅ OK' if acceptable else '❌ TOO HIGH'}")
        
        return {
            'slippage_pct': slippage_pct,
            'acceptable': acceptable,
            'intended_price': intended_price,
            'actual_price': actual_price,
            'loss_on_slippage': intended_price * slippage_pct
        }
    
    def get_breakeven_analysis(
        self,
        entry_price: float,
        position_size: float,
        leverage: int = 100,
        is_maker: bool = True
    ) -> Dict:
        """
        Analiza breakeven - ile muszę zarobić, aby wyjść na zero?
        """
        total_cost = self.calculate_entry_cost(position_size, entry_price, is_maker)
        exit_cost = self.calculate_exit_proceeds(position_size, entry_price, is_maker)
        
        total_fees = total_cost['fee_amount'] + (total_cost['position_value'] - exit_cost['net_proceeds'])
        
        # Break-even price
        required_profit = total_fees
        required_pct = (required_profit / total_cost['position_value']) * 100
        breakeven_price = entry_price + (entry_price * required_pct / 100)
        
        logger.info(f"Breakeven Price: ${breakeven_price:,.2f}")
        logger.info(f"Need to move: +{required_pct:.3f}% just for fees")
        
        return {
            'entry_price': entry_price,
            'breakeven_price': breakeven_price,
            'required_move_pct': required_pct,
            'total_fees': total_fees,
            'note': f'Pay attention: You need {required_pct:.3f}% gain just to break even on fees!'
        }


def demo_fees_slippage():
    """Demo: Fees i slippage impact"""
    
    print("\n" + "="*70)
    print("💰 FEES & SLIPPAGE ANALYSIS")
    print("="*70)
    
    manager = FeesAndSlippageManager(
        maker_fee=0.0001,  # 0.01%
        taker_fee=0.0002,  # 0.02%
        max_slippage_pct=0.1  # 0.1%
    )
    
    # Scenario: Entry BTC @ $50,000
    entry_price = 50000
    quantity = 0.1  # 0.1 BTC
    leverage = 100
    
    print(f"\n📊 SCENARIO: Long 0.1 BTC @ ${entry_price:,.0f} with {leverage}x leverage")
    print(f"   Position value: ${entry_price * quantity:,.0f}")
    print(f"   With leverage: ${entry_price * quantity * leverage:,.0f}")
    
    # 1. Entry cost analysis
    print("\n1️⃣ ENTRY COST (as taker):")
    entry_calc = manager.calculate_entry_cost(quantity, entry_price, is_maker=False)
    print(f"   Position value: ${entry_calc['position_value']:,.2f}")
    print(f"   Fee (0.02%): ${entry_calc['fee_amount']:.2f}")
    print(f"   Total cost: ${entry_calc['total_cost']:,.2f}")
    
    # 2. Breakeven analysis
    print("\n2️⃣ BREAKEVEN ANALYSIS:")
    be = manager.get_breakeven_analysis(entry_price, quantity, leverage, is_maker=False)
    print(f"   Breakeven price: ${be['breakeven_price']:,.2f}")
    print(f"   ⚠️ {be['note']}")
    
    # 3. Target price calculation (want 1% net profit)
    print("\n3️⃣ TARGET PRICE (want 1% net profit):")
    target = manager.calculate_target_price_with_fees(
        entry_price, target_pnl_pct=1.0, quantity=quantity, 
        leverage=leverage, is_maker=True
    )
    print(f"   Need to exit @ ${target:,.2f} for 1% net profit")
    
    # 4. Verify with true P&L calculation
    print("\n4️⃣ TRUE P&L CALCULATION:")
    exit_price = target
    pnl = manager.calculate_true_pnl(
        entry_price, exit_price, quantity, leverage,
        is_maker_entry=False, is_maker_exit=True
    )
    print(f"   Entry price: ${entry_price:,.0f}")
    print(f"   Exit price: ${exit_price:,.2f}")
    print(f"   Gross P&L: ${pnl['gross_pnl']:,.2f}")
    print(f"   Total fees: ${pnl['total_fees']:.2f}")
    print(f"   Net P&L: ${pnl['net_pnl']:,.2f}")
    print(f"   Net P&L %: {pnl['pnl_pct']:.2f}%")
    
    # 5. Slippage impact
    print("\n5️⃣ SLIPPAGE IMPACT:")
    print(f"   Intended exit price: ${exit_price:,.2f}")
    
    # Slippage scenarios
    for slippage_scenario in [0.0, 0.05, 0.10, 0.15]:  # 0%, 0.05%, 0.1%, 0.15%
        pnl_with_slippage = manager.calculate_true_pnl(
            entry_price, exit_price, quantity, leverage,
            is_maker_entry=False, is_maker_exit=True,
            slippage_realized=slippage_scenario / 100
        )
        status = "✅ OK" if slippage_scenario <= 0.1 else "❌ TOO HIGH"
        print(f"   @ {slippage_scenario:.2f}% slippage: Net P&L = ${pnl_with_slippage['net_pnl']:,.2f} ({pnl_with_slippage['pnl_pct']:.2f}%) {status}")
    
    # 6. Impact na 5 dokładek (pyramiding)
    print("\n6️⃣ PYRAMIDING IMPACT (5x $50 positions):")
    print(f"   5 entries = 5x fees!")
    
    total_fees_5x = 0
    for i in range(5):
        entry_calc = manager.calculate_entry_cost(quantity/5, entry_price, is_maker=False)
        total_fees_5x += entry_calc['fee_amount']
    
    print(f"   Total fees for 5 entries: ${total_fees_5x:.2f}")
    print(f"   ⚠️ This is why position sizing matters!")
    
    # 7. Rekomendacje
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS:")
    print("="*70)
    print("""
1. Use Maker orders when possible (0.01% vs 0.02%)
   - Place limit orders slightly below market
   - Sometimes takes longer to fill, but cheaper

2. Account for fees in Take Profit calculation
   - Don't aim for 1% gross profit
   - Aim for 1.5-2% to account for fees

3. Keep slippage below 0.1%
   - Use limit orders with tight price ranges
   - Avoid market orders in low liquidity

4. For pyramiding (5 entries):
   - Fees multiply: 5x entry + 1x exit = 6x fee impact
   - Make sure TP justifies this

5. Use maker order on exit
   - Most exchanges give rebate for maker
   - Can offset some entry fee

6. Monitor real fees for your exchange
   - Binance Spot: 0.01% maker, 0.02% taker
   - Lower for higher volumes or VIP
    """)
    print("="*70)


if __name__ == "__main__":
    demo_fees_slippage()
