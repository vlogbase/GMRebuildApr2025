"""
Simple test workflow to verify the model fallback confirmation feature.
"""
import os
import sys
import logging

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

def run():
    """Run the Flask application with the model fallback feature enabled"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Log startup message
    logging.info("Starting test_fallback workflow to verify model fallback confirmation")
    
    # Set environment variables for testing
    os.environ['FLASK_DEBUG'] = '1'
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    run()