"""
Script to run the Flask application for testing
"""
import os
import sys
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_app():
    """Run the Flask application"""
    try:
        logger.info("Starting Flask application")
        # Import the app here to avoid circular imports
        from app import app
        
        # Run the app with the application factory
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_app()