"""
Simple script to run the Flask application with admin functionality.
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
        logging.FileHandler('app_output.log')
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Set admin emails environment variable if not already set
        if 'ADMIN_EMAILS' not in os.environ:
            os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
            logger.info(f"Set ADMIN_EMAILS environment variable to: {os.environ['ADMIN_EMAILS']}")
        
        # Import the Flask app (which initializes admin)
        from app import app
        
        # Get the port from environment or use 3000 for deployment
        port = int(os.environ.get('PORT', 3000))
        
        # Run the app
        logger.info(f"Starting Flask application with admin interface on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)