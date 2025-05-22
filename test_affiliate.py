"""
Test script for the affiliate system

This script tests the PayPal email update functionality without requiring a workflow.
It runs the Flask app in debug mode to verify our JavaScript fixes.
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
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting affiliate system test")

# Run the Flask app
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)