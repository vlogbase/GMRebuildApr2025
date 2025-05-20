"""
This module provides a direct handler for the affiliate signup process
that doesn't rely on the affiliate blueprint.
"""

import uuid
import logging
import string
import secrets
from datetime import datetime
from flask import Flask, request, session, flash, redirect, url_for, render_template
from flask_wtf.csrf import generate_csrf, validate_csrf, CSRFError
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_direct_handler(app, db):
    """
    Register a direct route handler for the affiliate terms agreement
    that creates or updates the affiliate record.
    
    Args:
        app: Flask application
        db: SQLAlchemy database instance
    """
    logger.info("Registering direct affiliate signup handler")
    
    @app.route('/affiliate/agree-to-terms', methods=['GET', 'POST'])
    def direct_affiliate_signup():
        """
        Process the affiliate signup form submission.
        Creates a new affiliate account or updates an existing one.
        
        If terms are not agreed, we delete any pending affiliate record to put the user
        back in the state they were in before applying.
        
        Added GET method handling to provide a valid CSRF token and handle token issues.
        """
        from models import User, Affiliate
        
        # Handle GET requests - redirect to the affiliate section of the billing page
        if request.method == 'GET':
            return redirect(url_for('billing.account_management') + '#tellFriend')
        
        logger.debug("Direct affiliate signup handler called")
        logger.debug(f"Form data: {request.form}")
        
        # Check CSRF token
        csrf_token = request.form.get('csrf_token', '')
        try:
            validate_csrf(csrf_token)
        except CSRFError:
            logger.warning("CSRF validation failed")
            flash('Your session has expired. Please try again.', 'error')
            return redirect(url_for('billing.account_management') + '#tellFriend')
        
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
        
        # First, check for existing affiliate records
        affiliate = Affiliate.query.filter_by(user_id=user_id).first()
        
        # Also check by email as a fallback (for older records without user_id)
        if not affiliate:
            affiliate = Affiliate.query.filter_by(email=user.email).first()
            
        # If terms are not agreed, delete any pending affiliate record
        if not terms_agreed:
            if affiliate and affiliate.status == 'pending_terms':
                logger.info(f"Terms not agreed, deleting pending affiliate record for user {user_id}")
                try:
                    db.session.delete(affiliate)
                    db.session.commit()
                    logger.info(f"Successfully deleted pending affiliate record for user {user_id}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error deleting pending affiliate record: {str(e)}")
            
            flash('You must agree to the affiliate terms', 'error')
            return redirect(url_for('billing.account_management') + '#tellFriend')
        
        # If we have an existing affiliate record in pending status, delete it and create a new one
        if affiliate and affiliate.status == 'pending_terms':
            logger.info(f"Deleting pending affiliate record for user {user_id} to create a new one")
            try:
                db.session.delete(affiliate)
                db.session.commit()
                affiliate = None  # Set to None so we create a new record
                logger.info(f"Successfully deleted pending affiliate record for user {user_id}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting pending affiliate record: {str(e)}")
                flash('An error occurred while processing your application. Please try again.', 'error')
                return redirect(url_for('billing.account_management') + '#tellFriend')
        
        # If the user is not an affiliate yet or we deleted a pending record, create a new affiliate record
        if not affiliate:
            logger.info(f"Creating new affiliate record for user {user_id}")
            try:
                # Create new affiliate
                # Generate a unique, user-friendly referral code
                alphabet = string.ascii_uppercase + string.digits
                referral_code = ''.join(secrets.choice(alphabet) for _ in range(8))
                
                # Make sure the referral code is unique
                while db.session.query(Affiliate).filter_by(referral_code=referral_code).first():
                    referral_code = ''.join(secrets.choice(alphabet) for _ in range(8))
                    
                logger.info(f"Generated unique referral code: {referral_code}")
                logger.info(f"Creating affiliate with user_id: {user_id}, name: {user.username}, email: {user.email}")
                
                # Try to create affiliate with user_id
                try:
                    # Prepare a dictionary with all affiliate parameters
                    affiliate_data = {
                        'user_id': user_id,
                        'name': user.username,  # Use the username as the affiliate name
                        'email': user.email,    # Use the user's email
                        'paypal_email': paypal_email,
                        'referral_code': referral_code,
                        'status': 'active',     # Always create as active
                        'terms_agreed_at': datetime.now()  # Set terms agreed timestamp
                    }
                    
                    # Try to create the affiliate with all fields
                    affiliate = Affiliate(**affiliate_data)
                    logger.info("Successfully created affiliate with user_id field")
                except TypeError as e:
                    # If user_id field doesn't exist yet (older schema), remove it from the parameters
                    logger.warning(f"TypeError creating affiliate with user_id: {str(e)}")
                    logger.info("Creating affiliate without user_id field (will be linked later by migration)")
                    
                    # Remove user_id from parameters and try again
                    affiliate_data = {
                        'name': user.username,
                        'email': user.email,
                        'paypal_email': paypal_email,
                        'referral_code': referral_code,
                        'status': 'active',     # Always create as active
                        'terms_agreed_at': datetime.now()
                    }
                    affiliate = Affiliate(**affiliate_data)
                
                db.session.add(affiliate)
                db.session.commit()
                logger.info(f"New affiliate created with referral code {referral_code}")
                flash('You have successfully registered as an affiliate!', 'success')
            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"IntegrityError registering affiliate: {str(e)}")
                flash('There was a problem with your registration. This email may already be registered.', 'error')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error registering affiliate: {str(e)}")
                flash('An error occurred while registering. Please try again.', 'error')
        else:
            # User is already an affiliate, update the record
            logger.info(f"Updating existing affiliate record for user {user_id}")
            try:
                affiliate.terms_agreed_at = datetime.now()
                affiliate.status = 'active'  # Ensure status is always active when terms are agreed
                
                # Update PayPal email if provided
                if paypal_email:
                    affiliate.paypal_email = paypal_email
                
                db.session.commit()
                logger.info(f"Updated affiliate {affiliate.id} for user {user_id}")
                flash('Thank you for agreeing to the affiliate terms!', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating terms agreement: {str(e)}")
                flash('An error occurred. Please try again.', 'error')
        
        # Redirect to the account page's affiliate tab
        return redirect(url_for('billing.account_management') + '#tellFriend')