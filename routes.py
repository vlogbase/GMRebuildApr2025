"""
Routes module for the Flask application.
This module contains all routes and endpoints for the application.
"""

import logging
import os
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

# Set up logging
logger = logging.getLogger(__name__)

def register_routes(app):
    """Register all application routes with the Flask app"""
    # Import here to avoid circular imports
    from app import (
        handle_chat, upload_file, get_model_details, list_conversations, 
        get_conversation, create_conversation, update_conversation, 
        delete_conversation, get_user_preferences, update_user_preferences,
        login_view, register_view, logout_view, account_view, check_model_price
    )
    
    # Set up LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Define user loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Main application routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Authentication routes
    app.route('/login', methods=['GET', 'POST'])(login_view)
    app.route('/register', methods=['GET', 'POST'])(register_view)
    app.route('/logout')(logout_view)
    app.route('/account')(account_view)
    
    # API routes
    app.route('/api/chat', methods=['POST'])(handle_chat)
    app.route('/api/upload', methods=['POST'])(upload_file)
    app.route('/api/model-details', methods=['GET'])(get_model_details)
    app.route('/api/check-model-price', methods=['GET'])(check_model_price)
    
    # Conversation management routes
    app.route('/api/conversations', methods=['GET'])(list_conversations)
    app.route('/api/conversations/<int:conversation_id>', methods=['GET'])(get_conversation)
    app.route('/api/conversations', methods=['POST'])(create_conversation)
    app.route('/api/conversations/<int:conversation_id>', methods=['PUT'])(update_conversation)
    app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])(delete_conversation)
    
    # User preferences routes
    app.route('/api/user-preferences', methods=['GET'])(get_user_preferences)
    app.route('/api/user-preferences', methods=['POST'])(update_user_preferences)
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Resource not found"}), 404
        return render_template('error.html', error=error), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal server error"}), 500
        return render_template('error.html', error=error), 500
    
    # Log that routes have been registered
    logger.info("Application routes registered successfully")