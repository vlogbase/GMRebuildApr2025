"""
Admin dashboard workflow for testing the Flask application.
"""
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to sys.path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin_test.log')
    ]
)

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for admin dashboard testing.
    """
    try:
        # Make sure the admin email is set
        admin_emails = os.environ.get('ADMIN_EMAILS', '')
        if not admin_emails:
            logger.warning("ADMIN_EMAILS environment variable not set. Using default (andy@sentigral.com).")
            os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
        else:
            logger.info(f"Admin emails: {admin_emails}")
            
        # Import the Flask app
        from app import app
        
        # Enable debug mode for better error messages
        app.debug = True
        
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