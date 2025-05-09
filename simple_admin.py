"""
Simple Admin Module for GloriaMundo Chatbot

This is a minimal implementation of the admin interface to diagnose issues.
"""

from flask import redirect, url_for, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_required

from app import app, db
from models import User, Commission, Affiliate, Usage
from affiliate import is_admin

# Security mixin for all views
class SecureBaseView:
    def is_accessible(self):
        """Only allow access to admin users"""
        return current_user.is_authenticated and is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login page if user doesn't have access"""
        flash('You do not have permission to access the admin area.', 'error')
        return redirect(url_for('index'))

# Secure admin index view
class SecureAdminIndexView(AdminIndexView, SecureBaseView):
    @expose('/')
    def index(self):
        """Admin dashboard home page"""
        return self.render('admin/index.html')

# Initialize admin interface
def init_simple_admin():
    """Initialize a simple admin interface for testing"""
    # Create admin interface
    admin = Admin(
        app, 
        name='Simple Admin', 
        url='/simple-admin',
        endpoint='simple_admin',
        template_mode='bootstrap3',
        index_view=SecureAdminIndexView(name='Dashboard')
    )
    
    # Add a single view for users
    admin.add_view(ModelView(User, db.session, name='Users'))
    
    # Print debug info
    print(f"Simple Admin initialized at URL: {admin.url}")
    print(f"Routes registered: {[rule.rule for rule in app.url_map.iter_rules() if 'simple-admin' in rule.rule]}")
    
    # Create a direct route for admin access
    @app.route('/simple-admin-direct')
    @login_required
    def simple_admin_direct():
        """Direct route to admin dashboard"""
        if not is_admin():
            flash('You do not have permission to access the admin area.', 'error')
            return redirect(url_for('index'))
        return redirect('/simple-admin/')
    
    # Return the admin instance
    return admin