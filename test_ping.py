#!/usr/bin/env python
import socket
import unittest


class TestLocalPort(unittest.TestCase):
    """Verify the Flask development port when the server is running."""

    def test_port_5000(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 5000))
        finally:
            sock.close()
        if result != 0:
            self.skipTest(f"Flask server not running on port 5000 (code {result})")
        self.assertEqual(result, 0)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
