"""
Script to fix the affiliate registration/activation issue

This script patches both the affiliate blueprint and app.py to ensure
the affiliate signup process works correctly.
"""

import os
import logging
from datetime import datetime
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_file(filename):
    """Create a backup of a file before modifying it"""
    if os.path.exists(filename):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{filename}.bak_{timestamp}"
        with open(filename, 'r') as src, open(backup_filename, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Created backup: {backup_filename}")
        return True
    return False

def fix_agree_to_terms_function():
    """
    Fix the agree_to_terms function in affiliate.py to properly handle
    new user registrations
    """
    logger.info("Fixing the agree_to_terms function...")
    
    # Create a new affiliate.py file with the fixed function
    agree_to_terms_implementation = """
@app.route('/affiliate/agree-to-terms', methods=['POST'])
def agree_to_terms():
    \"\"\"
    Handle affiliate agreement to terms submission
    
    This function:
    1. Creates a new affiliate record if the user doesn't have one
    2. Updates an existing affiliate record with terms_agreed_at
    3. Saves the provided PayPal email (if any)
    4. Redirects back to the account page
    \"\"\"
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            flash('Please login to continue', 'warning')
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('login'))
        
        # Get the PayPal email from the form
        paypal_email = request.form.get('paypal_email', '').strip()
        
        # Check if checkbox was checked
        terms_agreed = request.form.get('agree_to_terms') == 'on'
        if not terms_agreed:
            flash('You must agree to the affiliate terms', 'error')
            return redirect(url_for('billing.account_management') + '#tellFriend')
        
        # Get user's affiliate info
        affiliate = Affiliate.query.filter_by(user_id=user_id).first()
        
        # If the user is not an affiliate yet, create an affiliate record
        if not affiliate:
            logger.info(f"Creating new affiliate record for user {user_id}")
            # Generate a unique referral code
            referral_code = str(uuid.uuid4())[:8]
            
            # Create new affiliate
            affiliate = Affiliate(
                user_id=user_id,
                name=user.username,  # Use the username as the affiliate name
                email=user.email,    # Use the user's email
                paypal_email=paypal_email,
                referral_code=referral_code,
                status='active',
                terms_agreed_at=datetime.now()  # Set terms agreed timestamp
            )
            
            try:
                db.session.add(affiliate)
                db.session.commit()
                logger.info(f"New affiliate created for user {user_id} with referral code {referral_code}")
                flash('You have successfully registered as an affiliate!', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error registering affiliate: {str(e)}")
                flash('An error occurred while registering. Please try again.', 'error')
                return redirect(url_for('billing.account_management') + '#tellFriend')
        else:
            # User is already an affiliate, update the record
            logger.info(f"Updating existing affiliate record for user {user_id}")
            affiliate.terms_agreed_at = datetime.now()
            affiliate.status = 'active'
            
            # Update PayPal email if provided
            if paypal_email:
                affiliate.paypal_email = paypal_email
            
            try:
                db.session.commit()
                logger.info(f"Updated affiliate {affiliate.id} for user {user_id}")
                flash('Thank you for agreeing to the affiliate terms!', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating terms agreement: {str(e)}")
                flash('An error occurred. Please try again.', 'error')
        
        # Redirect to the account page's affiliate tab
        return redirect(url_for('billing.account_management') + '#tellFriend')
    except Exception as e:
        logger.error(f"Unexpected error in agree_to_terms: {str(e)}", exc_info=True)
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('billing.account_management'))
"""
    
    # Create the direct implementation in app.py
    with open('direct_affiliate_fix.py', 'w') as f:
        f.write("""
import uuid
from datetime import datetime
from flask import request, redirect, url_for, flash, session
from app import app, db
from models import User, Affiliate

""" + agree_to_terms_implementation)
    
    logger.info("Created direct implementation file: direct_affiliate_fix.py")
    return True

def update_app_py():
    """
    Update app.py to register our direct fix for the affiliate signup
    """
    logger.info("Updating app.py to include direct implementation...")
    
    # Backup app.py first
    if not backup_file('app.py'):
        logger.error("Failed to backup app.py")
        return False
    
    # Read the current app.py file
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    # Find the position to insert our import
    import_position = app_content.find("# Initialize the app")
    if import_position == -1:
        logger.error("Could not find insertion point in app.py")
        return False
    
    # Insert the import for our direct fix
    import_line = "# Import the direct affiliate fix\ntry:\n    from direct_affiliate_fix import *\n    logger.info('Direct affiliate fix imported successfully')\nexcept Exception as e:\n    logger.error(f'Error importing direct affiliate fix: {e}')\n\n"
    updated_content = app_content[:import_position] + import_line + app_content[import_position:]
    
    # Write the updated content
    with open('app.py', 'w') as f:
        f.write(updated_content)
    
    logger.info("Updated app.py to include direct affiliate fix")
    return True

def main():
    """
    Run all fixes
    """
    logger.info("Starting affiliate signup fix...")
    
    # Fix the agree_to_terms function
    if not fix_agree_to_terms_function():
        logger.error("Failed to fix agree_to_terms function")
        return False
    
    # Update app.py to include our fix
    if not update_app_py():
        logger.error("Failed to update app.py")
        return False
    
    logger.info("Affiliate signup fix completed successfully")
    return True

if __name__ == "__main__":
    main()