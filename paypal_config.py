"""
PayPal Configuration Module

This module provides centralized configuration for PayPal API integration.
"""

import os
import logging
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest
from paypal.payouts import PayoutsPostRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client variable
paypal_client = None

def get_paypal_client():
    """Get or create PayPal client instance"""
    global paypal_client
    
    if paypal_client is not None:
        return paypal_client
    
    # Initialize client
    initialize_paypal()
    return paypal_client

def initialize_paypal():
    """Initialize PayPal SDK with credentials from environment variables"""
    global paypal_client
    
    try:
        # Get PayPal API credentials
        client_id = os.environ.get('PAYPAL_CLIENT_ID')
        client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
        mode = os.environ.get('PAYPAL_MODE', 'sandbox')  # Default to sandbox if not specified
        
        if not client_id or not client_secret:
            logger.error("PayPal API credentials missing")
            return False
        
        # Create environment based on mode
        if mode.lower() == 'live':
            environment = LiveEnvironment(client_id=client_id, client_secret=client_secret)
            logger.info("Using PayPal LIVE environment")
        else:
            environment = SandboxEnvironment(client_id=client_id, client_secret=client_secret)
            logger.info("Using PayPal SANDBOX environment")
        
        # Create client
        paypal_client = PayPalHttpClient(environment)
        
        logger.info(f"PayPal SDK initialized (mode: {mode})")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing PayPal SDK: {e}")
        return False

# Initialize PayPal when module is imported
initialize_paypal()