"""
Test script to verify that the Stripe webhook endpoint is exempt from CSRF protection
"""
import os
import sys
import logging
import requests
from flask import Flask, request, jsonify
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_webhook_exemption():
    """Test that the webhook endpoint is exempt from CSRF protection"""
    # Start a separate Python process to run the server
    logger.info("Testing webhook CSRF exemption...")
    
    # Get the webhook URL
    base_url = "http://localhost:5000"
    webhook_url = f"{base_url}/billing/webhook"
    
    # Create a simple test payload
    test_payload = {"type": "test_event", "data": {"object": "test"}}
    
    # Create a header similar to what Stripe would send
    headers = {
        "Content-Type": "application/json",
        "Stripe-Signature": "test_signature"
    }
    
    try:
        # Send a POST request to the webhook endpoint without a CSRF token
        logger.info(f"Sending POST request to {webhook_url}")
        response = requests.post(webhook_url, json=test_payload, headers=headers)
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response text: {response.text[:100]}...")
        
        # Check if we got a response that's not a 400 CSRF error
        # Note: We expect a 400 for invalid signature, but not for CSRF
        if "CSRF" in response.text:
            logger.error("❌ Webhook is still protected by CSRF!")
            return False
        else:
            logger.info("✅ Webhook is exempt from CSRF protection")
            return True
            
    except Exception as e:
        logger.error(f"Error testing webhook: {e}")
        return False

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000")
        if response.status_code != 200:
            logger.error("Server is not running properly. Please start it first.")
            sys.exit(1)
    except Exception:
        logger.error("Server is not running. Please start it first.")
        sys.exit(1)
        
    # Run the test
    success = test_webhook_exemption()
    if success:
        logger.info("Webhook CSRF exemption verified successfully!")
        sys.exit(0)
    else:
        logger.error("Webhook CSRF exemption test failed")
        sys.exit(1)