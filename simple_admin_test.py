"""
Simple script to test the Flask-Admin integration.
"""
import os
import logging
import sys
from flask import Flask, flash, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin_test.log')
    ]
)

logger = logging.getLogger(__name__)

# Set admin email
os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
logger.info(f"Admin emails: {os.environ.get('ADMIN_EMAILS')}")

# Create app and database classes
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Setup login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Security functions
def is_admin():
    """Check if the current user is an admin"""
    if not current_user.is_authenticated:
        return False
    
    # Get admin emails from environment
    admin_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
    admin_emails = [email.strip() for email in admin_emails]
    
    return current_user.email in admin_emails

class SecureBaseView:
    """Base view with security features for all admin views"""
    def is_accessible(self):
        """Only allow access to admin users"""
        return current_user.is_authenticated and is_admin()

    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login page if user doesn't have access"""
        flash('You do not have permission to access the admin area.', 'error')
        return redirect(url_for('index'))

class SecureAdminIndexView(AdminIndexView, SecureBaseView):
    """Secure index view for admin panel"""
    @expose('/')
    def index(self):
        """Admin dashboard home page"""
        return self.render('admin/index.html')

# Create admin interface
admin = Admin(
    app, 
    name='GloriaMundo Admin', 
    url='/gm-admin',
    endpoint='gm_admin',
    template_mode='bootstrap3',
    index_view=SecureAdminIndexView(name='Dashboard')
)

# Route for basic pages
@app.route('/')
def index():
    return "Welcome to GloriaMundo. <a href='/admin'>Admin</a>"

@app.route('/login')
def login():
    return "Login page. <a href='/'>Home</a>"

@app.route('/admin')
@login_required
def admin_index():
    """Redirect to admin dashboard"""
    if not is_admin():
        flash('You do not have permission to access the admin area.', 'error')
        return redirect(url_for('index'))
    return redirect(url_for('gm_admin.index'))

# Start the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)