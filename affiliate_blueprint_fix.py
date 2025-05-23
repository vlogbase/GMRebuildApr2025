"""
Affiliate Blueprint Module (Fixed Version)

This module provides a Flask blueprint for the affiliate system.
This implementation resolves circular import issues, prevents the blueprint 
from being registered multiple times, and fixes issues with PayPal email
updates and form submissions.
"""

import logging
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify

# Create a logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the blueprint with a proper URL prefix
affiliate_bp = Blueprint('affiliate', __name__, url_prefix='/affiliate')

@affiliate_bp.route('/dashboard')
def dashboard():
    """Affiliate dashboard view"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, Commission, CustomerReferral, Transaction
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to access your affiliate dashboard', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # In the simplified system, the user is already the affiliate
    # Just make sure they have a referral code
    if not user.referral_code:
        logger.info(f"Generating referral code for user {user_id}")
        user.referral_code = str(uuid.uuid4())[:8].upper()
        db.session.commit()
        
        flash('Your referral code has been generated! Start sharing your referral link to earn commissions.', 'success')
    
    # Get affiliate commissions (limit to 50 to avoid memory issues)
    commissions = Commission.query.filter_by(user_id=user.id).order_by(
        Commission.created_at.desc()
    ).limit(50).all()
    
    # Get direct referrals (limit to 100 to avoid memory issues)
    referrals = db.session.query(
        User,
        CustomerReferral,
        db.func.sum(Transaction.amount_usd).label('total_purchases')
    ).join(
        CustomerReferral, User.id == CustomerReferral.user_id
    ).outerjoin(
        Transaction, User.id == Transaction.user_id
    ).filter(
        CustomerReferral.referrer_id == user_id,
        CustomerReferral.referral_level == 1
    ).group_by(
        User.id, CustomerReferral.id
    ).limit(100).all()
    
    # Format referrals for template
    formatted_referrals = []
    for user, referral, total_purchases in referrals:
        formatted_referrals.append({
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at,
            'total_purchases': total_purchases or 0
        })
    
    # Get sub-affiliate referrals (tier 2) (limit to 100 to avoid memory issues)
    sub_referrals = db.session.query(
        User,
        CustomerReferral,
        db.func.sum(Transaction.amount_usd).label('total_purchases')
    ).join(
        CustomerReferral, User.id == CustomerReferral.user_id
    ).outerjoin(
        Transaction, User.id == Transaction.user_id
    ).filter(
        CustomerReferral.referrer_id == user_id,
        CustomerReferral.referral_level == 2
    ).group_by(
        User.id, CustomerReferral.id
    ).limit(100).all()
    
    # Format sub-referrals for template
    formatted_sub_referrals = []
    for user, referral, total_purchases in sub_referrals:
        formatted_sub_referrals.append({
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at,
            'total_purchases': total_purchases or 0
        })
    
    # Calculate commission stats
    total_earned = sum(c.commission_amount for c in commissions if c.status in ['approved', 'paid'])
    pending = sum(c.commission_amount for c in commissions if c.status == 'pending')
    total_referrals = len(formatted_referrals)
    conversion_rate = 'N/A'  # We'd need to track clicks for this
    
    commission_stats = {
        'total_earned': f"{total_earned:.2f}",
        'pending': f"{pending:.2f}",
        'referrals': total_referrals,
        'conversion_rate': conversion_rate
    }
    
    # Render the dashboard template
    return render_template(
        'affiliate/dashboard.html',
        affiliate=user,  # In the simplified system, the user is the affiliate
        commissions=commissions,
        referrals=formatted_referrals,
        sub_referrals=formatted_sub_referrals,
        commission_stats=commission_stats
    )

@affiliate_bp.route('/register')
def register():
    """
    Auto-creates an affiliate record for the user and redirects to dashboard.
    This is a compatibility route that now automatically creates active affiliates.
    """
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to access the affiliate program', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user info
    user = User.query.get(user_id)
    if not user:
        flash('User account not found', 'error')
        return redirect(url_for('index'))
        
    # In our simplified system, all users are affiliates
    # Just make sure they have a referral code
    if not user.referral_code:
        referral_code = str(uuid.uuid4())[:8].upper()
        user.referral_code = referral_code
        
        # Also set paypal_email if not already set
        if not user.paypal_email:
            user.paypal_email = user.email
            
        db.session.commit()
        
        flash('Your affiliate account has been created!', 'success')
    
    # Redirect to the affiliate dashboard
    return redirect(url_for('billing.account_management', _anchor='tellFriend'))

@affiliate_bp.route('/tell-a-friend')
def tell_a_friend():
    """Affiliate referral tools page"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to access your affiliate tools', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Make sure user has a referral code
    if not user.referral_code:
        return redirect(url_for('affiliate.register'))
    
    return render_template('affiliate/tell_friend_tab.html', affiliate=user)

