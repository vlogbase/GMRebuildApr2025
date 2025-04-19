"""
Migration script to add Google authentication fields to the User model.
This script will safely modify the User table to include google_id, profile_picture,
and last_login_at columns without losing any existing data.
"""
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the database migration to add Google auth fields to the User table."""
    logger.info("Starting Google authentication migration...")
    
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
        
        # Check if google_id column exists
        check_column_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'google_id'")
        result = connection.execute(check_column_sql)
        google_id_exists = result.fetchone() is not None
        
        if not google_id_exists:
            # Add google_id column
            logger.info("Adding google_id column to User table")
            add_google_id_sql = text("ALTER TABLE \"user\" ADD COLUMN google_id VARCHAR(128) UNIQUE")
            connection.execute(add_google_id_sql)
            
            # Create index on google_id
            logger.info("Creating index on google_id column")
            create_index_sql = text("CREATE INDEX ix_user_google_id ON \"user\" (google_id)")
            connection.execute(create_index_sql)
        else:
            logger.info("google_id column already exists in User table")
        
        # Check if profile_picture column exists
        check_column_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'profile_picture'")
        result = connection.execute(check_column_sql)
        profile_picture_exists = result.fetchone() is not None
        
        if not profile_picture_exists:
            # Add profile_picture column
            logger.info("Adding profile_picture column to User table")
            add_profile_picture_sql = text("ALTER TABLE \"user\" ADD COLUMN profile_picture VARCHAR(512)")
            connection.execute(add_profile_picture_sql)
        else:
            logger.info("profile_picture column already exists in User table")
        
        # Check if last_login_at column exists
        check_column_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'last_login_at'")
        result = connection.execute(check_column_sql)
        last_login_at_exists = result.fetchone() is not None
        
        if not last_login_at_exists:
            # Add last_login_at column
            logger.info("Adding last_login_at column to User table")
            add_last_login_sql = text("ALTER TABLE \"user\" ADD COLUMN last_login_at TIMESTAMP")
            connection.execute(add_last_login_sql)
        else:
            logger.info("last_login_at column already exists in User table")
        
        # Commit the transaction
        transaction.commit()
        logger.info("Google authentication migration completed successfully")
        return True
        
    except (OperationalError, ProgrammingError) as e:
        logger.error(f"Error during migration: {e}")
        transaction.rollback()
        return False
    finally:
        connection.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. Check logs for details.")