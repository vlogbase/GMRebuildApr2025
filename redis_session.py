"""
Redis Session Interface for Flask

This module provides a SessionInterface implementation that uses Redis for
server-side session storage. This allows for better scalability across
multiple application instances.
"""

import pickle
import logging
from datetime import timedelta
from uuid import uuid4

from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict
from redis_cache import redis_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RedisSession")

class RedisSession(CallbackDict, SessionMixin):
    """
    Custom session implementation that works with Redis storage.
    Extends CallbackDict for modification tracking and SessionMixin for Flask compatibility.
    """
    
    def __init__(self, initial=None, sid=None, new=False, prefix='session:'):
        """
        Initialize a new Redis session.
        
        Args:
            initial: Initial session data
            sid: Session ID
            new: Whether this is a new session
            prefix: Redis key prefix for the session
        """
        def on_update(self):
            self.modified = True
            
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False
        self.prefix = prefix


class RedisSessionInterface(SessionInterface):
    """
    A Flask session interface that uses Redis for storage.
    This allows sessions to be shared across multiple application instances.
    """
    
    serializer = pickle
    session_class = RedisSession
    
    def __init__(self, prefix='session:', permanent_lifetime=timedelta(days=31)):
        """
        Initialize the Redis session interface.
        
        Args:
            prefix: Redis key prefix for sessions
            permanent_lifetime: Default lifetime for permanent sessions
        """
        self.prefix = prefix
        self.permanent_lifetime = permanent_lifetime
        
    def _get_redis_expiration_time(self, app, session):
        """
        Get the session expiration time based on Flask app config.
        
        Args:
            app: Flask application
            session: Session object
            
        Returns:
            int: Expiration time in seconds
        """
        if session.permanent:
            return app.permanent_session_lifetime.total_seconds()
        return 86400  # 1 day for non-permanent sessions
    
    def open_session(self, app, request):
        """
        Open an existing session or create a new one.
        
        Args:
            app: Flask application
            request: Flask request object
            
        Returns:
            RedisSession: The session object
        """
        # Check Redis availability
        if not redis_cache.is_available():
            logger.warning("Redis unavailable. Falling back to Flask's default session implementation.")
            return None
        
        # Get the session ID from the cookie
        # Use a default cookie name if app.session_cookie_name is not available
        cookie_name = getattr(app, 'session_cookie_name', 'session')
        sid = request.cookies.get(cookie_name)
        
        # If no session ID, create a new session
        if not sid:
            sid = str(uuid4())
            return self.session_class(sid=sid, new=True, prefix=self.prefix)
        
        # Try to load the session from Redis
        session_key = f"{self.prefix}{sid}"
        val = redis_cache.get(session_key)
        
        if val is not None:
            try:
                data = self.serializer.loads(val)
                return self.session_class(data, sid=sid, prefix=self.prefix)
            except Exception as e:
                logger.error(f"Error deserializing session: {e}")
        
        # If session doesn't exist or is invalid, create a new one
        return self.session_class(sid=sid, new=True, prefix=self.prefix)
    
    def save_session(self, app, session, response):
        """
        Save the session to Redis.
        
        Args:
            app: Flask application
            session: Session object
            response: Flask response object
        """
        # Check Redis availability
        if not redis_cache.is_available():
            logger.warning("Redis unavailable. Cannot save session.")
            return
        
        # Use a default cookie name if app.session_cookie_name is not available
        cookie_name = getattr(app, 'session_cookie_name', 'session')
        
        # Don't save if session should be deleted
        if not session:
            if session.modified:
                session_key = f"{self.prefix}{session.sid}"
                redis_cache.delete(session_key)
                response.delete_cookie(
                    cookie_name,
                    domain=self.get_cookie_domain(app),
                    path=self.get_cookie_path(app)
                )
            return
        
        # Save if the session is modified or new
        if not session.modified and not session.new:
            return
        
        # Get session expiration
        expiry = self._get_redis_expiration_time(app, session)
        
        # Create Redis key
        session_key = f"{self.prefix}{session.sid}"
        
        # Serialize session data
        try:
            val = self.serializer.dumps(dict(session))
            redis_cache.set(session_key, val, int(expiry))
        except Exception as e:
            logger.error(f"Error saving session to Redis: {e}")
        
        # Set the cookie with a default name if session_cookie_name is not available
        cookie_name = getattr(app, 'session_cookie_name', 'session') 
        response.set_cookie(
            cookie_name,
            session.sid,
            expires=self.get_expiration_time(app, session),
            httponly=True,
            domain=self.get_cookie_domain(app),
            path=self.get_cookie_path(app),
            secure=self.get_cookie_secure(app),
            samesite=self.get_cookie_samesite(app)
        )


def setup_redis_session(app):
    """
    Set up Redis sessions for a Flask application.
    
    Args:
        app: Flask application to configure
    """
    # Check if Redis is available
    if not redis_cache.is_available():
        logger.warning("Redis is not available. Continuing with default session implementation.")
        return
    
    # Configure the app to use Redis sessions
    app.session_interface = RedisSessionInterface()
    
    # Set secure cookie flag in production
    app.config.setdefault('SESSION_COOKIE_SECURE', app.config.get('ENV', '') == 'production')
    
    # Set session lifetime (default: 30 days)
    app.config.setdefault('PERMANENT_SESSION_LIFETIME', timedelta(days=30))
    
    logger.info("Redis session interface configured successfully.")