"""
A simple workflow to run the Flask application for testing mobile UI improvements.
This file is designed to be used with the Replit workflow system.
"""

import os
import logging
from flask import Flask

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mobile_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run():
    """Run the Flask app for testing the mobile UI improvements."""
    try:
        logger.info("Starting Flask app for mobile UI testing...")
        import main
        app = main.app
        
        # Log some information about the static files
        logger.info(f"Static folder path: {app.static_folder}")
        
        # Run the app on all interfaces
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask app: {str(e)}")
        raise

if __name__ == "__main__":
    run()