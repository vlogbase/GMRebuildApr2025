"""
Simple script to run the Flask application for testing admin access functionality.
"""

import os
import sys
import logging
from datetime import datetime

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
        logger.info("Starting Flask application for admin access testing")
        
        # Print relevant environment variables for debugging
        admin_emails = os.environ.get('ADMIN_EMAILS', 'Not set')
        logger.info(f"ADMIN_EMAILS env variable: {admin_emails}")
        
        # Import here to avoid circular imports
        from app import app
        
        # Run the app
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()