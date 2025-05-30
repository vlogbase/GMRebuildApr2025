"""
Simple admin panel for GloriaMundo without Flask-Admin

This module provides a blueprint for a simple admin panel
using only Flask's native features to avoid template recursion issues.
"""

import os
import logging
import sys
import traceback
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, flash, redirect, url_for, render_template, request, abort, current_app
from flask_login import current_user, login_required
from sqlalchemy import func, desc, and_, not_

from models import User, Affiliate, Transaction, Commission, CustomerReferral, CommissionStatus, AffiliateStatus, PaymentStatus
from database import db
from datetime import datetime
import uuid

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Add a stream handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Log that the module was imported successfully
logger.info("Simple admin module loaded successfully")

# Simplified PayPal integration functions to avoid complex external dependencies
def generate_sender_batch_id():
    """Generate a unique batch ID for PayPal payouts"""
    return f"batch-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

def process_paypal_payout(sender_batch_id, payout_items):
    """
    Process PayPal payout (simplified stub implementation)
    
    In a real implementation, this would call the PayPal API.
    For now, we'll just return a simulated successful response.
    
    Args:
        sender_batch_id: A unique ID for this batch
        payout_items: List of payout items, each with recipient and amount
        
    Returns:
        dict: Simulated PayPal response
    """
    try:
        # Simulate PayPal API call
        return {
            "batch_header": {
                "payout_batch_id": sender_batch_id,
                "batch_status": "PENDING"
            }
        }
    except Exception as e:
        logger.error(f"Error processing PayPal payout: {str(e)}")
        raise

