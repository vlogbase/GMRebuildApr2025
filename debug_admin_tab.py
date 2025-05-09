"""
Debug script to test admin tab functionality
"""

import os
import sys
from app import app, db
from auth_utils import is_admin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_admin_visibility():
    """Test if admin functionality is working properly"""
    # Set admin emails
    os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com,test@example.com'
    logger.info(f"ADMIN_EMAILS set to: {os.environ.get('ADMIN_EMAILS')}")
    
    # Create a test context
    with app.test_request_context():
        # Import here to avoid circular imports
        from flask_login import login_user
        from models import User
        
        # Create or get test admin user
        admin_user = User.query.filter_by(email='andy@sentigral.com').first()
        if not admin_user:
            logger.info("Admin user not found, this is expected in test environment")
            # Create a minimal mock user for testing
            class MockUser:
                id = 999
                email = 'andy@sentigral.com'
                is_authenticated = True
                is_active = True
                def get_id(self):
                    return str(self.id)
            admin_user = MockUser()
        
        # Login the admin user
        login_user(admin_user)
        logger.info(f"Logged in as: {admin_user.email}")
        
        # Test if admin check works
        admin_status = is_admin()
        logger.info(f"Admin check result: {admin_status}")
        
        return admin_status

if __name__ == "__main__":
    # Run with app context
    with app.app_context():
        try:
            is_admin_result = test_admin_visibility()
            if is_admin_result:
                logger.info("SUCCESS: Admin check is working correctly!")
                sys.exit(0)
            else:
                logger.error("FAIL: Admin check returned False when it should be True")
                sys.exit(1)
        except Exception as e:
            logger.error(f"ERROR: Admin check failed with exception: {e}")
            sys.exit(1)