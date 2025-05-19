"""
Main Application Workflow Script

This script runs the Flask application with all its components.
"""

import os
import sys
import logging
from app import app

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

def run():
    """Run the Flask application server"""
    try:
        # Get port from environment variable or use 5000 as default
        port = int(os.environ.get("PORT", 5000))
        
        logger.info(f"Starting GloriaMundo app on port {port}")
        
        # Run the Flask application
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        logger.exception(f"Error running Flask app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()