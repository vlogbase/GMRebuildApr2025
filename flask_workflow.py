#!/usr/bin/env python3
"""
Simple script to run the Flask application for testing.
"""

import os
import sys
import logging
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        logger.info("Starting Flask application...")
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()