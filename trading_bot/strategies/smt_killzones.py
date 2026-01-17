#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SMT - Smart Money Technique
Korelacja BTC z ETH, DXY, Nasdaq - Divergence Detection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class SMTSignal:
    """Sygnał SMT"""
    asset_1: str
    asset_2: str
    divergence_type: str  # 'bullish', 'bearish', 'none'
    strength: float  # 0-100
    manipulation_likely: bool
    details: str


class SMTAnalyzer:
    """
    Smart Money Technique - Korelacja i Divergence
    
    Zasada ICT:
    - Jeśli BTC robi nowy HIGH, a ETH nie = Bearish Divergence (manipulation)
    - Jeśli BTC robi nowy LOW, a ETH nie = Bullish Divergence (manipulation)
    - Korelacja z DXY i Nasdaq dla potwierdzenia
    """
    
    def __init__(self, lookback: int = 50):
        self.lookback = lookback
        self.correlation_threshold = 0.7
        
    def detect_divergence(self, btc_df: pd.DataFrame, 
                         eth_df: pd.DataFrame,
                         lookback: int = 20) -> SMTSignal:
        """
        Wykryj divergence między BTC a ETH
        
        Returns:
            SMTSignal z informacją o manipulacji
        """
        # Ostatnie szczyty i dołki
        btc_recent_high = btc_df['high'].tail(lookback).max()
        btc_recent_low = btc_df['low'].tail(lookback).min()
        eth_recent_high = eth_df['high'].tail(lookback).max()
        eth_recent_low = eth_df['low'].tail(lookback).min()
        
        # Obecne ceny
        btc_current = btc_df['close'].iloc[-1]
        eth_current = eth_df['close'].iloc[-1]
        
        # Czy BTC robi nowy szczyt?
        btc_new_high = btc_current >= btc_recent_high * 0.999
        eth_new_high = eth_current >= eth_recent_high * 0.999
        
        # Czy BTC robi nowy dołek?
        btc_new_low = btc_current <= btc_recent_low * 1.001
        eth_new_low = eth_current <= eth_recent_low * 1.001
        
        # BEARISH DIVERGENCE: BTC nowy szczyt, ETH nie
        if btc_new_high and not eth_new_high:
            strength = abs(btc_current - btc_recent_high) / btc_recent_high * 100
            return SMTSignal(
                asset_1='BTC',
                asset_2='ETH',
                divergence_type='bearish',
                strength=min(strength * 10, 100),
                manipulation_likely=True,
                details=f'BTC robi nowy high ${btc_current:.0f}, ETH nie potwierdza. MANIPULATION!'
            )
        
        # BULLISH DIVERGENCE: BTC nowy dołek, ETH nie
        if btc_new_low and not eth_new_low:
            strength = abs(btc_recent_low - btc_current) / btc_recent_low * 100
            return SMTSignal(
                asset_1='BTC',
                asset_2='ETH',
                divergence_type='bullish',
                strength=min(strength * 10, 100),
                manipulation_likely=True,
                details=f'BTC robi nowy low ${btc_current:.0f}, ETH nie potwierdza. MANIPULATION!'
            )
        
        # Brak divergence
        return SMTSignal(
            asset_1='BTC',
            asset_2='ETH',
            divergence_type='none',
            strength=0,
            manipulation_likely=False,
            details='Brak divergence - aktywa poruszają się zgodnie'
        )
    
    def calculate_correlation(self, df1: pd.Series, df2: pd.Series, 
                             period: int = 50) -> float:
        """
        Oblicz korelację między dwoma instrumentami
        """
        if len(df1) < period or len(df2) < period:
            return 0
        
        returns1 = df1.pct_change().tail(period)
        returns2 = df2.pct_change().tail(period)
        
        correlation = returns1.corr(returns2)
        return correlation if not np.isnan(correlation) else 0
    
    def multi_asset_analysis(self, btc_df: pd.DataFrame,
                            eth_df: pd.DataFrame = None,
                            dxy_df: pd.DataFrame = None,
                            nasdaq_df: pd.DataFrame = None) -> Dict:
        """
        Kompleksowa analiza wieloaktywowa
        
        Korelacje:
        - BTC vs ETH (powinny być skorelowane)
        - BTC vs DXY (negatywna korelacja)
        - BTC vs Nasdaq (pozytywna korelacja)
        """
        results = {
            'btc_eth_divergence': None,
            'btc_dxy_correlation': None,
            'btc_nasdaq_correlation': None,
            'overall_sentiment': 'neutral',
            'manipulation_score': 0
        }
        
        # BTC vs ETH divergence
        if eth_df is not None:
            results['btc_eth_divergence'] = self.detect_divergence(btc_df, eth_df)
            
            # Korelacja
            btc_eth_corr = self.calculate_correlation(
                btc_df['close'], eth_df['close']
            )
            results['btc_eth_correlation'] = btc_eth_corr
            
            if results['btc_eth_divergence'].manipulation_likely:
                results['manipulation_score'] += 50
        
        # BTC vs DXY (Dollar Index)
        if dxy_df is not None:
            btc_dxy_corr = self.calculate_correlation(
                btc_df['close'], dxy_df['close']
            )
            results['btc_dxy_correlation'] = btc_dxy_corr
            
            # DXY rosnący powinien oznaczać spadek BTC
            if btc_dxy_corr > 0.3:  # Pozytywna korelacja to anomalia
                results['manipulation_score'] += 25
                results['dxy_warning'] = 'BTC rośnie z DXY - nietypowe!'
        
        # BTC vs Nasdaq
        if nasdaq_df is not None:
            btc_nasdaq_corr = self.calculate_correlation(
                btc_df['close'], nasdaq_df['close']
            )
            results['btc_nasdaq_correlation'] = btc_nasdaq_corr
            
            # Sprawdź czy zgodność
            btc_trend = 'up' if btc_df['close'].iloc[-1] > btc_df['close'].iloc[-10] else 'down'
            nasdaq_trend = 'up' if nasdaq_df['close'].iloc[-1] > nasdaq_df['close'].iloc[-10] else 'down'
            
            if btc_trend != nasdaq_trend:
                results['manipulation_score'] += 25
                results['nasdaq_warning'] = 'BTC i Nasdaq w przeciwnych kierunkach!'
        
        # Overall sentiment
        if results['manipulation_score'] > 50:
            results['overall_sentiment'] = 'manipulation_likely'
        elif results['manipulation_score'] > 25:
            results['overall_sentiment'] = 'caution'
        else:
            results['overall_sentiment'] = 'normal'
        
        return results
    
    def get_trading_recommendation(self, smt_analysis: Dict) -> str:
        """
        Rekomendacja tradingowa na podstawie SMT
        """
        manip_score = smt_analysis['manipulation_score']
        
        if manip_score > 75:
            return "🚨 WYSOKIE RYZYKO MANIPULACJI! Unikaj longu na szczycie / shortu na dołku."
        elif manip_score > 50:
            return "⚠️ Możliwa manipulacja. Czekaj na potwierdzenie lub graj kontrę."
        elif manip_score > 25:
            return "⚡ Lekka divergence. Obserwuj rozwój sytuacji."
        else:
            return "✅ Normalna korelacja. Możesz grać zgodnie z trendem."


