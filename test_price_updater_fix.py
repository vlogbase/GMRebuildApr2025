"""
Test script to verify that price_updater.py works without application context errors.
"""

import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_price_updater():
    """Test the price_updater functionality to verify there are no application context errors."""
    try:
        logger.info("Testing price_updater.py to check for application context errors")
        
        # Import functionality from price_updater
        from price_updater import should_update_prices, fetch_and_store_openrouter_prices, get_model_cost
        
        # Test 1: Check if we should update prices
        logger.info("Test 1: Checking should_update_prices()")
        should_update = should_update_prices()
        logger.info(f"Should update prices: {should_update}")
        
        # Test 2: Get model cost for a known model
        logger.info("Test 2: Checking get_model_cost()")
        model_id = "anthropic/claude-3-opus-20240229"
        cost_info = get_model_cost(model_id)
        logger.info(f"Cost info for {model_id}: {cost_info}")
        
        # Test 3: Fetch and store prices if needed
        logger.info("Test 3: Testing fetch_and_store_openrouter_prices()")
        if should_update or True:  # Force update for testing
            logger.info("Updating model prices...")
            result = fetch_and_store_openrouter_prices(force_update=True)
            logger.info(f"Price update result: {result}")
        
        logger.info("All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    start_time = time.time()
    success = test_price_updater()
    elapsed = time.time() - start_time
    
    if success:
        logger.info(f"All price_updater tests passed in {elapsed:.2f} seconds!")
    else:
        logger.error(f"price_updater tests failed after {elapsed:.2f} seconds")