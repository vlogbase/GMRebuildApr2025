"""
Redis Rate Limiter for GloriaMundo Chatbot

This module provides rate limiting functionality using Redis to track
and limit requests based on various criteria (user ID, IP address, etc.)
"""

import time
import logging
from functools import wraps
from flask import request, jsonify, current_app
from redis_cache import redis_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RateLimiter")

class RateLimiter:
    """
    Rate limiter class that uses Redis to track and limit requests.
    This enables distributed rate limiting across multiple application instances.
    """
    
    def __init__(self, redis_client=None):
        """Initialize the rate limiter with Redis client"""
        self.redis = redis_client or redis_cache
        
    def is_rate_limited(self, key, max_requests, period, increment=1):
        """
        Check if a request should be rate limited.
        
        Args:
            key: The unique key for rate limiting (e.g., 'ip:{ip}', 'user:{id}')
            max_requests: Maximum number of requests allowed in the period
            period: Time period in seconds
            increment: Amount to increment the counter (default: 1)
            
        Returns:
            tuple: (is_limited, remaining, reset_time)
        """
        if not self.redis.is_available():
            logger.warning("Redis not available for rate limiting. Allowing request.")
            return False, max_requests, 0
            
        current = int(time.time())
        window_key = f"ratelimit:{key}:{current // period}"
        
        # Get current count (if exists)
        count = self.redis.get(window_key)
        count = int(count) if count else 0
        
        # Calculate reset time
        reset = (current // period + 1) * period
        
        # Calculate remaining
        remaining = max(0, max_requests - count)
        
        # Check if rate limited
        if count >= max_requests:
            logger.warning(f"Rate limit exceeded for {key}. Count: {count}/{max_requests}")
            return True, remaining, reset
            
        # Increment counter in a pipeline
        try:
            # Set the key with expiration
            self.redis.setex(window_key, period, count + increment)
            return False, remaining - increment, reset
        except Exception as e:
            logger.error(f"Error incrementing rate limit counter: {e}")
            # Fail open to avoid blocking legitimate traffic if Redis fails
            return False, max_requests, 0

# Create a global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(requests_per_period, period, key_function=None):
    """
    Decorator for rate limiting Flask routes.
    
    Args:
        requests_per_period: Number of requests allowed per period
        period: Time period in seconds
        key_function: Function to generate unique key (default: user ID or IP)
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate rate limit key
            if key_function:
                key = key_function()
            else:
                # Default: use user ID if authenticated, IP otherwise
                from flask_login import current_user
                if current_user.is_authenticated:
                    key = f"user:{current_user.id}"
                else:
                    key = f"ip:{request.remote_addr}"
            
            # Check rate limit
            limited, remaining, reset = rate_limiter.is_rate_limited(
                key, requests_per_period, period
            )
            
            # Set rate limit headers
            response = current_app.make_response(f(*args, **kwargs))
            response.headers['X-RateLimit-Limit'] = str(requests_per_period)
            response.headers['X-RateLimit-Remaining'] = str(remaining)
            response.headers['X-RateLimit-Reset'] = str(reset)
            
            # If rate limited, return 429 Too Many Requests
            if limited:
                body = {
                    'error': 'Too many requests',
                    'message': f'Rate limit of {requests_per_period} requests per {period} seconds exceeded.',
                    'remaining': remaining,
                    'reset': reset
                }
                return jsonify(body), 429, response.headers
                
            return response
        return decorated_function
    return decorator