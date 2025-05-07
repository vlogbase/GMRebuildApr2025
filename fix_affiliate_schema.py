#!/usr/bin/env python3
"""
Quick fix script to add the terms_agreed_at column to the affiliate table.
This is a simplified version of the migrations_affiliate_update.py script.
"""

import logging
from sqlalchemy.sql import text
from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_affiliate_schema():
    """Add the terms_agreed_at column to the affiliate table"""
    logger.info("Starting affiliate schema fix")
    
    try:
        with app.app_context():
            # Get all table names from the database
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Existing tables: {tables}")
            
            # Only run if affiliate table exists
            if 'affiliate' in tables:
                logger.info("Checking 'affiliate' table schema...")
                
                # Check if the column already exists
                columns = [c['name'] for c in inspector.get_columns('affiliate')]
                logger.info(f"Existing columns: {columns}")
                
                if 'terms_agreed_at' not in columns:
                    logger.info("Adding terms_agreed_at column...")
                    db.session.execute(text("""
                    ALTER TABLE affiliate ADD COLUMN terms_agreed_at TIMESTAMP;
                    """))
                    db.session.commit()
                    logger.info("Added terms_agreed_at column successfully")
                else:
                    logger.info("terms_agreed_at column already exists, skipping")
                
                # Also check and fix paypal_email if needed
                if 'paypal_email' in columns:
                    try:
                        # Make column nullable if needed
                        db.session.execute(text("""
                        ALTER TABLE affiliate ALTER COLUMN paypal_email DROP NOT NULL;
                        """))
                        db.session.commit()
                        logger.info("Made paypal_email nullable")
                    except Exception as e:
                        logger.warning(f"Error or column already nullable: {e}")
                        db.session.rollback()
            else:
                logger.warning("Affiliate table doesn't exist, nothing to fix")
            
            logger.info("Schema fix completed")
            return True
            
    except Exception as e:
        logger.error(f"Error fixing affiliate schema: {e}")
        return False

if __name__ == "__main__":
    success = fix_affiliate_schema()
    if success:
        print("✅ Affiliate schema fix completed successfully!")
    else:
        print("❌ Affiliate schema fix failed! Check the logs for details.")