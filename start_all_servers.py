#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 HAMSTER TERMINAL - COMPLETE STARTUP SCRIPT
Uruchamia API i Dashboard jednocześnie
"""

import subprocess
import threading
import time
import sys
import os
from colorama import Fore, Style, init

init(autoreset=True)

def start_api():
    """Start API server on port 5000"""
    print(f"{Fore.GREEN}[1/2] Starting API Server on port 5000...{Style.RESET_ALL}")
    try:
        subprocess.run([
            sys.executable, 'api_server_enhanced.py'
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
    except Exception as e:
        print(f"{Fore.RED}❌ API Server error: {e}{Style.RESET_ALL}")

def start_dashboard():
    """Start HTTP server on port 8000"""
    print(f"{Fore.GREEN}[2/2] Starting HTTP Server on port 8000...{Style.RESET_ALL}")
    time.sleep(2)  # Wait for API to start
    try:
        subprocess.run([
            sys.executable, '-m', 'http.server', '8000'
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
    except Exception as e:
        print(f"{Fore.RED}❌ HTTP Server error: {e}{Style.RESET_ALL}")

if __name__ == '__main__':
    print("=" * 80)
    print(f"{Fore.YELLOW}🐹 HAMSTER TERMINAL - COMPLETE STACK STARTUP{Style.RESET_ALL}")
    print("=" * 80)
    print()
    print(f"{Fore.CYAN}Starting servers...{Style.RESET_ALL}")
    print()
    
    # Start API in background thread
    api_thread = threading.Thread(target=start_api, daemon=False)
    api_thread.start()
    
    time.sleep(1)
    
    # Start dashboard in background thread
    dashboard_thread = threading.Thread(target=start_dashboard, daemon=False)
    dashboard_thread.start()
    
    print()
    print("=" * 80)
    print(f"{Fore.GREEN}✓ SERVERS RUNNING{Style.RESET_ALL}")
    print("=" * 80)
    print()
    print(f"📡 API Server: {Fore.CYAN}http://localhost:5000{Style.RESET_ALL}")
    print(f"   Dashboard: {Fore.CYAN}http://localhost:5000/dashboard{Style.RESET_ALL}")
    print()
    print(f"🌐 HTTP Server: {Fore.CYAN}http://localhost:8000{Style.RESET_ALL}")
    print(f"   Dashboard: {Fore.CYAN}http://localhost:8000/demo_bloomberg_with_api.html{Style.RESET_ALL}")
    print()
    print(f"{Fore.YELLOW}Press Ctrl+C to stop all servers{Style.RESET_ALL}")
    print("=" * 80)
    print()
    
    try:
        api_thread.join()
        dashboard_thread.join()
    except KeyboardInterrupt:
        print()
        print(f"{Fore.RED}Shutting down servers...{Style.RESET_ALL}")
        sys.exit(0)
