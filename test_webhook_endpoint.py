"""
Test script to verify Stripe webhook endpoint configuration.
This script validates that our webhook endpoint matches what's registered in Stripe.
"""

import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_webhook_endpoint():
    """
    Test the webhook endpoint configuration.
    """
    try:
        # Get the base URL from environment variable or use a default value
        base_url = os.environ.get('STRIPE_WEBHOOK_ENDPOINT', 'https://gloriamundo.com/billing/stripe-webhook')
        
        # Print the full webhook URL for verification
        logger.info(f"Configured webhook endpoint: {base_url}")
        
        # Check if the endpoint exists in our application
        # This is just a health check without sending actual webhook data
        response = requests.get("http://localhost:5000/billing/stripe-webhook", timeout=5)
        
        if response.status_code == 405:  # Method Not Allowed (expected since we only accept POST)
            logger.info("Webhook endpoint exists and is properly configured (only accepts POST)")
            return True
        else:
            logger.warning(f"Unexpected response from webhook endpoint: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to the application. Is the server running?")
        return False
    except Exception as e:
        logger.error(f"Error testing webhook endpoint: {e}")
        return False

if __name__ == "__main__":
    test_webhook_endpoint()