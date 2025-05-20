"""
Improved affiliate agreement handler

This module provides a more robust handler for the /affiliate/agree-to-terms endpoint
that addresses form validation issues while maintaining CSRF compatibility.
"""

import logging
from datetime import datetime
from flask import request, session, flash, redirect, url_for
from app import app, db
from models import User, Affiliate
from forms import AgreeToTermsForm

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/affiliate/agree-to-terms', methods=['POST'])
def agree_to_terms():
    """
    Handle affiliate agreement to terms submission with improved validation
    
    This implementation:
    1. Uses Flask-WTF form validation correctly
    2. Handles form validation errors gracefully
    3. Creates a new affiliate record if needed
    4. Updates existing affiliate records appropriately
    """
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
        
        # Create form instance with request data - critical for validation to work
        form = AgreeToTermsForm()
        
        # Log request data for debugging
        logger.debug(f"Form data: agree_to_terms={request.form.get('agree_to_terms')}, paypal_email={request.form.get('paypal_email')}")
        
        # Validate form - this checks CSRF token and field requirements
        if not form.validate_on_submit():
            # Log validation errors
            logger.error(f"Form validation errors: {form.errors}")
            
            # Flash each error message
            for field_name, errors in form.errors.items():
                for error in errors:
                    # Get readable field name, defaulting to the field name if no label
                    field_label = getattr(form[field_name], 'label', None)
                    field_text = field_label.text if field_label else field_name
                    flash(f"{field_text}: {error}", 'error')
            
            # Redirect back to the form
            return redirect(url_for('billing.account_management') + '#tellFriend')
        
        # Get the validated data
        terms_agreed = form.agree_to_terms.data
        paypal_email = form.paypal_email.data.strip() if form.paypal_email.data else ''
        
        # Must agree to terms to continue
        if not terms_agreed:
            flash('You must agree to the affiliate terms', 'error')
            return redirect(url_for('billing.account_management') + '#tellFriend')
        
        # Get user's existing affiliate info if any
        affiliate = Affiliate.query.filter_by(user_id=user_id).first()
        
        # If the user is not an affiliate yet, create an affiliate record
        if not affiliate:
            logger.info(f"Creating new affiliate record for user {user_id}")
            
            # Generate a referral code with username and random string
            import string
            import random
            random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            referral_code = f"{user.username.lower()}-{random_str}"
            
            # Create new affiliate record
            try:
                affiliate = Affiliate(
                    user_id=user_id,
                    name=user.username,
                    email=user.email,
                    paypal_email=paypal_email,
                    referral_code=referral_code,
                    status='active',
                    terms_agreed_at=datetime.utcnow()
                )
                
                db.session.add(affiliate)
                db.session.commit()
                
                logger.info(f"Successfully created affiliate record for user {user_id}")
                flash('Thank you for joining our affiliate program!', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating affiliate: {str(e)}")
                flash('An error occurred. Please try again.', 'error')
        else:
            # Update existing affiliate record
            logger.info(f"Updating existing affiliate {affiliate.id} for user {user_id}")
            
            # Update terms agreement timestamp
            affiliate.terms_agreed_at = datetime.utcnow()
            
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