"""
Simple Flask server workflow for GloriaMundo Test

This workflow runs the main Flask application for testing purposes.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for testing
    """
    try:
        logger.info("Starting GloriaMundo App Test Workflow")
        logger.info("--------------------------------------")
        logger.info("This workflow will run the Flask application")
        logger.info("The application will be available at the webview URL")
        logger.info("Press Ctrl+C to stop the workflow")
        logger.info("--------------------------------------")
        
        # Run the Flask application
        subprocess.run(["python", "app.py"])
        
    except KeyboardInterrupt:
        logger.info("Workflow stopped by user")
    except Exception as e:
        logger.error(f"Error running workflow: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()