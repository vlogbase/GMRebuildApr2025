"""
Simple script to run the Flask application for testing dark theme compatibility.
"""

import os
import sys
import logging

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
        logger.info("Starting Flask application to test dark theme styling...")
        
        # Set Flask development mode
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        
        # Import the app
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from app import app
        
        # Run the app on port 5000 and listen on all interfaces
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {str(e)}")
        raise

if __name__ == '__main__':
    run()