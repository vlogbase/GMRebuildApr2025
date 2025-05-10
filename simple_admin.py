"""
Simple standalone Flask-Admin application for GloriaMundo.
Designed to be a minimal self-contained admin dashboard to avoid 
dependencies on the main app's complex initialization.
"""
import os
import logging
from flask import Flask, redirect, url_for, request, abort
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required
from sqlalchemy import func, desc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_admin.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Define base model class
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __str__(self):
        return self.username or self.email

class Affiliate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(120))
    paypal_email = db.Column(db.String(120))
    referral_code = db.Column(db.String(20))
    status = db.Column(db.String(20))
    terms_agreed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __str__(self):
        return self.name or self.email

class Commission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id'))
    commission_level = db.Column(db.Integer)
    purchase_amount_base = db.Column(db.Float)
    commission_amount = db.Column(db.Float)
    status = db.Column(db.String(20))
    commission_earned_date = db.Column(db.DateTime)
    commission_available_date = db.Column(db.DateTime)
    payout_batch_id = db.Column(db.String(64))
    
    affiliate = db.relationship('Affiliate', backref='commissions')

# Admin views
class SecureBaseView:
    """Base view with security features for all admin views"""
    def is_accessible(self):
        """Only allow access to admin users (email: andy@sentigral.com)"""
        if not current_user.is_authenticated:
            return False
        
        admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
        admin_emails = [email.strip() for email in admin_emails if email.strip()]
        
        logger.info(f"Checking admin access for {current_user.email}")
        logger.info(f"Admin emails: {admin_emails}")
        
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
        
        with app.app_context():
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
        
        return self.render('admin/index.html',
                          user_count=user_count,
                          affiliate_count=affiliate_count,
                          commission_count=commission_count,
                          pending_commissions=pending_commissions,
                          approved_commissions=approved_commissions,
                          paid_commissions=paid_commissions,
                          rejected_commissions=rejected_commissions,
                          total_pending=total_pending,
                          total_approved=total_approved,
                          total_paid=total_paid)

class UserModelView(ModelView, SecureBaseView):
    """User management view"""
    column_list = ['id', 'username', 'email', 'created_at']
    column_searchable_list = ['email', 'username']
    column_filters = ['created_at']
    column_default_sort = ('created_at', True)
    can_create = False  # Users are created through registration/OAuth
    can_edit = True     # Allow editing for account management

class AffiliateModelView(ModelView, SecureBaseView):
    """Affiliate management view"""
    column_list = [
        'id', 'name', 'email', 'paypal_email', 'referral_code', 
        'status', 'terms_agreed_at', 'created_at'
    ]
    column_filters = ['status', 'created_at']
    column_searchable_list = ['email', 'paypal_email']
    column_default_sort = ('created_at', True)
    can_create = False  # Affiliates are created through registration
    can_edit = True     # Allow editing of affiliate details

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
    can_create = False  # Commissions are created through the affiliate system
    can_edit = True     # Allow editing of status and other fields

# Flask routes
@app.route('/')
def index():
    return redirect(url_for('admin.index'))

@app.route('/login')
def login():
    # Create a test admin user if it doesn't exist
    with app.app_context():
        admin_user = User.query.filter_by(email='andy@sentigral.com').first()
        if not admin_user:
            admin_user = User(username='Andy Admin', email='andy@sentigral.com')
            db.session.add(admin_user)
            db.session.commit()
            logger.info("Created admin user")
        
        # Log in as admin user for testing
        login_user(admin_user)
        logger.info(f"Logged in as {admin_user.email}")
        
        next_url = request.args.get('next', '/')
        return redirect(next_url)

@app.route('/admin-check')
@login_required
def admin_check():
    """Check admin access"""
    admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
    is_admin = current_user.email in admin_emails
    
    return f"""
    <h1>Admin Check</h1>
    <p>Logged in as: {current_user.email}</p>
    <p>Admin emails: {admin_emails}</p>
    <p>Is admin: {is_admin}</p>
    <p><a href="/admin">Admin Dashboard</a></p>
    """

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    return User.query.get(int(user_id))

# Initialize app
def create_admin():
    # Initialize the Flask-Admin instance
    admin = Admin(
        app,
        name='GloriaMundo Admin',
        template_mode='bootstrap3',
        index_view=SecureAdminIndexView(name='Dashboard', url='/admin')
        # No base_template parameter
    )
    
    # Add ModelViews
    admin.add_view(UserModelView(User, db.session, name='Users', endpoint='admin_users'))
    admin.add_view(AffiliateModelView(Affiliate, db.session, name='Affiliates', endpoint='admin_affiliates'))
    admin.add_view(CommissionModelView(Commission, db.session, name='Commissions', endpoint='admin_commissions'))
    
    logger.info("Admin interface created successfully")
    return admin

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Create admin
    admin = create_admin()
    
    # Log routes
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        if 'admin' in str(rule):
            logger.info(f" - {rule.rule} (endpoint: {rule.endpoint})")
    
    # Run app
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"Starting admin app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)