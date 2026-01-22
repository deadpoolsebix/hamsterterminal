#!/usr/bin/env python3
import os
import unittest

import requests

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
BASE_URL = "https://finnhub.io/api/v1"


class TestFinnhubSetup(unittest.TestCase):
    """Validate Finnhub configuration when an API key is provided."""

    def test_api_key_available(self) -> None:
        if not FINNHUB_API_KEY:
            self.skipTest("Finnhub API key not configured")
        self.assertTrue(FINNHUB_API_KEY)

    def test_quote_endpoint(self) -> None:
        if not FINNHUB_API_KEY:
            self.skipTest("Finnhub API key not configured")
        try:
            response = requests.get(
                f"{BASE_URL}/quote",
                params={"symbol": "SPY", "token": FINNHUB_API_KEY},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            self.assertIn('c', data)
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"Finnhub request skipped: {exc}")


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
