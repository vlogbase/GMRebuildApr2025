"""
Redis Cache Module

This module provides a flexible Redis caching system for Flask applications.
It's designed to be used for general-purpose caching, rate limiting, and session storage.
"""

import os
import json
import pickle
import logging
import functools
from typing import Dict, List, Optional, Any, Callable, TypeVar, Union, cast
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Redis
try:
    import redis
    from redis.exceptions import RedisError
except ImportError:
    logger.error("Redis not installed. Please install with: pip install redis")
    redis = None
    RedisError = Exception

# Type variables
T = TypeVar('T')
ResponseT = TypeVar('ResponseT')

# Global Redis connection
_redis_connection = None

def get_redis_connection(redis_url=None, use_ssl=None):
    """
    Get or create a Redis connection
    
    Args:
        redis_url: Redis URL (optional, defaults to REDIS_URL env var)
        use_ssl: Whether to use SSL (optional, detected from URL if not provided)
        
    Returns:
        Redis client instance
    """
    global _redis_connection
    
    # Return existing connection if available
    if _redis_connection is not None:
        return _redis_connection
    
    # Check if Redis is available
    if redis is None:
        logger.error("Redis module not available")
        return None
    
    try:
        # Get Redis URL from environment if not provided
        if not redis_url:
            redis_url = os.environ.get('REDIS_URL')
            if not redis_url:
                logger.warning("REDIS_URL environment variable not set, defaulting to localhost")
                redis_url = 'redis://localhost:6379/0'
        
        # Detect SSL from URL if not provided
        if use_ssl is None:
            use_ssl = redis_url.startswith('rediss://')
        
        logger.info(f"Connecting to Redis at {redis_url} (SSL: {use_ssl})")
        
        # Parse Redis URL and create connection
        if redis_url.startswith('redis://') or redis_url.startswith('rediss://'):
            # Use URL to create connection
            connection_kwargs = {
                'url': redis_url,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
                'socket_keepalive': True,
                'health_check_interval': 30,
                'retry_on_timeout': True,
            }
            
            if use_ssl:
                connection_kwargs['ssl_cert_reqs'] = None
            
            _redis_connection = redis.Redis(**connection_kwargs)
        else:
            # Assume host:port format
            host, port = redis_url.split(':')
            _redis_connection = redis.Redis(
                host=host,
                port=int(port),
                socket_timeout=5,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
                retry_on_timeout=True,
                ssl=use_ssl,
                ssl_cert_reqs=None if use_ssl else 'none'
            )
        
        # Test connection
        _redis_connection.ping()
        logger.info("Redis connection established")
        
        return _redis_connection
    
    except (RedisError, ValueError, ConnectionError) as e:
        logger.error(f"Error connecting to Redis: {e}")
        _redis_connection = None
        
        # Return dummy Redis for fallback
        return DummyRedis()

class DummyRedis:
    """
    Dummy Redis implementation for when Redis is not available
    All operations are no-ops
    """
    def __getattr__(self, name):
        def dummy_method(*args, **kwargs):
            logger.debug(f"Dummy Redis: {name}() called")
            if name in ['get', 'hget', 'hgetall', 'hmget', 'smembers', 'zrange']:
                return None
            elif name in ['set', 'setex', 'hset', 'hmset', 'sadd', 'srem', 'zadd']:
                return True
            return None
        return dummy_method

