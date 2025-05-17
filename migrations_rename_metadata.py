"""
Run migrations to rename the 'metadata' column to 'message_metadata' in the Message table

This is necessary because 'metadata' is a reserved attribute name in SQLAlchemy's Declarative API.
"""
import os
import logging
import sys
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run migrations to rename the metadata column
    """
    try:
        # Get database URL from environment
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL environment variable not set.")
            return False
            
        logger.info(f"Connecting to database: {database_url[:20]}...")
        
        # Create engine and connection
        engine = create_engine(database_url)
        conn = engine.connect()
        
        # Check if the metadata column exists and message_metadata doesn't
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('message')]
        
        if 'metadata' in columns and 'message_metadata' not in columns:
            logger.info("Renaming 'metadata' column to 'message_metadata' in Message table...")
            
            # Execute the column rename
            conn.execute(text('ALTER TABLE message RENAME COLUMN metadata TO message_metadata'))
            
            # Commit the transaction
            conn.commit()
            logger.info("✅ Successfully renamed 'metadata' column to 'message_metadata'")
            return True
            
        elif 'metadata' not in columns and 'message_metadata' in columns:
            logger.info("✅ Column already renamed (message_metadata exists, metadata doesn't)")
            return True
            
        elif 'metadata' in columns and 'message_metadata' in columns:
            logger.warning("Both 'metadata' and 'message_metadata' columns exist. This is unexpected.")
            # In this case, we might want to copy data from one to the other, but for now just report
            return False
            
        else:
            logger.warning("Neither 'metadata' nor 'message_metadata' columns exist in the Message table")
            return False
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        logger.exception("Migration failed with exception:")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = run_migrations()
    if success:
        logger.info("Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("Migration failed")
        sys.exit(1)