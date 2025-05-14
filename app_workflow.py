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
    Run the Flask application on port 3000 with debugging (or use PORT from environment)
    """
    port = int(os.environ.get('PORT', 3000))
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logging.error(f"Error starting the app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()