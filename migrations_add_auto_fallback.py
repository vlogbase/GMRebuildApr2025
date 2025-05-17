"""
Add auto_fallback_enabled column to UserChatSettings table.

This migration adds a new boolean column to indicate whether a user prefers to 
automatically fall back to an alternative model when their selected model isn't available.
"""
import logging
import traceback
from flask import current_app
from sqlalchemy import Boolean, Column
from sqlalchemy.sql import text
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to add auto_fallback_enabled column to UserChatSettings table.
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    try:
        logger.info("Starting UserChatSettings auto_fallback migration...")
        
        # Check if the column already exists
        with db.engine.connect() as connection:
            insp = db.inspect(db.engine)
            columns = insp.get_columns('user_chat_settings')
            column_names = [col['name'] for col in columns]
            
            if 'auto_fallback_enabled' in column_names:
                logger.info("auto_fallback_enabled column already exists, skipping migration")
                return True
            
            # Add the column with default value of False
            logger.info("Adding auto_fallback_enabled column to user_chat_settings table...")
            connection.execute(text(
                "ALTER TABLE user_chat_settings ADD COLUMN auto_fallback_enabled BOOLEAN NOT NULL DEFAULT false"
            ))
            
            connection.commit()
            logger.info("Migration successful")
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Import app and run migration within app context
    from app import app
    with app.app_context():
        run_migration()