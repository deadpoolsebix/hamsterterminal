"""
Smart Alerts System
Intelligent market monitoring with Genius AI commentary
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time

logger = logging.getLogger(__name__)


class SmartAlert:
    """Individual alert configuration"""
    
    def __init__(
        self,
        alert_id: str,
        user_id: str,
        symbol: str,
        condition: str,
        value: float,
        alert_type: str = 'price',
        active: bool = True
    ):
        self.alert_id = alert_id
        self.user_id = user_id
        self.symbol = symbol
        self.condition = condition  # 'above', 'below', 'crosses_up', 'crosses_down'
        self.value = value
        self.alert_type = alert_type  # 'price', 'volume', 'change', 'pattern'
        self.active = active
        self.triggered = False
        self.created_at = datetime.now()
        self.triggered_at = None
        self.trigger_count = 0


class SmartAlertsSystem:
    """Monitor market conditions and trigger intelligent alerts"""
    
    def __init__(self):
        self.alerts: Dict[str, SmartAlert] = {}
        self.alert_history: List[Dict] = []
        self.monitoring = False
        self.monitor_thread = None
        
    def add_alert(
        self,
        user_id: str,
        symbol: str,
        condition: str,
        value: float,
        alert_type: str = 'price'
    ) -> str:
        """Add new alert"""
        alert_id = f"{user_id}_{symbol}_{int(time.time())}"
        
        alert = SmartAlert(
            alert_id=alert_id,
            user_id=user_id,
            symbol=symbol,
            condition=condition,
            value=value,
            alert_type=alert_type
        )
        
        self.alerts[alert_id] = alert
        logger.info(f"✅ Alert created: {symbol} {condition} {value}")
        
        return alert_id
    
    def remove_alert(self, alert_id: str) -> bool:
        """Remove alert by ID"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"🗑️ Alert removed: {alert_id}")
            return True
        return False
    
    def get_user_alerts(self, user_id: str) -> List[Dict]:
        """Get all alerts for user"""
        user_alerts = []
        for alert in self.alerts.values():
            if alert.user_id == user_id:
                user_alerts.append({
                    'alert_id': alert.alert_id,
                    'symbol': alert.symbol,
                    'condition': alert.condition,
                    'value': alert.value,
                    'type': alert.alert_type,
                    'active': alert.active,
                    'triggered': alert.triggered,
                    'created_at': alert.created_at.isoformat()
                })
        return user_alerts
    
    def check_alert(self, alert: SmartAlert, current_data: Dict) -> Optional[Dict]:
        """Check if alert condition is met"""
        if not alert.active or alert.triggered:
            return None
        
        symbol = alert.symbol
        current_price = current_data.get('price', 0)
        
        if current_price == 0:
            return None
        
        triggered = False
        message = ""
        
        # Price alerts
        if alert.alert_type == 'price':
            if alert.condition == 'above' and current_price > alert.value:
                triggered = True
                message = f"🚀 {symbol} crossed above ${alert.value:.2f} (now ${current_price:.2f})"
            
            elif alert.condition == 'below' and current_price < alert.value:
                triggered = True
                message = f"📉 {symbol} dropped below ${alert.value:.2f} (now ${current_price:.2f})"
        
        # Volume alerts
        elif alert.alert_type == 'volume':
            volume_24h = current_data.get('volume_24h', 0)
            if alert.condition == 'above' and volume_24h > alert.value:
                triggered = True
                message = f"📊 {symbol} volume spike: ${volume_24h/1e9:.2f}B (threshold ${alert.value/1e9:.2f}B)"
        
        # Change % alerts
        elif alert.alert_type == 'change':
            change_pct = current_data.get('change_24h', 0)
            if alert.condition == 'above' and change_pct > alert.value:
                triggered = True
                message = f"🔥 {symbol} pumping +{change_pct:.1f}% in 24h!"
            elif alert.condition == 'below' and change_pct < alert.value:
                triggered = True
                message = f"⚠️ {symbol} dumping {change_pct:.1f}% in 24h"
        
        if triggered:
            alert.triggered = True
            alert.triggered_at = datetime.now()
            alert.trigger_count += 1
            
            # Generate Genius AI commentary
            genius_comment = self._generate_genius_commentary(alert, current_data)
            
            trigger_data = {
                'alert_id': alert.alert_id,
                'user_id': alert.user_id,
                'symbol': alert.symbol,
                'message': message,
                'genius_comment': genius_comment,
                'current_price': current_price,
                'timestamp': datetime.now().isoformat(),
                'type': alert.alert_type
            }
            
            self.alert_history.append(trigger_data)
            logger.info(f"🔔 Alert triggered: {message}")
            
            return trigger_data
        
        return None
    
    def _generate_genius_commentary(self, alert: SmartAlert, data: Dict) -> str:
        """Generate AI commentary for triggered alert"""
        symbol = alert.symbol
        price = data.get('price', 0)
        change = data.get('change_24h', 0)
        
        comments = []
        
        if change > 5:
            comments.append(f"Strong bullish momentum on {symbol}. ")
            comments.append("Watch for resistance levels and consider taking partial profits. ")
        elif change > 2:
            comments.append(f"Moderate uptrend on {symbol}. ")
            comments.append("Good entry for swing positions if volume confirms. ")
        elif change < -5:
            comments.append(f"Heavy selling pressure on {symbol}. ")
            comments.append("Look for support levels before entering. ")
        elif change < -2:
            comments.append(f"Bearish action on {symbol}. ")
            comments.append("Wait for trend reversal signals. ")
        else:
            comments.append(f"Consolidation on {symbol}. ")
            comments.append("Wait for breakout direction. ")
        
        # Add risk warning
        comments.append("⚠️ Always use stop losses and manage position size.")
        
        return "".join(comments)
    
    def start_monitoring(self, market_data_callback):
        """Start monitoring alerts in background"""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor_loop():
            logger.info("🔍 Smart Alerts monitoring started")
            while self.monitoring:
                try:
                    # Get current market data
                    market_data = market_data_callback()
                    
                    # Check all active alerts
                    for alert in list(self.alerts.values()):
                        symbol_data = market_data.get(alert.symbol, {})
                        if symbol_data:
                            self.check_alert(alert, symbol_data)
                    
                    time.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    logger.error(f"Alert monitoring error: {e}")
                    time.sleep(30)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring alerts"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Smart Alerts monitoring stopped")
    
    def get_alert_history(self, user_id: str = None, limit: int = 50) -> List[Dict]:
        """Get alert history"""
        history = self.alert_history
        
        if user_id:
            history = [a for a in history if a['user_id'] == user_id]
        
        return history[-limit:]
    
    def suggest_alerts(self, symbol: str, current_price: float) -> List[Dict]:
        """Suggest intelligent alert levels based on current price"""
        suggestions = []
        
        # Key levels
        resistance_1 = current_price * 1.05  # +5%
        resistance_2 = current_price * 1.10  # +10%
        support_1 = current_price * 0.95     # -5%
        support_2 = current_price * 0.90     # -10%
        
        suggestions.append({
            'type': 'price',
            'condition': 'above',
            'value': resistance_1,
            'reason': 'Short-term resistance (+5%)',
            'priority': 'medium'
        })
        
        suggestions.append({
            'type': 'price',
            'condition': 'above',
            'value': resistance_2,
            'reason': 'Major breakout level (+10%)',
            'priority': 'high'
        })
        
        suggestions.append({
            'type': 'price',
            'condition': 'below',
            'value': support_1,
            'reason': 'Short-term support (-5%)',
            'priority': 'medium'
        })
        
        suggestions.append({
            'type': 'price',
            'condition': 'below',
            'value': support_2,
            'reason': 'Critical support level (-10%)',
            'priority': 'high'
        })
        
        return suggestions


# Singleton instance
_alerts_system = None

def get_alerts_system() -> SmartAlertsSystem:
    """Get or create Smart Alerts System instance"""
    global _alerts_system
    if _alerts_system is None:
        _alerts_system = SmartAlertsSystem()
    return _alerts_system
