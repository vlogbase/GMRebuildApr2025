"""
Simple script to run the Flask application with admin dashboard functionality.
"""

import os
import sys
import logging
from app import app, db
from gm_admin import create_admin

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('admin_output.log')
            ]
        )
        logger = logging.getLogger(__name__)
        
        # Set environment variable for admin access during development/testing
        if 'ADMIN_EMAILS' not in os.environ:
            os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
            logger.info(f"Set ADMIN_EMAILS environment variable to: {os.environ['ADMIN_EMAILS']}")
        
        # Initialize the admin interface
        admin = create_admin(app, db)
        logger.info("Admin interface created and initialized")
        
        # Log all registered routes for debugging
        logger.info("Registered routes:")
        for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
            logger.info(f"Route: {rule.rule} Methods: {rule.methods}")
        
        # Run the app
        logger.info("Starting Flask application")
        app.run(host='0.0.0.0', port=3000, debug=True)
        
    except Exception as e:
        logging.error(f"Error starting Flask application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    run()