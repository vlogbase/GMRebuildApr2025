"""
Migrations script for Affiliate System

This script handles database migrations for the affiliate system models.
"""

import logging
import os
from datetime import datetime

# Import SQLAlchemy components
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import Enum

from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run migrations for affiliate system"""
    logger.info("Running affiliate system migrations...")
    
    # Get database URI from app config
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    
    if not database_uri:
        logger.error("DATABASE_URL environment variable not set. Aborting migrations.")
        return False
    
    try:
        # Create engine and metadata
        engine = create_engine(database_uri)
        metadata = MetaData()
        
        # Define tables if they don't exist
        
        # Create Affiliate table if it doesn't exist
        if not engine.dialect.has_table(engine, 'affiliate'):
            logger.info("Creating affiliate table...")
            affiliate_table = Table(
                'affiliate',
                metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String(128), nullable=False),
                Column('email', String(120), unique=True, nullable=False, index=True),
                Column('paypal_email', String(120), nullable=False),
                Column('paypal_email_verified_at', DateTime, nullable=True),
                Column('referral_code', String(16), unique=True, nullable=False, index=True),
                Column('referred_by_affiliate_id', Integer, ForeignKey('affiliate.id', ondelete='SET NULL'), nullable=True),
                Column('status', String(20), nullable=False, default='active'),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            )
            affiliate_table.create(engine)
            logger.info("Affiliate table created successfully")
        else:
            logger.info("Affiliate table already exists")
        
        # Create CustomerReferral table if it doesn't exist
        if not engine.dialect.has_table(engine, 'customer_referral'):
            logger.info("Creating customer_referral table...")
            customer_referral_table = Table(
                'customer_referral',
                metadata,
                Column('id', Integer, primary_key=True),
                Column('customer_user_id', Integer, ForeignKey('user.id'), nullable=False, unique=True),
                Column('affiliate_id', Integer, ForeignKey('affiliate.id'), nullable=False),
                Column('signup_date', DateTime, default=datetime.utcnow),
                Column('created_at', DateTime, default=datetime.utcnow)
            )
            customer_referral_table.create(engine)
            logger.info("CustomerReferral table created successfully")
        else:
            logger.info("CustomerReferral table already exists")
        
        # Create Commission table if it doesn't exist
        if not engine.dialect.has_table(engine, 'commission'):
            logger.info("Creating commission table...")
            commission_table = Table(
                'commission',
                metadata,
                Column('id', Integer, primary_key=True),
                Column('affiliate_id', Integer, ForeignKey('affiliate.id'), nullable=False),
                Column('triggering_transaction_id', String(128), nullable=False, index=True),
                Column('stripe_payment_status', String(20), nullable=False),
                Column('purchase_amount_base', Numeric(10, 4), nullable=False),
                Column('commission_rate', Numeric(6, 4), nullable=False),
                Column('commission_amount', Numeric(10, 2), nullable=False),
                Column('commission_level', Integer, nullable=False),
                Column('status', String(20), nullable=False, default='held'),
                Column('commission_earned_date', DateTime, nullable=False, default=datetime.utcnow),
                Column('commission_available_date', DateTime, nullable=False),
                Column('payout_batch_id', String(128), nullable=True),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            )
            commission_table.create(engine)
            logger.info("Commission table created successfully")
        else:
            logger.info("Commission table already exists")
        
        # Check if we need to add is_admin to User table if it doesn't exist
        inspector = inspect(engine)
        columns = inspector.get_columns('user')
        column_names = [c['name'] for c in columns]
        
        if 'is_admin' not in column_names:
            logger.info("Adding is_admin column to user table...")
            
            # Create a temporary connection
            connection = engine.connect()
            
            # Execute ALTER TABLE statement to add the column
            connection.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
            
            # Close the connection
            connection.close()
            
            logger.info("Added is_admin column to user table")
        else:
            logger.info("is_admin column already exists in user table")
        
        # Update a specific admin user
        if os.environ.get('ADMIN_EMAIL'):
            admin_email = os.environ.get('ADMIN_EMAIL')
            logger.info(f"Setting admin privileges for {admin_email}...")
            
            # Create session
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Update the user
            admin_update_query = f"UPDATE user SET is_admin = TRUE WHERE email = '{admin_email}'"
            session.execute(admin_update_query)
            
            # Commit and close session
            session.commit()
            session.close()
            
            logger.info(f"Admin privileges set for {admin_email}")
        
        logger.info("Affiliate system migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running affiliate system migrations: {e}")
        return False

# Add inspector import at the top level to avoid NameError
from sqlalchemy import inspect

if __name__ == "__main__":
    with app.app_context():
        run_migrations()