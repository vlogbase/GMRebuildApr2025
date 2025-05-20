"""
Run the Flask application with app.py as the entry point.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app_workflow.log')
    ]
)

logger = logging.getLogger(__name__)

def run_app():
    """
    Run the Flask application using app.py as the entry point.
    """
    try:
        logger.info("Starting application workflow...")
        
        # Run the Flask application
        os.system("python app.py")
        
        logger.info("Application workflow completed.")
    except Exception as e:
        logger.error(f"Error in application workflow: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    run_app()