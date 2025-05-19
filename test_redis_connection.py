#!/usr/bin/env python
"""
Test Redis Connection

This script verifies that the application can connect to Redis and perform
basic operations. It also tests the job system by enqueueing a test job.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test basic Redis connection and operations"""
    try:
        from redis_cache import get_redis_connection, RedisCache
        
        # Get Redis connection
        redis_conn = get_redis_connection()
        if not redis_conn:
            logger.error("Failed to establish Redis connection")
            return False
        
        # Test Redis connection
        logger.info("Testing Redis connection...")
        redis_info = redis_conn.info()
        redis_version = redis_info.get('redis_version', 'Unknown')
        logger.info(f"Connected to Redis version: {redis_version}")
        
        # Test basic Redis operations
        test_key = f"test_connection:{datetime.now().isoformat()}"
        test_value = json.dumps({
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "message": "Redis connection test"
        })
        
        # Set a value
        logger.info(f"Setting test key: {test_key}")
        redis_conn.setex(test_key, 60, test_value)  # Expire in 60 seconds
        
        # Get the value back
        retrieved_value = redis_conn.get(test_key)
        if retrieved_value:
            logger.info(f"Retrieved test value: {retrieved_value.decode('utf-8')}")
        else:
            logger.error("Failed to retrieve test value")
            return False
        
        # Delete the test key
        redis_conn.delete(test_key)
        
        # Test RedisCache wrapper
        cache = RedisCache(namespace="test_cache")
        
        cache_key = f"test_cache_key:{int(time.time())}"
        cache_value = {"test": True, "timestamp": datetime.now().isoformat()}
        
        logger.info(f"Testing RedisCache with key: {cache_key}")
        cache.set(cache_key, cache_value, ttl=60)
        
        cached_value = cache.get(cache_key)
        if cached_value:
            logger.info(f"Retrieved cached value: {json.dumps(cached_value)}")
        else:
            logger.error("Failed to retrieve cached value")
            return False
        
        cache.delete(cache_key)
        
        logger.info("Basic Redis operations completed successfully")
        return True
    
    except ImportError as e:
        logger.error(f"Failed to import Redis modules: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Error testing Redis connection: {e}")
        return False

def test_job_system():
    """Test the job system by enqueueing a test job"""
    try:
        from jobs import job_manager
        
        # Define a test job function
        def test_job(message):
            """Simple test job function"""
            logger.info(f"Test job executed with message: {message}")
            return {
                "status": "success",
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        
        # Enqueue a test job
        logger.info("Enqueueing test job...")
        job = job_manager.enqueue(
            test_job, 
            f"Test job at {datetime.now().isoformat()}", 
            queue_name="default",
            description="Redis connection test job"
        )
        
        if job:
            logger.info(f"Test job enqueued with ID: {job.id}")
            
            # Check job status
            time.sleep(2)  # Give the worker a chance to process the job
            
            refreshed_job = job_manager.fetch_job(job.id)
            if refreshed_job:
                status = refreshed_job.get_status()
                logger.info(f"Test job status: {status}")
                
                # If a worker is running, the job might be completed already
                if refreshed_job.is_finished:
                    result = refreshed_job.result
                    logger.info(f"Test job result: {result}")
                
                return True
            else:
                logger.error(f"Could not fetch job with ID: {job.id}")
                return False
        else:
            logger.error("Failed to enqueue test job")
            return False
    
    except ImportError as e:
        logger.error(f"Failed to import job modules: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Error testing job system: {e}")
        return False

def test_api_cache():
    """Test the API cache with a decorated function"""
    try:
        from api_cache import ApiCache
        
        # Create API cache instance
        api_cache = ApiCache(namespace="test_api_cache")
        
        # Define a test function with caching
        @api_cache.cache(ttl=60)
        def test_api_function(param1, param2):
            """Example API function that would be cached"""
            result = {
                "param1": param1,
                "param2": param2,
                "timestamp": datetime.now().isoformat(),
                "random": os.urandom(4).hex()  # To verify we get the cached version
            }
            logger.info(f"Generated new API response: {result}")
            return result
        
        # Call the function twice, second call should be cached
        logger.info("Calling test API function first time...")
        result1 = test_api_function("value1", param2="value2")
        
        logger.info("Calling test API function second time (should be cached)...")
        result2 = test_api_function("value1", param2="value2")
        
        # Different parameters should generate a new response
        logger.info("Calling test API function with different parameters...")
        result3 = test_api_function("different", param2="values")
        
        # Verify caching worked
        if result1["random"] == result2["random"] and result1["random"] != result3["random"]:
            logger.info("API cache is working correctly")
            return True
        else:
            logger.error("API cache test failed")
            return False
    
    except ImportError as e:
        logger.error(f"Failed to import API cache modules: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Error testing API cache: {e}")
        return False

def main():
    """Main entry point"""
    try:
        logger.info("Starting Redis connection test...")
        
        # Test Redis connection
        redis_result = test_redis_connection()
        
        if redis_result:
            logger.info("✅ Redis connection test passed")
        else:
            logger.error("❌ Redis connection test failed")
            return 1
        
        # Test job system
        logger.info("\nStarting job system test...")
        job_result = test_job_system()
        
        if job_result:
            logger.info("✅ Job system test passed")
        else:
            logger.warning("⚠️ Job system test did not complete successfully")
            logger.warning("This could be because no worker is running yet - worker needs to be started separately")
        
        # Test API cache
        logger.info("\nStarting API cache test...")
        cache_result = test_api_cache()
        
        if cache_result:
            logger.info("✅ API cache test passed")
        else:
            logger.error("❌ API cache test failed")
            return 1
        
        logger.info("\nAll tests completed")
        return 0
    
    except Exception as e:
        logger.error(f"Error during tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())