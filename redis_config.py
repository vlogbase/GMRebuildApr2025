"""
Redis Configuration Module

This module provides centralized configuration for Redis connections across
different components of the application, with robust error handling and
fallback mechanisms when Redis is unavailable.
"""

import os
import logging
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default timeout values (in seconds)
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_SOCKET_TIMEOUT = 5.0
DEFAULT_RETRY_ON_TIMEOUT = True
DEFAULT_POOL_SIZE = 10

def get_redis_url() -> Optional[str]:
    """
    Get Redis URL from environment variables with consistent naming
    
    Checks both REDIS_HOST and REDIS_URL for backward compatibility
    
    Returns:
        Optional[str]: Redis URL or None if not available
    """
    # Primary parameter is REDIS_HOST
    redis_url = os.environ.get('REDIS_HOST')
    
    # Fall back to REDIS_URL for backward compatibility
    if not redis_url:
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            logger.info("Using REDIS_URL environment variable (REDIS_HOST recommended)")
    
    if not redis_url:
        logger.warning("No Redis host found in environment variables")
    
    return redis_url

def parse_redis_url(url: str) -> Dict[str, Any]:
    """
    Parse Redis URL into connection parameters
    
    Args:
        url: Redis connection URL
        
    Returns:
        Dict with Redis connection parameters
    """
    try:
        parsed = urlparse(url)
        
        # Extract username/password if provided
        auth = None
        if '@' in parsed.netloc:
            auth, netloc = parsed.netloc.split('@', 1)
        else:
            netloc = parsed.netloc
            
        # Parse host and port
        if ':' in netloc:
            host, port = netloc.split(':', 1)
            try:
                port = int(port)
            except ValueError:
                port = 6379
        else:
            host = netloc
            port = 6379
            
        # Extract password from auth part
        password = None
        if auth and ':' in auth:
            _, password = auth.split(':', 1)
            
        # Extract database number from path
        db = 0
        if parsed.path and len(parsed.path) > 1:
            try:
                db = int(parsed.path[1:])
            except ValueError:
                pass
                
        return {
            'host': host,
            'port': port,
            'password': password,
            'db': db
        }
        
    except Exception as e:
        logger.error(f"Failed to parse Redis URL: {str(e)}")
        # Return empty dict if parsing fails
        return {}

def get_redis_connection_params() -> Dict[str, Any]:
    """
    Get Redis connection parameters from environment variables
    with sensible defaults for timeouts and retry policies.
    
    Returns:
        Dict with Redis connection parameters
    """
    # Get Redis URL
    redis_url = get_redis_url()
    
    # If no Redis URL is available, return None for all params
    if not redis_url:
        logger.warning("Redis is not configured, features requiring Redis will be disabled")
        return {
            'host': None, 
            'port': None, 
            'password': None,
            'db': None,
            'socket_timeout': None,
            'socket_connect_timeout': None,
            'retry_on_timeout': None,
            'decode_responses': None
        }
    
    # Parse Redis URL
    parsed_params = parse_redis_url(redis_url)
    
    # Add connection timeout parameters
    params = {
        **parsed_params,
        'socket_timeout': float(os.environ.get('REDIS_SOCKET_TIMEOUT', DEFAULT_SOCKET_TIMEOUT)),
        'socket_connect_timeout': float(os.environ.get('REDIS_CONNECT_TIMEOUT', DEFAULT_CONNECT_TIMEOUT)),
        'retry_on_timeout': os.environ.get('REDIS_RETRY_ON_TIMEOUT', DEFAULT_RETRY_ON_TIMEOUT) == 'True',
        'decode_responses': True
    }
    
    return params

def initialize_redis_client(redis_class, namespace: str = '', expire_time: int = 3600, **kwargs):
    """
    Safely initialize a Redis client with error handling
    
    Args:
        redis_class: The Redis client class to initialize
        namespace: Optional namespace prefix for keys
        expire_time: Default expiration time in seconds
        **kwargs: Additional arguments for the Redis client
        
    Returns:
        Initialized Redis client or None if initialization fails
    """
    try:
        # Get connection parameters
        conn_params = get_redis_connection_params()
        
        # If no Redis host, return None
        if not conn_params['host']:
            logger.warning(f"No Redis host available, {namespace} Redis features will be disabled")
            return None
        
        # Override with any provided kwargs
        conn_params.update(kwargs)
        
        # Log Redis connection attempt with proper sanitization
        sanitized_params = conn_params.copy()
        if 'password' in sanitized_params and sanitized_params['password']:
            sanitized_params['password'] = '******'
        logger.debug(f"Initializing Redis client with params: {sanitized_params}")
        
        # Initialize client
        client = redis_class(**conn_params)
        
        # Set namespace and expire time if supported
        if hasattr(client, 'namespace'):
            client.namespace = namespace
        
        if hasattr(client, 'expire_time'):
            client.expire_time = expire_time
        
        # Test connection with ping if available
        connection_start = time.time()
        if hasattr(client, 'ping') and callable(client.ping):
            client.ping()
            connection_time = time.time() - connection_start
            logger.info(f"Successfully connected to Redis at {conn_params['host']} in {connection_time:.3f}s")
        
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {str(e)}")
        return None