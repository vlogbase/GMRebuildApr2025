"""
Simple Flask server workflow for GloriaMundo Chatbot

This workflow now includes the model fallback functionality to test:
1. The model fallback confirmation dialog when a model is unavailable
2. The auto-fallback preference setting in the account page
3. The model availability check endpoint
"""

import os
import logging
from main import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app_workflow.log'
)

# Set environment variables for testing
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

def run():
    """
    Run the Flask application for testing
    """
    # Log the startup
    logging.info("Starting Flask application for model fallback testing")
    
    try:
        # Start the Flask application
        app.run(
            host='0.0.0.0',  # Make the server externally visible
            port=5000,       # Default Flask port
            debug=True       # Enable debug mode
        )
    except Exception as e:
        logging.error(f"Error starting Flask application: {e}")
        raise

if __name__ == "__main__":
    run()