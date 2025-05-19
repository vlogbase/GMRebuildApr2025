"""
Flask server workflow for testing the billing/account fix
"""

import os
import sys
import logging
from flask import Flask, render_template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application
    """
    # We import the app from the main application file
    sys.path.insert(0, os.getcwd())
    
    try:
        # Import the app from app.py
        from app import app
        
        # Run the Flask app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask app: {e}")
        raise

if __name__ == "__main__":
    run()
