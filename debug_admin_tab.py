"""
Debug script to check admin tab permissions and rendering.
This can be used to test the affiliate admin functionality without making actual changes.
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Run tests to check admin tab functionality.
    """
    try:
        # Set environment variables for testing
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com,test@example.com'
        os.environ['FLASK_ENV'] = 'development'
        
        # Import app components
        from app import app, db
        from models import User, Affiliate, Commission, CommissionStatus
        
        with app.app_context():
            # Check admin access
            from affiliate import is_admin
            
            # Import and get a real admin user from database
            admin_email = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')[0]
            test_admin = User.query.filter_by(email=admin_email).first()
            
            # Log admin user details
            if test_admin:
                logger.info(f"Found admin user: {test_admin.email}")
            else:
                logger.warning(f"No admin user found with email: {admin_email}")
            
            # Simulate admin check
            result = is_admin()
            logger.info(f"Admin check result: {result}")
            
            # Check commission counts
            held_commissions = Commission.query.filter_by(status=CommissionStatus.HELD.value).count()
            approved_commissions = Commission.query.filter_by(status=CommissionStatus.APPROVED.value).count()
            paid_commissions = Commission.query.filter_by(status=CommissionStatus.PAID.value).count()
            
            logger.info(f"Commission counts - Held: {held_commissions}, Approved: {approved_commissions}, Paid: {paid_commissions}")
            
            # Check active affiliates
            active_affiliates = Affiliate.query.filter_by(status='active').count()
            logger.info(f"Active affiliates: {active_affiliates}")
            
            # Check available commissions (held and past their availability date)
            now = datetime.utcnow()
            available_commissions = Commission.query.filter(
                Commission.status == CommissionStatus.HELD.value,
                Commission.commission_available_date <= now
            ).count()
            
            logger.info(f"Available commissions: {available_commissions}")
            
            # Check for commissions that will be available soon
            future_date = now + timedelta(days=7)
            soon_available = Commission.query.filter(
                Commission.status == CommissionStatus.HELD.value,
                Commission.commission_available_date > now,
                Commission.commission_available_date <= future_date
            ).count()
            
            logger.info(f"Commissions available within 7 days: {soon_available}")
            
            # Success message
            logger.info("Admin tab debug test completed successfully")
    
    except Exception as e:
        logger.error(f"Error testing admin functionality: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()