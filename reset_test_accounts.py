"""
Reset test accounts and starter pack eligibility after transitioning from test to live mode.

This script will:
1. Reset balances for specific test accounts to zero
2. Reset all users' eligibility to purchase the $5 starter pack by removing test transactions

Usage:
    python reset_test_accounts.py
"""

import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from app import db
from models import User, Transaction, PaymentStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_test_accounts():
    """
    Reset balances for test accounts and restore starter pack eligibility for all users.
    """
    try:
        # Test account emails
        test_accounts = ['andy@sentigral.com', 'andysurytees924@gmail.com']
        
        # Find users by email
        test_users = User.query.filter(User.email.in_(test_accounts)).all()
        
        # Reset balances for test accounts
        for user in test_users:
            old_balance = user.credits
            user.credits = 1000  # Reset to default starting value
            logger.info(f"Reset {user.email} balance from {old_balance} to {user.credits} credits")
        
        # Find all test transactions (those with payment_method='stripe' and 'test' in payment_id)
        test_transactions = Transaction.query.filter(
            Transaction.payment_method == 'stripe',
            Transaction.payment_id.like('%test%')
        ).all()
        
        logger.info(f"Found {len(test_transactions)} test transactions to remove")
        
        # Delete test transactions
        for transaction in test_transactions:
            logger.info(f"Deleting test transaction ID: {transaction.id} for user ID: {transaction.user_id}")
            db.session.delete(transaction)
        
        # Commit changes
        db.session.commit()
        logger.info("Successfully reset test accounts and transactions")
        return True
    
    except Exception as e:
        logger.error(f"Error resetting test accounts: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Get app context
    from app import app
    with app.app_context():
        result = reset_test_accounts()
        if result:
            print("Successfully reset test accounts and transactions")
        else:
            print("Failed to reset test accounts. See logs for details.")