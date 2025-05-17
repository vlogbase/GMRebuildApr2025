"""
Standalone test for the model fallback confirmation feature.
This script creates a minimal Flask app to test the feature.
"""
import os
from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "test-secret-key")
csrf = CSRFProtect(app)

@app.route('/test-fallback')
def test_fallback():
    """
    Test page for the model fallback confirmation feature.
    """
    return render_template('test_fallback.html')

@app.route('/api/fallback/check_preference', methods=['GET'])
def check_fallback_preference():
    """
    Check if the user has enabled automatic fallback in their preferences.
    For testing purposes, this always returns false.
    """
    return jsonify({
        'auto_fallback_enabled': False
    })

@app.route('/api/fallback/update_preference', methods=['POST'])
def update_fallback_preference():
    """
    Update the user's automatic fallback preference.
    For testing purposes, this always returns success.
    """
    data = request.json
    auto_fallback_enabled = data.get('auto_fallback_enabled', False)
    
    return jsonify({
        'success': True,
        'auto_fallback_enabled': auto_fallback_enabled
    })

if __name__ == '__main__':
    print("Starting test server on http://0.0.0.0:5000/test-fallback")
    app.run(host='0.0.0.0', port=5000, debug=True)