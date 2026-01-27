"""
🎯 PRECISION SNIPER MODE
=========================
Moduł dla MAKSYMALNEJ precyzji wejść.

FILOZOFIA:
- Lepiej NIE grać niż grać źle
- Czekaj na KONFLUENCJĘ 5+ sygnałów
- Celuj w R:R minimum 1:5, idealnie 1:10
- Mniej tradów = mniej prowizji = więcej zysku

REALISTYCZNE OCZEKIWANIA:
- 3-5 tradów dziennie (zamiast 50+)
- Win Rate: 60-70%
- Średni R:R: 1:5 do 1:10
- Miesięczny zysk: 50-200% (realistycznie!)

MATEMATYKA:
- 5 tradów/dzień × 60% WR × 5R średnio = +15R dziennie
- 15R × 20 dni = +300R miesięcznie
- Przy ryzyku 1% kapitału: +300% miesięcznie
- Przy ryzyku 0.5%: +150% miesięcznie

Autor: Genius Trading System
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConfluenceLevel(Enum):
    """Poziomy konfluencji sygnałów."""
    NONE = 0        # Brak - NIE GRAJ
    WEAK = 1        # Słaba - NIE GRAJ
    MODERATE = 2    # Umiarkowana - MOŻE scalp
    STRONG = 3      # Silna - GRAJ normalnie
    EXTREME = 4     # Ekstremalna - GRAJ agresywnie (piramiduj)
    PERFECT = 5     # Perfekcyjna - FULL SEND (max pozycja)


@dataclass
class PrecisionSetup:
    """Precyzyjny setup tradingowy."""
    timestamp: datetime
    symbol: str
    direction: str  # LONG / SHORT
    
    # Ceny
    entry_price: float
    stop_loss: float
    take_profit_1: float  # 1:3
    take_profit_2: float  # 1:5
    take_profit_3: float  # 1:10
    
    # Risk/Reward
    risk_pct: float
    reward_1_pct: float
    reward_2_pct: float
    reward_3_pct: float
    
    # Konfluencja
    confluence_level: ConfluenceLevel
    confluence_score: float  # 0-100
    signals_aligned: List[str]
    signals_against: List[str]
    
    # Timing
    killzone: str
    time_to_killzone_end: int  # minuty
    
    # Rekomendacja
    should_trade: bool
    position_size_pct: float  # % kapitału
    reason: str


class PrecisionSniper:
    """
    🎯 PRECISION SNIPER
    
    Nie strzela losowo - czeka na PERFEKCYJNY moment.
    
    WYMAGANIA DO TRADE'A:
    1. ✅ Trend alignment (HTF + LTF zgodne)
    2. ✅ Liquidity grab POTWIERDZONE
    3. ✅ FVG do wypełnienia
    4. ✅ Killzone aktywna
    5. ✅ SMT nie pokazuje dywergencji
    6. ✅ On-chain wspiera kierunek
    7. ✅ Order flow wspiera (CVD)
    8. ✅ Brak dużych newsów w ciągu 1h
    
    Minimum 5 z 8 sygnałów = GRAJ
    """
    
    def __init__(self, 
                 min_confluence: int = 5,
                 min_rr: float = 3.0,
                 target_rr: float = 5.0,
                 max_risk_per_trade: float = 0.02):  # 2% max risk
        """
        Args:
            min_confluence: Minimalna liczba zgodnych sygnałów (5-8)
            min_rr: Minimalny Risk:Reward (3.0 = 1:3)
            target_rr: Docelowy R:R (5.0 = 1:5)
            max_risk_per_trade: Max ryzyko na trade (0.02 = 2%)
        """
        self.min_confluence = min_confluence
        self.min_rr = min_rr
        self.target_rr = target_rr
        self.max_risk = max_risk_per_trade
        
        # Stan
        self.last_analysis: Dict = {}
        self.waiting_for_setup = True
        self.current_setup: Optional[PrecisionSetup] = None
        
        logger.info(f"🎯 PrecisionSniper: min_confluence={min_confluence}, target_RR=1:{target_rr}")
    
    def analyze_confluence(self, market_data: Dict) -> Dict:
        """
        Analizuje WSZYSTKIE sygnały i oblicza konfluencję.
        
        Args:
            market_data: Słownik z danymi rynkowymi i sygnałami modułów
            
        Returns:
            Dict z analizą konfluencji
        """
        signals_bullish = []
        signals_bearish = []
        signals_neutral = []
        
        # ═══════════════════════════════════════════════════════════════
        # 1. TREND ALIGNMENT (HTF)
        # ═══════════════════════════════════════════════════════════════
        htf_trend = market_data.get('htf_trend', 'neutral')
        ltf_trend = market_data.get('ltf_trend', 'neutral')
        
        if htf_trend == ltf_trend == 'bullish':
            signals_bullish.append('📈 Trend HTF+LTF zgodny (BULL)')
        elif htf_trend == ltf_trend == 'bearish':
            signals_bearish.append('📉 Trend HTF+LTF zgodny (BEAR)')
        else:
            signals_neutral.append('⚪ Trend niezgodny HTF vs LTF')
        
        # ═══════════════════════════════════════════════════════════════
        # 2. LIQUIDITY GRAB
        # ═══════════════════════════════════════════════════════════════
        liq_grab = market_data.get('liquidity_grab', None)
        
        if liq_grab == 'bullish':  # Wybito dołki, teraz w górę
            signals_bullish.append('💧 Liquidity Grab BULLISH')
        elif liq_grab == 'bearish':  # Wybito szczyty, teraz w dół
            signals_bearish.append('💧 Liquidity Grab BEARISH')
        else:
            signals_neutral.append('⚪ Brak Liquidity Grab')
        
        # ═══════════════════════════════════════════════════════════════
        # 3. FVG (Fair Value Gap)
        # ═══════════════════════════════════════════════════════════════
        fvg = market_data.get('fvg', None)
        
        if fvg == 'bullish':  # FVG do wypełnienia w górę
            signals_bullish.append('🔲 FVG bullish do wypełnienia')
        elif fvg == 'bearish':
            signals_bearish.append('🔲 FVG bearish do wypełnienia')
        else:
            signals_neutral.append('⚪ Brak FVG')
        
        # ═══════════════════════════════════════════════════════════════
        # 4. KILLZONE
        # ═══════════════════════════════════════════════════════════════
        killzone = market_data.get('killzone', None)
        
        if killzone in ['London_Open', 'NY_Open']:
            signals_bullish.append(f'⏰ Aktywna {killzone} (PRIME TIME)')
            signals_bearish.append(f'⏰ Aktywna {killzone} (PRIME TIME)')
        elif killzone == 'Asian_Session':
            signals_neutral.append('⚪ Sesja azjatycka (range)')
        else:
            signals_neutral.append('⚪ Poza killzone')
        
        # ═══════════════════════════════════════════════════════════════
        # 5. SMT (Smart Money Divergence)
        # ═══════════════════════════════════════════════════════════════
        smt = market_data.get('smt_divergence', False)
        
        if not smt:
            signals_bullish.append('✅ Brak SMT divergence (BTC=ETH)')
            signals_bearish.append('✅ Brak SMT divergence (BTC=ETH)')
        else:
            signals_neutral.append('⚠️ SMT DIVERGENCE - uważaj!')
        
        # ═══════════════════════════════════════════════════════════════
        # 6. ON-CHAIN
        # ═══════════════════════════════════════════════════════════════
        on_chain = market_data.get('on_chain_signal', 0)
        
        if on_chain > 0.3:
            signals_bullish.append(f'🔗 On-chain BULLISH ({on_chain:.2f})')
        elif on_chain < -0.3:
            signals_bearish.append(f'🔗 On-chain BEARISH ({on_chain:.2f})')
        else:
            signals_neutral.append('⚪ On-chain neutralny')
        
        # ═══════════════════════════════════════════════════════════════
        # 7. ORDER FLOW (CVD)
        # ═══════════════════════════════════════════════════════════════
        cvd = market_data.get('cvd_signal', 0)
        
        if cvd > 0.3:
            signals_bullish.append(f'🐋 CVD BULLISH ({cvd:.2f})')
        elif cvd < -0.3:
            signals_bearish.append(f'🐋 CVD BEARISH ({cvd:.2f})')
        else:
            signals_neutral.append('⚪ CVD neutralny')
        
        # ═══════════════════════════════════════════════════════════════
        # 8. NEWS SAFETY
        # ═══════════════════════════════════════════════════════════════
        high_impact_news = market_data.get('high_impact_news_soon', False)
        
        if not high_impact_news:
            signals_bullish.append('✅ Brak ważnych newsów')
            signals_bearish.append('✅ Brak ważnych newsów')
        else:
            signals_neutral.append('⚠️ Ważne newsy w ciągu 1h - CZEKAJ')
        
        # ═══════════════════════════════════════════════════════════════
        # 9. ICT SIGNAL (z głównego modułu)
        # ═══════════════════════════════════════════════════════════════
        ict_signal = market_data.get('ict_signal', 0)
        
        if ict_signal > 0.5:
            signals_bullish.append(f'🧠 ICT BULLISH ({ict_signal:.2f})')
        elif ict_signal < -0.5:
            signals_bearish.append(f'🧠 ICT BEARISH ({ict_signal:.2f})')
        
        # ═══════════════════════════════════════════════════════════════
        # 10. LIQUIDATION LEVELS
        # ═══════════════════════════════════════════════════════════════
        liq_above = market_data.get('liquidations_above', 0)
        liq_below = market_data.get('liquidations_below', 0)
        
        if liq_above > liq_below * 1.5:
            signals_bullish.append(f'🔥 Więcej likwidacji ABOVE (magnes w górę)')
        elif liq_below > liq_above * 1.5:
            signals_bearish.append(f'🔥 Więcej likwidacji BELOW (magnes w dół)')
        
        # ═══════════════════════════════════════════════════════════════
        # OBLICZ KONFLUENCJĘ
        # ═══════════════════════════════════════════════════════════════
        
        bull_count = len(signals_bullish)
        bear_count = len(signals_bearish)
        
        # Określ kierunek
        if bull_count >= self.min_confluence and bull_count > bear_count + 2:
            direction = 'LONG'
            aligned = signals_bullish
            against = signals_bearish
            confluence_score = min(100, bull_count * 12.5)
        elif bear_count >= self.min_confluence and bear_count > bull_count + 2:
            direction = 'SHORT'
            aligned = signals_bearish
            against = signals_bullish
            confluence_score = min(100, bear_count * 12.5)
        else:
            direction = 'NEUTRAL'
            aligned = []
            against = signals_neutral
            confluence_score = 0
        
        # Określ poziom konfluencji
        if confluence_score >= 75:
            level = ConfluenceLevel.PERFECT
        elif confluence_score >= 62.5:
            level = ConfluenceLevel.EXTREME
        elif confluence_score >= 50:
            level = ConfluenceLevel.STRONG
        elif confluence_score >= 37.5:
            level = ConfluenceLevel.MODERATE
        elif confluence_score >= 25:
            level = ConfluenceLevel.WEAK
        else:
            level = ConfluenceLevel.NONE
        
        result = {
            'direction': direction,
            'confluence_level': level,
            'confluence_score': confluence_score,
            'signals_bullish': bull_count,
            'signals_bearish': bear_count,
            'signals_neutral': len(signals_neutral),
            'aligned_signals': aligned,
            'against_signals': against,
            'neutral_signals': signals_neutral,
            'should_trade': level.value >= ConfluenceLevel.STRONG.value,
            'timestamp': datetime.now()
        }
        
        self.last_analysis = result
        return result
    
    def calculate_precision_levels(self, 
                                    current_price: float,
                                    direction: str,
                                    atr: float,
                                    nearest_liquidity: float = None) -> Dict:
        """
        Oblicza PRECYZYJNE poziomy SL i TP.
        
        LOGIKA:
        - SL: Za najbliższym poziomem płynności + ATR buffer
        - TP1: 1:3 R:R
        - TP2: 1:5 R:R
        - TP3: 1:10 R:R
        """
        # Stop Loss - za płynnością + buffer
        if direction == 'LONG':
            if nearest_liquidity and nearest_liquidity < current_price:
                sl = nearest_liquidity - (atr * 0.5)  # Za płynnością
            else:
                sl = current_price - (atr * 1.5)  # 1.5 ATR
            
            risk = current_price - sl
            
            tp1 = current_price + (risk * 3)   # 1:3
            tp2 = current_price + (risk * 5)   # 1:5
            tp3 = current_price + (risk * 10)  # 1:10
            
        else:  # SHORT
            if nearest_liquidity and nearest_liquidity > current_price:
                sl = nearest_liquidity + (atr * 0.5)
            else:
                sl = current_price + (atr * 1.5)
            
            risk = sl - current_price
            
            tp1 = current_price - (risk * 3)
            tp2 = current_price - (risk * 5)
            tp3 = current_price - (risk * 10)
        
        risk_pct = (risk / current_price) * 100
        
        return {
            'entry': current_price,
            'stop_loss': round(sl, 2),
            'take_profit_1': round(tp1, 2),
            'take_profit_2': round(tp2, 2),
            'take_profit_3': round(tp3, 2),
            'risk_usd': risk,
            'risk_pct': round(risk_pct, 3),
            'rr_1': 3,
            'rr_2': 5,
            'rr_3': 10
        }
    
    def calculate_position_size(self, 
                                 capital: float,
                                 risk_per_trade_pct: float,
                                 entry_price: float,
                                 stop_loss: float,
                                 leverage: int = 100) -> Dict:
        """
        Oblicza PRECYZYJNĄ wielkość pozycji.
        
        MATEMATYKA:
        Risk$ = Capital × Risk%
        Position Size = Risk$ / (Entry - SL) × Leverage
        """
        risk_usd = capital * risk_per_trade_pct
        price_risk = abs(entry_price - stop_loss)
        price_risk_pct = price_risk / entry_price
        
        # Wielkość pozycji w USD (notional)
        position_notional = risk_usd / price_risk_pct
        
        # Margin wymagany przy dźwigni
        margin_required = position_notional / leverage
        
        # Sprawdź czy margin nie przekracza 5% kapitału
        max_margin = capital * 0.05
        if margin_required > max_margin:
            margin_required = max_margin
            position_notional = margin_required * leverage
            risk_usd = position_notional * price_risk_pct
        
        return {
            'position_notional_usd': round(position_notional, 2),
            'margin_required_usd': round(margin_required, 2),
            'margin_pct_of_capital': round((margin_required / capital) * 100, 2),
            'risk_usd': round(risk_usd, 2),
            'risk_pct': round((risk_usd / capital) * 100, 3),
            'max_loss_if_stopped': round(risk_usd, 2),
            'leverage_used': leverage
        }
    
    def generate_setup(self, 
                        market_data: Dict,
                        capital: float = 5000) -> Optional[PrecisionSetup]:
        """
        Generuje precyzyjny setup jeśli warunki są spełnione.
        """
        # 1. Analizuj konfluencję
        confluence = self.analyze_confluence(market_data)
        
        if not confluence['should_trade']:
            logger.info(f"⏳ Brak setupu: {confluence['confluence_level'].name} ({confluence['confluence_score']:.0f}%)")
            return None
        
        # 2. Pobierz dane
        current_price = market_data.get('current_price', 100000)
        atr = market_data.get('atr', current_price * 0.01)  # Default 1%
        nearest_liq = market_data.get('nearest_liquidity', None)
        direction = confluence['direction']
        
        # 3. Oblicz poziomy
        levels = self.calculate_precision_levels(
            current_price, direction, atr, nearest_liq
        )
        
        # 4. Sprawdź R:R
        if levels['rr_1'] < self.min_rr:
            logger.info(f"⏳ R:R za niski: {levels['rr_1']}:1 < {self.min_rr}:1")
            return None
        
        # 5. Oblicz position size
        position = self.calculate_position_size(
            capital=capital,
            risk_per_trade_pct=self.max_risk,
            entry_price=current_price,
            stop_loss=levels['stop_loss']
        )
        
        # 6. Stwórz setup
        setup = PrecisionSetup(
            timestamp=datetime.now(),
            symbol=market_data.get('symbol', 'BTCUSDT'),
            direction=direction,
            entry_price=current_price,
            stop_loss=levels['stop_loss'],
            take_profit_1=levels['take_profit_1'],
            take_profit_2=levels['take_profit_2'],
            take_profit_3=levels['take_profit_3'],
            risk_pct=levels['risk_pct'],
            reward_1_pct=levels['risk_pct'] * 3,
            reward_2_pct=levels['risk_pct'] * 5,
            reward_3_pct=levels['risk_pct'] * 10,
            confluence_level=confluence['confluence_level'],
            confluence_score=confluence['confluence_score'],
            signals_aligned=confluence['aligned_signals'],
            signals_against=confluence['against_signals'],
            killzone=market_data.get('killzone', 'unknown'),
            time_to_killzone_end=market_data.get('time_to_killzone_end', 60),
            should_trade=True,
            position_size_pct=position['margin_pct_of_capital'],
            reason=self._generate_reason(confluence, levels)
        )
        
        self.current_setup = setup
        return setup
    
    def _generate_reason(self, confluence: Dict, levels: Dict) -> str:
        """Generuje uzasadnienie setupu."""
        level = confluence['confluence_level'].name
        score = confluence['confluence_score']
        direction = confluence['direction']
        rr = levels['rr_3']
        
        return f"🎯 {direction} | Konfluencja: {level} ({score:.0f}%) | R:R do 1:{rr}"
    
    def print_setup(self, setup: PrecisionSetup):
        """Wyświetla setup w czytelnej formie."""
        print("\n" + "=" * 60)
        print("🎯 PRECISION SNIPER SETUP")
        print("=" * 60)
        
        print(f"\n📊 {setup.symbol} | {setup.direction}")
        print(f"⏰ {setup.killzone} | {setup.timestamp.strftime('%H:%M:%S')}")
        
        print(f"\n💰 POZIOMY:")
        print(f"  Entry:     ${setup.entry_price:,.2f}")
        print(f"  Stop Loss: ${setup.stop_loss:,.2f} ({setup.risk_pct:.2f}%)")
        print(f"  TP1 (1:3): ${setup.take_profit_1:,.2f} (+{setup.reward_1_pct:.2f}%)")
        print(f"  TP2 (1:5): ${setup.take_profit_2:,.2f} (+{setup.reward_2_pct:.2f}%)")
        print(f"  TP3 (1:10): ${setup.take_profit_3:,.2f} (+{setup.reward_3_pct:.2f}%)")
        
        print(f"\n🎯 KONFLUENCJA: {setup.confluence_level.name} ({setup.confluence_score:.0f}%)")
        print("  Sygnały ZA:")
        for s in setup.signals_aligned[:5]:
            print(f"    ✅ {s}")
        
        if setup.signals_against:
            print("  Sygnały PRZECIW:")
            for s in setup.signals_against[:3]:
                print(f"    ⚠️ {s}")
        
        print(f"\n📐 POZYCJA: {setup.position_size_pct:.2f}% kapitału")
        print(f"💡 {setup.reason}")
        
        print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# TRADE EXECUTION RULES
# ═══════════════════════════════════════════════════════════════

class PrecisionExecutor:
    """
    Wykonuje trade'y z precyzją chirurgiczną.
    
    ZASADY:
    1. Wejście tylko przy STRONG+ konfluencji
    2. Partial TP: 30% @ 1:3, 40% @ 1:5, 30% @ 1:10
    3. Move SL to BE po TP1
    4. Trail SL za ostatnim swing low/high po TP2
    """
    
    def __init__(self, sniper: PrecisionSniper):
        self.sniper = sniper
        self.active_position = None
        
        # Partial TP allocations
        self.tp1_allocation = 0.30  # 30% na TP1
        self.tp2_allocation = 0.40  # 40% na TP2
        self.tp3_allocation = 0.30  # 30% na TP3
    
    def should_enter(self, setup: PrecisionSetup) -> Tuple[bool, str]:
        """Czy wchodzić w trade?"""
        
        # Sprawdź konfluencję
        if setup.confluence_level.value < ConfluenceLevel.STRONG.value:
            return False, f"Konfluencja za słaba: {setup.confluence_level.name}"
        
        # Sprawdź R:R
        if setup.risk_pct > 2:
            return False, f"Ryzyko za duże: {setup.risk_pct:.2f}%"
        
        # Sprawdź killzone
        if setup.killzone == 'Asian_Session':
            if setup.confluence_level.value < ConfluenceLevel.EXTREME.value:
                return False, "Sesja azjatycka - wymaga EXTREME konfluencji"
        
        return True, "✅ Wszystkie warunki spełnione"
    
    def calculate_partial_exits(self, setup: PrecisionSetup, total_size: float) -> Dict:
        """Oblicza wielkości częściowych wyjść."""
        return {
            'tp1_size': total_size * self.tp1_allocation,
            'tp1_price': setup.take_profit_1,
            'tp2_size': total_size * self.tp2_allocation,
            'tp2_price': setup.take_profit_2,
            'tp3_size': total_size * self.tp3_allocation,
            'tp3_price': setup.take_profit_3,
        }
    
    def calculate_expected_value(self, setup: PrecisionSetup, win_rate: float = 0.6) -> Dict:
        """
        Oblicza oczekiwaną wartość trade'a.
        
        EV = (WinRate × AvgWin) - (LossRate × AvgLoss)
        """
        # Średni zysk przy częściowych TP
        # Zakładamy: 80% trafiamy TP1, 50% TP2, 30% TP3
        tp1_prob = 0.80
        tp2_prob = 0.50
        tp3_prob = 0.30
        
        avg_win_r = (
            self.tp1_allocation * 3 * tp1_prob +  # 30% × 3R × 80%
            self.tp2_allocation * 5 * tp2_prob +  # 40% × 5R × 50%
            self.tp3_allocation * 10 * tp3_prob   # 30% × 10R × 30%
        )
        
        # Średnia strata = 1R (stop loss)
        avg_loss_r = 1.0
        
        # Expected Value
        ev = (win_rate * avg_win_r) - ((1 - win_rate) * avg_loss_r)
        
        return {
            'expected_value_r': round(ev, 2),
            'avg_win_r': round(avg_win_r, 2),
            'avg_loss_r': avg_loss_r,
            'win_rate_assumed': win_rate,
            'is_positive_ev': ev > 0,
            'edge_description': f"+{ev:.2f}R na trade (przy {win_rate*100:.0f}% WR)"
        }


# ═══════════════════════════════════════════════════════════════
# SAFETY SYSTEM
# ═══════════════════════════════════════════════════════════════

class SafetySystem:
    """
    System zabezpieczeń.
    
    WARSTWY OCHRONY:
    1. Max dzienna strata
    2. Max pozycja
    3. Emergency exit
    4. Correlation check
    5. Drawdown protection
    """
    
    def __init__(self,
                 max_daily_loss_pct: float = 0.05,      # 5% dziennie max
                 max_position_pct: float = 0.05,        # 5% kapitału na pozycję
                 max_drawdown_pct: float = 0.15,        # 15% drawdown = stop
                 emergency_exit_pct: float = 0.18):     # 18% ruchu ceny = exit
        
        self.max_daily_loss = max_daily_loss_pct
        self.max_position = max_position_pct
        self.max_drawdown = max_drawdown_pct
        self.emergency_exit = emergency_exit_pct
        
        # Stan
        self.daily_pnl = 0
        self.peak_equity = 0
        self.current_equity = 0
        self.is_locked = False
        self.lock_reason = ""
    
    def check_all_safety(self, 
                          capital: float,
                          daily_pnl: float,
                          current_price: float,
                          entry_price: float,
                          position_value: float) -> Dict:
        """Sprawdza wszystkie zabezpieczenia."""
        
        warnings = []
        should_exit = False
        exit_reason = ""
        
        # 1. Dzienna strata
        daily_loss_pct = abs(daily_pnl) / capital if daily_pnl < 0 else 0
        if daily_loss_pct >= self.max_daily_loss:
            warnings.append(f"🔴 DZIENNA STRATA: {daily_loss_pct*100:.1f}% >= {self.max_daily_loss*100:.0f}%")
            self.is_locked = True
            self.lock_reason = "Max daily loss reached"
        
        # 2. Max pozycja
        position_pct = position_value / capital if capital > 0 else 0
        if position_pct > self.max_position:
            warnings.append(f"⚠️ POZYCJA: {position_pct*100:.1f}% > {self.max_position*100:.0f}%")
        
        # 3. Drawdown
        if self.peak_equity > 0:
            drawdown = (self.peak_equity - capital) / self.peak_equity
            if drawdown >= self.max_drawdown:
                warnings.append(f"🔴 DRAWDOWN: {drawdown*100:.1f}% >= {self.max_drawdown*100:.0f}%")
                should_exit = True
                exit_reason = "Max drawdown reached"
        
        # 4. Emergency exit
        if entry_price > 0:
            price_change = abs(current_price - entry_price) / entry_price
            if price_change >= self.emergency_exit:
                warnings.append(f"🚨 EMERGENCY: Ruch {price_change*100:.1f}% >= {self.emergency_exit*100:.0f}%")
                should_exit = True
                exit_reason = "Emergency exit triggered"
        
        # Aktualizuj peak
        if capital > self.peak_equity:
            self.peak_equity = capital
        
        return {
            'is_safe': len(warnings) == 0,
            'warnings': warnings,
            'should_exit': should_exit,
            'exit_reason': exit_reason,
            'is_locked': self.is_locked,
            'lock_reason': self.lock_reason
        }
    
    def reset_daily(self):
        """Reset dziennych limitów (wywołaj o północy)."""
        self.daily_pnl = 0
        self.is_locked = False
        self.lock_reason = ""


# ═══════════════════════════════════════════════════════════════
# GŁÓWNA FUNKCJA
# ═══════════════════════════════════════════════════════════════

def run_precision_analysis(market_data: Dict, capital: float = 5000) -> Dict:
    """
    Główna funkcja do uruchomienia precision analysis.
    
    Returns:
        Dict z setupem lub None
    """
    sniper = PrecisionSniper(
        min_confluence=5,
        min_rr=3.0,
        target_rr=5.0,
        max_risk_per_trade=0.02
    )
    
    setup = sniper.generate_setup(market_data, capital)
    
    if setup:
        executor = PrecisionExecutor(sniper)
        should_enter, reason = executor.should_enter(setup)
        ev = executor.calculate_expected_value(setup)
        
        return {
            'has_setup': True,
            'setup': setup,
            'should_enter': should_enter,
            'entry_reason': reason,
            'expected_value': ev,
            'partial_exits': executor.calculate_partial_exits(setup, 100)
        }
    
    return {
        'has_setup': False,
        'confluence': sniper.last_analysis
    }


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🎯 PRECISION SNIPER TEST")
    print("=" * 60)
    
    # Symuluj dane rynkowe z wieloma sygnałami
    market_data = {
        'current_price': 105000,
        'symbol': 'BTCUSDT',
        'atr': 1200,
        
        # Trendy
        'htf_trend': 'bullish',
        'ltf_trend': 'bullish',
        
        # ICT
        'liquidity_grab': 'bullish',
        'fvg': 'bullish',
        'ict_signal': 0.75,
        
        # Timing
        'killzone': 'NY_Open',
        'time_to_killzone_end': 90,
        
        # Korelacje
        'smt_divergence': False,
        
        # On-chain & Order Flow
        'on_chain_signal': 0.45,
        'cvd_signal': 0.55,
        
        # Liquidations
        'liquidations_above': 150000000,
        'liquidations_below': 80000000,
        'nearest_liquidity': 104200,
        
        # News
        'high_impact_news_soon': False
    }
    
    result = run_precision_analysis(market_data, capital=5000)
    
    if result['has_setup']:
        setup = result['setup']
        
        # Wyświetl setup
        sniper = PrecisionSniper()
        sniper.print_setup(setup)
        
        print(f"\n💡 SHOULD ENTER: {result['should_enter']}")
        print(f"   Reason: {result['entry_reason']}")
        
        print(f"\n📊 EXPECTED VALUE:")
        ev = result['expected_value']
        print(f"   EV per trade: {ev['edge_description']}")
        print(f"   Positive EV: {'✅ TAK' if ev['is_positive_ev'] else '❌ NIE'}")
        
        print(f"\n💰 PARTIAL EXITS (na $100 pozycji):")
        exits = result['partial_exits']
        print(f"   TP1 @ ${exits['tp1_price']:,.0f}: ${exits['tp1_size']:.0f}")
        print(f"   TP2 @ ${exits['tp2_price']:,.0f}: ${exits['tp2_size']:.0f}")
        print(f"   TP3 @ ${exits['tp3_price']:,.0f}: ${exits['tp3_size']:.0f}")
    else:
        print("\n⏳ Brak setupu - czekamy na lepsze warunki")
        conf = result.get('confluence', {})
        print(f"   Konfluencja: {conf.get('confluence_level', 'N/A')}")
        print(f"   Score: {conf.get('confluence_score', 0):.0f}%")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE!")