class RedisCache:
    """Redis-based caching system"""
    
    def __init__(self, namespace: str = 'cache', expire_time: int = 300, redis_client=None):
        """
        Initialize the cache
        
        Args:
            namespace: Namespace prefix for cache keys
            expire_time: Default cache expiration time in seconds (default: 5 minutes)
            redis_client: Redis client instance (optional, will create if None)
        """
        self.namespace = namespace
        self.expire_time = expire_time
        self.redis = redis_client or get_redis_connection()
    
    def _make_key(self, key: str) -> str:
        """
        Create a namespaced key
        
        Args:
            key: Base key
            
        Returns:
            str: Namespaced key
        """
        return f"{self.namespace}:{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Any: Cached value or default
        """
        try:
            full_key = self._make_key(key)
            data = self.redis.get(full_key)
            
            if data is None:
                return default
            
            try:
                # Try to unpickle first (for complex objects)
                return pickle.loads(data)
            except:
                # Fall back to string decoding
                try:
                    # Try to decode as JSON
                    return json.loads(data.decode('utf-8'))
                except:
                    # Return raw decoded string
                    return data.decode('utf-8')
        
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds (None to use default)
            
        Returns:
            bool: True if successful
        """
        try:
            full_key = self._make_key(key)
            
            # Use default expiration time if not specified
            if expire is None:
                expire = self.expire_time
            
            # Convert value to storable format
            if isinstance(value, str):
                data = value.encode('utf-8')
            elif isinstance(value, (dict, list, tuple, bool, int, float)) or value is None:
                # Use JSON for simple types
                data = json.dumps(value).encode('utf-8')
            else:
                # Use pickle for complex objects
                data = pickle.dumps(value)
            
            # Store in Redis with expiration
            if expire > 0:
                return bool(self.redis.setex(full_key, expire, data))
            else:
                return bool(self.redis.set(full_key, data))
        
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key was deleted
        """
        try:
            full_key = self._make_key(key)
            return bool(self.redis.delete(full_key))
        
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists
        """
        try:
            full_key = self._make_key(key)
            return bool(self.redis.exists(full_key))
        
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter
        
        Args:
            key: Counter key
            amount: Amount to increment (default: 1)
            
        Returns:
            int: New counter value
        """
        try:
            full_key = self._make_key(key)
            return self.redis.incrby(full_key, amount)
        
        except Exception as e:
            logger.error(f"Error incrementing cache key {key}: {e}")
            return -1
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on a key
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            full_key = self._make_key(key)
            return bool(self.redis.expire(full_key, seconds))
        
        except Exception as e:
            logger.error(f"Error setting expiration for cache key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get time to live for a key
        
        Args:
            key: Cache key
            
        Returns:
            int: Seconds until expiration (-1 if no expiry, -2 if key doesn't exist)
        """
        try:
            full_key = self._make_key(key)
            return self.redis.ttl(full_key)
        
        except Exception as e:
            logger.error(f"Error getting TTL for cache key {key}: {e}")
            return -2
    
    def hset(self, key: str, field: str, value: Any) -> bool:
        """
        Set a hash field
        
        Args:
            key: Hash key
            field: Hash field
            value: Value to set
            
        Returns:
            bool: True if successful
        """
        try:
            full_key = self._make_key(key)
            
            # Convert value to storable format
            if isinstance(value, str):
                data = value
            elif isinstance(value, (dict, list, tuple, bool, int, float)) or value is None:
                # Use JSON for simple types
                data = json.dumps(value)
            else:
                # Use pickle for complex objects (stored as base64 string)
                import base64
                data = base64.b64encode(pickle.dumps(value)).decode('utf-8')
            
            return bool(self.redis.hset(full_key, field, data))
        
        except Exception as e:
            logger.error(f"Error setting hash field {key}.{field}: {e}")
            return False
    
    def hget(self, key: str, field: str, default: Any = None) -> Any:
        """
        Get a hash field
        
        Args:
            key: Hash key
            field: Hash field
            default: Default value if field not found
            
        Returns:
            Any: Field value or default
        """
        try:
            full_key = self._make_key(key)
            data = self.redis.hget(full_key, field)
            
            if data is None:
                return default
            
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            try:
                # Try to decode as JSON
                return json.loads(data)
            except:
                try:
                    # Check if it's a pickled object (stored as base64)
                    if data.startswith("gASV") or (len(data) > 8 and '=' in data[-8:]):
                        import base64
                        return pickle.loads(base64.b64decode(data.encode('utf-8')))
                except:
                    pass
                
                # Return as is
                return data
        
        except Exception as e:
            logger.error(f"Error getting hash field {key}.{field}: {e}")
            return default
    
    def hdel(self, key: str, field: str) -> bool:
        """
        Delete a hash field
        
        Args:
            key: Hash key
            field: Hash field
            
        Returns:
            bool: True if field was deleted
        """
        try:
            full_key = self._make_key(key)
            return bool(self.redis.hdel(full_key, field))
        
        except Exception as e:
            logger.error(f"Error deleting hash field {key}.{field}: {e}")
            return False
    
    def hkeys(self, key: str) -> List[str]:
        """
        Get all hash fields
        
        Args:
            key: Hash key
            
        Returns:
            List[str]: List of field names
        """
        try:
            full_key = self._make_key(key)
            result = self.redis.hkeys(full_key)
            
            # Convert bytes to strings
            if result and isinstance(result[0], bytes):
                return [x.decode('utf-8') for x in result]
            
            return list(result or [])
        
        except Exception as e:
            logger.error(f"Error getting hash fields for {key}: {e}")
            return []
    
    def clear(self) -> bool:
        """
        Clear all keys in the namespace
        
        Returns:
            bool: True if successful
        """
        return self.clear_namespace()
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear keys matching a pattern within the namespace
        
        Args:
            pattern: Key pattern to match (e.g., 'user:*')
            
        Returns:
            int: Number of keys deleted
        """
        try:
            full_pattern = self._make_key(pattern)
            
            # Find all matching keys
            keys = self.redis.keys(full_pattern)
            
            if not keys:
                return 0
            
            # Delete all matching keys
            return self.redis.delete(*keys)
        
        except Exception as e:
            logger.error(f"Error clearing keys with pattern {pattern}: {e}")
            return 0
    
    def clear_namespace(self) -> int:
        """
        Clear all keys within this namespace
        
        Returns:
            int: Number of keys deleted
        """
        return self.clear_pattern("*")
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        try:
            key_count = len(self.redis.keys(self._make_key("*")))
            
            return {
                "namespace": self.namespace,
                "key_count": key_count,
                "default_expire_time": self.expire_time,
            }
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "namespace": self.namespace,
                "key_count": 0,
                "default_expire_time": self.expire_time,
                "error": str(e)
            }
    
    def memoize(self, expire: Optional[int] = None, include_self: bool = False):
        """
        Decorator to memoize a function using Redis
        
        Args:
            expire: Cache expiration time in seconds (None to use default)
            include_self: Whether to include self in the cache key (for methods)
            
        Returns:
            Decorated function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                key_parts = [func.__module__, func.__name__]
                
                # Skip self/cls for methods if not included
                if args and not include_self and key_parts[0] != '__main__':
                    if getattr(args[0].__class__, func.__name__, None) is not None:
                        args = args[1:]
                
                # Add args to key
                for arg in args:
                    key_parts.append(str(arg))
                
                # Add kwargs to key (sorted for consistency)
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}:{v}")
                
                # Create full key
                cache_key = ":".join(key_parts)
                
                # Check cache
                result = self.get(cache_key)
                if result is not None:
                    return result
                
                # Call function
                result = func(*args, **kwargs)
                
                # Cache result
                self.set(cache_key, result, expire)
                
                return result
            
            # Add clear_cache method to the wrapper
            def clear_cache(*args, **kwargs):
                key_parts = [func.__module__, func.__name__]
                if args or kwargs:
                    for arg in args:
                        key_parts.append(str(arg))
                    for k, v in sorted(kwargs.items()):
                        key_parts.append(f"{k}:{v}")
                    cache_key = ":".join(key_parts)
                    self.delete(cache_key)
                else:
                    # Clear all caches for this function
                    pattern = f"{func.__module__}:{func.__name__}:*"
                    self.clear_pattern(pattern)
            
            wrapper.clear_cache = clear_cache
            
            return wrapper
        
        return decorator
    
    def pipeline(self):
        """
        Get a Redis pipeline for batched operations
        
        Returns:
            Redis pipeline object
        """
        try:
            return self.redis.pipeline()
        except Exception as e:
            logger.error(f"Error creating Redis pipeline: {e}")
            return None

