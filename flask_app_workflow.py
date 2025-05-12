"""
Simple script to run the Flask application for testing in the Replit environment.
This is a wrapper script to start the app.py Flask application.
"""
import logging
import sys
import os
from app import app

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('app_workflow.log')
            ]
        )
        logger = logging.getLogger(__name__)
        
        logger.info("Starting Flask application for testing")
        
        # Check if CSRF protection is enabled
        csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)
        csrf_methods = app.config.get('WTF_CSRF_METHODS', set())
        csrf_headers = app.config.get('WTF_CSRF_HEADERS', [])
        
        logger.info(f"CSRF protection is {'ENABLED' if csrf_enabled else 'DISABLED'}")
        if csrf_enabled:
            logger.info(f"CSRF methods: {csrf_methods}")
            logger.info(f"CSRF headers: {csrf_headers}")
        
        logger.info("Starting Flask application. Access it via http://localhost:5000")
        
        # Run the Flask app
        app.run(host='0.0.0.0', debug=True)
    except Exception as e:
        logger.exception(f"Error running Flask application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()