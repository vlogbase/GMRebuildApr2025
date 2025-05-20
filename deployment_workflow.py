"""
Deployment workflow for GloriaMundo application

This script starts the Flask application using port 3000 to match Replit Deployments expectations
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """Run the Flask application for deployment"""
    try:
        # Add the parent directory to sys.path to import app
        sys.path.append(str(Path(__file__).parent))
        
        # Log startup
        logger.info("Starting Flask application for deployment testing...")
        
        # Import health check module
        try:
            from gunicorn_health_check import init_app as init_health_check
            logger.info("Health check module imported successfully")
        except ImportError as e:
            logger.error(f"Failed to import health check module: {e}")
            
        # Import the Flask app
        from app import app
        
        # Add health check routes
        try:
            from gunicorn_health_check import init_app as init_health_check
            init_health_check(app)
            logger.info("Health check routes registered successfully")
        except Exception as e:
            logger.error(f"Error setting up health check routes: {e}")
        
        # Use port 3000 for deployment (Replit Deployments expects this)
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', 3000))
        
        # Log startup configuration
        logger.info(f"Starting Flask app on {host}:{port} for deployment")
        
        # Run the application
        app.run(host=host, port=port, debug=False)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run()