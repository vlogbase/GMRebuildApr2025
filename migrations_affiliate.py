"""
Migrations script for the affiliate system.

This script adds the affiliate-related database tables and relationships:
- Affiliate table
- CustomerReferral table
- Commission table
"""

import logging
import os
import sys
from datetime import datetime, timedelta
import string
import secrets

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, Text, UniqueConstraint
from sqlalchemy.sql import text
from app import db
from models import CommissionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_referral_code(length=8):
    """Generate a unique referral code"""
    alphabet = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    return code

def run_migrations():
    """Run the affiliate system migrations"""
    logger.info("Starting affiliate system migrations")
    
    try:
        # Get all table names from the database
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f"Existing tables: {tables}")
        
        # Check if affiliate table exists
        if 'affiliate' not in tables:
            logger.info("Creating 'affiliate' table...")
            
            query = """
            CREATE TABLE affiliate (
                id SERIAL PRIMARY KEY,
                name VARCHAR(64) NOT NULL,
                email VARCHAR(120) NOT NULL UNIQUE,
                paypal_email VARCHAR(120) NOT NULL UNIQUE,
                paypal_email_verified_at TIMESTAMP,
                referral_code VARCHAR(16) NOT NULL UNIQUE,
                referred_by_affiliate_id INTEGER REFERENCES affiliate(id),
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_affiliate_email ON affiliate(email);
            CREATE INDEX idx_affiliate_referral_code ON affiliate(referral_code);
            """
            
            db.session.execute(text(query))
            logger.info("Created 'affiliate' table successfully")
        else:
            logger.info("'affiliate' table already exists, skipping creation")
        
        # Check if customer_referral table exists
        if 'customer_referral' not in tables:
            logger.info("Creating 'customer_referral' table...")
            
            query = """
            CREATE TABLE customer_referral (
                id SERIAL PRIMARY KEY,
                customer_user_id INTEGER NOT NULL REFERENCES "user"(id),
                affiliate_id INTEGER NOT NULL REFERENCES affiliate(id),
                signup_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT customer_affiliate_unique UNIQUE (customer_user_id)
            );
            
            CREATE INDEX idx_customer_referral_customer_user_id ON customer_referral(customer_user_id);
            CREATE INDEX idx_customer_referral_affiliate_id ON customer_referral(affiliate_id);
            """
            
            db.session.execute(text(query))
            logger.info("Created 'customer_referral' table successfully")
        else:
            logger.info("'customer_referral' table already exists, skipping creation")
        
        # Check if commission table exists
        if 'commission' not in tables:
            logger.info("Creating 'commission' table...")
            
            # First, create the commission_status enum type if it doesn't exist
            try:
                db.session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'commission_status') THEN
                        CREATE TYPE commission_status AS ENUM (
                            'held', 'approved', 'paid', 'rejected', 'payout_failed', 'payout_initiated'
                        );
                    END IF;
                END
                $$;
                """))
                logger.info("Created 'commission_status' enum type if it didn't exist")
            except Exception as e:
                logger.warning(f"Could not create enum type 'commission_status': {e}")
                logger.info("Will create commission table with VARCHAR status instead")
            
            query = """
            CREATE TABLE commission (
                id SERIAL PRIMARY KEY,
                affiliate_id INTEGER NOT NULL REFERENCES affiliate(id),
                triggering_transaction_id VARCHAR(128) NOT NULL,
                stripe_payment_status VARCHAR(32) NOT NULL,
                purchase_amount_base FLOAT NOT NULL,
                commission_rate FLOAT NOT NULL,
                commission_amount FLOAT NOT NULL,
                commission_level INTEGER NOT NULL,
                status VARCHAR(32) NOT NULL DEFAULT 'held',
                commission_earned_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                commission_available_date TIMESTAMP NOT NULL,
                payout_batch_id VARCHAR(128),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_commission_affiliate_id ON commission(affiliate_id);
            CREATE INDEX idx_commission_triggering_transaction_id ON commission(triggering_transaction_id);
            CREATE INDEX idx_commission_status ON commission(status);
            """
            
            db.session.execute(text(query))
            logger.info("Created 'commission' table successfully")
        else:
            logger.info("'commission' table already exists, skipping creation")
        
        # Commit all changes
        db.session.commit()
        logger.info("All migrations completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error running affiliate system migrations: {e}")
        db.session.rollback()
        return False


if __name__ == "__main__":
    # Set up the Flask app context for running the script directly
    from app import app
    with app.app_context():
        success = run_migrations()
        if success:
            print("Migrations completed successfully!")
            sys.exit(0)
        else:
            print("Migration failed! See log for details.")
            sys.exit(1)