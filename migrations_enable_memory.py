"""
Migration script to add enable_memory column to User model.
This script will add the enable_memory column to the User table if it doesn't exist.
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the database migration to add enable_memory field to the User table."""
    logger.info("Starting enable_memory migration...")
    
    # Get database URL from environment variables
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set.")
        return False
    
    # Create database engine
    engine = create_engine(db_url)
    connection = engine.connect()
    
    try:
        # Start a transaction
        transaction = connection.begin()
        
        # Check if enable_memory column exists
        check_column_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'enable_memory'")
        result = connection.execute(check_column_sql)
        enable_memory_exists = result.fetchone() is not None
        
        if not enable_memory_exists:
            # Add enable_memory column
            logger.info("Adding enable_memory column to User table")
            add_enable_memory_sql = text("ALTER TABLE \"user\" ADD COLUMN enable_memory BOOLEAN DEFAULT true")
            connection.execute(add_enable_memory_sql)
        else:
            logger.info("enable_memory column already exists in User table")
        
        # Commit the transaction
        transaction.commit()
        logger.info("Enable memory migration completed successfully")
        return True
        
    except (OperationalError, ProgrammingError) as e:
        logger.error(f"Error during migration: {e}")
        transaction.rollback()
        return False
    finally:
        # Close the connection
        connection.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. Check logs for details.")