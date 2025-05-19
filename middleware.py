"""
Middleware Module

This module provides Flask middleware for integrating Redis-based components:
- Session management with Redis
- Rate limiting
- Request/response hooks for caching
"""

import os
import logging
from functools import wraps
from flask import Flask, g, request, current_app

from redis_cache import get_redis_connection
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

def setup_redis_session(app, key_prefix="session", expiry=86400):
    """
    Set up Redis-backed sessions for a Flask app
    
    Args:
        app (Flask): The Flask app
        key_prefix (str): Prefix for session keys in Redis
        expiry (int): Session expiration time in seconds (default: 1 day)
    """
    logger.info("Setting up Redis-backed sessions")
    session_interface = RedisSessionInterface(
        prefix=key_prefix,
        expiry=expiry,
        key_prefix=app.name
    )
    app.session_interface = session_interface

def setup_rate_limiter(app, default_limits=None):
    """
    Set up rate limiting for a Flask app
    
    Args:
        app (Flask): The Flask app
        default_limits (dict): Default rate limits for different route types
            Example: {
                'default': {'limit': 60, 'window': 60},
                'api': {'limit': 30, 'window': 60}
            }
    """
    global rate_limiter
    
    logger.info("Setting up rate limiting")
    
    # Default rate limits if none provided
    if default_limits is None:
        default_limits = {
            'default': {'limit': 60, 'window': 60},  # 60 requests per minute for general routes
            'api': {'limit': 30, 'window': 60},      # 30 requests per minute for API routes
            'chat': {'limit': 10, 'window': 60}      # 10 requests per minute for chat routes
        }
    
    # Create rate limiter
    rate_limiter = RedisRateLimiter(
        key_prefix=f"rate_limit:{app.name}",
        default_limit=default_limits['default']['limit'],
        default_window=default_limits['default']['window']
    )
    
    # Register after_request handler to add rate limit headers
    @app.after_request
    def add_rate_limit_headers(response):
        return rate_limiter.apply_rate_limit_headers(response)
    
    # Store rate limiter in app context
    app.rate_limiter = rate_limiter
    
    # Define rate limit decorators for different route types
    app.limit_by_ip = rate_limiter.limit_by_ip
    app.limit_by_user = rate_limiter.limit_by_user
    
    # Add convenience functions for different route types
    def limit_api_route(f):
        """Limit API routes"""
        @wraps(f)
        @rate_limiter.limit_by_ip(
            limit=default_limits['api']['limit'],
            window=default_limits['api']['window']
        )
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated
    
    def limit_chat_route(f):
        """Limit chat routes"""
        @wraps(f)
        @rate_limiter.limit_by_ip(
            limit=default_limits['chat']['limit'],
            window=default_limits['chat']['window']
        )
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated
    
    # Add to app context
    app.limit_api_route = limit_api_route
    app.limit_chat_route = limit_chat_route

def setup_authenticated_rate_limits(app, authenticated_limits=None):
    """
    Set up different rate limits for authenticated users
    
    Args:
        app (Flask): The Flask app
        authenticated_limits (dict): Rate limits for authenticated users
            Example: {
                'default': {'limit': 120, 'window': 60},
                'api': {'limit': 60, 'window': 60}
            }
    """
    # Default authenticated limits if none provided
    if authenticated_limits is None:
        authenticated_limits = {
            'default': {'limit': 120, 'window': 60},  # 120 requests per minute for general routes (2x)
            'api': {'limit': 60, 'window': 60},       # 60 requests per minute for API routes (2x)
            'chat': {'limit': 20, 'window': 60}       # 20 requests per minute for chat routes (2x)
        }
    
    # Define authenticated rate limit decorators
    def limit_authenticated_api_route(f):
        """Limit API routes with higher limits for authenticated users"""
        @wraps(f)
        def decorated(*args, **kwargs):
            # Use user-based limiting if user is authenticated,
            # otherwise fall back to IP-based limiting
            if hasattr(g, 'user') and g.user:
                # User is authenticated, use higher limits
                return rate_limiter.limit_by_user(
                    limit=authenticated_limits['api']['limit'],
                    window=authenticated_limits['api']['window']
                )(f)(*args, **kwargs)
            else:
                # User is not authenticated, use default limits
                return app.limit_api_route(f)(*args, **kwargs)
        return decorated
    
    def limit_authenticated_chat_route(f):
        """Limit chat routes with higher limits for authenticated users"""
        @wraps(f)
        def decorated(*args, **kwargs):
            # Use user-based limiting if user is authenticated,
            # otherwise fall back to IP-based limiting
            if hasattr(g, 'user') and g.user:
                # User is authenticated, use higher limits
                return rate_limiter.limit_by_user(
                    limit=authenticated_limits['chat']['limit'],
                    window=authenticated_limits['chat']['window']
                )(f)(*args, **kwargs)
            else:
                # User is not authenticated, use default limits
                return app.limit_chat_route(f)(*args, **kwargs)
        return decorated
    
    # Add to app context
    app.limit_authenticated_api_route = limit_authenticated_api_route
    app.limit_authenticated_chat_route = limit_authenticated_chat_route

def setup_redis_middleware(app, key_prefix="session", session_expiry=86400,
                         default_limits=None, authenticated_limits=None):
    """
    Set up all Redis middleware components for a Flask app
    
    Args:
        app (Flask): The Flask app
        key_prefix (str): Prefix for session keys in Redis
        session_expiry (int): Session expiration time in seconds
        default_limits (dict): Default rate limits for different route types
        authenticated_limits (dict): Rate limits for authenticated users
    """
    # Set up Redis session
    setup_redis_session(app, key_prefix=key_prefix, expiry=session_expiry)
    
    # Set up rate limiting
    setup_rate_limiter(app, default_limits=default_limits)
    
    # Set up authenticated rate limits
    setup_authenticated_rate_limits(app, authenticated_limits=authenticated_limits)
    
    logger.info("Redis middleware setup complete")
    
    return app