class KillzonesManager:
    """
    Killzones - Optymalne czasy handlu
    
    ICT Killzones:
    - London Open: 02:00-05:00 EST (08:00-11:00 CET)
    - New York AM: 07:00-10:00 EST (13:00-16:00 CET)
    - New York PM: 13:30-16:00 EST (19:30-22:00 CET)
    - Asia Session: 20:00-00:00 EST (02:00-06:00 CET)
    """
    
    def __init__(self):
        # Killzones w UTC
        self.killzones = {
            'london_open': {'start': 7, 'end': 10, 'priority': 'high'},
            'ny_am': {'start': 12, 'end': 15, 'priority': 'high'},
            'ny_pm': {'start': 18, 'end': 21, 'priority': 'medium'},
            'asia': {'start': 1, 'end': 5, 'priority': 'low'}
        }
        
    def get_current_killzone(self, current_time: pd.Timestamp = None) -> Dict:
        """
        Określ aktualną killzone
        """
        if current_time is None:
            current_time = pd.Timestamp.now(tz='UTC')
        
        hour = current_time.hour
        
        for name, zone in self.killzones.items():
            if zone['start'] <= hour < zone['end']:
                return {
                    'name': name,
                    'priority': zone['priority'],
                    'active': True,
                    'recommendation': self._get_recommendation(zone['priority'])
                }
        
        return {
            'name': 'chop_hours',
            'priority': 'avoid',
            'active': False,
            'recommendation': 'Unikaj agresywnego tradingu. Tylko scalpy lub czekaj na killzone.'
        }
    
    def _get_recommendation(self, priority: str) -> str:
        """Rekomendacje dla różnych killzones"""
        if priority == 'high':
            return "✅ PRIME TIME! Wysoka płynność, najlepsze setup'y."
        elif priority == 'medium':
            return "⚡ Dobry czas na handel, ale mniej płynności."
        else:
            return "⏸️ Niska aktywność. Tylko dla doświadczonych."
    
    def should_trade_now(self, current_time: pd.Timestamp = None,
                        min_priority: str = 'medium') -> bool:
        """
        Czy bot powinien handlować w tym momencie?
        """
        zone = self.get_current_killzone(current_time)
        
        priority_order = {'high': 3, 'medium': 2, 'low': 1, 'avoid': 0}
        
        return priority_order.get(zone['priority'], 0) >= priority_order.get(min_priority, 2)
    
    def get_next_killzone(self, current_time: pd.Timestamp = None) -> Dict:
        """
        Kiedy będzie następna killzone?
        """
        if current_time is None:
            current_time = pd.Timestamp.now(tz='UTC')
        
        hour = current_time.hour
        
        # Znajdź następną killzone
        upcoming = []
        for name, zone in self.killzones.items():
            if zone['start'] > hour:
                hours_until = zone['start'] - hour
                upcoming.append({
                    'name': name,
                    'hours_until': hours_until,
                    'priority': zone['priority']
                })
        
        if upcoming:
            next_zone = min(upcoming, key=lambda x: x['hours_until'])
            return next_zone
        else:
            # Następna killzone jest jutro
            return {
                'name': 'london_open',
                'hours_until': 24 - hour + self.killzones['london_open']['start'],
                'priority': 'high'
            }


