"""
Redis Rate Limiter Module

This module provides a Redis-backed rate limiter for API endpoints.
It allows for IP-based and user-based rate limiting to prevent API abuse.
"""

import time
import logging
from flask import request, g
from functools import wraps

from redis_cache import get_redis_connection, RedisCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class RedisRateLimiter:
    """
    Redis-backed rate limiter for API endpoints
    
    This class provides rate limiting functionality backed by Redis.
    It supports both IP-based and user-based rate limiting.
    """
    
    def __init__(self, key_prefix='rate_limit', default_limit=60, default_window=60):
        """
        Initialize the rate limiter
        
        Args:
            key_prefix (str): Prefix for Redis keys
            default_limit (int): Default number of requests allowed per window
            default_window (int): Default window size in seconds
        """
        self.key_prefix = key_prefix
        self.default_limit = default_limit
        self.default_window = default_window
        self.redis_cache = RedisCache(namespace=key_prefix, expire_time=86400)  # 1 day
    
    def _get_rate_limit_key(self, key_type, identifier):
        """
        Get the Redis key for a rate limit
        
        Args:
            key_type (str): Type of rate limit (e.g., 'ip', 'user')
            identifier (str): Identifier (e.g., IP address, user ID)
            
        Returns:
            str: Rate limit key
        """
        return f"{key_type}:{identifier}"
    
    def check_rate_limit(self, key_type, identifier, limit=None, window=None):
        """
        Check if a request is within the rate limit
        
        Args:
            key_type (str): Type of rate limit (e.g., 'ip', 'user')
            identifier (str): Identifier (e.g., IP address, user ID)
            limit (int, optional): Number of requests allowed per window
            window (int, optional): Window size in seconds
            
        Returns:
            tuple: (allowed, remaining, reset_time)
        """
        limit = limit or self.default_limit
        window = window or self.default_window
        
        # Get the current time
        current_time = int(time.time())
        
        # Create a key for this rate limit
        rate_limit_key = self._get_rate_limit_key(key_type, identifier)
        
        # Get the current window start time
        window_key = f"{rate_limit_key}:window"
        window_start = self.redis_cache.get(window_key)
        
        if window_start is None:
            # No window exists, create a new one
            window_start = current_time
            self.redis_cache.set(window_key, window_start, expire=window + 10)
            
            # Reset the counter
            counter_key = f"{rate_limit_key}:counter"
            self.redis_cache.set(counter_key, 0, expire=window + 10)
        
        # Calculate when the window resets
        reset_time = window_start + window
        
        # If the current time is past the reset time, start a new window
        if current_time > reset_time:
            window_start = current_time
            self.redis_cache.set(window_key, window_start, expire=window + 10)
            
            # Reset the counter
            counter_key = f"{rate_limit_key}:counter"
            self.redis_cache.set(counter_key, 0, expire=window + 10)
            
            # Calculate new reset time
            reset_time = window_start + window
        
        # Get the current count
        counter_key = f"{rate_limit_key}:counter"
        count = self.redis_cache.get(counter_key) or 0
        
        # Check if the limit has been reached
        allowed = count < limit
        
        # Increment the counter if allowed
        if allowed:
            count = self.redis_cache.incr(counter_key)
            allowed = count <= limit  # Check again after incrementing
        
        # Calculate remaining requests
        remaining = max(0, limit - count)
        
        return (allowed, remaining, reset_time)
    
    def limit_by_ip(self, limit=None, window=None):
        """
        Create a decorator that limits requests by IP address
        
        Args:
            limit (int, optional): Number of requests allowed per window
            window (int, optional): Window size in seconds
            
        Returns:
            function: Decorator function
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get the client IP
                ip = request.remote_addr
                
                # Check rate limit
                allowed, remaining, reset_time = self.check_rate_limit('ip', ip, limit, window)
                
                # Store rate limit info in g for use in the response
                g.rate_limit_info = {
                    'limit': limit or self.default_limit,
                    'remaining': remaining,
                    'reset': reset_time
                }
                
                if not allowed:
                    response = {
                        'error': 'Rate limit exceeded',
                        'limit': limit or self.default_limit,
                        'remaining': 0,
                        'reset': reset_time
                    }
                    return response, 429  # Too Many Requests
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def limit_by_user(self, limit=None, window=None):
        """
        Create a decorator that limits requests by user ID
        
        Args:
            limit (int, optional): Number of requests allowed per window
            window (int, optional): Window size in seconds
            
        Returns:
            function: Decorator function
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get the user ID from the global context
                # This assumes you have g.user.id available from your authentication system
                if not hasattr(g, 'user') or not g.user:
                    # Fall back to IP-based limiting if no user is available
                    return self.limit_by_ip(limit, window)(f)(*args, **kwargs)
                
                user_id = g.user.id
                
                # Check rate limit
                allowed, remaining, reset_time = self.check_rate_limit('user', user_id, limit, window)
                
                # Store rate limit info in g for use in the response
                g.rate_limit_info = {
                    'limit': limit or self.default_limit,
                    'remaining': remaining,
                    'reset': reset_time
                }
                
                if not allowed:
                    response = {
                        'error': 'Rate limit exceeded',
                        'limit': limit or self.default_limit,
                        'remaining': 0,
                        'reset': reset_time
                    }
                    return response, 429  # Too Many Requests
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def get_rate_limit_headers(self):
        """
        Get HTTP headers with rate limit information
        
        Returns:
            dict: HTTP headers
        """
        headers = {}
        
        if hasattr(g, 'rate_limit_info'):
            info = g.rate_limit_info
            headers['X-RateLimit-Limit'] = str(info['limit'])
            headers['X-RateLimit-Remaining'] = str(info['remaining'])
            headers['X-RateLimit-Reset'] = str(info['reset'])
        
        return headers
    
    def apply_rate_limit_headers(self, response):
        """
        Apply rate limit headers to a response
        
        Args:
            response: Flask response object
            
        Returns:
            response: Modified response object
        """
        headers = self.get_rate_limit_headers()
        
        for key, value in headers.items():
            response.headers[key] = value
        
        return response