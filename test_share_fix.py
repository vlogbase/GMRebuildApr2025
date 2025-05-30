"""
Test workflow for the shared conversation guest view fix
"""
import sys
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application to test the shared conversation guest view fix
    """
    try:
        logger.info("Starting Flask application to test shared conversation guest view fix...")
        
        # Import the Flask app
        from app import app
        
        # Run the Flask app on host 0.0.0.0 to allow external access
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', 5000))
        
        logger.info(f"Starting Flask app on {host}:{port}")
        logger.info("Testing fix for guest users viewing shared conversations")
        
        # Run the application
        app.run(host=host, port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run()