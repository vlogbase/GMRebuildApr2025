"""
Test script to check Stripe API key functionality
"""

import os
import stripe
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stripe_api():
    """
    Test if the Stripe API key is working by making a simple API call.
    """
    # Set Stripe API key
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    if not stripe.api_key:
        logger.error("Stripe API key not found")
        return False
    
    try:
        # Make a simple API call - list products
        products = stripe.Product.list(limit=5)
        logger.info(f"Successfully retrieved {len(products.data)} products from Stripe")
        
        # Display some product details
        for product in products.data:
            logger.info(f"Product: {product.id}, Name: {product.name}")
        
        return True
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    if test_stripe_api():
        print("Stripe API test successful!")
    else:
        print("Stripe API test failed. Check logs for details.")