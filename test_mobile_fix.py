"""
Test workflow for mobile conversation selection fix
"""
import os
import logging
from app import app

def run():
    """
    Run the Flask application to test the mobile conversation selection fix
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Flask server to test mobile conversation selection fix...")
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run()