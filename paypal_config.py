"""
PayPal Configuration Module

This module provides centralized configuration for PayPal API integration.
"""

import os
import logging
import paypalrestsdk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_paypal():
    """Initialize PayPal SDK with credentials from environment variables"""
    try:
        # Get PayPal API credentials
        client_id = os.environ.get('PAYPAL_CLIENT_ID')
        client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
        mode = os.environ.get('PAYPAL_MODE', 'sandbox')  # Default to sandbox if not specified
        
        if not client_id or not client_secret:
            logger.error("PayPal API credentials missing")
            return False
        
        # Configure SDK
        paypalrestsdk.configure({
            "mode": mode,
            "client_id": client_id,
            "client_secret": client_secret
        })
        
        logger.info(f"PayPal SDK initialized (mode: {mode})")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing PayPal SDK: {e}")
        return False

# Initialize PayPal when module is imported
initialize_paypal()