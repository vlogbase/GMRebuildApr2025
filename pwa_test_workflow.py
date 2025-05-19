"""
Simple Flask server workflow to test PWA functionality and service worker caching
"""

import logging
import os
from flask import Flask, send_from_directory, render_template

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("pwa-test")

# Create a simple Flask app for testing
app = Flask(__name__)

@app.route('/')
def index():
    """Serve the main index page"""
    return render_template('pwa_test.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/manifest.json')
def serve_manifest():
    """Serve manifest.json from its location"""
    return send_from_directory('static/manifest', 'manifest.json')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)