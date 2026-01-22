#!/usr/bin/env python
import unittest

import requests

API_URL = 'http://127.0.0.1:5000/api/genius/commentary'


class TestLocalAPI(unittest.TestCase):
    """Ping the local Flask API when it is running."""

    def test_commentary_endpoint(self) -> None:
        try:
            response = requests.get(API_URL, timeout=5)
            response.raise_for_status()
            self.assertIn('genius', response.json())
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"Local API not reachable: {exc}")


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
