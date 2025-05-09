"""
Affiliate Module for GloriaMundo Chatbot

This module handles affiliate routes, registration, commission tracking,
and PayPal payouts for the two-tier affiliate system.
"""

import os
import logging
from datetime import datetime, timedelta
import stripe
import json
from urllib.parse import urljoin

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify, abort, g
from flask_login import current_user, login_required
from sqlalchemy import desc, func, and_, not_
from werkzeug.security import generate_password_hash

from app import db
from forms import AgreeToTermsForm, UpdatePayPalEmailForm
from models import User, Affiliate, CustomerReferral, Commission, CommissionStatus, AffiliateStatus, PaymentStatus, Transaction
from paypal_config import process_paypal_payout, check_payout_status, generate_sender_batch_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
affiliate_bp = Blueprint('affiliate', __name__)

# --- Referral Tracking ---

@affiliate_bp.before_app_request
def track_referral_cookie():
    """
    Track referral code in cookies for attribution.
    This runs before every request to the application.
    
    Implements the following referral attribution policies:
    1. The first affiliate link a user clicks establishes the referral relationship
    2. This can happen any time before the user makes their first payment
    3. Once a customer is linked to an affiliate, they cannot be reassigned to another affiliate
    """
    try:
        # Check if the request has a referral code in URL
        ref_code = request.args.get('ref')
        
        # If ref_code exists in URL, validate and store it
        if ref_code:
            # Validate referral code
            affiliate = Affiliate.query.filter_by(referral_code=ref_code).first()
            
            if affiliate and affiliate.status == AffiliateStatus.ACTIVE.value:
                # Store referral code in session for future use
                session['referral_code'] = ref_code
                session['referral_timestamp'] = datetime.utcnow().isoformat()
                logger.info(f"Stored referral code {ref_code} in session")
                
                # If user is authenticated, try to create referral record immediately
                if current_user.is_authenticated:
                    create_customer_referral(current_user.id, affiliate.id, ref_code)
                
            # Set a flag to update cookies in the after_request handler
            g.update_cookies = True
                
        # If no ref_code in URL but user is authenticated, check session for stored referral code
        elif current_user.is_authenticated:
            stored_ref_code = session.get('referral_code')
            if stored_ref_code:
                # Get the affiliate from the stored referral code
                affiliate = Affiliate.query.filter_by(referral_code=stored_ref_code).first()
                
                if affiliate and affiliate.status == AffiliateStatus.ACTIVE.value:
                    # Try to create customer referral from stored session data
                    create_customer_referral(current_user.id, affiliate.id, stored_ref_code)
                
    except Exception as e:
        import traceback
        logger.error(f"Error tracking referral cookie: {e}")
        traceback.print_exc()

def create_customer_referral(user_id, affiliate_id, ref_code):
    """
    Helper function to create a customer referral record if one doesn't exist.
    
    Args:
        user_id (int): The ID of the user to create a referral for
        affiliate_id (int): The ID of the affiliate who referred the user
        ref_code (str): The referral code used (for logging)
    """
    try:
        # Check if user already has a referral record
        existing_referral = CustomerReferral.query.filter_by(customer_user_id=user_id).first()
        
        if not existing_referral:
            # Create the new customer referral, regardless of transaction status
            # This implements the policy that ANY user who clicks a referral link
            # before their first payment should be attributed to that affiliate
            new_referral = CustomerReferral(
                customer_user_id=user_id,
                affiliate_id=affiliate_id
            )
            db.session.add(new_referral)
            db.session.commit()
            logger.info(f"Created customer referral for user {user_id} from affiliate {affiliate_id} with code {ref_code}")
            return True
        else:
            logger.info(f"User {user_id} already has a referral to affiliate {existing_referral.affiliate_id}, not creating another one")
            return False
    except Exception as e:
        import traceback
        logger.error(f"Error creating customer referral: {e}")
        traceback.print_exc()
        db.session.rollback()
        return False

