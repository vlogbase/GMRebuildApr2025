"""
Database migration to add auto_fallback_enabled to UserChatSettings model.

This script handles the migration to add the auto_fallback_enabled column
to the user_chat_settings table in the database.
"""
import logging
import traceback
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to add auto_fallback_enabled to UserChatSettings table.
    
    This checks if the column exists and adds it if it doesn't.
    """
    try:
        logger.info("Starting UserChatSettings migration...")
        
        # Import what we need to run the migration
        from app import app, db
        from sqlalchemy import inspect, text
        
        with app.app_context():
            # Check if the user_chat_settings table exists
            inspector = inspect(db.engine)
            if 'user_chat_settings' not in inspector.get_table_names():
                logger.warning("user_chat_settings table does not exist, will be created during the next db.create_all()")
                db.create_all()
                logger.info("Created user_chat_settings table.")
                return
            
            # Check if the auto_fallback_enabled column already exists
            columns = [col['name'] for col in inspector.get_columns('user_chat_settings')]
            if 'auto_fallback_enabled' in columns:
                logger.info("auto_fallback_enabled column already exists in user_chat_settings table.")
                return
            
            # Column doesn't exist, add it
            logger.info("Adding auto_fallback_enabled column to user_chat_settings table.")
            
            # Run SQL to add the column with a default value
            with db.engine.connect() as conn:
                # SQLite syntax
                if 'sqlite' in db.engine.url.get_backend_name():
                    conn.execute(text(
                        "ALTER TABLE user_chat_settings ADD COLUMN auto_fallback_enabled BOOLEAN DEFAULT 0 NOT NULL"
                    ))
                # PostgreSQL syntax
                else:
                    conn.execute(text(
                        "ALTER TABLE user_chat_settings ADD COLUMN auto_fallback_enabled BOOLEAN DEFAULT FALSE NOT NULL"
                    ))
                conn.commit()
            
            logger.info("Successfully added auto_fallback_enabled column to user_chat_settings table.")
        
    except Exception as e:
        logger.error(f"Error during UserChatSettings migration: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        run_migration()
        logger.info("UserChatSettings migration completed successfully.")
    except Exception as e:
        logger.error(f"UserChatSettings migration failed: {e}")
        logger.error(traceback.format_exc())