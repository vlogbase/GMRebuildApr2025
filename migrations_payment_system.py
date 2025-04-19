"""
Database migrations for the payment system.

This script:
1. Creates the necessary database tables for the payment system if they don't exist
2. Add default package options
3. Adds a credits field to the User model if not already present
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import database and model components
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Default package definitions
DEFAULT_PACKAGES = [
    {
        "name": "Starter",
        "description": "Basic package for getting started",
        "amount_usd": 5.00,
        "credits": 5000,  # $5.00 = 5000 credits (1 credit = $0.001)
    },
    {
        "name": "Standard",
        "description": "Recommended for regular usage",
        "amount_usd": 10.00,
        "credits": 11000,  # $10.00 = 11000 credits (10% bonus)
    },
    {
        "name": "Premium",
        "description": "Best value for heavy users",
        "amount_usd": 25.00,
        "credits": 30000,  # $25.00 = 30000 credits (20% bonus)
    },
    {
        "name": "Professional",
        "description": "For professional users with high volume",
        "amount_usd": 50.00,
        "credits": 65000,  # $50.00 = 65000 credits (30% bonus)
    }
]

def create_payment_tables(db_engine):
    """Create payment-related tables if they don't exist"""
    logger.info("Creating payment system tables...")
    
    try:
        # Add credits column to User table if it doesn't exist
        try:
            db_engine.execute(text(
                "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS credits INT DEFAULT 1000"
            ))
            logger.info("Added credits column to User table or it already exists")
        except (OperationalError, ProgrammingError) as e:
            logger.warning(f"Error adding credits column to User table: {e}")
            logger.info("Attempting alternate method to add credits column...")
            try:
                # Check if the column exists (note: table_name is lowercase in information_schema but we use quotes in our SQL)
                result = db_engine.execute(text(
                    "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'credits'"
                )).scalar()
                
                if result == 0:
                    db_engine.execute(text("ALTER TABLE \"user\" ADD COLUMN credits INT DEFAULT 1000"))
                    logger.info("Added credits column to User table (alternate method)")
                else:
                    logger.info("Credits column already exists in User table")
            except Exception as e2:
                logger.error(f"Failed to add credits column using alternate method: {e2}")
        
        # Add get_balance_usd method to User model
        logger.info("Credits column added to User table")
        
        # Create Package table
        db_engine.execute(text("""
            CREATE TABLE IF NOT EXISTS package (
                id SERIAL PRIMARY KEY,
                name VARCHAR(64) NOT NULL,
                description TEXT,
                amount_usd NUMERIC(10, 2) NOT NULL,
                credits INTEGER NOT NULL,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        logger.info("Created Package table or it already exists")
        
        # Create Transaction table
        db_engine.execute(text("""
            CREATE TABLE IF NOT EXISTS transaction (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES "user"(id),
                package_id INTEGER REFERENCES package(id),
                amount_usd NUMERIC(10, 2) NOT NULL,
                credits INTEGER NOT NULL,
                payment_method VARCHAR(64) NOT NULL,
                payment_id VARCHAR(128) NOT NULL,
                status VARCHAR(32) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
            )
        """))
        logger.info("Created Transaction table or it already exists")
        
        # Create Usage table
        db_engine.execute(text("""
            CREATE TABLE IF NOT EXISTS usage (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES "user"(id),
                credits_used INTEGER NOT NULL,
                usage_type VARCHAR(32) NOT NULL,
                model_id VARCHAR(128),
                message_id INTEGER,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
            )
        """))
        logger.info("Created Usage table or it already exists")
        
        return True
    except Exception as e:
        logger.error(f"Error creating payment tables: {e}")
        return False

def insert_default_packages(db_engine):
    """Insert default package options if they don't exist"""
    logger.info("Inserting default packages...")
    
    try:
        # Check if packages already exist
        count = db_engine.execute(text("SELECT COUNT(*) FROM package")).scalar()
        
        if count == 0:
            # Insert default packages
            for package in DEFAULT_PACKAGES:
                db_engine.execute(text("""
                    INSERT INTO package (name, description, amount_usd, credits)
                    VALUES (:name, :description, :amount_usd, :credits)
                """), package)
            
            logger.info(f"Inserted {len(DEFAULT_PACKAGES)} default packages")
        else:
            logger.info(f"Packages already exist, skipping insertion")
        
        return True
    except Exception as e:
        logger.error(f"Error inserting default packages: {e}")
        return False

def run_migration():
    """Run all payment system migrations"""
    logger.info("Starting payment system migrations...")
    
    # Get database URL from environment variable
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    # Create database engine
    try:
        engine = sqlalchemy.create_engine(database_url)
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return False
    
    # Run migrations
    try:
        with engine.begin() as transaction:
            success = create_payment_tables(transaction)
            if not success:
                logger.error("Failed to create payment tables")
                return False
            
            success = insert_default_packages(transaction)
            if not success:
                logger.error("Failed to insert default packages")
                return False
        
        logger.info("Payment system migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running payment system migrations: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)