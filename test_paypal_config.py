"""
Test the PayPal Payouts SDK configuration and functions.
"""

import logging
from paypal_config import get_paypal_client, generate_sender_batch_id

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_paypal_client():
    """Test that the PayPal client initializes correctly."""
    client = get_paypal_client()
    if client:
        logger.info("PayPal client initialized successfully")
        return True
    else:
        logger.error("PayPal client initialization failed")
        return False

def test_generate_sender_batch_id():
    """Test the generation of a unique sender batch ID."""
    sender_batch_id = generate_sender_batch_id()
    logger.info(f"Generated sender batch ID: {sender_batch_id}")
    return sender_batch_id is not None and sender_batch_id.startswith("GloriaMundoPayout-")

if __name__ == "__main__":
    print("Testing PayPal Payouts SDK configuration...")
    print(f"PayPal client test: {'PASSED' if test_paypal_client() else 'FAILED'}")
    print(f"Sender batch ID test: {'PASSED' if test_generate_sender_batch_id() else 'FAILED'}")