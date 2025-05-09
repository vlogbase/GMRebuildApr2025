"""
Test script for GloriaMundo Admin Dashboard

This script provides a quick way to verify the admin interface is working correctly
by accessing various admin endpoints and checking functionality.
"""

import os
import sys
import logging

from flask import redirect, url_for, flash, session
from flask_login import login_user, logout_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin_test.log')
    ]
)

logger = logging.getLogger(__name__)

def test_admin_access():
    """Test admin access with both authorized and unauthorized users"""
    from app import app, db
    from models import User
    from gm_admin import is_admin
    
    # Set admin email for testing
    os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
    
    with app.app_context():
        # Test case 1: Admin user
        admin_user = User.query.filter_by(email='andy@sentigral.com').first()
        if not admin_user:
            logger.warning("Admin user not found. Creating test admin user...")
            admin_user = User(username='Andy', email='andy@sentigral.com')
            db.session.add(admin_user)
            db.session.commit()
            logger.info(f"Created admin user: {admin_user.email}")
        
        # Test case 2: Non-admin user
        non_admin_user = User.query.filter_by(email='test@example.com').first()
        if not non_admin_user:
            logger.warning("Test user not found. Creating test non-admin user...")
            non_admin_user = User(username='Test', email='test@example.com')
            db.session.add(non_admin_user)
            db.session.commit()
            logger.info(f"Created non-admin user: {non_admin_user.email}")
        
        # Test admin check with admin user
        with app.test_request_context():
            # Simulate login for admin user
            login_user(admin_user)
            admin_result = is_admin()
            logger.info(f"Admin check for {admin_user.email}: {admin_result}")
            logout_user()
            
            # Simulate login for non-admin user
            login_user(non_admin_user)
            non_admin_result = is_admin()
            logger.info(f"Admin check for {non_admin_user.email}: {non_admin_result}")
            logout_user()
            
            # Verify results
            if admin_result and not non_admin_result:
                logger.info("✅ Admin access check passed!")
            else:
                logger.error("❌ Admin access check failed!")

def test_admin_routes():
    """Test admin routes for proper redirection and access control"""
    from app import app
    from models import User
    
    with app.app_context():
        admin_user = User.query.filter_by(email='andy@sentigral.com').first()
        non_admin_user = User.query.filter_by(email='test@example.com').first()
        
        if not admin_user or not non_admin_user:
            logger.error("Test users not found. Run test_admin_access first.")
            return
        
        with app.test_client() as client:
            # Test 1: Unauthenticated access redirects to login
            response = client.get('/gm-admin/', follow_redirects=False)
            if response.status_code == 302 and 'login' in response.location:
                logger.info("✅ Unauthenticated access correctly redirects to login")
            else:
                logger.error(f"❌ Unauthenticated access unexpected response: {response.status_code}, {response.location}")
            
            # Test 2: Non-admin access restricted
            with client.session_transaction() as sess:
                sess['_user_id'] = str(non_admin_user.id)
                
            response = client.get('/gm-admin/', follow_redirects=False)
            if response.status_code == 302 and 'login' in response.location:
                logger.info("✅ Non-admin access correctly restricted")
            else:
                logger.error(f"❌ Non-admin access unexpected response: {response.status_code}")
            
            # Test 3: Admin access allowed
            with client.session_transaction() as sess:
                sess.clear()
                sess['_user_id'] = str(admin_user.id)
                
            response = client.get('/gm-admin/', follow_redirects=False)
            if response.status_code == 200:
                logger.info("✅ Admin access correctly allowed")
            else:
                logger.error(f"❌ Admin access unexpected response: {response.status_code}")

def test_health_check():
    """Test health check endpoint for deployment compatibility"""
    from app import app
    
    with app.test_client() as client:
        # Test with health check user agent
        response = client.get('/', headers={'User-Agent': 'health-check-agent'})
        if response.status_code == 200 and 'status' in response.json and response.json['status'] == 'ok':
            logger.info("✅ Health check in user agent correctly handled")
        else:
            logger.error(f"❌ Health check in user agent unexpected response: {response.status_code}")
        
        # Test with health check query parameter
        response = client.get('/?health=check')
        if response.status_code == 200 and 'status' in response.json and response.json['status'] == 'ok':
            logger.info("✅ Health check in query parameter correctly handled")
        else:
            logger.error(f"❌ Health check in query parameter unexpected response: {response.status_code}")

def main():
    """Run all tests"""
    logger.info("=== Testing GloriaMundo Admin Dashboard ===")
    
    test_admin_access()
    test_admin_routes()
    test_health_check()
    
    logger.info("=== Tests completed ===")

if __name__ == "__main__":
    main()