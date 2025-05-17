"""
User-related utility functions for GloriaMundo Chatbot

This module provides functions for working with user settings and chat preferences
that can be imported by other modules.
"""

import logging
from models import UserChatSettings
from database import db

# Configure logging
logger = logging.getLogger(__name__)

def get_user_chat_settings(user_id=None):
    """
    Get chat settings for a specific user or default settings if user is anonymous.
    
    Args:
        user_id: ID of the user or None for anonymous
        
    Returns:
        Dictionary of chat settings with defaults
    """
    default_settings = {
        'temperature': 0.7,
        'top_p': 0.9,
        'max_tokens': 4000,
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0,
        'top_k': 40,
        'stop_sequences': None,
        'response_format': 'text',
        'auto_fallback_enabled': False
    }
    
    if not user_id:
        return default_settings
    
    try:
        # Get settings from database
        settings = UserChatSettings.query.filter_by(user_id=user_id).first()
        
        if not settings:
            return default_settings
            
        # Convert to dictionary
        settings_dict = {
            'temperature': settings.temperature if settings.temperature is not None else default_settings['temperature'],
            'top_p': settings.top_p if settings.top_p is not None else default_settings['top_p'],
            'max_tokens': settings.max_tokens if settings.max_tokens is not None else default_settings['max_tokens'],
            'frequency_penalty': settings.frequency_penalty if settings.frequency_penalty is not None else default_settings['frequency_penalty'],
            'presence_penalty': settings.presence_penalty if settings.presence_penalty is not None else default_settings['presence_penalty'],
            'top_k': settings.top_k if settings.top_k is not None else default_settings['top_k'],
            'stop_sequences': settings.stop_sequences if settings.stop_sequences is not None else default_settings['stop_sequences'],
            'response_format': settings.response_format if settings.response_format is not None else default_settings['response_format'],
            'auto_fallback_enabled': settings.auto_fallback_enabled
        }
        
        return settings_dict
    except Exception as e:
        logger.exception(f"Error getting user chat settings: {e}")
        return default_settings

def save_user_settings(user_id, settings_dict):
    """
    Save chat settings for a specific user.
    
    Args:
        user_id: ID of the user
        settings_dict: Dictionary of settings to save
        
    Returns:
        True if successful, False otherwise
    """
    if not user_id:
        return False
        
    try:
        # Get existing settings or create new
        settings = UserChatSettings.query.filter_by(user_id=user_id).first()
        
        if not settings:
            settings = UserChatSettings(user_id=user_id)
            db.session.add(settings)
        
        # Update settings
        if 'temperature' in settings_dict:
            settings.temperature = settings_dict['temperature']
        
        if 'top_p' in settings_dict:
            settings.top_p = settings_dict['top_p']
            
        if 'max_tokens' in settings_dict:
            settings.max_tokens = settings_dict['max_tokens']
            
        if 'frequency_penalty' in settings_dict:
            settings.frequency_penalty = settings_dict['frequency_penalty']
            
        if 'presence_penalty' in settings_dict:
            settings.presence_penalty = settings_dict['presence_penalty']
            
        if 'top_k' in settings_dict:
            settings.top_k = settings_dict['top_k']
            
        if 'stop_sequences' in settings_dict:
            settings.stop_sequences = settings_dict['stop_sequences']
            
        if 'response_format' in settings_dict:
            settings.response_format = settings_dict['response_format']
            
        if 'auto_fallback_enabled' in settings_dict:
            settings.auto_fallback_enabled = settings_dict['auto_fallback_enabled']
        
        # Save changes
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error saving user settings: {e}")
        return False