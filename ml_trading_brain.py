"""
AI TRADING BRAIN - Machine Learning & Reinforcement Learning
Bot uczy się z każdej transakcji i poprawia swoje decyzje
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import pickle
import os
from datetime import datetime, timedelta
from funding_rate_calculator import FundingRateCalculator


class TradingBrain:
    """
    AI Brain for trading bot - learns from experience
    Uses Q-Learning (Reinforcement Learning)
    """
    
    def __init__(self, learning_rate=0.1, discount_factor=0.95, epsilon=0.2):
        """
        Initialize AI brain
        
        Args:
            learning_rate: How fast bot learns (0.1 = 10%)
            discount_factor: How much bot values future rewards
            epsilon: Exploration rate (20% random exploration)
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        
        # Q-Table: stores learned values for state-action pairs
        self.q_table = {}
        
        # Experience memory
        self.memory = []
        self.max_memory_size = 10000
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0
        
        # Feature weights (learned)
        self.feature_weights = {
            'rsi': 1.0,
            'macd': 1.0,
            'momentum': 1.0,
            'volume': 1.0,
            'liquidity_grab': 2.0,
            'fvg': 1.5,
            'wyckoff': 1.2,
            'sentiment': 0.8
        }
        
        # Funding Rate Calculator
        self.funding_calculator = FundingRateCalculator()
        
    def get_state(self, indicators: Dict, market_data: Dict) -> str:
        """
        Convert market data to discrete state
        """
        # RSI state
        rsi = indicators.get('rsi', pd.Series([50])).iloc[-1]
        if rsi < 30:
            rsi_state = "oversold"
        elif rsi > 70:
            rsi_state = "overbought"
        else:
            rsi_state = "neutral"
        
        # MACD state
        macd = indicators.get('macd', pd.Series([0])).iloc[-1]
        macd_signal = indicators.get('macd_signal', pd.Series([0])).iloc[-1]
        macd_state = "bullish" if macd > macd_signal else "bearish"
        
        # Momentum state
        momentum = indicators.get('momentum', pd.Series([0])).iloc[-1]
        momentum_state = "positive" if momentum > 0 else "negative"
        
        # Volume state
        volume_ma = market_data.get('volume_ma', 1)
        current_volume = market_data.get('volume', 1)
        volume_state = "high" if current_volume > volume_ma * 1.5 else "normal"
        
        # Trend state
        price = market_data.get('price', 0)
        sma_20 = market_data.get('sma_20', price)
        trend_state = "uptrend" if price > sma_20 else "downtrend"
        
        # Combine into state string
        state = f"{rsi_state}_{macd_state}_{momentum_state}_{volume_state}_{trend_state}"
        
        return state
    
    def get_action(self, state: str, valid_actions: List[str] = None) -> str:
        """
        Choose action based on Q-table (with epsilon-greedy exploration)
        
        Args:
            state: Current market state
            valid_actions: List of valid actions ['BUY', 'SELL', 'HOLD']
        
        Returns:
            Chosen action
        """
        if valid_actions is None:
            valid_actions = ['BUY', 'SELL', 'HOLD']
        
        # Epsilon-greedy: sometimes explore randomly
        if np.random.random() < self.epsilon:
            return np.random.choice(valid_actions)
        
        # Otherwise, choose best action from Q-table
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in valid_actions}
        
        state_values = self.q_table[state]
        best_action = max(state_values, key=state_values.get)
        
        return best_action
    
    def update_q_value(self, state: str, action: str, reward: float, next_state: str):
        """
        Update Q-value based on received reward (Q-Learning algorithm)
        
        Q(s,a) = Q(s,a) + α * [R + γ * max(Q(s',a')) - Q(s,a)]
        """
        # Initialize if needed
        if state not in self.q_table:
            self.q_table[state] = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        
        if next_state not in self.q_table:
            self.q_table[next_state] = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        
        # Current Q-value
        current_q = self.q_table[state][action]
        
        # Max Q-value for next state
        max_next_q = max(self.q_table[next_state].values())
        
        # Q-Learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
    
    def learn_from_trade(self, trade_result: Dict):
        """
        Learn from completed trade
        
        Args:
            trade_result: {
                'state': state when entered,
                'action': 'BUY' or 'SELL',
                'next_state': state when exited,
                'pnl': profit/loss in $,
                'pnl_pct': profit/loss in %
            }
        """
        # Calculate reward
        reward = self._calculate_reward(trade_result)
        
        # Update Q-table
        self.update_q_value(
            state=trade_result['state'],
            action=trade_result['action'],
            reward=reward,
            next_state=trade_result['next_state']
        )
        
        # Store in memory
        self.memory.append({
            'timestamp': datetime.now(),
            'state': trade_result['state'],
            'action': trade_result['action'],
            'reward': reward,
            'pnl': trade_result['pnl']
        })
        
        # Limit memory size
        if len(self.memory) > self.max_memory_size:
            self.memory = self.memory[-self.max_memory_size:]
        
        # Update statistics
        self.total_trades += 1
        if trade_result['pnl'] > 0:
            self.winning_trades += 1
        self.total_pnl += trade_result['pnl']
        
        # Adapt weights based on performance
        self._adapt_feature_weights(trade_result)
    
    def _calculate_reward(self, trade_result: Dict) -> float:
        """
        Calculate reward for reinforcement learning
        Positive reward for profit, negative for loss
        """
        pnl_pct = trade_result.get('pnl_pct', 0)
        
        # Base reward from P&L
        reward = pnl_pct * 100  # Scale to reasonable range
        
        # Bonus for big wins
        if pnl_pct > 0.05:  # > 5% profit
            reward += 10
        elif pnl_pct > 0.10:  # > 10% profit
            reward += 50
        
        # Penalty for big losses
        if pnl_pct < -0.05:  # > 5% loss
            reward -= 20
        
        # Penalty for holding too long without profit
        hold_time = trade_result.get('hold_time_minutes', 0)
        if hold_time > 120 and pnl_pct < 0.01:  # 2 hours with no profit
            reward -= 5
        
        return reward
    
    def _adapt_feature_weights(self, trade_result: Dict):
        """
        Adapt feature weights based on trade performance
        Increases weights for features that predicted winning trades
        """
        if trade_result['pnl'] > 0:
            adjustment = 0.05  # Increase by 5%
        else:
            adjustment = -0.03  # Decrease by 3%
        
        # Get features that were active during this trade
        active_features = trade_result.get('active_features', [])
        
        for feature in active_features:
            if feature in self.feature_weights:
                self.feature_weights[feature] *= (1 + adjustment)
                # Keep weights in reasonable range
                self.feature_weights[feature] = np.clip(
                    self.feature_weights[feature], 0.1, 5.0
                )
    
    def get_confidence_score(self, indicators: Dict, market_data: Dict, 
                            action: str) -> float:
        """
        Calculate confidence score for proposed action (0-100%)
        Uses learned Q-values and feature weights
        """
        state = self.get_state(indicators, market_data)
        
        # Get Q-value for this state-action pair
        if state in self.q_table:
            q_value = self.q_table[state].get(action, 0)
            
            # Normalize Q-value to 0-100 range
            max_q = max(self.q_table[state].values())
            min_q = min(self.q_table[state].values())
            
            if max_q != min_q:
                normalized = (q_value - min_q) / (max_q - min_q) * 100
            else:
                normalized = 50
        else:
            normalized = 50  # Neutral confidence for unknown states
        
        # Adjust based on win rate
        win_rate = self.winning_trades / max(self.total_trades, 1)
        confidence = normalized * (0.5 + win_rate * 0.5)
        
        return np.clip(confidence, 0, 100)
    
    def get_optimal_position_size(self, confidence: float, 
                                  capital: float) -> float:
        """
        Calculate optimal position size based on confidence
        Uses Kelly Criterion adjusted by confidence
        
        Args:
            confidence: 0-100
            capital: Available capital
        
        Returns:
            Position size in $
        """
        # Base position size (conservative)
        base_size = capital * 0.05  # 5% of capital
        
        # Adjust based on confidence
        if confidence > 70:
            multiplier = 1.5  # 7.5% for high confidence
        elif confidence > 50:
            multiplier = 1.0  # 5% for medium confidence
        else:
            multiplier = 0.5  # 2.5% for low confidence
        
        position_size = base_size * multiplier
        
        # Cap at max position size
        max_size = capital * 0.10  # Never more than 10%
        
        return min(position_size, max_size)
    
    def should_pyramid(self, current_position: Dict, market_data: Dict) -> bool:
        """
        Decide if bot should add to winning position (pyramiding)
        """
        if not current_position:
            return False
        
        pnl_pct = current_position.get('pnl_pct', 0)
        
        # Only pyramid winning positions
        if pnl_pct < 0.02:  # Less than 2% profit
            return False
        
        # Check if we already have max pyramids
        pyramid_count = current_position.get('pyramid_count', 0)
        if pyramid_count >= 5:
            return False
        
        # Check momentum
        momentum = market_data.get('momentum', 0)
        if current_position['type'] == 'LONG' and momentum < 0:
            return False
        if current_position['type'] == 'SHORT' and momentum > 0:
            return False
        
        # AI confidence check
        confidence = self.get_confidence_score({}, market_data, current_position['type'])
        
        return confidence > 60
    
    # ==================== FUNDING RATE METHODS ====================
    
    def calculate_position_funding_cost(
        self,
        position_size_usdt: float,
        entry_price: float,
        exit_price: float,
        entry_time: datetime,
        exit_time: datetime,
        position_type: str = 'LONG',
        exchange: str = 'binance',
        leverage: int = 1,
        volatility_level: str = 'medium'
    ) -> Dict:
        """
        Oblicz funding cost dla kompletnej pozycji
        Uwzględnia: cena wejścia/wyjścia, czas holdowania, rzeczywiste fees
        """
        return self.funding_calculator.calculate_funding_cost_position(
            position_size_usdt=position_size_usdt,
            entry_price=entry_price,
            exit_price=exit_price,
            entry_time=entry_time,
            exit_time=exit_time,
            position_type=position_type,
            exchange=exchange,
            leverage=leverage,
            volatility_level=volatility_level
        )
    
    def calculate_position_break_even(
        self,
        position_size_usdt: float,
        entry_price: float,
        position_type: str = 'LONG',
        leverage: int = 1,
        exchange: str = 'binance',
        volatility_level: str = 'medium',
        hold_hours: float = 1.0
    ) -> Dict:
        """
        Oblicz break-even punkt dla pozycji
        Ile procent ruchu trzeba aby pokryć fees i funding
        """
        return self.funding_calculator.calculate_funding_break_even(
            position_size_usdt=position_size_usdt,
            entry_price=entry_price,
            position_type=position_type,
            leverage=leverage,
            exchange=exchange,
            volatility_level=volatility_level,
            hold_hours=hold_hours
        )
    
    def analyze_current_position(
        self,
        symbol: str,
        position_size_usdt: float,
        entry_price: float,
        current_price: float,
        position_type: str = 'LONG',
        leverage: int = 1,
        entry_time: datetime = None,
        exchange: str = 'binance',
        volatility_level: str = 'medium',
        coin_name: str = 'BTC'
    ) -> Dict:
        """
        Kompleksowa analiza bieżącej pozycji z fundingiem
        Uwzględnia: P&L, funding costs, fees, liquidation risk
        """
        return self.funding_calculator.calculate_position_analysis(
            symbol=symbol,
            position_size_usdt=position_size_usdt,
            entry_price=entry_price,
            current_price=current_price,
            position_type=position_type,
            leverage=leverage,
            entry_time=entry_time,
            exchange=exchange,
            volatility_level=volatility_level,
            coin_name=coin_name
        )
    
    def simulate_price_scenarios(
        self,
        position_size_usdt: float,
        entry_price: float,
        position_type: str = 'LONG',
        leverage: int = 1,
        hold_hours: float = 8.0,
        exchange: str = 'binance',
        volatility_level: str = 'medium',
        price_scenarios: List[float] = None
    ) -> Dict:
        """
        Symuluj scenariusze P&L dla różnych cen wyjścia
        Pomaga przy risk management i decyzjach TP/SL
        """
        return self.funding_calculator.simulate_position_scenarios(
            position_size_usdt=position_size_usdt,
            entry_price=entry_price,
            position_type=position_type,
            leverage=leverage,
            hold_hours=hold_hours,
            exchange=exchange,
            volatility_level=volatility_level,
            price_scenarios=price_scenarios
        )
    
    def calculate_optimal_position_with_funding(
        self,
        capital: float,
        confidence: float,
        entry_price: float,
        target_roi_percent: float = 2.0,
        max_hold_hours: float = 24.0,
        leverage: int = 10,
        exchange: str = 'binance',
        volatility_level: str = 'medium'
    ) -> Dict:
        """
        Oblicz optymalną wielkość pozycji uwzględniając funding rate
        Tak aby docelowy ROI pokrywał fees i funding costs
        """
        # Base position size
        base_position = self.get_optimal_position_size(confidence, capital)
        
        # Szacunkowy funding cost
        daily_funding_rate = self.funding_calculator.estimate_daily_funding_rate(
            exchange, volatility_level
        )
        funding_hours_rate = daily_funding_rate / 24
        estimated_funding_cost = base_position * funding_hours_rate * max_hold_hours
        
        # Fees
        taker_fee = 0.0004
        estimated_fees = base_position * taker_fee * 2
        
        # Total costs
        total_costs = estimated_funding_cost + estimated_fees
        
        # Required P&L to achieve target ROI
        margin = base_position / leverage
        required_pnl = margin * (target_roi_percent / 100)
        
        # Adjust position size if needed
        if required_pnl < total_costs:
            # Position size too small to cover costs with target ROI
            # Increase position size
            adjustment_multiplier = total_costs / required_pnl + 0.1
            optimized_position = base_position * adjustment_multiplier
        else:
            optimized_position = base_position
        
        # Cap at max position
        max_position = capital * 0.15
        optimized_position = min(optimized_position, max_position)
        
        return {
            'base_position_size': round(base_position, 2),
            'optimized_position_size': round(optimized_position, 2),
            'adjustment_multiplier': round(optimized_position / base_position, 2),
            'estimated_daily_funding_rate': round(daily_funding_rate * 100, 4),
            'estimated_funding_cost': round(estimated_funding_cost, 2),
            'estimated_fees': round(estimated_fees, 2),
            'total_estimated_costs': round(total_costs, 2),
            'target_roi_percent': target_roi_percent,
            'margin_required': round(margin, 2),
            'required_pnl': round(required_pnl, 2),
            'profitability_ratio': round(required_pnl / total_costs if total_costs > 0 else 0, 2),
            'exchange': exchange,
            'volatility_level': volatility_level,
            'max_hold_hours': max_hold_hours,
            'leverage': leverage
        }
    
    def evaluate_trade_with_funding(
        self,
        symbol: str,
        entry_price: float,
        exit_price: float,
        entry_time: datetime,
        exit_time: datetime,
        position_type: str,
        position_size_usdt: float,
        leverage: int = 1,
        exchange: str = 'binance',
        volatility_level: str = 'medium'
    ) -> Dict:
        """
        Ocen transakcję ze wszystkimi kosztami (funding, fees)
        Używane do uczenia AI z rzeczywistymi danymi
        """
        trade_data = self.calculate_position_funding_cost(
            position_size_usdt=position_size_usdt,
            entry_price=entry_price,
            exit_price=exit_price,
            entry_time=entry_time,
            exit_time=exit_time,
            position_type=position_type,
            exchange=exchange,
            leverage=leverage,
            volatility_level=volatility_level
        )
        
        return {
            'symbol': symbol,
            'position_type': position_type,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_size_usdt': position_size_usdt,
            'quantity_coins': trade_data['quantity_coins'],
            'hold_time_hours': trade_data['hold_time_hours'],
            'hold_time_days': trade_data['hold_time_days'],
            'gross_pnl': trade_data['pnl_gross'],
            'funding_cost': trade_data['total_funding_cost'],
            'fees': trade_data['total_fees'],
            'net_pnl': trade_data['pnl_net'],
            'roi_percent': trade_data['roi_percent'],
            'leverage': leverage,
            'exchange': exchange,
            'daily_funding_rate': trade_data['daily_funding_rate'],
            'entry_time': entry_time,
            'exit_time': exit_time,
            'is_profitable': trade_data['pnl_net'] > 0
        }
    
    def save_brain(self, filename: str = "trading_brain.pkl"):
        """
        Save learned Q-table and weights to file
        """
        brain_data = {
            'q_table': self.q_table,
            'feature_weights': self.feature_weights,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'total_pnl': self.total_pnl,
            'memory': self.memory[-1000:]  # Save last 1000 memories
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(brain_data, f)
        
        print(f"[✓] AI Brain saved to {filename}")
    
    def load_brain(self, filename: str = "trading_brain.pkl"):
        """
        Load previously learned Q-table and weights
        """
        if not os.path.exists(filename):
            print(f"[!] No saved brain found at {filename}")
            return False
        
        try:
            with open(filename, 'rb') as f:
                brain_data = pickle.load(f)
            
            self.q_table = brain_data.get('q_table', {})
            self.feature_weights = brain_data.get('feature_weights', self.feature_weights)
            self.total_trades = brain_data.get('total_trades', 0)
            self.winning_trades = brain_data.get('winning_trades', 0)
            self.total_pnl = brain_data.get('total_pnl', 0)
            self.memory = brain_data.get('memory', [])
            
            print(f"[✓] AI Brain loaded from {filename}")
            print(f"    Total trades: {self.total_trades}")
            print(f"    Win rate: {self.winning_trades/max(self.total_trades, 1)*100:.1f}%")
            print(f"    Total P&L: ${self.total_pnl:,.2f}")
            
            return True
            
        except Exception as e:
            print(f"[!] Error loading brain: {e}")
            return False
    
    def get_learning_stats(self) -> Dict:
        """
        Get statistics about bot's learning progress
        """
        win_rate = self.winning_trades / max(self.total_trades, 1) * 100
        avg_pnl = self.total_pnl / max(self.total_trades, 1)
        
        # Calculate exploration rate decay
        exploration_rate = self.epsilon * 100
        
        # Most learned states
        top_states = sorted(
            self.q_table.items(),
            key=lambda x: max(x[1].values()),
            reverse=True
        )[:5]
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'avg_pnl_per_trade': avg_pnl,
            'states_learned': len(self.q_table),
            'exploration_rate': exploration_rate,
            'top_learned_states': [s[0] for s in top_states],
            'feature_weights': self.feature_weights.copy()
        }
    
    def print_learning_report(self):
        """
        Print detailed learning report
        """
        stats = self.get_learning_stats()
        
        print("\n" + "="*80)
        print("AI LEARNING REPORT")
        print("="*80)
        print(f"\n📊 PERFORMANCE:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Winning Trades: {stats['winning_trades']}")
        print(f"   Win Rate: {stats['win_rate']:.1f}%")
        print(f"   Total P&L: ${stats['total_pnl']:,.2f}")
        print(f"   Avg P&L per Trade: ${stats['avg_pnl_per_trade']:,.2f}")
        
        print(f"\n🧠 LEARNING PROGRESS:")
        print(f"   States Learned: {stats['states_learned']}")
        print(f"   Exploration Rate: {stats['exploration_rate']:.1f}%")
        
        print(f"\n🎯 FEATURE WEIGHTS (learned):")
        for feature, weight in sorted(stats['feature_weights'].items(), 
                                     key=lambda x: x[1], reverse=True):
            print(f"   {feature:20s}: {weight:.2f}")
        
        print(f"\n🏆 TOP LEARNED STATES:")
        for i, state in enumerate(stats['top_learned_states'], 1):
            print(f"   {i}. {state}")
        
        print("\n" + "="*80)


