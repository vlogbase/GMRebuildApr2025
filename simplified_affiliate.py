"""
Simplified Affiliate Blueprint - Uses the User model directly for affiliate functionality
"""
import os
import logging
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy import desc, func

from app import db
from models import User, Commission, CustomerReferral, CommissionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
simplified_affiliate_bp = Blueprint('simplified_affiliate', __name__, url_prefix='/affiliate')

@simplified_affiliate_bp.route('/')
@login_required
def index():
    """
    Main affiliate route - always shows the dashboard directly
    No need to check status as every user is automatically an affiliate
    """
    # Simply redirect to the dashboard
    logger.info(f"User {current_user.id} accessed main affiliate route, showing dashboard")
    return redirect(url_for('simplified_affiliate.dashboard'))

@simplified_affiliate_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Show affiliate dashboard with stats and referral data
    """
    # Ensure user has a referral code
    if not current_user.referral_code:
        current_user.generate_referral_code()
        db.session.commit()
        logger.info(f"Generated referral code {current_user.referral_code} for user {current_user.id}")
    
    # Get commission statistics
    commission_stats = get_commission_stats(current_user.id)
    
    # Get referrals (users who were referred by this user)
    referrals = User.query.filter_by(referred_by_user_id=current_user.id).all()
    
    # Get commissions for this user
    commissions = Commission.query.filter_by(user_id=current_user.id).order_by(desc(Commission.created_at)).limit(10).all()
    
    # Get sub-referrals (Tier 2 - users referred by people this user referred)
    sub_referrals = []
    for referral in referrals:
        sub_refs = User.query.filter_by(referred_by_user_id=referral.id).all()
        sub_referrals.extend(sub_refs)
    
    return render_template(
        'affiliate/dashboard.html',
        commission_stats=commission_stats,
        referrals=referrals,
        sub_referrals=sub_referrals,
        commissions=commissions
    )

@simplified_affiliate_bp.route('/update_paypal_email', methods=['POST'])
@login_required
def update_paypal_email():
    """
    Update PayPal email for affiliate payouts
    """
    try:
        # Get form data
        paypal_email = request.form.get('paypal_email', '').strip()
        
        if not paypal_email:
            flash('Please provide a PayPal email address', 'error')
            return redirect(url_for('billing.account_management', _anchor='tellFriend'))
        
        # Log the update attempt
        logger.info(f"Updating PayPal email for user {current_user.id} from '{current_user.paypal_email or 'None'}' to '{paypal_email}'")
        
        # Update the user's PayPal email
        old_email = current_user.paypal_email or "None"
        
        # Update the PayPal email
        current_user.update_paypal_email(paypal_email)
        
        # Generate referral code if needed
        if not current_user.referral_code:
            current_user.generate_referral_code()
            logger.info(f"Generated new referral code {current_user.referral_code} for user {current_user.id}")
        
        # Commit changes
        db.session.commit()
        
        # Use a specific success message
        if old_email != paypal_email:
            flash(f'PayPal email updated successfully from {old_email} to {paypal_email}!', 'success')
        else:
            flash('PayPal email saved (no change detected)', 'info')
            
        logger.info(f"Successfully updated PayPal email in database")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {str(e)}", exc_info=True)
        flash('An error occurred while updating your PayPal email. Please try again.', 'error')
    
    return redirect(url_for('billing.account_management', _anchor='tellFriend'))

@simplified_affiliate_bp.route('/referral/<code>')
def track_referral(code):
    """
    Track a referral from a shared link
    """
    try:
        # Store the referral code in session
        session['referral_code'] = code
        logger.info(f"Stored referral code in session: {code}")
        
        # Get the referring user
        referring_user = User.query.filter_by(referral_code=code).first()
        
        if not referring_user:
            logger.warning(f"Invalid referral code: {code}")
            flash('Invalid referral code', 'warning')
            return redirect(url_for('index'))
        
        # If user is already logged in, track the referral immediately
        if current_user.is_authenticated and current_user.id != referring_user.id:
            # Don't allow self-referrals
            if not current_user.referred_by_user_id:
                current_user.referred_by_user_id = referring_user.id
                db.session.commit()
                
                # Create a customer referral record
                CustomerReferral.track_referral(code, current_user)
                
                logger.info(f"User {current_user.id} was referred by user {referring_user.id}")
                flash(f'You were successfully referred by {referring_user.username}!', 'success')
        
        # Redirect to the main page or a specific landing page
        redirect_url = request.args.get('redirect', url_for('index'))
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"Error tracking referral: {str(e)}", exc_info=True)
        return redirect(url_for('index'))

def get_commission_stats(user_id):
    """
    Get commission statistics for a user
    
    Args:
        user_id (int): User ID to get statistics for
        
    Returns:
        dict: Commission statistics including total earned, pending, and referrals
    """
    try:
        # Get total earned
        total_earned = db.session.query(func.sum(Commission.commission_amount)).\
            filter(Commission.user_id == user_id).\
            filter(Commission.status.in_([CommissionStatus.APPROVED.value, CommissionStatus.PAID.value])).\
            scalar() or 0
            
        # Get pending amount
        pending = db.session.query(func.sum(Commission.commission_amount)).\
            filter(Commission.user_id == user_id).\
            filter(Commission.status == CommissionStatus.HELD.value).\
            scalar() or 0
            
        # Get total referrals
        referrals = User.query.filter_by(referred_by_user_id=user_id).count()
        
        # Calculate conversion rate if there are referrals
        conversion_rate = "N/A"
        if referrals > 0:
            users_with_purchases = db.session.query(func.count(func.distinct(Commission.triggering_transaction_id))).\
                filter(Commission.user_id == user_id).\
                scalar() or 0
                
            if users_with_purchases > 0:
                conversion_rate = round((users_with_purchases / referrals) * 100, 2)
        
        return {
            'total_earned': round(total_earned, 2),
            'pending': round(pending, 2),
            'referrals': referrals,
            'conversion_rate': conversion_rate
        }
    except Exception as e:
        logger.error(f"Error getting commission stats: {str(e)}", exc_info=True)
        return {
            'total_earned': 0,
            'pending': 0,
            'referrals': 0,
            'conversion_rate': "N/A"
        }