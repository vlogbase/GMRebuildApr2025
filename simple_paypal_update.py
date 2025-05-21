"""
Simple PayPal Email Update Module

This standalone module provides a simple endpoint for updating
an affiliate's PayPal email address without CSRF validation.
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
simple_paypal_bp = Blueprint('simple_paypal', __name__, url_prefix='/simple-paypal')

@simple_paypal_bp.route('/update', methods=['POST'])
def update_paypal_email():
    """Simple endpoint to update PayPal email without CSRF validation"""
    # Import models inside function to avoid circular imports
    from models import User, Affiliate
    from database import db
    
    # Log the request
    logger.info("Simple PayPal email update requested")
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        logger.error("User not authenticated for PayPal email update")
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    # Get user from session
    user_id = session['user_id']
    
    # Import User model and get user
    try:
        from models import User
        user = User.query.get(user_id)
        
        if not user:
            logger.error(f"User not found for ID {user_id}")
            flash('User not found', 'error')
            return redirect(url_for('login'))
            
        logger.info(f"Processing PayPal update for user {user_id} ({user.email})")
        
        # Get PayPal email from form
        paypal_email = request.form.get('paypal_email', '').strip()
        
        if not paypal_email:
            logger.error("PayPal email update failed: No email provided")
            flash('PayPal email is required', 'error')
            return redirect(url_for('billing.account_management') + '#tellFriend')
        
        # Find affiliate record by email
        from models import Affiliate
        affiliate = Affiliate.query.filter_by(email=user.email).first()
        
        if not affiliate:
            logger.error(f"No affiliate record found for user {user_id} ({user.email})")
            flash('Affiliate record not found. Please contact support.', 'error')
            return redirect(url_for('billing.account_management') + '#tellFriend')
        
        # Update PayPal email
        logger.info(f"Updating PayPal email for affiliate ID {affiliate.id} to: {paypal_email}")
        affiliate.paypal_email = paypal_email
        
        # Save to database
        from database import db
        db.session.commit()
        
        # Success message
        flash('Your PayPal email has been updated successfully!', 'success')
        logger.info(f"PayPal email updated successfully for affiliate ID {affiliate.id}")
        
        # Redirect back to account page
        return redirect(url_for('billing.account_management') + '#tellFriend')
        
    except Exception as e:
        logger.error(f"Error updating PayPal email: {str(e)}")
        flash('An error occurred while updating your PayPal email. Please try again.', 'error')
        return redirect(url_for('billing.account_management') + '#tellFriend')

def register_blueprint(app):
    """Register the blueprint with the Flask app"""
    app.register_blueprint(simple_paypal_bp)
    logger.info("Simple PayPal update blueprint registered")