"""
Database migration for adding model cost filter preferences to the User table.

This script adds the following columns to the User table:
- max_input_cost_filter: Maximum input cost per million tokens a user wants to see
- max_output_cost_filter: Maximum output cost per million tokens a user wants to see
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add cost filter columns to the User table."""
    logger.info("Starting cost filter preferences migration...")
    
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
        
        # Check if max_input_cost_filter column exists
        check_input_col_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'max_input_cost_filter'")
        result = connection.execute(check_input_col_sql)
        input_cost_exists = result.fetchone() is not None
        
        if not input_cost_exists:
            # Add max_input_cost_filter column
            logger.info("Adding max_input_cost_filter column to User table")
            add_input_col_sql = text("ALTER TABLE \"user\" ADD COLUMN max_input_cost_filter FLOAT")
            connection.execute(add_input_col_sql)
        else:
            logger.info("max_input_cost_filter column already exists in User table")
        
        # Check if max_output_cost_filter column exists
        check_output_col_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'max_output_cost_filter'")
        result = connection.execute(check_output_col_sql)
        output_cost_exists = result.fetchone() is not None
        
        if not output_cost_exists:
            # Add max_output_cost_filter column
            logger.info("Adding max_output_cost_filter column to User table")
            add_output_col_sql = text("ALTER TABLE \"user\" ADD COLUMN max_output_cost_filter FLOAT")
            connection.execute(add_output_col_sql)
        else:
            logger.info("max_output_cost_filter column already exists in User table")
        
        # Commit the transaction
        transaction.commit()
        logger.info("Cost filter preferences migration completed successfully")
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