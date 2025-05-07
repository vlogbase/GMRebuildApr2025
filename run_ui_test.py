"""
Simple script to run the Flask application for testing UI improvements.
"""

import os
import sys
import logging
from flask import Flask, render_template, redirect, url_for
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "test_secret_key")

@app.route('/')
def home():
    """Redirect to account page for UI testing"""
    return redirect(url_for('billing.account_management'))

if __name__ == "__main__":
    try:
        logger.info("Starting UI test application...")
        
        # Import the billing blueprint (where our account page is)
        from billing import account_bp
        app.register_blueprint(account_bp, url_prefix='/billing')
        
        # Run the Flask application
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error starting UI test application: {e}")
        raise