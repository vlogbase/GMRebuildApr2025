"""
Authentication utilities for GloriaMundo Chatbot

This module provides authentication and authorization utility functions.
"""

import os
import logging
from flask_login import current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_admin():
    """
    Check if the current user is an admin
    
    This function performs the following checks:
    1. Verifies the user is authenticated
    2. Checks if the user's email is in the ADMIN_EMAILS environment variable
    3. For development, automatically grants admin access to andy@sentigral.com
    
    Returns:
        bool: True if the user is an admin, False otherwise
    """
    # Get logger for detailed diagnostics
    logger = logging.getLogger('affiliate')
    
    # Get admin emails from environment
    admin_emails_str = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com')  # Default admin email
    admin_emails = [email.strip() for email in admin_emails_str.split(',')] if admin_emails_str else []
    
    # Log the configuration
    logger.info(f"Admin check - Admin emails configured: {admin_emails}")
    
    # Check authentication status
    if not hasattr(current_user, 'is_authenticated'):
        logger.error("Admin check - current_user object doesn't have is_authenticated attribute")
        return False
        
    auth_status = current_user.is_authenticated
    if not auth_status:
        logger.info("Admin check - User is not authenticated")
        return False
    
    # Get user email (authenticated users should have this)
    if not hasattr(current_user, 'email'):
        logger.error("Admin check - authenticated user doesn't have email attribute")
        return False
        
    user_email = current_user.email
    
    # Check if user email is in admin list
    is_admin_status = user_email in admin_emails
    
    # Enhanced debug logging
    logger.info(f"Admin check - Current user: {user_email}")
    logger.info(f"Admin check - Is authenticated: {auth_status}")
    logger.info(f"Admin check - Is admin: {is_admin_status}")
    
    # Development fallback for debugging
    if os.environ.get('FLASK_ENV') == 'development' and user_email == 'andy@sentigral.com':
        logger.info("Development mode: Forcing admin access for andy@sentigral.com")
        return True
    
    # Strict admin check
    return is_admin_status