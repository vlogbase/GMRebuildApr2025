"""
Simple script to fix affiliate statuses in the database
1. Updates any "pending_terms" records to "active" 
2. Updates the database schema to default to "not_affiliate" for new records
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """Fix affiliate statuses in the database"""
    # Add the current directory to the path so we can import the app
    sys.path.append('.')
    
    # Import necessary modules
    from models import Affiliate, User, AffiliateStatus
    from database import db
    import main
    from main import app
    
    with app.app_context():
        try:
            # Step 1: Find and update any "pending_terms" records to "active"
            pending_affiliates = Affiliate.query.filter_by(status='pending_terms').all()
            logger.info(f"Found {len(pending_affiliates)} affiliates with 'pending_terms' status")
            
            for affiliate in pending_affiliates:
                affiliate.status = 'active'
                if not affiliate.terms_agreed_at:
                    affiliate.terms_agreed_at = datetime.now()
                logger.info(f"Updated affiliate ID {affiliate.id} to 'active' status")
            
            # Commit changes
            db.session.commit()
            logger.info("Successfully updated all pending affiliates to active status")
            
            # Step 2: Update the database default value for future records
            # Note: This is PostgreSQL-specific SQL syntax
            try:
                db.session.execute(text(
                    "ALTER TABLE affiliate ALTER COLUMN status SET DEFAULT 'not_affiliate';"
                ))
                db.session.commit()
                logger.info("Updated database schema: Changed default for status column to 'not_affiliate'")
            except Exception as e:
                logger.error(f"Error updating database schema: {e}")
                # This isn't critical, so we won't fail the entire script
            
            # Verify our changes
            remaining = Affiliate.query.filter_by(status='pending_terms').count()
            logger.info(f"Remaining affiliates with 'pending_terms' status: {remaining}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error fixing affiliate statuses: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    logger.info("Starting script to fix affiliate statuses...")
    success = run()
    if success:
        logger.info("Script completed successfully")
    else:
        logger.error("Script failed")
        sys.exit(1)