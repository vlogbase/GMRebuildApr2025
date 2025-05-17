"""
Blueprint for handling model fallback confirmation functionality.

This module provides:
1. API endpoint for getting and updating user fallback preferences
2. JavaScript functions for showing the model fallback confirmation dialog
3. Integration with the main app.py file
"""
import os
import logging
from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import current_user, login_required
from models import UserChatSettings, db

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Blueprint
fallback_api = Blueprint('fallback_api', __name__)

@fallback_api.route('/api/user/chat_settings', methods=['POST'])
@login_required
def update_chat_settings():
    """Update user chat settings including auto_fallback_enabled preference"""
    try:
        data = request.json
        user_id = current_user.id
        
        # Get or create user chat settings
        chat_settings = UserChatSettings.query.filter_by(user_id=user_id).first()
        if not chat_settings:
            chat_settings = UserChatSettings(user_id=user_id)
            db.session.add(chat_settings)
        
        # Update auto-fallback setting if provided
        if 'auto_fallback_enabled' in data:
            chat_settings.auto_fallback_enabled = data['auto_fallback_enabled']
            logger.info(f"Updated auto_fallback_enabled to {data['auto_fallback_enabled']} for user {user_id}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat settings updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating chat settings: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@fallback_api.route('/api/user/chat_settings', methods=['GET'])
@login_required
def get_chat_settings():
    """Get current user chat settings"""
    try:
        user_id = current_user.id
        
        # Get user chat settings
        chat_settings = UserChatSettings.query.filter_by(user_id=user_id).first()
        
        if not chat_settings:
            return jsonify({
                'auto_fallback_enabled': False  # Default value
            })
        
        return jsonify({
            'auto_fallback_enabled': chat_settings.auto_fallback_enabled
        })
    except Exception as e:
        logger.error(f"Error getting chat settings: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@fallback_api.route('/model_fallback.js')
def serve_model_fallback_js():
    """Serve the model fallback JavaScript file"""
    return current_app.send_static_file('js/model_fallback.js')

@fallback_api.route('/model_fallback.css')
def serve_model_fallback_css():
    """Serve the model fallback CSS file"""
    return current_app.send_static_file('css/model_fallback.css')

def init_fallback_api(app):
    """Initialize and register the fallback API Blueprint"""
    app.register_blueprint(fallback_api)
    logger.info("Fallback API Blueprint registered")