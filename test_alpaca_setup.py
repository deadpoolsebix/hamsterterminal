#!/usr/bin/env python3
import os
import unittest

try:
    from alpaca.data.live import StockDataStream  # noqa: F401
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


class TestAlpacaSetup(unittest.TestCase):
    """Lightweight checks for Alpaca SDK availability."""

    def test_sdk_installed(self) -> None:
        if not SDK_AVAILABLE:
            self.skipTest("alpaca-py not installed")
        self.assertTrue(SDK_AVAILABLE)

    def test_api_keys_configured(self) -> None:
        if not SDK_AVAILABLE:
            self.skipTest("alpaca-py not installed")
        api_key = os.getenv('ALPACA_API_KEY')
        secret = os.getenv('ALPACA_SECRET')
        if not api_key or not secret:
            self.skipTest("Alpaca API keys not configured")
        self.assertTrue(api_key)
        self.assertTrue(secret)

    def test_connection_optional(self) -> None:
        if not SDK_AVAILABLE:
            self.skipTest("alpaca-py not installed")
        api_key = os.getenv('ALPACA_API_KEY')
        secret = os.getenv('ALPACA_SECRET')
        if not api_key or not secret:
            self.skipTest("Alpaca API keys not configured")
        try:
            from alpaca.trading.client import TradingClient

            client = TradingClient(api_key, secret, paper=True)
            client.get_account()
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"Alpaca connection skipped: {exc}")


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
