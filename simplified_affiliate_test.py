"""
Test workflow for the simplified affiliate system
"""
import os
import sys
import logging
import time
from datetime import datetime

from app import app, db
from models import User, Commission, CustomerReferral
from simplified_affiliate import simplified_affiliate_bp
from generate_referral_codes import generate_referral_codes

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_referral_codes():
    """Make sure all users have referral codes"""
    with app.app_context():
        # Check if any users are missing referral codes
        users_without_codes = User.query.filter(
            (User.referral_code == None) | (User.referral_code == '')
        ).count()
        
        if users_without_codes > 0:
            logger.info(f"Found {users_without_codes} users without referral codes, generating them now...")
            generate_referral_codes()
        else:
            logger.info("All users already have referral codes")

def check_commission_fields():
    """Check if Commission model is using user_id instead of affiliate_id"""
    with app.app_context():
        # Get a sample commission record if one exists
        sample = Commission.query.first()
        if sample:
            logger.info(f"Sample commission: {sample}")
            logger.info(f"Commission fields: {', '.join([c.name for c in Commission.__table__.columns])}")
            
            # Check if user_id exists on the model
            if hasattr(sample, 'user_id'):
                logger.info("Commission model has user_id field ✓")
            else:
                logger.error("Commission model is missing user_id field ✗")
                
            # Check if affiliate_id still exists on the model (should be removed)
            if hasattr(sample, 'affiliate_id'):
                logger.warning("Commission model still has affiliate_id field ✗")
            else:
                logger.info("Commission model doesn't have affiliate_id field (good) ✓")
        else:
            logger.info("No commission records found to check")

def check_user_referral_fields():
    """Check if User model has the necessary referral fields"""
    with app.app_context():
        # Get a sample user
        sample = User.query.first()
        if sample:
            logger.info(f"Sample user: {sample.username} (ID: {sample.id})")
            logger.info(f"User fields: {', '.join([c.name for c in User.__table__.columns])}")
            
            # Check for referral_code field
            if hasattr(sample, 'referral_code'):
                logger.info("User model has referral_code field ✓")
                logger.info(f"Sample referral code: {sample.referral_code}")
            else:
                logger.error("User model is missing referral_code field ✗")
                
            # Check for paypal_email field
            if hasattr(sample, 'paypal_email'):
                logger.info("User model has paypal_email field ✓")
                logger.info(f"Sample PayPal email: {sample.paypal_email}")
            else:
                logger.error("User model is missing paypal_email field ✗")
                
            # Check for referred_by_user_id field
            if hasattr(sample, 'referred_by_user_id'):
                logger.info("User model has referred_by_user_id field ✓")
            else:
                logger.error("User model is missing referred_by_user_id field ✗")
        else:
            logger.info("No user records found to check")

def run():
    """Run the Flask application with the simplified affiliate system"""
    logger.info("Starting simplified affiliate system test")
    
    # Register blueprint with the app
    if simplified_affiliate_bp not in app.blueprints.values():
        app.register_blueprint(simplified_affiliate_bp)
        logger.info("Registered simplified_affiliate_bp with the app")
    
    # Check if all users have referral codes
    ensure_referral_codes()
    
    # Check if the models have the correct fields
    check_commission_fields()
    check_user_referral_fields()
    
    # Run the app
    logger.info("Starting Flask app on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()