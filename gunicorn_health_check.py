"""
Health check module for gunicorn deployments

This module provides simple health check routes required for Replit Deployments
"""

from flask import jsonify

def init_app(app):
    """Initialize health check routes for the Flask application"""
    
    @app.route('/healthz')
    def kubernetes_health_check():
        """Kubernetes-style health check endpoint for Replit Deployments"""
        return jsonify({
            "status": "ok",
            "message": "GloriaMundo API is running"
        })
    
    @app.route('/health/status')
    def detailed_health_check():
        """Detailed health check endpoint with version info"""
        return jsonify({
            "status": "ok",
            "service": "GloriaMundo",
            "version": "1.0"
        })
        
    return app