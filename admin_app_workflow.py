"""
Simple script to run the Flask application with admin privileges for testing.
"""

import os
import sys
import logging
from app import app

def run():
    """
    Run the Flask application with admin access enabled.
    """
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("admin_output.log")
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("Starting admin dashboard test workflow")
        
        # Set admin emails for testing
        if "ADMIN_EMAILS" not in os.environ:
            os.environ["ADMIN_EMAILS"] = "andy@sentigral.com,test@example.com"
            logger.info(f"Set ADMIN_EMAILS to: {os.environ['ADMIN_EMAILS']}")
        
        # Check if we're already in app context
        if app:
            host = os.environ.get("HOST", "0.0.0.0")
            port = int(os.environ.get("PORT", 5000))
            
            logger.info(f"Starting admin-enabled Flask application on {host}:{port}")
            logger.info("Access the admin dashboard at: /admin/dashboard")
            logger.info("Or access the account page with admin tab at: /billing/account?tab=admin")
            
            # Run the app
            app.run(host=host, port=port, debug=True, use_reloader=True)
        else:
            logger.error("Failed to get app instance for admin workflow")
    
    except Exception as e:
        logging.error(f"Error in admin workflow: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()