def demo_smt_killzones():
    """Demo SMT i Killzones"""
    
    print("=" * 60)
    print("🎯 SMT & KILLZONES - DEMO")
    print("=" * 60)
    
    # Generate fake data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    
    btc_prices = 100000 * np.exp(np.cumsum(np.random.normal(0.0001, 0.02, 100)))
    eth_prices = 4000 * np.exp(np.cumsum(np.random.normal(0.0001, 0.018, 100)))
    
    btc_df = pd.DataFrame({
        'open': btc_prices,
        'high': btc_prices * 1.01,
        'low': btc_prices * 0.99,
        'close': btc_prices
    }, index=dates)
    
    eth_df = pd.DataFrame({
        'open': eth_prices,
        'high': eth_prices * 1.01,
        'low': eth_prices * 0.99,
        'close': eth_prices
    }, index=dates)
    
    # SMT Analysis
    print("\n[1] SMT ANALYSIS")
    print("-" * 60)
    
    smt = SMTAnalyzer()
    divergence = smt.detect_divergence(btc_df, eth_df)
    
    print(f"Divergence Type: {divergence.divergence_type.upper()}")
    print(f"Manipulation Likely: {divergence.manipulation_likely}")
    print(f"Strength: {divergence.strength:.1f}%")
    print(f"Details: {divergence.details}")
    
    # Multi-asset
    multi_analysis = smt.multi_asset_analysis(btc_df, eth_df)
    print(f"\nManipulation Score: {multi_analysis['manipulation_score']}/100")
    print(f"Sentiment: {multi_analysis['overall_sentiment']}")
    print(f"\nRecommendation: {smt.get_trading_recommendation(multi_analysis)}")
    
    # Killzones
    print("\n[2] KILLZONES")
    print("-" * 60)
    
    kz = KillzonesManager()
    current_zone = kz.get_current_killzone()
    
    print(f"Current Killzone: {current_zone['name'].upper()}")
    print(f"Priority: {current_zone['priority']}")
    print(f"Active: {'YES' if current_zone['active'] else 'NO'}")
    print(f"Recommendation: {current_zone['recommendation']}")
    
    should_trade = kz.should_trade_now()
    print(f"\nShould Trade Now? {'✅ YES' if should_trade else '❌ NO - Wait for killzone'}")
    
    next_zone = kz.get_next_killzone()
    print(f"\nNext Killzone: {next_zone['name']} in {next_zone['hours_until']:.0f} hours")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_smt_killzones()
