"""
A simple workflow to run the Flask application for testing mobile UI improvements.
"""

import sys
import os
import logging
from flask import Flask

# Get the absolute path of the repo
repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, repo_path)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run():
    """Run the Flask app for testing the mobile UI improvements."""
    try:
        logger.info("Starting Flask app for mobile UI testing...")
        from app import app
        
        # Log the static files directory to verify CSS and JS files
        static_dir = os.path.join(repo_path, 'static')
        logger.info(f"Static directory: {static_dir}")
        
        # Run the app on all interfaces
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask app: {str(e)}")
        raise

if __name__ == "__main__":
    run()