"""
Simple script to test the Flask application with the application context fixes.
This is a wrapper script to start the app.py Flask application.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        logger.info("Starting Flask application in test mode with application context fixes")
        
        # Import and run the application
        from app import app
        
        # Set host to 0.0.0.0 to make the server externally accessible
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run()