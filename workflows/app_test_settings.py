"""
Run the Flask app to test the updated account settings UI
"""
import os
import sys
import logging
from app import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app_test_settings.log'
)

def run():
    """
    Run the Flask application
    """
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logging.error(f"Error starting the app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()