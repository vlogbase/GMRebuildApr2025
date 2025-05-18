"""
Flask server for running the web chat application
"""
import os
import sys
import logging
from app import app

def run():
    """Run the Flask application on port 5000"""
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app_workflow.log')
        ]
    )
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Starting Flask application server...")
    
    # Run the app
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()