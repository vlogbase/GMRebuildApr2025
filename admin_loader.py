"""
Minimal Admin Loader for GloriaMundo

This module provides a very simple admin interface without relying on Flask-Admin.
"""

import os
import logging
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import current_user, login_required

logger = logging.getLogger(__name__)

# Create blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')

def admin_required(f):
    """Decorator to require admin access for routes"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Check if current user's email is in the admin list
        admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
        admin_emails = [email.strip() for email in admin_emails if email.strip()]
        
        if current_user.email not in admin_emails:
            logger.warning(f"Unauthorized admin access attempt by {current_user.email}")
            abort(403)  # Forbidden
        
        logger.info(f"Admin access granted to {current_user.email}")
        return f(*args, **kwargs)
    
    return decorated_function

# Basic admin routes
@admin_bp.route('/')
@admin_required
def index():
    """Admin dashboard home page"""
    try:
        # Import models here to avoid circular imports
        from models import User
        from datetime import datetime
        user_count = User.query.count()
        
        # If available, get affiliate and commission counts
        affiliate_count = 0
        commission_count = 0
        try:
            from models import Affiliate, Commission
            affiliate_count = Affiliate.query.count()
            commission_count = Commission.query.count()
        except Exception as e:
            logger.warning(f"Could not get affiliate counts: {str(e)}")
            
        return render_template('admin/dashboard.html',
                              user_count=user_count,
                              affiliate_count=affiliate_count,
                              commission_count=commission_count,
                              total_pending=0,
                              total_approved=0,
                              total_paid=0,
                              now=datetime.now())
                              
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}")
        return f"""
        <h1>Admin Dashboard</h1>
        <p>You are logged in as {current_user.email}</p>
        <p>Error loading dashboard data: {str(e)}</p>
        <p><a href="/">Back to home</a></p>
        """

@admin_bp.route('/check')
@admin_required
def admin_check():
    """Admin access diagnostic page"""
    from datetime import datetime
    admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com')
    
    return render_template('admin/check.html',
                           admin_email=current_user.email,
                           admin_emails=admin_emails,
                           now=datetime.now())

# Function to register the admin blueprint
def register_admin_blueprint(app):
    """Register the admin blueprint with the app"""
    app.register_blueprint(admin_bp)
    
    # Register a direct /admin route that doesn't use the blueprint for fallback
    @app.route('/admin-direct')
    @login_required
    def admin_direct():
        # Check if current user is an admin
        admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
        admin_emails = [email.strip() for email in admin_emails if email.strip()]
        
        if current_user.email not in admin_emails:
            flash('Access denied. You are not an administrator.', 'danger')
            return redirect(url_for('index'))
        
        return redirect(url_for('admin.index'))
    
    logger.info("Admin blueprint registered successfully")
    return admin_bp