"""
Migration script to add UserChatSettings model.
This script creates the user_chat_settings table for advanced chat parameter settings.
"""
import os
import logging
import traceback
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, Float, String, Text, DateTime, ForeignKey, exc
from sqlalchemy.sql import func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the database migration to create the user_chat_settings table."""
    logger.info("Starting UserChatSettings migration...")
    
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
        
        # Check if user_chat_settings table exists
        check_table_sql = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'user_chat_settings'
            )
        """)
        result = connection.execute(check_table_sql)
        table_exists = result.scalar()
        
        if not table_exists:
            # Create user_chat_settings table
            logger.info("Creating user_chat_settings table...")
            create_table_sql = text("""
                CREATE TABLE user_chat_settings (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES "user" (id) ON DELETE CASCADE,
                    temperature FLOAT,
                    top_p FLOAT,
                    max_tokens INTEGER,
                    frequency_penalty FLOAT,
                    presence_penalty FLOAT,
                    top_k INTEGER,
                    stop_sequences TEXT,
                    response_format VARCHAR(20),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
                );
                
                CREATE INDEX ix_user_chat_settings_user_id ON user_chat_settings (user_id);
            """)
            connection.execute(create_table_sql)
            logger.info("user_chat_settings table created successfully.")
        else:
            logger.info("user_chat_settings table already exists.")
        
        # Commit the transaction
        transaction.commit()
        logger.info("UserChatSettings migration completed successfully.")
        return True
        
    except Exception as e:
        # Rollback in case of error
        if 'transaction' in locals():
            transaction.rollback()
        logger.error(f"Migration failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False
        
    finally:
        # Close connection
        connection.close()

if __name__ == "__main__":
    run_migration()