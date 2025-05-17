"""
Test script for price_updater.py application context fixes

This script tests if the price_updater.py application context issues have been
resolved by importing and calling functions that previously caused warnings.
"""
import logging
import sys
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_price_updater")

def test_price_updater():
    """Test price_updater functions to verify application context fixes"""
    logger.info("Starting price_updater test")
    
    # Import after logging setup
    from price_updater import should_update_prices, fetch_and_store_openrouter_prices, get_model_cost
    
    try:
        # Test should_update_prices
        logger.info("Testing should_update_prices()")
        update_needed = should_update_prices()
        logger.info(f"should_update_prices result: {update_needed}")
        
        # Test get_model_cost for a sample model
        logger.info("Testing get_model_cost()")
        model_id = "anthropic/claude-3-opus-20240229"
        cost_info = get_model_cost(model_id)
        logger.info(f"Cost info for {model_id}: {cost_info}")
        
        logger.info("Tests completed successfully")
        return True
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Application context test starting")
    test_price_updater()
    logger.info("Application context test completed")