"""
Quick test for the simplified affiliate system core functionality
"""
import os
import sys
import logging
from flask import Flask
from sqlalchemy import inspect

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_user_model_fields():
    """Check if User model has the necessary affiliate fields"""
    try:
        from app import db
        from models import User
        
        # Get model inspector
        inspector = inspect(User)
        columns = [c.key for c in inspector.columns]
        
        # Check required fields
        has_referral_code = 'referral_code' in columns
        has_paypal_email = 'paypal_email' in columns
        has_referred_by = 'referred_by_user_id' in columns
        
        logger.info("User model affiliate fields:")
        logger.info(f"- referral_code: {'✓' if has_referral_code else '✗'}")
        logger.info(f"- paypal_email: {'✓' if has_paypal_email else '✗'}")
        logger.info(f"- referred_by_user_id: {'✓' if has_referred_by else '✗'}")
        
        return has_referral_code and has_paypal_email and has_referred_by
    except Exception as e:
        logger.error(f"Error checking User model fields: {e}")
        return False

def check_affiliate_routes():
    """Check if simplified affiliate routes are registered"""
    try:
        from app import app
        
        # Check if blueprint is registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        # Check for key routes
        has_dashboard = '/affiliate/dashboard' in routes
        has_update_email = '/affiliate/update_paypal_email' in routes
        has_track_referral = '/affiliate/referral/<code>' in routes
        
        logger.info("Simplified affiliate routes:")
        logger.info(f"- /affiliate/dashboard: {'✓' if has_dashboard else '✗'}")
        logger.info(f"- /affiliate/update_paypal_email: {'✓' if has_update_email else '✗'}")
        logger.info(f"- /affiliate/referral/<code>: {'✓' if has_track_referral else '✗'}")
        
        return has_dashboard and has_update_email and has_track_referral
    except Exception as e:
        logger.error(f"Error checking affiliate routes: {e}")
        return False

def check_template_compatibility():
    """Check if templates reference User model directly"""
    try:
        import os
        
        # Check tell_friend_tab.html for direct User model references
        template_path = 'templates/affiliate/tell_friend_tab.html'
        if not os.path.exists(template_path):
            logger.error(f"Template file not found: {template_path}")
            return False
            
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Check for references to current_user attributes
        has_referral_code = 'current_user.referral_code' in content
        has_paypal_email = 'current_user.paypal_email' in content
        
        logger.info("Template compatibility:")
        logger.info(f"- current_user.referral_code: {'✓' if has_referral_code else '✗'}")
        logger.info(f"- current_user.paypal_email: {'✓' if has_paypal_email else '✗'}")
        
        return has_referral_code and has_paypal_email
    except Exception as e:
        logger.error(f"Error checking template compatibility: {e}")
        return False

def main():
    """Run all tests"""
    try:
        logger.info("==== SIMPLIFIED AFFILIATE SYSTEM TESTS ====")
        
        # Run tests
        user_model_test = check_user_model_fields()
        routes_test = check_affiliate_routes()
        template_test = check_template_compatibility()
        
        # Print summary
        logger.info("\n==== TEST RESULTS ====")
        logger.info(f"User model fields: {'PASS' if user_model_test else 'FAIL'}")
        logger.info(f"Affiliate routes: {'PASS' if routes_test else 'FAIL'}")
        logger.info(f"Template compatibility: {'PASS' if template_test else 'FAIL'}")
        
        overall = user_model_test and routes_test and template_test
        logger.info(f"\nOverall result: {'PASS' if overall else 'FAIL'}")
        
        return 0 if overall else 1
    except Exception as e:
        logger.error(f"Error in test execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())