# Global cache instances (for convenient access)
_cache_instances = {}

def get_cache(namespace: str = 'cache', expire_time: int = 300) -> RedisCache:
    """
    Get or create a cache instance
    
    Args:
        namespace: Cache namespace
        expire_time: Default expiration time in seconds
        
    Returns:
        RedisCache: Cache instance
    """
    global _cache_instances
    
    cache_key = f"{namespace}:{expire_time}"
    if cache_key not in _cache_instances:
        _cache_instances[cache_key] = RedisCache(namespace, expire_time)
    
    return _cache_instances[cache_key]

def clear_cache(namespace: str = None, pattern: str = None) -> int:
    """
    Clear cache keys
    
    Args:
        namespace: Cache namespace (None to use default)
        pattern: Key pattern to match (e.g., 'user:*')
        
    Returns:
        int: Number of keys deleted
    """
    if namespace is None:
        namespace = 'cache'
    
    cache = get_cache(namespace)
    
    if pattern:
        return cache.clear_pattern(pattern)
    else:
        return cache.clear_namespace()

def memoize(namespace: str = 'cache', expire_time: int = 3600, include_self: bool = False):
    """
    Decorator to memoize a function using Redis
    
    Args:
        namespace: Cache namespace
        expire_time: Expiration time in seconds
        include_self: Whether to include self in the cache key (for methods)
        
    Returns:
        Decorated function
    """
    cache = get_cache(namespace, expire_time)
    return cache.memoize(expire_time, include_self)