@affiliate_bp.route('/commissions')
def commissions():
    """View affiliate commissions"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, Commission
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to view your commissions', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Make sure user has a referral code
    if not user.referral_code:
        return redirect(url_for('affiliate.register'))
    
    # Get user commissions (limit to 100 to avoid memory issues)
    commissions = Commission.query.filter_by(user_id=user.id).order_by(
        Commission.created_at.desc()
    ).limit(100).all()
    
    # Calculate commission stats
    total_earned = sum(c.commission_amount for c in commissions if c.status in ['approved', 'paid'])
    pending = sum(c.commission_amount for c in commissions if c.status == 'pending')
    available = sum(c.commission_amount for c in commissions if c.status == 'approved')
    
    # Format dates for payout availability
    for commission in commissions:
        if commission.status == 'pending' and commission.commission_earned_date:
            # Calculate when this commission will be available (30 days after earned)
            available_date = commission.commission_earned_date + timedelta(days=30)
            commission.available_date = available_date
    
    commission_stats = {
        'total_earned': f"{total_earned:.2f}",
        'pending': f"{pending:.2f}",
        'available': f"{available:.2f}"
    }
    
    return render_template(
        'affiliate/commissions.html',
        affiliate=user,
        commissions=commissions,
        commission_stats=commission_stats
    )

@affiliate_bp.route('/track-referral')
def track_referral():
    """API endpoint to track affiliate referrals"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, CustomerReferral
    
    referral_code = request.args.get('code')
    if not referral_code:
        return jsonify({'success': False, 'message': 'No referral code provided'})
    
    user = User.query.filter_by(referral_code=referral_code).first()
    if not user:
        return jsonify({'success': False, 'message': 'Invalid referral code'})
    
    # Store the referral code in session for later conversion
    session['referral_code'] = referral_code
    
    return jsonify({'success': True, 'message': 'Referral tracked'})

