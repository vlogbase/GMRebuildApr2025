#!/usr/bin/env python3

"""
A simple script to manually test the affiliate referral creation.
This script directly calls our helper function to test creating a referral.
"""

from app import app, db
from affiliate import create_customer_referral
from models import CustomerReferral

# Test parameters
TEST_USER_ID = 1         # Andy user
AFFILIATE_ID = 4         # Your affiliate ID
AFFILIATE_CODE = "M11174LA"  # Your affiliate code

def check_referral_exists():
    """Check if a referral already exists for the test user"""
    with app.app_context():
        referral = CustomerReferral.query.filter_by(customer_user_id=TEST_USER_ID).first()
        if referral:
            print(f"Referral exists: User {TEST_USER_ID} is already referred by affiliate {referral.affiliate_id}")
            print(f"Referral details: {referral.id=}, {referral.signup_date=}")
            return True
        else:
            print(f"No referral exists for user {TEST_USER_ID}")
            return False

def clear_existing_referral():
    """Clear any existing referral for the test user"""
    with app.app_context():
        referral = CustomerReferral.query.filter_by(customer_user_id=TEST_USER_ID).first()
        if referral:
            print(f"Deleting existing referral: User {TEST_USER_ID} referred by affiliate {referral.affiliate_id}")
            db.session.delete(referral)
            db.session.commit()
            print("Referral deleted")
        else:
            print(f"No referral exists for user {TEST_USER_ID}")

def test_create_referral():
    """Test creating a referral for the test user"""
    with app.app_context():
        # Call the function directly
        print(f"Creating referral: User {TEST_USER_ID} referred by affiliate {AFFILIATE_ID}")
        result = create_customer_referral(TEST_USER_ID, AFFILIATE_ID, AFFILIATE_CODE)
        
        # Check if it was successful
        if result:
            print("Referral creation reported success")
        else:
            print("Referral creation reported failure")
        
        # Verify in database
        referral = CustomerReferral.query.filter_by(customer_user_id=TEST_USER_ID).first()
        if referral:
            print(f"✓ SUCCESS: Verified referral in database")
            print(f"  Referral ID: {referral.id}")
            print(f"  Customer ID: {referral.customer_user_id}")
            print(f"  Affiliate ID: {referral.affiliate_id}")
            print(f"  Signup Date: {referral.signup_date}")
            return True
        else:
            print("✗ FAILURE: No referral found in database after creation attempt")
            return False

if __name__ == "__main__":
    print("=== Testing Affiliate Referral Creation ===")
    
    # Check initial state
    print("\n1. Checking initial state:")
    has_referral = check_referral_exists()
    
    # Clear any existing referral
    if has_referral:
        print("\n2. Clearing existing referral:")
        clear_existing_referral()
    
    # Test creating a new referral
    print("\n3. Testing referral creation:")
    success = test_create_referral()
    
    # Final result
    print("\n=== Test Result ===")
    if success:
        print("✓ TEST PASSED: Referral was successfully created!")
    else:
        print("✗ TEST FAILED: Could not create referral")