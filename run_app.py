#!/usr/bin/env python3
"""
Run script for the Flask application.
This script ensures that the correct environment variables are set,
and that the application is started with the appropriate configuration.
"""
import os
import sys
import logging
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

if __name__ == "__main__":
    # Set up port
    port = int(os.environ.get("PORT", 5000))
    
    # Log startup information
    logging.info(f"Starting server on port {port}")
    logging.info(f"Debug mode: {app.debug}")
    
    # Run the Flask app
    app.run(host="0.0.0.0", port=port)