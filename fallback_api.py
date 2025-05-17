"""
Blueprint for handling model fallback confirmation functionality.
Includes API routes for checking user preferences and handling fallback decisions.
"""
import os
import json
import logging
from flask import Blueprint, request, jsonify, session, current_app
from flask_login import current_user
from models import UserChatSettings
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Blueprint
fallback_api = Blueprint('fallback_api', __name__)

@fallback_api.route('/api/fallback/check_preference', methods=['GET'])
def check_fallback_preference():
    """
    Check if the user has enabled automatic fallback in their preferences.
    
    Returns:
        JSON with auto_fallback setting
    """
    try:
        auto_fallback = False
        
        # Check if user is logged in with preferences
        if current_user and current_user.is_authenticated:
            # Get user's chat settings
            user_settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
            
            if user_settings:
                auto_fallback = user_settings.auto_fallback_enabled
                logger.info(f"User {current_user.id} fallback preference: {auto_fallback}")
            else:
                # Create settings with default (auto_fallback=False)
                user_settings = UserChatSettings(
                    user_id=current_user.id,
                    auto_fallback_enabled=False,
                    session_memory_enabled=True  # Default for memory
                )
                db.session.add(user_settings)
                db.session.commit()
                logger.info(f"Created default fallback preferences for user {current_user.id}")
        
        # Return the preference
        return jsonify({
            'auto_fallback_enabled': auto_fallback
        })
    
    except Exception as e:
        logger.error(f"Error checking fallback preference: {e}")
        return jsonify({
            'error': 'Could not retrieve fallback preference',
            'auto_fallback_enabled': False  # Default to false on error
        }), 500

@fallback_api.route('/api/fallback/update_preference', methods=['POST'])
def update_fallback_preference():
    """
    Update the user's automatic fallback preference.
    
    Request body:
        {
            "auto_fallback_enabled": boolean
        }
    
    Returns:
        JSON with success status
    """
    try:
        # Only allow authenticated users to update preferences
        if not current_user or not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required'
            }), 401
        
        # Get the auto_fallback setting from request
        data = request.json
        auto_fallback_enabled = data.get('auto_fallback_enabled', False)
        
        # Update user's chat settings
        user_settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
        
        if user_settings:
            user_settings.auto_fallback_enabled = auto_fallback_enabled
        else:
            # Create settings if they don't exist
            user_settings = UserChatSettings(
                user_id=current_user.id,
                auto_fallback_enabled=auto_fallback_enabled,
                session_memory_enabled=True  # Default for memory
            )
            db.session.add(user_settings)
        
        db.session.commit()
        logger.info(f"Updated fallback preference for user {current_user.id}: {auto_fallback_enabled}")
        
        return jsonify({
            'success': True,
            'auto_fallback_enabled': auto_fallback_enabled
        })
    
    except Exception as e:
        logger.error(f"Error updating fallback preference: {e}")
        return jsonify({
            'error': 'Could not update fallback preference',
            'success': False
        }), 500

def init_fallback_api(app):
    """
    Register the blueprint with the Flask app.
    
    Args:
        app: The Flask application instance
    """
    app.register_blueprint(fallback_api)
    logger.info("Registered fallback_api blueprint")