"""
Redis Integration Module

This module provides functions to integrate Redis-based services 
with a Flask application, including:
- Session management with Redis
- Rate limiting
- Background job processing
- API response caching
"""

import os
import logging
from typing import Dict, List, Optional, Callable, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def init_redis_services(app, session_prefix="session", 
                       rate_limits=None, authenticated_rate_limits=None,
                       job_queues=None, cache_config=None):
    """
    Initialize all Redis-based services for a Flask application
    
    Args:
        app (Flask): The Flask application
        session_prefix (str): Prefix for session keys in Redis
        rate_limits (dict): Rate limits for different route types
        authenticated_rate_limits (dict): Rate limits for authenticated users
        job_queues (dict): Job queue configuration
        cache_config (dict): API cache configuration
    """
    try:
        # Import necessary modules
        from middleware import setup_redis_middleware
        from jobs_blueprint import init_app as init_jobs_bp
        from redis_cache import get_redis_connection

        # Apply Redis session and rate limiting
        if rate_limits or authenticated_rate_limits:
            logger.info("Setting up Redis session and rate limiting")
            setup_redis_middleware(
                app, 
                key_prefix=session_prefix,
                default_limits=rate_limits,
                authenticated_limits=authenticated_rate_limits
            )
        
        # Set up job processing
        if job_queues is not None:
            logger.info("Setting up job processing")
            init_jobs_bp(app)
            
            # Make job manager available in app context
            from jobs import job_manager
            app.job_manager = job_manager
        
        # Set up API caching
        if cache_config is not None:
            logger.info("Setting up API response caching")
            from api_cache import ApiCache
            app.api_cache = ApiCache(
                namespace=cache_config.get('namespace', 'api_cache'),
                default_ttl=cache_config.get('default_ttl', 3600)
            )
        
        # Try to connect to Redis to verify connection
        redis_conn = get_redis_connection()
        if redis_conn:
            redis_info = redis_conn.info()
            logger.info(f"Successfully connected to Redis {redis_info.get('redis_version', 'unknown')}")
        
        logger.info("Redis services initialization complete")
        return True
    
    except ImportError as e:
        logger.error(f"Failed to import Redis modules: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Failed to initialize Redis services: {e}")
        return False

def setup_default_rate_limits():
    """
    Set up default rate limits for various route types
    
    Returns:
        tuple: (default_limits, authenticated_limits)
    """
    # Default rate limits for anonymous users (by IP)
    default_limits = {
        'default': {'limit': 60, 'window': 60},  # 60 requests per minute for standard routes
        'api': {'limit': 30, 'window': 60},      # 30 requests per minute for API routes
        'chat': {'limit': 5, 'window': 60},      # 5 requests per minute for chat routes
        'upload': {'limit': 3, 'window': 60},    # 3 requests per minute for file uploads
        'model': {'limit': 10, 'window': 60}     # 10 requests per minute for model-related routes
    }
    
    # Higher rate limits for authenticated users (by user ID)
    authenticated_limits = {
        'default': {'limit': 120, 'window': 60},  # 120 requests per minute for standard routes
        'api': {'limit': 60, 'window': 60},       # 60 requests per minute for API routes
        'chat': {'limit': 20, 'window': 60},      # 20 requests per minute for chat routes
        'upload': {'limit': 10, 'window': 60},    # 10 requests per minute for file uploads
        'model': {'limit': 30, 'window': 60}      # 30 requests per minute for model-related routes
    }
    
    return default_limits, authenticated_limits

def setup_default_job_queues():
    """
    Set up default job queues with sensible configurations
    
    Returns:
        dict: Queue configurations
    """
    return {
        'high': {'ttl': 3600, 'result_ttl': 3600},      # High-priority tasks (1 hour timeout)
        'default': {'ttl': 3600, 'result_ttl': 3600},   # Standard tasks (1 hour timeout)
        'low': {'ttl': 3600, 'result_ttl': 3600},       # Low-priority background tasks (1 hour timeout)
        'email': {'ttl': 7200, 'result_ttl': 3600},     # Email sending (2 hour timeout)
        'indexing': {'ttl': 10800, 'result_ttl': 3600}  # Document indexing (3 hour timeout)
    }

