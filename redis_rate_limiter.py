"""
Redis Rate Limiter Module

This module provides a Redis-backed rate limiting implementation for Flask applications.
It allows for flexible rate limits based on user authentication status,
request path, and client IP address.
"""

import time
import logging
from functools import wraps
from typing import Dict, Optional, List, Union, Callable, Any
import ipaddress

from flask import Flask, request, jsonify, g
from werkzeug.local import LocalProxy

from redis_cache import RedisCache, get_redis_connection, handle_redis_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default rate limits (requests per minute)
DEFAULT_RATE_LIMITS = {
    # Authenticated users
    'auth': {
        'chat': 20,    # Chat API endpoints
        'upload': 10,  # File upload endpoints
        'model': 30,   # Model-related endpoints
        'default': 60  # All other endpoints
    },
    # Anonymous users
    'anon': {
        'chat': 5,     # Chat API endpoints
        'upload': 3,   # File upload endpoints
        'model': 10,   # Model-related endpoints
        'default': 30  # All other endpoints
    }
}

class RedisRateLimiter:
    """Redis-backed rate limiter for Flask applications"""
    
    def __init__(self, namespace: str = 'rate_limit:', expire_time: int = 60):
        """
        Initialize the rate limiter
        
        Args:
            namespace: Redis key namespace for rate limit data
            expire_time: Default expiration time in seconds for rate limit windows
        """
        self.namespace = namespace
        self.expire_time = expire_time
        self.redis = RedisCache(namespace=namespace, expire_time=expire_time)
        self.client_ip = None
        self.rate_limits = DEFAULT_RATE_LIMITS
        
    def get_client_ip(self) -> str:
        """
        Get the client IP address from the request
        
        Returns:
            str: Client IP address
        """
        # Check for X-Forwarded-For header
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Use the first IP in the list (client IP)
            return forwarded_for.split(',')[0].strip()
            
        # Fall back to remote_addr
        return request.remote_addr or '127.0.0.1'
        
    def get_rate_limit_key(self, user_id: Optional[str] = None, path: Optional[str] = None, 
                           category: Optional[str] = None) -> str:
        """
        Generate a rate limit key for Redis
        
        Args:
            user_id: User ID (if authenticated)
            path: Request path
            category: Rate limit category
            
        Returns:
            str: Rate limit key
        """
        # Get client IP if not set
        if not self.client_ip:
            self.client_ip = self.get_client_ip()
            
        # Use either user_id (for authenticated users) or IP (for anonymous users)
        identity = str(user_id) if user_id else self.client_ip
        
        # Create key components
        components = [identity]
        
        # Add path component if provided
        if path:
            components.append(path.strip('/').replace('/', ':'))
            
        # Add category component if provided
        if category:
            components.append(category)
            
        # Create the key
        return ':'.join(components)
        
    def get_limit_for_request(self, user_id: Optional[str] = None, 
                              path: Optional[str] = None) -> int:
        """
        Get the rate limit for a request
        
        Args:
            user_id: User ID (if authenticated)
            path: Request path
            
        Returns:
            int: Rate limit (requests per minute)
        """
        # Determine if authenticated
        auth_type = 'auth' if user_id else 'anon'
        
        # Determine endpoint category based on path
        category = 'default'
        if path:
            path_lower = path.lower()
            if 'chat' in path_lower or 'message' in path_lower:
                category = 'chat'
            elif 'upload' in path_lower or 'file' in path_lower:
                category = 'upload'
            elif 'model' in path_lower or 'embedding' in path_lower:
                category = 'model'
        
        # Get the limit for this user type and category
        return self.rate_limits[auth_type].get(category, self.rate_limits[auth_type]['default'])
        
    def is_rate_limited(self, key: str, limit: int) -> Dict[str, Any]:
        """
        Check if a request should be rate limited
        
        Args:
            key: Rate limit key
            limit: Rate limit (requests per minute)
            
        Returns:
            Dict: Rate limit information
        """
        try:
            # Get current count
            count = self.redis.increment(key)
            
            # Create timer key if it doesn't exist
            timer_key = f"{key}:reset"
            timestamp = self.redis.get(timer_key)
            
            if not timestamp:
                # Set expiration time to current time + window
                timestamp = time.time() + self.expire_time
                self.redis.set(timer_key, str(timestamp), expire=self.expire_time)
            else:
                timestamp = float(timestamp)
            
            # Time remaining in the window
            reset_time = max(int(timestamp - time.time()), 0)
            
            # Check if limit is exceeded
            limited = count > limit
            
            return {
                'limited': limited,
                'count': count,
                'limit': limit,
                'remaining': max(limit - count, 0),
                'reset': reset_time
            }
        
        except Exception as e:
            # On error, don't rate limit
            logger.error(f"Error checking rate limit: {str(e)}")
            return {
                'limited': False,
                'count': 1,
                'limit': limit,
                'remaining': limit - 1,
                'reset': self.expire_time
            }
    
    def limit_path(self, path: str = None, user_id_function: Callable = None):
        """
        Decorator for rate-limiting a specific path
        
        Args:
            path: Optional custom path for the rate limit (defaults to request path)
            user_id_function: Optional function to get the user ID (defaults to g.user.id)
            
        Returns:
            Decorator function
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get user ID if available
                user_id = None
                try:
                    if user_id_function:
                        user_id = user_id_function()
                    elif hasattr(g, 'user') and g.user:
                        user_id = g.user.id
                except:
                    pass
                
                # Get the path to rate limit
                limit_path = path or request.path
                
                # Generate rate limit key
                key = self.get_rate_limit_key(user_id=user_id, path=limit_path)
                
                # Get the limit for this request
                limit = self.get_limit_for_request(user_id=user_id, path=limit_path)
                
                # Check if rate limited
                rate_info = self.is_rate_limited(key, limit)
                
                # Add rate limit headers to g for later use
                g.rate_limit = rate_info
                
                # If limited, return 429 response
                if rate_info['limited']:
                    response = jsonify({
                        'error': 'Too Many Requests',
                        'message': f"Rate limit exceeded. Try again in {rate_info['reset']} seconds.",
                        'limit': rate_info['limit'],
                        'remaining': 0,
                        'reset': rate_info['reset']
                    })
                    response.status_code = 429
                    
                    # Add rate limit headers
                    response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                    response.headers['X-RateLimit-Remaining'] = '0'
                    response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
                    response.headers['Retry-After'] = str(rate_info['reset'])
                    
                    return response
                
                # Proceed with the request
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter():
    """
    Get or create the global rate limiter instance
    
    Returns:
        RedisRateLimiter: The rate limiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RedisRateLimiter()
    return _rate_limiter

