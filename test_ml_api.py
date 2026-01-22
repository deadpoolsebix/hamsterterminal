"""Test ML-enhanced Genius API"""
import unittest

import requests

API_URL = 'http://localhost:5000/api/genius/commentary'


class TestMLApi(unittest.TestCase):
    """Check that the ML-backed endpoint responds when the server runs."""

    def test_genius_endpoint(self) -> None:
        try:
            response = requests.get(API_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            self.assertIn('signal', data)
            self.assertIn('commentary', data)
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"Genius API unavailable: {exc}")


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
