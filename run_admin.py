"""
Run the Flask admin interface directly
"""
import os
import logging
import sys
from flask import Flask, redirect, url_for, request, abort
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, func, desc
from datetime import datetime

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'admin-development-secret-key')

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin.log')
    ]
)
logger = logging.getLogger(__name__)


# Import models
from models import User, Affiliate, Commission, Usage

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin access check
def is_admin():
    """Check if the current user is an admin"""
    if not current_user.is_authenticated:
        return False
    
    admin_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
    admin_emails = [email.strip() for email in admin_emails if email.strip()]
    
    return current_user.email in admin_emails

# Base view with security features
class SecureBaseView:
    """Base view with security features for all admin views"""
    def is_accessible(self):
        """Only allow access to admin users"""
        return is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login page if user doesn't have access"""
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return abort(403)  # Forbidden

# Secure index view
class SecureAdminIndexView(AdminIndexView, SecureBaseView):
    """Secure index view for admin panel"""
    @expose('/')
    def index(self):
        """Admin dashboard home page with overview statistics"""
        logger.info("Rendering admin dashboard")
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

# Commission model view
class CommissionModelView(ModelView, SecureBaseView):
    """Commission management view"""
    column_list = [
        'id', 'affiliate_id', 'commission_level', 'purchase_amount_base', 
        'commission_amount', 'status', 'commission_earned_date', 
        'commission_available_date', 'payout_batch_id'
    ]
    
    column_formatters = {
        'purchase_amount_base': lambda v, c, m, p: f'£{m.purchase_amount_base:.2f}',
        'commission_amount': lambda v, c, m, p: f'£{m.commission_amount:.2f}'
    }
    
    column_default_sort = ('commission_available_date', True)
    column_filters = ['status', 'commission_available_date', 'commission_level']
    
    can_create = False  # Commissions are created automatically
    can_edit = True     # Allow editing status

# Affiliate model view
class AffiliateModelView(ModelView, SecureBaseView):
    """Affiliate management view"""
    column_list = [
        'id', 'name', 'email', 'paypal_email', 'referral_code', 
        'status', 'terms_agreed_at', 'created_at'
    ]
    
    column_filters = ['status', 'created_at']
    column_searchable_list = ['email', 'paypal_email']
    column_default_sort = ('created_at', True)

# User model view
class UserModelView(ModelView, SecureBaseView):
    """User management view"""
    column_list = ['id', 'username', 'email', 'created_at']
    column_searchable_list = ['email', 'username']
    column_filters = ['created_at']
    column_default_sort = ('created_at', True)
    can_create = False  # Users are created through registration/Google Auth

# Initialize Flask-Admin
admin = Admin(
    app, 
    name='GloriaMundo Admin',
    template_mode='bootstrap3',
    index_view=SecureAdminIndexView(name='Dashboard', url='/admin'),
    base_template='admin/master.html'
)

# Add model views
admin.add_view(UserModelView(User, db.session, name='Users', category='Users'))
admin.add_view(AffiliateModelView(Affiliate, db.session, name='Affiliates', category='Affiliates'))
admin.add_view(CommissionModelView(Commission, db.session, name='Commissions', category='Affiliates'))

# Simple routes for testing
@app.route('/')
def index():
    """Home page redirect to admin"""
    if is_admin():
        return redirect('/admin')
    return '<h1>Welcome to GloriaMundo Admin</h1><p>Please <a href="/login">log in</a> to access the admin dashboard.</p>'

@app.route('/login')
def login():
    """Placeholder login page"""
    return '<h1>Login Page</h1><p>This is a placeholder. The actual login functionality is in the main app.</p>'

@app.route('/admin-check')
def admin_check():
    """Simple check for admin access"""
    if not current_user.is_authenticated:
        return '<h1>Not logged in</h1><p>Please log in to check admin access.</p>'
    
    admin_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
    admin_emails = [email.strip() for email in admin_emails if email.strip()]
    
    html = f"""
    <h1>Admin Check</h1>
    <p>Logged in as: {current_user.email}</p>
    <p>Admin emails: {admin_emails}</p>
    <p>Is admin: {current_user.email in admin_emails}</p>
    <p><a href="/admin">Go to Admin Dashboard</a></p>
    """
    return html

if __name__ == '__main__':
    # Set environment variable for admin access (for testing)
    if 'ADMIN_EMAILS' not in os.environ:
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
        logger.info(f"Set ADMIN_EMAILS environment variable to: {os.environ['ADMIN_EMAILS']}")
    
    # Log all registered routes for debugging
    logger.info("Registered routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
        logger.info(f"Route: {rule.rule} Methods: {rule.methods}")
    
    # Run the app
    logger.info("Starting Flask application with admin interface")
    app.run(host='0.0.0.0', port=3000, debug=True)