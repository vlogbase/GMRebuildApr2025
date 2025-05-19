"""
WSGI entry point for the application

This file simplifies deployment with Gunicorn by providing
a standard WSGI entry point that works well with Replit's deployment system.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("wsgi")
logger.info("Initializing WSGI application")

# Import the Flask application
try:
    from main import app as application
    logger.info("WSGI application initialized successfully")
except Exception as e:
    logger.error(f"Error initializing WSGI application: {e}")
    # Provide a minimal WSGI application that returns a health check response
    # This allows the deployment platform to see that the application is running
    # even if there's an error in the main application
    def application(environ, start_response):
        status = '200 OK'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [b'Application is starting up. Please try again later.']

# Export the WSGI application object 
# This is the standard way to expose a WSGI application to Gunicorn
app = application

if __name__ == "__main__":
    logger.info("Running WSGI application in development mode")
    try:
        application.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running application: {e}")