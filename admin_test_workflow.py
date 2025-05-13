"""
Test workflow for the admin dashboard
"""

import logging
import sys
from app import app as flask_app

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for testing the admin dashboard
    """
    logger.info("Starting admin dashboard test")
    # Run the Flask application in non-debug mode to prevent auto-restart
    flask_app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    run()