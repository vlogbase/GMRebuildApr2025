"""
Simple script to check if the auto_fallback_enabled column exists in the database
"""
import logging
import sys
from app import app, db
from sqlalchemy import inspect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_auto_fallback_column():
    """Check if auto_fallback_enabled column exists in UserChatSettings table"""
    try:
        with app.app_context():
            # Get database inspector
            inspector = inspect(db.engine)
            
            # Check if user_chat_settings table exists
            if 'user_chat_settings' not in inspector.get_table_names():
                logger.info("user_chat_settings table does not exist. Will be created on next app startup.")
                return False
            
            # Check columns in the table
            columns = [col['name'] for col in inspector.get_columns('user_chat_settings')]
            
            if 'auto_fallback_enabled' in columns:
                logger.info("auto_fallback_enabled column already exists in user_chat_settings table.")
                return True
            else:
                logger.info("auto_fallback_enabled column does NOT exist in user_chat_settings table.")
                return False
            
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False

if __name__ == "__main__":
    if check_auto_fallback_column():
        print("✅ auto_fallback_enabled column exists")
        sys.exit(0)
    else:
        print("❌ auto_fallback_enabled column does NOT exist")
        sys.exit(1)