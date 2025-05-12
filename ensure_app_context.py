"""
Application context manager for Flask to prevent "outside application context" errors.

This module provides a utility function and context manager to ensure database operations
always have access to the Flask application context.
"""

import functools
import logging
from contextlib import contextmanager
from flask import current_app, has_app_context

logger = logging.getLogger(__name__)

def get_app():
    """
    Get the current Flask application.
    Returns the app from the application context if it exists.
    """
    try:
        from app import app
        return app
    except ImportError:
        logger.error("Could not import app. Make sure it's properly initialized.")
        return None

@contextmanager
def ensure_app_context():
    """
    Context manager to ensure operations are performed within the Flask application context.
    
    If already in an application context, this is a no-op.
    Otherwise, it temporarily pushes an application context.
    
    Example usage:
        with ensure_app_context():
            db.session.add(model_instance)
            db.session.commit()
    """
    app = get_app()
    if app is None:
        logger.error("No Flask app available")
        raise RuntimeError("No Flask application available")
        
    if has_app_context():
        # Already in an app context, do nothing
        yield
    else:
        # Create a new app context
        logger.debug("Pushing new application context")
        with app.app_context():
            yield

def with_app_context(func=None, *, error_handler=None):
    """
    Decorator to ensure a function runs within a Flask application context.
    
    Args:
        func: The function to decorate
        error_handler: Optional function to handle errors. If provided, it will be called
                      with the exception as its argument when an error occurs.
    
    Example usage:
        @with_app_context
        def save_to_database(model):
            db.session.add(model)
            db.session.commit()
            
        # With custom error handling:
        @with_app_context(error_handler=lambda e: logger.error(f"Database error: {e}"))
        def save_with_error_handling(model):
            db.session.add(model)
            db.session.commit()
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                with ensure_app_context():
                    return f(*args, **kwargs)
            except Exception as e:
                if error_handler:
                    return error_handler(e)
                raise  # Re-raise if no error handler
        return wrapper
    
    # This allows the decorator to be used with or without arguments
    if func is None:
        return decorator
    return decorator(func)