"""
Workflow script to run the Flask application with admin interface.
"""

import os
import sys
import logging
from app import app, db
from gm_admin import create_admin

def run():
    """
    Run the Flask application with admin interface.
    """
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('app_output.log')
            ]
        )
        
        # Set environment variable for admin access during development/testing
        if 'ADMIN_EMAILS' not in os.environ:
            os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
            logging.info(f"Set ADMIN_EMAILS environment variable to: {os.environ['ADMIN_EMAILS']}")
        
        # Initialize the admin interface
        admin = create_admin(app, db)
        logging.info("Admin interface created and initialized")
        
        # Log all registered routes for debugging
        logging.info("Registered routes:")
        for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
            logging.info(f"Route: {rule.rule} Methods: {rule.methods}")
        
        # Run the app
        logging.info("Starting Flask application")
        app.run(host='0.0.0.0', port=3000, debug=True)
        
    except Exception as e:
        logging.error(f"Error starting Flask application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    run()