def check_payout_status(batch_id):
    """
    Check the status of a PayPal payout batch (simplified stub implementation)
    
    In a real implementation, this would call the PayPal API.
    For now, we'll just return a simulated response.
    
    Args:
        batch_id: The batch ID to check
        
    Returns:
        dict: Simulated PayPal response with batch status
    """
    try:
        # Simulate PayPal API call to get batch status
        # In real implementation, this would check the actual status from PayPal
        return {
            "batch_header": {
                "payout_batch_id": batch_id,
                "batch_status": "SUCCESS"
            },
            "items": [
                {
                    "transaction_status": "SUCCESS",
                    "payout_item_id": "1",
                    "sender_item_id": "1"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error checking PayPal payout status: {str(e)}")
        raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint with a different URL prefix
admin_bp = Blueprint('admin', __name__, url_prefix='/admin_dash')

# --- Helper Functions ---

def is_admin():
    """Check if the current user is an admin (specifically andy@sentigral.com)"""
    if not current_user.is_authenticated:
        return False
    return current_user.email == 'andy@sentigral.com'

def admin_required(f):
    """Decorator to restrict access to admin users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not is_admin():
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Routes ---

@admin_bp.route('/')
@admin_required
def index():
    """Admin dashboard with stats and KPIs"""
    # Add debug logging to trace execution
    logger.info("Admin dashboard route accessed")
    try:
        # User stats
        logger.info("Getting user stats")
        total_users = User.query.count()
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        # Affiliate stats
        logger.info("Getting affiliate stats")
        total_affiliates = Affiliate.query.count()
        active_affiliates = Affiliate.query.filter_by(status=AffiliateStatus.ACTIVE.value).count()
    
        # Commission stats
        logger.info("Getting commission stats")
        pending_commissions = Commission.query.filter_by(status=CommissionStatus.APPROVED.value).count()
        recent_commissions = Commission.query.order_by(Commission.created_at.desc()).limit(5).all()
        
        # Revenue stats
        logger.info("Getting revenue stats")
        total_revenue = db.session.query(func.sum(Transaction.amount_usd)).filter_by(status=PaymentStatus.COMPLETED.value).scalar() or 0
        
        # Date range for charts
        logger.info("Preparing chart data")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # User registrations by day
        user_registrations = db.session.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(User.created_at >= start_date, User.created_at <= end_date)\
        .group_by(func.date(User.created_at))\
        .order_by(func.date(User.created_at))\
        .all()
        
        # Revenue by day
        revenue_by_day = db.session.query(
            func.date(Transaction.created_at).label('date'),
            func.sum(Transaction.amount_usd).label('amount')
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == PaymentStatus.COMPLETED.value
        )\
        .group_by(func.date(Transaction.created_at))\
        .order_by(func.date(Transaction.created_at))\
        .all()
        
        # Create a full date range for the last 30 days
        date_range = [(start_date + timedelta(days=i)).date() for i in range(31)]
        
        # Create dict for fast lookups
        user_dict = {str(r[0]): r[1] for r in user_registrations}
        revenue_dict = {str(r[0]): float(r[1]) for r in revenue_by_day}
        
        # Fill in missing dates with zeros
        user_data = [user_dict.get(str(d), 0) for d in date_range]
        revenue_data = [revenue_dict.get(str(d), 0) for d in date_range]
        date_labels = [d.strftime('%Y-%m-%d') for d in date_range]
        
        # Get PayPal mode
        paypal_mode = os.environ.get('PAYPAL_MODE', 'sandbox')
        
        logger.info("Rendering admin dashboard template")
        return render_template('admin/dashboard.html',
            total_users=total_users,
            recent_users=recent_users,
            total_affiliates=total_affiliates,
            active_affiliates=active_affiliates,
            pending_commissions=pending_commissions,
            recent_commissions=recent_commissions,
            total_revenue=total_revenue,
            user_labels=date_labels,
            user_data=user_data,
            revenue_labels=date_labels,
            revenue_data=revenue_data,
            paypal_mode=paypal_mode
        )
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}", exc_info=True)
        # Simple fallback page in case of errors
        return f"""
        <html>
            <head><title>Admin Dashboard Error</title></head>
            <body>
                <h1>Error Loading Admin Dashboard</h1>
                <p>An error occurred while loading the admin dashboard: {str(e)}</p>
                <p>This has been logged for investigation.</p>
                <a href="/">Return to Home</a>
            </body>
        </html>
        """, 500

@admin_bp.route('/manage_commissions')
@admin_required
def manage_commissions():
    """Admin page for managing commissions"""
    # Get filter parameters
    status = request.args.get('status', 'held')
    affiliate_id = request.args.get('affiliate_id', '')
    min_amount = request.args.get('min_amount', '')
    
    # Parse min_amount
    try:
        min_amount_val = float(min_amount) if min_amount else 0
    except ValueError:
        min_amount_val = 0
    
    # Build base query
    query = Commission.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    
    if affiliate_id:
        query = query.filter_by(affiliate_id=int(affiliate_id))
    
    if min_amount_val > 0:
        query = query.filter(Commission.commission_amount >= min_amount_val)
    
    # Get results
    commissions = query.order_by(Commission.created_at.desc()).all()
    
    # Group by affiliate for easier UI
    grouped_commissions = {}
    for commission in commissions:
        affiliate_id = commission.affiliate_id
        if affiliate_id not in grouped_commissions:
            affiliate = Affiliate.query.get(affiliate_id)
            grouped_commissions[affiliate_id] = {
                'affiliate': affiliate,
                'commissions': [],
                'total_amount': 0
            }
        
        grouped_commissions[affiliate_id]['commissions'].append(commission)
        grouped_commissions[affiliate_id]['total_amount'] += commission.commission_amount
    
    # Get all affiliates for filter dropdown
    affiliates = Affiliate.query.all()
    
    return render_template('admin/manage_commissions.html',
        grouped_commissions=grouped_commissions,
        affiliates=affiliates,
        status=status,
        affiliate_id=affiliate_id,
        min_amount=min_amount
    )

@admin_bp.route('/approve_commission/<int:commission_id>', methods=['GET', 'POST'])
@admin_required
def approve_commission(commission_id):
    """Approve a commission for payout"""
    # Handle batch approval
    if commission_id == 0 and request.method == 'POST':
        commission_ids = request.form.getlist('commission_ids[]')
        action = request.form.get('action')
        
        if action == 'batch_approve':
            for cid in commission_ids:
                commission = Commission.query.get(int(cid))
                if commission and commission.status == CommissionStatus.HELD.value:
                    commission.status = CommissionStatus.APPROVED.value
                    db.session.add(commission)
            
            db.session.commit()
            flash(f'Successfully approved {len(commission_ids)} commissions.', 'success')
            return redirect(url_for('admin.manage_commissions'))
    
    # Handle single approval
    commission = Commission.query.get(commission_id)
    if not commission:
        flash('Commission not found.', 'error')
        return redirect(url_for('admin.manage_commissions'))
    
    if commission.status != CommissionStatus.HELD.value:
        flash('This commission is not in HELD status and cannot be approved.', 'warning')
        return redirect(url_for('admin.manage_commissions'))
    
    commission.status = CommissionStatus.APPROVED.value
    db.session.add(commission)
    db.session.commit()
    
    flash(f'Commission #{commission_id} has been approved for payout.', 'success')
    return redirect(url_for('admin.manage_commissions'))

@admin_bp.route('/reject_commission/<int:commission_id>', methods=['GET', 'POST'])
@admin_required
def reject_commission(commission_id):
    """Reject a commission (e.g., if the associated purchase was refunded)"""
    # Handle batch rejection
    if commission_id == 0 and request.method == 'POST':
        commission_ids = request.form.getlist('commission_ids[]')
        action = request.form.get('action')
        
        if action == 'batch_reject':
            for cid in commission_ids:
                commission = Commission.query.get(int(cid))
                if commission and commission.status == CommissionStatus.HELD.value:
                    commission.status = CommissionStatus.REJECTED.value
                    db.session.add(commission)
            
            db.session.commit()
            flash(f'Successfully rejected {len(commission_ids)} commissions.', 'success')
            return redirect(url_for('admin.manage_commissions'))
    
    # Handle single rejection
    commission = Commission.query.get(commission_id)
    if not commission:
        flash('Commission not found.', 'error')
        return redirect(url_for('admin.manage_commissions'))
    
    if commission.status != CommissionStatus.HELD.value:
        flash('This commission is not in HELD status and cannot be rejected.', 'warning')
        return redirect(url_for('admin.manage_commissions'))
    
    commission.status = CommissionStatus.REJECTED.value
    db.session.add(commission)
    db.session.commit()
    
    flash(f'Commission #{commission_id} has been rejected.', 'success')
    return redirect(url_for('admin.manage_commissions'))

@admin_bp.route('/process_payouts', methods=['POST'])
@admin_required
def process_payouts():
    """Process PayPal payouts for selected affiliates"""
    # Get selected commission IDs
    commission_ids = request.form.getlist('commission_ids[]')
    
    if not commission_ids:
        flash('No commissions selected for payout.', 'warning')
        return redirect(url_for('admin.manage_commissions'))
    
    # Group commissions by affiliate for PayPal batch payout
    commissions_by_affiliate = {}
    for cid in commission_ids:
        commission = Commission.query.get(int(cid))
        if not commission:
            continue
        
        if commission.status != CommissionStatus.APPROVED.value:
            flash(f'Commission #{cid} is not in APPROVED status and cannot be paid out.', 'warning')
            continue
        
        affiliate_id = commission.affiliate_id
        if affiliate_id not in commissions_by_affiliate:
            commissions_by_affiliate[affiliate_id] = []
        
        commissions_by_affiliate[affiliate_id].append(commission)
    
    if not commissions_by_affiliate:
        flash('No eligible commissions found for payout.', 'warning')
        return redirect(url_for('admin.manage_commissions'))
    
    # Process each affiliate's payout
    successful_count = 0
    failed_count = 0
    batch_id = generate_sender_batch_id()
    
    for affiliate_id, commissions in commissions_by_affiliate.items():
        affiliate = Affiliate.query.get(affiliate_id)
        if not affiliate or not affiliate.paypal_email:
            flash(f'Affiliate #{affiliate_id} does not have a PayPal email address set.', 'error')
            failed_count += len(commissions)
            continue
        
        # Calculate total amount
        total_amount = sum(c.commission_amount for c in commissions)
        
        # Process payout via PayPal
        try:
            # Create payout item for this affiliate
            payout_item = {
                "recipient_type": "EMAIL",
                "amount": {
                    "value": str(total_amount),
                    "currency": "USD"
                },
                "receiver": affiliate.paypal_email,
                "note": f"GloriaMundo Affiliate Commission Payout",
                "sender_item_id": str(affiliate_id)
            }
            
            # Process the payout
            payout_response = process_paypal_payout(
                sender_batch_id=batch_id,
                payout_items=[payout_item]
            )
            
            # Mark commissions as processing
            for commission in commissions:
                commission.status = CommissionStatus.PROCESSING.value
                commission.payout_batch_id = batch_id
                db.session.add(commission)
            
            successful_count += len(commissions)
            
        except Exception as e:
            logger.error(f"PayPal payout failed: {str(e)}")
            flash(f'Error processing payout for affiliate #{affiliate_id}: {str(e)}', 'error')
            failed_count += len(commissions)
    
    db.session.commit()
    
    if successful_count > 0:
        flash(f'Successfully processed {successful_count} commissions for payout.', 'success')
    
    if failed_count > 0:
        flash(f'Failed to process {failed_count} commissions.', 'error')
    
    return redirect(url_for('admin.payouts'))

@admin_bp.route('/payouts')
@admin_required
def payouts():
    """Admin page for viewing and checking payout statuses"""
    # Get commissions with payout_batch_id (those that have been submitted for payout)
    commissions = Commission.query.filter(
        Commission.payout_batch_id.isnot(None),
        Commission.status.in_([
            CommissionStatus.PROCESSING.value,
            CommissionStatus.PAID.value,
            CommissionStatus.FAILED.value,
            CommissionStatus.UNCLAIMED.value
        ])
    ).order_by(Commission.updated_at.desc()).all()
    
    # Group by payout_batch_id
    grouped_payouts = {}
    for commission in commissions:
        batch_id = commission.payout_batch_id
        if batch_id not in grouped_payouts:
            # Find the first commission in this batch to get the creation date
            first_commission = Commission.query.filter_by(payout_batch_id=batch_id).order_by(Commission.updated_at).first()
            created_at = first_commission.updated_at if first_commission else datetime.now()
            
            grouped_payouts[batch_id] = {
                'commissions': [],
                'total_amount': 0,
                'created_at': created_at,
                'latest_status': None
            }
        
        grouped_payouts[batch_id]['commissions'].append(commission)
        grouped_payouts[batch_id]['total_amount'] += commission.commission_amount
        
        # Use the most recent status as the batch status
        previous_commissions = grouped_payouts[batch_id]['commissions'][:-1]
        previous_max_date = datetime.min
        if previous_commissions:
            previous_max_date = max(c.updated_at for c in previous_commissions)
            
        if not grouped_payouts[batch_id]['latest_status'] or commission.updated_at > previous_max_date:
            grouped_payouts[batch_id]['latest_status'] = commission.status
    
    return render_template('admin/payouts.html', grouped_payouts=grouped_payouts)

@admin_bp.route('/check_payout_status/<batch_id>')
@admin_required
def check_payout_status_route(batch_id):
    """Check and update the status of a PayPal payout batch"""
    if not batch_id:
        flash('No batch ID provided.', 'error')
        return redirect(url_for('admin.payouts'))
    
    try:
        # Check status with PayPal
        payout_status = check_payout_status(batch_id)
        
        # Update commission statuses
        commissions = Commission.query.filter_by(batch_id=batch_id).all()
        
        if not commissions:
            flash('No commissions found for this batch ID.', 'warning')
            return redirect(url_for('admin.payouts'))
        
        # Map PayPal statuses to our statuses
        status_map = {
            'SUCCESS': CommissionStatus.PAID.value,
            'FAILED': CommissionStatus.FAILED.value,
            'PENDING': CommissionStatus.PROCESSING.value,
            'UNCLAIMED': CommissionStatus.UNCLAIMED.value,
            'BLOCKED': CommissionStatus.FAILED.value,
            'REFUNDED': CommissionStatus.REJECTED.value
        }
        
        updated_count = 0
        for commission in commissions:
            # Get the specific status for this payment
            item_status = next((item['transaction_status'] for item in payout_status.get('items', []) 
                               if str(commission.id) in item.get('sender_item_id', '')), None)
            
            if item_status and item_status in status_map:
                new_status = status_map[item_status]
                if commission.status != new_status:
                    commission.status = new_status
                    db.session.add(commission)
                    updated_count += 1
        
        db.session.commit()
        
        flash(f'Successfully checked status. Updated {updated_count} commissions.', 'success')
        
    except Exception as e:
        logger.error(f"Error checking payout status: {str(e)}")
        flash(f'Error checking payout status: {str(e)}', 'error')
    
    return redirect(url_for('admin.payouts'))

@admin_bp.route('/toggle_paypal_mode', methods=['POST'])
@admin_required
def toggle_paypal_mode():
    """Toggle between PayPal sandbox and live modes"""
    current_mode = os.environ.get('PAYPAL_MODE', 'sandbox')
    new_mode = 'live' if current_mode == 'sandbox' else 'sandbox'
    
    # Set environment variable
    os.environ['PAYPAL_MODE'] = new_mode
    
    # In a production app, we would update a configuration file or database setting
    # But for simplicity, we're just toggling the environment variable in memory
    
    flash(f'PayPal mode changed from {current_mode} to {new_mode}.', 'success')
    return redirect(url_for('admin.index'))

# Initialize the admin module
def init_admin(app):
    """Register the admin blueprint with the app"""
    app.register_blueprint(admin_bp)
    return admin_bp