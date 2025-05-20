"""
Direct implementation of the agree_to_terms route for the affiliate system
"""

import uuid
from datetime import datetime
from flask import request, redirect, url_for, flash, session
from app import app, db
from models import User, Affiliate

@app.route('/affiliate/agree-to-terms', methods=['POST'])
def direct_agree_to_terms():
    """
    Handle affiliate agreement to terms submission
    
    This function:
    1. Creates a new affiliate record if the user doesn't have one
    2. Updates an existing affiliate record with terms_agreed_at
    3. Saves the provided PayPal email (if any)
    4. Redirects back to the account page
    """
    # Add detailed logging
    print("=== DIRECT AFFILIATE SIGNUP FUNCTION CALLED ===")
    print(f"Session: {session}")
    print(f"Form data: {request.form}")
    
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
            print(f"Creating new affiliate record for user {user_id}")
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
                print(f"New affiliate created with referral code {referral_code}")
                flash('You have successfully registered as an affiliate!', 'success')
            except Exception as e:
                db.session.rollback()
                print(f"Error registering affiliate: {str(e)}")
                flash('An error occurred while registering. Please try again.', 'error')
                return redirect(url_for('billing.account_management') + '#tellFriend')
        else:
            # User is already an affiliate, update the record
            print(f"Updating existing affiliate record for user {user_id}")
            affiliate.terms_agreed_at = datetime.now()
            affiliate.status = 'active'
            
            # Update PayPal email if provided
            if paypal_email:
                affiliate.paypal_email = paypal_email
            
            try:
                db.session.commit()
                print(f"Updated affiliate {affiliate.id} for user {user_id}")
                flash('Thank you for agreeing to the affiliate terms!', 'success')
            except Exception as e:
                db.session.rollback()
                print(f"Error updating terms agreement: {str(e)}")
                flash('An error occurred. Please try again.', 'error')
        
        # Redirect to the account page's affiliate tab
        return redirect(url_for('billing.account_management') + '#tellFriend')
    except Exception as e:
        print(f"Unexpected error in agree_to_terms: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('billing.account_management'))