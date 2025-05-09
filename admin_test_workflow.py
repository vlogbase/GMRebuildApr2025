"""
Simple script to run the Flask application for testing admin access functionality.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for admin dashboard testing.
    """
    try:
        logger.info("Starting Flask application for admin dashboard testing")
        
        # Force development mode and set admin email
        os.environ['FLASK_ENV'] = 'development'
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
        logger.info(f"ADMIN_EMAILS env variable set to: {os.environ['ADMIN_EMAILS']}")
        
        # Import and run app
        from app import app
        logger.info("Starting Flask app on port 5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run()