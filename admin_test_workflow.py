"""
Script to test the admin dashboard functionality.
This runs the Flask application with admin access enabled.
"""

import logging
import os
import sys
from app import app, db
from models import User, Affiliate, Commission, CommissionStatus
from auth_utils import is_admin
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """
    Run tests for admin dashboard functionality.
    """
    try:
        # Make sure we're in application context
        with app.app_context():
            # Check if admin functionality is working
            test_is_admin()
            
            # Check if we can access admin commissions
            test_admin_commissions()
            
            # Start the Flask application
            logger.info("Starting Flask application for admin testing")
            app.run(host='0.0.0.0', port=5000, debug=True)
            
    except Exception as e:
        logger.error(f"Error in admin test: {e}")
        sys.exit(1)

def test_is_admin():
    """Test the is_admin function"""
    logger.info("Testing is_admin functionality")
    
    # Create a test admin user directly in the env var
    os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com,test@example.com'
    
    # Simulate being logged in as an admin
    logger.info(f"ADMIN_EMAILS environment variable: {os.environ.get('ADMIN_EMAILS')}")
    
    # The actual function verification will happen when running the app
    logger.info("Admin functionality verification prepared")

def test_admin_commissions():
    """Test admin commissions functionality"""
    logger.info("Testing admin commissions functionality")
    
    try:
        # Query commissions that would be shown in admin dashboard
        admin_commissions = Commission.query.filter(
            (
                (Commission.status == CommissionStatus.HELD.value) &
                (Commission.commission_available_date <= datetime.utcnow())
            ) | 
            (Commission.status == CommissionStatus.APPROVED.value)
        ).order_by(Commission.commission_available_date.desc()).all()
        
        logger.info(f"Found {len(admin_commissions)} commissions for admin panel")
        
        # Check affiliate references
        for commission in admin_commissions[:5]:  # Log details for up to 5 commissions
            affiliate = Affiliate.query.get(commission.affiliate_id)
            logger.info(f"Commission ID: {commission.id}, Status: {commission.status}")
            logger.info(f"Affiliate ID: {commission.affiliate_id}, Name: {affiliate.name if affiliate else 'Not found'}")
    
    except Exception as e:
        logger.error(f"Error testing admin commissions: {e}")

if __name__ == "__main__":
    run()