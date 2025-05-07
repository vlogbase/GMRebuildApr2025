"""
Simple script to run the Flask application for testing the affiliate features.
"""

import os
import logging
from flask import Flask, render_template, url_for
from app import app

def run():
    """
    Run the Flask application.
    """
    try:
        # Start the Flask server on port 5000
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logging.error(f"Error running flask app: {e}")
        raise

if __name__ == "__main__":
    run()