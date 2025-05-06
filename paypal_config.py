"""
PayPal Configuration Module

This module handles PayPal API initialization and provides functions
for creating and managing PayPal payments.
"""

import os
import logging
import json
import paypalrestsdk
from paypalrestsdk.exceptions import ResourceNotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_paypal():
    """
    Initialize PayPal SDK with credentials from environment variables.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        client_id = os.environ.get('PAYPAL_CLIENT_ID')
        client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logger.error("PayPal credentials missing")
            return False
        
        # Configure the SDK with sandbox credentials
        paypalrestsdk.configure({
            "mode": "sandbox",  # Use "live" for production
            "client_id": client_id,
            "client_secret": client_secret
        })
        
        logger.info("PayPal SDK initialized in sandbox mode.")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing PayPal: {e}")
        return False

def create_payment(amount_usd, return_url, cancel_url, package_name=None):
    """
    Create a PayPal payment.
    
    Args:
        amount_usd (float): Amount in USD
        return_url (str): URL to redirect to after approval
        cancel_url (str): URL to redirect to after cancellation
        package_name (str, optional): Name of the package being purchased
    
    Returns:
        dict: Dictionary with success status, payment ID, and approval URL
    """
    try:
        # Initialize PayPal if not already initialized
        initialize_paypal()
        
        # Format the amount to 2 decimal places
        formatted_amount = "{:.2f}".format(float(amount_usd))
        
        # Create the payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": return_url,
                "cancel_url": cancel_url
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": package_name or "Credits Purchase",
                        "sku": "credit-package",
                        "price": formatted_amount,
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": formatted_amount,
                    "currency": "USD"
                },
                "description": package_name or f"Purchase of ${formatted_amount} in credits"
            }]
        })
        
        # Create the payment
        if payment.create():
            # Extract the approval URL
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            
            if approval_url:
                return {
                    "success": True,
                    "payment_id": payment.id,
                    "approval_url": approval_url
                }
            else:
                return {
                    "success": False,
                    "error": "No approval URL found in payment response"
                }
        else:
            return {
                "success": False,
                "error": payment.error
            }
    
    except Exception as e:
        logger.error(f"Error creating PayPal payment: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def execute_payment(payment_id, payer_id):
    """
    Execute a PayPal payment after approval.
    
    Args:
        payment_id (str): PayPal payment ID
        payer_id (str): PayPal payer ID
    
    Returns:
        dict: Dictionary with success status and payment info
    """
    try:
        # Initialize PayPal if not already initialized
        initialize_paypal()
        
        # Fetch the payment
        payment = paypalrestsdk.Payment.find(payment_id)
        
        # Execute the payment
        if payment.execute({"payer_id": payer_id}):
            # Extract relevant payment information
            transactions = payment.transactions[0]
            amount = transactions.amount.total
            currency = transactions.amount.currency
            
            return {
                "success": True,
                "payment_id": payment.id,
                "amount": amount,
                "currency": currency,
                "state": payment.state
            }
        else:
            return {
                "success": False,
                "error": payment.error
            }
    
    except ResourceNotFound:
        logger.error(f"Payment {payment_id} not found")
        return {
            "success": False,
            "error": "Payment not found"
        }
    except Exception as e:
        logger.error(f"Error executing PayPal payment: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_payment_details(payment_id):
    """
    Get details of a PayPal payment.
    
    Args:
        payment_id (str): PayPal payment ID
    
    Returns:
        dict: Dictionary with success status and payment details
    """
    try:
        # Initialize PayPal if not already initialized
        initialize_paypal()
        
        # Fetch the payment
        payment = paypalrestsdk.Payment.find(payment_id)
        
        # Extract relevant payment information
        transactions = payment.transactions[0]
        amount = transactions.amount.total
        currency = transactions.amount.currency
        
        return {
            "success": True,
            "payment_id": payment.id,
            "amount": amount,
            "currency": currency,
            "state": payment.state
        }
    
    except ResourceNotFound:
        logger.error(f"Payment {payment_id} not found")
        return {
            "success": False,
            "error": "Payment not found"
        }
    except Exception as e:
        logger.error(f"Error getting PayPal payment details: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Test PayPal integration
    success = initialize_paypal()
    print(f"PayPal initialization: {'Success' if success else 'Failed'}")