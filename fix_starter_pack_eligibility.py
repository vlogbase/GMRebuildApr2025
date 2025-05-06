"""
Reset starter pack eligibility for all users by removing any completed transactions.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, MetaData, Table, select, delete

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_eligibility():
    """Reset starter pack eligibility for all users."""
    
    # Get database URL from environment variable
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Create database engine
        engine = create_engine(database_url)
        
        # Define metadata and tables
        metadata = MetaData()
        transactions_table = Table('transaction', metadata, autoload_with=engine)
        package_table = Table('package', metadata, autoload_with=engine)
        
        # Connect to the database
        with engine.connect() as connection:
            # Begin a transaction
            with connection.begin():
                # Delete all completed transactions for andy@sentigral.com (user ID 4)
                delete_stmt = delete(transactions_table).where(
                    transactions_table.c.user_id == 4
                )
                
                result = connection.execute(delete_stmt)
                logger.info(f"Deleted {result.rowcount} transactions for andy@sentigral.com")
                
                # Also find and fix for andysurtees924@gmail.com
                users_table = Table('user', metadata, autoload_with=engine)
                select_stmt = select(users_table.c.id).where(users_table.c.email == 'andysurtees924@gmail.com')
                user_result = connection.execute(select_stmt).fetchone()
                
                if user_result:
                    user_id = user_result[0]
                    delete_stmt = delete(transactions_table).where(
                        transactions_table.c.user_id == user_id
                    )
                    
                    result = connection.execute(delete_stmt)
                    logger.info(f"Deleted {result.rowcount} transactions for andysurtees924@gmail.com")
                else:
                    logger.info("User andysurtees924@gmail.com not found")
                
        logger.info("Successfully reset starter pack eligibility")
        return True
    
    except Exception as e:
        logger.error(f"Error resetting eligibility: {e}")
        return False

if __name__ == "__main__":
    result = reset_eligibility()
    if result:
        print("Successfully reset starter pack eligibility for all users")
    else:
        print("Failed to reset eligibility. See logs for details.")
        sys.exit(1)