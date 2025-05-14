"""
Simple Flask server workflow for testing the mobile UI
"""

import sys
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='mobile_ui_test.log'
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import app
sys.path.append(str(Path(__file__).parent.parent))

def run():
    """
    Run the Flask application for testing the mobile UI with the long-press model buttons
    """
    try:
        # Log startup
        logger.info("Starting Flask application for mobile UI testing...")
        
        # Import the Flask app
        from app import app
        
        # Run the Flask app on host 0.0.0.0 to allow external access
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', 5000))
        
        # Log startup configuration
        logger.info(f"Starting Flask app on {host}:{port}")
        
        # Run the application
        app.run(host=host, port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run()