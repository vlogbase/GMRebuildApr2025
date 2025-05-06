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

import os
import logging
import random
import string
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, current_app, session
from flask_login import current_user, login_required
from sqlalchemy import desc, func, and_
from werkzeug.exceptions import Forbidden

from app import db
from models import User
from paypal_payouts import process_payout_batch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import models here to avoid circular imports
from migrations_affiliate import Affiliate, CustomerReferral, Commission, AffiliateStatus, CommissionStatus

# Create blueprint
affiliate_bp = Blueprint('affiliate', __name__, url_prefix='/affiliate')

# Define commission rates
LEVEL_1_COMMISSION_RATE = 0.10  # 10% for direct referrals
LEVEL_2_COMMISSION_RATE = 0.05  # 5% for second-tier referrals

# Commission holding period (days)
COMMISSION_HOLDING_PERIOD = 30  # Days before a commission becomes available for payout

# Set cookie expiration for referrals (30 days)
REFERRAL_COOKIE_EXPIRATION = 30

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Administrator access required", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def generate_referral_code():
    """Generate a unique referral code"""
    # Generate a random 8-character code
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        # Check if code already exists
        existing = Affiliate.query.filter_by(referral_code=code).first()
        if not existing:
            return code

def set_referral_cookie(response, referral_code):
    """Set the referral cookie"""
    # Set secure cookie that lasts for 30 days
    expires = datetime.now() + timedelta(days=REFERRAL_COOKIE_EXPIRATION)
    response.set_cookie(
        'referral_code', 
        referral_code, 
        expires=expires, 
        httponly=True, 
        secure=request.is_secure,
        samesite='Lax'
    )
    return response

def get_gbp_amount(usd_amount):
    """
    Convert USD amount to GBP
    
    In a production environment, this would use a currency conversion API.
    For now, we'll use a fixed exchange rate for simplicity.
    """
    # Fixed exchange rate: 1 USD = 0.78 GBP (example rate)
    exchange_rate = 0.78
    return round(usd_amount * exchange_rate, 4)

@affiliate_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Affiliate registration page"""
    # Check if user is already an affiliate
    existing_affiliate = Affiliate.query.filter_by(email=current_user.email).first()
    if existing_affiliate:
        flash("You are already registered as an affiliate", "info")
        return redirect(url_for('affiliate.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        paypal_email = request.form.get('paypal_email')
        referring_code = request.form.get('referring_code')
        
        # Validate fields
        if not name or not paypal_email:
            flash("All fields are required", "error")
            return render_template('affiliate/register.html')
        
        # Check if referring code exists and is valid
        referred_by_id = None
        if referring_code:
            referring_affiliate = Affiliate.query.filter_by(referral_code=referring_code).first()
            if referring_affiliate:
                if referring_affiliate.email == current_user.email:
                    flash("You cannot refer yourself", "error")
                    return render_template('affiliate/register.html')
                referred_by_id = referring_affiliate.id
            else:
                flash("Invalid referral code", "error")
                return render_template('affiliate/register.html')
        
        # Generate unique referral code
        referral_code = generate_referral_code()
        
        # Create new affiliate
        new_affiliate = Affiliate(
            name=name,
            email=current_user.email,
            paypal_email=paypal_email,
            referral_code=referral_code,
            referred_by_affiliate_id=referred_by_id,
            status=AffiliateStatus.ACTIVE.value
        )
        
        db.session.add(new_affiliate)
        db.session.commit()
        
        flash("You have successfully registered as an affiliate", "success")
        return redirect(url_for('affiliate.dashboard'))
    
    # Check if there's a referral code in the cookies
    referring_code = request.cookies.get('referral_code', '')
    
    return render_template('affiliate/register.html', referring_code=referring_code)

@affiliate_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Affiliate dashboard page"""
    # Get affiliate information
    affiliate = Affiliate.query.filter_by(email=current_user.email).first()
    
    if not affiliate:
        flash("You need to register as an affiliate first", "info")
        return redirect(url_for('affiliate.register'))
    
    # Get commissions
    commissions = Commission.query.filter_by(affiliate_id=affiliate.id).order_by(desc(Commission.created_at)).all()
    
    # Calculate statistics
    total_earned = db.session.query(func.sum(Commission.commission_amount)).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status.in_([CommissionStatus.APPROVED.value, CommissionStatus.PAID.value])
    ).scalar() or 0
    
    pending_payout = db.session.query(func.sum(Commission.commission_amount)).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status == CommissionStatus.APPROVED.value
    ).scalar() or 0
    
    paid_out = db.session.query(func.sum(Commission.commission_amount)).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status == CommissionStatus.PAID.value
    ).scalar() or 0
    
    on_hold = db.session.query(func.sum(Commission.commission_amount)).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status == CommissionStatus.HELD.value
    ).scalar() or 0
    
    # Get count of direct referrals (L1)
    direct_referrals = CustomerReferral.query.filter_by(affiliate_id=affiliate.id).count()
    
    # Get number of L2 affiliates (affiliates who joined using this affiliate's code)
    l2_affiliates = Affiliate.query.filter_by(referred_by_affiliate_id=affiliate.id).count()
    
    return render_template(
        'affiliate/dashboard.html',
        affiliate=affiliate,
        commissions=commissions,
        total_earned=total_earned,
        pending_payout=pending_payout,
        paid_out=paid_out,
        on_hold=on_hold,
        direct_referrals=direct_referrals,
        l2_affiliates=l2_affiliates
    )

