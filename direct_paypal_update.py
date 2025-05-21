"""
Direct PayPal Email Update

A direct, stripped-down module for updating PayPal email addresses
that completely bypasses CSRF protection.
"""

import logging
import os
from flask import Flask, request, redirect, url_for, flash, session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_route(app):
    """Create a direct route for updating PayPal email"""
    from flask_wtf.csrf import CSRFProtect
    
    # Create the route and explicitly exempt it from CSRF protection
    @app.route('/direct-paypal-update', methods=['POST'])
    def direct_paypal_update():
        """Update PayPal email directly, no CSRF validation"""
        logger.info("Direct PayPal email update route activated")
        
        try:
            # Log the entire session contents for debugging
            logger.info(f"Session contents: {dict(session)}")
            logger.info(f"Session keys: {list(session.keys())}")
            
            # Check all possible user ID keys that might be in the session
            user_id = None
            possible_keys = ['user_id', 'id', 'uid', '_user_id', 'user', 'flask_login_user_id']
            
            for key in possible_keys:
                if key in session:
                    user_id = session[key]
                    logger.info(f"Found user identifier in session with key '{key}': {user_id}")
                    break
                    
            if user_id is None:
                # Try to detect if we're using Flask-Login
                logger.info("No direct user ID in session, checking for Flask-Login session data")
                if 'user' in session:
                    logger.info(f"Found 'user' in session: {session['user']}")
                    if isinstance(session['user'], dict) and 'id' in session['user']:
                        user_id = session['user']['id']
                        logger.info(f"Extracted user ID from session['user']: {user_id}")
                
            if user_id is None:
                logger.error("No user identifier found in any expected session keys")
                flash('Session authentication issue. Please try logging out and back in.', 'warning')
                return redirect(url_for('login'))
            
            # Import models and get user
            from models import User, Affiliate
            from database import db
            
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User not found for ID {user_id}")
                flash('User not found', 'error')
                return redirect(url_for('login'))
                
            logger.info(f"Processing direct PayPal update for user {user_id} ({user.email})")
            
            # Get PayPal email from form
            paypal_email = request.form.get('paypal_email', '').strip()
            
            if not paypal_email:
                logger.error("PayPal email update failed: No email provided")
                flash('PayPal email is required', 'error')
                return redirect(url_for('billing.account_management') + '#tellFriend')
            
            # Find affiliate record by email
            affiliate = Affiliate.query.filter_by(email=user.email).first()
            
            if not affiliate:
                logger.error(f"No affiliate record found for user {user_id} ({user.email})")
                flash('Affiliate record not found. Please contact support.', 'error')
                return redirect(url_for('billing.account_management') + '#tellFriend')
            
            # Update PayPal email
            logger.info(f"Updating PayPal email for affiliate ID {affiliate.id} to: {paypal_email}")
            affiliate.paypal_email = paypal_email
            
            # Save to database
            db.session.commit()
            
            # Success message
            flash('Your PayPal email has been updated successfully!', 'success')
            logger.info(f"PayPal email updated successfully for affiliate ID {affiliate.id}")
            
            # Redirect back to account page
            return redirect(url_for('billing.account_management') + '#tellFriend')
            
        except Exception as e:
            logger.error(f"Error in direct PayPal update: {str(e)}")
            flash('An error occurred while updating your PayPal email. Please try again.', 'error')
            return redirect(url_for('billing.account_management') + '#tellFriend')
    
    # Explicitly exempt this route from CSRF protection
    csrf = app.extensions.get('csrf', None)
    if csrf and hasattr(csrf, 'exempt'):
        csrf.exempt(direct_paypal_update)
        logger.info("Direct PayPal update route explicitly exempted from CSRF protection")
    
    return app