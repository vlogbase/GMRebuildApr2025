"""
Migration script to add PDF URL support to the Message model
This script adds pdf_url and pdf_filename columns to the Message table
"""

import logging
from sqlalchemy import Column, String, Text as SQLText
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run the migrations to add PDF support to the Message model
    Returns True if successful, False if there was an error
    """
    try:
        # Get database URI from environment
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL environment variable not set.")
            return False
            
        logger.info(f"Connecting to database: {database_url[:20]}...")
        
        # Create engine and session
        engine = create_engine(database_url)
        
        # Check if the columns already exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        message_columns = [col['name'] for col in inspector.get_columns('message')]
        
        if 'pdf_url' in message_columns and 'pdf_filename' in message_columns:
            logger.info("PDF URL columns already exist in Message table, skipping migration")
            return True
        
        # Create a new session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Using raw SQL for the migration since it's simpler for adding columns
        if 'pdf_url' not in message_columns:
            logger.info("Adding pdf_url column to Message table")
            session.execute(text('ALTER TABLE message ADD COLUMN pdf_url TEXT'))
        
        if 'pdf_filename' not in message_columns:
            logger.info("Adding pdf_filename column to Message table")
            session.execute(text('ALTER TABLE message ADD COLUMN pdf_filename VARCHAR(255)'))
        
        # Commit the changes
        session.commit()
        
        logger.info("Successfully migrated Message table with PDF support columns")
        return True
        
    except Exception as e:
        logger.error(f"Error during PDF migration: {e}")
        logger.exception("Migration failed with exception:")
        return False

# Run the migrations if this script is executed directly
if __name__ == "__main__":
    success = run_migrations()
    if success:
        print("✅ PDF support migrations completed successfully")
    else:
        print("❌ PDF support migrations failed")
        exit(1)