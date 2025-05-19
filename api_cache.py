"""
API Cache Module

This module provides Redis-backed caching for API responses,
optimizing performance for repetitive API calls and reducing
the load on external services.
"""

import json
import hashlib
import logging
import time
from functools import wraps
from typing import Dict, Any, Optional, Callable, TypeVar, List, Union

from flask import Flask, request, g
from werkzeug.local import LocalProxy

from redis_cache import RedisCache, handle_redis_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type vars for better typing support
ResponseT = TypeVar('ResponseT')

class ApiCache:
    """Redis-backed API cache for optimizing API responses"""
    
    def __init__(self, namespace: str = 'api_cache:', 
                 default_ttl: int = 3600,
                 model_ttl_map: Optional[Dict[str, int]] = None):
        """
        Initialize the API cache
        
        Args:
            namespace: Redis key namespace
            default_ttl: Default TTL for cached responses in seconds
            model_ttl_map: Optional mapping of model names to TTL values
        """
        self.namespace = namespace
        self.default_ttl = default_ttl
        self.redis = RedisCache(namespace=namespace, expire_time=default_ttl)
        
        # Model-specific TTL settings (for model API responses)
        self.model_ttl_map = model_ttl_map or {
            # Default TTLs for different model types (in seconds)
            'embedding': 86400,       # Embedding models: 24 hours
            'text-generation': 1800,  # Text generation models: 30 minutes
            'vision': 3600,           # Vision models: 1 hour
            'chat': 1800,             # Chat models: 30 minutes
            
            # Specific model overrides
            'claude-3-opus': 3600,    # Claude 3 Opus: 1 hour
            'claude-3-sonnet': 3600,  # Claude 3 Sonnet: 1 hour
            'claude-3-haiku': 1800,   # Claude 3 Haiku: 30 minutes
            'gpt-4': 3600,            # GPT-4: 1 hour
            'gpt-3.5-turbo': 1800,    # GPT-3.5 Turbo: 30 minutes
        }
        
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key based on function arguments
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            str: Cache key
        """
        # Start with the base key
        key_parts = []
        
        # Add positional args
        for arg in args:
            try:
                # Convert to JSON string
                arg_str = json.dumps(arg, sort_keys=True)
                key_parts.append(arg_str)
            except (TypeError, ValueError):
                # If not JSON serializable, use string representation
                key_parts.append(str(arg))
                
        # Add keyword args (sorted to ensure consistent keys)
        for k in sorted(kwargs.keys()):
            try:
                # Convert to JSON string
                kwarg_str = json.dumps(kwargs[k], sort_keys=True)
                key_parts.append(f"{k}:{kwarg_str}")
            except (TypeError, ValueError):
                # If not JSON serializable, use string representation
                key_parts.append(f"{k}:{str(kwargs[k])}")
                
        # Join parts and hash
        combined = '-'.join(key_parts)
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def _get_ttl_for_model(self, model_name: Optional[str] = None, 
                           model_type: Optional[str] = None) -> int:
        """
        Get the appropriate TTL for a model
        
        Args:
            model_name: Optional model name
            model_type: Optional model type
            
        Returns:
            int: TTL in seconds
        """
        # Use exact model name if specified and in our map
        if model_name and model_name.lower() in self.model_ttl_map:
            return self.model_ttl_map[model_name.lower()]
            
        # Use model type if specified and in our map
        if model_type and model_type.lower() in self.model_ttl_map:
            return self.model_ttl_map[model_type.lower()]
            
        # Default TTL
        return self.default_ttl
    
    def cache_api_call(self, ttl: Optional[int] = None, 
                       model_param: Optional[str] = None,
                       skip_cache_condition: Optional[Callable] = None):
        """
        Decorator for caching API calls
        
        Args:
            ttl: Optional TTL override in seconds
            model_param: Optional parameter name that contains the model name/type
            skip_cache_condition: Optional function that returns True if caching should be skipped
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check if we should skip caching
                if skip_cache_condition and skip_cache_condition(*args, **kwargs):
                    return func(*args, **kwargs)
                
                # Determine appropriate TTL
                cache_ttl = ttl or self.default_ttl
                
                # If model param is provided, try to extract model info and use appropriate TTL
                if model_param and model_param in kwargs:
                    model_value = kwargs[model_param]
                    cache_ttl = self._get_ttl_for_model(model_name=model_value)
                
                # Generate cache key
                cache_key = self._generate_cache_key(*args, **kwargs)
                
                # Try to get from cache
                cached_result = self.redis.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_result
                
                # Call the original function
                result = func(*args, **kwargs)
                
                # Cache the result
                self.redis.set(cache_key, result, expire=cache_ttl)
                logger.debug(f"Cached result with key: {cache_key}, TTL: {cache_ttl}s")
                
                return result
            
            # Add a method to clear the cache for this function
            wrapper.clear_cache = lambda: self.redis.flush()
            
            return wrapper
        
        return decorator
    
    def cache_api_response(self, ttl: Optional[int] = None, 
                          model_param: Optional[str] = None,
                          key_extractor: Optional[Callable] = None,
                          skip_cache_condition: Optional[Callable] = None):
        """
        Decorator for caching API responses with more flexible key generation
        
        Args:
            ttl: Optional TTL override in seconds
            model_param: Optional parameter name that contains the model name/type
            key_extractor: Optional function to extract custom cache key components
            skip_cache_condition: Optional function that returns True if caching should be skipped
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check if we should skip caching
                if skip_cache_condition and skip_cache_condition(*args, **kwargs):
                    return func(*args, **kwargs)
                
                # Extract custom key components if provided
                custom_key = None
                if key_extractor:
                    try:
                        custom_key = key_extractor(*args, **kwargs)
                    except Exception as e:
                        logger.error(f"Error extracting cache key: {str(e)}")
                
                # Generate cache key
                if custom_key:
                    cache_key = hashlib.md5(str(custom_key).encode('utf-8')).hexdigest()
                else:
                    cache_key = self._generate_cache_key(*args, **kwargs)
                
                # Determine appropriate TTL
                cache_ttl = ttl or self.default_ttl
                
                # If model param is provided, try to extract model info and use appropriate TTL
                if model_param and model_param in kwargs:
                    model_value = kwargs[model_param]
                    cache_ttl = self._get_ttl_for_model(model_name=model_value)
                
                # Try to get from cache
                cached_result = self.redis.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_result
                
                # Start timing the API call
                start_time = time.time()
                
                # Call the original function
                result = func(*args, **kwargs)
                
                # Calculate API call duration
                duration = time.time() - start_time
                logger.debug(f"API call took {duration:.3f}s")
                
                # Cache the result
                self.redis.set(cache_key, result, expire=cache_ttl)
                logger.debug(f"Cached API response with key: {cache_key}, TTL: {cache_ttl}s")
                
                return result
            
            # Add a method to clear the cache for this function
            wrapper.clear_cache = lambda: self.redis.flush()
            
            return wrapper
        
        return decorator

# Global API cache instance
_api_cache = None

def get_api_cache() -> ApiCache:
    """
    Get or create the global API cache instance
    
    Returns:
        ApiCache: API cache instance
    """
    global _api_cache
    if _api_cache is None:
        _api_cache = ApiCache()
    return _api_cache

# Create a LocalProxy for the API cache for easy access in Flask
api_cache = LocalProxy(get_api_cache)

def init_api_cache(app: Flask, namespace: str = 'api_cache:', 
                  default_ttl: int = 3600,
                  model_ttl_map: Optional[Dict[str, int]] = None) -> ApiCache:
    """
    Initialize the API cache for a Flask application
    
    Args:
        app: Flask application
        namespace: Redis key namespace
        default_ttl: Default TTL for cached responses in seconds
        model_ttl_map: Optional mapping of model names to TTL values
        
    Returns:
        ApiCache: The initialized API cache instance
    """
    global _api_cache
    _api_cache = ApiCache(
        namespace=namespace,
        default_ttl=default_ttl,
        model_ttl_map=model_ttl_map
    )
    
    # Add the API cache to the app extensions
    app.extensions['api_cache'] = _api_cache
    
    logger.info("API cache initialized")
    return _api_cache