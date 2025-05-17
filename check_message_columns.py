"""
Check the actual columns in the Message table to understand what fields we're working with
"""
import os
import logging
import sys
from sqlalchemy import create_engine, inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_message_columns():
    """
    Check the actual columns in the Message table
    """
    try:
        # Get database URL from environment
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL environment variable not set.")
            return False
            
        logger.info(f"Connecting to database: {database_url[:20]}...")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Get inspector
        inspector = inspect(engine)
        
        # Check all tables
        tables = inspector.get_table_names()
        logger.info(f"Tables in database: {tables}")
        
        # Check columns in Message table
        if 'message' in tables:
            columns = inspector.get_columns('message')
            logger.info("Columns in Message table:")
            for column in columns:
                logger.info(f"  - {column['name']} ({column['type']})")
        else:
            logger.warning("Message table does not exist in the database")
            
        return True
            
    except Exception as e:
        logger.error(f"Error checking columns: {e}")
        logger.exception("Check failed with exception:")
        return False

if __name__ == "__main__":
    success = check_message_columns()
    if success:
        logger.info("Check completed successfully")
        sys.exit(0)
    else:
        logger.error("Check failed")
        sys.exit(1)