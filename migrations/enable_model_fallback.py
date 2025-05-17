"""
Migration script to add enable_model_fallback to User model.
This script adds a boolean field to determine whether fallback behavior is enabled.
"""
import os
import logging
import traceback
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the database migration to add enable_model_fallback to User model."""
    logger.info("Starting enable_model_fallback migration...")
    
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
        
        # Check if column exists
        check_column_sql = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'enable_model_fallback'
            )
        """)
        result = connection.execute(check_column_sql)
        column_exists = result.scalar()
        
        if not column_exists:
            # Add enable_model_fallback column to user table
            logger.info("Adding enable_model_fallback column to user table...")
            add_column_sql = text("""
                ALTER TABLE "user" 
                ADD COLUMN enable_model_fallback BOOLEAN NOT NULL DEFAULT true
            """)
            connection.execute(add_column_sql)
            
            logger.info("Column enable_model_fallback added successfully.")
        else:
            logger.info("Column enable_model_fallback already exists, skipping.")
        
        # Commit the transaction
        transaction.commit()
        logger.info("Migration completed successfully.")
        return True
        
    except Exception as e:
        # Rollback the transaction on error
        transaction.rollback()
        logger.error(f"Migration failed: {e}")
        logger.error(traceback.format_exc())
        return False
        
    finally:
        # Close the connection
        connection.close()

if __name__ == "__main__":
    run_migration()