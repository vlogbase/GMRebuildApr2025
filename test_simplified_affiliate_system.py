"""
Simple test script to verify the simplified affiliate system works properly
"""
import logging
from flask import url_for
from app import app, db
from models import User, CustomerReferral, Commission, CommissionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_referral_flow():
    """Test the simplified affiliate referral flow"""
    with app.app_context():
        try:
            # Create a referrer user
            referrer = User.query.filter_by(email='referrer@example.com').first()
            if not referrer:
                referrer = User(
                    username='referrer_test',
                    email='referrer@example.com'
                )
                db.session.add(referrer)
                db.session.commit()
                logger.info(f"Created referrer user with ID {referrer.id}")
            
            # Generate a referral code
            if not referrer.referral_code:
                referrer.generate_referral_code()
                db.session.commit()
                logger.info(f"Generated referral code {referrer.referral_code} for referrer")
            
            # Create a referred user
            referred = User.query.filter_by(email='referred@example.com').first()
            if not referred:
                referred = User(
                    username='referred_test',
                    email='referred@example.com'
                )
                db.session.add(referred)
                db.session.commit()
                logger.info(f"Created referred user with ID {referred.id}")
            
            # Track the referral
            if not referred.referred_by_user_id:
                referred.referred_by_user_id = referrer.id
                db.session.commit()
                logger.info(f"Set referred_by_user_id={referrer.id} for user {referred.id}")
            
            # Create a customer referral record
            referral = CustomerReferral.query.filter_by(customer_user_id=referred.id).first()
            if not referral:
                referral = CustomerReferral(
                    customer_user_id=referred.id,
                    referrer_user_id=referrer.id
                )
                db.session.add(referral)
                db.session.commit()
                logger.info(f"Created CustomerReferral record: {referral.id}")
            
            # Verify the referral relationship
            assert referred.referred_by_user_id == referrer.id
            logger.info("PASS: referred_by_user_id set correctly")
            
            # Check that the referral record exists
            referral = CustomerReferral.query.filter_by(
                customer_user_id=referred.id,
                referrer_user_id=referrer.id
            ).first()
            assert referral is not None
            logger.info("PASS: CustomerReferral record exists")
            
            # Verify the referrer's referrals
            assert referred in referrer.referred_users
            logger.info("PASS: referred user in referrer's referred_users")
            
            # Update PayPal email
            referrer.paypal_email = "paypal@example.com"
            db.session.commit()
            logger.info(f"Updated PayPal email for referrer to {referrer.paypal_email}")
            
            # Create a commission
            commission = Commission.query.filter_by(
                user_id=referrer.id,
                triggering_transaction_id="test_transaction"
            ).first()
            
            if not commission:
                commission = Commission(
                    user_id=referrer.id,
                    triggering_transaction_id="test_transaction",
                    stripe_payment_status="succeeded",
                    purchase_amount_base=100.0,
                    commission_rate=0.10,
                    commission_amount=10.0,
                    commission_level=1,
                    status=CommissionStatus.HELD.value
                )
                db.session.add(commission)
                db.session.commit()
                logger.info(f"Created Commission record: {commission.id}")
            
            # Verify the commission
            assert commission in referrer.commissions
            logger.info("PASS: commission in referrer's commissions")
            
            logger.info("All tests passed! The simplified affiliate system is working correctly.")
            return True
            
        except Exception as e:
            logger.error(f"Error testing referral flow: {str(e)}", exc_info=True)
            db.session.rollback()
            return False

if __name__ == "__main__":
    with app.app_context():
        result = test_referral_flow()
        if result:
            print("✅ All tests passed! The simplified affiliate system is working correctly.")
        else:
            print("❌ Test failed. See logs for details.")