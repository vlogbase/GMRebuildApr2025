"""
Health check module for gunicorn deployments

This module provides simple health check routes required for Replit Deployments
"""

from flask import jsonify

def init_app(app):
    """Initialize health check routes for the Flask application"""
    
    @app.route('/')
    def root_health_check():
        """Root health check endpoint for Replit Deployments"""
        return jsonify({
            "status": "ok",
            "message": "GloriaMundo API is running"
        })
    
    @app.route('/health')
    def health_check():
        """Explicit health check endpoint"""
        return jsonify({
            "status": "ok",
            "service": "GloriaMundo",
            "version": "1.0"
        })
        
    return app