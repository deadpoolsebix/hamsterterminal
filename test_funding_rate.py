#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎮 AI TRADER GAME BOY - FUNDING RATE CALCULATOR TEST
Przykłady użycia nowych funkcji do obliczania funding rate
"""

from ml_trading_brain import TradingBrain
from datetime import datetime, timedelta
import json

print("\n" + "="*90)
print("🎮 AI TRADER GAME BOY v2.0 - FUNDING RATE CALCULATOR")
print("="*90)

# Inicjalizuj AI Brain
brain = TradingBrain()

# ==================== TEST 1: ANALYZE POSITION ====================
print("\n[TEST 1] 📊 CURRENT POSITION ANALYSIS")
print("-"*90)

analysis = brain.analyze_current_position(
    symbol='BTCUSDT',
    position_size_usdt=10000,
    entry_price=95000,
    current_price=96500,
    position_type='LONG',
    leverage=10,
    entry_time=datetime.now() - timedelta(hours=3),
    exchange='binance',
    coin_name='BTC'
)

print(f"""
📌 POSITION INFO:
   Symbol: {analysis['symbol']}
   Type: {analysis['position_type']}
   Size: ${analysis['position_size_usdt']:,}
   Qty: {analysis['coin_quantity']:.8f} BTC
   Leverage: {analysis['leverage']}x

💰 PRICE:
   Entry: ${analysis['entry_price']:,}
   Current: ${analysis['current_price']:,}
   Move: {analysis['price_move_percent']:+.2f}%

⏱️ TIME:
   Hold: {analysis['hold_hours']:.2f}h ({analysis['hold_days']:.4f}d)

📈 P&L:
   Unrealized: ${analysis['unrealized_pnl']:,.2f}
   Funding Cost: ${analysis['accumulated_funding_cost']:.2f}
   Fees (entry): ${analysis['entry_fee']:.2f}
   Net P&L: ${analysis['net_pnl_current']:,.2f}
   ROI: {analysis['roi_percent']:.2f}%

⚠️ RISK:
   Daily Funding: {analysis['daily_funding_rate']:.4f}%
   Liquidation: ${analysis['liquidation_price']:,.2f}
   Distance: {analysis['distance_to_liquidation_percent']:.2f}%
   Break-Even: ${analysis['break_even_price']:,.2f}
""")

# ==================== TEST 2: BREAK-EVEN ANALYSIS ====================
print("\n[TEST 2] 🎯 BREAK-EVEN ANALYSIS")
print("-"*90)

break_even = brain.calculate_position_break_even(
    position_size_usdt=10000,
    entry_price=95000,
    position_type='LONG',
    leverage=10,
    hold_hours=4
)

print(f"""
Entry Price: ${break_even['entry_price']:,}
Break-Even Price: ${break_even['break_even_price']:,}
Price Move Needed: {break_even['move_needed_percent']:.4f}%

Costs to Recover:
  - Fees: ${break_even['total_fees']:.2f}
  - Funding: ${break_even['funding_cost']:.2f}
  - Total: ${break_even['total_cost_to_recover']:.2f}

💡 Meaning: Need +{break_even['move_needed_percent']:.4f}% price move
to break even after fees & funding costs
""")

# ==================== TEST 3: PRICE SCENARIOS ====================
print("\n[TEST 3] 📊 PRICE SCENARIOS (8h hold)")
print("-"*90)

scenarios = brain.simulate_price_scenarios(
    position_size_usdt=10000,
    entry_price=95000,
    position_type='LONG',
    leverage=10,
    hold_hours=8
)

print(f"\nDaily Funding Rate: {scenarios['daily_funding_rate']:.4f}%\n")
print(f"{'Exit Price':<15} {'Move %':<12} {'Gross P&L':<15} {'Fees':<10} {'Funding':<10} {'Net P&L':<15} {'ROI %':<12} {'Status':<10}")
print("-"*115)

for s in scenarios['scenarios']:
    status = "✓ PROFIT" if s['profitable'] else "✗ LOSS"
    color = "🟢" if s['profitable'] else "🔴"
    print(f"${s['exit_price']:<14.2f} {s['price_move_percent']:>10.2f}% ${s['gross_pnl']:<14.2f} ${s['fees']:<9.2f} ${s['funding_cost']:<9.2f} ${s['net_pnl']:<14.2f} {s['roi_percent']:>10.2f}% {color} {status:<8}")

# ==================== TEST 4: OPTIMAL POSITION ====================
print("\n[TEST 4] 🎯 OPTIMAL POSITION WITH FUNDING")
print("-"*90)

capital = 50000
opt_position = brain.calculate_optimal_position_with_funding(
    capital=capital,
    confidence=75,
    entry_price=95000,
    target_roi_percent=2.5,
    max_hold_hours=24,
    leverage=10
)

print(f"""
💼 CAPITAL & CONFIDENCE:
   Capital: ${capital:,}
   Confidence: 75%
   Target ROI: {opt_position['target_roi_percent']}%

