#!/usr/bin/env python3
"""
Simple Flask server to serve the professional trading dashboard online
"""

from flask import Flask, send_file
import os

app = Flask(__name__)
DASHBOARD_PATH = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def serve_dashboard():
    """Serve the professional dashboard HTML"""
    dashboard_file = os.path.join(DASHBOARD_PATH, 'professional_dashboard_final.html')
    if os.path.exists(dashboard_file):
        return send_file(dashboard_file)
    return "Dashboard file not found", 404

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'trading-dashboard'}, 200

if __name__ == '__main__':
    print("=" * 60)
    print("TRADING DASHBOARD SERVER")
    print("=" * 60)
    print("Starting Flask server on http://localhost:8080")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8080, debug=False)
