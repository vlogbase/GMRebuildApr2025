"""
Admin Blueprint Module for GloriaMundo Chatbot

This module creates a Flask Blueprint for admin routes,
ensuring the admin dashboard is properly integrated with the main application.
"""

import os
from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import current_user, login_required

from affiliate import is_admin

# Create blueprint
admin_blueprint = Blueprint('admin_blueprint', __name__, url_prefix='/gm-admin')

@admin_blueprint.route('/')
@login_required
def admin_index():
    """
    Main admin dashboard route.
    Redirects to the Flask-Admin dashboard if the user is an admin,
    otherwise shows an access denied page.
    """
    if not is_admin():
        flash('You do not have permission to access the admin area.', 'error')
        return render_template('admin_access_denied.html'), 403
    
    # If admin interface is initialized, redirect to it
    return redirect('/gm-admin/admin/')

@admin_blueprint.route('/check')
@login_required
def admin_check():
    """
    Debug route to check admin access and configuration.
    """
    admin_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
    
    # Check if current user is logged in and is admin
    is_logged_in = current_user.is_authenticated
    is_current_user_admin = is_admin() if is_logged_in else False
    
    # Build debug info
    debug_info = {
        'is_logged_in': is_logged_in,
        'user_email': current_user.email if is_logged_in else None,
        'admin_emails': admin_emails,
        'is_admin': is_current_user_admin,
    }
    
    return render_template('admin_check.html', debug_info=debug_info)