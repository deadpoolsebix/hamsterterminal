#!/usr/bin/env python3
"""
Flask server to serve the professional dashboard with Plotly charts
"""
from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the main dashboard HTML"""
    dashboard_path = os.path.join(os.path.dirname(__file__), 'professional_dashboard_final.html')
    return send_file(dashboard_path)

@app.route('/dashboard')
def dashboard():
    """Alternative route for dashboard"""
    return index()

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Flask Dashboard Server")
    print("=" * 60)
    print("📊 Dashboard available at: http://localhost:8080")
    print("🌐 When using Cloudflare Tunnel: https://[tunnel-url]")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8080, debug=False)
