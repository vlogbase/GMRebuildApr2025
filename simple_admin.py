"""
Simplified Admin Module for GloriaMundo Chatbot

This module provides a streamlined, reliable admin interface
without the analytics views that were causing issues.
"""

import os
import logging
import sys
from flask import redirect, url_for, request
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simple_admin.log')
    ]
)
logger = logging.getLogger(__name__)

class SecureBaseView:
    """Base view with security features for all admin views"""
    def is_accessible(self):
        """Only allow access to admin users (email: andy@sentigral.com)"""
        if not current_user.is_authenticated:
            return False
        
        admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
        return current_user.email in admin_emails
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login page if user doesn't have access"""
        logger.warning(f"Unauthorized access attempt to {name} by {current_user.email if current_user.is_authenticated else 'unauthenticated user'}")
        return redirect(url_for('login', next=request.url))

class SecureAdminIndexView(AdminIndexView, SecureBaseView):
    """Secure index view for admin panel"""
    def index(self):
        """Admin dashboard home page with overview statistics"""
        return self.render('admin/index.html')

class UserModelView(ModelView, SecureBaseView):
    """User management view"""
    column_list = ['id', 'username', 'email', 'created_at']
    column_searchable_list = ['email', 'username']
    column_filters = ['created_at']
    column_default_sort = ('created_at', True)
    can_create = False  # Users are created through registration/Google Auth

class AffiliateModelView(ModelView, SecureBaseView):
    """Affiliate management view"""
    column_list = [
        'id', 'user_id', 'name', 'email', 'paypal_email', 'referral_code', 
        'status', 'terms_agreed_at', 'created_at'
    ]
    column_filters = ['status', 'created_at']
    column_searchable_list = ['email', 'paypal_email']
    column_default_sort = ('created_at', True)

class CommissionModelView(ModelView, SecureBaseView):
    """Commission management view"""
    column_list = [
        'id', 'affiliate_id', 'referred_user_id', 'commission_level', 
        'purchase_amount_base', 'commission_amount', 'status', 
        'commission_earned_date', 'commission_available_date', 'payout_batch_id'
    ]
    
    column_formatters = {
        'purchase_amount_base': lambda v, c, m, p: f'£{m.purchase_amount_base:.2f}',
        'commission_amount': lambda v, c, m, p: f'£{m.commission_amount:.2f}'
    }
    
    column_default_sort = ('commission_available_date', True)
    column_filters = ['status', 'commission_available_date', 'commission_level']
    can_create = False  # Commissions are created automatically
    can_edit = True     # Allow editing status
    
    def _format_affiliate_email(view, context, model, name):
        """Get affiliate email for display"""
        try:
            if model.affiliate:
                return model.affiliate.email
            return "N/A"
        except Exception as e:
            logger.error(f"Error getting affiliate email: {e}")
            return "Error"

def create_admin(app, db):
    """
    Create and initialize a simplified admin interface for the application.
    This version avoids SQLAlchemy errors by not using the analytics views.
    
    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
    
    Returns:
        Admin: The initialized Flask-Admin instance
    """
    try:
        # Import models only after app context is established
        with app.app_context():
            from models import User, Affiliate, Commission
            
            # Create admin instance with unique endpoint names
            admin = Admin(
                app, 
                name='GloriaMundo Admin',
                template_mode='bootstrap3',
                index_view=SecureAdminIndexView(
                    name='Dashboard', 
                    url='/admin',
                    endpoint='admin_dashboard'  # Unique endpoint to avoid conflicts
                ),
                base_template='admin/master.html'
            )
            
            # Add views with unique endpoint names to avoid blueprint naming conflicts
            admin.add_view(UserModelView(
                User, db.session, 
                name='Users', 
                category='User Management',
                endpoint='admin_users'  # Unique endpoint to avoid conflicts
            ))
            admin.add_view(AffiliateModelView(
                Affiliate, db.session, 
                name='Affiliates', 
                category='Affiliate System',
                endpoint='admin_affiliates'  # Unique endpoint to avoid conflicts
            ))
            admin.add_view(CommissionModelView(
                Commission, db.session, 
                name='Commissions', 
                category='Affiliate System',
                endpoint='admin_commissions'  # Unique endpoint to avoid conflicts
            ))
            
            # Simple diagnostic routes
            @app.route('/admin-direct')
            def admin_direct():
                """Direct route to admin dashboard as a fallback"""
                return redirect('/admin')
                
            logger.info("Simple admin interface created successfully")
            return admin
    except Exception as e:
        logger.error(f"Error creating simple admin interface: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None