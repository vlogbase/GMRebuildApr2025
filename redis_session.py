"""
Redis Session Module

This module provides a Redis-backed session interface for Flask.
It allows session data to be stored in Redis instead of signed cookies,
which enables session sharing across multiple application instances.
"""

import pickle
import uuid
from datetime import timedelta
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict
from flask import current_app

from redis_cache import get_redis_connection

class RedisSession(CallbackDict, SessionMixin):
    """Redis-backed session implementation"""
    
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
            
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False

class RedisSessionInterface(SessionInterface):
    """Interface for Redis-backed sessions"""
    
    def __init__(self, prefix='session:', expiry=86400, key_prefix=''):
        """
        Initialize the Redis session interface
        
        Args:
            prefix (str): Prefix to use for session keys in Redis
            expiry (int): Session expiration time in seconds (default: 1 day)
            key_prefix (str): Additional prefix for session keys
        """
        self.prefix = prefix
        self.expiry = expiry
        self.key_prefix = key_prefix
        self._redis = None
    
    def _get_redis(self):
        """Get a Redis connection"""
        if self._redis is None:
            self._redis = get_redis_connection()
        return self._redis
    
    def _get_prefix(self):
        """Get the full session key prefix"""
        if self.key_prefix:
            return f'{self.key_prefix}:{self.prefix}'
        return self.prefix
    
    def _generate_sid(self):
        """Generate a unique session ID"""
        return str(uuid.uuid4())
    
    def _get_redis_session_key(self, sid):
        """Get the Redis key for a session"""
        return f'{self._get_prefix()}{sid}'
    
    def open_session(self, app, request):
        """
        Open a session from the request
        
        Args:
            app: The Flask app
            request: The request object
            
        Returns:
            RedisSession: The session object
        """
        sid = request.cookies.get(app.session_cookie_name)
        
        if not sid:
            # No session ID, create a new session
            sid = self._generate_sid()
            return RedisSession(sid=sid, new=True)
        
        # Try to load the session from Redis
        redis_key = self._get_redis_session_key(sid)
        session_data = None
        
        try:
            val = self._get_redis().get(redis_key)
            if val is not None:
                session_data = pickle.loads(val)
        except Exception as e:
            current_app.logger.error(f"Error loading session: {str(e)}")
            # If there's an error, create a new session
            sid = self._generate_sid()
            return RedisSession(sid=sid, new=True)
        
        if session_data is not None:
            # Session exists, return it
            return RedisSession(session_data, sid=sid)
        
        # Session doesn't exist or is expired, create a new one
        sid = self._generate_sid()
        return RedisSession(sid=sid, new=True)
    
    def save_session(self, app, session, response):
        """
        Save the session
        
        Args:
            app: The Flask app
            session: The session object
            response: The response object
        """
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        
        # Don't save empty sessions
        if not session:
            if session.modified:
                try:
                    # Delete the session from Redis
                    self._get_redis().delete(self._get_redis_session_key(session.sid))
                except Exception as e:
                    current_app.logger.error(f"Error deleting session: {str(e)}")
                
                # Delete the cookie
                response.delete_cookie(
                    app.session_cookie_name,
                    domain=domain,
                    path=path
                )
            return
        
        # Do we need to set the cookie?
        if session.modified or session.new:
            # Set expiration
            expiry = self.get_expiration_time(app, session)
            
            # Determine Redis expiration time
            if expiry is None:
                redis_exp = self.expiry
            else:
                redis_exp = int(total_seconds(expiry - timedelta(seconds=1)))
                
            # Save to Redis
            redis_key = self._get_redis_session_key(session.sid)
            session_data = pickle.dumps(dict(session))
            
            try:
                self._get_redis().setex(redis_key, redis_exp, session_data)
            except Exception as e:
                current_app.logger.error(f"Error saving session: {str(e)}")
            
            # Set the cookie
            response.set_cookie(
                app.session_cookie_name,
                session.sid,
                expires=expiry,
                httponly=True,
                domain=domain,
                path=path,
                secure=self.get_cookie_secure(app),
                samesite=self.get_cookie_samesite(app)
            )

def total_seconds(td):
    """
    Get the total seconds from a timedelta
    
    This is needed for compatibility with Python < 2.7
    
    Args:
        td (timedelta): The timedelta
        
    Returns:
        int: Total seconds
    """
    return td.days * 24 * 60 * 60 + td.seconds