"""
API Cache Module

This module provides a Redis-backed caching system for API responses.
It helps reduce load on external APIs and improves response times.
"""

import json
import hashlib
import logging
import time
from functools import wraps
from typing import Any, Dict, Optional, Callable, Union

from redis_cache import RedisCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class ApiCache:
    """
    Redis-backed API response cache
    
    This class provides caching for API responses to reduce load on external APIs.
    It handles serialization, deserialization, and cache invalidation.
    """
    
    def __init__(self, namespace='api_cache', default_ttl=3600):
        """
        Initialize the API cache
        
        Args:
            namespace (str): The namespace for the cache keys
            default_ttl (int): Default time-to-live for cache entries in seconds
        """
        self.namespace = namespace
        self.default_ttl = default_ttl
        self.redis_cache = RedisCache(namespace=namespace, expire_time=default_ttl)
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from function arguments
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            str: A unique cache key
        """
        # Create a string representation of the arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_str = ":".join(key_parts)
        
        # Create a hash of the string for a shorter key
        key_hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()
        
        return key_hash
    
    def _get_cache_key(self, prefix, *args, **kwargs) -> str:
        """
        Get a complete cache key with prefix
        
        Args:
            prefix (str): Key prefix (usually the function name)
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            str: A unique cache key with prefix
        """
        arg_key = self._generate_cache_key(*args, **kwargs)
        return f"{prefix}:{arg_key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache
        
        Args:
            key (str): The cache key
            
        Returns:
            Any: The cached value, or None if the key doesn't exist
        """
        return self.redis_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache
        
        Args:
            key (str): The cache key
            value (Any): The value to cache
            ttl (int, optional): Time-to-live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.redis_cache.set(key, value, expire=ttl or self.default_ttl)
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache
        
        Args:
            key (str): The cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.redis_cache.delete(key)
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern
        
        Args:
            pattern (str): The pattern to match
            
        Returns:
            int: The number of keys deleted
        """
        return self.redis_cache.clear_pattern(pattern)
    
    def cache(self, ttl: Optional[int] = None, prefix: Optional[str] = None, 
              condition: Optional[Callable] = None, skip_cache_if_error: bool = False) -> Callable:
        """
        Decorator for caching function results
        
        Args:
            ttl (int, optional): Time-to-live in seconds
            prefix (str, optional): Key prefix (defaults to function name)
            condition (callable, optional): Function that determines whether to use the cache
            skip_cache_if_error (bool): Whether to skip caching if the function raises an error
            
        Returns:
            callable: Decorated function
        """
        def decorator(func):
            # Use function name as prefix if not specified
            key_prefix = prefix or func.__name__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check if we should use the cache
                use_cache = condition(*args, **kwargs) if condition else True
                
                if not use_cache:
                    return func(*args, **kwargs)
                
                # Generate cache key
                cache_key = self._get_cache_key(key_prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                
                if cached_value is not None:
                    logger.debug(f"Cache hit for {func.__name__}({args}, {kwargs})")
                    return cached_value
                
                # Cache miss, call the function
                logger.debug(f"Cache miss for {func.__name__}({args}, {kwargs})")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Cache the result if not None
                    if result is not None:
                        self.set(cache_key, result, ttl=ttl)
                    
                    return result
                    
                except Exception as e:
                    if skip_cache_if_error:
                        logger.warning(f"Error in {func.__name__}, not caching: {str(e)}")
                        raise
                    else:
                        logger.error(f"Error in {func.__name__}, will still cache the error: {str(e)}")
                        raise
            
            # Add a method to clear the cache for this function
            def clear_cache(*args, **kwargs):
                if args or kwargs:
                    # Clear specific cache entry
                    cache_key = self._get_cache_key(key_prefix, *args, **kwargs)
                    deleted = self.delete(cache_key)
                    logger.debug(f"Cleared cache for {func.__name__}({args}, {kwargs}): {deleted}")
                    return deleted
                else:
                    # Clear all cache entries for this function
                    pattern = f"{key_prefix}:*"
                    count = self.clear_pattern(pattern)
                    logger.debug(f"Cleared {count} cache entries for {func.__name__}")
                    return count
            
            wrapper.clear_cache = clear_cache
            
            return wrapper
        
        return decorator
    
    def timed_cache(self, refresh_after: int, ttl: Optional[int] = None, 
                   prefix: Optional[str] = None) -> Callable:
        """
        Decorator for timed caching - returns cached results for refresh_after seconds,
        then refreshes in the background
        
        Args:
            refresh_after (int): Time in seconds before refreshing the cache in the background
            ttl (int, optional): Time-to-live in seconds (should be greater than refresh_after)
            prefix (str, optional): Key prefix (defaults to function name)
            
        Returns:
            callable: Decorated function
        """
        def decorator(func):
            # Use function name as prefix if not specified
            key_prefix = prefix or func.__name__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache keys for value and timestamp
                cache_key = self._get_cache_key(key_prefix, *args, **kwargs)
                timestamp_key = f"{cache_key}:timestamp"
                
                # Get from cache
                cached_value = self.get(cache_key)
                last_updated = self.get(timestamp_key) or 0
                
                current_time = time.time()
                age = current_time - last_updated
                
                # If we have a cached value
                if cached_value is not None:
                    if age < refresh_after:
                        # Return cached value without refreshing
                        logger.debug(f"Cache hit (fresh) for {func.__name__}({args}, {kwargs})")
                        return cached_value
                    else:
                        # Return cached value but refresh in the background
                        logger.debug(f"Cache hit (stale) for {func.__name__}({args}, {kwargs}), refreshing in background")
                        # In a real application, this would use a background job
                        # For simplicity, we'll just refresh it now
                        try:
                            result = func(*args, **kwargs)
                            self.set(cache_key, result, ttl=ttl or self.default_ttl)
                            self.set(timestamp_key, current_time, ttl=ttl or self.default_ttl)
                            return result
                        except Exception as e:
                            logger.error(f"Error refreshing cache for {func.__name__}: {str(e)}")
                            return cached_value
                
                # Cache miss, call the function
                logger.debug(f"Cache miss for {func.__name__}({args}, {kwargs})")
                
                result = func(*args, **kwargs)
                
                # Cache the result
                self.set(cache_key, result, ttl=ttl or self.default_ttl)
                self.set(timestamp_key, current_time, ttl=ttl or self.default_ttl)
                
                return result
            
            # Add a method to clear the cache for this function
            def clear_cache(*args, **kwargs):
                if args or kwargs:
                    # Clear specific cache entry
                    cache_key = self._get_cache_key(key_prefix, *args, **kwargs)
                    timestamp_key = f"{cache_key}:timestamp"
                    deleted1 = self.delete(cache_key)
                    deleted2 = self.delete(timestamp_key)
                    logger.debug(f"Cleared cache for {func.__name__}({args}, {kwargs}): {deleted1 and deleted2}")
                    return deleted1 and deleted2
                else:
                    # Clear all cache entries for this function
                    pattern = f"{key_prefix}:*"
                    count = self.clear_pattern(pattern)
                    logger.debug(f"Cleared {count} cache entries for {func.__name__}")
                    return count
            
            wrapper.clear_cache = clear_cache
            
            return wrapper
        
        return decorator