@affiliate_bp.route('/referral-link', methods=['GET'])
@login_required
def referral_link():
    """Generate referral link for affiliate"""
    affiliate = Affiliate.query.filter_by(email=current_user.email).first()
    
    if not affiliate:
        flash("You need to register as an affiliate first", "info")
        return redirect(url_for('affiliate.register'))
    
    # Generate full referral URL
    base_url = request.host_url.rstrip('/')
    referral_url = f"{base_url}/?ref={affiliate.referral_code}"
    
    return render_template(
        'affiliate/referral_link.html',
        affiliate=affiliate,
        referral_url=referral_url
    )

@affiliate_bp.route('/admin', methods=['GET'])
@login_required
@admin_required
def admin():
    """Admin dashboard for managing affiliates and commissions"""
    # Get all affiliates
    affiliates = Affiliate.query.order_by(Affiliate.created_at.desc()).all()
    
    # Update held commissions to approved if holding period has ended
    held_commissions = Commission.query.filter(
        Commission.status == CommissionStatus.HELD.value,
        Commission.commission_available_date <= datetime.utcnow()
    ).all()
    
    for commission in held_commissions:
        commission.status = CommissionStatus.APPROVED.value
        commission.updated_at = datetime.utcnow()
    
    if held_commissions:
        db.session.commit()
        logger.info(f"Updated {len(held_commissions)} commissions from HELD to APPROVED status")
    
    # Get commissions pending approval
    pending_commissions = Commission.query.filter(
        Commission.status == CommissionStatus.APPROVED.value,
    ).order_by(Commission.commission_available_date).all()
    
    # Calculate total pending payout amount
    total_pending = db.session.query(func.sum(Commission.commission_amount)).filter(
        Commission.status == CommissionStatus.APPROVED.value,
    ).scalar() or 0
    
    # Get recent payouts
    recent_payouts = Commission.query.filter(
        Commission.status.in_([CommissionStatus.PAID.value, CommissionStatus.PAYOUT_FAILED.value])
    ).order_by(Commission.updated_at.desc()).limit(20).all()
    
    # Group recent payouts by batch ID
    batched_payouts = {}
    for payout in recent_payouts:
        if payout.payout_batch_id not in batched_payouts:
            batched_payouts[payout.payout_batch_id] = {
                'date': payout.updated_at,
                'total_amount': 0,
                'status': 'Mixed' if payout.status == CommissionStatus.PAYOUT_FAILED.value else 'Completed',
                'commissions': []
            }
        
        batched_payouts[payout.payout_batch_id]['commissions'].append(payout)
        batched_payouts[payout.payout_batch_id]['total_amount'] += float(payout.commission_amount)
        
        # Update batch status if any item failed
        if payout.status == CommissionStatus.PAYOUT_FAILED.value:
            batched_payouts[payout.payout_batch_id]['status'] = 'Mixed'
    
    return render_template(
        'affiliate/admin.html',
        affiliates=affiliates,
        pending_commissions=pending_commissions,
        total_pending=total_pending,
        batched_payouts=batched_payouts
    )

