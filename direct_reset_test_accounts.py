"""
Direct database script to reset test accounts and starter pack eligibility.

This script connects directly to the database to:
1. Reset balances for specific test users to the default value of 1000 credits
2. Delete all test transactions to reset starter pack eligibility

It avoids loading the full application for faster execution.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select, update, delete, and_

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_test_accounts():
    """Reset test account balances and remove test transactions."""
    
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
        users_table = Table('user', metadata, autoload_with=engine)
        transactions_table = Table('transaction', metadata, autoload_with=engine)
        
        # Connect to the database
        with engine.connect() as connection:
            # Begin a transaction
            with connection.begin():
                # Test account emails
                test_accounts = ['andy@sentigral.com', 'andysurytees924@gmail.com']
                
                # Reset balances for test accounts
                for email in test_accounts:
                    # Find user by email
                    select_stmt = select(users_table).where(users_table.c.email == email)
                    user_result = connection.execute(select_stmt).fetchone()
                    
                    if user_result:
                        user_id = user_result.id
                        old_balance = user_result.credits
                        
                        # Update user balance
                        update_stmt = update(users_table).where(users_table.c.id == user_id).values(credits=1000)
                        connection.execute(update_stmt)
                        
                        logger.info(f"Reset {email} balance from {old_balance} to 1000 credits")
                
                # Find all test transactions (payment_method='stripe' and 'test' in payment_id)
                delete_stmt = delete(transactions_table).where(
                    and_(
                        transactions_table.c.payment_method == 'stripe',
                        transactions_table.c.payment_id.like('%test%')
                    )
                )
                
                result = connection.execute(delete_stmt)
                logger.info(f"Deleted {result.rowcount} test transactions")
                
        logger.info("Successfully reset test accounts and transactions")
        return True
    
    except Exception as e:
        logger.error(f"Error resetting test accounts: {e}")
        return False

if __name__ == "__main__":
    result = reset_test_accounts()
    if result:
        print("Successfully reset test accounts and transactions")
    else:
        print("Failed to reset test accounts. See logs for details.")
        sys.exit(1)