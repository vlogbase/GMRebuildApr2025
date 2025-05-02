"""
Migration script to update the database schema for Stripe integration.

This script adds the following changes to the database:
1. Add stripe_price_id column to the Package table
2. Add stripe_payment_intent column to the Transaction table
3. Add package_id column to the Transaction table (foreign key to Package)
"""

import os
import logging
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, ForeignKey
from sqlalchemy.sql import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run the database migrations for Stripe integration.
    """
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            logger.error("DATABASE_URL not found in environment variables")
            return False
        
        # Create engine and connect to database
        engine = create_engine(db_url)
        conn = engine.connect()
        
        # Create metadata object
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        # Get Package and Transaction tables
        package_table = metadata.tables.get('package')
        transaction_table = metadata.tables.get('transaction')
        
        if not package_table or not transaction_table:
            logger.error("Package or Transaction table not found in database")
            return False
        
        # Check if columns already exist
        package_cols = [col.name for col in package_table.columns]
        transaction_cols = [col.name for col in transaction_table.columns]
        
        # Add stripe_price_id to Package table if it doesn't exist
        if 'stripe_price_id' not in package_cols:
            logger.info("Adding stripe_price_id column to Package table")
            conn.execute('ALTER TABLE package ADD COLUMN stripe_price_id VARCHAR(255);')
        
        # Add stripe_payment_intent to Transaction table if it doesn't exist
        if 'stripe_payment_intent' not in transaction_cols:
            logger.info("Adding stripe_payment_intent column to Transaction table")
            conn.execute('ALTER TABLE transaction ADD COLUMN stripe_payment_intent VARCHAR(255);')
        
        # Add package_id to Transaction table if it doesn't exist
        if 'package_id' not in transaction_cols:
            logger.info("Adding package_id column to Transaction table")
            conn.execute('ALTER TABLE transaction ADD COLUMN package_id INTEGER REFERENCES package(id);')
        
        logger.info("Database migrations completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    
    if success:
        print("Stripe database migrations completed successfully")
        sys.exit(0)
    else:
        print("Failed to run Stripe database migrations")
        sys.exit(1)