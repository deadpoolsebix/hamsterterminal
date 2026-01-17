# 💰 FUNDING RATE CALCULATOR - QUICK REFERENCE

## 📌 ONE-PAGE CHEAT SHEET

### FORMULA
```
Break-Even % = (Funding Cost + Fees) / Entry Price × 100

Funding Cost = Position Size × Daily Rate / 24 × Hold Hours
Fees = Position Size × 0.04% (entry) + 0.04% (exit) = 0.08% total
```

### QUICK NUMBERS (Binance)

| Hold Time | Position Size | Daily Rate | Funding Cost |
|-----------|---------------|-----------|------------|
| 1h | $10,000 | 0.01% | $0.04 |
| 4h | $10,000 | 0.01% | $0.17 |
| 8h | $10,000 | 0.01% | $0.33 |
| 24h | $10,000 | 0.01% | $1.00 |
| 7 days | $10,000 | 0.01% | $7.00 |

### BREAK-EVEN PERCENTAGES

| Leverage | Position | Entry | 4h Hold | Break-Even % |
|----------|----------|-------|---------|------------|
| 10x | $10,000 | 95,000 | LONG | 0.0817% |
| 20x | $10,000 | 95,000 | LONG | 0.0817% |
| 50x | $10,000 | 95,000 | LONG | 0.0817% |
| 100x | $10,000 | 95,000 | LONG | 0.0817% |

### GAME BOY INPUTS
```
Position (USDT): [____]  ← Total position size
Entry $: [____]          ← Entry price
Leverage: [____]         ← 1-125
Hold (h): [____]         ← Hours to hold

→ [CALC FUNDING] →

Cost: $X.XX              ← Total funding + fees
B/E: X.XXXX%            ← % move needed
```

### STRATEGY TABLE

| Funding Rate | Best Action | Why |
|------------|------------|-----|
| **Negative** (-0.01%) | SHORT | You EARN funding |
| **Low** (<0.005%) | LONG | Cheap to hold |
| **Medium** (0.01%) | Scalp | OK for short |
| **High** (0.02%+) | AVOID | Too expensive |
| **Extreme** (0.1%+) | SKIP | Likely losing |

### POSITION TYPES COMPARISON

```
SCALP (5-30 min):
  Funding Cost: $0.01-0.1
  Break-Even: 0.001-0.01%
  ✅ Best for funding savings

SWING (2-8h):
  Funding Cost: $0.1-1
  Break-Even: 0.01-0.1%
  ✅ Balanced

POSITION (1-7 days):
  Funding Cost: $1-50+
  Break-Even: 0.1-0.5%
  ❌ Expensive, watch funding
```

## 🎯 BEFORE EVERY TRADE

```
1. Check daily funding rate
   ↓ Use Game Boy calculator
   ↓
2. Calculate break-even %
   ↓ Should be <0.2% (good)
   ↓
3. Compare to price targets
   ↓ TP - B/E should be >1%
   ↓
4. Verify liquidation distance
   ↓ Should be 10%+ away
   ↓
5. EXECUTE (or skip if B/E too high)
```

## 💡 KEY INSIGHTS

- **Funding is REAL cost** - Not included in entry/exit
- **Accumulates fast** - 0.01% × 24h = $24 on $10k
- **Changes every 8h** - Monitor rates on giełdzie
- **SHORTs can profit** - Negative funding = free money
- **Scalp > Position** - Time is cost, reduce it
- **Volatility increases cost** - 2-3x multiplier in crazy markets

## 📊 EXAMPLES

### Example 1: LONG Scalp
```
Position: $5,000 | Entry: $95,000 | Leverage: 5x
Hold: 15 minutes | Daily Funding: 0.01%

Funding: $5,000 × 0.0001 / 24 × 0.25 = $0.005
Fees: $5,000 × 0.0008 = $4.00
Total Cost: $4.005
Break-Even: 0.0084% ← Super small!

✅ Good trade potential
```

### Example 2: LONG Swing (BAD)
```
Position: $10,000 | Entry: $95,000 | Leverage: 50x
Hold: 24 hours | Daily Funding: 0.03% (high!)

Funding: $10,000 × 0.0003 × 1 = $3.00
Fees: $10,000 × 0.0008 = $8.00
Total Cost: $11.00
Break-Even: 0.0116% ← Too expensive

❌ Avoid this!
```

### Example 3: SHORT (GOOD!)
```
Position: $10,000 | Entry: $95,000 | Leverage: 10x
Hold: 8 hours | Daily Funding: -0.01% (negative!)

Funding: $10,000 × -0.0001 / 24 × 8 = -$0.33 ← YOU EARN!
Fees: $10,000 × 0.0008 = $8.00
Total Cost: $7.67 (after earning funding)
Break-Even: 0.0809% ← Much better!

✅ Perfect trade setup
```

## 🔴 RED FLAGS

| Flag | Meaning | Action |
|------|---------|--------|
| B/E > 0.5% | Too expensive | Skip trade |
| Funding > 0.05% | Extreme | Don't LONG |
| Liq. < 5% | Too risky | Reduce size |
| B/E > TP% | Negative EV | Skip |
| Holding 7+ days | Funding piles up | Set SL tighter |

## 🟢 GREEN FLAGS

| Flag | Meaning | Action |
|------|---------|--------|
| B/E < 0.1% | Cheap entry | Good trade |
| Funding < 0 | FREE money (SHORT) | Take it |
| Liq. > 10% | Safe buffer | OK size |
| B/E << TP% | Positive EV | Execute |
| Scalp time | Low cost | Go |

## 🎮 GAME BOY WORKFLOW

```
🎮 OPEN GAME BOY
    ↓
💰 FIND FUNDING CALC PANEL
    ↓
📝 ENTER YOUR POSITION DATA
    ↓
🔢 CLICK "CALC FUNDING"
    ↓
✅ LOOK AT BREAK-EVEN %
    ↓
📊 COMPARE TO YOUR STRATEGY
    ↓
✋ SKIP IF B/E TOO HIGH
✔️ EXECUTE IF B/E LOW
```

## 📋 CHECKLIST

- [ ] Funding rate checked (< 0.02%?)
- [ ] Break-even calculated (< 0.2%?)
- [ ] Liquidation distance OK (> 10%?)
- [ ] Position size optimized
- [ ] SL below break-even buffer
- [ ] TP targets profit > B/E costs
- [ ] Time frame considered (scalp vs swing)
- [ ] Ready to execute

## 🚀 PYTHON ONE-LINER

```python
brain.analyze_current_position(
    symbol='BTCUSDT', position_size_usdt=10000, entry_price=95000,
    current_price=96500, position_type='LONG', leverage=10,
    entry_time=datetime.now()-timedelta(hours=3)
).get('net_pnl_current')
```

## 📞 HELP

**Need calculation?** → Use Game Boy panel  
**Want details?** → Read FUNDING_RATE_GUIDE.md  
**Testing code?** → Run test_funding_rate.py  
**In production?** → Use ml_trading_brain.py methods  

---

**Remember**: Costs are REAL. Calculate before trading! 💰
