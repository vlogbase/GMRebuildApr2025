"""
Simple script to test admin access and route configuration.
"""

import os
import sys
import logging
from flask_login import current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin_check.log')
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run a simple check of admin access and routes.
    """
    try:
        # Import the Flask app
        from app import app
        
        # Test route for checking admin access
        @app.route('/admin-test')
        def admin_test():
            """Test page for admin access"""
            if not current_user.is_authenticated:
                return '<h1>Not logged in</h1><p>Please log in to check admin access.</p>'
            
            admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
            is_admin = current_user.email in admin_emails
            
            # Get all admin routes
            admin_routes = [rule.rule for rule in app.url_map.iter_rules() if 'admin' in rule.rule]
            
            return f"""
            <h1>Admin Access Check</h1>
            <p>Logged in as: {current_user.email}</p>
            <p>Admin emails: {admin_emails}</p>
            <p>Is admin: {is_admin}</p>
            <p>Admin routes:</p>
            <ul>
                {' '.join(f'<li><a href="{route}">{route}</a></li>' for route in sorted(admin_routes))}
            </ul>
            <p><a href="/admin">Go to Admin Dashboard</a></p>
            """
        
        # Run the app
        logger.info("Starting Flask application for admin check")
        app.run(host='0.0.0.0', port=3000, debug=True)
        
    except Exception as e:
        logger.error(f"Error testing admin access: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    run()