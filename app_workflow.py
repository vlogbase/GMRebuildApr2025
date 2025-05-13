"""
Simple Flask server workflow for the chat app
"""
import os
import sys
import logging
from app import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app_workflow.log'
)

def run():
    """
    Run the Flask application on port 5000 with debugging
    """
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logging.error(f"Error starting the app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()