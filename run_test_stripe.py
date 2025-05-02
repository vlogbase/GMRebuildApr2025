"""
Run script for the test Stripe app.
This script sets up a Flask server to test the Stripe integration.
"""

import os
import sys
import logging
from test_stripe_app import app

if __name__ == "__main__":
    # Check for Stripe API key
    if not os.environ.get('STRIPE_SECRET_KEY'):
        print("ERROR: Stripe API key not found in environment variables")
        print("Please set the STRIPE_SECRET_KEY environment variable")
        sys.exit(1)
    
    # Run the app
    print("Starting test Stripe app...")
    print("Open http://127.0.0.1:5000 in your browser to test the integration")
    app.run(host='0.0.0.0', port=5000, debug=True)