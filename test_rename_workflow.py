"""
Simple Flask server workflow for testing the chat renaming feature
"""

import os
import logging
from app import app

def run():
    """
    Run the Flask application for testing the chat renaming feature
    """
    try:
        port = 5000
        print(f"Starting server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logging.error(f"Error starting server: {e}")
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    run()