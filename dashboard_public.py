"""
💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀
Online Dashboard - NO REGISTRATION NEEDED!
"""

from flask import Flask, send_file
import os
import subprocess
import sys

app = Flask(__name__)

@app.route('/')
@app.route('/professional_dashboard_final.html')
def dashboard():
    return send_file('professional_dashboard_final.html')

@app.route('/<path:path>')
def serve_file(path):
    if os.path.exists(path):
        return send_file(path)
    return "File not found", 404

if __name__ == '__main__':
    print("💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀")
    print("Starting Online Dashboard Server...")
    print("")
    
    # Start Flask in background
    import threading
    def run_flask():
        app.run(port=5000, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("✅ Server started on port 5000")
    print("🌐 Creating public tunnel...")
    print("")
    
    # Check if Node.js is installed
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        
        # Use npx to run localtunnel (no installation needed)
        print("📡 Connecting to localtunnel...")
        print("🔗 Your public URL will appear below:")
        print("")
        
        subprocess.run([
            "npx",
            "-y",  # Auto-accept install
            "localtunnel",
            "--port", "5000"
        ])
        
    except FileNotFoundError:
        print("❌ Node.js not found!")
        print("📥 Please install Node.js from: https://nodejs.org")
        print("")
        print("Alternative: Access locally at http://localhost:5000")
        print("Or use: http://192.168.1.132:5000 (on your WiFi)")
        
        # Keep Flask running
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nServer stopped.")
