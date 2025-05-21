"""
Migration to improve the affiliate status system:
1. Add a new 'not_affiliate' status
2. Change any existing 'pending_terms' records to 'active' if they've agreed to terms
3. Create records for all users who don't yet have an affiliate record
"""

import logging
import sys
from datetime import datetime
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to improve the affiliate status system.
    """
    # Import models inside the function to ensure the app context is set up
    from app import app, db
    from models import User, Affiliate, AffiliateStatus
    
    with app.app_context():
        try:
            # Step 1: Add 'not_affiliate' to the AffiliateStatus enum if not already there
            # NOTE: This is for documentation - the actual enum update must be done in models.py
            logger.info("Checking for 'not_affiliate' status in AffiliateStatus enum...")
            has_not_affiliate = False
            try:
                has_not_affiliate = AffiliateStatus.NOT_AFFILIATE.value == "not_affiliate"
                logger.info("'not_affiliate' status exists in enum: True")
            except:
                logger.warning("'not_affiliate' status does not exist in AffiliateStatus enum.")
                logger.warning("You should update models.py to add NOT_AFFILIATE = 'not_affiliate' to the AffiliateStatus enum.")
            
            # Step 2: Fix any existing 'pending_terms' records
            pending_affiliates = Affiliate.query.filter_by(status='pending_terms').all()
            logger.info(f"Found {len(pending_affiliates)} affiliates with 'pending_terms' status.")
            
            for affiliate in pending_affiliates:
                # If they have agreed to terms or have a terms_agreed_at date, make them active
                if hasattr(affiliate, 'terms_agreed') and affiliate.terms_agreed or affiliate.terms_agreed_at:
                    affiliate.status = 'active'
                    logger.info(f"Updated affiliate ID {affiliate.id} to 'active' status")
                else:
                    # Otherwise, if not_affiliate status exists, use that, else keep as pending_terms
                    if has_not_affiliate:
                        affiliate.status = 'not_affiliate'
                        logger.info(f"Updated affiliate ID {affiliate.id} to 'not_affiliate' status")
                    else:
                        # Default to active if we can't use not_affiliate
                        affiliate.status = 'active'
                        logger.info(f"Default: Updated affiliate ID {affiliate.id} to 'active' status")
            
            # Commit the changes to fix existing records
            db.session.commit()
            
            # Step 3: Create records for all users who don't have an affiliate record
            # Only do this if we have the not_affiliate status
            if has_not_affiliate:
                users_without_affiliate = User.query.filter(
                    ~User.id.in_(db.session.query(Affiliate.user_id))
                ).all()
                
                logger.info(f"Found {len(users_without_affiliate)} users without affiliate records.")
                
                # Create affiliate records for these users with not_affiliate status
                for user in users_without_affiliate:
                    new_affiliate = Affiliate(
                        user_id=user.id,
                        name=user.username,
                        email=user.email,
                        status='not_affiliate'
                    )
                    db.session.add(new_affiliate)
                    logger.info(f"Created 'not_affiliate' record for user ID {user.id}")
                
                # Commit the new records
                db.session.commit()
            
            # Step 4: Update the default value in the database schema (for future records)
            # NOTE: This is PostgreSQL specific syntax
            if has_not_affiliate:
                db.session.execute(text(
                    "ALTER TABLE affiliate ALTER COLUMN status SET DEFAULT 'not_affiliate';"
                ))
                db.session.commit()
                logger.info("Updated database schema: Changed default for status column to 'not_affiliate'")
            
            return True
        
        except Exception as e:
            logger.error(f"Error in affiliate status migration: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    logger.info("Starting affiliate status migration...")
    result = run_migration()
    if result:
        logger.info("Migration completed successfully.")
    else:
        logger.error("Migration encountered errors. Check the logs for details.")