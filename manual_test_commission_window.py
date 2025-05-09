#!/usr/bin/env python3

"""
Manual test script for the affiliate commission window functionality.
This script creates a test transaction for an existing user and tries
to process a commission through the updated process_affiliate_commission function.
"""

import sys
import os
from datetime import datetime, timedelta
from app import app, db
from models import User, Transaction, Commission, PaymentStatus, CustomerReferral
from billing import process_affiliate_commission

# User ID for the test (User 1 - andysurtees924@gmail.com)
# This user already has a CustomerReferral record (ID 2) linking to Affiliate 4
TEST_USER_ID = 1

def set_commission_date():
    """Set the first_commissioned_purchase_at date for testing"""
    with app.app_context():
        # Get the customer referral record
        referral = CustomerReferral.query.filter_by(customer_user_id=TEST_USER_ID).first()
        
        if referral:
            # Set the date to one year ago minus one day (so a transaction today would be eligible)
            one_year_ago_minus_one_day = datetime.utcnow() - timedelta(days=364)
            referral.first_commissioned_purchase_at = one_year_ago_minus_one_day
            db.session.add(referral)
            db.session.commit()
            
            print(f"Set first_commissioned_purchase_at to {referral.first_commissioned_purchase_at}")
            print(f"Window ends at {referral.first_commissioned_purchase_at + timedelta(days=365)}")
            
            return True
        else:
            print(f"No CustomerReferral found for user {TEST_USER_ID}")
            return False

def create_test_transaction():
    """Create a test transaction for the user"""
    with app.app_context():
        # Create a unique payment intent ID
        payment_intent_id = f"test_window_pi_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create the transaction
        test_transaction = Transaction()
        test_transaction.user_id = TEST_USER_ID
        test_transaction.amount_usd = 50.0
        test_transaction.credits = 5000000
        test_transaction.payment_method = 'stripe'
        test_transaction.payment_id = f"test_payment_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        test_transaction.stripe_payment_intent = payment_intent_id
        test_transaction.status = PaymentStatus.COMPLETED.value
        
        db.session.add(test_transaction)
        db.session.commit()
        
        print(f"Created test transaction: ID {test_transaction.id}, Payment Intent: {payment_intent_id}")
        return test_transaction

def test_process_commission(transaction):
    """Test the process_affiliate_commission function with the transaction"""
    with app.app_context():
        # First, check the customer referral's current state
        referral = CustomerReferral.query.filter_by(customer_user_id=TEST_USER_ID).first()
        
        if not referral:
            print("ERROR: No referral found for test user")
            return False
        
        print(f"\nProcessing commission for transaction {transaction.id}...")
        print(f"- User: {TEST_USER_ID}")
        print(f"- Affiliate: {referral.affiliate_id}")
        print(f"- First Commission Date: {referral.first_commissioned_purchase_at}")
        print(f"- Transaction Date: {transaction.created_at}")
        
        # Process the commission
        result = process_affiliate_commission(TEST_USER_ID, transaction)
        
        # Check if commission was created
        commission = Commission.query.filter_by(
            triggering_transaction_id=transaction.stripe_payment_intent
        ).first()
        
        if result and commission:
            print("\n✓ SUCCESS: Commission was created!")
            print(f"Commission details:")
            print(f"- ID: {commission.id}")
            print(f"- Amount: £{commission.commission_amount}")
            print(f"- Affiliate: {commission.affiliate_id}")
            print(f"- Level: {commission.commission_level}")
            print(f"- Status: {commission.status}")
            return True
        else:
            print("\n✗ FAILURE: Commission was not created")
            if not result:
                print("- process_affiliate_commission returned False")
            if not commission:
                print("- No commission record found in database")
            return False

def cleanup(transaction):
    """Clean up the test data"""
    with app.app_context():
        try:
            # Delete the commission
            Commission.query.filter_by(
                triggering_transaction_id=transaction.stripe_payment_intent
            ).delete()
            
            # Delete the transaction
            db.session.delete(transaction)
            
            db.session.commit()
            print("\nTest data cleaned up successfully")
            return True
        except Exception as e:
            print(f"Error cleaning up test data: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("=== Testing Affiliate Commission Window ===\n")
    
    # Set the first_commissioned_purchase_at date
    setup_success = set_commission_date()
    if not setup_success:
        print("Failed to set up test. Exiting.")
        sys.exit(1)
    
    # Create a test transaction
    transaction = create_test_transaction()
    
    # Test processing the commission
    test_success = test_process_commission(transaction)
    
    # Clean up
    cleanup(transaction)
    
    print("\n=== Test Results ===")
    if test_success:
        print("✓ TEST PASSED: The affiliate commission window functionality is working correctly!")
        sys.exit(0)
    else:
        print("✗ TEST FAILED: There was a problem with the affiliate commission window functionality.")
        sys.exit(1)