#!/usr/bin/env python
import importlib
import unittest

REQUIRED_MODULES = [
    'numpy',
    'pandas',
    'scipy',
    'matplotlib',
    'requests',
]

OPTIONAL_MODULES = [
    'finvizfinance',
    'pyql',
    'tensortrade',
    'tensorflow',
    'keras',
    'gym',
    'bs4',
    'vollib',
]


class TestRequiredLibraries(unittest.TestCase):
    """Ensure core scientific dependencies are available."""

    def test_required_modules(self) -> None:
        for module in REQUIRED_MODULES:
            with self.subTest(module=module):
                importlib.import_module(module)


class TestOptionalLibraries(unittest.TestCase):
    """Informative checks for optional packages."""

    def test_optional_modules(self) -> None:
        missing = []
        for module in OPTIONAL_MODULES:
            try:
                importlib.import_module(module)
            except ImportError as exc:
                missing.append(f"{module}: {exc}")
        if missing:
            self.skipTest("Optional modules missing → " + ", ".join(missing))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
