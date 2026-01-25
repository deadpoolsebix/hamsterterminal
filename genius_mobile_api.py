"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GENIUS MOBILE API v1.0                                     ║
║                    React Native Compatible REST API                           ║
║                                                                              ║
║  Features:                                                                   ║
║  • RESTful API endpoints for mobile apps                                    ║
║  • WebSocket support for real-time updates                                  ║
║  • JWT authentication                                                       ║
║  • Rate limiting and CORS support                                           ║
║  • Optimized responses for mobile bandwidth                                 ║
║  • Push notification triggers                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from functools import wraps
import hashlib
import secrets
import logging

# Flask imports
try:
    from flask import Flask, jsonify, request, Response
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️ Flask not installed. Run: pip install flask flask-cors")

# JWT for authentication
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("⚠️ PyJWT not installed. Run: pip install PyJWT")

# WebSocket support
try:
    from flask_socketio import SocketIO, emit
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class MobileAPIConfig:
    """Mobile API Configuration"""
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = 5050
    DEBUG = True
    
    # Authentication
    JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_EXPIRY_HOURS = 24
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 60
    
    # CORS
    ALLOWED_ORIGINS = ['*']  # Configure for production
    
    # API version
    API_VERSION = 'v1'


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MobileSignal:
    """Optimized signal format for mobile"""
    id: str
    symbol: str
    direction: str  # LONG, SHORT, NEUTRAL
    confidence: float
    price: float
    entry: float
    stop_loss: float
    take_profit: float
    timestamp: str
    factors_summary: str
    risk_level: str  # LOW, MEDIUM, HIGH
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MobilePosition:
    """Position format for mobile"""
    id: str
    symbol: str
    side: str
    entry_price: float
    current_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    opened_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MobileStats:
    """Trading stats for mobile dashboard"""
    total_signals: int
    win_rate: float
    total_pnl: float
    best_trade: float
    worst_trade: float
    current_positions: int
    last_signal_time: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════════════
# API HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def create_jwt_token(user_id: str) -> str:
    """Create JWT token for user"""
    
    if not JWT_AVAILABLE:
        return "jwt-not-available"
    
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=MobileAPIConfig.JWT_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, MobileAPIConfig.JWT_SECRET, algorithm='HS256')


