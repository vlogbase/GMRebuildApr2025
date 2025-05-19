"""
WSGI entry point for GloriaMundo application.
This file is used for deployment to make the application compatible with Replit Deployments.
"""

import os
import logging
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get port from environment variable or use 3000 as the default for Replit Deployments
port = int(os.environ.get('PORT', 3000))

if __name__ == '__main__':
    logger.info(f"Starting server on port {port} for deployment")
    app.run(host='0.0.0.0', port=port, debug=False)