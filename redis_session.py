"""
Redis Session Module

This module provides a Redis-backed session interface for Flask applications.
It allows sessions to be shared across multiple application instances, enabling
horizontal scaling and improved reliability.
"""

import json
import pickle
import uuid
import logging
from datetime import timedelta
from typing import Dict, Any, Optional, MutableMapping, Mapping, Iterable, Union, Tuple

from flask import Flask
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict

# Import Redis cache module
from redis_cache import get_redis_connection, RedisCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisSession(CallbackDict, SessionMixin):
    """Redis-backed session implementation"""
    
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
            
        CallbackDict.__init__(self, initial or {}, on_update)
        self.sid = sid
        self.new = new
        self.modified = False
        self.permanent = True
    
    def __getitem__(self, key):
        return super().__getitem__(key)
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        
    def __delitem__(self, key):
        super().__delitem__(key)
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def update(self, other=None, **kwargs):
        if other:
            for key, value in other.items() if hasattr(other, 'items') else other:
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value

class RedisSessionInterface(SessionInterface):
    """Session interface that uses Redis as the session backend"""
    
    serializer = json
    session_class = RedisSession
    
    def __init__(self, prefix='session:', expire=86400, redis_url=None):
        """
        Initialize the session interface
        
        Args:
            prefix: Key prefix for session data in Redis
            expire: Session expiration time in seconds (default: 1 day)
            redis_url: Redis URL (optional, will use environment variable if None)
        """
        self.prefix = prefix
        self.expire = expire
        self.redis = RedisCache(namespace=prefix, expire_time=expire)
        self.redis_conn = get_redis_connection(redis_url)
    
    def _get_redis_session_key(self, sid):
        """Get the Redis key for a session ID"""
        return f"{self.prefix}{sid}"
    
    def open_session(self, app: Flask, request):
        """
        Open a session
        
        Args:
            app: Flask application
            request: Flask request
            
        Returns:
            RedisSession: Session object
        """
        sid = request.cookies.get(app.session_cookie_name)
        
        if not sid:
            # Create a new session
            sid = str(uuid.uuid4())
            return self.session_class(sid=sid, new=True)
            
        # Try to load existing session
        try:
            data = self.redis.get(sid)
            if data is not None:
                data = self.serializer.loads(data)
                return self.session_class(data, sid=sid)
        except Exception as e:
            logger.error(f"Error loading session {sid}: {e}")
        
        # Return a new session if loading failed
        return self.session_class(sid=sid, new=True)
            
    def save_session(self, app: Flask, session, response):
        """
        Save a session
        
        Args:
            app: Flask application
            session: Session object
            response: Flask response
            
        Returns:
            None
        """
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        
        # Skip saving if session should be deleted
        if not session:
            if session.modified:
                self.redis.delete(session.sid)
                response.delete_cookie(
                    app.session_cookie_name,
                    domain=domain,
                    path=path
                )
            return
            
        # Skip saving if session is not modified
        if not session.modified:
            return
            
        # Set session expiration
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        samesite = self.get_cookie_samesite(app)
        
        # Get session expiration
        timeout = self.expire
        if session.permanent:
            timeout = app.permanent_session_lifetime.total_seconds()
        
        # Save session data to Redis
        try:
            data = dict(session)
            self.redis.set(session.sid, self.serializer.dumps(data), expire=int(timeout))
        except Exception as e:
            logger.error(f"Error saving session {session.sid}: {e}")
            
        # Set cookie
        response.set_cookie(
            app.session_cookie_name,
            session.sid,
            expires=self.get_expiration_time(app, session),
            httponly=httponly,
            domain=domain,
            path=path,
            secure=secure,
            samesite=samesite
        )

def setup_redis_session(app: Flask, expire: int = 86400, redis_url: Optional[str] = None) -> None:
    """
    Set up Redis session interface for a Flask application
    
    Args:
        app: Flask application
        expire: Session expiration time in seconds (default: 1 day)
        redis_url: Redis URL (optional, will use environment variable if None)
        
    Returns:
        None
    """
    # Use Redis as the session interface
    try:
        session_interface = RedisSessionInterface(expire=expire, redis_url=redis_url)
        app.session_interface = session_interface
        logger.info("Redis session interface configured")
    except Exception as e:
        logger.error(f"Error setting up Redis session interface: {e}")
        logger.info("Falling back to Flask's default session interface")