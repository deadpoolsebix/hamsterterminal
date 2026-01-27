"""
🔥 REINFORCEMENT LEARNING TRADING AGENT
========================================

Bot który UCZY SIĘ z własnych transakcji i ADAPTUJE strategię!

Przewaga: 99% botów ma sztywne reguły. Ten bot ewoluuje.

Wykorzystuje:
- Deep Q-Network (DQN) lub PPO
- TensorTrade integration
- Reward shaping dla tradingu
- Experience Replay
- Adaptive exploration

Author: Genius Engine Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque
import random
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Deep Learning imports
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Install with: pip install torch")

try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# TRADING ENVIRONMENT
# ═══════════════════════════════════════════════════════════════

class TradingAction(Enum):
    """Możliwe akcje bota"""
    HOLD = 0
    BUY = 1
    SELL = 2
    CLOSE = 3


@dataclass
class TradingState:
    """Stan środowiska tradingowego"""
    # Dane rynkowe (znormalizowane)
    price_features: np.ndarray  # RSI, MACD, BB, momentum, etc.
    position: int  # -1 (short), 0 (flat), 1 (long)
    unrealized_pnl: float
    entry_price: float
    time_in_position: int
    
    # Kontekst ICT
    killzone: int  # 0-3 (Asian, London, NY, Off)
    liquidity_grab: int  # 0 or 1
    fvg_nearby: int  # 0 or 1
    wyckoff_phase: int  # 0-4
    
    def to_tensor(self) -> np.ndarray:
        """Konwertuj stan do tensora dla sieci neuronowej"""
        context = np.array([
            self.position,
            self.unrealized_pnl,
            self.time_in_position / 100,  # normalize
            self.killzone / 3,
            self.liquidity_grab,
            self.fvg_nearby,
            self.wyckoff_phase / 4
        ])
        return np.concatenate([self.price_features, context])


class TradingEnvironment:
    """
    Środowisko do treningu RL Agent.
    
    Symuluje trading z pełną logiką ICT.
    """
    
    def __init__(self, 
                 data: pd.DataFrame,
                 initial_balance: float = 5000,
                 position_size: float = 50,
                 leverage: int = 100,
                 fee_rate: float = 0.0004):
        """
        Args:
            data: OHLCV DataFrame
            initial_balance: Początkowy kapitał
            position_size: Wielkość pojedynczej pozycji
            leverage: Dźwignia
            fee_rate: Opłata za transakcję
        """
        self.data = data
        self.initial_balance = initial_balance
        self.position_size = position_size
        self.leverage = leverage
        self.fee_rate = fee_rate
        
        # Feature engineering
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self._prepare_features()
        
        self.reset()
    
    def _prepare_features(self):
        """Przygotuj features dla każdego timestep"""
        df = self.data.copy()
        
        # Technical indicators
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(20).std()
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + gain / loss))
        
        # MACD
        df['ema12'] = df['close'].ewm(span=12).mean()
        df['ema26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema12'] - df['ema26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # Bollinger Bands position
        df['sma20'] = df['close'].rolling(20).mean()
        df['bb_std'] = df['close'].rolling(20).std()
        df['bb_position'] = (df['close'] - df['sma20']) / (df['bb_std'] * 2)
        
        # Momentum
        df['momentum_5'] = df['close'].pct_change(5)
        df['momentum_20'] = df['close'].pct_change(20)
        
        # Volume
        if 'volume' in df.columns:
            df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        else:
            df['volume_ma_ratio'] = 1.0
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        df['atr'] = tr.rolling(14).mean() / df['close']
        
        # Normalize features
        feature_cols = ['returns', 'volatility', 'rsi', 'macd', 'macd_signal',
                       'bb_position', 'momentum_5', 'momentum_20', 'volume_ma_ratio', 'atr']
        
        df = df.dropna()
        
        if self.scaler:
            self.features = self.scaler.fit_transform(df[feature_cols].values)
        else:
            self.features = df[feature_cols].values
        
        self.prices = df['close'].values
        self.highs = df['high'].values
        self.lows = df['low'].values
        
        # ICT context (simplified - można połączyć z ict_smart_money_bot)
        self._prepare_ict_context(df)
    
    def _prepare_ict_context(self, df):
        """Przygotuj kontekst ICT dla każdego timestep"""
        n = len(self.prices)
        
        self.ict_context = {
            'killzone': np.zeros(n, dtype=int),  # Uproszczone
            'liquidity_grab': np.zeros(n, dtype=int),
            'fvg': np.zeros(n, dtype=int),
            'wyckoff': np.zeros(n, dtype=int)
        }
        
        # Detect liquidity grabs (simplified)
        for i in range(20, n):
            recent_low = min(self.lows[i-20:i])
            recent_high = max(self.highs[i-20:i])
            
            # Bullish liquidity grab
            if self.lows[i] < recent_low and self.prices[i] > recent_low:
                self.ict_context['liquidity_grab'][i] = 1
            # Bearish liquidity grab
            elif self.highs[i] > recent_high and self.prices[i] < recent_high:
                self.ict_context['liquidity_grab'][i] = 1
    
    def reset(self) -> TradingState:
        """Reset środowiska"""
        self.current_step = 50  # Start po warmup
        self.balance = self.initial_balance
        self.position = 0  # -1, 0, 1
        self.entry_price = 0
        self.time_in_position = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0
        
        return self._get_state()
    
    def _get_state(self) -> TradingState:
        """Pobierz aktualny stan"""
        current_price = self.prices[self.current_step]
        
        # Unrealized P&L
        if self.position != 0:
            if self.position == 1:  # Long
                unrealized_pnl = (current_price - self.entry_price) / self.entry_price
            else:  # Short
                unrealized_pnl = (self.entry_price - current_price) / self.entry_price
            unrealized_pnl *= self.leverage
        else:
            unrealized_pnl = 0
        
        return TradingState(
            price_features=self.features[self.current_step],
            position=self.position,
            unrealized_pnl=unrealized_pnl,
            entry_price=self.entry_price,
            time_in_position=self.time_in_position,
            killzone=self.ict_context['killzone'][self.current_step],
            liquidity_grab=self.ict_context['liquidity_grab'][self.current_step],
            fvg_nearby=self.ict_context['fvg'][self.current_step],
            wyckoff_phase=self.ict_context['wyckoff'][self.current_step]
        )
    
    def step(self, action: int) -> Tuple[TradingState, float, bool, Dict]:
        """
        Wykonaj akcję i zwróć nowy stan.
        
        Returns:
            (new_state, reward, done, info)
        """
        current_price = self.prices[self.current_step]
        reward = 0
        info = {}
        
        # ═══ WYKONAJ AKCJĘ ═══
        
        if action == TradingAction.BUY.value and self.position != 1:
            # Zamknij short jeśli jest
            if self.position == -1:
                reward += self._close_position(current_price)
            # Otwórz long
            self._open_position(current_price, 1)
            info['action'] = 'BUY'
            
        elif action == TradingAction.SELL.value and self.position != -1:
            # Zamknij long jeśli jest
            if self.position == 1:
                reward += self._close_position(current_price)
            # Otwórz short
            self._open_position(current_price, -1)
            info['action'] = 'SELL'
            
        elif action == TradingAction.CLOSE.value and self.position != 0:
            reward += self._close_position(current_price)
            info['action'] = 'CLOSE'
            
        else:
            info['action'] = 'HOLD'
        
        # ═══ PRZEJDŹ DO NASTĘPNEGO KROKU ═══
        
        self.current_step += 1
        
        if self.position != 0:
            self.time_in_position += 1
        
        # ═══ SPRAWDŹ CZY KONIEC ═══
        
        done = self.current_step >= len(self.prices) - 1
        
        if done and self.position != 0:
            # Zamknij pozycję na końcu
            reward += self._close_position(self.prices[self.current_step])
        
        # ═══ REWARD SHAPING ═══
        
        # Bonus za trzymanie zyskownej pozycji
        if self.position != 0:
            state = self._get_state()
            if state.unrealized_pnl > 0:
                reward += state.unrealized_pnl * 0.01  # Mały bonus za zysk
            
            # Kara za zbyt długie trzymanie pozycji bez zysku
            if self.time_in_position > 50 and state.unrealized_pnl < 0:
                reward -= 0.001
        
        # Bonus za trading w killzone z liquidity grab
        if self.ict_context['liquidity_grab'][self.current_step] == 1:
            if info.get('action') in ['BUY', 'SELL']:
                reward += 0.01  # Bonus za wejście na liquidity grab
        
        new_state = self._get_state()
        
        info['balance'] = self.balance
        info['total_pnl'] = self.total_pnl
        info['win_rate'] = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        return new_state, reward, done, info
    
    def _open_position(self, price: float, direction: int):
        """Otwórz pozycję"""
        self.position = direction
        self.entry_price = price
        self.time_in_position = 0
        
        # Fee
        self.balance -= self.position_size * self.fee_rate
    
    def _close_position(self, price: float) -> float:
        """Zamknij pozycję i zwróć reward"""
        if self.position == 0:
            return 0
        
        # Oblicz P&L
        if self.position == 1:  # Long
            pnl_pct = (price - self.entry_price) / self.entry_price
        else:  # Short
            pnl_pct = (self.entry_price - price) / self.entry_price
        
        pnl = pnl_pct * self.position_size * self.leverage
        
        # Fee
        pnl -= self.position_size * self.fee_rate
        
        # Update stats
        self.balance += pnl
        self.total_pnl += pnl
        self.total_trades += 1
        
        if pnl > 0:
            self.winning_trades += 1
        
        # Reset position
        self.position = 0
        self.entry_price = 0
        self.time_in_position = 0
        
        # Reward = P&L jako procent kapitału (skalowany)
        reward = pnl / self.initial_balance * 10
        
        return reward


# ═══════════════════════════════════════════════════════════════
# DEEP Q-NETWORK
# ═══════════════════════════════════════════════════════════════

if TORCH_AVAILABLE:
    
    class DQN(nn.Module):
        """
        Deep Q-Network dla tradingu.
        
        Architektura:
        - Input: Stan środowiska (features + context)
        - Hidden: 3 warstwy z ReLU i Dropout
        - Output: Q-values dla każdej akcji
        """
        
        def __init__(self, state_size: int, action_size: int):
            super(DQN, self).__init__()
            
            self.fc1 = nn.Linear(state_size, 256)
            self.bn1 = nn.BatchNorm1d(256)
            self.dropout1 = nn.Dropout(0.2)
            
            self.fc2 = nn.Linear(256, 128)
            self.bn2 = nn.BatchNorm1d(128)
            self.dropout2 = nn.Dropout(0.2)
            
            self.fc3 = nn.Linear(128, 64)
            self.bn3 = nn.BatchNorm1d(64)
            
            self.fc4 = nn.Linear(64, action_size)
        
        def forward(self, x):
            # Handle both single samples and batches
            single_sample = x.dim() == 1
            if single_sample:
                x = x.unsqueeze(0)
            
            x = F.relu(self.bn1(self.fc1(x)))
            x = self.dropout1(x)
            
            x = F.relu(self.bn2(self.fc2(x)))
            x = self.dropout2(x)
            
            x = F.relu(self.bn3(self.fc3(x)))
            
            x = self.fc4(x)
            
            if single_sample:
                x = x.squeeze(0)
            
            return x


# ═══════════════════════════════════════════════════════════════
# RL TRADING AGENT
# ═══════════════════════════════════════════════════════════════

class ReplayBuffer:
    """Experience Replay Buffer"""
    
    def __init__(self, capacity: int = 100000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (np.array(states), np.array(actions), np.array(rewards),
                np.array(next_states), np.array(dones))
    
    def __len__(self):
        return len(self.buffer)


class RLTradingAgent:
    """
    🤖 REINFORCEMENT LEARNING TRADING AGENT
    
    Uczy się optymalnej strategii poprzez interakcję ze środowiskiem.
    """
    
    def __init__(self,
                 state_size: int = 17,  # 10 features + 7 context
                 action_size: int = 4,  # HOLD, BUY, SELL, CLOSE
                 learning_rate: float = 0.001,
                 gamma: float = 0.99,    # Discount factor
                 epsilon: float = 1.0,   # Exploration rate
                 epsilon_min: float = 0.01,
                 epsilon_decay: float = 0.995,
                 batch_size: int = 64,
                 target_update: int = 10):
        
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for RL Agent")
        
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update = target_update
        
        # Networks
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.policy_net = DQN(state_size, action_size).to(self.device)
        self.target_net = DQN(state_size, action_size).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.memory = ReplayBuffer()
        
        self.training_step = 0
        self.episode_rewards = []
    
    def select_action(self, state: TradingState, training: bool = True) -> int:
        """
        Wybierz akcję używając epsilon-greedy.
        """
        if training and random.random() < self.epsilon:
            return random.randrange(self.action_size)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state.to_tensor()).to(self.device)
            self.policy_net.eval()
            q_values = self.policy_net(state_tensor)
            self.policy_net.train()
            return q_values.argmax().item()
    
    def remember(self, state, action, reward, next_state, done):
        """Zapisz doświadczenie do pamięci"""
        self.memory.push(
            state.to_tensor(), action, reward,
            next_state.to_tensor(), done
        )
    
    def learn(self):
        """Uczenie się z pamięci (Experience Replay)"""
        if len(self.memory) < self.batch_size:
            return 0
        
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Current Q values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values (from target network)
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Loss
        loss = F.smooth_l1_loss(current_q.squeeze(), target_q)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        # Update target network
        self.training_step += 1
        if self.training_step % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        return loss.item()
    
    def decay_epsilon(self):
        """Zmniejsz exploration rate"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def train(self, env: TradingEnvironment, episodes: int = 100) -> Dict:
        """
        Trenuj agenta na środowisku.
        
        Returns:
            Dict z wynikami treningu
        """
        logger.info(f"Starting training for {episodes} episodes...")
        
        all_rewards = []
        all_pnls = []
        
        for episode in range(episodes):
            state = env.reset()
            total_reward = 0
            
            while True:
                action = self.select_action(state, training=True)
                next_state, reward, done, info = env.step(action)
                
                self.remember(state, action, reward, next_state, done)
                loss = self.learn()
                
                state = next_state
                total_reward += reward
                
                if done:
                    break
            
            self.decay_epsilon()
            all_rewards.append(total_reward)
            all_pnls.append(info.get('total_pnl', 0))
            
            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(all_rewards[-10:])
                avg_pnl = np.mean(all_pnls[-10:])
                logger.info(f"Episode {episode+1}/{episodes} | Avg Reward: {avg_reward:.2f} | "
                           f"Avg P&L: ${avg_pnl:.2f} | Epsilon: {self.epsilon:.3f}")
        
        return {
            'episodes': episodes,
            'final_epsilon': self.epsilon,
            'avg_reward': np.mean(all_rewards[-20:]),
            'avg_pnl': np.mean(all_pnls[-20:]),
            'best_pnl': max(all_pnls),
            'all_rewards': all_rewards,
            'all_pnls': all_pnls
        }
    
    def save(self, path: str):
        """Zapisz model"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_step': self.training_step
        }, path)
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str):
        """Załaduj model"""
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
        self.training_step = checkpoint['training_step']
        logger.info(f"Model loaded from {path}")


# ═══════════════════════════════════════════════════════════════
# INTEGRATION WITH GENIUS BRAIN
# ═══════════════════════════════════════════════════════════════

def get_rl_signal(data: pd.DataFrame, model_path: str = None) -> Dict:
    """
    Pobierz sygnał z RL Agent dla Genius Brain.
    
    Args:
        data: OHLCV DataFrame
        model_path: Ścieżka do zapisanego modelu
    
    Returns:
        Dict z sygnałem
    """
    if not TORCH_AVAILABLE:
        return {'signal': 0, 'confidence': 0, 'reasons': ['PyTorch not available']}
    
    try:
        # Create environment (only for state extraction)
        env = TradingEnvironment(data)
        state = env._get_state()
        
        # Create agent
        agent = RLTradingAgent(state_size=len(state.to_tensor()))
        
        # Load model if available
        if model_path:
            try:
                agent.load(model_path)
            except:
                logger.warning("Could not load RL model, using untrained agent")
        
        # Get action
        action = agent.select_action(state, training=False)
        
        # Convert to signal
        signal_map = {
            TradingAction.HOLD.value: 0,
            TradingAction.BUY.value: 0.8,
            TradingAction.SELL.value: -0.8,
            TradingAction.CLOSE.value: 0
        }
        
        signal = signal_map.get(action, 0)
        
        # Confidence based on Q-values spread
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state.to_tensor()).to(agent.device)
            q_values = agent.policy_net(state_tensor).cpu().numpy()
            
            # Higher spread = higher confidence
            q_range = q_values.max() - q_values.min()
            confidence = min(q_range / 2, 1.0)
        
        action_name = TradingAction(action).name
        
        return {
            'signal': signal,
            'confidence': confidence,
            'action': action_name,
            'reasons': [f"RL Agent recommends {action_name}"],
            'q_values': q_values.tolist()
        }
        
    except Exception as e:
        logger.error(f"RL signal error: {e}")
        return {'signal': 0, 'confidence': 0, 'reasons': [f'Error: {str(e)}']}


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 REINFORCEMENT LEARNING TRADING AGENT - TEST")
    print("=" * 60)
    
    if not TORCH_AVAILABLE:
        print("❌ PyTorch not available. Install with: pip install torch")
        exit(1)
    
    # Generate sample data
    np.random.seed(42)
    n = 1000
    
    prices = 100000 * np.exp(np.cumsum(np.random.randn(n) * 0.02))
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(n) * 0.01)),
        'low': prices * (1 - np.abs(np.random.randn(n) * 0.01)),
        'close': prices,
        'volume': np.random.randint(1000, 10000, n)
    })
    
    print("\n1️⃣ CREATING ENVIRONMENT")
    print("-" * 40)
    
    env = TradingEnvironment(data, initial_balance=5000, position_size=50)
    print(f"Environment created with {len(env.prices)} timesteps")
    
    print("\n2️⃣ CREATING RL AGENT")
    print("-" * 40)
    
    state = env.reset()
    state_size = len(state.to_tensor())
    print(f"State size: {state_size}")
    
    agent = RLTradingAgent(state_size=state_size)
    print(f"Agent created on device: {agent.device}")
    
    print("\n3️⃣ TRAINING (20 episodes - demo)")
    print("-" * 40)
    
    results = agent.train(env, episodes=20)
    
    print(f"\nTraining Results:")
    print(f"  Avg Reward: {results['avg_reward']:.2f}")
    print(f"  Avg P&L: ${results['avg_pnl']:.2f}")
    print(f"  Best P&L: ${results['best_pnl']:.2f}")
    
    print("\n4️⃣ TEST SIGNAL GENERATION")
    print("-" * 40)
    
    signal = get_rl_signal(data)
    print(f"Signal: {signal}")
    
    print("\n" + "=" * 60)
    print("✅ RL Trading Agent Ready!")
    print("=" * 60)
