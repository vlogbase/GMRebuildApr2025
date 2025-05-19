"""
Test script for Redis connection with proper SSL/TLS support

This script tests the Redis connection using the improved configuration
with SSL/TLS 1.2 support for Azure Redis Cache.
"""

import os
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("redis-test")

def test_redis_connection():
    """Test Redis connection with our improved configuration"""
    try:
        # Import Redis modules
        from redis_config import initialize_redis_client, check_redis_health
        
        logger.info("Testing Redis connection...")
        
        # Print Redis environment variables (without passwords)
        redis_host = os.environ.get('REDIS_HOST', 'Not configured')
        redis_port = os.environ.get('REDIS_PORT', 'Not configured')
        ssl_enabled = os.environ.get('REDIS_SSL', 'Not configured')
        
        logger.info(f"Redis configuration: host={redis_host}, port={redis_port}, ssl={ssl_enabled}")
        
        # Test Redis connection with the initialize_redis_client function
        redis_client = initialize_redis_client(
            namespace='test',
            decode_responses=True,
            max_retries=3,
            retry_delay=0.5
        )
        
        if redis_client:
            logger.info("✅ Successfully connected to Redis")
            
            # Test basic operations
            test_key = f"test:connection:{datetime.now().timestamp()}"
            test_value = {"status": "success", "timestamp": datetime.now().isoformat()}
            
            # Set a test value
            redis_client.set(test_key, str(test_value), ex=60)  # expire in 60 seconds
            logger.info(f"Set test value with key: {test_key}")
            
            # Get the test value
            retrieved = redis_client.get(test_key)
            logger.info(f"Retrieved test value: {retrieved}")
            
            # Check Redis health
            health = check_redis_health('test')
            logger.info(f"Redis health check: {health}")
            
            return True
        else:
            logger.error("❌ Failed to connect to Redis")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Redis connection: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    if success:
        logger.info("Redis connection test completed successfully")
        sys.exit(0)
    else:
        logger.error("Redis connection test failed")
        sys.exit(1)