# Create a LocalProxy for the rate limiter for easy access in Flask
rate_limiter = LocalProxy(get_rate_limiter)

def setup_rate_limiting(app: Flask, custom_limits: Optional[Dict] = None) -> None:
    """
    Set up rate limiting for a Flask application
    
    Args:
        app: Flask application
        custom_limits: Optional custom rate limits
        
    Returns:
        None
    """
    limiter = get_rate_limiter()
    
    # Set custom limits if provided
    if custom_limits:
        for auth_type, categories in custom_limits.items():
            if auth_type in limiter.rate_limits:
                limiter.rate_limits[auth_type].update(categories)
    
    # Set up after-request handler to add rate limit headers
    @app.after_request
    def add_rate_limit_headers(response):
        # Skip if no rate limit info on this request
        if not hasattr(g, 'rate_limit'):
            return response
            
        # Add headers
        response.headers['X-RateLimit-Limit'] = str(g.rate_limit['limit'])
        response.headers['X-RateLimit-Remaining'] = str(g.rate_limit['remaining'])
        response.headers['X-RateLimit-Reset'] = str(g.rate_limit['reset'])
        
        return response
    
    # Save the limiter instance on the app
    app.extensions['rate_limiter'] = limiter
    
    return limiter

def apply_rate_limiting(app: Flask, endpoint_map: Optional[Dict] = None) -> None:
    """
    Apply rate limiting to specific endpoints
    
    Args:
        app: Flask application
        endpoint_map: Optional mapping of endpoint names to rate limit categories
        
    Returns:
        None
    """
    limiter = get_rate_limiter()
    
    # Default endpoint categorization
    default_map = {
        # Chat endpoints
        'chat': 'chat',
        'conversations': 'chat',
        'messages': 'chat',
        
        # Upload endpoints
        'upload': 'upload',
        'file': 'upload',
        'attachments': 'upload',
        
        # Model endpoints
        'model': 'model',
        'models': 'model',
        'embeddings': 'model'
    }
    
    # Merge custom map with default map
    endpoint_map = endpoint_map or {}
    mapping = {**default_map, **endpoint_map}
    
    # Apply rate limiting to routes
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        
        # Skip static files and special endpoints
        if endpoint.startswith('static') or endpoint == 'root':
            continue
            
        # Find the view function for this endpoint
        view_func = app.view_functions.get(endpoint)
        if not view_func:
            continue
            
        # Determine category
        category = None
        for key, cat in mapping.items():
            if key in endpoint:
                category = cat
                break
        
        # Wrap the view function with rate limiting
        # We don't actually replace the function to avoid issues with blueprints
        # Instead, we create a rate-limited version that wraps the original function
        original_func = view_func
        
        # Create rate limited wrapper
        @wraps(original_func)
        def rate_limited_view(*args, **kwargs):
            # Get user ID if available
            user_id = None
            try:
                if hasattr(g, 'user') and g.user:
                    user_id = g.user.id
            except:
                pass
                
            # Generate rate limit key
            key = limiter.get_rate_limit_key(user_id=user_id, path=request.path, category=category)
            
            # Get the limit for this request
            limit = limiter.get_limit_for_request(user_id=user_id, path=request.path)
            
            # Check if rate limited
            rate_info = limiter.is_rate_limited(key, limit)
            
            # Add rate limit headers to g for later use
            g.rate_limit = rate_info
            
            # If limited, return 429 response
            if rate_info['limited']:
                response = jsonify({
                    'error': 'Too Many Requests',
                    'message': f"Rate limit exceeded. Try again in {rate_info['reset']} seconds.",
                    'limit': rate_info['limit'],
                    'remaining': 0,
                    'reset': rate_info['reset']
                })
                response.status_code = 429
                
                # Add rate limit headers
                response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
                response.headers['Retry-After'] = str(rate_info['reset'])
                
                return response
            
            # Proceed with the request
            return original_func(*args, **kwargs)
        
        # Replace the view function with our rate-limited version
        app.view_functions[endpoint] = rate_limited_view
        
    logger.info(f"Rate limiting applied to {len(app.view_functions)} routes")
    
    return limiter