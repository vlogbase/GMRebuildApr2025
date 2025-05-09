#!/usr/bin/env python3

"""
Migration script to add the first_commissioned_purchase_at column to the customer_referral table.
This script adds a new column to track when a customer's first purchase generates a commission.
This is used to implement the one-year commission window policy.
"""

import os
import sys
import logging
from datetime import datetime
from app import app, db
from models import CustomerReferral

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to add the first_commissioned_purchase_at column to the customer_referral table.
    """
    try:
        with app.app_context():
            # Check if the column already exists
            inspect_query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'customer_referral' AND column_name = 'first_commissioned_purchase_at';"
            result = db.session.execute(inspect_query).fetchone()
            
            if result:
                logger.info("The first_commissioned_purchase_at column already exists in the customer_referral table.")
                return True
                
            # Add the column
            logger.info("Adding first_commissioned_purchase_at column to customer_referral table...")
            
            # Create the column
            add_column_query = "ALTER TABLE customer_referral ADD COLUMN first_commissioned_purchase_at TIMESTAMP WITHOUT TIME ZONE;"
            db.session.execute(add_column_query)
            
            # Commit the changes
            db.session.commit()
            
            logger.info("Migration completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    logger.info("Starting affiliate commission window migration...")
    
    success = run_migration()
    
    if success:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)