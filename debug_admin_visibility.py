"""
Debug tool to check admin tab visibility in the account page.
This script provides a simplified environment to test admin tab activation.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, url_for, redirect, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('admin_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Simple Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'debug_secret_key')

# Fix for URL generation behind proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Mock user classes
class User(UserMixin):
    def __init__(self, id, email, is_admin=False):
        self.id = id
        self.email = email
        self.is_admin_value = is_admin
        logger.debug(f"Created User: {email}, Admin: {is_admin}")
    
    def get_balance_usd(self):
        return 100.00
    
    def is_admin(self):
        return self.is_admin_value

# Create test users
admin_user = User(1, 'admin@example.com', True)
regular_user = User(2, 'user@example.com', False)

# User storage
users = {
    '1': admin_user,
    '2': regular_user
}

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Loading user ID: {user_id}")
    return users.get(user_id)

# Simple route to login
@app.route('/login')
def login():
    user_type = request.args.get('type', 'admin')
    
    if user_type == 'admin':
        login_user(admin_user)
        flash('Logged in as admin user', 'success')
        logger.info(f"Logged in as admin user: {admin_user.email}")
    else:
        login_user(regular_user)
        flash('Logged in as regular user', 'success')
        logger.info(f"Logged in as regular user: {regular_user.email}")
    
    # Determine redirect target from request args
    target = request.args.get('target', 'default')
    if target == 'admin_tab':
        return redirect(url_for('test_admin_tab', tab='admin'))
    else:
        return redirect(url_for('test_admin_tab'))

# Route to test admin tab visibility
@app.route('/test-admin-tab')
@login_required
def test_admin_tab():
    """Test the admin tab with various URL parameters"""
    # Debugging info
    logger.info(f"User: {current_user.email}, Is Admin: {current_user.is_admin()}")
    logger.info(f"Request args: {dict(request.args)}")
    
    # Get tab parameter from URL
    tab = request.args.get('tab')
    logger.info(f"Tab parameter: {tab}")
    
    # Generate sample admin commissions for testing
    admin_commissions = []
    if current_user.is_admin():
        # Add some mock commissions for display testing
        admin_commissions = [
            {
                'id': 1,
                'affiliate': {'username': 'affiliate1', 'email': 'affiliate1@example.com'},
                'status': 'HELD',
                'amount_usd': 25.00,
                'created_at': datetime.utcnow(),
                'available_at': datetime.utcnow()
            },
            {
                'id': 2,
                'affiliate': {'username': 'affiliate2', 'email': 'affiliate2@example.com'},
                'status': 'APPROVED',
                'amount_usd': 15.50,
                'created_at': datetime.utcnow(),
                'available_at': datetime.utcnow()
            }
        ]
    
    # Render template with admin settings
    return render_template(
        'account.html',
        user=current_user,
        packages=[],
        recent_transactions=[],
        recent_usage=[],
        affiliate=None,
        commission_stats={},
        commissions=[],
        referrals=[],
        sub_referrals=[],
        stats={
            'total_affiliates': 25,
            'active_affiliates': 12,
            'pending_commissions': 10,
            'paid_commissions': 35
        },
        is_admin=current_user.is_admin(),
        admin_commissions=admin_commissions,
        now=datetime.utcnow()
    )

# API route to check admin tab status - useful for client-side debugging
@app.route('/api/check-admin-tab')
@login_required
def check_admin_tab():
    """
    API endpoint to check the status of admin variables and configurations.
    Helps with debugging any issues with admin tab visibility.
    """
    result = {
        'user_email': current_user.email,
        'is_admin': current_user.is_admin(),
        'request_args': dict(request.args),
        'url_path': request.path,
        'admin_tab_param': request.args.get('tab') == 'admin',
        'debug_info': {
            'admin_emails': os.environ.get('ADMIN_EMAILS', '')
        }
    }
    return jsonify(result)

# Information page about how to use this debugging tool
@app.route('/')
def index():
    """Information about how to use this debugging tool"""
    return """
    <html>
    <head>
        <title>Admin Tab Visibility Debug Tool</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            .link { display: block; margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 4px; text-decoration: none; color: #333; }
            .link:hover { background: #e9e9e9; }
            code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>Admin Tab Visibility Debug Tool</h1>
        <p>This tool helps test the admin tab visibility in various configurations.</p>
        
        <h2>Test Links:</h2>
        <a class="link" href="/login?type=admin">1. Login as Admin User</a>
        <a class="link" href="/login?type=regular">2. Login as Regular User</a>
        <a class="link" href="/login?type=admin&target=admin_tab">3. Login as Admin and Redirect to Admin Tab</a>
        <a class="link" href="/test-admin-tab?tab=admin">4. Access Account Page with tab=admin Parameter</a>
        <a class="link" href="/api/check-admin-tab">5. Check Admin Tab Configuration API</a>
        
        <h2>How to Use:</h2>
        <p>Use these links to test different user types and tab activation scenarios. Watch the browser console and server logs for debugging information.</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Set admin emails (can be overridden by environment variable)
    if 'ADMIN_EMAILS' not in os.environ:
        os.environ['ADMIN_EMAILS'] = 'admin@example.com,test@example.com'
    
    logger.info(f"Admin emails configured as: {os.environ.get('ADMIN_EMAILS')}")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)