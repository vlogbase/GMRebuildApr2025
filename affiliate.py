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
from models import User, Affiliate, CustomerReferral, Commission, CommissionStatus
from paypal_config import process_paypal_payout, check_payout_status, generate_sender_batch_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
affiliate_bp = Blueprint('affiliate', __name__)

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
        
        # Get selected affiliate IDs from form
        selected_affiliates = request.form.getlist('affiliate_id')
        
        if not selected_affiliates:
            flash("No affiliates selected for payout", "warning")
            return redirect(url_for('affiliate.admin_commissions'))
        
        # Generate a unique sender batch ID
        sender_batch_id = generate_sender_batch_id()
        
        # Prepare payout items
        payout_items = []
        affected_commission_ids = []
        
        for affiliate_id in selected_affiliates:
            # Get all eligible commissions for this affiliate
            commissions = Commission.query.filter(
                and_(
                    Commission.affiliate_id == affiliate_id,
                    Commission.status == CommissionStatus.HELD.value,
                    Commission.commission_available_date <= datetime.utcnow()
                )
            ).all()
            
            if not commissions:
                continue
            
            # Get affiliate details
            affiliate = Affiliate.query.get(affiliate_id)
            if not affiliate:
                continue
            
            # Calculate total amount to pay
            total_amount = sum(c.commission_amount for c in commissions)
            
            # Add payout item
            payout_items.append({
                'recipient_email': affiliate.paypal_email,
                'amount': round(total_amount, 2),
                'currency': 'GBP',
                'sender_item_id': f"aff_{affiliate_id}"
            })
            
            # Track commission IDs to update later
            affected_commission_ids.extend([c.id for c in commissions])
        
        if not payout_items:
            flash("No eligible commissions found for selected affiliates", "warning")
            return redirect(url_for('affiliate.admin_commissions'))
        
        # Process the PayPal payout
        payout_result = process_paypal_payout(sender_batch_id, payout_items)
        
        if not payout_result['success']:
            flash(f"Error processing PayPal payout: {payout_result.get('error')}", "error")
            return redirect(url_for('affiliate.admin_commissions'))
        
        # Update commission records with payout batch ID and status
        payout_batch_id = payout_result['payout_batch_id']
        
        for commission_id in affected_commission_ids:
            commission = Commission.query.get(commission_id)
            if commission:
                commission.status = CommissionStatus.PAYOUT_INITIATED.value
                commission.payout_batch_id = payout_batch_id
                commission.updated_at = datetime.utcnow()
        
        # Commit the changes
        db.session.commit()
        
        flash(f"PayPal payout initiated successfully! Batch ID: {payout_batch_id}", "success")
        return redirect(url_for('affiliate.admin_payouts'))
        
    except Exception as e:
        logger.error(f"Error processing payouts: {e}")
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

# --- Cookie and Referral Tracking ---

@affiliate_bp.before_app_request
def track_referral_cookie():
    """
    Track referral code in cookies for attribution.
    This runs before every request to the application.
    """
    # Check if there's a referral code in the query parameters
    ref_code = request.args.get('ref')
    
    if ref_code:
        # Check if it's a valid affiliate code
        affiliate = Affiliate.query.filter_by(referral_code=ref_code).first()
        
        if affiliate:
            # Set a cookie with the referral code that expires in 30 days
            max_age = 60 * 60 * 24 * 30  # 30 days in seconds
            expires = datetime.utcnow() + timedelta(days=30)
            
            # Store these in the response after the view function returns
            if not hasattr(g, 'cookies_to_set'):
                g.cookies_to_set = []
            
            g.cookies_to_set.append({
                'key': 'referral_code',
                'value': ref_code,
                'max_age': max_age,
                'expires': expires,
                'path': '/'
            })

@affiliate_bp.after_app_request
def set_referral_cookies(response):
    """
    Set cookies after the request is processed.
    """
    if hasattr(g, 'cookies_to_set'):
        for cookie in g.cookies_to_set:
            response.set_cookie(
                cookie['key'],
                cookie['value'],
                max_age=cookie['max_age'],
                expires=cookie['expires'],
                path=cookie['path']
            )
    
    return response