"""
Application Integration Module

This module integrates the Redis-based services with the main Flask application.
It includes functions to register job processing, session management, rate limiting,
and API caching with a Flask application.
"""

import os
import logging
from typing import Dict, Optional, Any, List, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def integrate_redis_services(app):
    """
    Integrate Redis-based services with the Flask application
    
    Args:
        app (Flask): The Flask application
        
    Returns:
        bool: True if successful, False otherwise
    """
    success = True
    
    # Register Redis session interface if not already registered
    if not hasattr(app, '_redis_session_registered'):
        try:
            from redis_session import setup_redis_session
            setup_redis_session(app)
            app._redis_session_registered = True
            logger.info("Redis session interface registered")
        except ImportError as e:
            logger.warning(f"Could not import Redis session module: {e}")
            success = False
        except Exception as e:
            logger.warning(f"Error registering Redis session interface: {e}")
            success = False
    
    # Register rate limiting middleware if not already registered
    if not hasattr(app, '_rate_limiting_registered'):
        try:
            from middleware import setup_redis_middleware
            
            # Default rate limits
            default_limits = {
                'default': {'limit': 60, 'window': 60},   # 60 requests per minute
                'api': {'limit': 30, 'window': 60},       # 30 requests per minute
                'chat': {'limit': 5, 'window': 60},       # 5 requests per minute
                'upload': {'limit': 3, 'window': 60},     # 3 requests per minute
                'model': {'limit': 10, 'window': 60}      # 10 requests per minute
            }
            
            # Higher limits for authenticated users
            authenticated_limits = {
                'default': {'limit': 120, 'window': 60},  # 120 requests per minute
                'api': {'limit': 60, 'window': 60},       # 60 requests per minute
                'chat': {'limit': 20, 'window': 60},      # 20 requests per minute
                'upload': {'limit': 10, 'window': 60},    # 10 requests per minute
                'model': {'limit': 30, 'window': 60}      # 30 requests per minute
            }
            
            setup_redis_middleware(
                app, 
                key_prefix=f"session:{app.name}",
                default_limits=default_limits,
                authenticated_limits=authenticated_limits
            )
            app._rate_limiting_registered = True
            logger.info("Rate limiting middleware registered")
        except ImportError as e:
            logger.warning(f"Could not import Redis middleware module: {e}")
            success = False
        except Exception as e:
            logger.warning(f"Error registering rate limiting middleware: {e}")
            success = False
    
    # Register jobs blueprint if not already registered
    if not hasattr(app, '_jobs_blueprint_registered'):
        try:
            from jobs_blueprint import init_app as init_jobs_bp
            init_jobs_bp(app)
            app._jobs_blueprint_registered = True
            logger.info("Jobs blueprint registered")
        except ImportError as e:
            logger.warning(f"Could not import jobs blueprint module: {e}")
            success = False
        except Exception as e:
            logger.warning(f"Error registering jobs blueprint: {e}")
            success = False
    
    # Register API cache if not already registered
    if not hasattr(app, '_api_cache_registered'):
        try:
            from api_cache import ApiCache
            app.api_cache = ApiCache(
                namespace=f"api_cache:{app.name}",
                default_ttl=3600  # 1 hour default TTL
            )
            
            # Register cache decorator on app
            app.cache_api = app.api_cache.cache
            app.timed_cache_api = app.api_cache.timed_cache
            
            app._api_cache_registered = True
            logger.info("API cache registered")
        except ImportError as e:
            logger.warning(f"Could not import API cache module: {e}")
            success = False
        except Exception as e:
            logger.warning(f"Error registering API cache: {e}")
            success = False
    
    # Register job manager if not already registered
    if not hasattr(app, '_job_manager_registered'):
        try:
            from jobs import job_manager
            
            # Add job manager to app context
            app.job_manager = job_manager
            
            # Add background job decorator to app
            app.background_job = job_manager.background_job
            
            # Common queue shortcuts
            app.queue_high = lambda func: job_manager.background_job(queue_name='high')(func)
            app.queue_default = lambda func: job_manager.background_job(queue_name='default')(func)
            app.queue_low = lambda func: job_manager.background_job(queue_name='low')(func)
            app.queue_email = lambda func: job_manager.background_job(queue_name='email')(func)
            app.queue_indexing = lambda func: job_manager.background_job(queue_name='indexing')(func)
            
            app._job_manager_registered = True
            logger.info("Job manager registered")
        except ImportError as e:
            logger.warning(f"Could not import job manager module: {e}")
            success = False
        except Exception as e:
            logger.warning(f"Error registering job manager: {e}")
            success = False
    
    # Add Redis connection test function to app
    if not hasattr(app, 'test_redis_connection'):
        try:
            from redis_cache import get_redis_connection
            
            def test_redis_connection():
                """Test the Redis connection"""
                redis_conn = get_redis_connection()
                if redis_conn:
                    redis_info = redis_conn.info()
                    return {
                        'connected': True,
                        'redis_version': redis_info.get('redis_version', 'Unknown'),
                        'uptime_seconds': redis_info.get('uptime_in_seconds', 0),
                        'connected_clients': redis_info.get('connected_clients', 0)
                    }
                return {'connected': False}
            
            app.test_redis_connection = test_redis_connection
            logger.info("Redis connection test function registered")
        except ImportError as e:
            logger.warning(f"Could not import Redis connection module: {e}")
            success = False
        except Exception as e:
            logger.warning(f"Error registering Redis connection test: {e}")
            success = False
    
    return success

def register_example_job_functions(app):
    """
    Register example job functions with the Flask application
    
    Args:
        app (Flask): The Flask application
        
    Returns:
        dict: Dictionary of registered job functions
    """
    if not hasattr(app, 'job_manager'):
        logger.warning("Cannot register example job functions: job_manager not found on app")
        return {}
    
    try:
        from jobs import (
            example_email_job, example_report_job, 
            example_processing_job, example_cache_update_job,
            example_long_task
        )
        
        # Register example job functions on app for easy access
        app.example_jobs = {
            'email_job': example_email_job,
            'report_job': example_report_job,
            'processing_job': example_processing_job,
            'cache_update_job': example_cache_update_job,
            'long_task': example_long_task
        }
        
        logger.info(f"Registered {len(app.example_jobs)} example job functions")
        return app.example_jobs
    except ImportError as e:
        logger.warning(f"Could not import example job functions: {e}")
        return {}
    except Exception as e:
        logger.warning(f"Error registering example job functions: {e}")
        return {}