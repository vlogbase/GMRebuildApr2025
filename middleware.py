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
    Configure Flask to use Redis for session storage with fallback to filesystem
    
    Args:
        app: Flask application instance
        key_prefix: Prefix for session keys in Redis
        expiry: Session expiry time in seconds (default: 1 day)
    """
    # Get Redis URL from environment variables
    redis_url = os.environ.get('REDIS_HOST')
    
    # If Redis URL is not available, fall back to filesystem sessions
    if not redis_url:
        logger.warning("REDIS_HOST environment variable not set")
        setup_filesystem_session(app, key_prefix)
        return
        
    # Determine if SSL should be used
    ssl = redis_url.startswith('rediss://')
    
    # Mask password in logs if URL contains authentication
    safe_url = redis_url
    if '@' in redis_url:
        # Only show up to the @ symbol to mask credentials
        safe_url = redis_url[:redis_url.find('@') + 1] + "***"
    
    logger.info(f"Setting up Redis session with prefix {key_prefix}, expiry {expiry}s")
    logger.info(f"Using Redis URL: {safe_url}")
    
    try:
        # Import our more robust Redis session implementation 
        from redis_session import setup_redis_session as setup_redis_session_robust
        
        # Use the more robust implementation
        setup_redis_session_robust(app, expire=expiry, redis_url=redis_url)
        logger.info("Enhanced Redis session handler configured")
        
    except (ImportError, Exception) as e:
        logger.error(f"Could not use enhanced Redis session handler: {e}")
        
        try:
            # Fallback to basic Redis session interface
            logger.warning("Falling back to basic Redis session implementation")
            
            # Create the session interface with shorter timeouts
            session_interface = RedisSessionInterface(
                prefix=key_prefix + ':',
                expire=expiry,
                redis_url=redis_url
            )
            
            # Assign to Flask app
            app.session_interface = session_interface
            
            # Test the Redis connection
            if hasattr(session_interface, 'redis') and session_interface.redis:
                # Basic connectivity test
                logger.info("Redis session connection verified")
            else:
                # Connection failed, use filesystem sessions
                logger.error("Redis session connection failed")
                setup_filesystem_session(app, key_prefix)
                return
                
            logger.info("Basic Redis session setup complete")
            
        except Exception as e:
            logger.error(f"Redis session setup failed: {e}")
            setup_filesystem_session(app, key_prefix)

def setup_filesystem_session(app: Flask, key_prefix: str = 'session'):
    """Set up filesystem-based sessions as a fallback"""
    logger.warning("Setting up filesystem-based sessions")
    
    # Configure filesystem session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = key_prefix + ':'
    
    try:
        from flask_session import Session
        Session(app)
        logger.info("Filesystem session configured successfully")
    except ImportError:
        logger.error("Failed to import flask_session. Using default Flask sessions")
        # Continue with Flask's default session

def setup_rate_limiting(app: Flask, default_limits: Optional[Dict[str, Dict[str, int]]] = None):
    """
    Configure rate limiting middleware with fallback if Redis is unavailable
    
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
    
    try:
        # Get Redis URL from environment
        redis_url = os.environ.get('REDIS_HOST')
        
        if not redis_url:
            logger.warning("REDIS_HOST environment variable not set, rate limiting will be disabled")
            rate_limiter = None
        else:
            # Initialize rate limiter with the specified Redis connection
            # Set short timeouts to prevent application hanging
            rate_limiter = RedisRateLimiter(namespace='rate_limit:', expire_time=60)
            
            # Verify that Redis connection is working
            if hasattr(rate_limiter, 'redis') and rate_limiter.redis:
                # Test if Redis is actually available
                logger.info("Rate limiter initialized with Redis backend")
            else:
                logger.warning("Redis connection for rate limiter failed, rate limiting will be disabled")
                rate_limiter = None
    except Exception as e:
        logger.error(f"Error setting up rate limiter: {e}")
        rate_limiter = None
    
    # Apply rate limit headers to all responses (even if rate limiter is disabled)
    @app.after_request
    def add_rate_limit_headers(response):
        """Add rate limit headers to responses"""
        if rate_limiter:
            try:
                # First try the direct method if it exists
                if hasattr(rate_limiter, 'apply_rate_limit_headers'):
                    return rate_limiter.apply_rate_limit_headers(response)
                
                # Otherwise add basic headers if we have rate info in g
                if hasattr(g, 'rate_limit_info'):
                    limit_info = g.rate_limit_info
                    response.headers['X-RateLimit-Limit'] = str(limit_info.get('limit', 0))
                    response.headers['X-RateLimit-Remaining'] = str(limit_info.get('remaining', 0))
                    response.headers['X-RateLimit-Reset'] = str(limit_info.get('reset', 0))
            except Exception as e:
                # Don't let rate limiting issues break the app
                logger.error(f"Error applying rate limit headers: {e}")
                
        return response
    
    # Create route decorators for common rate limit scenarios
    # These will work even if rate_limiter is None (will be no-ops)
    app.public_endpoint = public_endpoint
    app.auth_required_endpoint = auth_required_endpoint
    app.api_endpoint = api_endpoint
    app.upload_endpoint = upload_endpoint
    app.admin_endpoint = admin_endpoint
    
    if rate_limiter:
        logger.info("Rate limiting is enabled")
    else:
        logger.warning("Rate limiting is disabled due to Redis connection issues")

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
                try:
                    # Check if rate_limiter has the needed method
                    if hasattr(rate_limiter, 'limit_by_ip'):
                        # Use IP-based limiting for public endpoints
                        return rate_limiter.limit_by_ip(
                            limit=limit,
                            window=window,
                            endpoint='public'
                        )(func)(*args, **kwargs)
                    else:
                        # Method doesn't exist, log and continue without rate limiting
                        logger.warning("Rate limiter doesn't support limit_by_ip method")
                except Exception as e:
                    # If rate limiting fails, log and continue without it
                    logger.error(f"Rate limiting error in public_endpoint: {e}")
            
            # Return the original function if rate limiting is disabled or fails
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
                try:
                    # Check if rate_limiter has the needed method
                    if hasattr(rate_limiter, 'limit_by_user'):
                        # Use user-based limiting for authenticated endpoints
                        return rate_limiter.limit_by_user(
                            limit=limit,
                            window=window,
                            endpoint='auth'
                        )(func)(*args, **kwargs)
                    else:
                        # Method doesn't exist, log and continue without rate limiting
                        logger.warning("Rate limiter doesn't support limit_by_user method")
                except Exception as e:
                    # If rate limiting fails, log and continue without it
                    logger.error(f"Rate limiting error in auth_required_endpoint: {e}")
            
            # Return the original function if rate limiting is disabled or fails
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