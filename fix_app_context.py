"""
Fix application context issues in Flask app
"""

import logging
import os
import sys
from sqlalchemy import text
from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_app_context():
    """
    Push the application context if needed, ensuring database operations work correctly
    """
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

def fix_app_context():
    """
    Ensure application context is available globally
    """
    try:
        # Ensure we have the app context
        ensure_app_context()
        
        # Test database connection to verify it works in this context
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("Database connection test successful")
            else:
                logger.error("Database connection test failed with unexpected result")
                return False
        
        logger.info("Application context successfully configured")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing application context: {e}")
        logger.exception("Context fix failed with exception:")
        return False
        
# Run the fix if this script is executed directly
if __name__ == "__main__":
    success = fix_app_context()
    if success:
        print("✅ Application context fix applied successfully")
    else:
        print("❌ Application context fix failed")
        sys.exit(1)