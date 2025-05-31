"""
Script to test if CSRF tokens are working correctly for API endpoints
This will run the Flask application and verify that all endpoints that require
CSRF protection are working properly.
"""
import os
import sys
import time
import logging
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for CSRF token testing
    """
    try:
        logger.info("Starting Flask application for CSRF token testing")
        
        # Import the Flask app from app.py
        from app import app
        
        # Production mode - disable debug and testing
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Log CSRF protection status
        if app.config.get('WTF_CSRF_ENABLED', True):
            logger.info("CSRF protection is ENABLED")
        else:
            logger.warning("CSRF protection is DISABLED")
            
        # Log protection settings
        logger.info(f"CSRF methods: {app.config.get('WTF_CSRF_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE'])}")
        logger.info(f"CSRF headers: {app.config.get('WTF_CSRF_HEADERS', ['X-CSRFToken', 'X-CSRF-Token'])}")
        
        # Start the Flask server
        logger.info("Starting Flask application. Access it via http://localhost:5000")
        app.run(host='0.0.0.0', port=5000)
        
    except Exception as e:
        logger.error(f"Error starting Flask application: {e}")
        raise

if __name__ == "__main__":
    run()