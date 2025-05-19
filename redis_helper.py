"""
Redis Helper Module

This module provides helper functions for creating resilient 
Redis connections and handling Redis-related errors gracefully.
"""

import logging
import os
from functools import wraps
from typing import Optional, Any, Dict, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_redis_operation(default_return_value=None):
    """
    Decorator for safely executing Redis operations with graceful error handling.
    
    Args:
        default_return_value: Value to return if the Redis operation fails
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Check if first arg (self) has redis attribute
                # and if it's None, return the default value
                if args and hasattr(args[0], 'redis') and args[0].redis is None:
                    logger.debug(f"Redis not available for operation: {func.__name__}")
                    return default_return_value
                
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Redis operation failed: {func.__name__} - {str(e)}")
                return default_return_value
        return wrapper
    return decorator

def get_redis_connection_params() -> Dict[str, Any]:
    """
    Get Redis connection parameters from environment variables
    with sensible defaults for timeouts and retry policies.
    
    Returns:
        Dict with Redis connection parameters
    """
    # Primary parameter is REDIS_HOST (also accept REDIS_URL for backward compatibility)
    redis_host = os.environ.get('REDIS_HOST') or os.environ.get('REDIS_URL')
    
    # If no Redis host is available, return None for all params
    if not redis_host:
        logger.warning("No Redis host found in environment variables")
        return {
            'host': None, 
            'port': None, 
            'db': None,
            'password': None,
            'socket_timeout': None,
            'socket_connect_timeout': None,
            'retry_on_timeout': None,
            'decode_responses': None
        }
    
    # Get remaining parameters with defaults
    return {
        'host': redis_host,
        'port': int(os.environ.get('REDIS_PORT', 6379)),
        'db': int(os.environ.get('REDIS_DB', 0)),
        'password': os.environ.get('REDIS_PASSWORD'),
        'socket_timeout': 5.0,  # 5 seconds timeout for operations
        'socket_connect_timeout': 5.0,  # 5 seconds timeout for connections
        'retry_on_timeout': True,  # Retry on timeout
        'decode_responses': True  # Auto-decode responses to strings
    }

def initialize_redis_client(redis_class, **kwargs):
    """
    Safely initialize a Redis client with error handling
    
    Args:
        redis_class: The Redis client class to initialize
        **kwargs: Additional arguments for the Redis client
        
    Returns:
        Initialized Redis client or None if initialization fails
    """
    try:
        # Get connection parameters
        conn_params = get_redis_connection_params()
        
        # If no Redis host, return None
        if not conn_params['host']:
            logger.warning("No Redis host available, Redis features will be disabled")
            return None
        
        # Override with any provided kwargs
        conn_params.update(kwargs)
        
        # Initialize client
        client = redis_class(**conn_params)
        
        # Test connection with ping
        if hasattr(client, 'ping') and callable(client.ping):
            client.ping()
            logger.info(f"Successfully connected to Redis at {conn_params['host']}")
        
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {str(e)}")
        return None

def safe_flush(redis_client):
    """
    Safely flush Redis cache with error handling
    
    Args:
        redis_client: Redis client instance
    
    Returns:
        bool: Success status
    """
    if redis_client is None:
        logger.warning("Cannot flush: Redis client is not available")
        return False
    
    try:
        if hasattr(redis_client, 'flush') and callable(redis_client.flush):
            redis_client.flush()
        elif hasattr(redis_client, 'flushdb') and callable(redis_client.flushdb):
            redis_client.flushdb()
        else:
            logger.warning("Redis client does not support flush operations")
            return False
        
        logger.debug("Successfully flushed Redis cache")
        return True
    except Exception as e:
        logger.error(f"Failed to flush Redis cache: {str(e)}")
        return False

# Enhanced Redis functions with built-in error handling
def safe_get(redis_client, key, default=None):
    """Get a value from Redis with error handling"""
    if redis_client is None:
        return default
    
    try:
        return redis_client.get(key)
    except Exception as e:
        logger.error(f"Redis GET failed for key {key}: {str(e)}")
        return default

def safe_set(redis_client, key, value, expire=None):
    """Set a value in Redis with error handling"""
    if redis_client is None:
        return False
    
    try:
        return redis_client.set(key, value, expire=expire)
    except Exception as e:
        logger.error(f"Redis SET failed for key {key}: {str(e)}")
        return False

def safe_exists(redis_client, key):
    """Check if a key exists in Redis with error handling"""
    if redis_client is None:
        return False
    
    try:
        return redis_client.exists(key)
    except Exception as e:
        logger.error(f"Redis EXISTS failed for key {key}: {str(e)}")
        return False

def safe_delete(redis_client, key):
    """Delete a key from Redis with error handling"""
    if redis_client is None:
        return False
    
    try:
        return redis_client.delete(key)
    except Exception as e:
        logger.error(f"Redis DELETE failed for key {key}: {str(e)}")
        return False