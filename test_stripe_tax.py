"""
Test script to verify Stripe automatic tax collection is configured correctly
"""
import os
import sys
import logging
import stripe

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
if not stripe.api_key:
    logger.error("STRIPE_SECRET_KEY environment variable not set")
    sys.exit(1)

def test_checkout_session_tax_config():
    """Test if a checkout session includes automatic tax configuration"""
    try:
        # Create a test checkout session with automatic tax
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': 'price_1RKOl0CkgfcNKUGFhI5RljJd',  # Use the Starter Pack price ID
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            automatic_tax={'enabled': True},
            billing_address_collection='required',
            tax_id_collection={'enabled': True},
        )
        
        logger.info(f"Created checkout session: {checkout_session.id}")
        
        # Retrieve the session to verify configurations
        session = stripe.checkout.Session.retrieve(checkout_session.id)
        
        # Check if automatic tax is enabled
        if session.automatic_tax.enabled:
            logger.info("✓ Automatic tax is enabled")
        else:
            logger.error("✗ Automatic tax is not enabled")
            return False
        
        # Check if billing address collection is required
        if session.billing_address_collection == 'required':
            logger.info("✓ Billing address collection is required")
        else:
            logger.error(f"✗ Billing address collection is not required: {session.billing_address_collection}")
            return False
        
        # Check if tax ID collection is enabled
        if session.tax_id_collection.enabled:
            logger.info("✓ Tax ID collection is enabled")
        else:
            logger.error("✗ Tax ID collection is not enabled")
            return False
        
        logger.info("All tax configuration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating or testing checkout session: {e}")
        return False
        
def run_tests():
    """Run all tests to verify Stripe tax configuration"""
    logger.info("Starting automatic tax configuration tests...")
    
    # Test automatic tax configuration
    if not test_checkout_session_tax_config():
        logger.error("Automatic tax configuration test failed")
        return False
        
    logger.info("All Stripe tax configuration tests passed successfully!")
    return True

if __name__ == '__main__':
    # Run tests
    success = run_tests()
    if success:
        logger.info("Stripe automatic tax collection is configured correctly!")
        sys.exit(0)
    else:
        logger.error("Stripe automatic tax tests failed")
        sys.exit(1)