@affiliate_bp.after_app_request
def set_referral_cookies(response):
    """
    Set cookies after the request is processed.
    """
    try:
        # Check if we need to update cookies
        if hasattr(g, 'update_cookies') and g.update_cookies:
            # Get referral data from session
            ref_code = session.get('referral_code')
            ref_timestamp = session.get('referral_timestamp')
            
            if ref_code:
                # Set cookies with a 30-day expiry
                expires = datetime.utcnow() + timedelta(days=30)
                response.set_cookie('gm_ref', ref_code, expires=expires, httponly=True, secure=True, samesite='Lax')
                
                if ref_timestamp:
                    response.set_cookie('gm_ref_ts', ref_timestamp, expires=expires, httponly=True, secure=True, samesite='Lax')
                    
    except Exception as e:
        logger.error(f"Error setting referral cookies: {e}")
        
    return response

# --- Helper Functions ---

def is_admin():
    """Check if the current user is an admin"""
    # In a real application, you would check against a role or a specific column
    # For simplicity, we're checking if the user email is in the ADMIN_EMAILS list
    admin_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
    return current_user.is_authenticated and current_user.email in admin_emails

def get_gbp_exchange_rate(currency):
    """Get the exchange rate from a currency to GBP"""
    # In a production environment, you'd use a proper currency conversion API
    # For simplicity, we're using a dictionary with fixed rates
    rates = {
        'USD': 0.79,  # 1 USD = 0.79 GBP
        'EUR': 0.85,  # 1 EUR = 0.85 GBP
        'GBP': 1.0,   # 1 GBP = 1.0 GBP (no conversion needed)
        # Add more currencies as needed
    }
    
    return rates.get(currency.upper(), 1.0)  # Default to 1.0 if currency not found

# --- Referral Routes ---

@affiliate_bp.route('/terms')
def terms():
    """
    Display affiliate terms and conditions.
    """
    return render_template('affiliate/terms.html')

@affiliate_bp.route('/agree-to-terms', methods=['POST'])
@login_required
def agree_to_terms():
    """
    Process affiliate terms agreement and optional PayPal email.
    """
    # Create the form
    form = AgreeToTermsForm()
    
    # Validate the form - this will check the CSRF token
    if form.validate_on_submit():
        try:
            # Check if user has already agreed to terms
            affiliate = Affiliate.query.filter_by(email=current_user.email).first()
            
            if not affiliate:
                # Auto-create affiliate for the user
                affiliate = Affiliate.auto_create_for_user(current_user)
                if not affiliate:
                    flash("Error creating affiliate account. Please try again.", "error")
                    return redirect(url_for('billing.account_management'))
                    
            # Check if already active
            if affiliate.status == AffiliateStatus.ACTIVE.value:
                flash("You have already agreed to the affiliate terms.", "info")
                return redirect(url_for('billing.account_management'))
                
            # Get PayPal email from the form
            paypal_email = form.paypal_email.data
            
            # Update affiliate status
            affiliate.agree_to_terms(paypal_email)
            
            # Save to database
            db.session.commit()
            
            flash("Your affiliate account is now active! You can start sharing your referral link.", "success")
            return redirect(url_for('billing.account_management'))
            
        except Exception as e:
            logger.error(f"Error in agree_to_terms: {e}")
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('billing.account_management'))
    else:
        # Form validation failed
        logger.warning(f"Form validation failed: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")
        return redirect(url_for('billing.account_management'))

@affiliate_bp.route('/update-paypal-email', methods=['POST'])
@login_required
def update_paypal_email():
    """
    Update PayPal email for affiliate.
    """
    # Create the form
    form = UpdatePayPalEmailForm()
    
    # Validate the form - this will check the CSRF token
    if form.validate_on_submit():
        try:
            paypal_email = form.paypal_email.data
            
            # Get the affiliate associated with the current user
            affiliate = Affiliate.query.filter_by(email=current_user.email).first()
            
            if not affiliate:
                flash("You are not registered as an affiliate. Please activate your account first.", "info")
                return redirect(url_for('billing.account_management'))
                
            # Update PayPal email
            affiliate.paypal_email = paypal_email
            affiliate.paypal_email_verified_at = None  # Reset verification status
            db.session.commit()
            
            flash("PayPal email updated successfully", "success")
            return redirect(url_for('billing.account_management'))
            
        except Exception as e:
            logger.error(f"Error updating PayPal email: {e}")
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('billing.account_management'))
    else:
        # Form validation failed
        logger.warning(f"Form validation failed: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")
        return redirect(url_for('billing.account_management'))

