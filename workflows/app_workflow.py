"""
Simple Flask server workflow for GloriaMundo Chat Application
"""

from main import app
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application
    """
    logger.info("Starting Flask application workflow")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()