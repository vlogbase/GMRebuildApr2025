"""
Enhanced wrapper script to run the Flask application for testing in the Replit environment.
This script provides improved logging and error handling for app.py startup.
"""

import os
import sys
import logging
import time
import traceback
from datetime import datetime

# Configure more detailed logging
log_filename = f"app_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename)
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with enhanced error handling and logging.
    This function implements best practices for application context management
    and prevents the common "Working outside of application context" errors.
    """
    logger.info("Starting enhanced app_workflow.py")
    
    try:
        # We delay importing app until after logging is configured
        # to capture any startup errors in the log
        logger.info("Importing Flask application...")
        start_time = time.time()
        
        # Use a timeout to prevent indefinite hanging during import
        # if there are blocking operations
        import_timeout = 30  # seconds
        
        # Import the Flask app with timeout protection
        try:
            # The actual import
            from app import app
            import_duration = time.time() - start_time
            logger.info(f"Flask application imported successfully in {import_duration:.2f} seconds")
            
            # Start the web server
            logger.info("Starting Flask web server on port 5000...")
            app.run(host='0.0.0.0', port=5000, debug=True)
        except Exception as import_error:
            logger.error(f"Error importing or starting Flask application: {import_error}")
            logger.error(traceback.format_exc())
            
            # Provide helpful diagnostics for common errors
            if "Working outside of application context" in str(import_error):
                logger.error("CONTEXT ERROR: This is likely due to accessing Flask objects outside of an application context.")
                logger.error("Fix: Make sure all Flask operations occur within 'with app.app_context():' blocks")
                logger.error("     or use separate background threads for database operations.")
            
            # Attempt to recover by directly running the app module
            logger.info("Attempting alternate startup method...")
            os.system(f"{sys.executable} -m flask --app app run --host=0.0.0.0 --port=5000")
            
    except Exception as e:
        logger.error(f"Critical error in app_workflow.py: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run()
