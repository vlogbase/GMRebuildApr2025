"""
Simple script to run the Flask application for testing billing functionality.
"""
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('billing_workflow.log')
    ]
)

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        # Import app here to avoid circular imports
        from app import app
        logging.info("Starting Flask application for billing testing")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logging.error(f"Failed to start the application: {e}")
        raise

if __name__ == "__main__":
    run()