"""
Simple test script to add a dedicated test page route to the main app
for testing the model fallback confirmation feature.
"""
import sys
import os
import logging
from flask import render_template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to the path for importing the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app
from app import app

@app.route('/test-fallback-page')
def test_fallback_page():
    """Dedicated test page for model fallback confirmation feature"""
    return render_template('test_fallback.html')

if __name__ == '__main__':
    # Add the test route to the app
    logger.info("Starting app with test fallback page route added")
    logger.info("Test URL: http://localhost:5000/test-fallback-page")
    
    # Run the app with the test route
    app.run(host='0.0.0.0', port=5000, debug=True)