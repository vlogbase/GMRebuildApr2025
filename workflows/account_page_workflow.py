"""
Simple workflow to run the Flask application for testing account page enhancements.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application in workflow mode.
    """
    try:
        logger.info("Starting account page workflow...")
        
        # Set environment variables
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        os.environ['REPLIT_WORKFLOW_MODE'] = 'true'
        
        # Add root directory to path
        root_dir = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(root_dir))
        
        # Import app
        from app import app
        
        # Run the Flask application
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error starting account page workflow: {e}")
        raise

if __name__ == "__main__":
    run()