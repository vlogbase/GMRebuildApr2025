"""
Test workflow for conversation management

This workflow tests the conversation cleanup functionality.
"""
import logging
from app import app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application.
    """
    logger.info("Starting Flask application with conversation cleanup functionality")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

if __name__ == '__main__':
    run()