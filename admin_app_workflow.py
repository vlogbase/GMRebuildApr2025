"""
Simple script to run the Flask application with admin privileges for testing.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with admin access enabled.
    """
    try:
        logger.info("Starting Flask application with admin access")
        
        # Set environment variables for admin testing
        os.environ['FLASK_ENV'] = 'development'
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
        logger.info(f"ADMIN_EMAILS env variable set to: {os.environ['ADMIN_EMAILS']}")
        
        # Import the Flask app from app.py
        from app import app
        
        # Set debug mode
        app.config['DEBUG'] = True
        
        # Log access control settings
        logger.info("Admin access enabled for testing")
        logger.info(f"Admin emails: {os.environ.get('ADMIN_EMAILS')}")
        
        # Start the Flask server
        logger.info("Starting Flask application with admin access. Access it via http://localhost:5000")
        app.run(host='0.0.0.0', port=5000)
        
    except Exception as e:
        logger.error(f"Error starting Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run()