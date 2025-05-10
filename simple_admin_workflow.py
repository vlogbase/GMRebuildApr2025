"""
Simple script to run the Flask application with admin dashboard functionality.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin.log')
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        # Set environment variable for admin access during development/testing
        if 'ADMIN_EMAILS' not in os.environ:
            os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
            logger.info(f"Set ADMIN_EMAILS environment variable to: {os.environ['ADMIN_EMAILS']}")
        
        # Import the Flask app
        from app import app
        
        # Initialize the admin interface
        from simple_admin import create_admin
        from app import db
        
        # Create admin interface
        admin = create_admin(app, db)
        if admin:
            logger.info("Admin interface created and initialized")
        else:
            logger.error("Failed to create admin interface")
        
        # Log all registered routes for debugging
        logger.info("Registered routes:")
        for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
            logger.info(f"Route: {rule.rule} Methods: {rule.methods}")
        
        # Run the app
        logger.info("Starting Flask application")
        app.run(host='0.0.0.0', port=3000, debug=True)
        
    except Exception as e:
        logger.error(f"Error starting Flask application: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    run()