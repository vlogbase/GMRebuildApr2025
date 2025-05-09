"""
Admin Factory Module for GloriaMundo Chatbot

This module creates an admin interface using a factory pattern to avoid
circular imports and ensure proper initialization.
"""

import os
import logging
from flask import redirect, url_for, request, abort
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

class SecureBaseView:
    """Base view with security features for all admin views"""
    def is_accessible(self):
        """Only allow access to admin users (email: andy@sentigral.com)"""
        if not current_user.is_authenticated:
            return False
        
        admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
        admin_emails = [email.strip() for email in admin_emails if email.strip()]
        
        return current_user.email in admin_emails
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login page if user doesn't have access"""
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return abort(403)  # Forbidden

class SecureAdminIndexView(AdminIndexView, SecureBaseView):
    """Secure index view for admin panel"""
    @expose('/')
    def index(self):
        """Admin dashboard home page with overview statistics"""
        logger.info("Rendering admin dashboard")
        
        # Access to models only after app context is available
        from models import User, Affiliate, Commission
        
        # Basic stats
        user_count = User.query.count()
        affiliate_count = Affiliate.query.count()
        commission_count = Commission.query.count()
        pending_commissions = Commission.query.filter_by(status='pending').count()
        
        return self.render('admin/index.html',
                        user_count=user_count,
                        affiliate_count=affiliate_count,
                        commission_count=commission_count,
                        pending_commissions=pending_commissions)

class UserModelView(ModelView, SecureBaseView):
    """User management view"""
    column_list = ['id', 'username', 'email', 'created_at']
    column_searchable_list = ['email', 'username']
    column_filters = ['created_at']
    column_default_sort = ('created_at', True)
    can_create = False  # Users are created through registration/Google Auth

class CommissionModelView(ModelView, SecureBaseView):
    """Commission management view"""
    column_list = [
        'id', 'affiliate.email', 'commission_level', 'purchase_amount_base', 
        'commission_amount', 'status', 'commission_earned_date', 
        'commission_available_date', 'payout_batch_id'
    ]
    
    def _get_affiliate_email(view, context, model, name):
        """Get the affiliate email for display"""
        if model.affiliate:
            return model.affiliate.email
        return "N/A"
    
    column_formatters = {
        'affiliate.email': _get_affiliate_email,
        'purchase_amount_base': lambda v, c, m, p: f'£{m.purchase_amount_base:.2f}',
        'commission_amount': lambda v, c, m, p: f'£{m.commission_amount:.2f}'
    }
    
    column_default_sort = ('commission_available_date', True)
    column_filters = ['status', 'commission_available_date', 'commission_level']
    can_create = False  # Commissions are created automatically
    can_edit = True     # Allow editing status
    
    def approve_commissions(self, ids):
        """Approve selected commissions"""
        from models import Commission
        from app import db
        
        try:
            for commission_id in ids:
                commission = Commission.query.get(commission_id)
                if commission and commission.status == 'pending':
                    commission.status = 'approved'
                    commission.commission_available_date = func.now()
            
            db.session.commit()
            logger.info(f"Approved {len(ids)} commissions")
            return True
        except Exception as e:
            logger.error(f"Error approving commissions: {str(e)}")
            db.session.rollback()
            return False

class AffiliateModelView(ModelView, SecureBaseView):
    """Affiliate management view"""
    column_list = [
        'id', 'name', 'email', 'paypal_email', 'referral_code', 
        'status', 'terms_agreed_at', 'created_at'
    ]
    
    column_filters = ['status', 'created_at']
    column_searchable_list = ['email', 'paypal_email']
    column_default_sort = ('created_at', True)

def create_admin(app, db):
    """
    Create and initialize the admin interface for the application.
    
    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
    
    Returns:
        Admin: The initialized Flask-Admin instance
    """
    # Import models only after app context is established
    with app.app_context():
        from models import User, Affiliate, Commission, Usage
        
        # Create admin instance
        admin = Admin(
            app, 
            name='GloriaMundo Admin',
            template_mode='bootstrap3',
            index_view=SecureAdminIndexView(name='Dashboard', url='/admin'),
            base_template='admin/master.html'
        )
        
        # Add views
        admin.add_view(UserModelView(User, db.session, name='Users', category='Users'))
        admin.add_view(AffiliateModelView(Affiliate, db.session, name='Affiliates', category='Affiliates'))
        admin.add_view(CommissionModelView(Commission, db.session, name='Commissions', category='Affiliates'))
        
        # Simple diagnostic routes
        @app.route('/admin-home')
        def admin_home():
            """Admin home page that checks access"""
            if current_user.is_authenticated:
                admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
                is_admin = current_user.email in admin_emails
                if is_admin:
                    return redirect('/admin')
                return f'Access denied. {current_user.email} is not an admin. Admin users: {admin_emails}'
            return 'Please log in to access the admin dashboard'
        
        @app.route('/admin-check')
        def admin_check():
            """Diagnostic page to check admin access"""
            if not current_user.is_authenticated:
                return '<h1>Not logged in</h1><p>Please log in to check admin access.</p>'
            
            admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
            is_admin = current_user.email in admin_emails
            
            return f"""
            <h1>Admin Check</h1>
            <p>Logged in as: {current_user.email}</p>
            <p>Admin emails: {admin_emails}</p>
            <p>Is admin: {is_admin}</p>
            <p><a href="/admin">Admin Dashboard</a></p>
            """
        
        @app.route('/admin-direct')
        def admin_direct():
            """Direct route to admin dashboard as a fallback"""
            return redirect('/admin')
            
        logger.info("Admin interface created successfully")
        return admin