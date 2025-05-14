"""
Simple Flask server workflow for testing URL formatting in chat messages
"""

import os
import logging
from app import app

def run():
    """
    Run the Flask application for testing URL formatting in chat messages.
    """
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Enable debug mode for development
    app.debug = True
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    logger.info(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    run()