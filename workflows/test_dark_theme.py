"""
Script to run the Flask application for testing dark theme UI improvements.
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
    Run the Flask application for testing dark theme UI.
    """
    try:
        logger.info("Starting Flask application for dark theme testing...")
        
        # Set environment variables
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        
        # Add root directory to path
        root_dir = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(root_dir))
        
        # Import and run the app
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error running dark theme test app: {str(e)}")
        raise

if __name__ == "__main__":
    run()