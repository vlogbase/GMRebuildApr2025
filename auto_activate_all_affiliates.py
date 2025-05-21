"""
Script to automatically set all users as active affiliates
1. Creates affiliate records for any users without one
2. Updates any existing affiliate records to active status
"""

import sys
import logging
import string
import random
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """Set all users as active affiliates"""
    # Add the current directory to the path so we can import the app
    sys.path.append('.')
    
    # Import necessary modules
    from models import User, Affiliate, AffiliateStatus
    from database import db
    import main  # This automatically imports the Flask app
    from main import app  # Get the app from main module
    
    with app.app_context():
        try:
            # Step 1: Get all users
            users = User.query.all()
            logger.info(f"Found {len(users)} users in the database")
            
            # Step 2: Loop through users and ensure they all have active affiliate records
            created_count = 0
            updated_count = 0
            
            for user in users:
                # Check if user already has an affiliate record
                affiliate = Affiliate.query.filter_by(email=user.email).first()
                
                if affiliate:
                    # Update existing affiliate record to active
                    if affiliate.status != AffiliateStatus.ACTIVE.value:
                        affiliate.status = AffiliateStatus.ACTIVE.value
                        if not affiliate.terms_agreed_at:
                            affiliate.terms_agreed_at = datetime.now()
                        logger.info(f"Updated affiliate ID {affiliate.id} ({user.email}) to active status")
                        updated_count += 1
                else:
                    # Create new active affiliate record for the user
                    # Generate a unique referral code
                    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    referral_code = f"{user.username.lower()}-{random_str}"
                    
                    # Create a new affiliate record
                    new_affiliate = Affiliate(
                        name=user.username,
                        email=user.email,
                        referral_code=referral_code,
                        status=AffiliateStatus.ACTIVE.value,
                        terms_agreed_at=datetime.now()
                    )
                    
                    db.session.add(new_affiliate)
                    logger.info(f"Created new active affiliate record for user {user.id} ({user.email})")
                    created_count += 1
            
            # Commit all changes
            db.session.commit()
            logger.info(f"Successfully processed all users: {created_count} created, {updated_count} updated")
            
            # Step 3: Verify our changes
            active_count = Affiliate.query.filter_by(status=AffiliateStatus.ACTIVE.value).count()
            total_count = Affiliate.query.count()
            logger.info(f"Final affiliate counts: {active_count} active out of {total_count} total")
            
            return True
        
        except Exception as e:
            logger.error(f"Error activating affiliates: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    logger.info("Starting script to activate all affiliates...")
    success = run()
    if success:
        logger.info("Script completed successfully")
    else:
        logger.error("Script failed")
        sys.exit(1)