@affiliate_bp.route('/process-commissions', methods=['POST'])
@login_required
@admin_required
def process_commissions():
    """Process selected commissions for payout"""
    commission_ids = request.form.getlist('commission_ids')
    
    if not commission_ids:
        flash("No commissions selected", "error")
        return redirect(url_for('affiliate.admin'))
    
    # Get selected commissions
    commissions = Commission.query.filter(Commission.id.in_(commission_ids)).all()
    
    # First, check if any of the selected commissions' triggering transactions have been refunded/disputed
    # We do this by checking Stripe's API using the triggering_transaction_id
    import stripe
    from stripe_config import initialize_stripe
    
    # Initialize Stripe if needed
    initialize_stripe()
    
    # Track commissions to be rejected due to refunded/disputed transactions
    rejected_commissions = []
    valid_commissions = []
    
    for commission in commissions:
        try:
            # Check the Stripe payment status using the triggering_transaction_id
            payment_intent = stripe.PaymentIntent.retrieve(commission.triggering_transaction_id)
            
            # If payment was refunded or has a dispute, mark the commission as rejected
            if payment_intent.status != 'succeeded' or getattr(payment_intent, 'amount_refunded', 0) > 0:
                commission.status = CommissionStatus.REJECTED.value
                commission.updated_at = datetime.utcnow()
                rejected_commissions.append(commission.id)
                logger.info(f"Commission {commission.id} rejected due to refunded/disputed transaction")
            else:
                valid_commissions.append(commission)
        except Exception as e:
            logger.error(f"Error checking Stripe payment status for commission {commission.id}: {e}")
            # Continue with other commissions even if there's an error with one
            valid_commissions.append(commission)
    
    # If any commissions were rejected, save those changes
    if rejected_commissions:
        db.session.commit()
        flash(f"{len(rejected_commissions)} commissions were rejected due to refunded/disputed transactions", "warning")
        
    # Group valid commissions by affiliate for batch processing
    affiliate_payouts = {}
    for commission in valid_commissions:
        # Skip any commissions that aren't in APPROVED status or commission_available_date hasn't passed
        if commission.status != CommissionStatus.APPROVED.value or commission.commission_available_date > datetime.utcnow():
            continue
            
        affiliate = Affiliate.query.get(commission.affiliate_id)
        if not affiliate or affiliate.status != AffiliateStatus.ACTIVE.value:
            continue
            
        if affiliate.id not in affiliate_payouts:
            affiliate_payouts[affiliate.id] = {
                'paypal_email': affiliate.paypal_email,
                'amount': 0,
                'commission_ids': []
            }
        
        affiliate_payouts[affiliate.id]['amount'] += float(commission.commission_amount)
        affiliate_payouts[affiliate.id]['commission_ids'].append(commission.id)
    
    if not affiliate_payouts:
        flash("No valid commissions to process", "error")
        return redirect(url_for('affiliate.admin'))
    
    # Process payouts
    result = process_payout_batch(affiliate_payouts)
    
    if result['success']:
        batch_id = result['batch_id']
        commission_map = result.get('commission_map', {})
        
        # Get item-level results if available
        item_results = result.get('item_results', [])
        
        # Update commission statuses based on payout batch results
        for item_result in item_results:
            commission_id = item_result.get('commission_id')
            if commission_id:
                commission = Commission.query.get(commission_id)
                if commission:
                    # Initial status is PAID for batch-level success
                    # Individual items might be updated later through a webhook or status check
                    commission.status = CommissionStatus.PAID.value
                    commission.payout_batch_id = batch_id
                    commission.updated_at = datetime.utcnow()
                    
                    # Mark affiliate's PayPal email as verified once they receive a successful payout
                    affiliate = Affiliate.query.get(commission.affiliate_id)
                    if affiliate and not affiliate.paypal_email_verified_at:
                        affiliate.paypal_email_verified_at = datetime.utcnow()
        
        db.session.commit()
        flash(f"Successfully initiated {len(result['items_processed'])} payouts. Batch ID: {batch_id}", "success")
    else:
        flash(f"Error processing payouts: {result['error']}", "error")
    
    return redirect(url_for('affiliate.admin'))

