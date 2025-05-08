#!/usr/bin/env python3
"""
Test workflow to verify UI enhancements for model display names.
"""

import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    try:
        # Start the Flask app directly
        logger.info("Starting Flask application to test UI enhancements...")
        subprocess.run(["python", "app.py"])
        
        return 0
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run())