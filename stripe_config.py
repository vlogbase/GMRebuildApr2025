"""
Stripe Configuration Module for GloriaMundo Chatbot

This module contains Stripe configuration and helper functions.
"""

import os
import logging
import json
import stripe
from datetime import datetime

from flask import current_app, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_stripe():
    """
    Initialize Stripe with API keys.
    """
    try:
        # Set Stripe API key
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        if not stripe.api_key:
            logger.error("Stripe API key not found")
            return False
        
        logger.info("Stripe initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing Stripe: {e}")
        return False

def create_checkout_session(price_id, user_id, success_url, cancel_url, is_first_purchase=False):
    """
    Create a Stripe Checkout Session with automatic tax calculation.
    
    This function enables Stripe Tax for automatic tax calculation, including support for 
    UK VAT and B2B reverse charge. It requires the customer's billing address and 
    allows businesses to provide their tax ID (VAT number) during checkout.
    
    Args:
        price_id (str): Stripe Price ID
        user_id (int): User ID
        success_url (str): URL to redirect after success
        cancel_url (str): URL to redirect after cancellation
        is_first_purchase (bool): Whether this is the user's first purchase
        
    Returns:
        dict: Dictionary with checkout result
    """
    try:
        # Create Checkout Session
        checkout_params = {
            'payment_method_types': ['card'],
            'line_items': [
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            'mode': 'payment',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'client_reference_id': str(user_id),
            'allow_promotion_codes': True,
            'automatic_tax': {'enabled': True},
            'billing_address_collection': 'required',
            'tax_id_collection': {'enabled': True},
        }
        
        # Add metadata for first-time purchases
        if is_first_purchase:
            checkout_params['metadata'] = {
                'is_first_purchase': 'true'
            }
        
        session = stripe.checkout.Session.create(**checkout_params)
        
        return {
            'success': True,
            'session_id': session.id,
            'checkout_url': session.url
        }
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def verify_webhook_signature(payload, sig_header, webhook_secret):
    """
    Verify the Stripe webhook signature.
    
    Args:
        payload (bytes): Request payload
        sig_header (str): Stripe-Signature header
        webhook_secret (str): Webhook secret
        
    Returns:
        dict: Dictionary with verification result
    """
    try:
        # Verify signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        
        return {
            'success': True,
            'event': event
        }
    
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Signature verification failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def retrieve_session(session_id):
    """
    Retrieve a Stripe Checkout Session.
    
    Args:
        session_id (str): Stripe Checkout Session ID
        
    Returns:
        dict: Dictionary with session data
    """
    try:
        # Retrieve session
        session = stripe.checkout.Session.retrieve(session_id)
        
        return {
            'success': True,
            'session': session
        }
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    
    except Exception as e:
        logger.error(f"Error retrieving session: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# Initialize Stripe when the module is imported
initialize_stripe()