"""
Test workflow for the admin dashboard
"""

import sys
import os
import logging

# Add the root directory to Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app

def run():
    """
    Run the Flask application for testing the admin dashboard
    """
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Run the Flask application
    flask_app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()