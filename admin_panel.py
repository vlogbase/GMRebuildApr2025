"""
Admin Panel Module for GloriaMundo Chatbot

This module sets up the Flask-Admin interface for managing affiliates,
commissions, payouts, and provides application analytics.
"""

import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, NoReturn

from flask import Blueprint, flash, redirect, url_for, request, session, render_template, Response, abort
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import current_user
from sqlalchemy import func, desc, and_, not_
from wtforms import BooleanField, Form, StringField, PasswordField, validators, SelectField, FloatField, DateTimeField

from models import User, Affiliate, Transaction, Commission, CustomerReferral, CommissionStatus, AffiliateStatus, PaymentStatus
from database import db
from paypal_config import process_paypal_payout, check_payout_status, generate_sender_batch_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin_panel', __name__, url_prefix='/admin_portal')

# --- Helper Functions ---

def is_admin():
    """Check if the current user is an admin (specifically andy@sentigral.com)"""
    # Check if user is authenticated and has the specific email
    admin_email = os.environ.get('ADMIN_EMAIL', 'andy@sentigral.com').lower()
    return current_user.is_authenticated and current_user.email.lower() == admin_email

def admin_required(f):
    """Decorator to restrict access to admin users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in and has admin access
        if not current_user.is_authenticated or not is_admin():
            flash("You do not have permission to access this page", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Views ---

class AuthenticatedIndexView(AdminIndexView):
    """Custom admin index view that requires authentication
    
    Uses the standard AdminIndexView from Flask-Admin but with authentication
    to ensure only admin users can access the dashboard.
    """
    def dashboard_data(self):
        """Get data for dashboard display"""
        # User stats
        total_users = User.query.count()
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        # Affiliate stats
        total_affiliates = Affiliate.query.count()
        active_affiliates = Affiliate.query.filter_by(status=AffiliateStatus.ACTIVE.value).count()
        
        # Commission stats
        pending_commissions = Commission.query.filter_by(status=CommissionStatus.APPROVED.value).count()
        recent_commissions = Commission.query.order_by(Commission.created_at.desc()).limit(5).all()
        
        # Revenue stats
        total_revenue = db.session.query(func.sum(Transaction.amount_usd)).filter_by(status=PaymentStatus.COMPLETED.value).scalar() or 0
        
        # Get data for charts
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
        
        # Convert to lists for charts
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
        
        return dict(
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
        
    def is_accessible(self):
        """Check if the user has access to the admin interface"""
        return current_user.is_authenticated and is_admin()
    
    def inaccessible_callback(self, name, **kwargs) -> NoReturn:
        """Handle unauthorized access attempts"""
        flash("You do not have permission to access this page", "error")
        # Using abort to indicate no return, which satisfies NoReturn type
        response = redirect(url_for('index'))
        abort(response.status_code)
    
    @expose('/')
    def index(self) -> str:
        """Admin index page showing dashboard"""
        # Since we handle authentication in is_accessible and inaccessible_callback,
        # we know by this point that the user is authorized
        return self.render('admin/dashboard.html', **self.dashboard_data())
    
    @expose('/dashboard')
    def dashboard(self) -> str:
        """Dashboard with app metrics and stats"""
        return self.render('admin/dashboard.html', **self.dashboard_data())

class SecureModelView(ModelView):
    """Base ModelView that requires admin authentication"""
    def is_accessible(self):
        return current_user.is_authenticated and is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        # Flash a message and redirect to homepage
        flash("You do not have permission to access this page", "error")
        # This function is not supposed to return a value according to Flask-Admin
        # but we need to return a response to make it work
        abort(redirect(url_for('index')))

class UserModelView(SecureModelView):
    """User model admin view"""
    column_exclude_list = ['password_hash']
    column_searchable_list = ['username', 'email']
    column_filters = ['created_at', 'user_is_active']
    column_labels = {
        'username': 'Username',
        'email': 'Email',
        'created_at': 'Joined',
        'user_is_active': 'Active'
    }
    
    # Disable user creation/deletion from admin
    can_create = False
    can_delete = False

class AffiliateModelView(SecureModelView):
    """Affiliate model admin view"""
    column_searchable_list = ['name', 'email', 'paypal_email', 'referral_code']
    column_filters = ['status', 'created_at']
    column_labels = {
        'name': 'Name',
        'email': 'Email',
        'paypal_email': 'PayPal Email',
        'referral_code': 'Referral Code',
        'status': 'Status',
        'created_at': 'Joined'
    }
    
    # Format datetime fields
    column_formatters = {
        'created_at': lambda v, c, m, p: m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else '',
        'updated_at': lambda v, c, m, p: m.updated_at.strftime('%Y-%m-%d %H:%M:%S') if m.updated_at else '',
        'terms_agreed_at': lambda v, c, m, p: m.terms_agreed_at.strftime('%Y-%m-%d %H:%M:%S') if m.terms_agreed_at else ''
    }

class TransactionModelView(SecureModelView):
    """Transaction model admin view"""
    column_searchable_list = ['payment_id', 'stripe_payment_intent']
    column_filters = ['status', 'payment_method', 'created_at']
    column_labels = {
        'user_id': 'User ID',
        'amount_usd': 'Amount (USD)',
        'credits': 'Credits',
        'payment_method': 'Payment Method',
        'status': 'Status',
        'created_at': 'Date'
    }
    
    # Format datetime fields
    column_formatters = {
        'created_at': lambda v, c, m, p: m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else '',
        'updated_at': lambda v, c, m, p: m.updated_at.strftime('%Y-%m-%d %H:%M:%S') if m.updated_at else ''
    }
    
    # Disable creation/deletion from admin
    can_create = False
    can_delete = False

class CommissionModelView(SecureModelView):
    """Commission model admin view"""
    column_searchable_list = ['triggering_transaction_id']
    column_filters = ['status', 'affiliate_id', 'commission_level', 'created_at']
    column_labels = {
        'affiliate_id': 'Affiliate ID',
        'commission_amount': 'Amount',
        'commission_level': 'Level',
        'status': 'Status',
        'commission_earned_date': 'Earned Date',
        'commission_available_date': 'Available Date',
        'created_at': 'Created'
    }
    
    # Format datetime fields
    column_formatters = {
        'commission_earned_date': lambda v, c, m, p: m.commission_earned_date.strftime('%Y-%m-%d %H:%M:%S') if m.commission_earned_date else '',
        'commission_available_date': lambda v, c, m, p: m.commission_available_date.strftime('%Y-%m-%d %H:%M:%S') if m.commission_available_date else '',
        'created_at': lambda v, c, m, p: m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else ''
    }
    
    # Action to approve commissions
    action_approve_commission = 'Approve'
    action_reject_commission = 'Reject'
    
    @expose('/action/', methods=('POST',))
    def action_view(self):
        """Custom action handler for commission approval/rejection"""
        action = request.form.get('action')
        ids = request.form.getlist('rowid')
        
        if not ids:
            flash('No commissions selected', 'error')
            return redirect(url_for('.index_view'))
            
        if action == self.action_approve_commission:
            count = 0
            for commission_id in ids:
                commission = Commission.query.get(commission_id)
                if commission and commission.status == CommissionStatus.HELD.value:
                    commission.status = CommissionStatus.APPROVED.value
                    count += 1
            
            db.session.commit()
            flash(f'Successfully approved {count} commissions', 'success')
            
        elif action == self.action_reject_commission:
            count = 0
            for commission_id in ids:
                commission = Commission.query.get(commission_id)
                if commission and commission.status == CommissionStatus.HELD.value:
                    commission.status = CommissionStatus.REJECTED.value
                    count += 1
            
            db.session.commit()
            flash(f'Successfully rejected {count} commissions', 'success')
            
        return redirect(url_for('.index_view'))

# --- Admin initialization function ---

def init_admin(app):
    """Initialize the admin interface with the app"""
    # Create admin interface - will only run once due to Flask's app context
    # Addresses circular template reference by providing explicit template_mode
    admin = Admin(
        app,
        name='GloriaMundo Admin', 
        template_mode='bootstrap4',  # This sets the base template to bootstrap4/admin/base.html
        index_view=AuthenticatedIndexView(name='Dashboard', url='/admin_portal', endpoint='admin'),
        url='/admin_portal',
        static_url_path='/admin_portal/static'  # Ensures static files are properly served
    )
    
    # Add model views
    admin.add_view(UserModelView(User, db.session, name='Users', category='Users'))
    admin.add_view(AffiliateModelView(Affiliate, db.session, name='Affiliates', category='Affiliate Program'))
    admin.add_view(SecureModelView(CustomerReferral, db.session, name='Referrals', category='Affiliate Program'))
    admin.add_view(CommissionModelView(Commission, db.session, name='Commissions', category='Affiliate Program'))
    admin.add_view(TransactionModelView(Transaction, db.session, name='Transactions', category='Billing'))
    
    # Add custom commission management view in blueprint
    
    # Add link back to main site
    admin.add_link(MenuLink(name='Back to Site', url='/'))
    
    return admin

# --- Blueprint Routes ---

@admin_bp.route('/manage-commissions')
@admin_required
def manage_commissions():
    """
    Admin page for managing commissions (custom interface).
    This provides a more user-friendly interface than the default ModelView.
    """
    # Get filter parameters
    status = request.args.get('status', 'held')
    min_amount = request.args.get('min_amount')
    affiliate_id = request.args.get('affiliate_id')
    
    # Base query
    query = Commission.query
    
    # Apply filters
    if status:
        query = query.filter(Commission.status == status)
    if min_amount:
        try:
            min_amount = float(min_amount)
            query = query.filter(Commission.commission_amount >= min_amount)
        except ValueError:
            pass
    if affiliate_id:
        try:
            affiliate_id = int(affiliate_id)
            query = query.filter(Commission.affiliate_id == affiliate_id)
        except ValueError:
            pass
            
    # Get all held commissions that are available for payout
    commissions = query.order_by(Commission.commission_available_date).all()
    
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
    
    # Get all affiliates for filter dropdown
    affiliates = Affiliate.query.filter_by(status=AffiliateStatus.ACTIVE.value).all()
    
    return render_template(
        'admin/manage_commissions.html',
        grouped_commissions=grouped_commissions,
        affiliates=affiliates,
        status=status,
        min_amount=min_amount,
        affiliate_id=affiliate_id
    )

@admin_bp.route('/process-payouts', methods=['POST'])
@admin_required
def process_payouts():
    """
    Process PayPal payouts for selected affiliates.
    """
    try:
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
                return redirect(url_for('admin_panel.manage_commissions'))
                
            selected_affiliates = [str(affiliate.affiliate_id) for affiliate in eligible_affiliates]
        else:
            # Get selected commission IDs from form (individual payout)
            selected_commission_ids = request.form.getlist('commission_ids[]')
            
            if not selected_commission_ids:
                flash("No commissions selected for payout", "warning")
                return redirect(url_for('admin_panel.manage_commissions'))
                
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
            return redirect(url_for('admin_panel.manage_commissions'))
            
        # Process the payout via PayPal
        payout_result = process_paypal_payout(sender_batch_id, payout_items, note=request.form.get('payout_note', 'GloriaMundo Chat Affiliate Commission Payout'))
        
        if payout_result['success']:
            # Update commission status to PROCESSING
            batch_id = payout_result['payout_batch_id']
            for commission_id in affected_commission_ids:
                commission = Commission.query.get(commission_id)
                if commission:
                    commission.status = CommissionStatus.PROCESSING.value
                    commission.payout_batch_id = batch_id
            
            db.session.commit()
            
            flash(f"Successfully initiated payout batch {batch_id}. {len(affected_commission_ids)} commissions are being processed.", "success")
            return redirect(url_for('admin_panel.payouts'))
        else:
            error = payout_result.get('error', 'Unknown error')
            flash(f"PayPal payout failed: {error}", "error")
            return redirect(url_for('admin_panel.manage_commissions'))
        
    except Exception as e:
        logger.error(f"Error in process_payouts: {e}")
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('admin_panel.manage_commissions'))

@admin_bp.route('/payouts')
@admin_required
def payouts():
    """
    Admin page for viewing and checking payout statuses.
    """
    try:
        # Get all commissions that have been assigned to a payout batch
        commissions = Commission.query.filter(
            Commission.payout_batch_id.isnot(None)
        ).order_by(
            desc(Commission.updated_at)
        ).all()
        
        # Group by payout batch
        grouped_payouts = {}
        for commission in commissions:
            batch_id = commission.payout_batch_id
            if batch_id not in grouped_payouts:
                grouped_payouts[batch_id] = {
                    'batch_id': batch_id,
                    'commissions': [],
                    'total_amount': 0.0,
                    'created_at': commission.updated_at,
                    'latest_status': None
                }
            
            # Add commission to group and update totals
            grouped_payouts[batch_id]['commissions'].append(commission)
            grouped_payouts[batch_id]['total_amount'] += float(commission.commission_amount)
            
            # Update latest status (prioritize PAID over other statuses)
            if grouped_payouts[batch_id]['latest_status'] is None:
                grouped_payouts[batch_id]['latest_status'] = commission.status
            elif commission.status == CommissionStatus.PAID.value:
                grouped_payouts[batch_id]['latest_status'] = CommissionStatus.PAID.value
        
        return render_template(
            'admin/payouts.html',
            grouped_payouts=grouped_payouts
        )
        
    except Exception as e:
        logger.error(f"Error in admin payouts: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('admin_panel.index'))

@admin_bp.route('/check-payout-status/<batch_id>')
@admin_required
def check_payout_status_route(batch_id):
    """
    Check and update the status of a PayPal payout batch.
    """
    try:
        # Get status from PayPal
        status_result = check_payout_status(batch_id)
        
        if not status_result['success']:
            flash(f"Error checking payout status: {status_result.get('error')}", "error")
            return redirect(url_for('admin_panel.payouts'))
        
        # Process each item in the payout batch
        updated_count = 0
        for item in status_result['items']:
            sender_item_id = item['sender_item_id']
            transaction_status = item['transaction_status']
            
            # Extract affiliate ID from sender_item_id (format: "aff_123_timestamp")
            if not sender_item_id.startswith('aff_'):
                continue
                
            parts = sender_item_id.split('_')
            if len(parts) < 2:
                continue
                
            affiliate_id = int(parts[1])
            
            # Update all commissions for this affiliate in this batch
            commissions = Commission.query.filter(
                and_(
                    Commission.affiliate_id == affiliate_id,
                    Commission.payout_batch_id == batch_id
                )
            ).all()
            
            for commission in commissions:
                old_status = commission.status
                
                # Map PayPal status to CommissionStatus
                if transaction_status == 'SUCCESS':
                    commission.status = CommissionStatus.PAID.value
                    updated_count += 1
                elif transaction_status == 'FAILED':
                    commission.status = CommissionStatus.FAILED.value
                    updated_count += 1
                elif transaction_status == 'PENDING':
                    commission.status = CommissionStatus.PROCESSING.value
                    updated_count += 1
                elif transaction_status == 'UNCLAIMED':
                    commission.status = CommissionStatus.UNCLAIMED.value
                    updated_count += 1
                    
                # Log status change if it occurred
                if old_status != commission.status:
                    logger.info(f"Updated commission {commission.id} status from {old_status} to {commission.status}")
        
        # Commit changes
        db.session.commit()
        
        flash(f"Successfully updated status for {updated_count} commissions in batch {batch_id}", "success")
        return redirect(url_for('admin_panel.payouts'))
        
    except Exception as e:
        logger.error(f"Error checking payout status: {e}")
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('admin_panel.payouts'))

@admin_bp.route('/toggle-paypal-mode', methods=['POST'])
@admin_required
def toggle_paypal_mode():
    """
    Toggle between PayPal sandbox and live modes.
    """
    try:
        current_mode = os.environ.get('PAYPAL_MODE', 'sandbox')
        new_mode = 'live' if current_mode == 'sandbox' else 'sandbox'
        
        # Update environment variable
        os.environ['PAYPAL_MODE'] = new_mode
        
        flash(f"PayPal mode switched from {current_mode} to {new_mode}", "success")
        return redirect(url_for('admin_panel.index'))
        
    except Exception as e:
        logger.error(f"Error toggling PayPal mode: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('admin_panel.index'))

@admin_bp.route('/approve-commission/<int:commission_id>')
@admin_required
def approve_commission(commission_id):
    """
    Approve a commission for payout.
    """
    try:
        commission = Commission.query.get(commission_id)
        
        if not commission:
            flash("Commission not found", "error")
            return redirect(url_for('admin_panel.manage_commissions'))
            
        if commission.status != CommissionStatus.HELD.value:
            flash(f"Commission is not in HELD status (current: {commission.status})", "warning")
            return redirect(url_for('admin_panel.manage_commissions'))
            
        # Update status
        commission.status = CommissionStatus.APPROVED.value
        db.session.commit()
        
        flash(f"Commission #{commission_id} approved for payout", "success")
        return redirect(url_for('admin_panel.manage_commissions'))
        
    except Exception as e:
        logger.error(f"Error approving commission: {e}")
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('admin_panel.manage_commissions'))

@admin_bp.route('/reject-commission/<int:commission_id>')
@admin_required
def reject_commission(commission_id):
    """
    Reject a commission (e.g., if the associated purchase was refunded).
    """
    try:
        commission = Commission.query.get(commission_id)
        
        if not commission:
            flash("Commission not found", "error")
            return redirect(url_for('admin_panel.manage_commissions'))
            
        if commission.status != CommissionStatus.HELD.value:
            flash(f"Commission is not in HELD status (current: {commission.status})", "warning")
            return redirect(url_for('admin_panel.manage_commissions'))
            
        # Update status
        commission.status = CommissionStatus.REJECTED.value
        db.session.commit()
        
        flash(f"Commission #{commission_id} rejected", "success")
        return redirect(url_for('admin_panel.manage_commissions'))
        
    except Exception as e:
        logger.error(f"Error rejecting commission: {e}")
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('admin_panel.manage_commissions'))