def setup_default_cache_config():
    """
    Set up default API cache configuration
    
    Returns:
        dict: Cache configuration
    """
    return {
        'namespace': 'api_cache',
        'default_ttl': 3600,  # 1 hour default TTL
        'endpoints': {
            # Example endpoint-specific TTLs
            'openrouter_models': 86400,       # 24 hours for model listings
            'model_pricing': 43200,           # 12 hours for pricing info
            'user_preferences': 300,          # 5 minutes for user preferences
            'conversation_list': 60           # 1 minute for conversation listings
        }
    }

def get_job_function_examples():
    """
    Get example job functions that can be scheduled
    
    Returns:
        dict: Dictionary of example job functions
    """
    try:
        # Import example job functions
        from jobs import (
            example_email_job, example_report_job, 
            example_processing_job, example_cache_update_job,
            example_long_task
        )
        
        return {
            'email_job': example_email_job,
            'report_job': example_report_job,
            'processing_job': example_processing_job,
            'cache_update_job': example_cache_update_job,
            'long_task': example_long_task
        }
    except ImportError:
        logger.warning("Could not import example job functions")
        return {}

def configure_app_with_redis(app, enable_all=False):
    """
    Configure a Flask application with Redis services using sensible defaults
    
    Args:
        app (Flask): The Flask application
        enable_all (bool): Enable all Redis services, or just sessions
        
    Returns:
        bool: True if successful, False otherwise
    """
    if enable_all:
        # Enable all Redis services with sensible defaults
        default_limits, authenticated_limits = setup_default_rate_limits()
        job_queues = setup_default_job_queues()
        cache_config = setup_default_cache_config()
        
        return init_redis_services(
            app,
            session_prefix=f"session:{app.name}",
            rate_limits=default_limits,
            authenticated_rate_limits=authenticated_limits,
            job_queues=job_queues,
            cache_config=cache_config
        )
    else:
        # Enable just Redis sessions and rate limiting
        default_limits, authenticated_limits = setup_default_rate_limits()
        
        return init_redis_services(
            app,
            session_prefix=f"session:{app.name}",
            rate_limits=default_limits,
            authenticated_rate_limits=authenticated_limits
        )

def register_job_decorators(app):
    """
    Register job decorator functions directly on the Flask app
    
    Args:
        app (Flask): The Flask application
        
    Returns:
        Flask: The modified Flask application
    """
    try:
        from jobs import job_manager
        
        # Add background job decorator to app
        app.background_job = job_manager.background_job
        
        # Common queue shortcuts
        app.queue_high = lambda func: job_manager.background_job(queue_name='high')(func)
        app.queue_default = lambda func: job_manager.background_job(queue_name='default')(func)
        app.queue_low = lambda func: job_manager.background_job(queue_name='low')(func)
        app.queue_email = lambda func: job_manager.background_job(queue_name='email')(func)
        app.queue_indexing = lambda func: job_manager.background_job(queue_name='indexing')(func)
        
        logger.info("Job decorators registered on Flask app")
        return app
    
    except ImportError:
        logger.warning("Could not import job_manager, job decorators not registered")
        return app

def register_cache_decorators(app):
    """
    Register API cache decorator functions directly on the Flask app
    
    Args:
        app (Flask): The Flask application
        
    Returns:
        Flask: The modified Flask application
    """
    try:
        from api_cache import ApiCache
        
        if not hasattr(app, 'api_cache'):
            app.api_cache = ApiCache()
            
        # Add cache decorator to app
        app.cache_api = app.api_cache.cache
        
        # Add timed cache decorator to app
        app.timed_cache_api = app.api_cache.timed_cache
        
        logger.info("Cache decorators registered on Flask app")
        return app
    
    except ImportError:
        logger.warning("Could not import ApiCache, cache decorators not registered")
        return app