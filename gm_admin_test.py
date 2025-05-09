"""
Test script for directly checking admin routes
"""

import logging
import sys
import os
from flask import Flask, render_template, redirect, url_for, request, abort, flash
from flask_login import LoginManager, current_user, login_required
from models import User, Commission, Affiliate, Usage
from admin_blueprint import admin_blueprint
from admin_routes import admin_routes, admin_required, is_admin
from admin_factory import create_admin, SecureAdminIndexView

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gm_admin.log')
    ]
)
logger = logging.getLogger(__name__)

# Set environment variable for admin access (for testing)
if 'ADMIN_EMAILS' not in os.environ:
    os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
    logger.info(f"Set ADMIN_EMAILS environment variable to: {os.environ['ADMIN_EMAILS']}")

# Mini Flask app for testing admin routes
app = Flask(__name__)
app.secret_key = 'admin-test-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register the admin blueprint
app.register_blueprint(admin_blueprint, url_prefix='/admin')
app.register_blueprint(admin_routes, url_prefix='/admin-routes')

# Add a direct route for testing
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin-check')
def admin_check():
    """Simple check for admin access"""
    admin_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
    admin_emails = [email.strip() for email in admin_emails if email.strip()]
    
    is_admin_user = False
    if current_user.is_authenticated:
        is_admin_user = current_user.email in admin_emails
    
    return render_template(
        'admin/check.html',
        user_email=current_user.email if current_user.is_authenticated else 'Not logged in',
        admin_emails=admin_emails,
        is_admin=is_admin_user
    )

@app.route('/login-test')
def login_test():
    """Test login page"""
    return render_template('login.html')

# Create the admin interface
admin = create_admin(app, None)  # Pass None for db since we're just testing routes

if __name__ == '__main__':
    # Print diagnostic information
    logger.info(f"Admin access configured for: {os.environ.get('ADMIN_EMAILS', 'None configured')}")
    logger.info(f"Admin routes should be accessible at various prefixes")
    
    # Log all registered routes for debugging
    logger.info("Registered routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
        logger.info(f"Route: {rule.rule} Methods: {rule.methods}")
    
    # Run the app
    app.run(host='0.0.0.0', port=3000, debug=True)