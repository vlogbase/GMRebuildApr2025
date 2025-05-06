"""
Affiliate System Module for GloriaMundo Chatbot

This module handles affiliate program management including:
1. Affiliate registration and management
2. Referral tracking with cookies
3. Commission calculation on Stripe payments
4. PayPal payouts for affiliates

It implements a two-tier affiliate structure where:
- Level 1 (L1) affiliates get 10% commission on referred customer purchases
- Level 2 (L2) affiliates get 5% commission on purchases from customers referred by their referred affiliates
"""

import logging
import secrets
from datetime import datetime, timedelta
import json
import os

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.exceptions import Forbidden

from app import db
from models import Affiliate, CustomerReferral, Commission, AffiliateStatus, CommissionStatus, Transaction, User

from paypal_payouts import process_payout_batch, get_payout_batch_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
affiliate_bp = Blueprint('affiliate', __name__, url_prefix='/affiliate')

# Configuration
REFERRAL_COOKIE_NAME = 'referral_code'
REFERRAL_COOKIE_DAYS = 30  # Cookie lasts for 30 days
COMMISSION_HOLDING_DAYS = 30  # Hold commissions for 30 days before paying out
L1_COMMISSION_RATE = 0.10  # 10% for direct referral
L2_COMMISSION_RATE = 0.05  # 5% for second-tier referral

def admin_required(f):
    """Decorator to require admin access"""
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def generate_referral_code():
    """Generate a unique referral code"""
    while True:
        code = secrets.token_urlsafe(8)[:8]
        if not Affiliate.query.filter_by(referral_code=code).first():
            return code

def set_referral_cookie(response, referral_code):
    """Set the referral cookie"""
    expires = datetime.utcnow() + timedelta(days=REFERRAL_COOKIE_DAYS)
    response.set_cookie(
        REFERRAL_COOKIE_NAME, 
        referral_code,
        expires=expires,
        httponly=True,
        samesite='Lax',
        secure=request.is_secure
    )
    return response

def get_gbp_amount(usd_amount):
    """
    Convert USD amount to GBP
    
    In a production environment, this would use a currency conversion API.
    For now, we'll use a fixed exchange rate for simplicity.
    """
    # Fixed exchange rate (1 USD = 0.78 GBP) - this should be dynamically updated in production
    exchange_rate = 0.78
    return round(float(usd_amount) * exchange_rate, 2)

