"""
Migrations script for the affiliate system tables.

This script creates the necessary tables for the affiliate system if they don't exist.
"""

import os
import logging
from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint, Enum, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# Define enums
class AffiliateStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class CommissionStatus(enum.Enum):
    HELD = "held"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"
    PAYOUT_FAILED = "payout_failed"

# Define models
class Affiliate(Base):
    __tablename__ = 'affiliate'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    paypal_email = Column(String(120), unique=True, nullable=False)
    paypal_email_verified_at = Column(DateTime, nullable=True)
    referral_code = Column(String(16), unique=True, nullable=False, index=True)
    referred_by_affiliate_id = Column(Integer, ForeignKey('affiliate.id', ondelete='SET NULL'), nullable=True)
    status = Column(String(20), nullable=False, default=AffiliateStatus.ACTIVE.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CustomerReferral(Base):
    __tablename__ = 'customer_referral'
    
    id = Column(Integer, primary_key=True)
    customer_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    affiliate_id = Column(Integer, ForeignKey('affiliate.id'), nullable=False)
    signup_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('customer_user_id', name='unique_customer_referral'),
    )

class Commission(Base):
    __tablename__ = 'commission'
    
    id = Column(Integer, primary_key=True)
    affiliate_id = Column(Integer, ForeignKey('affiliate.id'), nullable=False)
    triggering_transaction_id = Column(String(128), nullable=False, index=True)
    stripe_payment_status = Column(String(20), nullable=False)
    purchase_amount_base = Column(Numeric(10, 4), nullable=False)  # Base amount for calculation (GBP)
    commission_rate = Column(Numeric(6, 4), nullable=False)  # Decimal rate (e.g., 0.10 for 10%)
    commission_amount = Column(Numeric(10, 2), nullable=False)  # Commission amount in GBP
    commission_level = Column(Integer, nullable=False)  # 1 for L1, 2 for L2
    status = Column(String(20), nullable=False, default=CommissionStatus.HELD.value)
    commission_earned_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    commission_available_date = Column(DateTime, nullable=False)
    payout_batch_id = Column(String(128), nullable=True)  # PayPal Payout batch ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Add is_admin field to User model if it doesn't exist
def add_is_admin_to_user():
    from sqlalchemy import inspect
    from app import db
    from models import User
    
    inspector = inspect(db.engine)
    columns = [column['name'] for column in inspector.get_columns('user')]
    
    if 'is_admin' not in columns:
        logger.info("Adding is_admin column to User model")
        db.engine.execute('ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT FALSE')
        logger.info("is_admin column added to User model")

def run_migrations():
    """Run database migrations for the affiliate system"""
    logger.info("Running migrations for affiliate system")
    
    try:
        from app import db
        
        # Create tables if they don't exist
        engine = db.engine
        Base.metadata.create_all(engine, tables=[
            Affiliate.__table__,
            CustomerReferral.__table__,
            Commission.__table__
        ])
        
        # Add is_admin field to User model if it doesn't exist
        add_is_admin_to_user()
        
        logger.info("Affiliate system migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise

if __name__ == "__main__":
    run_migrations()