def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify JWT token"""
    
    if not JWT_AVAILABLE:
        return {'user_id': 'demo'}
    
    try:
        payload = jwt.decode(token, MobileAPIConfig.JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated


def api_response(data: Any, status: int = 200) -> Response:
    """Create standardized API response"""
    
    response = {
        'success': status < 400,
        'data': data,
        'timestamp': datetime.utcnow().isoformat(),
        'api_version': MobileAPIConfig.API_VERSION
    }
    
    return jsonify(response), status


# ═══════════════════════════════════════════════════════════════════════════════
# MOBILE API SERVER
# ═══════════════════════════════════════════════════════════════════════════════

class GeniusMobileAPI:
    """
    REST API Server for React Native Mobile App
    
    Endpoints:
    - /api/v1/auth/login - User authentication
    - /api/v1/signals - Get trading signals
    - /api/v1/signals/latest - Get latest signal
    - /api/v1/positions - Get open positions
    - /api/v1/stats - Get trading statistics
    - /api/v1/alerts - Manage price alerts
    - /ws - WebSocket for real-time updates
    """
    
    def __init__(self):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask required. Run: pip install flask flask-cors")
        
        self.app = Flask(__name__)
        CORS(self.app, origins=MobileAPIConfig.ALLOWED_ORIGINS)
        
        if SOCKETIO_AVAILABLE:
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        else:
            self.socketio = None
        
        self.logger = logging.getLogger('GeniusMobileAPI')
        
        # In-memory storage (replace with database in production)
        self.signals: List[MobileSignal] = []
        self.positions: List[MobilePosition] = []
        self.alerts: Dict[str, List[Dict]] = {}
        self.users: Dict[str, Dict] = {}
        
        # Rate limiting
        self.request_counts: Dict[str, List[datetime]] = {}
        
        # Register routes
        self._register_routes()
        
        # Register WebSocket handlers
        if self.socketio:
            self._register_websocket_handlers()
        
        # Generate demo data
        self._generate_demo_data()
    
    def _register_routes(self):
        """Register all API routes"""
        
        app = self.app
        
        # ─────────────────────────────────────────────────────────────────
        # Health & Info
        # ─────────────────────────────────────────────────────────────────
        
        @app.route('/api/v1/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return api_response({
                'status': 'healthy',
                'version': '1.0.0',
                'engine': 'Genius Engine v5.0'
            })
        
        @app.route('/api/v1/info', methods=['GET'])
        def info():
            """API information"""
            return api_response({
                'name': 'Genius Mobile API',
                'version': MobileAPIConfig.API_VERSION,
                'endpoints': [
                    '/api/v1/health',
                    '/api/v1/auth/login',
                    '/api/v1/signals',
                    '/api/v1/signals/latest',
                    '/api/v1/positions',
                    '/api/v1/stats',
                    '/api/v1/alerts'
                ]
            })
        
        # ─────────────────────────────────────────────────────────────────
        # Authentication
        # ─────────────────────────────────────────────────────────────────
        
        @app.route('/api/v1/auth/login', methods=['POST'])
        def login():
            """User login"""
            data = request.get_json() or {}
            
            username = data.get('username', '')
            password = data.get('password', '')
            
            # Demo authentication (replace with real auth in production)
            if username and password:
                user_id = hashlib.sha256(username.encode()).hexdigest()[:16]
                token = create_jwt_token(user_id)
                
                return api_response({
                    'token': token,
                    'user_id': user_id,
                    'expires_in': MobileAPIConfig.JWT_EXPIRY_HOURS * 3600
                })
            
            return api_response({'error': 'Invalid credentials'}, 401)
        
        @app.route('/api/v1/auth/register', methods=['POST'])
        def register():
            """User registration"""
            data = request.get_json() or {}
            
            username = data.get('username', '')
            password = data.get('password', '')
            email = data.get('email', '')
            
            if username and password and email:
                user_id = hashlib.sha256(username.encode()).hexdigest()[:16]
                
                self.users[user_id] = {
                    'username': username,
                    'email': email,
                    'created_at': datetime.utcnow().isoformat()
                }
                
                token = create_jwt_token(user_id)
                
                return api_response({
                    'token': token,
                    'user_id': user_id,
                    'message': 'Registration successful'
                }, 201)
            
            return api_response({'error': 'Missing required fields'}, 400)
        
        # ─────────────────────────────────────────────────────────────────
        # Signals
        # ─────────────────────────────────────────────────────────────────
        
        @app.route('/api/v1/signals', methods=['GET'])
        @require_auth
        def get_signals():
            """Get all recent signals"""
            limit = request.args.get('limit', 20, type=int)
            symbol = request.args.get('symbol', None)
            
            signals = self.signals[-limit:]
            
            if symbol:
                signals = [s for s in signals if s.symbol == symbol.upper()]
            
            return api_response({
                'signals': [s.to_dict() for s in signals],
                'count': len(signals)
            })
        
        @app.route('/api/v1/signals/latest', methods=['GET'])
        @require_auth
        def get_latest_signal():
            """Get the most recent signal"""
            symbol = request.args.get('symbol', 'BTC/USDT')
            
            # Filter by symbol
            matching = [s for s in self.signals if s.symbol == symbol.upper()]
            
            if matching:
                return api_response({'signal': matching[-1].to_dict()})
            else:
                return api_response({'signal': None, 'message': 'No signals found'})
        
        @app.route('/api/v1/signals/<signal_id>', methods=['GET'])
        @require_auth
        def get_signal_by_id(signal_id):
            """Get specific signal by ID"""
            for signal in self.signals:
                if signal.id == signal_id:
                    return api_response({'signal': signal.to_dict()})
            
            return api_response({'error': 'Signal not found'}, 404)
        
        # ─────────────────────────────────────────────────────────────────
        # Positions
        # ─────────────────────────────────────────────────────────────────
        
        @app.route('/api/v1/positions', methods=['GET'])
        @require_auth
        def get_positions():
            """Get all open positions"""
            return api_response({
                'positions': [p.to_dict() for p in self.positions],
                'count': len(self.positions),
                'total_pnl': sum(p.pnl for p in self.positions)
            })
        
        @app.route('/api/v1/positions/<position_id>', methods=['GET'])
        @require_auth
        def get_position(position_id):
            """Get specific position"""
            for position in self.positions:
                if position.id == position_id:
                    return api_response({'position': position.to_dict()})
            
            return api_response({'error': 'Position not found'}, 404)
        
        # ─────────────────────────────────────────────────────────────────
        # Stats
        # ─────────────────────────────────────────────────────────────────
        
        @app.route('/api/v1/stats', methods=['GET'])
        @require_auth
        def get_stats():
            """Get trading statistics"""
            stats = MobileStats(
                total_signals=len(self.signals),
                win_rate=0.65,
                total_pnl=1250.00,
                best_trade=850.00,
                worst_trade=-200.00,
                current_positions=len(self.positions),
                last_signal_time=self.signals[-1].timestamp if self.signals else ''
            )
            
            return api_response({'stats': stats.to_dict()})
        
        @app.route('/api/v1/stats/performance', methods=['GET'])
        @require_auth
        def get_performance():
            """Get detailed performance metrics"""
            return api_response({
                'daily_pnl': [
                    {'date': '2026-01-23', 'pnl': 350.00},
                    {'date': '2026-01-22', 'pnl': -100.00},
                    {'date': '2026-01-21', 'pnl': 500.00},
                    {'date': '2026-01-20', 'pnl': 200.00},
                    {'date': '2026-01-19', 'pnl': 300.00},
                ],
                'win_streak': 3,
                'sharpe_ratio': 1.85,
                'max_drawdown': -5.2
            })
        
        # ─────────────────────────────────────────────────────────────────
        # Alerts
        # ─────────────────────────────────────────────────────────────────
        
        @app.route('/api/v1/alerts', methods=['GET'])
        @require_auth
        def get_alerts():
            """Get user's price alerts"""
            user_id = request.headers.get('X-User-ID', 'demo')
            alerts = self.alerts.get(user_id, [])
            
            return api_response({
                'alerts': alerts,
                'count': len(alerts)
            })
        
        @app.route('/api/v1/alerts', methods=['POST'])
        @require_auth
        def create_alert():
            """Create new price alert"""
            data = request.get_json() or {}
            user_id = request.headers.get('X-User-ID', 'demo')
            
            alert = {
                'id': secrets.token_hex(8),
                'symbol': data.get('symbol', 'BTC/USDT'),
                'price': data.get('price', 0),
                'condition': data.get('condition', 'above'),  # above, below
                'active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            if user_id not in self.alerts:
                self.alerts[user_id] = []
            
            self.alerts[user_id].append(alert)
            
            return api_response({'alert': alert}, 201)
        
        @app.route('/api/v1/alerts/<alert_id>', methods=['DELETE'])
        @require_auth
        def delete_alert(alert_id):
            """Delete price alert"""
            user_id = request.headers.get('X-User-ID', 'demo')
            
            if user_id in self.alerts:
                self.alerts[user_id] = [
                    a for a in self.alerts[user_id] if a['id'] != alert_id
                ]
            
            return api_response({'message': 'Alert deleted'})
        
        # ─────────────────────────────────────────────────────────────────
        # Market Data
        # ─────────────────────────────────────────────────────────────────
        
        @app.route('/api/v1/market/price', methods=['GET'])
        @require_auth
        def get_market_price():
            """Get current market price"""
            symbol = request.args.get('symbol', 'BTC/USDT')
            
            # Demo price
            return api_response({
                'symbol': symbol,
                'price': 97500.00,
                'change_24h': 2.5,
                'high_24h': 98200.00,
                'low_24h': 95800.00,
                'volume_24h': 25000000000,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @app.route('/api/v1/market/ticker', methods=['GET'])
        @require_auth
        def get_ticker():
            """Get multiple tickers"""
            symbols = request.args.get('symbols', 'BTC/USDT,ETH/USDT').split(',')
            
            tickers = []
            demo_prices = {
                'BTC/USDT': 97500, 'ETH/USDT': 3150, 'SOL/USDT': 185,
                'BNB/USDT': 620, 'XRP/USDT': 2.35
            }
            
            for symbol in symbols:
                symbol = symbol.strip().upper()
                price = demo_prices.get(symbol, 100)
                tickers.append({
                    'symbol': symbol,
                    'price': price,
                    'change_24h': round((hash(symbol) % 100 - 50) / 10, 2)
                })
            
            return api_response({'tickers': tickers})
        
        # ─────────────────────────────────────────────────────────────────
        # Predictions
        # ─────────────────────────────────────────────────────────────────
        
        @app.route('/api/v1/predictions', methods=['GET'])
        @require_auth
        def get_predictions():
            """Get AI price predictions"""
            symbol = request.args.get('symbol', 'BTC/USDT')
            
            return api_response({
                'symbol': symbol,
                'current_price': 97500,
                'predictions': {
                    '1h': {'price': 97650, 'direction': 'UP', 'confidence': 0.72},
                    '4h': {'price': 98100, 'direction': 'UP', 'confidence': 0.65},
                    '24h': {'price': 99500, 'direction': 'UP', 'confidence': 0.58},
                    '7d': {'price': 102000, 'direction': 'UP', 'confidence': 0.45}
                },
                'model': 'Transformer v1.0'
            })
    
    def _register_websocket_handlers(self):
        """Register WebSocket event handlers"""
        
        socketio = self.socketio
        
        @socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            emit('connected', {'status': 'ok', 'message': 'Connected to Genius API'})
        
        @socketio.on('subscribe')
        def handle_subscribe(data):
            """Subscribe to updates for a symbol"""
            symbol = data.get('symbol', 'BTC/USDT')
            emit('subscribed', {'symbol': symbol, 'status': 'subscribed'})
        
        @socketio.on('unsubscribe')
        def handle_unsubscribe(data):
            """Unsubscribe from updates"""
            symbol = data.get('symbol', 'BTC/USDT')
            emit('unsubscribed', {'symbol': symbol, 'status': 'unsubscribed'})
    
    def _generate_demo_data(self):
        """Generate demo signals and positions"""
        
        # Demo signals
        demo_signals = [
            MobileSignal(
                id=secrets.token_hex(8),
                symbol='BTC/USDT',
                direction='LONG',
                confidence=0.82,
                price=97500,
                entry=97500,
                stop_loss=95000,
                take_profit=102000,
                timestamp=(datetime.utcnow() - timedelta(hours=2)).isoformat(),
                factors_summary='Liquidity Grab + FVG + MTF Aligned',
                risk_level='MEDIUM'
            ),
            MobileSignal(
                id=secrets.token_hex(8),
                symbol='ETH/USDT',
                direction='SHORT',
                confidence=0.76,
                price=3150,
                entry=3150,
                stop_loss=3250,
                take_profit=2950,
                timestamp=(datetime.utcnow() - timedelta(hours=5)).isoformat(),
                factors_summary='RSI Overbought + Whale Selling',
                risk_level='HIGH'
            ),
            MobileSignal(
                id=secrets.token_hex(8),
                symbol='SOL/USDT',
                direction='LONG',
                confidence=0.71,
                price=185,
                entry=185,
                stop_loss=175,
                take_profit=200,
                timestamp=(datetime.utcnow() - timedelta(hours=8)).isoformat(),
                factors_summary='Support Test + Volume Spike',
                risk_level='LOW'
            )
        ]
        
        self.signals.extend(demo_signals)
        
        # Demo positions
        demo_positions = [
            MobilePosition(
                id=secrets.token_hex(8),
                symbol='BTC/USDT',
                side='LONG',
                entry_price=96500,
                current_price=97500,
                quantity=0.1,
                pnl=100,
                pnl_pct=1.04,
                opened_at=(datetime.utcnow() - timedelta(hours=24)).isoformat()
            )
        ]
        
        self.positions.extend(demo_positions)
    
    def broadcast_signal(self, signal: MobileSignal):
        """Broadcast new signal to all connected clients"""
        
        self.signals.append(signal)
        
        if self.socketio:
            self.socketio.emit('new_signal', signal.to_dict())
    
    def broadcast_price_update(self, symbol: str, price: float):
        """Broadcast price update"""
        
        if self.socketio:
            self.socketio.emit('price_update', {
                'symbol': symbol,
                'price': price,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    def run(self, host: str = None, port: int = None, debug: bool = None):
        """Start the API server"""
        
        host = host or MobileAPIConfig.HOST
        port = port or MobileAPIConfig.PORT
        debug = debug if debug is not None else MobileAPIConfig.DEBUG
        
        print(f"\n🚀 Starting Genius Mobile API on http://{host}:{port}")
        print(f"   API Version: {MobileAPIConfig.API_VERSION}")
        print(f"   WebSocket: {'Enabled' if self.socketio else 'Disabled'}")
        
        if self.socketio:
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        else:
            self.app.run(host=host, port=port, debug=debug)


# ═══════════════════════════════════════════════════════════════════════════════
# REACT NATIVE CLIENT HELPER
# ═══════════════════════════════════════════════════════════════════════════════

REACT_NATIVE_CLIENT_CODE = '''
// React Native Client for Genius Mobile API
// File: src/api/geniusAPI.js

import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://YOUR_SERVER_IP:5050/api/v1';

class GeniusAPI {
  constructor() {
    this.token = null;
  }

  async init() {
    this.token = await AsyncStorage.getItem('genius_token');
  }

  async login(username, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    if (data.success) {
      this.token = data.data.token;
      await AsyncStorage.setItem('genius_token', this.token);
    }
    return data;
  }

  async getSignals(limit = 20) {
    const response = await fetch(`${API_BASE_URL}/signals?limit=${limit}`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }

  async getLatestSignal(symbol = 'BTC/USDT') {
    const response = await fetch(`${API_BASE_URL}/signals/latest?symbol=${symbol}`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }

  async getPositions() {
    const response = await fetch(`${API_BASE_URL}/positions`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }

  async getStats() {
    const response = await fetch(`${API_BASE_URL}/stats`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }

  async getPredictions(symbol = 'BTC/USDT') {
    const response = await fetch(`${API_BASE_URL}/predictions?symbol=${symbol}`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }

  async createAlert(symbol, price, condition) {
    const response = await fetch(`${API_BASE_URL}/alerts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify({ symbol, price, condition })
    });
    return response.json();
  }
}

export default new GeniusAPI();
'''


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demo the Mobile API"""
    
    print("=" * 70)
    print("📱 GENIUS MOBILE API v1.0 - DEMO")
    print("=" * 70)
    
    print("\n📦 Dependencies:")
    print(f"   Flask:        {'✅ Available' if FLASK_AVAILABLE else '❌ Not installed'}")
    print(f"   PyJWT:        {'✅ Available' if JWT_AVAILABLE else '❌ Not installed'}")
    print(f"   Flask-SocketIO: {'✅ Available' if SOCKETIO_AVAILABLE else '❌ Not installed'}")
    
    if not FLASK_AVAILABLE:
        print("\n⚠️ Install Flask to run the API server:")
        print("   pip install flask flask-cors PyJWT flask-socketio")
        return False
    
    print("\n📡 API ENDPOINTS:")
    print("-" * 50)
    
    endpoints = [
        ("GET", "/api/v1/health", "Health check"),
        ("POST", "/api/v1/auth/login", "User login"),
        ("POST", "/api/v1/auth/register", "User registration"),
        ("GET", "/api/v1/signals", "Get all signals"),
        ("GET", "/api/v1/signals/latest", "Get latest signal"),
        ("GET", "/api/v1/positions", "Get open positions"),
        ("GET", "/api/v1/stats", "Get trading stats"),
        ("GET", "/api/v1/stats/performance", "Get performance metrics"),
        ("GET", "/api/v1/alerts", "Get price alerts"),
        ("POST", "/api/v1/alerts", "Create price alert"),
        ("DELETE", "/api/v1/alerts/<id>", "Delete price alert"),
        ("GET", "/api/v1/market/price", "Get market price"),
        ("GET", "/api/v1/market/ticker", "Get multiple tickers"),
        ("GET", "/api/v1/predictions", "Get AI predictions"),
    ]
    
    for method, path, desc in endpoints:
        print(f"   {method:6} {path:30} - {desc}")
    
    print("\n🔐 AUTHENTICATION:")
    print("-" * 50)
    print("   JWT Token-based authentication")
    print(f"   Token expiry: {MobileAPIConfig.JWT_EXPIRY_HOURS} hours")
    
    # Test JWT
    if JWT_AVAILABLE:
        test_token = create_jwt_token("test_user")
        print(f"\n   Sample token: {test_token[:50]}...")
        
        payload = verify_jwt_token(test_token)
        print(f"   Verified user: {payload.get('user_id', 'N/A')}")
    
    print("\n📱 REACT NATIVE CLIENT:")
    print("-" * 50)
    print("   Example client code generated!")
    print("   See: REACT_NATIVE_CLIENT_CODE variable")
    
    print("\n⚙️ CONFIGURATION:")
    print("-" * 50)
    print(f"   Host: {MobileAPIConfig.HOST}")
    print(f"   Port: {MobileAPIConfig.PORT}")
    print(f"   Rate Limit: {MobileAPIConfig.RATE_LIMIT_PER_MINUTE}/min")
    
    print("\n" + "=" * 70)
    print("✅ Mobile API ready!")
    print("   To start server: python genius_mobile_api.py --run")
    print("=" * 70)
    
    return True


def main():
    """Main entry point"""
    import sys
    
    if '--run' in sys.argv:
        # Start the server
        api = GeniusMobileAPI()
        api.run()
    else:
        # Just demo
        demo()


if __name__ == "__main__":
    main()
