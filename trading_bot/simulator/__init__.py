"""
Simulator package for 7-day bot simulation with live dashboard and charts
"""

from .bot_simulator_7days import BotSimulator7Days
from .live_dashboard import LiveDashboard
from .plotting_engine import AdvancedPlotter

__all__ = ['BotSimulator7Days', 'LiveDashboard', 'AdvancedPlotter']
