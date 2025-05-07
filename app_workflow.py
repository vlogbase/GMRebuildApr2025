"""
Simple script to run the Flask application for testing in the Replit environment.
This is a wrapper script to start the app.py Flask application.
"""

import os
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        logger.info("Starting Flask application in workflow")
        
        # Set Flask development mode
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        
        # Log environment for debugging
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Import the app after setting environment variables
        from app import app
        
        # Log route information
        logger.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.info(f"  {rule.endpoint} - {rule.rule}")
        
        # Run the app on port 3000 and listen on all interfaces
        logger.info("Starting Flask server on port 3000")
        app.run(host='0.0.0.0', port=3000, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    run()