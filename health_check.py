"""
Health check module for deployment

This module provides simple health check endpoints for deployment monitoring.
"""

import logging
from flask import Blueprint, Response, jsonify

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint for health check routes
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring systems"""
    return jsonify({"status": "ok", "message": "Application is healthy"})
    
@health_bp.route('/healthz')
def kubernetes_health():
    """Kubernetes-style health check endpoint"""
    return Response("OK", status=200, mimetype='text/plain')

def init_app(app):
    """Register the health check blueprint with the Flask app"""
    # DISABLED: No longer registering this blueprint to avoid endpoint conflicts
    # app.register_blueprint(health_bp)
    logger.info("Health check blueprint disabled to avoid endpoint conflicts")
