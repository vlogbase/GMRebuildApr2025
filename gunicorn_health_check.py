"""
Health check module for Gunicorn-based deployments

This module adds a simple health check capability to ensure the application
can properly respond to health check requests from Replit's deployment system.
"""

import logging
from flask import Blueprint, Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a blueprint for health check routes
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """
    Simple health check endpoint that returns a 200 OK response
    
    This allows deployment platforms like Replit to verify the application
    is running properly.
    """
    logger.debug("Health check request received")
    return Response("OK", status=200, mimetype='text/plain')

def init_app(app):
    """
    Register the health check blueprint with the application
    
    Args:
        app: Flask application instance
    """
    logger.info("Registering health check routes")
    app.register_blueprint(health_bp)
    
    # Also add a route handler directly to the app for the root path
    # as some deployment systems check this path specifically
    @app.route('/healthz')
    def root_health_check():
        """Root health check for Kubernetes-style health checks"""
        logger.debug("Root health check request received")
        return Response("OK", status=200, mimetype='text/plain')
        
    logger.info("Health check routes registered successfully")