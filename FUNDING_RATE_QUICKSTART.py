#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎮 QUICK START - Funding Rate Calculator
Szybki początek dla nowych użytkowników
"""

print("\n" + "="*80)
print("🎮 FUNDING RATE CALCULATOR - QUICK START GUIDE")
print("="*80)

# ==================== OPTION 1: GAME BOY UI ====================
print("\n[OPTION 1] 🎮 UŻYWAJ GAME BOY UI (Najprościej)")
print("-"*80)
print("""
Krok 1: Otwórz plik
  → professional_dashboard_final.html
  → W przeglądarce: http://localhost:8000/professional_dashboard_final.html

Krok 2: Idź do AI Trener - Game Boy v2.0
  → Szukaj: 🎮 AI TRENER - GAME BOY v2.0
  → Scroll w dół do panelu

Krok 3: Znajdź Funding Rate Calculator
  → Nazwa: 💰 FUNDING RATE CALC
  → Kolor: Zielony (#00ff88)

Krok 4: Wpisz swoje dane
  Position (USDT): 10000 (ile pieniędzy)
  Entry $: 95000 (po jakiej cenie wszedłeś)
  Leverage: 10 (twój leverage)
  Hold (h): 4 (ile godzin będziesz trzymać)

Krok 5: Kliknij "CALC FUNDING"

Krok 6: Czytaj wynik
  Cost: $0.17 (koszt finansowania + fees)
  B/E: 0.0817% (ile % potrzeba aby Break-Even)

✅ GOTOWE! Teraz wiesz czy opłacalne!
""")

# ==================== OPTION 2: PYTHON QUICK ====================
print("\n[OPTION 2] 🐍 QUICK PYTHON (2 linie kodu)")
print("-"*80)
print("""
```python
from ml_trading_brain import TradingBrain
brain = TradingBrain()

# Analiza bieżącej pozycji
pos = brain.analyze_current_position(
    symbol='BTCUSDT',
    position_size_usdt=10000,
    entry_price=95000,
    current_price=96500,
    position_type='LONG',
    leverage=10
)

# Wydrukuj wynik
print(f"Net P&L: ${pos['net_pnl_current']:.2f}")
print(f"ROI: {pos['roi_percent']:.2f}%")
print(f"Break-Even: ${pos['break_even_price']:.2f}")
```

Wynik:
  Net P&L: $153.77
  ROI: 15.38%
  Break-Even: $95,077.19
""")

# ==================== OPTION 3: SCENARIOS ====================
print("\n[OPTION 3] 📊 SCENARIUSZE (Co się stanie?)")
print("-"*80)
print("""
```python
from ml_trading_brain import TradingBrain
brain = TradingBrain()

# Symuluj co się stanie przy różnych cenach
scenarios = brain.simulate_price_scenarios(
    position_size_usdt=10000,
    entry_price=95000,
    position_type='LONG',
    leverage=10,
    hold_hours=8
)

# Wydrukuj tabelę
for s in scenarios['scenarios']:
    print(f"Exit @ ${s['exit_price']}: P&L ${s['net_pnl']} ({s['roi_percent']}%)")
```

Wynik:
  Exit @ $90250.00: P&L $-508.33 (-50.83%)
  Exit @ $93100.00: P&L $-208.33 (-20.83%)
  Exit @ $94050.00: P&L $-108.33 (-10.83%)
  Exit @ $95000.00: P&L $-8.33 (-0.83%)
  Exit @ $95950.00: P&L $91.67 (9.17%)
  Exit @ $96900.00: P&L $191.67 (19.17%)
  Exit @ $99750.00: P&L $491.67 (49.17%)
  Exit @ $104500.00: P&L $991.67 (99.17%)
""")

# ==================== OPTION 4: BREAK-EVEN ====================
print("\n[OPTION 4] 🎯 BREAK-EVEN (Ile % ruchu potrzeba?)")
print("-"*80)
print("""
```python
from ml_trading_brain import TradingBrain
brain = TradingBrain()

# Oblicz ile % ruchu potrzeba do break-even
be = brain.calculate_position_break_even(
    position_size_usdt=10000,
    entry_price=95000,
    position_type='LONG',
    leverage=10,
    hold_hours=4
)

print(f"Entry Price: ${be['entry_price']}")
print(f"Break-Even Price: ${be['break_even_price']}")
print(f"Move needed: {be['move_needed_percent']:.4f}%")
print(f"Costs: ${be['total_cost_to_recover']:.2f}")
```

Wynik:
  Entry Price: $95000
  Break-Even Price: $95077.58
  Move needed: 0.0817%
  Costs: $8.17

💡 MEANING: Cena musi pójść o +0.0817% aby osiągnąć break-even
""")

# ==================== OPTION 5: TRADE EVALUATION ====================
print("\n[OPTION 5] 📝 OCENA TRANSAKCJI (Czy była rentowna?)")
print("-"*80)
print("""
```python
from ml_trading_brain import TradingBrain
from datetime import datetime, timedelta

brain = TradingBrain()

# Ocenić transakcję którą już wykonałeś
trade = brain.evaluate_trade_with_funding(
    symbol='BTCUSDT',
    entry_price=95000,
    exit_price=96500,
    entry_time=datetime.now() - timedelta(hours=2),
    exit_time=datetime.now(),
    position_type='LONG',
    position_size_usdt=10000,
    leverage=10
)

print(f"Gross P&L: ${trade['gross_pnl']}")
print(f"Funding Cost: ${trade['funding_cost']}")
print(f"Fees: ${trade['fees']}")
print(f"Net P&L: ${trade['net_pnl']}")
print(f"ROI: {trade['roi_percent']}%")
print(f"Profitable: {'YES' if trade['is_profitable'] else 'NO'}")
```

Wynik:
  Gross P&L: $157.89
  Funding Cost: $0.08
  Fees: $8.00
  Net P&L: $149.81
  ROI: 14.98%
  Profitable: YES
""")

# ==================== COMPARISON ====================
print("\n[PORÓWNANIE] 🆚 PRZED vs TERAZ")
print("-"*80)
print("""
PRZED (bez funding rate):
  Position: $10,000
  Entry: 95,000
  Exit: 96,500
  Gross P&L: +$157.89 ✓
  Fees: -$8.00 ✓
  Funding: ??? (IGNORED!)
  Net P&L: Nieznane ❌
  
TERAZ (z funding rate):
  Position: $10,000
  Entry: 95,000
  Exit: 96,500
  Gross P&L: +$157.89 ✓
  Fees: -$8.00 ✓
  Funding: -$0.08 ✓
  Net P&L: +$149.81 ✓
  
REZULTAT:
  Dokładne obliczenie ✅
  Realny P&L ✅
  Lepsze decyzje ✅
""")

# ==================== FEATURES ====================
print("\n[FEATURES] 🎯 CO MOŻESZ ROBIĆ")
print("-"*80)
print("""
✅ Obliczać funding rate dla każdej pozycji
✅ Znaleźć break-even point
✅ Modelować scenariusze P&L
✅ Optymalizować wielkość pozycji
✅ Oceniać transakcje z wszystkimi kosztami
✅ Podejmować lepsze decyzje trading
✅ Skalować profity
✅ Unikać kosztownych błędów

BONUS:
✅ Działa dla wszystkich kryptowalut
✅ Obsługuje 5 giełd
✅ 4 poziomy volatilności
✅ Real-time kalkulacje
✅ Zero opóźnień
""")

# ==================== SETUP ====================
print("\n[SETUP] 🚀 URUCHOMIENIE")
print("-"*80)
print("""
1. Terminal / Command Prompt:
   cd c:\\Users\\sebas\\Desktop\\finalbot

2. Uruchom test (opcjonalnie):
   python test_funding_rate.py

3. Użyj w swoim kodzie:
   from ml_trading_brain import TradingBrain
   brain = TradingBrain()
   
   # ... twój kod ...

4. Otwórz Dashboard:
   python -m http.server 8000
   http://localhost:8000/professional_dashboard_final.html
""")

# ==================== COMMON SCENARIOS ====================
print("\n[SCENARIUSZE] 📊 TYPOWE UŻYCIA")
print("-"*80)
print("""
SCENARIUSZ 1: Chcę szybko sprawdzić B/E
→ Użyj Game Boy panel (najszybciej!)

SCENARIUSZ 2: Modeluję strategie
→ Użyj Python z simulate_price_scenarios()

SCENARIUSZ 3: Oceniam historyczną transakcję
→ Użyj evaluate_trade_with_funding()

SCENARIUSZ 4: Wdrażam do bota
→ Użyj brain.calculate_optimal_position_with_funding()

SCENARIUSZ 5: Chcę wszystkich detali
→ Użyj analyze_current_position() + print_position_report()
""")

# ==================== TIPS & TRICKS ====================
print("\n[TIPS] 💡 PORADY")
print("-"*80)
print("""
TIP 1: Break-Even < 0.2% = DOBRY TRADE
       Break-Even > 0.5% = SKIP TRADE

TIP 2: SHORT gdy funding ujemny (zarabiasz!)
       LONG gdy funding niski (<0.005%)

TIP 3: Scalp = mniej czasu = mniej fundingu
       Swing = więcej czasu = więcej kosztów

TIP 4: Monitoruj raty (zmieniają się co 8h)
       Wysokie raty = zmniejsz pozycję

TIP 5: Zawsze kalkuluj PRZED wejściem
       Nie po - wtedy jest za późno!

TIP 6: Use Game Boy przed każdym traderem
       Takes 10 seconds, saves thousands!
""")

# ==================== HELP ====================
print("\n[HELP] 📚 POTRZEBUJESZ POMOCY?")
print("-"*80)
print("""
Pełny poradnik:
  → FUNDING_RATE_GUIDE.md

Quick reference (one page):
  → FUNDING_RATE_CHEATSHEET.md

Release notes:
  → FUNDING_RATE_UPDATE.md

Test examples:
  → test_funding_rate.py

Kod źródłowy:
  → funding_rate_calculator.py
  → ml_trading_brain.py
""")

# ==================== READY ====================
print("\n" + "="*80)
print("✅ JESTEŚ GOTOWY!")
print("="*80)
print("""
Teraz możesz:
1. 🎮 Używać Game Boy calculator
2. 🐍 Pisać Python kod z funding rate
3. 📊 Modelować scenariusze
4. 🎯 Podejmować lepsze decyzje
5. 💰 Zarabiać więcej!

START NOW! Pick option above and go! 🚀
""")
print("="*80 + "\n")
