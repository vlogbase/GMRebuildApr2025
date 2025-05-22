"""
Test workflow for the simplified affiliate system
"""
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """Run the Flask application with the simplified affiliate system"""
    logger.info("Starting simplified affiliate system test workflow")
    
    try:
        # Import the necessary modules
        from app import app
        from simplified_affiliate import simplified_affiliate_bp
        
        # Run the app
        logger.info("Starting Flask app on http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running the affiliate test workflow: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()