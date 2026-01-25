import threading
import subprocess
import sys
import os

print("=" * 50)
print("🚀 STARTING HAMSTER TERMINAL - MAIN LAUNCHER")
print("=" * 50)

def run_api_server():
    print("🌐 Starting API Server...")
    subprocess.run([sys.executable, "api_server.py"])

def run_telegram_bot():
    print("🤖 Starting Telegram Bot...")
    subprocess.run([sys.executable, "telegram_bot_buttons.py"])

if __name__ == "__main__":
    print(f"Python: {sys.executable}")
    print(f"Working dir: {os.getcwd()}")
    
    t1 = threading.Thread(target=run_api_server, daemon=True)
    t2 = threading.Thread(target=run_telegram_bot, daemon=True)
    
    t1.start()
    t2.start()
    
    print("✅ Both services started!")
    print("Press Ctrl+C to stop...")
    
    try:
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
