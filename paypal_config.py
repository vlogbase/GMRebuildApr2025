"""
PayPal Payouts API Configuration for GloriaMundo Affiliate System

This module contains the PayPal Payouts SDK configuration and helper functions
for processing affiliate payouts using the PayPal Payouts API.
"""

import os
import logging
import uuid
from datetime import datetime

# Import the correct PayPal Payouts SDK components
from paypalhttp import Environment
from paypalpayoutssdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalpayoutssdk.payouts import PayoutsPostRequest, PayoutsGetRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PayPal API credentials from environment variables
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'

# Initialize the PayPal client
def get_paypal_client():
    """
    Initialize and return the PayPal HTTP client with appropriate environment.
    
    Returns:
        PayPalHttpClient: Initialized PayPal client
    """
    try:
        if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
            logger.error("PayPal API credentials are missing")
            return None
            
        # Create the appropriate environment
        if PAYPAL_MODE.lower() == 'live':
            environment = LiveEnvironment(
                client_id=PAYPAL_CLIENT_ID,
                client_secret=PAYPAL_CLIENT_SECRET
            )
        else:
            environment = SandboxEnvironment(
                client_id=PAYPAL_CLIENT_ID,
                client_secret=PAYPAL_CLIENT_SECRET
            )
            
        # Create the PayPal client
        client = PayPalHttpClient(environment)
        logger.info(f"PayPal Payouts SDK client initialized successfully in {PAYPAL_MODE} mode")
        return client
        
    except Exception as e:
        logger.error(f"Error initializing PayPal client: {e}")
        return None

def process_paypal_payout(sender_batch_id, payout_items):
    """
    Process a PayPal payout batch using the PayPal Payouts SDK.
    
    Args:
        sender_batch_id (str): Unique identifier for the batch
        payout_items (list): List of dicts with payout details:
            [
                {
                    'recipient_email': 'affiliate@example.com',
                    'amount': 12.34,
                    'currency': 'GBP',
                    'sender_item_id': '123'
                },
                ...
            ]
    
    Returns:
        dict: Status and details of the payout
    """
    try:
        # Get the PayPal client
        client = get_paypal_client()
        if not client:
            return {
                'success': False,
                'error': 'PayPal client initialization failed'
            }
            
        # Create the payout request
        payout_request = PayoutsPostRequest()
        
        # Prepare the request body with sender batch header and items
        payout_request.request_body({
            "sender_batch_header": {
                "sender_batch_id": sender_batch_id,
                "email_subject": "You have received a commission payment",
                "email_message": "Thank you for being an affiliate. This payment is for your commissions."
            },
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": str(item['amount']),
                        "currency": item['currency']
                    },
                    "note": "Thank you for your partnership with GloriaMundo",
                    "sender_item_id": item['sender_item_id'],
                    "receiver": item['recipient_email']
                } for item in payout_items
            ]
        })
        
        # Execute the payout
        response = client.execute(payout_request)
        
        # Process the response
        result = response.result
        
        return {
            'success': True,
            'payout_batch_id': result.batch_header.payout_batch_id,
            'batch_status': result.batch_header.batch_status,
            'links': [{'href': link.href, 'rel': link.rel} for link in result.links]
        }
        
    except Exception as e:
        logger.error(f"Error processing PayPal payout: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def check_payout_status(payout_batch_id):
    """
    Check the status of a PayPal payout batch.
    
    Args:
        payout_batch_id (str): PayPal payout batch ID
    
    Returns:
        dict: Status and details of the payout
    """
    try:
        # Get the PayPal client
        client = get_paypal_client()
        if not client:
            return {
                'success': False,
                'error': 'PayPal client initialization failed'
            }
            
        # Create the PayoutsGetRequest
        request = PayoutsGetRequest(payout_batch_id)
        
        # Execute the request
        response = client.execute(request)
        result = response.result
        
        # Parse the items to extract individual payout statuses
        items_status = []
        for item in result.items:
            item_status = {
                'payout_item_id': item.payout_item_id,
                'transaction_id': getattr(item, 'transaction_id', None),
                'transaction_status': getattr(item, 'transaction_status', None),
                'sender_item_id': item.sender_item_id
            }
            
            # Add receiver if available
            if hasattr(item, 'payout_item') and hasattr(item.payout_item, 'receiver'):
                item_status['receiver'] = item.payout_item.receiver
            
            # Add amount if available
            if hasattr(item, 'payout_item') and hasattr(item.payout_item, 'amount'):
                item_status['amount'] = {
                    'currency': item.payout_item.amount.currency,
                    'value': item.payout_item.amount.value
                }
            
            # Add errors if present
            if hasattr(item, 'errors') and item.errors:
                item_status['error'] = item.errors
                
            items_status.append(item_status)
            
        return {
            'success': True,
            'batch_header': {
                'payout_batch_id': result.batch_header.payout_batch_id,
                'batch_status': result.batch_header.batch_status,
                'time_created': result.batch_header.time_created,
                'time_completed': getattr(result.batch_header, 'time_completed', None)
            },
            'items': items_status
        }
        
    except Exception as e:
        logger.error(f"Error checking PayPal payout status: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_sender_batch_id():
    """
    Generate a unique sender batch ID for PayPal payouts.
    
    Returns:
        str: Unique sender batch ID
    """
    return f"GloriaMundoPayout-{uuid.uuid4()}"