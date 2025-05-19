"""
Redis Configuration Module

This module centralizes Redis configuration settings and provides a unified
interface for establishing Redis connections with proper error handling.

Features:
- Environment-based configuration (different settings for dev/prod)
- Connection pooling for better performance
- Automatic fallback mechanisms when Redis is unavailable
- Consistent timeout and retry settings across the application
"""

import os
import logging
import time
from typing import Optional, Dict, Any, Union
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

# Default Redis configuration
DEFAULT_CONFIG = {
    'host': os.environ.get('REDIS_HOST', ''),
    'port': os.environ.get('REDIS_PORT', 6379),
    'db': os.environ.get('REDIS_DB', 0),
    'password': os.environ.get('REDIS_PASSWORD', None),
    'socket_timeout': 2.0,  # Short timeout to prevent app hanging
    'socket_connect_timeout': 2.0,
    'retry_on_timeout': True,
    'health_check_interval': 30,
    'max_connections': 10,
    'decode_responses': True  # Default to decode responses
}

# Cache for connection pools to avoid recreating them
_connection_pools = {}

def get_redis_config(namespace: str = '') -> Dict[str, Any]:
    """
    Get Redis configuration settings with optional namespace-specific overrides
    
    Args:
        namespace: Optional namespace for specific Redis usage (e.g., 'session', 'cache')
        
    Returns:
        Dict containing Redis connection parameters
    """
    config = DEFAULT_CONFIG.copy()
    
    # Check for namespace-specific environment variables
    if namespace:
        namespace_prefix = f'REDIS_{namespace.upper()}_'
        
        # Look for namespace-specific variables
        for key in ['HOST', 'PORT', 'DB', 'PASSWORD']:
            env_var = f'{namespace_prefix}{key}'
            if os.environ.get(env_var):
                config_key = key.lower()
                config[config_key] = os.environ.get(env_var)
    
    # If host is empty, Redis is disabled/unavailable
    if not config['host']:
        logger.warning(f"No Redis host available, {namespace}: Redis features will be disabled")
    
    return config

def is_redis_available(namespace: str = '') -> bool:
    """
    Check if Redis is available for the given namespace
    
    Args:
        namespace: Optional namespace for specific Redis usage
        
    Returns:
        bool: True if Redis is configured and available, False otherwise
    """
    config = get_redis_config(namespace)
    return bool(config['host'])

def get_redis_connection_params(namespace: str = '') -> Dict[str, Any]:
    """
    Get Redis connection parameters for a given namespace
    
    This function returns the necessary parameters for establishing a Redis connection,
    with proper defaults and namespace-specific configuration if available.
    
    Args:
        namespace: Optional namespace for specific Redis usage (e.g., 'cache', 'session')
        
    Returns:
        Dict: Redis connection parameters that can be used to create a Redis client
    """
    # Get the base configuration
    config = get_redis_config(namespace)
    
    # Return connection parameters
    return {
        'host': config['host'],
        'port': config['port'],
        'db': config['db'],
        'password': config['password'],
        'socket_timeout': config['socket_timeout'],
        'socket_connect_timeout': config['socket_connect_timeout'],
        'retry_on_timeout': config['retry_on_timeout'],
        'health_check_interval': config['health_check_interval'],
        'decode_responses': config['decode_responses']
    }

def create_redis_client(namespace: str = '', decode_responses: bool = True) -> Optional[Any]:
    """
    Create a Redis client with the given namespace configuration
    
    This function handles errors gracefully and returns None if Redis is unavailable,
    allowing fallback mechanisms to be implemented.
    
    Args:
        namespace: Optional namespace for specific Redis usage
        decode_responses: Whether to decode byte responses to strings
        
    Returns:
        Redis client instance or None if Redis is unavailable
    """
    try:
        import redis
        from redis.exceptions import RedisError
        
        config = get_redis_config(namespace)
        
        # Override decode_responses setting
        config['decode_responses'] = decode_responses
        
        # Don't attempt connection if host is empty
        if not config['host']:
            return None
        
        # Create or get connection pool
        pool_key = f"{namespace}:{config['host']}:{config['port']}:{config['db']}"
        
        if pool_key not in _connection_pools:
            # Create a new connection pool
            pool = redis.ConnectionPool(
                host=config['host'],
                port=int(config['port']),
                db=int(config['db']),
                password=config['password'],
                socket_timeout=config['socket_timeout'],
                socket_connect_timeout=config['socket_connect_timeout'],
                retry_on_timeout=config['retry_on_timeout'],
                health_check_interval=config['health_check_interval'],
                max_connections=config['max_connections'],
                decode_responses=config['decode_responses']
            )
            _connection_pools[pool_key] = pool
        
        # Create client using the pool
        client = redis.Redis(connection_pool=_connection_pools[pool_key])
        
        # Test connection with minimal overhead
        client.ping()
        
        return client
    except ImportError:
        logger.warning("Redis package not installed, falling back to file storage")
        return None
    except RedisError as e:
        logger.warning(f"Redis connection error: {str(e)}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error creating Redis client: {str(e)}", exc_info=True)
        return None

def get_redis_url(namespace: str = '') -> str:
    """
    Get a Redis URL based on configuration
    
    Args:
        namespace: Optional namespace for specific Redis usage
        
    Returns:
        str: Redis URL in the format redis://user:password@host:port/db
    """
    config = get_redis_config(namespace)
    
    if not config['host']:
        return ''
    
    # Build URL
    auth = f":{config['password']}@" if config['password'] else ''
    return f"redis://{auth}{config['host']}:{config['port']}/{config['db']}"

def parse_redis_url(url: str) -> Dict[str, Any]:
    """
    Parse a Redis URL into configuration parameters
    
    Args:
        url: Redis URL in the format redis://user:password@host:port/db
        
    Returns:
        Dict containing Redis connection parameters
    """
    if not url:
        return {'host': '', 'port': 6379, 'db': 0, 'password': None}
    
    parsed = urlparse(url)
    
    # Extract parts
    host = parsed.hostname or ''
    port = parsed.port or 6379
    password = parsed.password or None
    path = parsed.path or '/'
    db = int(path[1:]) if path and path[1:].isdigit() else 0
    
    return {
        'host': host,
        'port': port,
        'db': db,
        'password': password
    }

def check_redis_health(namespace: str = '') -> Dict[str, Any]:
    """
    Check Redis health and return status information
    
    Args:
        namespace: Optional namespace for specific Redis usage
        
    Returns:
        Dict containing health check results
    """
    start_time = time.time()
    
    try:
        import redis
        from redis.exceptions import RedisError
        
        result = {
            'status': 'unavailable',
            'error': None,
            'latency_ms': 0,
            'info': None
        }
        
        client = create_redis_client(namespace)
        
        if not client:
            result['error'] = 'Redis client could not be created'
            return result
        
        # Ping to check connectivity
        client.ping()
        
        # Get server info (limited subset)
        info = client.info(section='server')
        
        result['status'] = 'available'
        result['info'] = {
            'version': info.get('redis_version', 'unknown'),
            'uptime_days': info.get('uptime_in_days', 0),
            'clients_connected': info.get('connected_clients', 0),
            'memory_used_mb': round(info.get('used_memory', 0) / (1024 * 1024), 2)
        }
        
        # Calculate latency
        result['latency_ms'] = round((time.time() - start_time) * 1000, 2)
        
        return result
    except (ImportError, RedisError) as e:
        return {
            'status': 'unavailable',
            'error': str(e),
            'latency_ms': 0,
            'info': None
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': f"Unexpected error: {str(e)}",
            'latency_ms': 0,
            'info': None
        }