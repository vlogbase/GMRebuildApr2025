"""
Test Redis Connection and Flush Cache

This script tests the connection to the Redis cache and flushes it if successful.
"""

import time
import logging
from redis_cache import redis_cache

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RedisTest")

def test_redis_connection():
    """Test the Redis connection and basic operations."""
    logger.info("Testing Redis connection...")
    
    # Check if Redis is available
    if not redis_cache.is_available():
        logger.error("Redis is not available. Check your connection settings.")
        return False
    
    logger.info("Successfully connected to Redis!")
    
    # Flush the cache
    logger.warning("Flushing Redis cache...")
    if redis_cache.flush():
        logger.info("Cache flushed successfully.")
    else:
        logger.error("Failed to flush cache.")
        return False
    
    # Test basic operations
    logger.info("Testing basic Redis operations...")
    
    # Test set and get
    test_key = "test:key"
    test_value = {"name": "Test Value", "timestamp": time.time()}
    
    logger.info(f"Setting key: {test_key}")
    if not redis_cache.set(test_key, test_value, ttl=60):
        logger.error("Failed to set test key.")
        return False
    
    logger.info(f"Getting key: {test_key}")
    retrieved_value = redis_cache.get(test_key)
    if retrieved_value != test_value:
        logger.error(f"Retrieved value doesn't match: {retrieved_value} vs {test_value}")
        return False
    
    logger.info("Set and get operations successful!")
    
    # Test hash operations
    test_hash = "test:hash"
    field1 = "field1"
    field2 = "field2"
    value1 = "value1"
    value2 = {"complex": "value", "with": ["nested", "data"]}
    
    logger.info(f"Setting hash fields in {test_hash}")
    redis_cache.hash_set(test_hash, field1, value1)
    redis_cache.hash_set(test_hash, field2, value2)
    
    logger.info(f"Getting hash fields from {test_hash}")
    retrieved_field1 = redis_cache.hash_get(test_hash, field1)
    retrieved_field2 = redis_cache.hash_get(test_hash, field2)
    
    if retrieved_field1 != value1 or retrieved_field2 != value2:
        logger.error("Hash operations failed!")
        return False
    
    logger.info("Hash operations successful!")
    
    # Test delete
    logger.info(f"Deleting key: {test_key}")
    if not redis_cache.delete(test_key):
        logger.error("Failed to delete key.")
        return False
    
    if redis_cache.get(test_key) is not None:
        logger.error("Key still exists after deletion!")
        return False
    
    logger.info("Delete operation successful!")
    
    # Test key pattern operations
    for i in range(5):
        redis_cache.set(f"pattern:test:{i}", f"value {i}", ttl=60)
    
    logger.info("Deleting keys with pattern 'pattern:test:*'")
    deleted = redis_cache.key_prefix_delete("pattern:test:")
    logger.info(f"Deleted {deleted} keys with pattern")
    
    if deleted != 5:
        logger.warning(f"Expected to delete 5 keys, but deleted {deleted}")
    
    # All tests passed
    logger.info("All Redis tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_redis_connection()
    if success:
        print("\n✅ Redis connection test passed! The cache is ready to use.")
    else:
        print("\n❌ Redis connection test failed. Please check your configuration.")