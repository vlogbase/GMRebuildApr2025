"""
Workflow script to run the test_model_api Flask app
"""

import logging
from test_model_api import app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    """
    Run the test model API on port 5001
    """
    logger.info("Starting Test Model API server...")
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == "__main__":
    run()