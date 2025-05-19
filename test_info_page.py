"""
Simple Flask server workflow for testing the /info page
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for testing
    """
    # Import app from the main module
    sys.path.insert(0, os.getcwd())
    try:
        from app import app
        
        # Set Flask development environment
        os.environ['FLASK_ENV'] = 'development'
        
        # Configure app for testing
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        
        # Log start
        logger.info("Starting Flask test server for /info page")
        
        # Run the app
        app.run(host='0.0.0.0', port=5000)
        
    except Exception as e:
        logger.error(f"Error starting test server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()