📊 POSITION SIZING:
   Base Position: ${opt_position['base_position_size']:,.2f}
   Optimized Position: ${opt_position['optimized_position_size']:,.2f}
   Adjustment: {opt_position['adjustment_multiplier']}x

📈 ESTIMATED COSTS (24h hold):
   Daily Funding Rate: {opt_position['estimated_daily_funding_rate']:.4f}%
   Funding Cost: ${opt_position['estimated_funding_cost']:.2f}
   Fees (entry+exit): ${opt_position['estimated_fees']:.2f}
   Total Costs: ${opt_position['total_estimated_costs']:.2f}

⚡ PROFITABILITY:
   Required P&L: ${opt_position['required_pnl']:.2f}
   Profitability Ratio: {opt_position['profitability_ratio']}x
   
💡 Meaning: Position size adjusted so that {opt_position['target_roi_percent']}% ROI
   covers all costs with {opt_position['profitability_ratio']}x margin
""")

# ==================== TEST 5: TRADE EVALUATION ====================
print("\n[TEST 5] 📝 TRADE EVALUATION")
print("-"*90)

trade_eval = brain.evaluate_trade_with_funding(
    symbol='BTCUSDT',
    entry_price=95000,
    exit_price=96500,
    entry_time=datetime.now() - timedelta(hours=2),
    exit_time=datetime.now(),
    position_type='LONG',
    position_size_usdt=10000,
    leverage=10,
    exchange='binance'
)

print(f"""
📌 TRADE SUMMARY:
   {trade_eval['position_type']} {trade_eval['symbol']}
   Entry: ${trade_eval['entry_price']:,} | Exit: ${trade_eval['exit_price']:,}
   Position: ${trade_eval['position_size_usdt']:,}
   Quantity: {trade_eval['quantity_coins']:.8f} coins
   Hold Time: {trade_eval['hold_time_hours']:.2f}h

💰 FINANCIAL RESULTS:
   Gross P&L: ${trade_eval['gross_pnl']:+,.2f}
   Funding Cost: ${trade_eval['funding_cost']:+,.2f}
   Fees: ${trade_eval['fees']:+,.2f}
   ─────────────────────────
   Net P&L: ${trade_eval['net_pnl']:+,.2f}
   ROI: {trade_eval['roi_percent']:+.2f}%
   
✅ PROFITABLE: {'YES ✓' if trade_eval['is_profitable'] else 'NO ✗'}

