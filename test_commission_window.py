#!/usr/bin/env python3

"""
Test script to verify the one-year commission window functionality.

This script:
1. Runs the migration to add the first_commissioned_purchase_at column
2. Creates a test customer, affiliate, and referral relationship
3. Sets a first commissioned purchase date for testing
4. Tests transactions both within and outside the one-year window
"""

import sys
import os
from datetime import datetime, timedelta
from app import app, db
from models import User, Affiliate, CustomerReferral, Transaction, Commission, AffiliateStatus, PaymentStatus
from billing import process_affiliate_commission
from migrations_affiliate_commission_window import run_migration

def setup_test_data():
    """Set up test data for the commission window test"""
    with app.app_context():
        # Create test affiliate
        test_affiliate = Affiliate.query.filter_by(email='test_affiliate@example.com').first()
        if not test_affiliate:
            test_affiliate = Affiliate(
                name='Test Affiliate',
                email='test_affiliate@example.com',
                referral_code='TESTCODE',
                status=AffiliateStatus.ACTIVE.value,
                terms_agreed_at=datetime.utcnow()
            )
            db.session.add(test_affiliate)
            db.session.flush()  # Get the ID without committing
            
        # Create test customer
        test_customer = User.query.filter_by(email='test_customer@example.com').first()
        if not test_customer:
            test_customer = User(
                username='test_customer',
                email='test_customer@example.com',
                credits=1000
            )
            db.session.add(test_customer)
            db.session.flush()  # Get the ID without committing
            
        # Create or get the referral relationship
        referral = CustomerReferral.query.filter_by(customer_user_id=test_customer.id).first()
        if not referral:
            referral = CustomerReferral(
                customer_user_id=test_customer.id,
                affiliate_id=test_affiliate.id,
                signup_date=datetime.utcnow()
            )
            db.session.add(referral)
            
        # Set a first commissioned purchase date (one year ago minus 1 day)
        one_year_ago_minus_one_day = datetime.utcnow() - timedelta(days=364)
        referral.first_commissioned_purchase_at = one_year_ago_minus_one_day
        
        # Commit the changes
        db.session.commit()
        
        print(f"Test data created:")
        print(f"- Affiliate: {test_affiliate.name} (ID: {test_affiliate.id})")
        print(f"- Customer: {test_customer.username} (ID: {test_customer.id})")
        print(f"- Referral: ID {referral.id}, First Commission: {referral.first_commissioned_purchase_at}")
        
        return test_customer.id, test_affiliate.id, referral.id

def test_transaction_within_window():
    """Test a transaction within the one-year commission window"""
    with app.app_context():
        customer_id, affiliate_id, referral_id = setup_test_data()
        
        # Create a test transaction (today)
        test_transaction = Transaction(
            user_id=customer_id,
            amount_usd=100.0,
            credits=10000000,  # $100 worth of credits
            payment_method='stripe',
            payment_id='test_payment_id_1',
            stripe_payment_intent='test_payment_intent_1',
            status=PaymentStatus.COMPLETED.value,
            created_at=datetime.utcnow()  # This is within the window (less than 1 year after first purchase)
        )
        db.session.add(test_transaction)
        db.session.commit()
        
        # Test processing the commission
        print("\nTesting transaction WITHIN one-year window:")
        print(f"Transaction date: {test_transaction.created_at}")
        referral = CustomerReferral.query.get(referral_id)
        print(f"First commission date: {referral.first_commissioned_purchase_at}")
        print(f"Window ends: {referral.first_commissioned_purchase_at + timedelta(days=365)}")
        
        # Process the commission
        result = process_affiliate_commission(customer_id, test_transaction)
        
        # Check if commission was created
        commission = Commission.query.filter_by(triggering_transaction_id=test_transaction.stripe_payment_intent).first()
        
        if result and commission:
            print("✓ SUCCESS: Commission was created for transaction within the one-year window")
            print(f"Commission details: {commission.commission_amount} to affiliate {commission.affiliate_id}")
            return True
        else:
            print("✗ FAILURE: Commission was NOT created for transaction within the one-year window")
            return False

def test_transaction_outside_window():
    """Test a transaction outside the one-year commission window"""
    with app.app_context():
        customer_id, affiliate_id, referral_id = setup_test_data()
        
        # Get the referral to determine the exact outside-window date
        referral = CustomerReferral.query.get(referral_id)
        outside_window_date = referral.first_commissioned_purchase_at + timedelta(days=366)  # Just over 1 year
        
        # Create a test transaction (outside the window)
        test_transaction = Transaction(
            user_id=customer_id,
            amount_usd=200.0,
            credits=20000000,  # $200 worth of credits
            payment_method='stripe',
            payment_id='test_payment_id_2',
            stripe_payment_intent='test_payment_intent_2',
            status=PaymentStatus.COMPLETED.value,
            created_at=outside_window_date  # This is outside the window (over 1 year after first purchase)
        )
        db.session.add(test_transaction)
        db.session.commit()
        
        # Test processing the commission
        print("\nTesting transaction OUTSIDE one-year window:")
        print(f"Transaction date: {test_transaction.created_at}")
        print(f"First commission date: {referral.first_commissioned_purchase_at}")
        print(f"Window ends: {referral.first_commissioned_purchase_at + timedelta(days=365)}")
        
        # Process the commission
        result = process_affiliate_commission(customer_id, test_transaction)
        
        # Check if commission was created
        commission = Commission.query.filter_by(triggering_transaction_id=test_transaction.stripe_payment_intent).first()
        
        if not result and not commission:
            print("✓ SUCCESS: Commission was NOT created for transaction outside the one-year window")
            return True
        else:
            print("✗ FAILURE: Commission WAS created for transaction outside the one-year window")
            return False

def cleanup_test_data():
    """Clean up test data created for this test"""
    try:
        with app.app_context():
            # Delete test commissions
            Commission.query.filter(Commission.triggering_transaction_id.like('test_payment_intent%')).delete()
            
            # Delete test transactions
            Transaction.query.filter(Transaction.stripe_payment_intent.like('test_payment_intent%')).delete()
            
            # Delete test referral
            customer = User.query.filter_by(email='test_customer@example.com').first()
            if customer:
                CustomerReferral.query.filter_by(customer_user_id=customer.id).delete()
            
            # Delete test customer and affiliate
            User.query.filter_by(email='test_customer@example.com').delete()
            Affiliate.query.filter_by(email='test_affiliate@example.com').delete()
            
            db.session.commit()
            print("\nTest data cleaned up successfully")
            return True
    except Exception as e:
        print(f"Error cleaning up test data: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("=== Testing One-Year Commission Window ===")
    
    # First, run the migration
    print("\nRunning migration to add first_commissioned_purchase_at column...")
    migration_success = run_migration()
    if not migration_success:
        print("Migration failed! Exiting tests.")
        sys.exit(1)
    
    # Run the tests
    within_window_success = test_transaction_within_window()
    outside_window_success = test_transaction_outside_window()
    
    # Clean up test data
    cleanup_test_data()
    
    # Print results
    print("\n=== Test Results ===")
    if within_window_success and outside_window_success:
        print("✓ ALL TESTS PASSED! The one-year commission window is working correctly.")
        sys.exit(0)
    else:
        print("✗ TESTS FAILED! The one-year commission window is not working correctly.")
        sys.exit(1)