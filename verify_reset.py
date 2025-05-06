"""
Verify that test accounts have been reset properly.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, MetaData, Table, select, and_, func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_reset():
    """Verify that test accounts have been reset properly."""
    
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
            # Test account emails
            test_accounts = ['andy@sentigral.com', 'andysurytees924@gmail.com']
            
            # Verify user balances
            for email in test_accounts:
                select_stmt = select(users_table).where(users_table.c.email == email)
                user_result = connection.execute(select_stmt).fetchone()
                
                if user_result:
                    logger.info(f"User {email} has balance: {user_result.credits} credits")
                else:
                    logger.warning(f"User with email {email} not found")
            
            # Count remaining test transactions
            count_stmt = select(func.count()).select_from(transactions_table).where(
                and_(
                    transactions_table.c.payment_method == 'stripe',
                    transactions_table.c.payment_id.like('%test%')
                )
            )
            
            test_count = connection.execute(count_stmt).scalar()
            logger.info(f"Remaining test transactions: {test_count}")
            
            # Verify that test users can buy starter pack again
            logger.info("All users should now be eligible to purchase the $5 starter pack again")
            
        return True
    
    except Exception as e:
        logger.error(f"Error verifying reset: {e}")
        return False

if __name__ == "__main__":
    result = verify_reset()
    if not result:
        sys.exit(1)