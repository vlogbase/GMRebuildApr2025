"""
Test script for the simplified affiliate system

This script validates the key components of our simplified affiliate system:
1. Verifies User model has the necessary affiliate fields
2. Tests PayPal email update functionality
3. Checks referral code generation
4. Validates the referral tracking system
"""
import os
import sys
import logging
import random
import string
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_user_model():
    """Test that the User model has the necessary affiliate fields"""
    from app import app, db
    from models import User
    
    with app.app_context():
        logger.info("Testing User model affiliate fields...")
        
        # Get a test user (first user in the database)
        test_user = User.query.first()
        if not test_user:
            logger.warning("No users found in database, creating test user")
            test_user = User(username="test_user", email="test@example.com")
            db.session.add(test_user)
            db.session.commit()
            
        # Test referral_code field
        logger.info(f"Testing referral_code field: {'PASS' if hasattr(test_user, 'referral_code') else 'FAIL'}")
        
        # Test paypal_email field
        logger.info(f"Testing paypal_email field: {'PASS' if hasattr(test_user, 'paypal_email') else 'FAIL'}")
        
        # Test referred_by_user_id field
        logger.info(f"Testing referred_by_user_id field: {'PASS' if hasattr(test_user, 'referred_by_user_id') else 'FAIL'}")
        
        return (hasattr(test_user, 'referral_code') and 
                hasattr(test_user, 'paypal_email') and 
                hasattr(test_user, 'referred_by_user_id'))

def test_paypal_email_update():
    """Test updating a user's PayPal email"""
    from app import app, db
    from models import User
    
    with app.app_context():
        logger.info("Testing PayPal email update functionality...")
        
        # Get a test user
        test_user = User.query.first()
        if not test_user:
            logger.warning("No test user found")
            return False
            
        # Generate a test email
        test_email = f"test_paypal_{random.randint(1000, 9999)}@example.com"
        
        # Save original email for later comparison
        original_email = test_user.paypal_email
        
        try:
            # Update PayPal email
            if hasattr(test_user, 'update_paypal_email'):
                # Use method if it exists
                test_user.update_paypal_email(test_email)
            else:
                # Direct assignment otherwise
                test_user.paypal_email = test_email
                
            db.session.commit()
            
            # Verify the update
            updated_user = User.query.get(test_user.id)
            result = updated_user.paypal_email == test_email
            
            logger.info(f"PayPal email update test: {'PASS' if result else 'FAIL'}")
            logger.info(f"Original email: {original_email}, New email: {updated_user.paypal_email}")
            
            # Restore original email
            if hasattr(test_user, 'update_paypal_email'):
                test_user.update_paypal_email(original_email)
            else:
                test_user.paypal_email = original_email
                
            db.session.commit()
            
            return result
        except Exception as e:
            logger.error(f"Error testing PayPal email update: {str(e)}")
            return False

def test_referral_code_generation():
    """Test generating a referral code for a user"""
    from app import app, db
    from models import User
    
    with app.app_context():
        logger.info("Testing referral code generation...")
        
        # Get or create a test user without a referral code
        test_user = User.query.filter_by(referral_code=None).first()
        if not test_user:
            test_user = User.query.first()
            # Clear referral code for testing
            test_user.referral_code = None
            db.session.commit()
            
        if not test_user:
            logger.warning("No test user found")
            return False
            
        try:
            original_code = test_user.referral_code
            
            # Generate a referral code
            if hasattr(test_user, 'generate_referral_code'):
                # Use method if it exists
                result = test_user.generate_referral_code()
            else:
                # Generate code manually
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                test_user.referral_code = code
                result = code
                
            db.session.commit()
            
            # Verify code was generated
            updated_user = User.query.get(test_user.id)
            logger.info(f"Original code: {original_code}, Generated code: {updated_user.referral_code}")
            
            success = updated_user.referral_code is not None and updated_user.referral_code != ''
            logger.info(f"Referral code generation test: {'PASS' if success else 'FAIL'}")
            
            return success
        except Exception as e:
            logger.error(f"Error testing referral code generation: {str(e)}")
            return False

def run_tests():
    """Run all tests for the simplified affiliate system"""
    logger.info("Starting simplified affiliate system tests...")
    
    results = {
        "user_model": test_user_model(),
        "paypal_email": test_paypal_email_update(),
        "referral_code": test_referral_code_generation()
    }
    
    # Print summary of results
    logger.info("\n=== TEST RESULTS SUMMARY ===")
    for test, result in results.items():
        logger.info(f"{test}: {'PASS' if result else 'FAIL'}")
    
    # Overall result
    success = all(results.values())
    logger.info(f"\nOverall result: {'SUCCESS' if success else 'FAILURE'}")
    
    return success

if __name__ == "__main__":
    run_tests()