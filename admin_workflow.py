"""
Simple script to run the Flask application for testing the admin dashboard.
"""
import os
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin_output.log')
    ]
)

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with error handling and logging.
    """
    # Make sure the admin email is set first (before importing app)
    admin_emails = os.environ.get('ADMIN_EMAILS', '')
    if not admin_emails:
        logger.warning("ADMIN_EMAILS environment variable not set. Using default (andy@sentigral.com).")
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
    else:
        logger.info(f"Admin emails: {admin_emails}")
    
    try:
        # Import Flask app after environment variables are set
        from app import app
        
        # Enable debug mode for better error messages
        app.debug = True
        
        # Save the server's PID to a file for easy termination
        with open('app.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Initialize admin module explicitly
        import admin
        logger.info("Admin module initialized")
        
        # Start the Flask application
        logger.info("Starting Flask application for admin dashboard testing...")
        app.run(host='0.0.0.0', port=5000)
        
    except Exception as e:
        logger.error(f"Error starting the Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    run()