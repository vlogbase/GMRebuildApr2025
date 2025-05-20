"""
Script to fix affiliate schema issues in the database.
This comprehensive script ensures all affiliate tables and columns are correctly set up.
"""

import os
import logging
import sys
from sqlalchemy import create_engine, inspect, text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

def main():
    """Run all database schema fixes for affiliate functionality"""
    logger.info("Starting affiliate schema fixes")
    
    # Create database engine
    engine = create_engine(DATABASE_URL)
    
    # Get database inspector
    inspector = inspect(engine)
    
    # Check if tables exist
    tables = inspector.get_table_names()
    logger.info(f"Found {len(tables)} tables in database")
    
    # Check and create/fix affiliate table
    fix_affiliate_table(engine, inspector, tables)
    
    # Check and create/fix customer_referral table
    fix_customer_referral_table(engine, inspector, tables)
    
    # Check and create/fix commission table
    fix_commission_table(engine, inspector, tables)
    
    logger.info("All affiliate schema fixes completed successfully")

def fix_affiliate_table(engine, inspector, tables):
    """Create or fix the affiliate table"""
    if 'affiliate' not in tables:
        logger.info("Creating missing 'affiliate' table")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE affiliate (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(64) NOT NULL,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    paypal_email VARCHAR(120) NULL UNIQUE,
                    paypal_email_verified_at TIMESTAMP NULL,
                    referral_code VARCHAR(16) NOT NULL UNIQUE,
                    referred_by_affiliate_id INTEGER NULL REFERENCES affiliate(id),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending_terms',
                    terms_agreed_at TIMESTAMP NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
        logger.info("'affiliate' table created successfully")
    else:
        logger.info("'affiliate' table exists, checking columns")
        
        # Get existing columns
        columns = {col['name']: col for col in inspector.get_columns('affiliate')}
        
        # Check for missing columns
        if 'terms_agreed_at' not in columns:
            logger.info("Adding missing 'terms_agreed_at' column to affiliate table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE affiliate ADD COLUMN terms_agreed_at TIMESTAMP NULL"))
                conn.commit()
            logger.info("'terms_agreed_at' column added successfully")
            
        # Check if paypal_email is non-nullable and fix it
        if 'paypal_email' in columns and not columns['paypal_email']['nullable']:
            logger.info("Fixing 'paypal_email' column to allow NULL values")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE affiliate ALTER COLUMN paypal_email DROP NOT NULL"))
                conn.commit()
            logger.info("'paypal_email' column fixed to allow NULL values")

def fix_customer_referral_table(engine, inspector, tables):
    """Create or fix the customer_referral table"""
    if 'customer_referral' not in tables:
        logger.info("Creating missing 'customer_referral' table")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE customer_referral (
                    id SERIAL PRIMARY KEY,
                    customer_user_id INTEGER NOT NULL REFERENCES "user"(id),
                    affiliate_id INTEGER NOT NULL REFERENCES affiliate(id),
                    signup_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT customer_affiliate_unique UNIQUE (customer_user_id)
                )
            """))
            conn.commit()
        logger.info("'customer_referral' table created successfully")
    else:
        logger.info("'customer_referral' table exists")

def fix_commission_table(engine, inspector, tables):
    """Create or fix the commission table"""
    if 'commission' not in tables:
        logger.info("Creating missing 'commission' table")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE commission (
                    id SERIAL PRIMARY KEY,
                    affiliate_id INTEGER NOT NULL REFERENCES affiliate(id),
                    triggering_transaction_id VARCHAR(128) NOT NULL,
                    stripe_payment_status VARCHAR(32) NOT NULL,
                    purchase_amount_base FLOAT NOT NULL,
                    commission_rate FLOAT NOT NULL,
                    commission_amount FLOAT NOT NULL,
                    commission_tier INTEGER NOT NULL,
                    currency VARCHAR(3) NOT NULL DEFAULT 'GBP',
                    payment_batch_id VARCHAR(128) NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'held',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Create index for triggering_transaction_id
            conn.execute(text("CREATE INDEX idx_commission_transaction_id ON commission (triggering_transaction_id)"))
            conn.commit()
        logger.info("'commission' table created successfully")
    else:
        logger.info("'commission' table exists")
        
        # Get existing columns
        columns = {col['name']: col for col in inspector.get_columns('commission')}
        
        # Check for missing columns
        if 'commission_tier' not in columns:
            logger.info("Adding missing 'commission_tier' column to commission table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE commission ADD COLUMN commission_tier INTEGER NOT NULL DEFAULT 1"))
                conn.commit()
            logger.info("'commission_tier' column added successfully")
            
        if 'currency' not in columns:
            logger.info("Adding missing 'currency' column to commission table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE commission ADD COLUMN currency VARCHAR(3) NOT NULL DEFAULT 'GBP'"))
                conn.commit()
            logger.info("'currency' column added successfully")

if __name__ == "__main__":
    main()