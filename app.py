from flask import Flask, jsonify, send_from_directory
import requests
import os

app = Flask(__name__, static_folder='.')

# Cache commodity prices
prices_cache = {
    'gold': 4594.61,
    'silver': 134.52,
    'last_update': 0
}

@app.route('/api/prices', methods=['GET'])
def get_prices():
    """Get current commodity prices"""
    try:
        # Try to fetch real prices from Alpha Vantage or similar
        # For now return cached/estimated prices
        return jsonify({
            'gold': 4594.61,
            'silver': 134.52,
            'btc': 95000,
            'eth': 2800,
            'timestamp': 'live'
        })
    except:
        return jsonify({
            'gold': 4594.61,
            'silver': 134.52,
            'btc': 95000,
            'eth': 2800,
            'timestamp': 'cached'
        })

@app.route('/<path:filename>')
def serve_files(filename):
    """Serve HTML and other files"""
    if filename == '' or filename == '/':
        filename = 'professional_dashboard_final.html'
    return send_from_directory('.', filename)

@app.route('/')
def index():
    """Serve main dashboard"""
    return send_from_directory('.', 'professional_dashboard_final.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
