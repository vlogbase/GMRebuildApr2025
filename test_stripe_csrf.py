"""
Test script to verify CSRF protection and Stripe integration
"""
import os
import sys
import logging
from flask import Flask, render_template, request, session
from flask_wtf.csrf import CSRFProtect
import stripe

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a minimal Flask app for testing
app = Flask(__name__)
app.secret_key = 'test-secret-key'
csrf = CSRFProtect(app)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
if not stripe.api_key:
    logger.error("STRIPE_SECRET_KEY environment variable not set")
    sys.exit(1)

@app.route('/')
def test_page():
    """Test page with a form that includes CSRF token"""
    return render_template('csrf_test.html')

@app.route('/test-checkout', methods=['POST'])
def test_checkout():
    """Test route for Stripe checkout"""
    if not request.form.get('csrf_token'):
        return "CSRF token missing", 400
    
    try:
        # Create a simple Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': 'price_1RKOl0CkgfcNKUGFhI5RljJd',  # Use the Starter Pack price ID
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + 'success.html',
            cancel_url=request.host_url + 'cancel.html',
        )
        logger.info(f"Created checkout session: {checkout_session.id}")
        return f"Checkout session created: {checkout_session.id}"
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return f"Error: {str(e)}", 500

def run_tests():
    """Run a series of tests to verify CSRF protection and Stripe integration"""
    logger.info("Starting tests...")
    
    # Test 1: Check CSRF protection
    logger.info("Test 1: Checking CSRF protection")
    with app.test_client() as client:
        # First, get a CSRF token
        response = client.get('/')
        assert response.status_code == 200, "Failed to load test page"
        
        # Try without CSRF token - should fail
        response = client.post('/test-checkout', data={})
        assert response.status_code == 400, "CSRF protection not working - request without token should be rejected"
        logger.info("✓ CSRF protection is working")
    
    # Test 2: Check Stripe API key
    logger.info("Test 2: Checking Stripe API key")
    try:
        # Perform a simple API operation to validate the key
        stripe.Customer.list(limit=1)
        logger.info("✓ Stripe API key is valid")
    except stripe.error.AuthenticationError:
        logger.error("✗ Stripe API key is invalid")
        sys.exit(1)
    
    # Test 3: Check price ID exists
    logger.info("Test 3: Checking Stripe Price ID")
    try:
        price = stripe.Price.retrieve('price_1RKOl0CkgfcNKUGFhI5RljJd')
        logger.info(f"✓ Price ID is valid: {price.product} - ${price.unit_amount/100}")
    except stripe.error.InvalidRequestError:
        logger.error("✗ Test price ID does not exist")
        sys.exit(1)
    
    logger.info("All tests passed!")
    return True

if __name__ == '__main__':
    # Run tests
    success = run_tests()
    if success:
        logger.info("CSRF and Stripe setup verified successfully!")
    else:
        logger.error("Tests failed")
        sys.exit(1)