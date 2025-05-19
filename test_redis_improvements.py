#!/usr/bin/env python3
"""
Test script to verify Redis error handling improvements
"""
import logging
import time
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("redis_test")
logger.info("Starting Redis improvements test")

# Test Redis cache module
try:
    logger.info("Testing Redis cache module...")
    from redis_cache import RedisCache
    
    # Create a cache instance
    cache = RedisCache(namespace="test_cache")
    logger.info(f"Redis cache availability: {cache.is_available()}")
    
    # Test Redis operations with error handling
    test_key = "test_key"
    test_value = {"test": "data", "timestamp": time.time()}
    
    logger.info(f"Setting test data: {test_value}")
    set_result = cache.set(test_key, test_value)
    logger.info(f"Set result: {set_result}")
    
    logger.info(f"Getting test data")
    get_result = cache.get(test_key)
    logger.info(f"Get result: {get_result}")
    
    logger.info("Redis cache test completed")
except Exception as e:
    logger.error(f"Redis cache test failed: {str(e)}")

# Test API cache module
try:
    logger.info("Testing API cache module...")
    from api_cache import ApiCache, get_api_cache
    
    # Get a cache instance
    api_cache = get_api_cache()
    logger.info(f"API cache initialized")
    
    # Define a test function to be cached
    @api_cache.cache_api_call(ttl=60)
    def test_api_function(param):
        logger.info(f"Executing test API function with param: {param}")
        return {"result": f"Processed {param}", "timestamp": time.time()}
    
    # Test the caching behavior
    logger.info("Calling test function (first call)")
    first_result = test_api_function("test_data")
    logger.info(f"First call result: {first_result}")
    
    logger.info("Calling test function again (should be cached)")
    second_result = test_api_function("test_data")
    logger.info(f"Second call result: {second_result}")
    
    # Test cache clearing
    logger.info("Clearing cache")
    test_api_function.clear_cache()
    
    logger.info("Calling test function after cache clear")
    third_result = test_api_function("test_data")
    logger.info(f"Third call result: {third_result}")
    
    logger.info("API cache test completed")
except Exception as e:
    logger.error(f"API cache test failed: {str(e)}")

# Test model pricing cache
try:
    logger.info("Testing model pricing cache...")
    from api_cache import cache_model_pricing
    
    @cache_model_pricing(ttl=60)
    def get_test_pricing(force_refresh=False):
        logger.info(f"Executing pricing function (force_refresh={force_refresh})")
        return {"models": [{"id": "test-model", "price": 0.01}], "timestamp": time.time()}
    
    logger.info("Calling pricing function (first call)")
    first_pricing = get_test_pricing()
    logger.info(f"First pricing result: {first_pricing}")
    
    logger.info("Calling pricing function again (should be cached)")
    second_pricing = get_test_pricing()
    logger.info(f"Second pricing result: {second_pricing}")
    
    logger.info("Calling pricing function with force_refresh=True")
    force_pricing = get_test_pricing(force_refresh=True)
    logger.info(f"Forced refresh pricing result: {force_pricing}")
    
    logger.info("Model pricing cache test completed")
except Exception as e:
    logger.error(f"Model pricing cache test failed: {str(e)}")

logger.info("All tests completed")