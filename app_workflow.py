"""
Simple Flask server workflow for GloriaMundo Chat Application

This workflow runs the Flask application with the model fallback confirmation
feature enabled for testing.
"""
import logging
import os
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app_workflow.log'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application
    """
    try:
        logger.info("Starting Flask application in workflow mode")
        # Make sure the application runs on 0.0.0.0 to be accessible from outside
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        raise

if __name__ == '__main__':
    run()