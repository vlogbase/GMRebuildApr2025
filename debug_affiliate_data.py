import os
import sys
import json
from datetime import datetime
import logging
import psycopg2
import psycopg2.extras

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def dump_datetime(value):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError("Type %s not serializable" % type(value))

# !!! Use these actual email addresses in the script !!!
dads_email_to_check = "pdsurtees@gmail.com"
your_affiliate_email = "andy@sentigral.com"

try:
    # Get database connection string from environment variable
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    logger.info("Connecting to database...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    output_data = {
        'dad_user_info': {},
        'your_affiliate_info': {},
        'referral_info': {},
        'transaction_info': {},
        'commission_info': {}
    }
    
    # Get dad's user info
    logger.info(f"Looking up user with email: {dads_email_to_check}")
    cursor.execute("SELECT id, email, username, created_at FROM \"user\" WHERE email = %s", (dads_email_to_check,))
    dad = cursor.fetchone()
    
    # Get affiliate info
    logger.info(f"Looking up affiliate with email: {your_affiliate_email}")
    cursor.execute("SELECT id, referral_code, status, email FROM affiliate WHERE email = %s", (your_affiliate_email,))
    you_as_affiliate = cursor.fetchone()
    
    if you_as_affiliate:
        output_data['your_affiliate_info'] = {
            "id": you_as_affiliate['id'],
            "referral_code": you_as_affiliate['referral_code'],
            "status": you_as_affiliate['status'],
            "email": you_as_affiliate['email']
        }
        logger.info(f"Found affiliate: {output_data['your_affiliate_info']}")
    else:
        output_data['your_affiliate_info']['error'] = f"Affiliate record not found for {your_affiliate_email}"
        logger.warning(f"Affiliate not found: {your_affiliate_email}")
    
    if dad:
        dads_user_id = dad['id']
        output_data['dad_user_info'] = {
            "id": dad['id'],
            "email": dad['email'],
            "username": dad['username'],
            "created_at": dad['created_at']
        }
        logger.info(f"Found user: {output_data['dad_user_info']}")
        
        # Get referral info
        cursor.execute("SELECT id, customer_user_id, affiliate_id, signup_date FROM customer_referral WHERE customer_user_id = %s", (dads_user_id,))
        referral = cursor.fetchone()
        
        if referral:
            output_data['referral_info'] = {
                "id": referral['id'],
                "customer_user_id": referral['customer_user_id'],
                "affiliate_id": referral['affiliate_id'],
                "signup_date": referral['signup_date']
            }
            logger.info(f"Found referral: {output_data['referral_info']}")
        else:
            output_data['referral_info']['error'] = f"No CustomerReferral for User ID {dads_user_id} (Email: {dads_email_to_check})"
            logger.warning(f"No referral found for user ID: {dads_user_id}")
        
        # Assuming the transaction amount was $5.00 for this specific check
        cursor.execute(
            "SELECT id, user_id, package_id, amount_usd, credits, status, stripe_payment_intent, created_at FROM transaction WHERE user_id = %s AND amount_usd = %s ORDER BY created_at DESC LIMIT 1", 
            (dads_user_id, 5.0)
        )
        dads_transaction = cursor.fetchone()
        
        if dads_transaction:
            output_data['transaction_info'] = {
                "id": dads_transaction['id'],
                "user_id": dads_transaction['user_id'],
                "package_id": dads_transaction['package_id'],
                "amount_usd": float(dads_transaction['amount_usd']),
                "credits": dads_transaction['credits'],
                "status": dads_transaction['status'],
                "stripe_payment_intent": dads_transaction['stripe_payment_intent'],
                "created_at": dads_transaction['created_at']
            }
            logger.info(f"Found transaction: {output_data['transaction_info']}")
            
            if dads_transaction['stripe_payment_intent']:
                # Check for commissions
                cursor.execute(
                    "SELECT id, affiliate_id, commission_amount, commission_level, status, commission_earned_date, commission_available_date FROM commission WHERE triggering_transaction_id = %s", 
                    (dads_transaction['stripe_payment_intent'],)
                )
                commissions = cursor.fetchall()
                
                if commissions:
                    output_data['commission_info']['related_to_transaction'] = [{
                        "id": comm['id'], 
                        "affiliate_id": comm['affiliate_id'],
                        "amount": float(comm['commission_amount']), 
                        "level": comm['commission_level'],
                        "status": comm['status'], 
                        "earned_date": comm['commission_earned_date'],
                        "available_date": comm['commission_available_date']
                    } for comm in commissions]
                    logger.info(f"Found commissions: {output_data['commission_info']['related_to_transaction']}")
                else:
                    output_data['commission_info']['related_to_transaction_error'] = f"No Commission for intent {dads_transaction['stripe_payment_intent']}"
                    logger.warning(f"No commissions found for payment intent: {dads_transaction['stripe_payment_intent']}")
            else:
                output_data['commission_info']['transaction_intent_error'] = "Transaction has no stripe_payment_intent"
                logger.warning("Transaction has no stripe_payment_intent")
        else:
            output_data['transaction_info']['error'] = f"No $5.00 transaction for User ID {dads_user_id} (Email: {dads_email_to_check})"
            logger.warning(f"No $5.00 transaction found for user ID: {dads_user_id}")
    else:
        output_data['dad_user_info']['error'] = f"User with email {dads_email_to_check} not found"
        logger.warning(f"User not found: {dads_email_to_check}")
    
    # Close database connection
    cursor.close()
    conn.close()
    
    # Write to a file
    with open("affiliate_debug_output.json", "w") as f:
        json.dump(output_data, f, indent=4, default=dump_datetime)
    print("Debug data written to affiliate_debug_output.json")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()