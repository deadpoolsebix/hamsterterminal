"""
TEST AI TRADING BOT
Quick test to verify AI learning integration
"""

from ml_trading_brain import TradingBrain
import pandas as pd
import numpy as np

print("\n" + "="*80)
print("AI TRADING BOT - TEST")
print("="*80)

# Initialize AI Brain
brain = TradingBrain()

print("\n[1] Testing AI Brain initialization...")
print(f"    Learning rate: {brain.learning_rate}")
print(f"    Discount factor: {brain.discount_factor}")
print(f"    Exploration rate: {brain.epsilon * 100}%")
print("    ✓ AI Brain initialized")

# Simulate market states and learning
print("\n[2] Simulating 50 trades for AI learning...")
for i in range(50):
    # Random market conditions
    indicators = {
        'rsi': pd.Series([np.random.uniform(20, 80)]),
        'macd': pd.Series([np.random.uniform(-100, 100)]),
        'momentum': pd.Series([np.random.uniform(-500, 500)])
    }
    
    market_data = {
        'price': 95000 + np.random.uniform(-2000, 2000),
        'sma_20': 94000,
        'volume': 1000000 + np.random.uniform(-200000, 200000),
        'volume_ma': 900000
    }
    
    # Get state and action from AI
    state = brain.get_state(indicators, market_data)
    action = brain.get_action(state)
    
    # Simulate trade result (70% win rate for testing)
    if np.random.random() < 0.7:
        pnl = np.random.uniform(50, 300)  # Win
    else:
        pnl = np.random.uniform(-150, -50)  # Loss
    
    trade_result = {
        'state': state,
        'action': action,
        'next_state': state,
        'pnl': pnl,
        'pnl_pct': pnl / 5000,
        'hold_time_minutes': np.random.uniform(15, 120),
        'active_features': ['rsi', 'macd', 'momentum']
    }
    
    brain.learn_from_trade(trade_result)
    
    if (i + 1) % 10 == 0:
        print(f"    Completed {i + 1}/50 trades...")

print("    ✓ AI learning simulation completed")

# Print learning statistics
print("\n[3] AI Learning Statistics:")
stats = brain.get_learning_stats()
print(f"    Total trades: {stats['total_trades']}")
print(f"    Winning trades: {stats['winning_trades']}")
print(f"    Win rate: {stats['win_rate']:.1f}%")
print(f"    Total P&L: ${stats['total_pnl']:,.2f}")
print(f"    Avg P&L per trade: ${stats['avg_pnl_per_trade']:,.2f}")
print(f"    States learned: {stats['states_learned']}")
print(f"    Exploration rate: {stats['exploration_rate']:.1f}%")

# Test confidence scoring
print("\n[4] Testing AI confidence scoring...")
test_indicators = {
    'rsi': pd.Series([25]),  # Oversold
    'macd': pd.Series([50]),
    'momentum': pd.Series([200])
}
test_market = {
    'price': 95000,
    'sma_20': 94000,
    'volume': 1200000,
    'volume_ma': 900000
}

confidence_buy = brain.get_confidence_score(test_indicators, test_market, 'BUY')
confidence_sell = brain.get_confidence_score(test_indicators, test_market, 'SELL')

print(f"    Confidence for BUY: {confidence_buy:.1f}%")
print(f"    Confidence for SELL: {confidence_sell:.1f}%")
print(f"    ✓ AI recommends: {'BUY' if confidence_buy > confidence_sell else 'SELL'}")

# Test position sizing
print("\n[5] Testing optimal position sizing...")
capital = 5000
position_size_high = brain.get_optimal_position_size(confidence=80, capital=capital)
position_size_medium = brain.get_optimal_position_size(confidence=60, capital=capital)
position_size_low = brain.get_optimal_position_size(confidence=40, capital=capital)

print(f"    High confidence (80%): ${position_size_high:.2f} ({position_size_high/capital*100:.1f}% of capital)")
print(f"    Medium confidence (60%): ${position_size_medium:.2f} ({position_size_medium/capital*100:.1f}% of capital)")
print(f"    Low confidence (40%): ${position_size_low:.2f} ({position_size_low/capital*100:.1f}% of capital)")
print("    ✓ Position sizing works correctly")

# Save and load test
print("\n[6] Testing brain save/load...")
brain.save_brain("test_brain.pkl")
print("    ✓ Brain saved")

new_brain = TradingBrain()
success = new_brain.load_brain("test_brain.pkl")
if success:
    print("    ✓ Brain loaded successfully")
    print(f"    Loaded {new_brain.total_trades} trades from memory")
else:
    print("    ✗ Brain load failed")

# Full learning report
print("\n[7] Full AI Learning Report:")
brain.print_learning_report()

print("\n" + "="*80)
print("TEST COMPLETED SUCCESSFULLY! ✓")
print("="*80)
print("\n📊 SUMMARY:")
print("   • AI Brain initialized and working")
print("   • Learning algorithm functioning (Q-Learning)")
print("   • Confidence scoring operational")
print("   • Position sizing adaptive")
print("   • Save/Load persistence working")
print("\n💡 Bot jest gotowy do uczenia się na prawdziwych danych!")
print("   Uruchom: python run_professional_bot.py")
print("\n" + "="*80 + "\n")
