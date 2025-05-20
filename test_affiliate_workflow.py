"""
Simple Flask server workflow for testing affiliate signup
"""

import logging
from app import app

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for testing affiliate signup
    """
    logger.info("Starting test affiliate workflow")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()