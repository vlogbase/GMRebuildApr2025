"""
Test script for the billing system.

This script will verify the functioning of the PayPal sandbox integration and credit calculations.
"""

import os
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Make sure the app directory is in the path
sys.path.append(os.getcwd())

# Import the required modules
from app import app, db
from models import User, Transaction, Usage, Package, PaymentStatus
from billing import calculate_openrouter_credits, calculate_embedding_credits
from paypal_config import initialize_paypal, create_payment, get_payment_details

def test_credits_calculation():
    """Test credit calculation for various models and token counts"""
    logger.info("Testing credit calculations...")
    
    # Test OpenRouter credit calculation
    test_cases = [
        {"model": "GPT-4", "prompt_tokens": 1000, "completion_tokens": 500, "model_cost_per_million": 60.0},
        {"model": "Claude-3-Opus", "prompt_tokens": 1000, "completion_tokens": 500, "model_cost_per_million": 45.0},
        {"model": "Claude-3-Sonnet", "prompt_tokens": 1000, "completion_tokens": 500, "model_cost_per_million": 15.0},
        {"model": "Gemini-1.5-Pro", "prompt_tokens": 1000, "completion_tokens": 500, "model_cost_per_million": 10.0},
        {"model": "GPT-3.5", "prompt_tokens": 1000, "completion_tokens": 500, "model_cost_per_million": 1.0},
    ]
    
    for test_case in test_cases:
        model = test_case["model"]
        prompt_tokens = test_case["prompt_tokens"]
        completion_tokens = test_case["completion_tokens"]
        model_cost_per_million = test_case["model_cost_per_million"]
        
        credits = calculate_openrouter_credits(prompt_tokens, completion_tokens, model_cost_per_million)
        
        # Calculate expected credits:
        # Cost per token = model_cost_per_million / 1,000,000
        # Total cost = (prompt_tokens * cost per token) + (completion_tokens * cost per token)
        # Total cost with markup = total cost * 2
        # Credits = total cost with markup * 1,000,000 (1 credit = $0.001)
        expected_cost_per_token = model_cost_per_million / 1000000
        expected_total_cost = (prompt_tokens * expected_cost_per_token) + (completion_tokens * expected_cost_per_token)
        expected_cost_with_markup = expected_total_cost * 2
        expected_credits = int(expected_cost_with_markup * 1000000)
        
        logger.info(f"Model: {model}, Tokens: {prompt_tokens}p/{completion_tokens}c, Cost: ${expected_total_cost:.6f} (${expected_cost_with_markup:.6f} with markup), Credits: {credits}")
        
        assert credits == expected_credits, f"Expected {expected_credits} credits, got {credits}"
    
    # Test embedding credit calculation
    embedding_test_cases = [
        {"tokens": 1000},
        {"tokens": 10000},
        {"tokens": 100000},
    ]
    
    for test_case in embedding_test_cases:
        tokens = test_case["tokens"]
        credits = calculate_embedding_credits(tokens)
        
        # Calculate expected credits:
        # Cost per token = 1.0 / 1,000,000
        # Total cost = tokens * cost per token
        # Credits = total cost * 1,000,000 (1 credit = $0.001)
        expected_cost_per_token = 1.0 / 1000000
        expected_total_cost = tokens * expected_cost_per_token
        expected_credits = int(expected_total_cost * 1000000)
        
        logger.info(f"Embedding Tokens: {tokens}, Cost: ${expected_total_cost:.6f}, Credits: {credits}")
        
        assert credits == expected_credits, f"Expected {expected_credits} credits, got {credits}"
    
    logger.info("Credit calculation tests passed!")

def test_paypal_integration():
    """Test PayPal sandbox integration"""
    logger.info("Testing PayPal sandbox integration...")
    
    # Initialize PayPal SDK
    initialized = initialize_paypal()
    assert initialized, "Failed to initialize PayPal SDK"
    
    # Create a test payment
    return_url = "https://example.com/return"
    cancel_url = "https://example.com/cancel"
    
    payment_result = create_payment(
        amount_usd=10.00,
        return_url=return_url,
        cancel_url=cancel_url,
        package_name="Test Package"
    )
    
    assert payment_result["success"], f"Failed to create PayPal payment: {payment_result.get('error', 'Unknown error')}"
    
    logger.info(f"Successfully created PayPal payment ID: {payment_result['payment_id']}")
    logger.info(f"Approval URL: {payment_result['approval_url']}")
    
    # Get payment details
    payment_details = get_payment_details(payment_result["payment_id"])
    assert payment_details["success"], f"Failed to get payment details: {payment_details.get('error', 'Unknown error')}"
    
    logger.info(f"Payment state: {payment_details['state']}")
    logger.info(f"Payment amount: ${payment_details['amount']} {payment_details['currency']}")
    
    logger.info("PayPal sandbox integration tests passed!")

def main():
    """Run all billing tests"""
    logger.info("Starting billing system tests...")
    
    try:
        test_credits_calculation()
        test_paypal_integration()
        
        logger.info("All billing system tests passed!")
    except Exception as e:
        logger.error(f"Billing system tests failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    with app.app_context():
        main()