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
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, ForeignKey, text
from sqlalchemy.sql import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run the database migrations for Stripe integration using explicit transactions.
    """
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False

    engine = create_engine(db_url)
    # Use a transaction block for safety (automatically commits/rolls back)
    with engine.begin() as conn:
        try:
            logger.info("Starting database migrations within transaction...")
            metadata = MetaData()
            # Reflect database schema within the transaction
            metadata.reflect(bind=conn)

            package_table = metadata.tables.get('package')
            transaction_table = metadata.tables.get('transaction')

            # Check if tables exist; raise error if not found
            if package_table is None or transaction_table is None:
                table_names = [t for t, exists in [('package', package_table is None), ('transaction', transaction_table is None)] if exists]
                logger.error(f"{', '.join(table_names)} table(s) not found in database.")
                # Raising an error ensures the transaction rolls back
                raise Exception(f"Required table(s) not found during migration: {', '.join(table_names)}")

            # Get column names
            package_cols = [col.name for col in package_table.columns]
            transaction_cols = [col.name for col in transaction_table.columns]

            # Add columns if they don't exist, using text() for raw SQL
            if 'stripe_price_id' not in package_cols:
                logger.info("Adding stripe_price_id column to Package table")
                conn.execute(text('ALTER TABLE package ADD COLUMN stripe_price_id VARCHAR(255);'))

            if 'stripe_payment_intent' not in transaction_cols:
                logger.info("Adding stripe_payment_intent column to Transaction table")
                conn.execute(text('ALTER TABLE transaction ADD COLUMN stripe_payment_intent VARCHAR(255);'))

            if 'package_id' not in transaction_cols:
                logger.info("Adding package_id column to Transaction table")
                conn.execute(text('ALTER TABLE transaction ADD COLUMN package_id INTEGER REFERENCES package(id);'))

            logger.info("Database migrations schema changes completed successfully.")
            # Commit happens automatically when 'with' block exits without error
            return True

        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            # Rollback happens automatically when 'with' block exits with error
            return False
    # Connection is closed automatically by 'with engine.begin()'

if __name__ == "__main__":
    success = run_migrations()
    
    if success:
        print("Stripe database migrations completed successfully")
        sys.exit(0)
    else:
        print("Failed to run Stripe database migrations")
        sys.exit(1)