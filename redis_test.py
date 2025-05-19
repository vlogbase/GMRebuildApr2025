#!/usr/bin/env python
"""
Simple Redis Connection Test

This script tests basic Redis connectivity to Azure Redis Cache.
"""

import os
import sys
import ssl
import logging
from redis import Redis
from redis.connection import SSLConnection, ConnectionPool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test connection to Redis"""
    # Redis connection details
    redis_host = "my-bullmq-cache.redis.cache.windows.net"
    redis_port = 6380
    redis_password = os.environ.get("REDIS_PASSWORD", "")
    
    logger.info(f"Testing connection to Redis at {redis_host}:{redis_port}")
    
    try:
        # Method 1: Using SSLConnection directly
        logger.info("Method 1: Using SSLConnection via ConnectionPool")
        pool = ConnectionPool(
            connection_class=SSLConnection,
            host=redis_host,
            port=redis_port,
            password=redis_password,
            ssl_cert_reqs=ssl.CERT_NONE,
            socket_timeout=10,
            socket_connect_timeout=10,
            health_check_interval=30
        )
        client = Redis(connection_pool=pool)
        response = client.ping()
        logger.info(f"Method 1 ping response: {response}")
        
        # Test key-value operations
        client.set("test_key", "test_value")
        value = client.get("test_key")
        logger.info(f"Method 1 set/get test: {value}")
        
        return True
    except Exception as e:
        logger.error(f"Redis connection error: {str(e)}")
        logger.exception("Details:")
        return False

if __name__ == "__main__":
    test_redis_connection()