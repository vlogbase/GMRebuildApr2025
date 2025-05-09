"""
Admin Routes Module for GloriaMundo Chatbot

This module handles admin routes and views without relying on Flask-Admin.
It provides a secure admin interface for managing the system.
"""

import os
import logging
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import current_user, login_required
from sqlalchemy import func, desc

from app import db
from models import User, Affiliate, Commission, CommissionStatus, Transaction, Usage
from affiliate import is_admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint with a distinct URL prefix
admin_routes = Blueprint('admin_routes', __name__, url_prefix='/admin-dashboard')

# Secure route decorator
def admin_required(f):
    """Decorator to require admin access for routes"""
    @login_required
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('You do not have permission to access the admin area.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_routes.route('/')
@admin_required
def dashboard():
    """Admin dashboard home page with overview statistics"""
    # Get basic stats
    user_count = User.query.count()
    affiliate_count = Affiliate.query.count()
    commission_count = Commission.query.count()
    pending_commissions = Commission.query.filter_by(status='pending').count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get top affiliates by commission amount
    top_affiliates = db.session.query(
        Affiliate,
        func.sum(Commission.commission_amount).label('total_commission')
    ).join(Commission).group_by(Affiliate.id).order_by(desc('total_commission')).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        user_count=user_count,
        affiliate_count=affiliate_count,
        commission_count=commission_count,
        pending_commissions=pending_commissions,
        recent_users=recent_users,
        top_affiliates=top_affiliates
    )

@admin_routes.route('/users')
@admin_required
def users():
    """List all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_routes.route('/affiliates')
@admin_required
def affiliates():
    """List all affiliates"""
    affiliates = Affiliate.query.order_by(Affiliate.created_at.desc()).all()
    return render_template('admin/affiliates.html', affiliates=affiliates)

@admin_routes.route('/commissions')
@admin_required
def commissions():
    """List all commissions"""
    status_filter = request.args.get('status', '')
    
    query = Commission.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    commissions = query.order_by(Commission.commission_earned_date.desc()).all()
    
    # Define statuses for the template
    commission_statuses = ['pending', 'approved', 'paid', 'rejected']
    
    return render_template(
        'admin/commissions.html',
        commissions=commissions,
        current_filter=status_filter,
        statuses=commission_statuses
    )

@admin_routes.route('/commission/<int:commission_id>/approve', methods=['POST'])
@admin_required
def approve_commission(commission_id):
    """Approve a commission"""
    commission = Commission.query.get_or_404(commission_id)
    
    if commission.status != 'pending':
        flash(f'Commission #{commission_id} is not in PENDING status', 'error')
    else:
        commission.status = 'approved'
        commission.commission_available_date = datetime.utcnow()
        db.session.commit()
        flash(f'Commission #{commission_id} approved successfully', 'success')
    
    return redirect(url_for('admin_routes.commissions'))

@admin_routes.route('/commission/<int:commission_id>/reject', methods=['POST'])
@admin_required
def reject_commission(commission_id):
    """Reject a commission"""
    commission = Commission.query.get_or_404(commission_id)
    
    if commission.status not in ['pending', 'approved']:
        flash(f'Commission #{commission_id} cannot be rejected from {commission.status} status', 'error')
    else:
        commission.status = 'rejected'
        db.session.commit()
        flash(f'Commission #{commission_id} rejected successfully', 'success')
    
    return redirect(url_for('admin_routes.commissions'))

@admin_routes.route('/usage')
@admin_required
def usage():
    """View usage statistics"""
    # Get top users by token usage
    top_users = db.session.query(
        User,
        func.sum(Usage.credits_used).label('total_credits')
    ).join(Usage).group_by(User.id).order_by(desc('total_credits')).limit(10).all()
    
    # Get top models by usage
    top_models = db.session.query(
        Usage.model_id,
        func.count(Usage.id).label('usage_count'),
        func.sum(Usage.credits_used).label('total_credits')
    ).group_by(Usage.model_id).order_by(desc('usage_count')).limit(10).all()
    
    return render_template(
        'admin/usage.html',
        top_users=top_users,
        top_models=top_models
    )

@admin_routes.route('/check')
@admin_required
def admin_check():
    """Diagnostic page to verify admin access"""
    admin_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
    admin_emails = [email.strip() for email in admin_emails if email.strip()]
    
    return render_template(
        'admin/check.html',
        user_email=current_user.email,
        admin_emails=admin_emails,
        is_admin=is_admin()
    )