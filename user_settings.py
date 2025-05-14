"""
User Settings Module for GloriaMundo Chatbot

This module handles user settings management, including saving and loading 
advanced chat parameters like temperature, top_p, etc.
"""

import logging
import json
from flask import Blueprint, jsonify, request, current_app, g
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app import db
from models import UserChatSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
user_settings_bp = Blueprint('user_settings', __name__, url_prefix='/api/user')

@user_settings_bp.route('/chat_settings', methods=['GET'])
@login_required
def get_chat_settings():
    """Get the user's chat settings"""
    try:
        # Get the user's chat settings
        settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
        
        if settings:
            # Return existing settings
            return jsonify({
                'success': True,
                'settings': {
                    'temperature': settings.temperature,
                    'top_p': settings.top_p,
                    'max_tokens': settings.max_tokens,
                    'frequency_penalty': settings.frequency_penalty,
                    'presence_penalty': settings.presence_penalty,
                    'top_k': settings.top_k,
                    'stop_sequences': settings.stop_sequences,
                    'response_format': settings.response_format
                }
            })
        else:
            # Return empty settings (all defaults)
            return jsonify({
                'success': True,
                'settings': {
                    'temperature': None,
                    'top_p': None,
                    'max_tokens': None,
                    'frequency_penalty': None,
                    'presence_penalty': None,
                    'top_k': None,
                    'stop_sequences': None,
                    'response_format': None
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting chat settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_settings_bp.route('/chat_settings', methods=['POST'])
@login_required
def save_chat_settings():
    """Save the user's chat settings"""
    try:
        # Get the settings from the request
        data = request.json
        
        # Validate inputs
        temperature = data.get('temperature')
        if temperature is not None:
            try:
                temperature = float(temperature)
                if temperature < 0 or temperature > 2:
                    return jsonify({
                        'success': False,
                        'error': 'Temperature must be between 0 and 2'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Temperature must be a number'
                }), 400
        
        top_p = data.get('top_p')
        if top_p is not None:
            try:
                top_p = float(top_p)
                if top_p < 0 or top_p > 1:
                    return jsonify({
                        'success': False,
                        'error': 'Top P must be between 0 and 1'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Top P must be a number'
                }), 400
        
        max_tokens = data.get('max_tokens')
        if max_tokens is not None:
            try:
                max_tokens = int(max_tokens)
                if max_tokens < 1 or max_tokens > 8000:
                    return jsonify({
                        'success': False,
                        'error': 'Max Tokens must be between 1 and 8000'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Max Tokens must be an integer'
                }), 400
        
        frequency_penalty = data.get('frequency_penalty')
        if frequency_penalty is not None:
            try:
                frequency_penalty = float(frequency_penalty)
                if frequency_penalty < -2 or frequency_penalty > 2:
                    return jsonify({
                        'success': False,
                        'error': 'Frequency Penalty must be between -2 and 2'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Frequency Penalty must be a number'
                }), 400
        
        presence_penalty = data.get('presence_penalty')
        if presence_penalty is not None:
            try:
                presence_penalty = float(presence_penalty)
                if presence_penalty < -2 or presence_penalty > 2:
                    return jsonify({
                        'success': False,
                        'error': 'Presence Penalty must be between -2 and 2'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Presence Penalty must be a number'
                }), 400
        
        top_k = data.get('top_k')
        if top_k is not None:
            try:
                top_k = int(top_k)
                if top_k < 0 or top_k > 100:
                    return jsonify({
                        'success': False,
                        'error': 'Top K must be between 0 and 100'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Top K must be an integer'
                }), 400
        
        stop_sequences = data.get('stop_sequences')
        if stop_sequences is not None:
            try:
                # Validate JSON
                json.loads(stop_sequences)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Stop Sequences must be valid JSON'
                }), 400
        
        response_format = data.get('response_format')
        if response_format is not None and response_format not in ['text', 'json']:
            return jsonify({
                'success': False,
                'error': 'Response Format must be either "text" or "json"'
            }), 400
        
        # Get existing settings or create new ones
        settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
        
        if not settings:
            # Create new settings
            settings = UserChatSettings(user_id=current_user.id)
            db.session.add(settings)
        
        # Update settings with new values
        settings.temperature = temperature
        settings.top_p = top_p
        settings.max_tokens = max_tokens
        settings.frequency_penalty = frequency_penalty
        settings.presence_penalty = presence_penalty
        settings.top_k = top_k
        settings.stop_sequences = stop_sequences
        settings.response_format = response_format
        
        # Save to database
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat settings saved successfully'
        })
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error saving chat settings: {e}")
        return jsonify({
            'success': False,
            'error': f"Database error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error saving chat settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def init_user_settings(app):
    """Register the user settings blueprint with the app"""
    app.register_blueprint(user_settings_bp)


def get_chat_settings_for_user(user_id):
    """Get chat settings for a specific user (utility function for other modules)"""
    settings = UserChatSettings.query.filter_by(user_id=user_id).first()
    
    if settings:
        return settings.to_dict()
    
    return {}  # Return empty dict if no settings found (use defaults)


def validate_model_specific_parameters(settings_dict, model_id):
    """
    Validate and adjust parameters based on model-specific constraints.
    This function modifies the settings_dict in place.
    
    Args:
        settings_dict (dict): The user's chat settings
        model_id (str): The OpenRouter model ID
        
    Returns:
        dict: The validated settings dictionary
    """
    from models import OpenRouterModel
    
    # If max_tokens is set, ensure it doesn't exceed the model's context length
    if 'max_tokens' in settings_dict and settings_dict['max_tokens'] is not None:
        model = OpenRouterModel.query.filter_by(model_id=model_id).first()
        
        if model and model.context_length:
            # Cap max_tokens at model's context length
            settings_dict['max_tokens'] = min(settings_dict['max_tokens'], model.context_length)
    
    return settings_dict