Daily Funding Rate: {trade_eval['daily_funding_rate']:.4f}%
Exchange: {trade_eval['exchange']}
""")

# ==================== TEST 6: GAME BOY CALCULATOR ====================
print("\n[TEST 6] 🎮 GAME BOY CALCULATOR SIMULATION")
print("-"*90)

print("""
💰 FUNDING RATE CALCULATOR (Game Boy Panel):
┌─────────────────────────────────┐
│ Position (USDT): 10000          │
│ Entry $: 95000                  │
│ Leverage: 10                    │
│ Hold (h): 4                     │
├─────────────────────────────────┤
│ [CALC FUNDING]                  │
├─────────────────────────────────┤
""")

# Simulate calculator
pos_size = 10000
entry_price = 95000
leverage = 10
hold_hours = 4

daily_funding = 0.0001
hourly_rate = daily_funding / 24
funding_cost = pos_size * hourly_rate * hold_hours
taker_fee = 0.0004
total_fees = pos_size * taker_fee * 2
total_cost = funding_cost + total_fees

coin_qty = pos_size / entry_price
cost_per_coin = total_cost / coin_qty
break_even_price = entry_price + cost_per_coin
be_percent = (cost_per_coin / entry_price) * 100

print(f"""
│ Cost: ${funding_cost:.2f}                 │
│ Fees: ${total_fees:.2f}                │
│ B/E: {be_percent:.4f}%                 │
└─────────────────────────────────┘
""")

# ==================== COMPARISON ====================
print("\n[TEST 7] 📊 COMPARISON: WITHOUT vs WITH FUNDING")
print("-"*90)

# Without funding calculation
gross_pnl = (96500 - 95000) * (10000/95000)
fees_only = 10000 * 0.0004 * 2
pnl_without_funding = gross_pnl - fees_only

# With funding calculation
funding_cost_total = 10000 * (0.0001/24) * 4
pnl_with_funding = gross_pnl - fees_only - funding_cost_total
roi_without = (pnl_without_funding / (10000/10)) * 100
roi_with = (pnl_with_funding / (10000/10)) * 100

print(f"""
SCENARIO: LONG $10,000 BTC @ 95,000 → 96,500 (4h hold, 10x leverage)

WITHOUT FUNDING CALCULATION (Mistake!):
  Gross P&L: ${gross_pnl:.2f}
  Fees: ${fees_only:.2f}
  Net P&L: ${pnl_without_funding:.2f}
  ROI: {roi_without:.2f}% ❌

WITH FUNDING CALCULATION (Correct!):
  Gross P&L: ${gross_pnl:.2f}
  Fees: ${fees_only:.2f}
  Funding Cost: ${funding_cost_total:.2f}
  Net P&L: ${pnl_with_funding:.2f}
  ROI: {roi_with:.2f}% ✓

DIFFERENCE: ${pnl_without_funding - pnl_with_funding:.2f} ({(pnl_without_funding - pnl_with_funding)/pnl_without_funding*100:.1f}%)

💡 KEY INSIGHT: Ignoring funding costs leads to
   overestimating profitability by ~{abs((pnl_without_funding - pnl_with_funding)/pnl_without_funding*100):.1f}%!
""")

# ==================== RECOMMENDATIONS ====================
print("\n[RECOMMENDATIONS] 🎯 BEST PRACTICES")
print("-"*90)

print(f"""
1️⃣ FUNDING RATE STRATEGY:
   ✓ SHORT when funding is negative (earn 0.005-0.02% daily)
   ✓ LONG when funding is low (<0.005% daily)
   ✓ Avoid LONG when funding >0.02% (expensive!)

2️⃣ POSITION SIZING:
   ✓ Always calculate break-even BEFORE entering
   ✓ Use optimized position sizing (covers funding costs)
   ✓ Reduce size if break-even > 0.5% (too risky)

3️⃣ SCALP vs SWING:
   ✓ Scalp (minutes): Funding ~$0.01 cost
   ✓ Swing (hours): Funding ~$1-10 cost
   ✓ Position (days): Funding ~$50-500 cost
   → Choose timeframe based on funding rates

4️⃣ RISK MANAGEMENT:
   ⚠️ Liquidation distance > break-even + 2%
   ⚠️ Monitor funding rate every 8 hours (changes!)
   ⚠️ Use tighter SL during high funding
   ⚠️ Avoid averaging down on expensive funding

5️⃣ GAME BOY CALCULATOR:
   ✓ Use before EVERY trade
   ✓ Check B/E % (should be <0.2% for good trades)
   ✓ Adjust position size if B/E too high
   ✓ Remember: costs are REAL, not estimates!
""")

print("\n" + "="*90)
print("✅ TESTING COMPLETE - AI TRADER GAME BOY READY!")
print("="*90 + "\n")
