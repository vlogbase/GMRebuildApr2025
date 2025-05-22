"""
Simplified Affiliate Blueprint Module

This module provides a streamlined version of the affiliate system blueprint.
It focuses only on essential functionality with improved error handling and
eliminates complex status requirements.
"""

import logging
from flask import Blueprint, request, redirect, url_for, flash, session, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
simplified_affiliate_bp = Blueprint('simplified_affiliate', __name__, url_prefix='/simplified-affiliate')

@simplified_affiliate_bp.route('/update-paypal-email', methods=['POST'])
def update_paypal_email():
    """Update user's PayPal email address with improved error handling"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User
    
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            flash('Please login to update your PayPal email', 'warning')
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        
        # Get form data with extra validation
        paypal_email = request.form.get('paypal_email', '').strip()
        
        if not paypal_email or '@' not in paypal_email:
            flash('Please enter a valid PayPal email address', 'error')
            return redirect(url_for('billing.account_management'))
        
        # Update user's PayPal email
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User not found for ID {user_id}")
            flash('User not found', 'error')
            return redirect(url_for('billing.account_management'))
        
        # Log the change for debugging
        logger.info(f"Updating PayPal email for user {user_id} from '{user.paypal_email}' to '{paypal_email}'")
        
        user.paypal_email = paypal_email
        db.session.commit()
        
        flash('Your PayPal email has been updated successfully', 'success')
        return redirect(url_for('billing.account_management'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {str(e)}", exc_info=True)
        flash('There was a problem updating your PayPal email. Please try again.', 'error')
        return redirect(url_for('billing.account_management'))

def init_app(app):
    """
    Initialize the simplified affiliate blueprint with a Flask application
    
    This function registers the blueprint and ensures it's only registered once.
    
    Args:
        app: Flask application
        
    Returns:
        None
    """
    # Register blueprint
    if 'simplified_affiliate_bp_registered' not in app.extensions:
        app.register_blueprint(simplified_affiliate_bp)
        app.extensions['simplified_affiliate_bp_registered'] = True
        
        # Make sure to exempt from CSRF protection
        from flask_wtf.csrf import CSRFProtect
        csrf = CSRFProtect(app)
        csrf.exempt('simplified_affiliate.update_paypal_email')
        
        logger.info("Simplified Affiliate blueprint registered successfully")