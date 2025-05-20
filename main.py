"""
Main entry point for the application
This file imports the Flask app instance from app.py
"""
import os
import logging
from flask_session import Session
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set session configuration
logger.info("Configuring Flask session")

# Try to use Redis for sessions if available
try:
    from redis_config import initialize_redis_client, is_redis_available
    
    # Check if Redis is available
    if is_redis_available('session'):
        logger.info("Redis available, configuring Redis sessions")
        redis_client = initialize_redis_client('session', decode_responses=False)
        
        if redis_client:
            app.config['SESSION_TYPE'] = 'redis'
            app.config['SESSION_PERMANENT'] = False
            app.config['SESSION_USE_SIGNER'] = True
            app.config['SESSION_KEY_PREFIX'] = 'gloria_mundo_session:'
            app.config['SESSION_COOKIE_NAME'] = 'gloria_mundo_session'
            app.config['SESSION_REDIS'] = redis_client
            logger.info("Redis session configuration complete")
        else:
            logger.warning("Redis client initialization failed, falling back to filesystem sessions")
            app.config['SESSION_TYPE'] = 'filesystem'
            app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
    else:
        logger.info("Redis not available, using filesystem sessions")
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
        
except ImportError as e:
    logger.warning(f"Redis modules not available: {e}")
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
except Exception as e:
    logger.error(f"Error setting up Redis sessions: {e}")
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')

# Common session settings regardless of backend
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'gloria_mundo_session:'
app.config['SESSION_COOKIE_NAME'] = 'gloria_mundo_session'

# Initialize Flask-Session
Session(app)
logger.info(f"Flask session initialized with {app.config['SESSION_TYPE']} backend")

# Register health check routes for deployment health checks
try:
    from gunicorn_health_check import init_app as init_health_check
    init_health_check(app)
    logger.info("Health check routes registered successfully")
except ImportError as e:
    logger.warning(f"Failed to import health check module: {e}")
except Exception as e:
    logger.error(f"Error registering health check routes: {e}")

# This ensures that the app is available for Gunicorn
# as specified in the .replit configuration file
if __name__ == "__main__":
    logger.info("Starting Flask application in development mode")
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # When running under Gunicorn, log the startup
    logger.info("Flask application loaded by Gunicorn")