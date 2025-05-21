"""
Simple Flask server workflow for testing the affiliate system
"""
import os
import logging
from app import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='affiliate_test.log'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for testing affiliate functionality
    """
    logger.info("Starting affiliate system test server")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    run()