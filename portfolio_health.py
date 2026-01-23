"""
Portfolio Health Check System
Analyze portfolio risk, correlation, and provide recommendations
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class PortfolioHealthCheck:
    """Comprehensive portfolio analysis and health scoring"""
    
    def __init__(self):
        self.risk_levels = {
            'conservative': {'max_volatility': 0.15, 'max_drawdown': 0.10},
            'moderate': {'max_volatility': 0.25, 'max_drawdown': 0.20},
            'aggressive': {'max_volatility': 0.40, 'max_drawdown': 0.35}
        }
    
    def analyze_portfolio(self, positions: List[Dict], prices: Dict[str, float]) -> Dict:
        """
        Comprehensive portfolio analysis
        
        Args:
            positions: List of {symbol, quantity, entry_price, current_price}
            prices: Current market prices {symbol: price}
            
        Returns:
            Complete portfolio health report
        """
        
        if not positions:
            return {'error': 'No positions provided'}
        
        # Calculate portfolio metrics
        total_value = 0
        total_cost = 0
        position_values = {}
        
        for pos in positions:
            symbol = pos['symbol']
            quantity = pos['quantity']
            entry_price = pos.get('entry_price', 0)
            current_price = prices.get(symbol, pos.get('current_price', 0))
            
            position_value = quantity * current_price
            position_cost = quantity * entry_price
            
            total_value += position_value
            total_cost += position_cost
            position_values[symbol] = {
                'value': position_value,
                'cost': position_cost,
                'pnl': position_value - position_cost,
                'pnl_pct': ((position_value / position_cost) - 1) * 100 if position_cost > 0 else 0
            }
        
        total_pnl = total_value - total_cost
        total_pnl_pct = ((total_value / total_cost) - 1) * 100 if total_cost > 0 else 0
        
        # Calculate position weights
        weights = {}
        for symbol, data in position_values.items():
            weights[symbol] = (data['value'] / total_value) * 100 if total_value > 0 else 0
        
        # Analyze diversification
        diversification = self._analyze_diversification(weights)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(positions, weights)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            weights, position_values, risk_score
        )
        
        # Health score (0-100)
        health_score = self._calculate_health_score(
            diversification['score'],
            risk_score,
            total_pnl_pct
        )
        
        return {
            'summary': {
                'total_value': round(total_value, 2),
                'total_cost': round(total_cost, 2),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_pct': round(total_pnl_pct, 2),
                'health_score': health_score,
                'risk_level': self._get_risk_level(risk_score)
            },
            'positions': position_values,
            'weights': weights,
            'diversification': diversification,
            'risk_analysis': {
                'risk_score': risk_score,
                'largest_position': max(weights.items(), key=lambda x: x[1]) if weights else ('N/A', 0),
                'concentration_risk': max(weights.values()) if weights else 0
            },
            'recommendations': recommendations,
            'genius_commentary': self._generate_genius_commentary(health_score, risk_score, total_pnl_pct),
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_diversification(self, weights: Dict[str, float]) -> Dict:
        """Analyze portfolio diversification"""
        if not weights:
            return {'score': 0, 'status': 'No positions'}
        
        num_positions = len(weights)
        max_weight = max(weights.values())
        
        # Calculate Herfindahl index (concentration measure)
        herfindahl = sum((w/100)**2 for w in weights.values())
        
        # Diversification score (0-100, higher is better)
        if num_positions == 1:
            div_score = 20
            status = 'Highly concentrated'
        elif num_positions == 2:
            div_score = 40
            status = 'Low diversification'
        elif num_positions <= 5:
            div_score = 60
            status = 'Moderate diversification'
        elif num_positions <= 10:
            div_score = 80
            status = 'Good diversification'
        else:
            div_score = 95
            status = 'Excellent diversification'
        
        # Penalize if any position > 40%
        if max_weight > 40:
            div_score -= 20
            status = 'Over-concentrated'
        
        return {
            'score': max(0, div_score),
            'status': status,
            'num_positions': num_positions,
            'max_position_weight': round(max_weight, 2),
            'herfindahl_index': round(herfindahl, 4)
        }
    
    def _calculate_risk_score(self, positions: List[Dict], weights: Dict) -> int:
        """Calculate portfolio risk score (0-100, higher = more risk)"""
        
        # Base risk on concentration
        max_weight = max(weights.values()) if weights else 0
        concentration_risk = min(max_weight, 100)
        
        # Number of positions (more = less risk)
        num_positions = len(positions)
        position_risk = max(0, 100 - (num_positions * 10))
        
        # Average weight (if too high = concentrated)
        avg_weight = sum(weights.values()) / len(weights) if weights else 0
        avg_weight_risk = min(avg_weight * 2, 100)
        
        # Combine factors
        risk_score = (concentration_risk * 0.5 + position_risk * 0.3 + avg_weight_risk * 0.2)
        
        return int(min(risk_score, 100))
    
    def _get_risk_level(self, risk_score: int) -> str:
        """Get risk level from score"""
        if risk_score < 30:
            return 'Low'
        elif risk_score < 60:
            return 'Moderate'
        else:
            return 'High'
    
    def _calculate_health_score(self, div_score: int, risk_score: int, pnl_pct: float) -> int:
        """Calculate overall portfolio health score"""
        
        # Diversification contributes 40%
        div_component = div_score * 0.4
        
        # Risk (inverse) contributes 30%
        risk_component = (100 - risk_score) * 0.3
        
        # Performance contributes 30%
        if pnl_pct > 20:
            perf_component = 100 * 0.3
        elif pnl_pct > 10:
            perf_component = 80 * 0.3
        elif pnl_pct > 0:
            perf_component = 60 * 0.3
        elif pnl_pct > -10:
            perf_component = 40 * 0.3
        else:
            perf_component = 20 * 0.3
        
        health = div_component + risk_component + perf_component
        
        return int(min(health, 100))
    
    def _generate_recommendations(
        self,
        weights: Dict,
        position_values: Dict,
        risk_score: int
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check concentration
        max_weight = max(weights.values()) if weights else 0
        if max_weight > 40:
            max_symbol = max(weights.items(), key=lambda x: x[1])[0]
            recommendations.append(
                f"⚠️ Reduce {max_symbol} position (currently {max_weight:.1f}% of portfolio)"
            )
        
        # Check number of positions
        if len(weights) < 3:
            recommendations.append(
                "📊 Consider adding more positions for better diversification (target 5-10)"
            )
        
        # Check risk level
        if risk_score > 70:
            recommendations.append(
                "🛑 High risk detected. Consider rebalancing to reduce concentration"
            )
        elif risk_score < 30:
            recommendations.append(
                "✅ Low risk profile. Portfolio is well-balanced"
            )
        
        # Check losing positions
        losers = [s for s, v in position_values.items() if v['pnl'] < 0]
        if len(losers) > len(position_values) * 0.5:
            recommendations.append(
                "📉 More than half positions in red. Review stop losses"
            )
        
        # Check if any position is very profitable
        big_winners = [s for s, v in position_values.items() if v['pnl_pct'] > 100]
        if big_winners:
            recommendations.append(
                f"💰 Consider taking profits on {', '.join(big_winners)} (up >100%)"
            )
        
        if not recommendations:
            recommendations.append("✅ Portfolio looks healthy. Keep monitoring regularly.")
        
        return recommendations
    
    def _generate_genius_commentary(
        self,
        health_score: int,
        risk_score: int,
        pnl_pct: float
    ) -> str:
        """Generate Genius AI commentary on portfolio"""
        
        commentary = []
        
        # Health assessment
        if health_score > 80:
            commentary.append("🎯 Excellent portfolio health! ")
        elif health_score > 60:
            commentary.append("👍 Solid portfolio structure. ")
        elif health_score > 40:
            commentary.append("⚠️ Portfolio needs attention. ")
        else:
            commentary.append("🚨 Portfolio requires immediate action. ")
        
        # Risk assessment
        if risk_score > 70:
            commentary.append("High concentration risk detected. ")
            commentary.append("Diversify to reduce downside exposure. ")
        elif risk_score < 30:
            commentary.append("Well-balanced risk profile. ")
        
        # Performance
        if pnl_pct > 20:
            commentary.append("Outstanding returns! ")
            commentary.append("Consider taking some profits and securing gains. ")
        elif pnl_pct > 0:
            commentary.append("Positive performance. ")
            commentary.append("Maintain discipline and stick to your strategy. ")
        else:
            commentary.append("Portfolio in drawdown. ")
            commentary.append("Review positions and cut losers if thesis has changed. ")
        
        commentary.append("\n💡 Remember: Diversification reduces risk without sacrificing long-term returns.")
        
        return "".join(commentary)
    
    def suggest_rebalancing(self, positions: List[Dict], target_allocation: Dict[str, float]) -> List[Dict]:
        """Suggest rebalancing trades to reach target allocation"""
        # Implementation for future
        return []


# Singleton instance
_portfolio_health = None

def get_portfolio_health() -> PortfolioHealthCheck:
    """Get or create Portfolio Health Check instance"""
    global _portfolio_health
    if _portfolio_health is None:
        _portfolio_health = PortfolioHealthCheck()
    return _portfolio_health
