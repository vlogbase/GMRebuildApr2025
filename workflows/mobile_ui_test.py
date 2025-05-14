"""
Flask application workflow file for testing mobile UI improvements
"""
import os
import sys
import logging
from app import app

def run():
    """
    Run the Flask application with debug enabled for testing mobile UI improvements
    """
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Log the start of the application
    logging.info("Starting Flask application for mobile UI testing")
    
    # Run the Flask application
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()