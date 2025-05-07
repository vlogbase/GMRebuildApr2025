"""
Test script for the model refresh endpoint

This script directly tests the price refresh functionality and model fetch functions
without running the full Flask application.
"""

import os
import json
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the modified cache module
from price_updater import model_prices_cache, fetch_and_store_openrouter_prices

def test_refresh():
    """
    Test the price refresh functionality
    """
    # Check initial cache state
    logger.info("Initial cache state:")
    logger.info(f"Cache has {len(model_prices_cache.get('prices', {}))} models")
    logger.info(f"Last updated: {model_prices_cache.get('last_updated')}")
    
    # Perform refresh
    logger.info("\nPerforming model price refresh...")
    success = fetch_and_store_openrouter_prices()
    
    # Check updated cache state
    logger.info(f"\nRefresh successful: {success}")
    logger.info(f"Cache now has {len(model_prices_cache.get('prices', {}))} models")
    logger.info(f"Last updated: {model_prices_cache.get('last_updated')}")
    
    # Get some sample models
    prices = model_prices_cache.get('prices', {})
    sample_models = list(prices.keys())[:5] if prices else []
    
    # Log sample models
    logger.info("\nSample models in cache:")
    for model_id in sample_models:
        model_data = prices[model_id]
        logger.info(f"  {model_id} - Input: ${model_data['input_price']:.2f}, Output: ${model_data['output_price']:.2f}")
    
    # Report success
    if success and len(prices) > 0:
        logger.info("\nTEST PASSED: Successfully refreshed model prices")
        return True
    else:
        logger.error("\nTEST FAILED: Could not refresh model prices")
        return False

def direct_api_test():
    """
    Test direct API call to verify connection and data format
    """
    logger.info("\n==== Testing direct API call to OpenRouter ====")
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found in environment variables")
        return False

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        logger.info("Fetching models from OpenRouter API...")
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            timeout=15.0
        )
        
        # Log response status
        logger.info(f"Response status code: {response.status_code}")
        
        # Check response status
        response.raise_for_status()
        
        # Parse response JSON
        models_data = response.json()
        
        model_count = len(models_data.get('data', []))
        logger.info(f"Successfully fetched {model_count} models from OpenRouter API")
        
        # Log the first 3 models
        logger.info("Sample models from API call:")
        for i, model in enumerate(models_data.get('data', [])[:3]):
            logger.info(f"  {i+1}. {model.get('id')} - {model.get('name')}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing direct API call: {e}")
        return False

def test_cache_persistence():
    """
    Test if the cache is properly persisting to disk
    """
    logger.info("\n==== Testing cache persistence ====")
    
    # 1. Verify initial state
    logger.info(f"Initial model count: {len(model_prices_cache.get('prices', {}))}")
    
    # 2. Update the cache
    success = fetch_and_store_openrouter_prices()
    if not success:
        logger.error("Failed to update the cache with fresh data")
        return False
    
    # 3. Record updated state
    model_count = len(model_prices_cache.get('prices', {}))
    logger.info(f"Updated model count: {model_count}")
    
    # 4. Create a new instance of the cache (which should load from disk)
    from price_updater import ModelPricesCache
    test_cache = ModelPricesCache()
    
    # 5. Verify the new instance has the same data
    test_model_count = len(test_cache.get('prices', {}))
    logger.info(f"New instance model count: {test_model_count}")
    
    if test_model_count == model_count and test_model_count > 0:
        logger.info("Cache persistence test PASSED ✓")
        return True
    else:
        logger.error("Cache persistence test FAILED ✗")
        return False

if __name__ == "__main__":
    # Run the tests
    logger.info("=== Starting Refresh Endpoint Tests ===")
    
    # Test direct API connection
    api_status = direct_api_test()
    
    if api_status:
        # Test refresh functionality
        refresh_status = test_refresh()
        
        # Test cache persistence
        persistence_status = test_cache_persistence()
        
        # Report overall status
        if refresh_status and persistence_status:
            logger.info("\n==== ALL TESTS PASSED ====")
        else:
            logger.error("\n==== SOME TESTS FAILED ====")
    else:
        logger.error("API connection test failed, skipping remaining tests")