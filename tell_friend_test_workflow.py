"""
Simple script to run the Flask application for testing the Tell a Friend tab.
"""

import os
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        logger.info("Starting Flask application to test the Tell a Friend tab")
        
        # Set Flask development mode
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        
        # Log environment for debugging
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Import the app
        from app import app
        
        # Run the app on port 3000 and listen on all interfaces
        logger.info("Starting Flask server on port 3000")
        app.run(host='0.0.0.0', port=3000, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    run()