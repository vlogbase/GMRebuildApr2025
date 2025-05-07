"""
Test script to run the app with our fixes.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='test_fix_output.log'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        # Log startup
        logger.info("Starting Flask application with improved model handling and account linking...")
        
        # Import the Flask app
        from app import app
        
        # Run the Flask app on host 0.0.0.0 to allow external access
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', 5000))
        
        # Log startup configuration
        logger.info(f"Starting Flask app on {host}:{port}")
        
        # Run the application
        app.run(host=host, port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run()