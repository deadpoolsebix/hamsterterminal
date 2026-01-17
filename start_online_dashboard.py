#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick start script - uruchamia dashboard server + HTTP server
"""

import subprocess
import sys
import time
import os

def main():
    print("=" * 80)
    print("🚀 BLOOMBERG TERMINAL - ONLINE DASHBOARD STARTER")
    print("=" * 80)
    print()
    print("Ten skrypt uruchomi:")
    print("  1. Dashboard Data Engine (aktualizuje data.json co 3s)")
    print("  2. HTTP Server (localhost:8000)")
    print()
    print("Następnie możesz użyć Ngrok:")
    print("  ngrok http 8000")
    print()
    print("=" * 80)
    print()
    
    # Check if data engine should run
    print("[1/2] Starting Dashboard Data Engine...")
    
    try:
        # Start data engine in background
        if sys.platform == 'win32':
            data_engine = subprocess.Popen(
                ['python', 'dashboard_server.py'],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            data_engine = subprocess.Popen(['python', 'dashboard_server.py'])
        
        print("[✓] Data Engine started (PID: {})".format(data_engine.pid))
        time.sleep(2)
        
    except Exception as e:
        print(f"[!] Error starting data engine: {e}")
        return
    
    print()
    print("[2/2] Starting HTTP Server on port 8000...")
    print()
    print("=" * 80)
    print("📡 Dashboard dostępny pod adresem:")
    print("   http://localhost:8000/dashboard_online.html")
    print()
    print("🌍 Aby udostępnić online, uruchom w nowym terminalu:")
    print("   ngrok http 8000")
    print()
    print("Naciśnij Ctrl+C aby zatrzymać wszystko")
    print("=" * 80)
    print()
    
    try:
        # Start HTTP server (blocking)
        subprocess.run([
            'python', '-m', 'http.server', '8000'
        ])
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        data_engine.terminate()
        print("[✓] Everything stopped")

if __name__ == "__main__":
    main()
