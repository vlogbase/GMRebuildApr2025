"""
Simple Flask server workflow for GloriaMundo

This file runs the Flask application with a specific focus
on performance optimization and debugging.
"""
import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("workflow.flask_app")

def run():
    """
    Run the Flask application with debugging enabled
    """
    try:
        logger.info("Starting Flask application in optimized mode")
        
        # Import the app from app.py
        from app import app as flask_app
        
        # Use 0.0.0.0 to make the server externally visible
        # Default port 5000
        flask_app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        logger.error(f"Error starting Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run()