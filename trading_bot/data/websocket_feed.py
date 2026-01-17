#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket Real-Time Data Feed
Dla scalpingu 5m i niskiej latencji
"""

import asyncio
import json
import websockets
import pandas as pd
from datetime import datetime
from typing import Callable, Dict
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketFeed:
    """
    WebSocket feed dla real-time data
    
    Obsługuje:
    - Binance WebSocket
    - Real-time price updates
    - Order book updates
    - Trade stream
    - Reconnection logic
    """
    
    def __init__(self, symbol: str = 'btcusdt'):
        self.symbol = symbol.lower()
        self.ws = None
        self.running = False
        self.price_buffer = deque(maxlen=1000)
        self.callbacks = []
        self.last_price = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def add_callback(self, callback: Callable):
        """Dodaj callback dla nowych danych"""
        self.callbacks.append(callback)
    
    async def connect(self):
        """Połącz z WebSocket"""
        # Binance WebSocket URL
        url = f"wss://stream.binance.com:9443/ws/{self.symbol}@trade"
        
        try:
            logger.info(f"Connecting to {url}...")
            self.ws = await websockets.connect(url)
            self.running = True
            self.reconnect_attempts = 0
            logger.info("✅ WebSocket connected!")
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            await self._handle_reconnect()
    
    async def _handle_reconnect(self):
        """Obsłuż reconnection"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            wait_time = min(2 ** self.reconnect_attempts, 30)
            logger.warning(f"Reconnecting in {wait_time}s... (Attempt {self.reconnect_attempts})")
            await asyncio.sleep(wait_time)
            await self.connect()
        else:
            logger.critical("❌ Max reconnection attempts reached. Manual intervention required.")
            self.running = False
    
    async def listen(self):
        """Nasłuchuj na wiadomości"""
        while self.running:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Parse trade data
                trade = {
                    'symbol': data.get('s'),
                    'price': float(data.get('p', 0)),
                    'quantity': float(data.get('q', 0)),
                    'timestamp': pd.Timestamp.fromtimestamp(data.get('T', 0) / 1000),
                    'is_buyer_maker': data.get('m', False)
                }
                
                self.last_price = trade['price']
                self.price_buffer.append(trade)
                
                # Execute callbacks
                for callback in self.callbacks:
                    try:
                        callback(trade)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("⚠️ WebSocket connection closed")
                await self._handle_reconnect()
                
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                await asyncio.sleep(1)
    
    async def subscribe_orderbook(self):
        """Subscribe do orderbook (depth)"""
        depth_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@depth20@100ms"
        
        try:
            self.depth_ws = await websockets.connect(depth_url)
            logger.info("✅ OrderBook WebSocket connected!")
            
            while self.running:
                message = await self.depth_ws.recv()
                data = json.loads(message)
                
                orderbook = {
                    'bids': [(float(b[0]), float(b[1])) for b in data.get('bids', [])],
                    'asks': [(float(a[0]), float(a[1])) for a in data.get('asks', [])],
                    'timestamp': pd.Timestamp.now()
                }
                
                # Analyze bid/ask walls
                self._analyze_orderbook(orderbook)
                
        except Exception as e:
            logger.error(f"OrderBook error: {e}")
    
    def _analyze_orderbook(self, orderbook: Dict):
        """
        Analiza orderbook - wykryj bid/ask walls
        """
        if not orderbook['bids'] or not orderbook['asks']:
            return
        
        # Total volume
        bid_volume = sum(q for p, q in orderbook['bids'])
        ask_volume = sum(q for p, q in orderbook['asks'])
        
        # Bid/Ask imbalance
        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        
        # Detect walls (> 10x average)
        avg_bid_size = bid_volume / len(orderbook['bids'])
        avg_ask_size = ask_volume / len(orderbook['asks'])
        
        bid_walls = [p for p, q in orderbook['bids'] if q > avg_bid_size * 10]
        ask_walls = [p for p, q in orderbook['asks'] if q > avg_ask_size * 10]
        
        if bid_walls:
            logger.info(f"💰 BID WALL detected @ ${bid_walls[0]:,.0f}")
        
        if ask_walls:
            logger.info(f"💰 ASK WALL detected @ ${ask_walls[0]:,.0f}")
        
        if abs(imbalance) > 0.3:
            if imbalance > 0:
                logger.info(f"📈 Bullish orderbook pressure ({imbalance*100:.1f}%)")
            else:
                logger.info(f"📉 Bearish orderbook pressure ({imbalance*100:.1f}%)")
    
    def get_recent_prices(self, count: int = 100) -> pd.DataFrame:
        """Pobierz ostatnie ceny"""
        if len(self.price_buffer) == 0:
            return pd.DataFrame()
        
        recent = list(self.price_buffer)[-count:]
        return pd.DataFrame(recent)
    
    def get_current_price(self) -> float:
        """Aktualna cena"""
        return self.last_price if self.last_price else 0
    
    async def stop(self):
        """Zatrzymaj WebSocket"""
        self.running = False
        if self.ws:
            await self.ws.close()
        logger.info("WebSocket stopped")


