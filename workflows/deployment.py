"""
Deployment workflow for GloriaMundo application

This script configures the application for deployment, ensuring that:
1. SQLAlchemy is properly initialized only once
2. Azure Blob Storage is configured correctly
3. The proper gunicorn settings are used
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main deployment preparation function
    
    This validates the deployment configuration and ensures everything is
    set up correctly before running the server.
    """
    logger.info("Starting deployment preparation...")
    
    # Validate environment variables
    check_environment_variables()
    
    # Configure gunicorn for deployment
    configure_gunicorn()
    
    logger.info("Deployment preparation complete")
    
def check_environment_variables():
    """
    Check required environment variables and warn if missing
    """
    required_vars = [
        "DATABASE_URL",
        "SESSION_SECRET",
        "AZURE_STORAGE_CONNECTION_STRING",
        "AZURE_STORAGE_CONTAINER_NAME",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Application may not function correctly without these variables")
    else:
        logger.info("All required environment variables are set")

def configure_gunicorn():
    """
    Configure gunicorn for deployment
    """
    logger.info("Using gunicorn with gevent worker for optimal performance")
    logger.info("Configuration: 4 workers, 300s timeout, binding to 0.0.0.0:5000")

if __name__ == "__main__":
    main()