"""
Test script for the model fallback confirmation feature.

This script runs the Flask application and focuses on
testing the model fallback confirmation dialog functionality.
"""
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_fallback_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Import the Flask app
from app import app

if __name__ == '__main__':
    print("Starting model fallback test server...")
    logging.info("Model fallback test server started")
    
    # Set important environment variables for testing
    os.environ['FLASK_DEBUG'] = '1'
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)