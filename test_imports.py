#!/usr/bin/env python
import unittest
from importlib import import_module


class TestSimulatorImports(unittest.TestCase):
    """Ensure critical simulator modules import without errors."""

    def test_bot_simulator_module(self) -> None:
        module = import_module('trading_bot.simulator.bot_simulator_7days')
        self.assertTrue(hasattr(module, 'BotSimulator7Days'))

    def test_live_dashboard_module(self) -> None:
        module = import_module('trading_bot.simulator.live_dashboard')
        self.assertTrue(hasattr(module, 'LiveDashboard'))

    def test_plotting_engine_module(self) -> None:
        try:
            module = import_module('trading_bot.simulator.plotting_engine')
        except ImportError as exc:
            self.skipTest(f"Plotting engine dependencies missing: {exc}")
        self.assertTrue(hasattr(module, 'AdvancedPlotter'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