# Example usage
if __name__ == "__main__":
    # Test the AI brain
    brain = TradingBrain()
    
    print("\n" + "="*80)
    print("🧠 AI TRADING BRAIN WITH FUNDING RATE CALCULATOR")
    print("="*80)
    
    # Test 1: Calculate position with funding
    print("\n[1] POSITION ANALYSIS WITH FUNDING RATE")
    print("-" * 80)
    
    entry_time = datetime.now() - timedelta(hours=4)
    exit_time = datetime.now()
    
    position_cost = brain.calculate_position_funding_cost(
        position_size_usdt=10000,
        entry_price=95000,
        exit_price=97000,
        entry_time=entry_time,
        exit_time=exit_time,
        position_type='LONG',
        leverage=10,
        exchange='binance',
        volatility_level='medium'
    )
    
    print(f"Position Size: ${position_cost['position_size_usdt']:,}")
    print(f"Quantity: {position_cost['quantity_coins']:.8f} BTC")
    print(f"Entry Price: ${position_cost['entry_price']:,}")
    print(f"Exit Price: ${position_cost['exit_price']:,}")
    print(f"Hold Time: {position_cost['hold_time_hours']:.2f} hours")
    print(f"Daily Funding Rate: {position_cost['daily_funding_rate']*100:.4f}%")
    print(f"Funding Cost: ${position_cost['total_funding_cost']:.2f}")
    print(f"Fees: ${position_cost['total_fees']:.2f}")
    print(f"Gross P&L: ${position_cost['pnl_gross']:.2f}")
    print(f"Net P&L: ${position_cost['pnl_net']:.2f}")
    print(f"ROI: {position_cost['roi_percent']:.2f}%")
    
    # Test 2: Current position analysis
    print("\n[2] CURRENT POSITION ANALYSIS")
    print("-" * 80)
    
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
    
    print(f"Symbol: {analysis['symbol']}")
    print(f"Current Price: ${analysis['current_price']:,}")
    print(f"Price Move: {analysis['price_move_percent']:.2f}%")
    print(f"Unrealized P&L: ${analysis['unrealized_pnl']:.2f}")
    print(f"Funding Cost (accumulated): ${analysis['accumulated_funding_cost']:.2f}")
    print(f"Net P&L: ${analysis['net_pnl_current']:.2f}")
    print(f"ROI: {analysis['roi_percent']:.2f}%")
    print(f"Liquidation Price: ${analysis['liquidation_price']:,}")
    print(f"Distance to Liquidation: {analysis['distance_to_liquidation_percent']:.2f}%")
    
    # Test 3: Break-even analysis
    print("\n[3] BREAK-EVEN ANALYSIS")
    print("-" * 80)
    
    break_even = brain.calculate_position_break_even(
        position_size_usdt=10000,
        entry_price=95000,
        position_type='LONG',
        leverage=10,
        hold_hours=3
    )
    
    print(f"Entry Price: ${break_even['entry_price']:,}")
    print(f"Break-Even Price: ${break_even['break_even_price']:,}")
    print(f"Price Move Needed: {break_even['move_needed_percent']:.4f}%")
    print(f"Total Cost to Recover: ${break_even['total_cost_to_recover']:.2f}")
    print(f"  - Fees: ${break_even['total_fees']:.2f}")
    print(f"  - Funding: ${break_even['funding_cost']:.2f}")
    
    # Test 4: Price scenarios
    print("\n[4] PRICE SCENARIOS (8h hold)")
    print("-" * 80)
    
    scenarios = brain.simulate_price_scenarios(
        position_size_usdt=10000,
        entry_price=95000,
        position_type='LONG',
        leverage=10,
        hold_hours=8
    )
    
    print(f"\nEntry Price: ${scenarios['entry_price']:,}")
    print(f"Daily Funding Rate: {scenarios['daily_funding_rate']:.4f}%\n")
    print(f"{'Exit Price':<15} {'Move %':<10} {'Gross P&L':<12} {'Net P&L':<12} {'ROI %':<10} {'Status':<10}")
    print("-" * 80)
    
    for s in scenarios['scenarios']:
        status = "✓ WIN" if s['profitable'] else "✗ LOSS"
        print(f"${s['exit_price']:<14.2f} {s['price_move_percent']:>8.2f}% ${s['gross_pnl']:<11.2f} ${s['net_pnl']:<11.2f} {s['roi_percent']:>8.2f}% {status:<10}")
    
    # Test 5: Optimal position sizing with funding
    print("\n[5] OPTIMAL POSITION SIZING")
    print("-" * 80)
    
    opt_position = brain.calculate_optimal_position_with_funding(
        capital=50000,
        confidence=75,
        entry_price=95000,
        target_roi_percent=2.5,
        max_hold_hours=24,
        leverage=10
    )
    
    print(f"Capital: ${capital:,}")
    print(f"Confidence: 75%")
    print(f"Target ROI: {opt_position['target_roi_percent']}%")
    print(f"\nBase Position Size: ${opt_position['base_position_size']:,}")
    print(f"Optimized Position Size: ${opt_position['optimized_position_size']:,}")
    print(f"Adjustment Multiplier: {opt_position['adjustment_multiplier']}x")
    print(f"\nEstimated Costs:")
    print(f"  - Daily Funding Rate: {opt_position['estimated_daily_funding_rate']:.4f}%")
    print(f"  - Funding Cost: ${opt_position['estimated_funding_cost']:.2f}")
    print(f"  - Fees: ${opt_position['estimated_fees']:.2f}")
    print(f"  - Total: ${opt_position['total_estimated_costs']:.2f}")
    print(f"\nProfitability: {opt_position['profitability_ratio']}x (Required P&L / Total Costs)")
    
    # Test 6: Evaluate trade
    print("\n[6] TRADE EVALUATION")
    print("-" * 80)
    
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
    
    print(f"\nTrade: {trade_eval['position_type']} {trade_eval['symbol']}")
    print(f"Entry: ${trade_eval['entry_price']:,} | Exit: ${trade_eval['exit_price']:,}")
    print(f"Position Size: ${trade_eval['position_size_usdt']:,} ({trade_eval['quantity_coins']:.8f} coins)")
    print(f"Hold Time: {trade_eval['hold_time_hours']:.2f}h")
    print(f"\nFinancial Results:")
    print(f"  Gross P&L: ${trade_eval['gross_pnl']:.2f}")
    print(f"  Funding Cost: ${trade_eval['funding_cost']:.2f}")
    print(f"  Fees: ${trade_eval['fees']:.2f}")
    print(f"  Net P&L: ${trade_eval['net_pnl']:.2f}")
    print(f"  ROI: {trade_eval['roi_percent']:.2f}%")
    print(f"  Profitable: {'YES ✓' if trade_eval['is_profitable'] else 'NO ✗'}")
    
    print("\n" + "="*80)
    print("✓ AI Brain with Funding Rate Calculator ready!")
    print("="*80)
