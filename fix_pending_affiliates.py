"""
Script to fix all affiliate records stuck in the 'pending_terms' status.
We'll move them all to 'active' status as discussed with the client.

This is a one-time script to clean up the database.
"""

import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def fix_pending_affiliates():
    """
    Find and fix all affiliate records with status='pending_terms'
    by changing their status to 'active'.
    """
    # Import models inside the function to ensure the app context is set up
    from app import app, db
    from models import Affiliate

    with app.app_context():
        try:
            # Find all pending_terms affiliates
            pending_affiliates = Affiliate.query.filter_by(status='pending_terms').all()
            
            if not pending_affiliates:
                logger.info("No affiliates with 'pending_terms' status found. Database is clean.")
                return True
                
            # Log the found affiliates
            logger.info(f"Found {len(pending_affiliates)} affiliates with 'pending_terms' status.")
            for affiliate in pending_affiliates:
                logger.info(f"Affiliate ID: {affiliate.id}, Email: {affiliate.email}")
                
            # Update all the pending_terms affiliates to active
            for affiliate in pending_affiliates:
                affiliate.status = 'active'
                # Set terms_agreed_at if it's not already set
                if not affiliate.terms_agreed_at:
                    affiliate.terms_agreed_at = datetime.now()
                logger.info(f"Updated affiliate ID {affiliate.id} to 'active' status")
                
            # Commit the changes to the database
            db.session.commit()
            logger.info(f"Successfully updated {len(pending_affiliates)} affiliates to 'active' status.")
            
            # Verify the changes
            remaining_pending = Affiliate.query.filter_by(status='pending_terms').count()
            if remaining_pending > 0:
                logger.warning(f"Still found {remaining_pending} affiliates with 'pending_terms' status after update!")
            else:
                logger.info("Verified: No affiliates with 'pending_terms' status remain in the database.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating affiliate statuses: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    logger.info("Starting affiliate status fix script...")
    result = fix_pending_affiliates()
    if result:
        logger.info("Script completed successfully.")
    else:
        logger.error("Script encountered errors. Check the logs for details.")