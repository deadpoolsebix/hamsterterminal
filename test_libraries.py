#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Script - Weryfikacja Zainstalowanych Bibliotek
Data: 15 stycznia 2026
"""

import sys
print("=" * 60)
print("TEST ZAINSTALOWANYCH BIBLIOTEK")
print("=" * 60)

# Test bibliotek finansowych
print("\n[1] Testowanie bibliotek finansowych...")
try:
    import finvizfinance
    print("✓ finvizfinance zainstalowana")
except ImportError as e:
    print(f"✗ finvizfinance błąd: {e}")

try:
    import pyql
    print("✓ PyQL zainstalowana")
except ImportError as e:
    print(f"✗ PyQL błąd: {e}")

try:
    import tensortrade
    print("✓ tensortrade zainstalowana")
except ImportError as e:
    print(f"✗ tensortrade błąd: {e}")

# Test bibliotek naukowych
print("\n[2] Testowanie bibliotek naukowych...")
try:
    import numpy as np
    print(f"✓ numpy {np.__version__} zainstalowana")
except ImportError as e:
    print(f"✗ numpy błąd: {e}")

try:
    import pandas as pd
    print(f"✓ pandas {pd.__version__} zainstalowana")
except ImportError as e:
    print(f"✗ pandas błąd: {e}")

try:
    import scipy
    print(f"✓ scipy zainstalowana")
except ImportError as e:
    print(f"✗ scipy błąd: {e}")

try:
    import matplotlib.pyplot as plt
    print("✓ matplotlib zainstalowana")
except ImportError as e:
    print(f"✗ matplotlib błąd: {e}")

# Test ML
print("\n[3] Testowanie bibliotek Machine Learning...")
try:
    import tensorflow as tf
    print(f"✓ TensorFlow {tf.__version__} zainstalowana")
except ImportError as e:
    print(f"✗ TensorFlow błąd: {e}")

try:
    import keras
    print(f"✓ Keras zainstalowana")
except ImportError as e:
    print(f"✗ Keras błąd: {e}")

try:
    import gym
    print("✓ gym zainstalowana")
except ImportError as e:
    print(f"✗ gym błąd: {e}")

# Test web scraping
print("\n[4] Testowanie bibliotek Web...")
try:
    import requests
    print("✓ requests zainstalowana")
except ImportError as e:
    print(f"✗ requests błąd: {e}")

try:
    from bs4 import BeautifulSoup
    print("✓ BeautifulSoup zainstalowana")
except ImportError as e:
    print(f"✗ BeautifulSoup błąd: {e}")

# Test vollib
print("\n[5] Testowanie vollib...")
try:
    import vollib
    print("✓ vollib zainstalowana")
except ImportError as e:
    print(f"✗ vollib nie zainstalowana: {e}")
    print("  Uwaga: vollib wymaga SWIG do kompilacji")

print("\n" + "=" * 60)
print("TEST ZAKOŃCZONY")
print("=" * 60)