@affiliate_bp.route('/update-paypal', methods=['POST'])
@login_required
def update_paypal():
    """Update affiliate PayPal email"""
    try:
        # Get the affiliate
        affiliate = Affiliate.query.filter_by(email=current_user.email).first()
        
        if not affiliate:
            flash("You are not registered as an affiliate", "error")
            return redirect(url_for('affiliate.register'))
        
        # Verify user owns this affiliate account
        if affiliate.email != current_user.email:
            flash("You can only update your own PayPal email", "error")
            return redirect(url_for('affiliate.dashboard'))
        
        # Get the new PayPal email
        new_paypal_email = request.form.get('new_paypal_email')
        
        if not new_paypal_email:
            flash("PayPal email is required", "error")
            return redirect(url_for('affiliate.dashboard'))
        
        # Update the PayPal email
        affiliate.paypal_email = new_paypal_email
        affiliate.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash("PayPal email updated successfully", "success")
        return redirect(url_for('affiliate.dashboard'))
    
    except Exception as e:
        logger.error(f"Error updating PayPal email: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('affiliate.dashboard'))

@affiliate_bp.route('/check-payout-status/<string:batch_id>', methods=['GET'])
@login_required
@admin_required
def check_payout_status(batch_id):
    """Check the status of a payout batch"""
    try:
        from paypal_payouts import get_payout_batch_status
        
        # Get commissions for this batch to build commission map
        commissions = Commission.query.filter_by(payout_batch_id=batch_id).all()
        
        # Build a map of sender_item_id to commission_id for status matching
        # We can reconstruct this from our naming convention pattern
        commission_map = {}
        for commission in commissions:
            sender_item_id = f"AFFCOM_{commission.id}_" + commission.updated_at.strftime('%Y%m%d%H%M%S')
            commission_map[sender_item_id] = commission.id
        
        # Get batch status from PayPal
        batch_status = get_payout_batch_status(batch_id, commission_map)
        
        if batch_status['success']:
            # Update commission statuses based on individual item statuses
            if 'items' in batch_status:
                for item in batch_status['items']:
                    commission_id = item.get('commission_id')
                    if commission_id:
                        commission = Commission.query.get(commission_id)
                        if commission:
                            if item['status'] == 'SUCCESS':
                                commission.status = CommissionStatus.PAID.value
                            elif item['status'] in ['FAILED', 'RETURNED', 'BLOCKED']:
                                commission.status = CommissionStatus.PAYOUT_FAILED.value
                            
                            commission.updated_at = datetime.utcnow()
                
                db.session.commit()
                
            flash(f"Payout batch status: {batch_status['batch_status']}", "info")
        else:
            flash(f"Error checking payout status: {batch_status.get('error')}", "error")
        
        return redirect(url_for('affiliate.admin'))
    
    except Exception as e:
        logger.error(f"Error checking payout status: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('affiliate.admin'))

@affiliate_bp.route('/toggle-status/<int:affiliate_id>', methods=['GET'])
@login_required
@admin_required
def toggle_status(affiliate_id):
    """Toggle affiliate status between active and inactive"""
    try:
        # Get the affiliate
        affiliate = Affiliate.query.get(affiliate_id)
        
        if not affiliate:
            flash("Affiliate not found", "error")
            return redirect(url_for('affiliate.admin'))
        
        # Toggle the status
        if affiliate.status == AffiliateStatus.ACTIVE.value:
            affiliate.status = AffiliateStatus.INACTIVE.value
            status_message = "deactivated"
        else:
            affiliate.status = AffiliateStatus.ACTIVE.value
            status_message = "activated"
        
        affiliate.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash(f"Affiliate {affiliate.name} has been {status_message}", "success")
        return redirect(url_for('affiliate.admin'))
    
    except Exception as e:
        logger.error(f"Error toggling affiliate status: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('affiliate.admin'))

@affiliate_bp.route('/track', methods=['GET'])
def track_referral():
    """Middleware to track referral codes from URL parameters"""
    referral_code = request.args.get('ref')
    
    if not referral_code:
        return redirect(url_for('index'))
    
    # Verify referral code exists
    affiliate = Affiliate.query.filter_by(referral_code=referral_code).first()
    if not affiliate or affiliate.status != AffiliateStatus.ACTIVE.value:
        return redirect(url_for('index'))
    
    # Set referral cookie and redirect to homepage
    response = make_response(redirect(url_for('index')))
    return set_referral_cookie(response, referral_code)

def handle_affiliate_commission(payment_intent_id, customer_user_id, amount_usd):
    """
    Handle affiliate commission for a completed payment
    
    Args:
        payment_intent_id (str): Stripe PaymentIntent ID
        customer_user_id (int): User ID of the customer
        amount_usd (float): Payment amount in USD
    """
    try:
        # Check if customer has a referral
        customer_referral = CustomerReferral.query.filter_by(customer_user_id=customer_user_id).first()
        if not customer_referral:
            logger.info(f"No referral found for user {customer_user_id}")
            return
        
        # Get the affiliate
        l1_affiliate = Affiliate.query.get(customer_referral.affiliate_id)
        if not l1_affiliate or l1_affiliate.status != AffiliateStatus.ACTIVE.value:
            logger.info(f"Affiliate {customer_referral.affiliate_id} not found or inactive")
            return
        
        # Calculate Level 1 commission
        base_amount_gbp = get_gbp_amount(amount_usd)
        l1_commission_amount = round(base_amount_gbp * LEVEL_1_COMMISSION_RATE, 2)
        
        # Create Level 1 commission record
        commission_available_date = datetime.utcnow() + timedelta(days=COMMISSION_HOLDING_PERIOD)
        
        l1_commission = Commission(
            affiliate_id=l1_affiliate.id,
            triggering_transaction_id=payment_intent_id,
            stripe_payment_status="succeeded",
            purchase_amount_base=base_amount_gbp,
            commission_rate=LEVEL_1_COMMISSION_RATE,
            commission_amount=l1_commission_amount,
            commission_level=1,  # Level 1
            status=CommissionStatus.HELD.value,
            commission_earned_date=datetime.utcnow(),
            commission_available_date=commission_available_date
        )
        
        db.session.add(l1_commission)
        
        # Check for Level 2 commission (if L1 affiliate was referred by another affiliate)
        if l1_affiliate.referred_by_affiliate_id:
            l2_affiliate = Affiliate.query.get(l1_affiliate.referred_by_affiliate_id)
            if l2_affiliate and l2_affiliate.status == AffiliateStatus.ACTIVE.value:
                # Calculate Level 2 commission
                l2_commission_amount = round(base_amount_gbp * LEVEL_2_COMMISSION_RATE, 2)
                
                # Create Level 2 commission record
                l2_commission = Commission(
                    affiliate_id=l2_affiliate.id,
                    triggering_transaction_id=payment_intent_id,
                    stripe_payment_status="succeeded",
                    purchase_amount_base=base_amount_gbp,
                    commission_rate=LEVEL_2_COMMISSION_RATE,
                    commission_amount=l2_commission_amount,
                    commission_level=2,  # Level 2
                    status=CommissionStatus.HELD.value,
                    commission_earned_date=datetime.utcnow(),
                    commission_available_date=commission_available_date
                )
                
                db.session.add(l2_commission)
        
        db.session.commit()
        logger.info(f"Commission recorded for payment {payment_intent_id}")
    
    except Exception as e:
        logger.error(f"Error handling affiliate commission: {e}")
        db.session.rollback()

def check_referral_on_auth(user_id):
    """
    Check for referral cookie during user signup or login
    
    Args:
        user_id (int): User ID of the authenticated user
    """
    try:
        # Check if user already has a referral
        existing_referral = CustomerReferral.query.filter_by(customer_user_id=user_id).first()
        if existing_referral:
            logger.info(f"User {user_id} already has a referral")
            return
        
        # Check for referral cookie
        referral_code = request.cookies.get('referral_code')
        if not referral_code:
            logger.info(f"No referral cookie found for user {user_id}")
            return
        
        # Verify affiliate exists and is active
        affiliate = Affiliate.query.filter_by(referral_code=referral_code).first()
        if not affiliate or affiliate.status != AffiliateStatus.ACTIVE.value:
            logger.info(f"Invalid or inactive affiliate for referral code {referral_code}")
            return
        
        # Get user details
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return
            
        # Check that user isn't referring themselves
        if user.email == affiliate.email:
            logger.info(f"User {user_id} cannot refer themselves")
            return
        
        # Create customer referral record
        customer_referral = CustomerReferral(
            customer_user_id=user_id,
            affiliate_id=affiliate.id,
            signup_date=datetime.utcnow()
        )
        
        db.session.add(customer_referral)
        db.session.commit()
        logger.info(f"Referral recorded for user {user_id} from affiliate {affiliate.id}")
    
    except Exception as e:
        logger.error(f"Error checking referral on auth: {e}")
        db.session.rollback()