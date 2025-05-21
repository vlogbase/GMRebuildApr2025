"""
Test script to validate our affiliate system changes
"""
import os
import sys
import logging
from datetime import datetime
import uuid

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='affiliate_changes_test.log'
)
logger = logging.getLogger(__name__)

# Import the database models inside an app context
from app import app
from database import db, User, Affiliate

def test_auto_affiliate_creation():
    """Test automatic creation of active affiliates"""
    with app.app_context():
        # Create a test user if not exists
        test_username = f"test_user_{uuid.uuid4().hex[:8]}"
        test_email = f"{test_username}@example.com"
        
        user = User.query.filter_by(username=test_username).first()
        if not user:
            logger.info(f"Creating test user: {test_username}")
            user = User(
                username=test_username,
                email=test_email,
                user_is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        # Get or create affiliate for this user
        affiliate = Affiliate.query.filter_by(user_id=user.id).first()
        if affiliate:
            logger.info(f"Existing affiliate found for user {user.id}: status={affiliate.status}")
            
            # Test activation of existing affiliate
            if affiliate.status != 'active':
                logger.info(f"Activating affiliate: {affiliate.id}")
                affiliate.status = 'active'
                affiliate.terms_agreed_at = datetime.now()
                db.session.commit()
                logger.info(f"Affiliate activated: {affiliate.id}, status={affiliate.status}")
        else:
            # Test auto-creation of active affiliate
            logger.info(f"Creating new active affiliate for user {user.id}")
            referral_code = str(uuid.uuid4())[:8]
            
            affiliate = Affiliate(
                user_id=user.id,
                name=user.username,
                email=user.email,
                referral_code=referral_code,
                status='active',
                terms_agreed_at=datetime.now()
            )
            db.session.add(affiliate)
            db.session.commit()
            logger.info(f"Created affiliate: {affiliate.id}, status={affiliate.status}")
        
        # Validate that the affiliate is active
        affiliate = Affiliate.query.filter_by(user_id=user.id).first()
        assert affiliate is not None, "Affiliate not found"
        assert affiliate.status == 'active', f"Affiliate not active: {affiliate.status}"
        assert affiliate.terms_agreed_at is not None, "Terms agreed timestamp missing"
        
        logger.info(f"Validation successful: affiliate is active")
        return True

if __name__ == '__main__':
    try:
        print("Testing affiliate system changes...")
        result = test_auto_affiliate_creation()
        print(f"Test {'PASSED' if result else 'FAILED'}")
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        print(f"Test FAILED: {str(e)}")
        sys.exit(1)