@affiliate_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Affiliate registration page"""
    # Check if user is already an affiliate
    existing_affiliate = Affiliate.query.filter_by(email=current_user.email).first()
    if existing_affiliate:
        flash('You are already registered as an affiliate.', 'info')
        return redirect(url_for('affiliate.dashboard'))
    
    # Check for referral code
    referral_code = request.cookies.get(REFERRAL_COOKIE_NAME)
    referring_affiliate = None
    
    if referral_code:
        referring_affiliate = Affiliate.query.filter_by(referral_code=referral_code).first()
    
    if request.method == 'POST':
        paypal_email = request.form.get('paypal_email')
        
        # Simple validation
        if not paypal_email or '@' not in paypal_email:
            flash('Please enter a valid PayPal email address.', 'danger')
            return render_template('affiliate/register.html', referring_affiliate=referring_affiliate)
        
        # Create new affiliate
        new_affiliate = Affiliate(
            name=current_user.username,
            email=current_user.email,
            paypal_email=paypal_email,
            status=AffiliateStatus.ACTIVE.value
        )
        
        # Generate unique referral code
        new_affiliate.referral_code = generate_referral_code()
        
        # Set referring affiliate if applicable
        if referring_affiliate:
            new_affiliate.referred_by_affiliate_id = referring_affiliate.id
        
        db.session.add(new_affiliate)
        
        try:
            db.session.commit()
            flash('You have successfully registered as an affiliate!', 'success')
            return redirect(url_for('affiliate.dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering affiliate: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('affiliate/register.html', referring_affiliate=referring_affiliate)

@affiliate_bp.route('/dashboard')
@login_required
def dashboard():
    """Affiliate dashboard page"""
    # Check if user is an affiliate
    affiliate = Affiliate.query.filter_by(email=current_user.email).first()
    if not affiliate:
        flash('You are not registered as an affiliate yet.', 'info')
        return redirect(url_for('affiliate.register'))
    
    # Get commission data
    commissions = Commission.query.filter_by(affiliate_id=affiliate.id).order_by(Commission.created_at.desc()).all()
    
    # Calculate totals by status
    pending_amount = sum(float(c.commission_amount) for c in commissions if c.status == CommissionStatus.HELD.value)
    available_amount = sum(float(c.commission_amount) for c in commissions if c.status == CommissionStatus.APPROVED.value)
    paid_amount = sum(float(c.commission_amount) for c in commissions if c.status == CommissionStatus.PAID.value)
    
    # Get referral data
    customer_referrals = CustomerReferral.query.filter_by(affiliate_id=affiliate.id).count()
    referred_affiliates = Affiliate.query.filter_by(referred_by_affiliate_id=affiliate.id).count()
    
    # Get sales data
    referred_user_ids = [r.customer_user_id for r in CustomerReferral.query.filter_by(affiliate_id=affiliate.id).all()]
    total_sales = 0
    if referred_user_ids:
        total_sales = db.session.query(func.sum(Transaction.amount_usd)).filter(
            Transaction.user_id.in_(referred_user_ids),
            Transaction.status == 'completed'
        ).scalar() or 0
    
    return render_template(
        'affiliate/dashboard.html',
        affiliate=affiliate,
        commissions=commissions,
        pending_amount=pending_amount,
        available_amount=available_amount,
        paid_amount=paid_amount,
        customer_referrals=customer_referrals,
        referred_affiliates=referred_affiliates,
        total_sales=total_sales,
        commission_rate_l1=L1_COMMISSION_RATE * 100,  # Convert to percentage
        commission_rate_l2=L2_COMMISSION_RATE * 100  # Convert to percentage
    )

@affiliate_bp.route('/referral-link')
@login_required
def referral_link():
    """Generate referral link for affiliate"""
    # Check if user is an affiliate
    affiliate = Affiliate.query.filter_by(email=current_user.email).first()
    if not affiliate:
        flash('You are not registered as an affiliate yet.', 'info')
        return redirect(url_for('affiliate.register'))
    
    # Construct base URL (handles both HTTP and HTTPS)
    base_url = request.host_url.rstrip('/')
    
    # Construct referral URL
    referral_url = f"{base_url}?ref={affiliate.referral_code}"
    
    return render_template('affiliate/referral_link.html', affiliate=affiliate, referral_url=referral_url)

@affiliate_bp.route('/admin')
@admin_required
def admin():
    """Admin dashboard for managing affiliates and commissions"""
    # Get all affiliates
    affiliates = Affiliate.query.order_by(Affiliate.created_at.desc()).all()
    
    # Get commissions eligible for payout (approved status)
    eligible_commissions = Commission.query.filter_by(status=CommissionStatus.APPROVED.value).all()
    
    # Group by affiliate for easier processing
    commissions_by_affiliate = {}
    for commission in eligible_commissions:
        if commission.affiliate_id not in commissions_by_affiliate:
            commissions_by_affiliate[commission.affiliate_id] = {
                'amount': 0,
                'commission_ids': []
            }
        
        commissions_by_affiliate[commission.affiliate_id]['amount'] += float(commission.commission_amount)
        commissions_by_affiliate[commission.affiliate_id]['commission_ids'].append(commission.id)
    
    # Get affiliates with their commissions
    affiliates_with_commissions = []
    for affiliate in affiliates:
        commission_data = commissions_by_affiliate.get(affiliate.id, {'amount': 0, 'commission_ids': []})
        affiliates_with_commissions.append({
            'affiliate': affiliate,
            'commissions_amount': commission_data['amount'],
            'commission_ids': commission_data['commission_ids'],
            'referral_count': CustomerReferral.query.filter_by(affiliate_id=affiliate.id).count()
        })
    
    return render_template('affiliate/admin.html', affiliates=affiliates_with_commissions)

@affiliate_bp.route('/process-commissions', methods=['POST'])
@admin_required
def process_commissions():
    """Process selected commissions for payout"""
    # Get selected affiliate IDs
    selected_affiliate_ids = request.form.getlist('affiliate_id')
    
    if not selected_affiliate_ids:
        flash('No affiliates selected for payout.', 'warning')
        return redirect(url_for('affiliate.admin'))
    
    # Prepare payout data
    payout_data = {}
    for affiliate_id in selected_affiliate_ids:
        # Get affiliate and their eligible commissions
        affiliate = Affiliate.query.get(affiliate_id)
        if not affiliate:
            continue
        
        # Verify PayPal email
        if not affiliate.paypal_email:
            flash(f'Affiliate {affiliate.name} does not have a PayPal email set.', 'danger')
            continue
        
        # Get approved commissions
        commissions = Commission.query.filter_by(
            affiliate_id=affiliate.id,
            status=CommissionStatus.APPROVED.value
        ).all()
        
        if not commissions:
            continue
        
        # Calculate total amount
        total_amount = sum(float(commission.commission_amount) for commission in commissions)
        
        # Add to payout data
        payout_data[int(affiliate_id)] = {
            'paypal_email': affiliate.paypal_email,
            'amount': total_amount,
            'commission_ids': [commission.id for commission in commissions]
        }
    
    if not payout_data:
        flash('No eligible commissions found for payout.', 'warning')
        return redirect(url_for('affiliate.admin'))
    
    # Process payout with PayPal
    result = process_payout_batch(payout_data)
    
    if result.get('success'):
        # Update commission statuses
        batch_id = result.get('batch_id')
        commission_map = result.get('commission_map', {})
        for item_result in result.get('item_results', []):
            commission_id = item_result.get('commission_id')
            if commission_id:
                commission = Commission.query.get(commission_id)
                if commission:
                    commission.status = CommissionStatus.PAID.value
                    commission.payout_batch_id = batch_id
        
        try:
            db.session.commit()
            flash(f'Successfully processed payouts. Batch ID: {batch_id}', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating commission statuses: {e}")
            flash('Payouts were processed but there was an error updating commission statuses.', 'warning')
    else:
        error_message = result.get('error', 'Unknown error')
        flash(f'Error processing payouts: {error_message}', 'danger')
    
    return redirect(url_for('affiliate.admin'))

@affiliate_bp.route('/update-paypal', methods=['POST'])
@login_required
def update_paypal():
    """Update affiliate PayPal email"""
    # Check if user is an affiliate
    affiliate = Affiliate.query.filter_by(email=current_user.email).first()
    if not affiliate:
        flash('You are not registered as an affiliate yet.', 'info')
        return redirect(url_for('affiliate.register'))
    
    paypal_email = request.form.get('paypal_email')
    
    # Simple validation
    if not paypal_email or '@' not in paypal_email:
        flash('Please enter a valid PayPal email address.', 'danger')
        return redirect(url_for('affiliate.dashboard'))
    
    # Update PayPal email
    affiliate.paypal_email = paypal_email
    affiliate.paypal_email_verified_at = None  # Reset verification status
    
    try:
        db.session.commit()
        flash('Your PayPal email has been updated.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {e}")
        flash('An error occurred while updating your PayPal email.', 'danger')
    
    return redirect(url_for('affiliate.dashboard'))

@affiliate_bp.route('/check-payout-status/<batch_id>')
@admin_required
def check_payout_status(batch_id):
    """Check the status of a payout batch"""
    # Get commissions for this batch
    commissions = Commission.query.filter_by(payout_batch_id=batch_id).all()
    
    # Create mapping of PayPal sender_item_id to commission_id
    commission_map = {}
    for commission in commissions:
        # Reconstruct sender_item_id format used in process_payout_batch
        timestamp = commission.updated_at.strftime('%Y%m%d%H%M%S')
        sender_item_id = f"AFFCOM_{commission.id}_{timestamp}"
        commission_map[sender_item_id] = commission.id
    
    # Get status from PayPal
    result = get_payout_batch_status(batch_id, commission_map)
    
    if result.get('success'):
        batch_status = result.get('batch_status')
        items = result.get('items', [])
        
        # Update commission statuses based on item statuses
        for item in items:
            commission_id = item.get('commission_id')
            item_status = item.get('status')
            
            if commission_id and item_status:
                commission = Commission.query.get(commission_id)
                if commission:
                    # Map PayPal status to our status
                    if item_status == 'SUCCESS':
                        commission.status = CommissionStatus.PAID.value
                    elif item_status in ['FAILED', 'RETURNED', 'BLOCKED', 'UNCLAIMED']:
                        commission.status = CommissionStatus.PAYOUT_FAILED.value
        
        try:
            db.session.commit()
            flash(f'Payout status updated. Batch status: {batch_status}', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating commission statuses: {e}")
            flash('There was an error updating commission statuses.', 'danger')
        
        return jsonify(result)
    else:
        error_message = result.get('error', 'Unknown error')
        flash(f'Error checking payout status: {error_message}', 'danger')
        return jsonify(result), 400

@affiliate_bp.route('/toggle-status/<int:affiliate_id>', methods=['POST'])
@admin_required
def toggle_status(affiliate_id):
    """Toggle affiliate status between active and inactive"""
    affiliate = Affiliate.query.get_or_404(affiliate_id)
    
    # Toggle status
    if affiliate.status == AffiliateStatus.ACTIVE.value:
        affiliate.status = AffiliateStatus.INACTIVE.value
        status_message = 'deactivated'
    else:
        affiliate.status = AffiliateStatus.ACTIVE.value
        status_message = 'activated'
    
    try:
        db.session.commit()
        flash(f'Affiliate {affiliate.name} has been {status_message}.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling affiliate status: {e}")
        flash('An error occurred while updating the affiliate status.', 'danger')
    
    return redirect(url_for('affiliate.admin'))

def track_referral():
    """Middleware to track referral codes from URL parameters"""
    referral_code = request.args.get('ref')
    
    if not referral_code:
        return None
    
    # Validate referral code
    affiliate = Affiliate.query.filter_by(referral_code=referral_code, status=AffiliateStatus.ACTIVE.value).first()
    if not affiliate:
        return None
    
    # Set referral cookie
    response = make_response(redirect(request.path))
    set_referral_cookie(response, referral_code)
    
    # Log referral
    logger.info(f"Referral tracked: {referral_code}")
    
    return response

def handle_affiliate_commission(payment_intent_id, customer_user_id, amount_usd):
    """
    Handle affiliate commission for a completed payment
    
    Args:
        payment_intent_id (str): Stripe PaymentIntent ID
        customer_user_id (int): User ID of the customer
        amount_usd (float): Payment amount in USD
    """
    # Check if customer was referred by an affiliate
    customer_referral = CustomerReferral.query.filter_by(customer_user_id=customer_user_id).first()
    
    if not customer_referral:
        logger.info(f"No affiliate referral for user {customer_user_id}")
        return
    
    # Get the L1 affiliate (direct referrer)
    l1_affiliate = Affiliate.query.get(customer_referral.affiliate_id)
    
    if not l1_affiliate or l1_affiliate.status != AffiliateStatus.ACTIVE.value:
        logger.info(f"L1 affiliate {customer_referral.affiliate_id} not active")
        return
    
    # Calculate L1 commission
    l1_commission_amount = get_gbp_amount(amount_usd) * L1_COMMISSION_RATE
    
    # Create L1 commission record
    l1_commission = Commission(
        affiliate_id=l1_affiliate.id,
        triggering_transaction_id=payment_intent_id,
        stripe_payment_status='succeeded',
        purchase_amount_base=get_gbp_amount(amount_usd),
        commission_rate=L1_COMMISSION_RATE,
        commission_amount=l1_commission_amount,
        commission_level=1,
        status=CommissionStatus.HELD.value,
        commission_earned_date=datetime.utcnow(),
        commission_available_date=datetime.utcnow() + timedelta(days=COMMISSION_HOLDING_DAYS)
    )
    
    db.session.add(l1_commission)
    
    # Check for L2 affiliate (if L1 was referred by someone)
    if l1_affiliate.referred_by_affiliate_id:
        l2_affiliate = Affiliate.query.get(l1_affiliate.referred_by_affiliate_id)
        
        if l2_affiliate and l2_affiliate.status == AffiliateStatus.ACTIVE.value:
            # Calculate L2 commission
            l2_commission_amount = get_gbp_amount(amount_usd) * L2_COMMISSION_RATE
            
            # Create L2 commission record
            l2_commission = Commission(
                affiliate_id=l2_affiliate.id,
                triggering_transaction_id=payment_intent_id,
                stripe_payment_status='succeeded',
                purchase_amount_base=get_gbp_amount(amount_usd),
                commission_rate=L2_COMMISSION_RATE,
                commission_amount=l2_commission_amount,
                commission_level=2,
                status=CommissionStatus.HELD.value,
                commission_earned_date=datetime.utcnow(),
                commission_available_date=datetime.utcnow() + timedelta(days=COMMISSION_HOLDING_DAYS)
            )
            
            db.session.add(l2_commission)
    
    try:
        db.session.commit()
        logger.info(f"Commission(s) created for payment {payment_intent_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating affiliate commission: {e}")

def check_referral_on_auth(user_id):
    """
    Check for referral cookie during user signup or login
    
    Args:
        user_id (int): User ID of the authenticated user
    """
    referral_code = request.cookies.get(REFERRAL_COOKIE_NAME)
    
    if not referral_code:
        return
    
    # Check if this user already has a referral record
    existing_referral = CustomerReferral.query.filter_by(customer_user_id=user_id).first()
    if existing_referral:
        logger.info(f"User {user_id} already has a referral record")
        return
    
    # Find the affiliate by referral code
    affiliate = Affiliate.query.filter_by(referral_code=referral_code, status=AffiliateStatus.ACTIVE.value).first()
    if not affiliate:
        logger.warning(f"Invalid referral code in cookie: {referral_code}")
        return
    
    # Check if user is trying to refer themselves
    user = User.query.get(user_id)
    if user and user.email == affiliate.email:
        logger.warning(f"User {user_id} attempted to refer themselves")
        return
    
    # Create customer referral record
    new_referral = CustomerReferral(
        customer_user_id=user_id,
        affiliate_id=affiliate.id
    )
    
    try:
        db.session.add(new_referral)
        db.session.commit()
        logger.info(f"Created referral record: User {user_id} referred by Affiliate {affiliate.id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating customer referral: {e}")