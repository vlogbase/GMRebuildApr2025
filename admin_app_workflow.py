"""
Simple script to run the Flask application with admin privileges for testing.
"""

import os
import sys
import logging
from datetime import datetime

from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with admin access enabled.
    """
    try:
        # Set environment variables for admin testing
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com,test@example.com'
        os.environ['FLASK_ENV'] = 'development'
        
        # Import the Flask app object
        from app import app
        
        # Run the application
        logger.info("Starting Flask application with admin access enabled...")
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=True,
            use_reloader=False  # Disable reloader in development to avoid duplicate processes
        )
        
    except Exception as e:
        logger.error(f"Error starting the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
    else:
        print("Usage: python admin_app_workflow.py run")