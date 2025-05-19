"""
Redis Cache Module for GloriaMundo Chatbot

This module provides Redis caching functionality to improve application performance.
It handles connections to Redis and offers functions for storing and retrieving cached data.
"""

import os
import logging
import json
import pickle
import time
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta

import redis
from redis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RedisCache")

class RedisCache:
    """
    Redis cache manager for the application.
    
    This class provides a centralized way to interact with Redis for caching.
    It handles connection management, serialization/deserialization, and offers
    convenient methods for common caching operations.
    """
    
    def __init__(self, connection_pool=None):
        """
        Initialize the Redis cache manager.
        
        Args:
            connection_pool: Optional existing Redis connection pool
        """
        self.redis_client = None
        self.connection_pool = connection_pool
        self.initialized = False
        
        # Try to initialize the Redis client
        self._initialize_redis()
        
    def _initialize_redis(self):
        """Initialize the Redis client with environment variables."""
        try:
            # If we already have a connection pool, use it
            if self.connection_pool:
                self.redis_client = redis.Redis(connection_pool=self.connection_pool)
                logger.info("Using existing Redis connection pool")
                self.initialized = True
                return
            
            # Get Redis connection parameters from environment
            redis_host = os.environ.get("REDIS_HOST")
            redis_port = int(os.environ.get("REDIS_PORT", 6380))
            redis_password = os.environ.get("REDIS_PASSWORD")
            use_ssl = os.environ.get("REDIS_SSL", "true").lower() == "true"
            
            if not redis_host or not redis_password:
                logger.warning("Redis not fully configured. Missing host or password.")
                self.initialized = False
                return
                
            # For Azure Redis Cache, create a direct connection
            import ssl
            logger.info(f"Connecting to Redis at {redis_host}:{redis_port}")
            
            try:
                # Azure Redis Cache requires SSL and specific parameters
                import urllib.parse
                
                # URL-encode password for special characters
                encoded_password = urllib.parse.quote_plus(redis_password)
                
                # Build connection URL with SSL (rediss://)
                connection_string = f"rediss://:{encoded_password}@{redis_host}:{redis_port}"
                logger.info(f"Connecting to Redis using URL: {connection_string.replace(encoded_password, '***')}")
                
                # Create Redis client using URL approach
                self.redis_client = redis.from_url(
                    url=connection_string,
                    socket_timeout=10,
                    socket_connect_timeout=5,
                    ssl_cert_reqs=ssl.CERT_NONE  # Don't verify certificate
                )
            except Exception as e:
                logger.error(f"Error creating Redis client: {e}")
                self.initialized = False
                return
            
            # Store the connection pool for future reference
            self.connection_pool = self.redis_client.connection_pool
            
            # Test the connection
            self.redis_client.ping()
            logger.info(f"Successfully connected to Redis at {redis_host}:{redis_port}")
            self.initialized = True
            
        except RedisError as e:
            logger.error(f"Redis connection error: {e}")
            self.initialized = False
        except Exception as e:
            logger.error(f"Error initializing Redis cache: {e}")
            self.initialized = False
    
    def is_available(self) -> bool:
        """Check if Redis is available and connected."""
        if not self.initialized or not self.redis_client:
            return False
            
        try:
            return self.redis_client.ping()
        except:
            return False
            
    def get_redis(self):
        """
        Get the underlying Redis client instance.
        
        This is useful when direct Redis client access is needed,
        such as for RQ worker configuration.
        
        Returns:
            redis.Redis: The Redis client instance, or None if not available
        """
        if not self.is_available():
            return None
        return self.redis_client
    
    def get(self, key: str, default=None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default if not found
        """
        if not self.is_available():
            return default
            
        try:
            data = self.redis_client.get(key)
            if data is None:
                return default
                
            # Try to unpickle the data
            try:
                return pickle.loads(data)
            except:
                # If unpickling fails, return raw data
                return data
                
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set a value in the cache with optional time-to-live.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            return False
            
        try:
            # Pickle the value for proper serialization
            pickled_value = pickle.dumps(value)
            
            if ttl is not None:
                return self.redis_client.setex(key, ttl, pickled_value)
            else:
                return self.redis_client.set(key, pickled_value)
                
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            return False
            
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        if not self.is_available():
            return False
            
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking if key {key} exists in Redis: {e}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a key's value and return the new value.
        
        Args:
            key: Cache key to increment
            amount: Amount to increment by (default: 1)
            
        Returns:
            int: New value or None if operation failed
        """
        if not self.is_available():
            return None
            
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key} in Redis: {e}")
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            return False
            
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Error setting expiration for key {key} in Redis: {e}")
            return False
    
    def ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining time to live for a key.
        
        Args:
            key: Cache key
            
        Returns:
            int: TTL in seconds or None if error
        """
        if not self.is_available():
            return None
            
        try:
            ttl = self.redis_client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Error getting TTL for key {key} from Redis: {e}")
            return None
    
    def hash_set(self, name: str, key: str, value: Any) -> bool:
        """
        Set a hash field to a value.
        
        Args:
            name: Hash name
            key: Field name
            value: Field value
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            return False
            
        try:
            # Pickle the value for proper serialization
            pickled_value = pickle.dumps(value)
            return bool(self.redis_client.hset(name, key, pickled_value))
        except Exception as e:
            logger.error(f"Error setting hash field {name}.{key} in Redis: {e}")
            return False
    
    def hash_get(self, name: str, key: str, default=None) -> Any:
        """
        Get the value of a hash field.
        
        Args:
            name: Hash name
            key: Field name
            default: Default value if field not found
            
        Returns:
            Field value or default if not found
        """
        if not self.is_available():
            return default
            
        try:
            data = self.redis_client.hget(name, key)
            if data is None:
                return default
                
            # Try to unpickle the data
            try:
                return pickle.loads(data)
            except:
                # If unpickling fails, return raw data
                return data
                
        except Exception as e:
            logger.error(f"Error getting hash field {name}.{key} from Redis: {e}")
            return default
    
    def hash_delete(self, name: str, key: str) -> bool:
        """
        Delete a hash field.
        
        Args:
            name: Hash name
            key: Field name
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            return False
            
        try:
            return bool(self.redis_client.hdel(name, key))
        except Exception as e:
            logger.error(f"Error deleting hash field {name}.{key} from Redis: {e}")
            return False
    
    def hash_keys(self, name: str) -> List[str]:
        """
        Get all the fields in a hash.
        
        Args:
            name: Hash name
            
        Returns:
            List of field names
        """
        if not self.is_available():
            return []
            
        try:
            keys = self.redis_client.hkeys(name)
            return [k.decode('utf-8') if isinstance(k, bytes) else k for k in keys]
        except Exception as e:
            logger.error(f"Error getting hash keys for {name} from Redis: {e}")
            return []
    
    def flush(self) -> bool:
        """
        Flush the entire Redis database.
        Warning: This will remove all keys from the database!
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            return False
            
        try:
            logger.warning("Flushing entire Redis database!")
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error flushing Redis database: {e}")
            return False
    
    def key_prefix_delete(self, prefix: str) -> int:
        """
        Delete all keys matching a prefix.
        
        Args:
            prefix: Key prefix to match
            
        Returns:
            int: Number of keys deleted
        """
        if not self.is_available():
            return 0
            
        try:
            # Get all keys matching the pattern
            keys = self.redis_client.keys(f"{prefix}*")
            if not keys:
                return 0
                
            # Delete all matching keys
            return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting keys with prefix {prefix} from Redis: {e}")
            return 0
    
    def key_pattern_delete(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (using Redis glob-style pattern)
            
        Returns:
            int: Number of keys deleted
        """
        if not self.is_available():
            return 0
            
        try:
            # Get all keys matching the pattern
            keys = self.redis_client.keys(pattern)
            if not keys:
                return 0
                
            # Delete all matching keys
            return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting keys with pattern {pattern} from Redis: {e}")
            return 0
    
    def pipeline(self) -> Optional[redis.client.Pipeline]:
        """
        Get a Redis pipeline for batch operations.
        
        Returns:
            Pipeline object or None if Redis is not available
        """
        if not self.is_available():
            return None
            
        try:
            return self.redis_client.pipeline()
        except Exception as e:
            logger.error(f"Error creating Redis pipeline: {e}")
            return None
    
    def cache_decorator(self, prefix: str, ttl: int = 3600):
        """
        Decorator to cache function results in Redis.
        
        Args:
            prefix: Prefix for cache keys
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            Decorated function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Skip caching if Redis is not available
                if not self.is_available():
                    return func(*args, **kwargs)
                
                # Create a cache key based on function args and kwargs
                key_parts = [prefix, func.__name__]
                
                # Add string representation of args and kwargs to key
                for arg in args:
                    key_parts.append(str(arg))
                
                # Add sorted kwargs to ensure consistent key ordering
                sorted_kwargs = sorted(kwargs.items())
                for k, v in sorted_kwargs:
                    key_parts.append(f"{k}={v}")
                
                cache_key = ":".join(key_parts)
                
                # Try to get from cache first
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Call the function and cache the result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

# Create a singleton instance for global use
redis_cache = RedisCache()

# Flush the cache on startup if environment variable is set
if os.environ.get("REDIS_FLUSH_ON_STARTUP", "false").lower() == "true":
    if redis_cache.is_available():
        logger.warning("Flushing Redis cache on startup...")
        redis_cache.flush()
        logger.info("Redis cache flushed successfully")