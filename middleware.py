"""
Middleware Module for Redis Integration

This module provides middleware functions to integrate Redis-based components
with Flask, including:
- Redis-backed session storage
- Rate limiting
- Request logging
"""

import os
import time
import logging
from functools import wraps
from typing import Dict, Optional, Union, Callable, Any
from flask import Flask, request, g, session, Response, current_app

# Import Redis components
from redis_session import RedisSessionInterface
from redis_rate_limiter import RedisRateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Global rate limiter instance
rate_limiter = None

def setup_redis_session(app: Flask, key_prefix: str = 'session', expiry: int = 86400):
    """
    Configure Flask to use Redis for session storage
    
    Args:
        app: Flask application instance
        key_prefix: Prefix for session keys in Redis
        expiry: Session expiry time in seconds (default: 1 day)
    """
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    ssl = redis_url.startswith('rediss://')
    
    logger.info(f"Setting up Redis session with prefix {key_prefix}, expiry {expiry}s")
    logger.info(f"Using Redis URL: {redis_url[:redis_url.find('@') + 1]}***")
    
    # Create the session interface
    session_interface = RedisSessionInterface(
        redis_url=redis_url,
        key_prefix=key_prefix,
        use_ssl=ssl,
        default_expiry=expiry
    )
    
    # Assign to Flask app
    app.session_interface = session_interface
    
    # Setup session saving after each request
    @app.after_request
    def save_session(response):
        """Save session after each request"""
        return session_interface.save_session(app, session, response)
    
    logger.info("Redis session setup complete")

def setup_rate_limiting(app: Flask, default_limits: Optional[Dict[str, Dict[str, int]]] = None):
    """
    Configure rate limiting middleware
    
    Args:
        app: Flask application instance
        default_limits: Dictionary of default rate limits per endpoint type
                       Format: {'default': {'limit': 60, 'window': 60}}
    """
    global rate_limiter
    
    # Set up default limits if not provided
    if default_limits is None:
        default_limits = {
            'default': {'limit': 60, 'window': 60},  # 60 requests per minute
        }
    
    logger.info(f"Setting up rate limiting with defaults: {default_limits}")
    
    # Initialize rate limiter
    rate_limiter = RedisRateLimiter(key_prefix='rate_limit')
    
    # Apply rate limit headers to all responses
    @app.after_request
    def add_rate_limit_headers(response):
        """Add rate limit headers to responses"""
        if rate_limiter:
            return rate_limiter.apply_rate_limit_headers(response)
        return response
    
    # Create route decorators for common rate limit scenarios
    app.public_endpoint = public_endpoint
    app.auth_required_endpoint = auth_required_endpoint
    app.api_endpoint = api_endpoint
    app.upload_endpoint = upload_endpoint
    app.admin_endpoint = admin_endpoint
    
    logger.info("Rate limiting setup complete")

