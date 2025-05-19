"""
Application Integration Module

This module integrates Redis-based functionality into the main Flask application.
It includes functions to set up various Redis features like caching, sessions,
rate limiting, and background job processing.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_redis_integration(app):
    """
    Set up Redis integration for the Flask application
    
    Args:
        app: Flask application
        
    Returns:
        Flask application with Redis integration
    """
    # Ensure Redis URL is available
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        logger.warning("REDIS_URL not set in environment variables")
        redis_url = f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', '6379')}/0"
        
        # Check if Redis password is available
        redis_password = os.environ.get('REDIS_PASSWORD')
        if redis_password:
            # Format URL with password
            if '@' not in redis_url:
                protocol = 'rediss://' if redis_url.startswith('rediss://') else 'redis://'
                host_part = redis_url.split('://', 1)[1] if '://' in redis_url else redis_url
                redis_url = f"{protocol}:{redis_password}@{host_part}"
        
        logger.info(f"Using Redis URL: {redis_url.replace(redis_password or '', '***') if redis_password else redis_url}")
        os.environ['REDIS_URL'] = redis_url
    
    # Initialize Redis components
    try:
        # Import Redis modules
        from redis_cache import get_redis_connection
        
        # Check Redis connection
        redis_conn = get_redis_connection()
        if not redis_conn:
            logger.error("Could not connect to Redis")
            return app
        
        # Set up Redis session
        setup_redis_session(app)
        
        # Set up Redis rate limiting
        setup_redis_rate_limiting(app)
        
        # Set up API caching
        setup_api_caching(app)
        
        # Set up job system
        setup_job_system(app)
        
        logger.info("Redis integration setup complete")
        return app
        
    except ImportError as e:
        logger.error(f"Redis modules not available: {e}")
        return app
    
    except Exception as e:
        logger.error(f"Error setting up Redis integration: {e}")
        return app

def setup_redis_session(app):
    """
    Set up Redis session store for the Flask application
    
    Args:
        app: Flask application
        
    Returns:
        None
    """
    try:
        from redis_session import RedisSessionInterface
        
        # Initialize session interface
        session_interface = RedisSessionInterface()
        app.session_interface = session_interface
        
        logger.info("Redis session store configured")
    except ImportError:
        logger.warning("Redis session module not available")
    except Exception as e:
        logger.error(f"Error setting up Redis session: {e}")

def setup_redis_rate_limiting(app):
    """
    Set up Redis-based rate limiting for the Flask application
    
    Args:
        app: Flask application
        
    Returns:
        None
    """
    try:
        from middleware import apply_rate_limiting
        
        # Apply rate limiting middleware
        apply_rate_limiting(app)
        
        logger.info("Redis rate limiting configured")
    except ImportError:
        logger.warning("Redis rate limiting module not available")
    except Exception as e:
        logger.error(f"Error setting up Redis rate limiting: {e}")

def setup_api_caching(app):
    """
    Set up Redis-based API caching for the Flask application
    
    Args:
        app: Flask application
        
    Returns:
        None
    """
    try:
        from api_cache import init_api_cache
        
        # Initialize API cache
        init_api_cache(app)
        
        logger.info("Redis API caching configured")
    except ImportError:
        logger.warning("Redis API caching module not available")
    except Exception as e:
        logger.error(f"Error setting up Redis API caching: {e}")

def setup_job_system(app):
    """
    Set up Redis-based background job system for the Flask application
    
    Args:
        app: Flask application
        
    Returns:
        None
    """
    try:
        from jobs_blueprint import init_app as init_jobs_bp
        
        # Initialize job system blueprint
        init_jobs_bp(app)
        
        logger.info("Redis job system configured")
        
        # Register example job functions (for testing purposes)
        register_example_jobs()
        
    except ImportError:
        logger.warning("Redis job system module not available")
    except Exception as e:
        logger.error(f"Error setting up Redis job system: {e}")

def register_example_jobs():
    """
    Register example job functions for testing
    
    Returns:
        None
    """
    try:
        from jobs import background_job
        import time
        import random
        
        @background_job(queue_name='email')
        def example_email_job(recipient, subject, body):
            """Example email sending job"""
            # Simulate work
            time.sleep(2)
            return {'sent': True, 'to': recipient, 'subject': subject}
        
        @background_job(queue_name='default')
        def example_report_job(report_id, parameters):
            """Example report generation job"""
            from jobs import current_job_progress
            
            # Simulate work with progress updates
            total_steps = 5
            for i in range(total_steps):
                # Update progress
                current_job_progress(
                    message=f"Processing step {i+1}/{total_steps}",
                    progress=((i+1)/total_steps) * 100,
                    step=i+1,
                    total_steps=total_steps
                )
                
                # Simulate work
                time.sleep(1)
            
            return {'report_id': report_id, 'status': 'completed', 'parameters': parameters}
        
        @background_job(queue_name='low')
        def example_processing_job(items, process_type="standard"):
            """Example data processing job"""
            from jobs import current_job_progress
            
            # Simulate work with progress updates
            total = len(items)
            processed = []
            
            for i, item in enumerate(items):
                # Update progress
                current_job_progress(
                    message=f"Processing item {i+1}/{total}",
                    progress=((i+1)/total) * 100,
                    current=i+1,
                    total=total
                )
                
                # Simulate processing
                time.sleep(0.5)
                processed.append(f"{item}-processed-{process_type}")
            
            return {'processed': processed, 'total': total}
        
        @background_job(queue_name='high')
        def example_cache_update_job():
            """Example cache update job"""
            # Simulate work
            time.sleep(1)
            return {'cache_updated': True, 'timestamp': time.time()}
        
        @background_job(queue_name='default', timeout=600)
        def example_long_task(duration=30):
            """Example long-running task"""
            from jobs import current_job_progress
            import time
            
            # Cap duration for safety
            duration = min(duration, 300)
            
            # Simulate long-running task with progress updates
            start_time = time.time()
            end_time = start_time + duration
            
            while time.time() < end_time:
                elapsed = time.time() - start_time
                progress = min(99, (elapsed / duration) * 100)
                
                # Update progress
                current_job_progress(
                    message=f"Running long task ({int(elapsed)}s / {duration}s)",
                    progress=progress,
                    elapsed=elapsed,
                    duration=duration
                )
                
                # Sleep briefly
                time.sleep(1)
            
            # Final update
            current_job_progress(
                message=f"Completed long task ({duration}s)",
                progress=100,
                elapsed=duration,
                duration=duration
            )
            
            return {'duration': duration, 'completed': True}
        
        logger.info("Example jobs registered")
        
    except ImportError:
        logger.warning("Could not register example jobs - job module not available")
    except Exception as e:
        logger.error(f"Error registering example jobs: {e}")