"""
Script to run the Flask application with our fixed JSON handling
"""

import sys
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    filename='fixed_app_output.log',
    filemode='w'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with our fixed JSON handling
    """
    try:
        # Log startup
        logger.info("Starting Flask application with fixed JSON handling...")
        
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