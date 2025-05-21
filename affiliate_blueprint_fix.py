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
    from models import User, Affiliate, Commission, CustomerReferral, Transaction
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to access your affiliate dashboard', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get user's affiliate info by matching user ID first
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    # If not found by user_id, try by email as a fallback
    if not affiliate:
        affiliate = Affiliate.query.filter_by(email=user.email).first()
    
    # If no affiliate record exists, create one automatically with active status
    if not affiliate:
        logger.info(f"Creating affiliate record for user {user_id}")
        referral_code = str(uuid.uuid4())[:8]
        
        affiliate = Affiliate(
            user_id=user_id,
            name=user.username,
            email=user.email,
            referral_code=referral_code,
            status='active',
            terms_agreed_at=datetime.now()
        )
        db.session.add(affiliate)
        db.session.commit()
        
        flash('Your affiliate account has been created! Start sharing your referral link to earn commissions.', 'success')
    
    # Get affiliate commissions (limit to 50 to avoid memory issues)
    commissions = Commission.query.filter_by(affiliate_id=affiliate.id).order_by(
        Commission.created_at.desc()
    ).limit(50).all() if affiliate else []
    
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
        affiliate=affiliate,
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
    return redirect(url_for('affiliate.dashboard'))

@affiliate_bp.route('/tell-a-friend')
def tell_a_friend():
    """Affiliate referral tools page"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, Affiliate
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to access your affiliate tools', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get user's affiliate info by matching user ID
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    # If not found by user_id, try by email
    if not affiliate:
        affiliate = Affiliate.query.filter_by(email=user.email).first()
    
    # If no affiliate record exists, redirect to dashboard to auto-create one
    if not affiliate:
        return redirect(url_for('affiliate.dashboard'))
    
    return render_template('affiliate/tell_friend_tab.html', affiliate=affiliate)

@affiliate_bp.route('/commissions')
def commissions():
    """View affiliate commissions"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, Affiliate, Commission
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to view your commissions', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get user's affiliate info by matching user ID
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    # If not found by user_id, try by email
    if not affiliate:
        affiliate = Affiliate.query.filter_by(email=user.email).first()
    
    # If no affiliate record exists, redirect to dashboard to auto-create one
    if not affiliate:
        return redirect(url_for('affiliate.dashboard'))
    
    # Get affiliate commissions (limit to 100 to avoid memory issues)
    commissions = Commission.query.filter_by(affiliate_id=affiliate.id).order_by(
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
        affiliate=affiliate,
        commissions=commissions,
        commission_stats=commission_stats
    )

@affiliate_bp.route('/track-referral')
def track_referral():
    """API endpoint to track affiliate referrals"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import Affiliate, CustomerReferral
    
    referral_code = request.args.get('code')
    if not referral_code:
        return jsonify({'success': False, 'message': 'No referral code provided'})
    
    affiliate = Affiliate.query.filter_by(referral_code=referral_code).first()
    if not affiliate:
        return jsonify({'success': False, 'message': 'Invalid referral code'})
    
    # Store the referral code in session for later conversion
    session['referral_code'] = referral_code
    
    return jsonify({'success': True, 'message': 'Referral tracked'})

@affiliate_bp.route('/commission-metrics')
def commission_metrics():
    """API endpoint to get commission metrics for charts"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import Affiliate, Commission, User
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    user_id = session['user_id']
    
    # Get user's affiliate info by matching user ID
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    # If not found by user_id, try by email
    if not affiliate and User.query.get(user_id):
        user = User.query.get(user_id)
        affiliate = Affiliate.query.filter_by(email=user.email).first()
    
    if not affiliate:
        return jsonify({'success': False, 'message': 'Affiliate not found'})
    
    # Get monthly commissions for the past 6 months
    six_months_ago = datetime.now() - timedelta(days=180)
    
    monthly_commissions = db.session.query(
        db.func.date_trunc('month', Commission.created_at).label('month'),
        db.func.sum(Commission.commission_amount).label('amount')
    ).filter(
        Commission.affiliate_id == affiliate.id,
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
    from models import User, Affiliate
    
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
        # Check if affiliate record already exists
        affiliate = Affiliate.query.filter_by(user_id=user_id).first()
        
        if not affiliate:
            # If not found by user_id, try by email
            affiliate = Affiliate.query.filter_by(email=user.email).first()
        
        if affiliate:
            # Update existing affiliate
            if paypal_email:
                affiliate.paypal_email = paypal_email
            
            affiliate.status = 'active'
            affiliate.terms_agreed_at = datetime.now()
            
            if hasattr(affiliate, 'updated_at'):
                affiliate.updated_at = datetime.now()
        else:
            # Create new affiliate
            referral_code = str(uuid.uuid4())[:8]
            
            # Use provided paypal_email if available, otherwise default to user's email
            affiliate_paypal_email = paypal_email if paypal_email else user.email
            
            affiliate = Affiliate(
                user_id=user_id,
                name=user.username,
                email=user.email,
                paypal_email=affiliate_paypal_email,
                referral_code=referral_code,
                status='active',
                terms_agreed_at=datetime.now()
            )
            db.session.add(affiliate)
        
        db.session.commit()
        flash('Your affiliate account is now active!', 'success')
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing affiliate request: {str(e)}", exc_info=True)
        flash('An error occurred while processing your request. Please try again.', 'error')
    
    # Redirect to the Tell a Friend tab
    return redirect(url_for('billing.account_management') + '#tellFriend')

@affiliate_bp.route('/update-paypal-email', methods=['POST'])
def update_paypal_email():
    """Update affiliate's PayPal email address"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, Affiliate
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get user's affiliate info by matching user ID
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    # If not found by user_id, try by email
    if not affiliate:
        affiliate = Affiliate.query.filter_by(email=user.email).first()
    
    if not affiliate:
        # If no affiliate is found, create one automatically
        logger.info(f"Creating affiliate record for user {user_id} during PayPal email update")
        referral_code = str(uuid.uuid4())[:8]
        
        affiliate = Affiliate(
            user_id=user_id,
            name=user.username,
            email=user.email,
            paypal_email=user.email,  # Pre-fill with login email for convenience
            referral_code=referral_code,
            status='active',
            terms_agreed_at=datetime.now()
        )
        db.session.add(affiliate)
        
    # Get and validate new email
    paypal_email = request.form.get('paypal_email', '').strip()
    
    if not paypal_email:
        flash('PayPal email is required', 'error')
        return redirect(url_for('billing.account_management') + '#tellFriend')
    
    # Update the affiliate's PayPal email
    try:
        # Log the update for debugging
        logger.info(f"Updating PayPal email for affiliate {affiliate.id} to {paypal_email}")
        
        affiliate.paypal_email = paypal_email
        
        # Update timestamp
        if hasattr(affiliate, 'updated_at'):
            affiliate.updated_at = datetime.now()
            
        db.session.commit()
        flash('PayPal email updated successfully', 'success')
        logger.info(f"Successfully updated PayPal email for affiliate {affiliate.id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {str(e)}", exc_info=True)
        flash('An error occurred while updating your PayPal email. Please try again.', 'error')
    
    # Redirect back to account management page, specifically the Tell a Friend tab
    return redirect(url_for('billing.account_management') + '#tellFriend')

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