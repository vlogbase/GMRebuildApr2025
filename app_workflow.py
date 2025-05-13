"""
Main application workflow
"""

import logging
import sys
from app import app as flask_app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app_workflow.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application
    """
    logger.info("Starting Flask application")
    flask_app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    run()