class LatencyMonitor:
    """
    Monitor latencji
    Dla leverage 100x każda milisekunda ma znaczenie
    """
    
    def __init__(self):
        self.latencies = deque(maxlen=1000)
        self.warnings = []
        
    def record_latency(self, latency_ms: float):
        """Zapisz latencję"""
        self.latencies.append(latency_ms)
        
        # Warning jeśli >100ms
        if latency_ms > 100:
            self.warnings.append({
                'timestamp': pd.Timestamp.now(),
                'latency': latency_ms
            })
            logger.warning(f"⚠️ High latency: {latency_ms:.0f}ms")
    
    def get_stats(self) -> Dict:
        """Statystyki latencji"""
        if not self.latencies:
            return {}
        
        return {
            'avg_latency': np.mean(self.latencies),
            'min_latency': np.min(self.latencies),
            'max_latency': np.max(self.latencies),
            'p95_latency': np.percentile(self.latencies, 95),
            'warnings_count': len(self.warnings)
        }
    
    def check_health(self) -> Dict:
        """Sprawdź health latencji"""
        stats = self.get_stats()
        
        if not stats:
            return {'status': 'unknown'}
        
        if stats['p95_latency'] < 50:
            status = 'excellent'
        elif stats['p95_latency'] < 100:
            status = 'good'
        elif stats['p95_latency'] < 200:
            status = 'warning'
        else:
            status = 'critical'
        
        return {
            'status': status,
            'stats': stats,
            'recommendation': self._get_recommendation(status)
        }
    
    def _get_recommendation(self, status: str) -> str:
        """Rekomendacje dla latencji"""
        if status == 'excellent':
            return "✅ Latencja optymalna. Scalping możliwy."
        elif status == 'good':
            return "⚡ Latencja dobra. Możesz handlować."
        elif status == 'warning':
            return "⚠️ Wysoka latencja. Unikaj scalpu 5m."
        else:
            return "🚨 KRYTYCZNA latencja! Tylko długoterminowe pozycje."


async def demo_websocket():
    """Demo WebSocket feed"""
    
    print("=" * 60)
    print("🌐 WEBSOCKET REAL-TIME FEED - DEMO")
    print("=" * 60)
    
    # Initialize feed
    feed = WebSocketFeed(symbol='btcusdt')
    
    # Callback dla nowych cen
    def on_new_price(trade):
        print(f"📊 {trade['symbol']}: ${trade['price']:,.2f} | "
              f"Vol: {trade['quantity']:.4f} | "
              f"Side: {'SELL' if trade['is_buyer_maker'] else 'BUY'}")
    
    feed.add_callback(on_new_price)
    
    # Connect
    await feed.connect()
    
    # Listen for 10 seconds
    try:
        await asyncio.wait_for(feed.listen(), timeout=10)
    except asyncio.TimeoutError:
        print("\n✅ Demo completed (10s)")
    
    # Stats
    recent = feed.get_recent_prices()
    if not recent.empty:
        print(f"\nReceived {len(recent)} trades")
        print(f"Price range: ${recent['price'].min():,.0f} - ${recent['price'].max():,.0f}")
    
    await feed.stop()
    print("=" * 60)


if __name__ == "__main__":
    # Note: Requires active internet connection
    try:
        import numpy as np  # dla LatencyMonitor
        asyncio.run(demo_websocket())
    except Exception as e:
        print(f"Demo requires internet connection: {e}")
        print("WebSocket module is ready for production use.")
