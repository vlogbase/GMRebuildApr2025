"""
PayPal Configuration Module

This module provides centralized configuration for PayPal API integration.
"""

import logging
import os
from typing import Optional, Dict, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import PayPal SDK
try:
    import paypalrestsdk
    PAYPAL_SDK_AVAILABLE = True
    logger.info("PayPal REST SDK successfully imported")
except ImportError:
    logger.warning("PayPal REST SDK not available. PayPal features will be disabled.")
    PAYPAL_SDK_AVAILABLE = False

# Global client instance flag
_paypal_initialized = False

def initialize_paypal():
    """Initialize PayPal SDK with credentials from environment variables"""
    global _paypal_initialized
    
    if not PAYPAL_SDK_AVAILABLE:
        logger.error("PayPal SDK is not available. Cannot initialize.")
        return False
    
    try:
        # Get environment variables
        client_id = os.environ.get("PAYPAL_CLIENT_ID")
        client_secret = os.environ.get("PAYPAL_CLIENT_SECRET")
        mode = os.environ.get("PAYPAL_MODE", "sandbox")  # Default to sandbox
        
        if not client_id or not client_secret:
            logger.error("PayPal credentials are missing. Please check environment variables.")
            return False
        
        # Configure the SDK
        paypalrestsdk.configure({
            "mode": mode,
            "client_id": client_id,
            "client_secret": client_secret
        })
        
        _paypal_initialized = True
        logger.info(f"PayPal configured for {mode.upper()} environment")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing PayPal: {e}")
        return False

def is_paypal_initialized():
    """Check if PayPal has been initialized"""
    return PAYPAL_SDK_AVAILABLE and _paypal_initialized

def create_payout(sender_batch_id, email_subject, email_message, items):
    """
    Create a PayPal payout
    
    Args:
        sender_batch_id (str): Unique ID for the batch
        email_subject (str): Subject of email sent to recipients
        email_message (str): Email message sent to recipients
        items (list): List of payout items (dict with 'recipient_type', 'amount', 'receiver', 'note')
    
    Returns:
        dict: Result of the payout operation
    """
    if not is_paypal_initialized():
        return {
            'success': False, 
            'error': 'PayPal not initialized'
        }
    
    try:
        payout = paypalrestsdk.Payout({
            "sender_batch_header": {
                "sender_batch_id": sender_batch_id,
                "email_subject": email_subject,
                "email_message": email_message
            },
            "items": items
        })
        
        if payout.create():
            logger.info(f"Payout created with batch ID: {payout.batch_header.payout_batch_id}")
            return {
                'success': True,
                'batch_id': payout.batch_header.payout_batch_id,
                'batch_status': payout.batch_header.batch_status
            }
        else:
            logger.error(f"Failed to create payout: {payout.error}")
            return {
                'success': False,
                'error': payout.error
            }
    except Exception as e:
        logger.error(f"Error creating payout: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_payout_details(payout_batch_id):
    """
    Get details of a payout batch
    
    Args:
        payout_batch_id (str): PayPal payout batch ID
    
    Returns:
        dict: Payout batch status and details
    """
    if not is_paypal_initialized():
        return {
            'success': False, 
            'error': 'PayPal not initialized'
        }
    
    try:
        payout = paypalrestsdk.Payout.find(payout_batch_id)
        
        if payout:
            return {
                'success': True,
                'batch_id': payout_batch_id,
                'batch_status': payout.batch_header.batch_status,
                'items': payout.items
            }
        else:
            return {
                'success': False,
                'error': 'Payout not found'
            }
    except Exception as e:
        logger.error(f"Error getting payout details: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_paypal_environment_details() -> Dict[str, Any]:
    """Get PayPal environment details for debugging"""
    try:
        mode = os.environ.get("PAYPAL_MODE", "sandbox")
        client_id = os.environ.get("PAYPAL_CLIENT_ID", "")
        client_secret_masked = "Available" if os.environ.get("PAYPAL_CLIENT_SECRET") else "Missing"
        
        return {
            "mode": mode,
            "client_id": client_id[:5] + "..." if client_id else "Missing",
            "client_secret": client_secret_masked,
            "sdk_available": PAYPAL_SDK_AVAILABLE,
            "initialized": _paypal_initialized
        }
    except Exception as e:
        logger.error(f"Error getting PayPal environment details: {e}")
        return {
            "error": str(e)
        }