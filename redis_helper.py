"""
Redis Helper Module

This module provides utility functions for working with Redis throughout the application.
It ensures consistent configuration and error handling for Redis connections.
"""

import os
import logging
from typing import Optional, Dict, Any

# Import Redis configuration
from redis_config import get_redis_connection_params

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_redis_url() -> Optional[str]:
    """
    Get Redis URL from environment variables
    
    Returns:
        str: Redis URL or None if not configured
    """
    # Try environment variables in order of preference
    redis_url = os.environ.get('REDIS_HOST') or os.environ.get('REDIS_URL')
    
    if not redis_url:
        logger.warning("No Redis URL configured")
        return None
        
    return redis_url

def configure_redis(redis_url: Optional[str] = None) -> bool:
    """
    Configure Redis connection
    
    Args:
        redis_url: Redis URL (optional, will use environment variable if None)
        
    Returns:
        bool: True if Redis is configured successfully, False otherwise
    """
    # If redis_url is provided, set it in the environment
    if redis_url:
        os.environ['REDIS_HOST'] = redis_url
        return True
        
    # Check if Redis is configured in environment
    if get_redis_url():
        return True
        
    return False

def check_redis_connection() -> bool:
    """
    Check if Redis connection is available
    
    Returns:
        bool: True if Redis connection is available, False otherwise
    """
    try:
        # Import Redis
        import redis
        
        # Get connection parameters
        params = get_redis_connection_params()
        
        # If no Redis host, return False
        if not params['host']:
            return False
            
        # Create connection
        r = redis.Redis(
            host=params['host'],
            port=params['port'],
            password=params['password'],
            socket_timeout=params['socket_timeout'],
            socket_connect_timeout=params['socket_connect_timeout'],
            retry_on_timeout=params['retry_on_timeout']
        )
        
        # Test connection with ping
        return r.ping()
    except Exception as e:
        logger.error(f"Redis connection check failed: {str(e)}")
        return False