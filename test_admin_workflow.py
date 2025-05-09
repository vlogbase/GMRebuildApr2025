"""
Simple script to run the Flask application with admin access enabled.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
log_file = f"admin_test.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with admin access enabled.
    """
    logger.info("Starting Flask application with admin access...")
    
    # Ensure admin credentials are set
    os.environ['ADMIN_EMAILS'] = 'test@example.com,andy@sentigral.com'
    logger.info(f"Admin emails set to: {os.environ.get('ADMIN_EMAILS')}")

    # Set server host and port
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Run the Flask app with admin access enabled
    from app import app
    
    # Set up routes that don't require login for testing
    from flask import render_template, request
    
    @app.route('/test-admin-tab')
    def test_admin_tab():
        """Test page for checking admin tab rendering."""
        from models import User, Affiliate, Commission
        from billing import account_management
        
        # Get admin commissions
        admin_commissions = Commission.query.filter(
            Commission.status.in_(['held', 'approved', 'rejected'])
        ).all()
        
        # Render a test version of the page with admin content
        return render_template(
            'account.html',
            is_admin=True,
            admin_commissions=admin_commissions,
            now=datetime.now()
        )
    
    logger.info("Starting Flask app on http://0.0.0.0:5000/test-admin-tab")
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    run()