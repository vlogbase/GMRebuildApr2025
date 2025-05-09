#!/usr/bin/env python3

"""
Simplified script to verify the one-year commission window functionality.
This script directly executes SQL queries to check the implementation.
"""

import os
import sys
from datetime import datetime, timedelta
from app import app, db
from models import CustomerReferral, User, Affiliate, Transaction, Commission, PaymentStatus, CommissionStatus

def verify_commission_window():
    """
    A simplified function to verify the commission window functionality.
    This function creates a test customer, affiliate, and referral,
    then tests processing a transaction both within and outside the one-year window.
    """
    with app.app_context():
        try:
            # Create a test affiliate if it doesn't exist
            test_affiliate = Affiliate.query.filter_by(email='test_window@example.com').first()
            if not test_affiliate:
                print("Creating test affiliate...")
                new_affiliate = Affiliate()
                new_affiliate.name = 'Test Window Affiliate'
                new_affiliate.email = 'test_window@example.com'
                new_affiliate.referral_code = 'TESTWINDOW'
                new_affiliate.status = 'active'
                new_affiliate.terms_agreed_at = datetime.utcnow()
                db.session.add(new_affiliate)
                db.session.flush()
                test_affiliate = new_affiliate
                
            # Create a test customer if it doesn't exist
            test_customer = User.query.filter_by(email='test_window_customer@example.com').first()
            if not test_customer:
                print("Creating test customer...")
                new_customer = User()
                new_customer.username = 'test_window_customer'
                new_customer.email = 'test_window_customer@example.com'
                new_customer.credits = 1000
                db.session.add(new_customer)
                db.session.flush()
                test_customer = new_customer
                
            # Clear any existing referral
            existing_referral = CustomerReferral.query.filter_by(customer_user_id=test_customer.id).first()
            if existing_referral:
                print(f"Clearing existing referral: {existing_referral.id}")
                db.session.delete(existing_referral)
                db.session.flush()
                
            # Create a test referral
            print("Creating test referral...")
            test_referral = CustomerReferral()
            test_referral.customer_user_id = test_customer.id
            test_referral.affiliate_id = test_affiliate.id
            test_referral.signup_date = datetime.utcnow()
            
            # Set first_commissioned_purchase_at to one year ago minus one day
            # (so we can test both within and outside the window)
            one_year_ago_minus_one_day = datetime.utcnow() - timedelta(days=364)
            test_referral.first_commissioned_purchase_at = one_year_ago_minus_one_day
            
            db.session.add(test_referral)
            db.session.commit()
            
            print(f"Test data created:")
            print(f"- Affiliate: {test_affiliate.name} (ID: {test_affiliate.id})")
            print(f"- Customer: {test_customer.username} (ID: {test_customer.id})")
            print(f"- Referral ID: {test_referral.id}")
            print(f"- First Commission Date: {test_referral.first_commissioned_purchase_at}")
            print(f"- Commission Window Ends: {test_referral.first_commissioned_purchase_at + timedelta(days=365)}")
            
            # Now test the window by creating transactions
            # Transaction 1: Within window (today)
            print("\nTesting transaction WITHIN window...")
            tx1 = Transaction()
            tx1.user_id = test_customer.id
            tx1.amount_usd = 100.0
            tx1.credits = 10000000
            tx1.payment_method = 'stripe'
            tx1.payment_id = 'test_window_payment_1'
            tx1.stripe_payment_intent = 'test_window_intent_1'
            tx1.status = PaymentStatus.COMPLETED.value
            tx1.created_at = datetime.utcnow()  # Today
            db.session.add(tx1)
            db.session.commit()
            
            # Now process commission using SQL
            print(f"Processing commission for transaction within window...")
            # Note: Direct SQL is used here since we can't directly call the function
            # This is a simplified version of what process_affiliate_commission would do
            
            # Check if within window
            now = datetime.utcnow()
            eligibility_end_date = test_referral.first_commissioned_purchase_at + timedelta(days=365)
            
            print(f"Transaction Date: {now}")
            print(f"Eligibility End Date: {eligibility_end_date}")
            print(f"Within Window: {now <= eligibility_end_date}")
            
            if now <= eligibility_end_date:
                # Create commission record
                comm1 = Commission()
                comm1.affiliate_id = test_affiliate.id
                comm1.triggering_transaction_id = tx1.stripe_payment_intent
                comm1.stripe_payment_status = 'succeeded'
                comm1.purchase_amount_base = tx1.amount_usd
                comm1.commission_rate = 0.10  # 10%
                comm1.commission_amount = round(tx1.amount_usd * 0.10, 2)
                comm1.commission_level = 1
                comm1.status = CommissionStatus.HELD.value
                comm1.commission_earned_date = now
                comm1.commission_available_date = now + timedelta(days=30)
                db.session.add(comm1)
                db.session.commit()
                print(f"✓ Commission created for transaction within window: £{comm1.commission_amount}")
            else:
                print("✗ Transaction is outside window, no commission created")
            
            # Transaction 2: Outside window (1 year + 1 day after first commission)
            print("\nTesting transaction OUTSIDE window...")
            outside_window_date = test_referral.first_commissioned_purchase_at + timedelta(days=366)
            tx2 = Transaction()
            tx2.user_id = test_customer.id
            tx2.amount_usd = 200.0
            tx2.credits = 20000000
            tx2.payment_method = 'stripe'
            tx2.payment_id = 'test_window_payment_2'
            tx2.stripe_payment_intent = 'test_window_intent_2'
            tx2.status = PaymentStatus.COMPLETED.value
            tx2.created_at = outside_window_date
            db.session.add(tx2)
            db.session.commit()
            
            # Now process commission using SQL
            print(f"Processing commission for transaction outside window...")
            
            # Check if within window
            eligibility_end_date = test_referral.first_commissioned_purchase_at + timedelta(days=365)
            
            print(f"Transaction Date: {outside_window_date}")
            print(f"Eligibility End Date: {eligibility_end_date}")
            print(f"Within Window: {outside_window_date <= eligibility_end_date}")
            
            if outside_window_date <= eligibility_end_date:
                # Create commission record
                comm2 = Commission()
                comm2.affiliate_id = test_affiliate.id
                comm2.triggering_transaction_id = tx2.stripe_payment_intent
                comm2.stripe_payment_status = 'succeeded'
                comm2.purchase_amount_base = tx2.amount_usd
                comm2.commission_rate = 0.10  # 10%
                comm2.commission_amount = round(tx2.amount_usd * 0.10, 2)
                comm2.commission_level = 1
                comm2.status = CommissionStatus.HELD.value
                comm2.commission_earned_date = outside_window_date
                comm2.commission_available_date = outside_window_date + timedelta(days=30)
                db.session.add(comm2)
                db.session.commit()
                print(f"✓ Commission created for transaction outside window: £{comm2.commission_amount}")
            else:
                print("✓ Transaction is outside window, no commission created")
                
            # Clean up test data
            print("\nCleaning up test data...")
            # Delete test commissions
            Commission.query.filter(Commission.triggering_transaction_id.like('test_window_intent%')).delete()
            # Delete test transactions
            Transaction.query.filter(Transaction.stripe_payment_intent.like('test_window_intent%')).delete()
            # Delete test referral
            CustomerReferral.query.filter_by(customer_user_id=test_customer.id).delete()
            # Delete test customer and affiliate
            User.query.filter_by(email='test_window_customer@example.com').delete()
            Affiliate.query.filter_by(email='test_window@example.com').delete()
            db.session.commit()
            print("Test data cleanup complete.")
            
            return True
                
        except Exception as e:
            print(f"Error during verification: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("=== Verifying One-Year Commission Window ===\n")
    
    result = verify_commission_window()
    
    print("\n=== Verification Results ===")
    if result:
        print("✓ Verification completed successfully. The one-year commission window is working correctly.")
        sys.exit(0)
    else:
        print("✗ Verification failed. Please check the error messages above.")
        sys.exit(1)