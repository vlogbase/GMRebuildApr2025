"""
Test Flask application for Stripe integration.
This simple Flask app demonstrates the Stripe Checkout integration.
"""

import os
import json
import logging
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify
import stripe

# Define Jinja2 filter for datetime formatting
def datetime_filter(timestamp):
    """Convert timestamp to readable datetime."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_secret_key'
app.debug = True

# Register Jinja2 filter
app.jinja_env.filters['datetime'] = datetime_filter

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

@app.route('/')
def index():
    """Home page with package selection."""
    # Get test prices
    try:
        prices = stripe.Price.list(
            limit=10,
            active=True,
        )
        return render_template('test_checkout.html', prices=prices.data)
    except Exception as e:
        logger.error(f"Error getting prices: {e}")
        return f"Error getting prices: {e}", 500

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe Checkout Session."""
    try:
        price_id = request.form.get('price_id')
        
        if not price_id:
            return "Price ID is required", 400
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'cancel',
            client_reference_id='test_user_123',
        )
        
        return redirect(checkout_session.url, code=303)
    
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return f"Error creating checkout session: {e}", 500

@app.route('/success')
def success():
    """Success page after successful payment."""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return "Session ID is required", 400
        
        # Retrieve checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        return render_template('test_success.html', session=checkout_session)
    
    except Exception as e:
        logger.error(f"Error retrieving session: {e}")
        return f"Error retrieving session: {e}", 500

@app.route('/cancel')
def cancel():
    """Cancel page after cancelled payment."""
    return render_template('test_cancel.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    """Stripe webhook endpoint."""
    try:
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        if not webhook_secret:
            logger.warning("Webhook secret not set, skipping signature verification")
            event = json.loads(payload)
        else:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Signature verification failed: {e}")
                return "Signature verification failed", 400
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            logger.info("Checkout session completed")
            session = event['data']['object']
            
            # Process the payment
            logger.info(f"Payment successful for session {session['id']}")
            logger.info(f"User ID: {session['client_reference_id']}")
            logger.info(f"Amount paid: {session['amount_total'] / 100:.2f} {session['currency'].upper()}")
        
        return jsonify(success=True)
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return f"Error processing webhook: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)