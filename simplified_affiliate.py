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
    """Update user's PayPal email address with improved AJAX handling and error reporting"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User
    
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Please login to update your PayPal email'}), 401
            flash('Please login to update your PayPal email', 'warning')
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        
        # Handle both AJAX and traditional form submissions
        if request.is_json:
            data = request.get_json()
            paypal_email = data.get('paypal_email', '').strip() if data else ''
        else:
            paypal_email = request.form.get('paypal_email', '').strip()
        
        # Validate the email
        if not paypal_email or '@' not in paypal_email:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Please enter a valid PayPal email address'}), 400
            flash('Please enter a valid PayPal email address', 'error')
            return redirect(url_for('billing.account_management'))
        
        # Update user's PayPal email
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User not found for ID {user_id}")
            if request.is_json:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            flash('User not found', 'error')
            return redirect(url_for('billing.account_management'))
        
        # Log the change for debugging
        logger.info(f"Updating PayPal email for user {user_id} from '{user.paypal_email}' to '{paypal_email}'")
        
        # Only update if it's different to avoid unnecessary database operations
        if user.paypal_email != paypal_email:
            user.paypal_email = paypal_email
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Your PayPal email has been updated successfully',
                    'new_email': paypal_email
                })
            
            flash('Your PayPal email has been updated successfully', 'success')
        else:
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'No changes needed - PayPal email remains the same',
                    'new_email': paypal_email
                })
            
            flash('No changes needed - PayPal email remains the same', 'info')
            
        if not request.is_json:
            return redirect(url_for('billing.account_management'))
        return jsonify({'success': True, 'message': 'Your PayPal email has been updated successfully', 'new_email': paypal_email})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {str(e)}", exc_info=True)
        
        if request.is_json:
            return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'}), 500
            
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
        
        # Get the existing CSRF protection instance
        # In Flask-WTF, the CSRFProtect instance is stored in app.extensions['csrf']
        # We add detailed logging to track the CSRF setup for debugging
        csrf = app.extensions.get('csrf', None)
        if csrf:
            # Exempt our route from CSRF protection using the existing instance
            csrf.exempt('simplified_affiliate.update_paypal_email')
            logger.info("CSRF exemption successfully applied to simplified_affiliate.update_paypal_email")
        else:
            logger.warning("Could not find CSRF extension in app.extensions. CSRF exemption not applied!")
        
        logger.info("Simplified Affiliate blueprint registered successfully")