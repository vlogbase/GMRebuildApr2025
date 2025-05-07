"""
Migrations script for the affiliate system update.

This script updates the affiliate-related database tables:
- Makes paypal_email nullable in Affiliate table
- Adds terms_agreed_at to Affiliate table
"""

import logging
from sqlalchemy.sql import text
from app import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run the affiliate system update migrations"""
    logger.info("Starting affiliate system update migrations")
    
    try:
        # Get all table names from the database
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f"Existing tables: {tables}")
        
        # Only run if affiliate table exists
        if 'affiliate' in tables:
            logger.info("Updating 'affiliate' table...")
            
            # Make paypal_email nullable
            try:
                # First, drop the unique constraint
                db.session.execute(text("""
                ALTER TABLE affiliate DROP CONSTRAINT IF EXISTS affiliate_paypal_email_key;
                """))
                
                # Make the column nullable
                db.session.execute(text("""
                ALTER TABLE affiliate ALTER COLUMN paypal_email DROP NOT NULL;
                """))
                
                # Add the unique constraint back for non-null values
                db.session.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS affiliate_paypal_email_unique_idx 
                ON affiliate (paypal_email) 
                WHERE paypal_email IS NOT NULL;
                """))
                
                logger.info("Made paypal_email nullable successfully")
            except Exception as e:
                logger.error(f"Error making paypal_email nullable: {e}")
                db.session.rollback()
                return False
            
            # Add terms_agreed_at column if it doesn't exist
            try:
                # Check if the column already exists
                columns = [c['name'] for c in inspector.get_columns('affiliate')]
                
                if 'terms_agreed_at' not in columns:
                    db.session.execute(text("""
                    ALTER TABLE affiliate ADD COLUMN terms_agreed_at TIMESTAMP;
                    """))
                    logger.info("Added terms_agreed_at column successfully")
                else:
                    logger.info("terms_agreed_at column already exists, skipping")
            except Exception as e:
                logger.error(f"Error adding terms_agreed_at column: {e}")
                db.session.rollback()
                return False
            
            # Update status for existing affiliates if needed
            try:
                db.session.execute(text("""
                UPDATE affiliate 
                SET status = 'active' 
                WHERE status = 'pending_terms' AND paypal_email IS NOT NULL;
                """))
                logger.info("Updated status for existing affiliates with PayPal email")
            except Exception as e:
                logger.error(f"Error updating status for existing affiliates: {e}")
                db.session.rollback()
                return False
            
        else:
            logger.warning("Affiliate table doesn't exist, skipping migrations")
        
        # Commit all changes
        db.session.commit()
        logger.info("All migrations completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error running affiliate system update migrations: {e}")
        db.session.rollback()
        return False