"""
Test script to verify the affiliate referral functionality.

This script simulates a logged-in user visiting a URL with a referral code,
to verify that a CustomerReferral record is properly created.
"""

import os
import sys
from app import app, db
from flask_login import login_user
from models import User, Affiliate, CustomerReferral

# Configuration
TEST_USER_ID = 1  # Andy (andysurtees924@gmail.com)
AFFILIATE_CODE = "M11174LA"  # Andy's affiliate code
AFFILIATE_ID = 4  # Andy's affiliate ID

def clear_test_referral():
    """Clear any existing test CustomerReferral for our test user"""
    with app.app_context():
        # Delete any existing referral for this test user
        existing = CustomerReferral.query.filter_by(customer_user_id=TEST_USER_ID).first()
        if existing:
            print(f"Deleting existing CustomerReferral (ID: {existing.id}) for user {TEST_USER_ID}")
            db.session.delete(existing)
            db.session.commit()
        else:
            print(f"No existing CustomerReferral found for user {TEST_USER_ID}")

def test_referral_creation():
    """Test the creation of a CustomerReferral when a logged-in user visits a referral link"""
    with app.test_client() as client:
        with app.app_context():
            # 1. First, log in as the test user
            test_user = User.query.get(TEST_USER_ID)
            if not test_user:
                print(f"Error: Test user with ID {TEST_USER_ID} not found")
                return False
                
            print(f"Testing with user: {test_user.username} (ID: {test_user.id}, Email: {test_user.email})")
            
            # 2. Create a session for this user
            with client.session_transaction() as session:
                # Mark the user as logged in in the session
                session['_user_id'] = str(test_user.id)
                
            # 3. Visit a URL with the referral code
            print(f"Simulating visit to URL with referral code: {AFFILIATE_CODE}")
            response = client.get(f"/?ref={AFFILIATE_CODE}")
            
            # Check response status
            if response.status_code != 200:
                print(f"Error: Unexpected response status: {response.status_code}")
                return False
                
            # 4. Check if a CustomerReferral was created
            referral = CustomerReferral.query.filter_by(customer_user_id=TEST_USER_ID).first()
            
            if referral:
                print("✓ SUCCESS: CustomerReferral was created!")
                print(f"  Referral ID: {referral.id}")
                print(f"  Customer User ID: {referral.customer_user_id}")
                print(f"  Affiliate ID: {referral.affiliate_id}")
                print(f"  Signup Date: {referral.signup_date}")
                
                # Verify it's linked to the correct affiliate
                if referral.affiliate_id == AFFILIATE_ID:
                    print(f"✓ VERIFIED: Referral is correctly linked to affiliate ID {AFFILIATE_ID}")
                    return True
                else:
                    print(f"✗ ERROR: Referral is linked to wrong affiliate ID: {referral.affiliate_id} (expected {AFFILIATE_ID})")
                    return False
            else:
                print("✗ ERROR: No CustomerReferral was created!")
                return False

if __name__ == "__main__":
    print("=== Testing Affiliate Referral Functionality ===")
    
    # First, clean up any existing test data
    clear_test_referral()
    
    # Run the test
    result = test_referral_creation()
    
    print("\n=== Test Result ===")
    if result:
        print("✓ TEST PASSED: The affiliate referral functionality is working correctly!")
        sys.exit(0)
    else:
        print("✗ TEST FAILED: The affiliate referral functionality is not working correctly!")
        sys.exit(1)