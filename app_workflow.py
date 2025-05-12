"""
Simple script to run the Flask application for testing in the Replit environment.
This is a wrapper script to start the app.py Flask application.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_app_context():
    """
    Push the application context if needed, ensuring database operations work correctly
    """
    from app import app
    
    try:
        # Try to access configuration which requires app context
        app.config["SQLALCHEMY_DATABASE_URI"]
        logger.info("Application context is already active")
        return True
    except RuntimeError:
        # Push the application context
        logger.info("Pushing Flask application context")
        app.app_context().push()
        logger.info("Application context is now active")
        return True
    except Exception as e:
        logger.error(f"Error ensuring app context: {e}")
        return False

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        logger.info("Starting Flask application for testing")
        
        # Import the Flask app from app.py
        from app import app, db
        
        # Set debug mode
        app.config['DEBUG'] = True
        
        # Ensure application context is pushed
        ensure_app_context()
        
        # Test database connection to verify it works in this context
        from sqlalchemy import text
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
                if row and row[0] == 1:
                    logger.info("Database connection test successful")
                else:
                    logger.warning("Database connection test failed with unexpected result")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
        
        # Log CSRF protection status
        if app.config.get('WTF_CSRF_ENABLED', True):
            logger.info("CSRF protection is ENABLED")
        else:
            logger.warning("CSRF protection is DISABLED")
            
        # Log protection settings
        logger.info(f"CSRF methods: {app.config.get('WTF_CSRF_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE'])}")
        logger.info(f"CSRF headers: {app.config.get('WTF_CSRF_HEADERS', ['X-CSRFToken', 'X-CSRF-Token'])}")
        
        # Start the Flask server
        logger.info("Starting Flask application. Access it via http://localhost:5000")
        app.run(host='0.0.0.0', port=5000)
        
    except Exception as e:
        logger.error(f"Error starting Flask application: {e}")
        raise

if __name__ == "__main__":
    run()