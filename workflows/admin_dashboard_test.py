"""
Simple Flask server workflow for testing the admin dashboard
"""

import os
import sys
import logging
from app import app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin_dashboard_test.log')
    ]
)

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application.
    """
    try:
        logger.info("Starting Flask server for admin dashboard testing")
        # Run the Flask app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask app: {e}", exc_info=True)

if __name__ == "__main__":
    run()