def public_endpoint(f=None, *, limit=None, window=None):
    """
    Decorator for public endpoints with IP-based rate limiting
    
    Args:
        limit: Max requests per window (optional)
        window: Window size in seconds (optional)
    """
    global rate_limiter
    
    # Default values for public endpoints (less restrictive)
    if limit is None:
        limit = 60  # 60 requests per minute
    if window is None:
        window = 60  # 1 minute window
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Apply rate limiting if available
            if rate_limiter:
                # Use IP-based limiting for public endpoints
                return rate_limiter.limit_by_ip(
                    limit=limit,
                    window=window,
                    endpoint='public'
                )(func)(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    
    # Handle both @public_endpoint and @public_endpoint(limit=X) forms
    if f:
        return decorator(f)
    return decorator

def auth_required_endpoint(f=None, *, limit=None, window=None):
    """
    Decorator for authenticated endpoints with user-based rate limiting
    
    Args:
        limit: Max requests per window (optional)
        window: Window size in seconds (optional)
    """
    global rate_limiter
    
    # Default values for authenticated endpoints (more permissive)
    if limit is None:
        limit = 100  # 100 requests per minute
    if window is None:
        window = 60  # 1 minute window
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Apply rate limiting if available
            if rate_limiter:
                # Use user-based limiting for authenticated endpoints
                return rate_limiter.limit_by_user(
                    limit=limit,
                    window=window,
                    endpoint='auth'
                )(func)(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    
    # Handle both @auth_required_endpoint and @auth_required_endpoint(limit=X) forms
    if f:
        return decorator(f)
    return decorator

def api_endpoint(f=None, *, limit=None, window=None):
    """
    Decorator for API endpoints with appropriate rate limiting
    
    Args:
        limit: Max requests per window (optional)
        window: Window size in seconds (optional)
    """
    global rate_limiter
    
    # Default values for API endpoints
    if limit is None:
        limit = 30  # 30 requests per minute
    if window is None:
        window = 60  # 1 minute window
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Apply rate limiting if available
            if rate_limiter:
                # Check if user is authenticated, use user or IP accordingly
                if hasattr(g, 'user') and g.user:
                    # Authenticated API request
                    return rate_limiter.limit_by_user(
                        limit=limit,
                        window=window,
                        endpoint='api'
                    )(func)(*args, **kwargs)
                else:
                    # Unauthenticated API request
                    return rate_limiter.limit_by_ip(
                        limit=limit // 3,  # 1/3 the limit for unauthenticated
                        window=window,
                        endpoint='api'
                    )(func)(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    
    # Handle both @api_endpoint and @api_endpoint(limit=X) forms
    if f:
        return decorator(f)
    return decorator

def upload_endpoint(f=None, *, limit=None, window=None):
    """
    Decorator for upload endpoints with restrictive rate limiting
    
    Args:
        limit: Max requests per window (optional)
        window: Window size in seconds (optional)
    """
    global rate_limiter
    
    # Default values for upload endpoints (more restrictive)
    if limit is None:
        limit = 10  # 10 uploads per minute
    if window is None:
        window = 60  # 1 minute window
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Apply rate limiting if available
            if rate_limiter:
                # Check if user is authenticated, use user or IP accordingly
                if hasattr(g, 'user') and g.user:
                    # Authenticated upload
                    return rate_limiter.limit_by_user(
                        limit=limit,
                        window=window,
                        endpoint='upload'
                    )(func)(*args, **kwargs)
                else:
                    # Unauthenticated upload
                    return rate_limiter.limit_by_ip(
                        limit=limit // 3,  # 1/3 the limit for unauthenticated
                        window=window,
                        endpoint='upload'
                    )(func)(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    
    # Handle both @upload_endpoint and @upload_endpoint(limit=X) forms
    if f:
        return decorator(f)
    return decorator

def admin_endpoint(f=None, *, limit=None, window=None):
    """
    Decorator for admin endpoints with permissive rate limiting
    
    Args:
        limit: Max requests per window (optional)
        window: Window size in seconds (optional)
    """
    global rate_limiter
    
    # Default values for admin endpoints (very permissive)
    if limit is None:
        limit = 300  # 300 requests per minute
    if window is None:
        window = 60  # 1 minute window
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Apply rate limiting if available
            if rate_limiter:
                # Admin endpoints should always use user-based limiting
                return rate_limiter.limit_by_user(
                    limit=limit,
                    window=window,
                    endpoint='admin'
                )(func)(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    
    # Handle both @admin_endpoint and @admin_endpoint(limit=X) forms
    if f:
        return decorator(f)
    return decorator

def request_logger(app: Flask):
    """
    Request logging middleware
    
    Logs details about each request including timing information.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request():
        """Capture start time before request processing"""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Log request details after processing"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Get basic request info
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            method = request.method
            path = request.path
            status = response.status_code
            user_agent = request.headers.get('User-Agent', '')
            
            # Get user info if available
            user_id = None
            if hasattr(g, 'user') and g.user:
                if hasattr(g.user, 'id'):
                    user_id = g.user.id
                elif hasattr(g.user, 'get_id'):
                    user_id = g.user.get_id()
            
            # Log the request
            logger.info(
                f"Request: {method} {path} | Status: {status} | IP: {client_ip} "
                f"| User: {user_id or 'Anonymous'} | Duration: {duration:.4f}s"
            )
        
        return response
    
    logger.info("Request logging middleware attached")
    return app