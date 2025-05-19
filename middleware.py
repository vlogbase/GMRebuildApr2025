"""
Middleware for GloriaMundo Chatbot

This module contains middleware functions that can be applied to the Flask application
to provide additional functionality like rate limiting.
"""

import time
import logging
from functools import wraps
from flask import request, jsonify, g, current_app
from redis_cache import redis_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Middleware")

def setup_rate_limiting(app):
    """
    Configure rate limiting for the application.
    
    Args:
        app: Flask application to configure
    """
    @app.before_request
    def rate_limit_middleware():
        """
        Rate limiting middleware that runs before each request.
        Uses Redis to track and limit requests based on user ID or IP.
        """
        # Skip rate limiting for some routes
        if should_skip_rate_limiting():
            return None
            
        # Check if Redis is available
        if not redis_cache.is_available():
            logger.warning("Redis not available for rate limiting. Allowing request.")
            return None
            
        # Get user ID or IP address for rate limiting
        from flask_login import current_user
        if current_user.is_authenticated:
            # Use user ID for authenticated users
            key = f"ratelimit:user:{current_user.id}:{request.endpoint}"
            max_requests = get_authenticated_user_rate_limit(request.endpoint)
        else:
            # Use IP address for anonymous users
            key = f"ratelimit:ip:{request.remote_addr}:{request.endpoint}"
            max_requests = get_anonymous_user_rate_limit(request.endpoint)
            
        # Get current period (1 minute)
        period = 60
        current = int(time.time())
        window_key = f"{key}:{current // period}"
        
        # Get current count
        count = redis_cache.get(window_key)
        count = int(count) if count is not None else 0
        
        # Calculate reset time and remaining requests
        reset = (current // period + 1) * period
        remaining = max(0, max_requests - count)
        
        # Store rate limit info in Flask g object for response headers
        g.rate_limit_info = {
            'limit': max_requests,
            'remaining': remaining,
            'reset': reset
        }
        
        # Check if rate limited
        if count >= max_requests:
            logger.warning(f"Rate limit exceeded for {key}. Count: {count}/{max_requests}")
            response = jsonify({
                'error': 'Too many requests',
                'message': f'Rate limit of {max_requests} requests per minute exceeded. Try again in {reset - current} seconds.'
            })
            response.status_code = 429
            response.headers['X-RateLimit-Limit'] = str(max_requests)
            response.headers['X-RateLimit-Remaining'] = '0'
            response.headers['X-RateLimit-Reset'] = str(reset)
            return response
            
        # Increment counter
        try:
            redis_cache.setex(window_key, period, count + 1)
        except Exception as e:
            logger.error(f"Error incrementing rate limit counter: {e}")
            # Don't block the request if Redis fails
            
        return None
        
    @app.after_request
    def add_rate_limit_headers(response):
        """Add rate limit headers to responses"""
        if hasattr(g, 'rate_limit_info'):
            info = g.rate_limit_info
            response.headers['X-RateLimit-Limit'] = str(info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
            response.headers['X-RateLimit-Reset'] = str(info['reset'])
        return response

def should_skip_rate_limiting():
    """
    Determine if rate limiting should be skipped for the current request.
    
    Returns:
        bool: True if rate limiting should be skipped
    """
    # Skip static files and certain endpoints
    if request.path.startswith('/static/'):
        return True
        
    # Skip OPTIONS requests
    if request.method == 'OPTIONS':
        return True
        
    # Skip health check and non-API endpoints
    skip_endpoints = ['health', 'index', 'login']
    if request.endpoint in skip_endpoints:
        return True
        
    return False

def get_authenticated_user_rate_limit(endpoint):
    """
    Get rate limit for authenticated users based on endpoint.
    
    Args:
        endpoint: Flask endpoint name
    
    Returns:
        int: Maximum requests per minute
    """
    # Higher limits for authenticated users
    limits = {
        'chat': 20,  # 20 requests per minute for chat
        'upload_file': 10,  # 10 uploads per minute
        'get_model_pricing': 30,  # 30 requests per minute for pricing
        'get_models': 30  # 30 requests per minute for models list
    }
    
    # Default limit for other endpoints
    return limits.get(endpoint, 60)  # Default: 60 per minute (1 per second)

def get_anonymous_user_rate_limit(endpoint):
    """
    Get rate limit for anonymous users based on endpoint.
    
    Args:
        endpoint: Flask endpoint name
    
    Returns:
        int: Maximum requests per minute
    """
    # Lower limits for anonymous users
    limits = {
        'chat': 5,  # 5 requests per minute for chat
        'upload_file': 3,  # 3 uploads per minute
        'get_model_pricing': 10,  # 10 requests per minute for pricing
        'get_models': 10  # 10 requests per minute for models list
    }
    
    # Default limit for other endpoints
    return limits.get(endpoint, 30)  # Default: 30 per minute (1 per 2 seconds)