#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Real-Time Bot - Main Script
Uruchomienie bota na realnych danych w tempie rzeczywistym
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.simulator.realtime_bot_sim import RealTimeBotSimulator

if __name__ == "__main__":
    print("\n[*] Real-Time Bot Simulator")
    print("[*] Bot gra na realnych danych BTC w tempie rzeczywistym\n")
    
    # Uruchom na ostatnich 7 dniach z interwałem 1h
    simulator = RealTimeBotSimulator(days=7, interval='1h')
    simulator.run_simulation()
