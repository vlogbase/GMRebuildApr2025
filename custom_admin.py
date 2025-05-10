"""
Custom Admin Dashboard for GloriaMundo

A lightweight custom admin dashboard implementation that doesn't rely on Flask-Admin.
This approach uses standard Flask routes and templates to provide admin functionality.
"""

import os
import logging
from datetime import datetime
from functools import wraps
from flask import Blueprint, redirect, url_for, render_template, request, abort, flash
from flask_login import current_user
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Access control decorator
def admin_required(f):
    """Decorator to require admin access for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        
        admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
        admin_emails = [email.strip() for email in admin_emails if email.strip()]
        
        if current_user.email not in admin_emails:
            logger.warning(f"Unauthorized admin access attempt by {current_user.email}")
            abort(403)  # Forbidden
            
        logger.info(f"Admin access granted to {current_user.email}")
        return f(*args, **kwargs)
    return decorated_function

# Admin routes
@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard home page with overview statistics"""
    from models import User, Affiliate, Commission, Usage
    from app import db
    
    # Basic stats
    user_count = User.query.count()
    affiliate_count = Affiliate.query.count()
    commission_count = Commission.query.count()
    pending_commissions = Commission.query.filter_by(status='pending').count()
    approved_commissions = Commission.query.filter_by(status='approved').count()
    paid_commissions = Commission.query.filter_by(status='paid').count()
    rejected_commissions = Commission.query.filter_by(status='rejected').count()
    
    # Total commission amounts
    total_pending = Commission.query.filter_by(status='pending').with_entities(
        func.sum(Commission.commission_amount)).scalar() or 0
    total_approved = Commission.query.filter_by(status='approved').with_entities(
        func.sum(Commission.commission_amount)).scalar() or 0
    total_paid = Commission.query.filter_by(status='paid').with_entities(
        func.sum(Commission.commission_amount)).scalar() or 0
    
    # Recent user activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                          user_count=user_count,
                          affiliate_count=affiliate_count,
                          commission_count=commission_count,
                          pending_commissions=pending_commissions,
                          approved_commissions=approved_commissions,
                          paid_commissions=paid_commissions,
                          rejected_commissions=rejected_commissions,
                          total_pending=total_pending,
                          total_approved=total_approved,
                          total_paid=total_paid,
                          recent_users=recent_users)

@admin_bp.route('/users')
@admin_required
def users():
    """List all users"""
    from models import User
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/affiliates')
@admin_required
def affiliates():
    """List all affiliates"""
    from models import Affiliate
    
    affiliates = Affiliate.query.order_by(Affiliate.created_at.desc()).all()
    return render_template('admin/affiliates.html', affiliates=affiliates)

@admin_bp.route('/commissions')
@admin_required
def commissions():
    """List all commissions"""
    from models import Commission, Affiliate
    from app import db
    
    # Get all commissions with affiliate info
    commissions = db.session.query(
        Commission, Affiliate.email.label('affiliate_email')
    ).join(
        Affiliate, Commission.affiliate_id == Affiliate.id
    ).order_by(
        Commission.commission_available_date.desc()
    ).all()
    
    return render_template('admin/commissions.html', commissions=commissions)

@admin_bp.route('/approve_commission/<int:commission_id>', methods=['POST'])
@admin_required
def approve_commission(commission_id):
    """Approve a commission"""
    from models import Commission
    from app import db
    
    commission = Commission.query.get_or_404(commission_id)
    if commission.status == 'pending':
        commission.status = 'approved'
        commission.commission_available_date = datetime.now()
        db.session.commit()
        flash('Commission approved successfully.', 'success')
        logger.info(f"Commission {commission_id} approved by {current_user.email}")
    else:
        flash('Commission cannot be approved (not in pending status).', 'warning')
    
    return redirect(url_for('admin.commissions'))

@admin_bp.route('/reject_commission/<int:commission_id>', methods=['POST'])
@admin_required
def reject_commission(commission_id):
    """Reject a commission"""
    from models import Commission
    from app import db
    
    commission = Commission.query.get_or_404(commission_id)
    if commission.status in ['pending', 'approved']:
        commission.status = 'rejected'
        db.session.commit()
        flash('Commission rejected successfully.', 'success')
        logger.info(f"Commission {commission_id} rejected by {current_user.email}")
    else:
        flash('Commission cannot be rejected (already paid or rejected).', 'warning')
    
    return redirect(url_for('admin.commissions'))

@admin_bp.route('/token_usage')
@admin_required
def token_usage():
    """View token usage statistics"""
    from models import Usage, User
    from app import db
    
    # Build a query to summarize token usage
    usage_data = (
        db.session.query(
            Usage.user_id.label('user_id'),
            User.email.label('email'),
            func.sum(Usage.credits_used).label('total_credits'),
            func.max(Usage.created_at).label('last_activity')
        )
        .join(User, Usage.user_id == User.id)
        .group_by(Usage.user_id, User.email)
        .order_by(desc('total_credits'))
        .all()
    )
    
    return render_template('admin/token_usage.html', usage_data=usage_data)

@admin_bp.route('/popular_models')
@admin_required
def popular_models():
    """View popular models statistics"""
    from models import Usage
    from app import db
    
    # Build a query to summarize model usage
    models_data = (
        db.session.query(
            Usage.model_id.label('model_id'),
            func.count(Usage.id).label('usage_count'),
            func.sum(Usage.credits_used).label('total_credits'),
            func.max(Usage.created_at).label('last_used')
        )
        .group_by(Usage.model_id)
        .order_by(desc('usage_count'))
        .all()
    )
    
    return render_template('admin/popular_models.html', models_data=models_data)

@admin_bp.route('/check')
@admin_required
def admin_check():
    """Diagnostic page to verify admin access"""
    return render_template('admin/check.html', 
                          admin_email=current_user.email,
                          admin_emails=os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com'))

def register_admin_blueprint(app):
    """Register the admin blueprint with the Flask application"""
    app.register_blueprint(admin_bp)
    
    # Add a redirect from the root /admin to the blueprint
    @app.route('/admin')
    def admin_redirect():
        return redirect(url_for('admin.dashboard'))
    
    logger.info("Admin blueprint registered successfully")
    return admin_bp