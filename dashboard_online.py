"""
💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀
Online Dashboard with pyngrok
"""

from flask import Flask, send_file
import os

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
    
    try:
        from pyngrok import ngrok
        
        # Open ngrok tunnel
        public_url = ngrok.connect(5000)
        print(f"✅ Dashboard is ONLINE!")
        print(f"🌐 Public URL: {public_url}")
        print(f"📱 Share this link with anyone - works on phone & computer!")
        print("")
        print("⚠️  Keep this window open to keep the dashboard online")
        print("Press Ctrl+C to stop")
        print("")
        
        # Start Flask server
        app.run(port=5000)
        
    except ImportError:
        print("📥 Installing pyngrok...")
        os.system("pip install pyngrok flask")
        print("✅ Installed! Please run the script again.")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Starting local server on port 5000...")
        app.run(port=5000, debug=False)