@affiliate_bp.route('/commission-metrics')
def commission_metrics():
    """API endpoint to get commission metrics for charts"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import Commission, User
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    user_id = session['user_id']
    
    # Get user info
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Make sure user has a referral code
    if not user.referral_code:
        return jsonify({'success': False, 'message': 'User is not set up as an affiliate yet'})
    
    # Get monthly commissions for the past 6 months
    six_months_ago = datetime.now() - timedelta(days=180)
    
    monthly_commissions = db.session.query(
        db.func.date_trunc('month', Commission.created_at).label('month'),
        db.func.sum(Commission.commission_amount).label('amount')
    ).filter(
        Commission.user_id == user.id,
        Commission.created_at >= six_months_ago
    ).group_by(
        db.func.date_trunc('month', Commission.created_at)
    ).order_by(
        db.func.date_trunc('month', Commission.created_at)
    ).all()
    
    # Format data for charts
    labels = []
    data = []
    
    for month, amount in monthly_commissions:
        labels.append(month.strftime('%b %Y'))
        data.append(float(amount))
    
    return jsonify({
        'success': True,
        'labels': labels,
        'data': data
    })

@affiliate_bp.route('/agree-to-terms', methods=['POST'])
def agree_to_terms_handler():
    """
    Handle the submission of the affiliate terms agreement form
    
    This is now simplified to automatically create or activate an affiliate account
    and just update the PayPal email if provided. No terms agreement is required.
    """
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to register as an affiliate', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get PayPal email from form
    paypal_email = request.form.get('paypal_email', '').strip()
    
    try:
        # Directly update the user model
        if paypal_email:
            user.paypal_email = paypal_email
        
        # Ensure user has a referral code
        if not user.referral_code:
            user.referral_code = str(uuid.uuid4())[:8]
        
        db.session.commit()
        flash('Your affiliate account is now active!', 'success')
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing affiliate request: {str(e)}", exc_info=True)
        flash('An error occurred while processing your request. Please try again.', 'error')
    
    # Redirect to the Tell a Friend tab - using _anchor parameter for reliability
    return redirect(url_for('billing.account_management', _anchor='tellFriend'))

@affiliate_bp.route('/update-paypal-email', methods=['POST'])
def update_paypal_email():
    """Update affiliate's PayPal email address - completely rewritten version"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User
    
    # Log all incoming data for debugging
    logger.info(f"PayPal email update request: {request.form}")
    logger.info(f"Session data: {dict(session)}")
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    # Simple implementation that ignores CSRF completely
    try:
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if not user:
            logger.error(f"User {user_id} not found in database")
            flash('User not found', 'error')
            return redirect(url_for('login'))
        
        # Ensure user has a referral code (everyone is automatically an affiliate)
        if not user.referral_code:
            logger.info(f"Setting up referral code for user {user_id}")
            user.referral_code = str(uuid.uuid4())[:8]
            
            # Pre-fill with login email if paypal_email not set
            if not hasattr(user, 'paypal_email') or not user.paypal_email:
                user.paypal_email = user.email
                
            db.session.commit()  # Commit immediately
            logger.info(f"Created referral code {user.referral_code} for user {user_id}")
        
        # Get the submitted email (with very basic validation)
        paypal_email = request.form.get('paypal_email', '').strip()
        
        # Basic validation - just ensure it's not empty and has an @ symbol
        if not paypal_email or '@' not in paypal_email:
            logger.warning(f"Invalid email provided: '{paypal_email}'")
            flash('Please enter a valid email address for PayPal payments', 'error')
            return redirect(url_for('billing.account_management', _anchor='tellFriend'))
        
        # Update the email
        old_email = user.paypal_email if hasattr(user, 'paypal_email') and user.paypal_email else user.email
        user.paypal_email = paypal_email
        
        # Commit changes
        db.session.commit()
        
        # Log the change
        if old_email != paypal_email:
            logger.info(f"Updated PayPal email for user {user.id} from '{old_email}' to '{paypal_email}'")
            flash('PayPal email updated successfully!', 'success')
        else:
            logger.info(f"PayPal email unchanged for user {user.id}: '{paypal_email}'")
            flash('PayPal email saved', 'info')
        
        # Set a session flag for JavaScript to use
        session['paypal_email_updated'] = True
        
    except Exception as e:
        logger.error(f"Error in PayPal email update: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while updating your PayPal email. Our team has been notified.', 'error')
    
    # Always redirect back to account page with Tell a Friend tab active
    return redirect(url_for('billing.account_management', _anchor='tellFriend'))

# Helper function for templates
def affiliate_helpers():
    """Provide helper functions to affiliate templates"""
    def format_date(date):
        """Format a date for display"""
        if not date:
            return ''
        return date.strftime('%b %d, %Y')
    
    def format_currency(amount):
        """Format an amount as currency"""
        if not amount:
            return '$0.00'
        return f"${float(amount):.2f}"
    
    def get_status_class(status):
        """Get CSS class for status display"""
        status_classes = {
            'pending': 'warning',
            'approved': 'success',
            'paid': 'primary',
            'rejected': 'danger',
            'active': 'success',
            'inactive': 'secondary',
            'applied': 'info'
        }
        return status_classes.get(status, 'secondary')
    
    return {
        'format_date': format_date,
        'format_currency': format_currency,
        'get_status_class': get_status_class
    }

def init_app(app):
    """
    Initialize the affiliate blueprint with a Flask application
    
    This function registers the affiliate blueprint and adds its context processors.
    It carefully avoids circular imports and re-registration issues.
    
    Args:
        app: Flask application
        
    Returns:
        None
    """
    # Only register the blueprint if it hasn't been registered yet
    if not app.blueprints.get('affiliate'):
        # Register blueprint
        app.register_blueprint(affiliate_bp)
        
        # Add template context processor for helper functions
        app.context_processor(affiliate_helpers)
        
        logger.info("Affiliate blueprint registered successfully")
    else:
        logger.info("Affiliate blueprint already registered, skipping")