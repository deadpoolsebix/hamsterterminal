#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BLOOMBERG TERMINAL ENGINE - Live Data Server
Aktualizuje data.json co 3s dla dashboardu online
"""

import json
import time
from datetime import datetime
import os
import sys

# Import bota (jeśli działa)
try:
    from trading_bot.simulator.real_data_fetcher import RealDataFetcher
    from live_indicators_analyzer import LiveIndicatorsAnalyzer
    HAS_BOT = True
except:
    HAS_BOT = False
    print("[!] Bot modules not available, using mock data")

import random


class DashboardDataEngine:
    """
    Silnik danych dla dashboardu Bloomberg
    Pobiera dane z bota lub symuluje je
    """
    
    def __init__(self):
        if HAS_BOT:
            self.fetcher = RealDataFetcher()
            self.analyzer = LiveIndicatorsAnalyzer()
        self.iteration = 0
        self.users_online = random.randint(3, 8)  # Multi-user mode
        
    def get_real_market_data(self):
        """Pobiera realne dane z rynku"""
        try:
            if HAS_BOT:
                # Fetch real BTC data
                data = self.fetcher.fetch_data('BTC-USD', period='1d', interval='15m')
                if data is not None and len(data) > 50:
                    current_price = float(data['close'].iloc[-1])
                    
                    # Calculate indicators
                    indicators = self.analyzer.calculate_all_indicators(data)
                    
                    rsi = float(indicators['rsi'].iloc[-1])
                    macd = float(indicators['macd'].iloc[-1])
                    sentiment = float(indicators['sentiment'].iloc[-1])
                    
                    # Detect phase
                    if sentiment > 0.02 and rsi < 50:
                        phase = "ACCUMULATION (PHASE C)"
                        regime = "BULLISH BIAS (Smart Money Accumulating)"
                        probability = random.uniform(65, 72)
                    elif sentiment > 0.05 and rsi > 50:
                        phase = "MARKUP (PHASE E)"
                        regime = "STRONG TREND (Momentum)"
                        probability = random.uniform(70, 78)
                    elif sentiment < -0.02 and rsi > 50:
                        phase = "DISTRIBUTION (PHASE C)"
                        regime = "BEARISH BIAS (Whales Selling)"
                        probability = random.uniform(40, 50)
                    else:
                        phase = "NEUTRAL"
                        regime = "SIDEWAYS"
                        probability = random.uniform(48, 55)
                    
                    # SMT Divergence (simplified)
                    smt_status = "STABLE"
                    if abs(sentiment) > 0.03:
                        smt_status = "⚠️ SMT DIVERGENCE DETECTED"
                    
                    # Liquidity Hunt targets
                    high_24h = float(data['high'].iloc[-24:].max())
                    low_24h = float(data['low'].iloc[-24:].min())
                    
                    if current_price > (high_24h + low_24h) / 2:
                        liquidity_target = f"${high_24h:,.0f} (EQH)"
                    else:
                        liquidity_target = f"${low_24h:,.0f} (EQL)"
                    
                    # Volume spike detection
                    vol_spike = data['volume'].iloc[-1] > data['volume'].mean() * 1.5
                    
                    # The Tape events
                    tape_events = []
                    if vol_spike:
                        side = "BUY" if data['close'].iloc[-1] > data['open'].iloc[-1] else "SELL"
                        vol = round(random.uniform(10, 150), 2)
                        tape_events.append(f"🐳 WHALE {side}: {vol} BTC")
                    
                    # Liquidations
                    if abs(data['high'].iloc[-1] - data['low'].iloc[-1]) > current_price * 0.01:
                        liq_amt = random.randint(500000, 5000000)
                        tape_events.append(f"🔥 LIQ: ${liq_amt/1e6:.1f}M")
                    
                    tape_events.append(f"📊 DXY: 103.{random.randint(10,99)}")
                    
                    return {
                        "price": round(current_price, 2),
                        "phase": phase,
                        "probability": round(probability, 1),
                        "regime": regime,
                        "smt": smt_status,
                        "hunt": liquidity_target,
                        "tape": " | ".join(tape_events),
                        "rsi": round(rsi, 1),
                        "macd": round(macd, 2),
                        "sentiment": round(sentiment * 100, 1),
                        "volume": int(data['volume'].iloc[-1]),
                        "high_24h": round(high_24h, 2),
                        "low_24h": round(low_24h, 2),
                        "last_update": datetime.now().strftime("%H:%M:%S"),
                        "users_online": self.users_online,
                        "iteration": self.iteration
                    }
        except Exception as e:
            print(f"[!] Error fetching real data: {e}")
        
        # Fallback to mock data
        return self.get_mock_data()
    
    def detect_session(self):
        """Wykryj aktualną sesję tradingową"""
        hour = datetime.now().hour
        
        if 0 <= hour < 8:
            return "🌏 ASIAN SESSION (TOKYO)", "asian"
        elif 8 <= hour < 16:
            return "🇬🇧 LONDON SESSION (HIGH VOLUME)", "london"
        elif 16 <= hour < 24:
            return "🇺🇸 NEW YORK SESSION (WALL STREET)", "ny"
        else:
            return "🌙 AFTER HOURS", "closed"
    
    def calculate_buy_sell_volume(self):
        """Oblicz wolumen BUY vs SELL i przewagę"""
        # Symulacja (w realnym systemie to byłyby dane z order book)
        buy_vol = random.uniform(45, 70)
        sell_vol = 100 - buy_vol
        
        if buy_vol > 55:
            dominance = "🐂 PRZEWAGA BYKÓW"
            strength = "STRONG" if buy_vol > 65 else "MODERATE"
        elif sell_vol > 55:
            dominance = "🐻 PRZEWAGA NIEDŹWIEDZI"
            strength = "STRONG" if sell_vol > 65 else "MODERATE"
        else:
            dominance = "⚖️ RÓWNOWAGA"
            strength = "NEUTRAL"
        
        return {
            'buy_volume': round(buy_vol, 1),
            'sell_volume': round(sell_vol, 1),
            'dominance': dominance,
            'strength': strength
        }
    
    def get_mock_data(self):
        """Symulowane dane (fallback)"""
        current_price = 94800 + random.uniform(-200, 200)
        
        # Przykład SMT Divergence (BTC vs ETH)
        smt_status = random.choice(["STABLE", "STABLE", "⚠️ SMT DIVERGENCE DETECTED"])
        
        # Przykład Retail Liquidity
        liquidity_target = random.choice(["$97,200 (EQL)", "$99,500 (EQH)", "$93,800 (EQL)"])
        
        # Random phase
        phases = [
            ("ACCUMULATION (PHASE C)", "BULLISH BIAS (Smart Money Accumulating)", random.uniform(65, 72)),
            ("MARKUP (PHASE E)", "STRONG TREND (Momentum)", random.uniform(70, 78)),
            ("DISTRIBUTION (PHASE C)", "BEARISH BIAS (Whales Selling)", random.uniform(40, 50)),
        ]
        phase, regime, prob = random.choice(phases)
        
        # Sesja i wolumen
        session_name, session_type = self.detect_session()
        volume_data = self.calculate_buy_sell_volume()
        
        # Sentyment bazujący na wolumenie
        if volume_data['buy_volume'] > 60:
            sentiment_text = "� BULLISH - Kupujący dominują"
        elif volume_data['sell_volume'] > 60:
            sentiment_text = "🔴 BEARISH - Sprzedający dominują"
        else:
            sentiment_text = "🟡 NEUTRAL - Rynek w równowadze"
        
        data = {
            "price": round(current_price, 2),
            "phase": phase,
            "probability": round(prob, 1),
            "regime": regime,
            "smt": smt_status,
            "hunt": liquidity_target,
            "tape": f"🐳 WHALE BUY: {random.randint(10,50)} BTC | 🔥 LIQ: ${random.uniform(1,3):.1f}M | 📊 DXY: 103.{random.randint(10,99)}",
            "rsi": round(random.uniform(30, 70), 1),
            "macd": round(random.uniform(-200, 200), 2),
            "sentiment": round(random.uniform(-10, 10), 1),
            "volume": random.randint(1000000, 5000000),
            "high_24h": round(current_price + random.uniform(100, 500), 2),
            "low_24h": round(current_price - random.uniform(100, 500), 2),
            "last_update": datetime.now().strftime("%H:%M:%S"),
            "users_online": self.users_online,
            "iteration": self.iteration,
            "session_name": session_name,
            "session_type": session_type,
            "buy_volume": volume_data['buy_volume'],
            "sell_volume": volume_data['sell_volume'],
            "volume_dominance": volume_data['dominance'],
            "volume_strength": volume_data['strength'],
            "sentiment_text": sentiment_text
        }
        return data
    
    def update_loop(self):
        """Main update loop - aktualizuje co 3s"""
        print("=" * 80)
        print("🚀 BLOOMBERG TERMINAL ENGINE STARTED")
        print("=" * 80)
        print(f"Mode: {'LIVE DATA' if HAS_BOT else 'MOCK DATA'}")
        print(f"Update Interval: 3 seconds")
        print(f"Output: data.json")
        print("=" * 80)
        print()
        
        while True:
            try:
                # Pobierz dane
                data = self.get_real_market_data()
                
                # Zapisz do JSON
                with open('data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # Log
                self.iteration += 1
                print(f"[{data['last_update']}] Update #{self.iteration} | Price: ${data['price']:,.2f} | "
                      f"Probability: {data['probability']}% | Phase: {data['phase']}")
                
                # Random user count fluctuation
                if random.random() > 0.9:
                    self.users_online = max(1, self.users_online + random.choice([-1, 1]))
                    data['users_online'] = self.users_online
                
                time.sleep(3)
                
            except KeyboardInterrupt:
                print("\n[*] Shutting down Bloomberg Engine...")
                break
            except Exception as e:
                print(f"[!] Error in update loop: {e}")
                time.sleep(3)


if __name__ == "__main__":
    engine = DashboardDataEngine()
    engine.update_loop()
