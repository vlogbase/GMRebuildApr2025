"""
Minimal Flask-Admin implementation to test core functionality
"""
import os
import logging
from flask import Flask, redirect, url_for, request, abort
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, UserMixin, current_user, login_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
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
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    def __str__(self):
        return self.username

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
        return self.render('admin/index.html')

class UserModelView(ModelView, SecureBaseView):
    """User management view"""
    column_list = ['id', 'username', 'email', 'created_at']
    column_searchable_list = ['email', 'username']
    column_filters = ['created_at']
    column_default_sort = ('created_at', True)
    can_create = False  # Users are created through registration/OAuth
    can_edit = True     # Allow editing for account management

class AnalyticsView(BaseView, SecureBaseView):
    """Simple analytics view"""
    @expose('/')
    def index(self):
        """Show basic analytics"""
        return self.render('admin/analytics.html')

# Flask routes
@app.route('/')
def index():
    return 'Welcome to the minimal admin test app. <a href="/admin/">Admin Dashboard</a>'

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

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    return User.query.get(int(user_id))

# Create admin interface
def create_admin():
    # Initialize the Flask-Admin instance
    admin = Admin(
        app,
        name='GloriaMundo Admin',
        template_mode='bootstrap3',
        index_view=SecureAdminIndexView(name='Dashboard', url='/admin'),
        base_template='admin/bootstrap3/layout.html'  # Use actual base template
    )
    
    # Add views
    admin.add_view(UserModelView(User, db.session, name='Users'))
    admin.add_view(AnalyticsView(name='Analytics', endpoint='analytics'))
    
    return admin

# Initialize app (using Flask 2.0+ approach)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Create admin interface
    admin = create_admin()
    
    # Check admin routes
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        if 'admin' in str(rule):
            logger.info(f" - {rule.rule} (endpoint: {rule.endpoint})")
    
    # Run app
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"Starting minimal admin app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)