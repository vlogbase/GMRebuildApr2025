"""
API Cache Module for GloriaMundo Chatbot

This module provides caching functionality for API responses to improve performance
and reduce load on external services like OpenRouter, Azure OpenAI, etc.
"""

import time
import json
import hashlib
import logging
from functools import wraps
from typing import Any, Dict, List, Optional, Union, Callable

from redis_cache import redis_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ApiCache")

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key based on function arguments.
    
    Args:
        prefix: Prefix for the key
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        str: Cache key
    """
    # Convert args and kwargs to a string representation
    key_parts = [prefix]
    
    # Add string representation of args
    for arg in args:
        if arg is None:
            key_parts.append("None")
        elif isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, (list, tuple, set)):
            key_parts.append(','.join(str(x) for x in arg))
        elif isinstance(arg, dict):
            # Sort dict keys for consistent hashing
            sorted_items = sorted(arg.items())
            key_parts.append(','.join(f"{k}={v}" for k, v in sorted_items))
        else:
            # For complex objects, use their string representation
            key_parts.append(str(arg))
    
    # Add sorted kwargs for consistent key generation
    sorted_kwargs = sorted(kwargs.items())
    for k, v in sorted_kwargs:
        if v is None:
            key_parts.append(f"{k}=None")
        elif isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")
        elif isinstance(v, (list, tuple, set)):
            key_parts.append(f"{k}={','.join(str(x) for x in v)}")
        elif isinstance(v, dict):
            # Hash the dictionary content for complex nested structures
            dict_str = json.dumps(v, sort_keys=True)
            dict_hash = hashlib.md5(dict_str.encode()).hexdigest()
            key_parts.append(f"{k}={dict_hash}")
        else:
            # For complex objects, use their string representation
            key_parts.append(f"{k}={str(v)}")
    
    # Join all parts with colon
    key_base = ":".join(key_parts)
    
    # For very long keys, create a hash
    if len(key_base) > 250:
        return f"{prefix}:hash:{hashlib.md5(key_base.encode()).hexdigest()}"
    
    return key_base

def cache_api_response(prefix: str, ttl: int = 3600):
    """
    Decorator to cache API responses in Redis.
    
    Args:
        prefix: Prefix for cache keys
        ttl: Time to live in seconds (default: 1 hour)
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if Redis is not available or if force_refresh is True
            force_refresh = kwargs.pop('force_refresh', False)
            
            if not redis_cache.is_available() or force_refresh:
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache first
            cached_value = redis_cache.get(cache_key)
            if cached_value is not None:
                logger.info(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss - call the function
            logger.info(f"Cache miss for {cache_key}")
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            # Cache the result
            if result is not None:
                redis_cache.set(cache_key, result, ttl)
                logger.info(f"Cached response for {cache_key} (took {elapsed:.2f}s)")
            
            return result
        return wrapper
    return decorator

def cache_model_pricing(ttl: int = 10800):  # Default: 3 hours
    """
    Specific decorator for caching model pricing information.
    Uses a dedicated prefix and expiration time.
    
    Args:
        ttl: Time to live in seconds (default: 3 hours)
    
    Returns:
        Decorated function
    """
    return cache_api_response("model_pricing", ttl)

def cache_openrouter_response(ttl: int = 3600):  # Default: 1 hour
    """
    Specific decorator for caching OpenRouter API responses.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
    
    Returns:
        Decorated function
    """
    return cache_api_response("openrouter", ttl)

def cache_azure_response(ttl: int = 3600):  # Default: 1 hour
    """
    Specific decorator for caching Azure OpenAI API responses.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
    
    Returns:
        Decorated function
    """
    return cache_api_response("azure_openai", ttl)

def clear_api_cache(prefix: str = None) -> int:
    """
    Clear all API response caches or just those with a specific prefix.
    
    Args:
        prefix: Optional prefix to limit which keys are cleared
    
    Returns:
        int: Number of keys deleted
    """
    if not redis_cache.is_available():
        logger.warning("Redis not available. Cannot clear API cache.")
        return 0
    
    pattern = f"{prefix}:*" if prefix else "model_pricing:*|openrouter:*|azure_openai:*"
    deleted = redis_cache.key_pattern_delete(pattern)
    logger.info(f"Cleared {deleted} keys from API cache with pattern {pattern}")
    return deleted