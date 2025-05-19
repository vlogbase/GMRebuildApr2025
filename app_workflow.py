"""
Main Application Workflow Script

This script runs the Flask application with all improved components:
- Redis connection with fallback mechanisms
- Fixed blueprint registrations for jobs and affiliate modules
- Robust error handling for Redis operations
"""

import os
import sys
import logging

# Configure logging first (before any other imports)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app_workflow.log')
    ]
)

logger = logging.getLogger(__name__)

# Set up Redis environment variables for testing if not present
# This allows the system to start up with Redis in fallback mode
if not os.environ.get("REDIS_HOST"):
    logger.warning("REDIS_HOST not set, Redis features will use fallback mode")
    os.environ["REDIS_HOST"] = ""  # Empty string to trigger fallback

# Import the improved modules with fixed circular dependencies
# Import these before importing the app to ensure they're available
logger.info("Initializing improved modules")
try:
    from jobs_blueprint_improved import init_app as init_jobs_bp
    logger.info("Imported improved jobs blueprint")
except Exception as e:
    logger.error(f"Error importing improved jobs blueprint: {e}")

try:
    from affiliate_blueprint_improved import init_app as init_affiliate_bp
    logger.info("Imported improved affiliate blueprint")
except Exception as e:
    logger.error(f"Error importing improved affiliate blueprint: {e}")

# Now import the app module
logger.info("Importing main app module")
from app import app

def run():
    """Run the Flask application server"""
    try:
        # Get port from environment variable or use 5000 as default
        port = int(os.environ.get("PORT", 5000))
        
        logger.info(f"Starting GloriaMundo app on port {port}")
        
        # Run the Flask application
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        logger.exception(f"Error running Flask app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()