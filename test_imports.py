#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick Test - Verify all modules load correctly
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testing imports...\n")

try:
    print("✓ Importing BotSimulator7Days...")
    from trading_bot.simulator.bot_simulator_7days import BotSimulator7Days
    print("  OK\n")
    
    print("✓ Importing LiveDashboard...")
    from trading_bot.simulator.live_dashboard import LiveDashboard
    print("  OK\n")
    
    print("✓ Importing AdvancedPlotter...")
    from trading_bot.simulator.plotting_engine import AdvancedPlotter
    print("  OK\n")
    
    print("✓ Creating simulator instance...")
    sim = BotSimulator7Days(account_size=5000, risk_per_trade=250)
    print("  OK\n")
    
    print("✓ Generating test data...")
    data = sim.generate_realistic_data(days=1)
    print(f"  Generated {len(data)} candles")
    print(f"  Columns: {list(data.columns)}\n")
    
    print("✓ All imports successful!\n")
    print("🎉 Ready to run: python run_7day_simulation.py\n")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
