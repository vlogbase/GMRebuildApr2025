"""
Redis Cache Module (Improved)

Enhanced version of the Redis cache module with:
1. Robust error handling
2. Consistent Redis connection management
3. Graceful fallback when Redis is unavailable
4. Standardized logging
"""

import os
import json
import time
import logging
import functools
from typing import Any, Dict, Optional, Union, Callable, TypeVar
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Redis configuration
from redis_config import get_redis_connection_params, initialize_redis_client

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis package not installed, Redis caching will be disabled")

# Type variable for better type hinting
T = TypeVar('T')

def handle_redis_error(default_return_value):
    """
    Decorator for handling Redis errors
    
    Args:
        default_return_value: The default value to return on error
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Redis error in {func.__name__}: {str(e)}")
                return default_return_value
        return wrapper
    return decorator

class RedisCache:
    """
    Redis-backed cache implementation with robust error handling
    
    Features:
    - Resilient to Redis connection issues
    - Safe serialization/deserialization
    - Consistent timeouts
    - Automatic key namespacing
    """
    
    def __init__(self, namespace: str = '', expire_time: int = 3600):
        """
        Initialize Redis cache
        
        Args:
            namespace: Key namespace for this cache instance
            expire_time: Default expiration time in seconds
        """
        self.namespace = namespace
        self.expire_time = expire_time
        self.redis_client = None
        
        # Initialize Redis client safely
        if REDIS_AVAILABLE:
            try:
                # Use the centralized Redis configuration
                try:
                    logger.info(f"Attempting to initialize Redis client with namespace '{namespace}'")
                    # Simple direct connection approach to avoid any parameter conflicts
                    import redis
                    from redis_config import get_redis_connection_params
                    
                    # Get connection parameters
                    params = get_redis_connection_params(namespace)
                    params['decode_responses'] = True
                    
                    # Create Redis client directly
                    self.redis_client = redis.Redis(**params)
                    
                    # Test connection
                    self.redis_client.ping()
                except Exception as e:
                    logger.error(f"Direct Redis connection failed: {e}")
                    self.redis_client = None
                
                if self.redis_client:
                    logger.info(f"Redis cache initialized with namespace '{namespace}'")
                else:
                    logger.warning(f"Redis connection failed, '{namespace}' cache will use fallback mode")
            except Exception as e:
                logger.error(f"Error initializing Redis cache: {str(e)}")
                self.redis_client = None
        else:
            logger.warning("Redis package not available, cache will use fallback mode")
    
    def _get_full_key(self, key: str) -> str:
        """
        Generate a namespaced key
        
        Args:
            key: The original key
            
        Returns:
            str: Namespaced key
        """
        if self.namespace:
            return f"{self.namespace}:{key}"
        return key
    
    def _serialize(self, value: Any) -> str:
        """
        Serialize a value for Redis storage
        
        Args:
            value: The value to serialize
            
        Returns:
            str: Serialized value
        """
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            # Fallback to string representation if JSON serialization fails
            return str(value)
    
    def _deserialize(self, value: Optional[bytes]) -> Any:
        """
        Deserialize a value from Redis storage
        
        Args:
            value: The value to deserialize
            
        Returns:
            Any: Deserialized value or None
        """
        if value is None:
            return None
            
        try:
            # Try to decode and parse as JSON
            decoded = value.decode('utf-8')
            return json.loads(decoded)
        except json.JSONDecodeError:
            # Not JSON, return as string
            return decoded
        except UnicodeDecodeError:
            # Binary data, return as is
            return value
    
    @handle_redis_error(False)
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to store
            expire: Optional TTL in seconds (overrides default expire_time)
            
        Returns:
            bool: Success status
        """
        if self.redis_client is None:
            return False
            
        full_key = self._get_full_key(key)
        serialized = self._serialize(value)
        
        # Use provided expiration or default
        expiration = expire if expire is not None else self.expire_time
        
        return self.redis_client.set(full_key, serialized, ex=expiration)
    
    @handle_redis_error(None)
    def get(self, key: str) -> Any:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Any: The cached value or None if not found
        """
        if self.redis_client is None:
            return None
            
        full_key = self._get_full_key(key)
        value = self.redis_client.get(full_key)
        
        return self._deserialize(value)
    
    @handle_redis_error(False)
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists, False otherwise
        """
        if self.redis_client is None:
            return False
            
        full_key = self._get_full_key(key)
        return bool(self.redis_client.exists(full_key))
    
    @handle_redis_error(0)
    def delete(self, key: str) -> int:
        """
        Delete a key from the cache
        
        Args:
            key: Cache key
            
        Returns:
            int: Number of keys deleted (0 or 1)
        """
        if self.redis_client is None:
            return 0
            
        full_key = self._get_full_key(key)
        return self.redis_client.delete(full_key)
    
    @handle_redis_error(0)
    def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment a key's value
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            int: New value after increment
        """
        if self.redis_client is None:
            return 0
            
        full_key = self._get_full_key(key)
        return self.redis_client.incr(full_key, amount)
    
    @handle_redis_error(False)
    def expire(self, key: str, time_seconds: int) -> bool:
        """
        Set expiration time for a key
        
        Args:
            key: Cache key
            time_seconds: TTL in seconds
            
        Returns:
            bool: Success status
        """
        if self.redis_client is None:
            return False
            
        full_key = self._get_full_key(key)
        return bool(self.redis_client.expire(full_key, time_seconds))
    
    @handle_redis_error(None)
    def ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining TTL for a key
        
        Args:
            key: Cache key
            
        Returns:
            Optional[int]: TTL in seconds, -1 if no expiry, -2 if key doesn't exist, None on error
        """
        if self.redis_client is None:
            return None
            
        full_key = self._get_full_key(key)
        return self.redis_client.ttl(full_key)
    
    @handle_redis_error(False)
    def flush(self) -> bool:
        """
        Clear all cache keys in the current namespace
        
        Returns:
            bool: Success status
        """
        if self.redis_client is None:
            return False
            
        # If namespace is set, only clear keys in that namespace
        if self.namespace:
            pattern = f"{self.namespace}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                return bool(self.redis_client.delete(*keys))
            return True
        
        # No namespace, clear everything (use with caution)
        return bool(self.redis_client.flushdb())
    
    @handle_redis_error(False)
    def ping(self) -> bool:
        """
        Check if Redis connection is alive
        
        Returns:
            bool: Connection status
        """
        if self.redis_client is None:
            return False
            
        return self.redis_client.ping()
    
    def is_available(self) -> bool:
        """
        Check if Redis is available
        
        Returns:
            bool: True if Redis is available, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            return self.ping()
        except:
            return False

def create_cache(namespace: str = '', expire_time: int = 3600) -> RedisCache:
    """
    Factory function to create a Redis cache instance
    
    Args:
        namespace: Key namespace
        expire_time: Default expiration time in seconds
        
    Returns:
        RedisCache: Initialized Redis cache
    """
    return RedisCache(namespace=namespace, expire_time=expire_time)

def get_redis_connection(use_pool=True):
    """
    Establishes and returns a Redis connection.
    Uses a connection pool by default for efficiency.
    
    This function is maintained for backward compatibility with existing code.
    For new code, consider using RedisCache class directly.
    
    Args:
        use_pool: Whether to use a connection pool (recommended)
        
    Returns:
        Redis connection object or None if connection fails
    """
    # Import Redis configuration
    from redis_config import get_redis_connection_params
    
    try:
        # Only import redis if available
        import redis
        
        # Get connection parameters
        params = get_redis_connection_params()
        
        # If no Redis host, return None
        if not params['host']:
            logger.warning("No Redis host available, returning None for Redis connection")
            return None
        
        # Create connection pool if requested
        if use_pool:
            # Create a connection pool
            pool = redis.ConnectionPool(
                host=params['host'],
                port=params['port'],
                db=params['db'],
                password=params['password'],
                socket_timeout=params['socket_timeout'],
                socket_connect_timeout=params['socket_connect_timeout'],
                retry_on_timeout=params['retry_on_timeout'],
                decode_responses=params['decode_responses']
            )
            return redis.Redis(connection_pool=pool)
        else:
            # Create direct connection
            return redis.Redis(
                host=params['host'],
                port=params['port'],
                db=params['db'],
                password=params['password'],
                socket_timeout=params['socket_timeout'],
                socket_connect_timeout=params['socket_connect_timeout'],
                retry_on_timeout=params['retry_on_timeout'],
                decode_responses=params['decode_responses']
            )
    except ImportError:
        logger.warning("Redis package not installed, cannot create Redis connection")
        return None
    except Exception as e:
        logger.error(f"Failed to create Redis connection: {str(e)}")
        return None