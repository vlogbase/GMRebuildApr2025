"""
Test script to check Stripe checkout session creation
"""

import os
import logging
from stripe_config import initialize_stripe, create_checkout_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_checkout_session():
    """
    Test creating a Stripe checkout session
    """
    try:
        # Initialize Stripe
        if not initialize_stripe():
            logger.error("Failed to initialize Stripe")
            return False
        
        # Test price ID for $5 package found in the previous API call
        test_price_id = 'price_1RKOl0CkgfcNKUGFhI5RljJd'  # Using starter pack price ID
        test_user_id = 1
        success_url = 'https://example.com/success?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = 'https://example.com/cancel'
        
        # Create checkout session
        result = create_checkout_session(
            price_id=test_price_id,
            user_id=test_user_id,
            success_url=success_url,
            cancel_url=cancel_url,
            is_first_purchase=True
        )
        
        if result['success']:
            logger.info(f"Checkout session created successfully. Session ID: {result['session_id']}")
            logger.info(f"Checkout URL: {result['checkout_url']}")
            return True
        else:
            logger.error(f"Failed to create checkout session: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    if test_checkout_session():
        print("Checkout session test successful!")
    else:
        print("Checkout session test failed. Check logs for details.")