@affiliate_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register as an affiliate.
    """
    # Get the referral code from the query string if it exists
    ref_code = request.args.get('ref')
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            paypal_email = request.form.get('paypal_email')
            referrer_code = request.form.get('ref_code')
            
            # Validate form data
            if not name or not email or not paypal_email:
                flash("All fields are required", "error")
                return render_template('affiliate/register.html', ref_code=referrer_code)
            
            # Check if email already exists
            existing_affiliate = Affiliate.query.filter_by(email=email).first()
            if existing_affiliate:
                flash("An affiliate with this email already exists", "error")
                return render_template('affiliate/register.html', ref_code=referrer_code)
            
            # Create affiliate
            affiliate = Affiliate.create_affiliate(
                name=name,
                email=email,
                paypal_email=paypal_email,
                referred_by_code=referrer_code
            )
            
            # Save to database
            db.session.add(affiliate)
            db.session.commit()
            
            flash("Affiliate registration successful! Your referral code is: " + affiliate.referral_code, "success")
            return redirect(url_for('affiliate.dashboard'))
            
        except Exception as e:
            logger.error(f"Error in affiliate registration: {e}")
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "error")
            return render_template('affiliate/register.html', ref_code=ref_code)
    
    # GET request - show the form
    return render_template('affiliate/register.html', ref_code=ref_code)

@affiliate_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Affiliate dashboard showing commissions and referrals.
    """
    try:
        # Get the affiliate associated with the current user
        affiliate = Affiliate.query.filter_by(email=current_user.email).first()
        
        if not affiliate:
            flash("You are not registered as an affiliate. Please register first.", "info")
            return redirect(url_for('affiliate.register'))
        
        # Get commissions
        commissions = Commission.query.filter_by(affiliate_id=affiliate.id) \
            .order_by(desc(Commission.created_at)).all()
        
        # Calculate statistics
        total_earned = sum(c.commission_amount for c in commissions if c.status in [CommissionStatus.APPROVED.value, CommissionStatus.PAID.value])
        pending_commissions = sum(c.commission_amount for c in commissions if c.status == CommissionStatus.HELD.value)
        paid_commissions = sum(c.commission_amount for c in commissions if c.status == CommissionStatus.PAID.value)
        
        # Get direct referrals (users referred by this affiliate)
        direct_referrals = CustomerReferral.query.filter_by(affiliate_id=affiliate.id).count()
        
        # Get second-tier referrals (affiliates referred by this affiliate)
        referred_affiliates = Affiliate.query.filter_by(referred_by_affiliate_id=affiliate.id).count()
        
        return render_template(
            'affiliate/dashboard.html',
            affiliate=affiliate,
            commissions=commissions,
            total_earned=total_earned,
            pending_commissions=pending_commissions,
            paid_commissions=paid_commissions,
            direct_referrals=direct_referrals,
            referred_affiliates=referred_affiliates
        )
        
    except Exception as e:
        logger.error(f"Error in affiliate dashboard: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@affiliate_bp.route('/referral-link')
@login_required
def referral_link():
    """
    Generate a referral link for the affiliate.
    """
    try:
        # Get the affiliate associated with the current user
        affiliate = Affiliate.query.filter_by(email=current_user.email).first()
        
        if not affiliate:
            flash("You are not registered as an affiliate. Please register first.", "info")
            return redirect(url_for('affiliate.register'))
        
        # Generate referral links for different pages
        base_url = request.host_url.rstrip('/')
        referral_links = {
            'homepage': f"{base_url}/?ref={affiliate.referral_code}",
            'register': f"{base_url}/affiliate/register?ref={affiliate.referral_code}",
            'signup': f"{base_url}/signup?ref={affiliate.referral_code}"
        }
        
        return render_template(
            'affiliate/referral_link.html',
            affiliate=affiliate,
            referral_links=referral_links
        )
        
    except Exception as e:
        logger.error(f"Error generating referral link: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('affiliate.dashboard'))

# --- Admin Routes ---

@affiliate_bp.route('/admin/commissions')
@login_required
def admin_commissions():
    """
    Admin page for managing commissions.
    """
    try:
        # Check if user is admin
        if not is_admin():
            flash("You do not have permission to access this page", "error")
            return redirect(url_for('index'))
        
        # Get all held commissions that are available for payout
        commissions = Commission.query.filter(
            and_(
                Commission.status == CommissionStatus.HELD.value,
                Commission.commission_available_date <= datetime.utcnow()
            )
        ).all()
        
        # Group commissions by affiliate
        grouped_commissions = {}
        for commission in commissions:
            affiliate_id = commission.affiliate_id
            if affiliate_id not in grouped_commissions:
                affiliate = Affiliate.query.get(affiliate_id)
                grouped_commissions[affiliate_id] = {
                    'affiliate': affiliate,
                    'commissions': [],
                    'total_amount': 0.0
                }
            
            # Add commission to group and update total
            grouped_commissions[affiliate_id]['commissions'].append(commission)
            grouped_commissions[affiliate_id]['total_amount'] += float(commission.commission_amount)
        
        return render_template(
            'affiliate/admin_commissions.html',
            grouped_commissions=grouped_commissions
        )
        
    except Exception as e:
        logger.error(f"Error in admin commissions: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@affiliate_bp.route('/admin/process-payouts', methods=['POST'])
@login_required
def process_payouts():
    """
    Process PayPal payouts for selected affiliates.
    """
    try:
        # Check if user is admin
        if not is_admin():
            flash("You do not have permission to access this page", "error")
            return redirect(url_for('index'))
        
        # Check if bulk payout requested
        if request.form.get('bulk_payout'):
            min_threshold = float(request.form.get('min_threshold', 25.0))
            payout_note = request.form.get('payout_note', 'GloriaMundo Chat Affiliate Commission Payout')
            
            # Get all affiliates with approved commissions totaling at least min_threshold
            eligible_affiliates = db.session.query(
                Commission.affiliate_id,
                func.sum(Commission.commission_amount).label('total_amount')
            ).filter(
                Commission.status == CommissionStatus.APPROVED.value
            ).group_by(
                Commission.affiliate_id
            ).having(
                func.sum(Commission.commission_amount) >= min_threshold
            ).all()
            
            if not eligible_affiliates:
                flash("No affiliates eligible for payout", "warning")
                return redirect(url_for('affiliate.admin_commissions'))
                
            selected_affiliates = [str(affiliate.affiliate_id) for affiliate in eligible_affiliates]
        else:
            # Get selected commission IDs from form (individual payout)
            selected_commission_ids = request.form.getlist('commission_ids[]')
            
            if not selected_commission_ids:
                flash("No commissions selected for payout", "warning")
                return redirect(url_for('affiliate.admin_commissions'))
                
            # Get commissions
            selected_commissions = Commission.query.filter(
                Commission.id.in_(selected_commission_ids),
                Commission.status == CommissionStatus.APPROVED.value
            ).all()
            
            # Group by affiliate
            commissions_by_affiliate = {}
            for commission in selected_commissions:
                if commission.affiliate_id not in commissions_by_affiliate:
                    commissions_by_affiliate[commission.affiliate_id] = []
                commissions_by_affiliate[commission.affiliate_id].append(commission)
                
            selected_affiliates = list(commissions_by_affiliate.keys())
            
        # Generate a unique sender batch ID
        sender_batch_id = generate_sender_batch_id()
        
        # Prepare payout items
        payout_items = []
        affected_commission_ids = []
        
        for affiliate_id in selected_affiliates:
            # Get the affiliate to check PayPal email
            affiliate = Affiliate.query.get(affiliate_id)
            
            if not affiliate or not affiliate.paypal_email:
                logger.warning(f"Skipping affiliate {affiliate_id} - no PayPal email")
                continue
                
            # Get all eligible commissions for this affiliate
            commissions = Commission.query.filter(
                and_(
                    Commission.affiliate_id == affiliate_id,
                    Commission.status == CommissionStatus.APPROVED.value
                )
            ).all()
            
            if not commissions:
                continue
                
            # Calculate total payout amount
            total_amount = sum(c.commission_amount for c in commissions)
            
            # Add to payout items
            payout_items.append({
                'recipient_email': affiliate.paypal_email,
                'amount': total_amount,
                'currency': 'USD',  # Adjust based on your app's requirements
                'sender_item_id': f"aff_{affiliate_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            })
            
            # Track commission IDs to update after successful payout
            affected_commission_ids.extend([c.id for c in commissions])
        
        if not payout_items:
            flash("No eligible affiliates for payout", "warning")
            return redirect(url_for('affiliate.admin_commissions'))
            
        # Process the payout via PayPal
        payout_result = process_paypal_payout(sender_batch_id, payout_items)
        
        if payout_result['success']:
            # Store payout batch information
            payout_batch = {
                'batch_id': payout_result['payout_batch_id'],
                'status': payout_result['batch_status'],
                'sender_batch_id': sender_batch_id,
                'created_at': datetime.utcnow(),
                'total_amount': sum(item['amount'] for item in payout_items),
                'item_count': len(payout_items),
                'commission_ids': affected_commission_ids
            }
            
            # Update commission status to PAID if the payout is marked as success
            # Otherwise, we'll update them when we check the status later
            if payout_result['batch_status'] == 'SUCCESS':
                for commission_id in affected_commission_ids:
                    commission = Commission.query.get(commission_id)
                    if commission:
                        commission.status = CommissionStatus.PAID.value
                        commission.payout_batch_id = payout_result['payout_batch_id']
                        commission.paid_at = datetime.utcnow()
            else:
                # Update status to PAYOUT_INITIATED
                for commission_id in affected_commission_ids:
                    commission = Commission.query.get(commission_id)
                    if commission:
                        commission.status = CommissionStatus.PAYOUT_INITIATED.value
                        commission.payout_batch_id = payout_result['payout_batch_id']
                        commission.updated_at = datetime.utcnow()
                        
            # Commit the changes
            db.session.commit()
                
            # Store payout batch info in session to display in the next page
            session['payout_batch'] = json.dumps(payout_batch)
            
            flash("Payout successfully initiated!", "success")
            return redirect(url_for('affiliate.admin_payouts'))
            
        else:
            flash(f"Error processing payout: {payout_result.get('error', 'Unknown error')}", "error")
            return redirect(url_for('affiliate.admin_commissions'))
            
    except Exception as e:
        logger.error(f"Error in process_payouts: {e}")
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('affiliate.admin_commissions'))

@affiliate_bp.route('/admin/payouts')
@login_required
def admin_payouts():
    """
    Admin page for viewing and checking payout statuses.
    """
    try:
        # Check if user is admin
        if not is_admin():
            flash("You do not have permission to access this page", "error")
            return redirect(url_for('index'))
        
        # Get all commissions that have payout_batch_id (i.e., were part of a payout)
        commissions = Commission.query.filter(
            Commission.payout_batch_id.isnot(None)
        ).order_by(desc(Commission.updated_at)).all()
        
        # Group commissions by payout batch ID
        grouped_payouts = {}
        for commission in commissions:
            batch_id = commission.payout_batch_id
            if batch_id not in grouped_payouts:
                # Initialize the payout batch entry
                grouped_payouts[batch_id] = {
                    'batch_id': batch_id,
                    'commissions': [],
                    'total_amount': 0.0,
                    'affiliates': set(),
                    'latest_status': None,
                    'created_at': commission.updated_at
                }
            
            # Add commission to batch and update totals
            grouped_payouts[batch_id]['commissions'].append(commission)
            grouped_payouts[batch_id]['total_amount'] += float(commission.commission_amount)
            grouped_payouts[batch_id]['affiliates'].add(commission.affiliate_id)
            
            # Track latest status
            if grouped_payouts[batch_id]['latest_status'] is None:
                grouped_payouts[batch_id]['latest_status'] = commission.status
            elif commission.status == CommissionStatus.PAID.value:
                grouped_payouts[batch_id]['latest_status'] = CommissionStatus.PAID.value
        
        return render_template(
            'affiliate/admin_payouts.html',
            grouped_payouts=grouped_payouts
        )
        
    except Exception as e:
        logger.error(f"Error in admin payouts: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@affiliate_bp.route('/admin/check-payout-status/<batch_id>', methods=['POST'])
@login_required
def check_payout_status_route(batch_id):
    """
    Check and update the status of a PayPal payout batch.
    """
    try:
        # Check if user is admin
        if not is_admin():
            flash("You do not have permission to access this page", "error")
            return redirect(url_for('index'))
        
        # Get status from PayPal
        status_result = check_payout_status(batch_id)
        
        if not status_result['success']:
            flash(f"Error checking payout status: {status_result.get('error')}", "error")
            return redirect(url_for('affiliate.admin_payouts'))
        
        # Process each item in the payout batch
        updated_count = 0
        for item in status_result['items']:
            sender_item_id = item['sender_item_id']
            transaction_status = item['transaction_status']
            
            # Extract affiliate ID from sender_item_id (format: "aff_123")
            if not sender_item_id.startswith('aff_'):
                continue
                
            affiliate_id = int(sender_item_id.split('_')[1])
            
            # Update all commissions for this affiliate in this batch
            commissions = Commission.query.filter(
                and_(
                    Commission.affiliate_id == affiliate_id,
                    Commission.payout_batch_id == batch_id
                )
            ).all()
            
            for commission in commissions:
                old_status = commission.status
                
                # Update status based on transaction status
                if transaction_status == 'SUCCESS':
                    commission.status = CommissionStatus.PAID.value
                    
                    # Update paypal_email_verified_at for the affiliate
                    affiliate = Affiliate.query.get(affiliate_id)
                    if affiliate and not affiliate.paypal_email_verified_at:
                        affiliate.paypal_email_verified_at = datetime.utcnow()
                        
                elif transaction_status in ['FAILED', 'RETURNED', 'BLOCKED', 'UNCLAIMED']:
                    commission.status = CommissionStatus.PAYOUT_FAILED.value
                    
                # Only count if there was a change in status
                if commission.status != old_status:
                    updated_count += 1
        
        # Commit changes
        db.session.commit()
        
        flash(f"Payout status updated! {updated_count} commissions were updated.", "success")
        return redirect(url_for('affiliate.admin_payouts'))
        
    except Exception as e:
        logger.error(f"Error checking payout status: {e}")
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('affiliate.admin_payouts'))

@affiliate_bp.route('/admin/approve-commission/<commission_id>', methods=['POST'])
@login_required
def approve_commission(commission_id):
    """
    Approve a commission for payout.
    """
    try:
        # Check if user is admin
        if not is_admin():
            flash("You do not have permission to access this page", "error")
            return redirect(url_for('index'))
        
        # Get the commission
        commission = Commission.query.get(commission_id)
        if not commission:
            flash("Commission not found", "error")
            return redirect(url_for('affiliate.admin_commissions'))
        
        # Update status
        commission.status = CommissionStatus.APPROVED.value
        commission.updated_at = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        flash("Commission approved successfully", "success")
        return redirect(url_for('affiliate.admin_commissions'))
        
    except Exception as e:
        logger.error(f"Error approving commission: {e}")
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('affiliate.admin_commissions'))

@affiliate_bp.route('/admin/reject-commission/<commission_id>', methods=['POST'])
@login_required
def reject_commission(commission_id):
    """
    Reject a commission (e.g., if the associated purchase was refunded).
    """
    try:
        # Check if user is admin
        if not is_admin():
            flash("You do not have permission to access this page", "error")
            return redirect(url_for('index'))
        
        # Get the commission
        commission = Commission.query.get(commission_id)
        if not commission:
            flash("Commission not found", "error")
            return redirect(url_for('affiliate.admin_commissions'))
        
        # Update status
        commission.status = CommissionStatus.REJECTED.value
        commission.updated_at = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        flash("Commission rejected successfully", "success")
        return redirect(url_for('affiliate.admin_commissions'))
        
    except Exception as e:
        logger.error(f"Error rejecting commission: {e}")
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('affiliate.admin_commissions'))

# --- End of the routes ---