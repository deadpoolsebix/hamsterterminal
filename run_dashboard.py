"""
💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀
Public Dashboard - Works 24/7!

Najprostsze rozwiązanie - tylko Python, bez dodatkowych instalacji!
"""

from flask import Flask, send_file, send_from_directory
import os

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_file('professional_dashboard_final.html')

@app.route('/professional_dashboard_final.html')
def dashboard():
    return send_file('professional_dashboard_final.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    print("=" * 70)
    print("💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀".center(70))
    print("=" * 70)
    print()
    print("✅ Dashboard Server is RUNNING!")
    print()
    print("📱 ACCESS OPTIONS:")
    print("-" * 70)
    print()
    print("1️⃣  ON THIS COMPUTER:")
    print("    http://localhost:8080")
    print()
    print("2️⃣  ON YOUR PHONE/TABLET (same WiFi):")
    print("    http://192.168.1.132:8080")
    print()
    print("3️⃣  PUBLIC ACCESS (anyone, anywhere):")
    print("    Follow these steps:")
    print()
    print("    A) Keep this window OPEN")
    print("    B) Open NEW terminal and run:")
    print("       ssh -R 80:localhost:8080 serveo.net")
    print()
    print("    C) You'll get a PUBLIC URL like:")
    print("       https://xyz123.serveo.net")
    print()
    print("    D) Share that URL with anyone!")
    print()
    print("=" * 70)
    print("⚠️  KEEP THIS WINDOW OPEN to keep dashboard running")
    print("    Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    # Run Flask
    app.run(host='0.0.0.0', port=8080, debug=False)
