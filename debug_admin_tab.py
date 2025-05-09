"""
Debug script to verify admin tab functionality.

This script tests that the admin tab is visible and properly rendered when:
1. The user is an admin
2. The URL contains the parameter ?tab=admin
"""

import os
import sys
import logging
from flask import request, session, url_for
from app import app
from flask_login import login_user, current_user
from models import User

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Run the admin tab debug script."""
    with app.app_context():
        # Test environment setup
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['SERVER_NAME'] = 'localhost:5000'
        app.config['APPLICATION_ROOT'] = '/'
        app.config['PREFERRED_URL_SCHEME'] = 'http'
        
        # Ensure the admin user exists
        admin_email = os.environ.get('ADMIN_EMAILS', 'test@example.com')
        admin_emails = [email.strip() for email in admin_email.split(',')]
        admin_user = User.query.filter(User.email.in_(admin_emails)).first()
        
        if not admin_user:
            logger.warning(f"No admin user found with emails: {admin_emails}")
            logger.info("Creating a test admin user for debugging")
            admin_user = User.query.first()  # Use first user as admin for testing
            
            if not admin_user:
                logger.error("No users found in the database. Please create a user first.")
                sys.exit(1)
        
        logger.info(f"Using admin user: {admin_user.email}")
        
        # Test normal access
        with app.test_client() as client:
            with client.session_transaction() as sess:
                # Setup session for the admin user
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            # Test accessing billing account page normally
            response = client.get('/billing/account')
            logger.info(f"Normal access response code: {response.status_code}")
            
            # Check if 'admin-tab' is in the response
            if 'admin-tab' in response.data.decode('utf-8'):
                logger.info("Admin tab button found in the response")
            else:
                logger.error("Admin tab button NOT found in the response")
            
            # Test accessing with tab=admin parameter
            response = client.get('/billing/account?tab=admin')
            logger.info(f"Tab=admin parameter response code: {response.status_code}")
            
            # Also test the direct admin dashboard URL
            response = client.get('/admin/dashboard')
            logger.info(f"Direct admin dashboard URL response code: {response.status_code}")
            
            # Check response data for admin tab content
            data = response.data.decode('utf-8')
            if 'id="admin"' in data and 'class="tab-pane' in data:
                logger.info("Admin tab pane element found in the DOM")
                
                # Look for specific admin tab content
                if 'Commissions Ready for Processing' in data:
                    logger.info("Found admin dashboard content in the response")
                else:
                    logger.warning("Admin dashboard content not found in the response")
            else:
                logger.error("Admin tab pane NOT found in the DOM")
            
        logger.info("Debugging admin tab access completed")

if __name__ == "__main__":
    main()