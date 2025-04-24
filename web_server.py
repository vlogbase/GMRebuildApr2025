"""
Simple script to run the Flask application in a workflow context.
"""
import os
import sys
import logging
from app import app

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting Flask app in workflow")
    
    # Run the app on host 0.0.0.0 to make it accessible over the network
    app.run(host='0.0.0.0', port=5000, debug=True)