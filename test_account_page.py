"""
Script to test the account page rendering with admin tab
"""

import os
import sys
import logging
from app import app, db
from auth_utils import is_admin

# Configure logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_account_page():
    """Test if account page renders properly with admin tab"""
    try:
        # Set admin emails
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com,test@example.com'
        logger.info(f"ADMIN_EMAILS set to: {os.environ.get('ADMIN_EMAILS')}")
        
        # Create a test client
        client = app.test_client()
        app.config['SERVER_NAME'] = 'example.com'
        app.config['TESTING'] = True
        
        # Run in an application context
        with app.app_context():
            # Create a test request context
            with app.test_request_context():
                # Import here to avoid circular imports
                from flask import render_template
                from flask_login import login_user
                from models import User
                
                # Create or get test admin user
                admin_user = User.query.filter_by(email='andy@sentigral.com').first()
                if not admin_user:
                    logger.info("Admin user not found, creating mock user")
                    # Create a minimal mock user for testing
                    class MockUser:
                        id = 999
                        email = 'andy@sentigral.com'
                        is_authenticated = True
                        is_active = True
                        def get_id(self):
                            return str(self.id)
                        def get_balance_usd(self):
                            return 100.00
                    admin_user = MockUser()
                
                # Login the admin user
                login_user(admin_user)
                logger.info(f"Logged in as: {admin_user.email}")
                
                # Test if admin check works
                admin_status = is_admin()
                logger.info(f"Admin check result: {admin_status}")
                
                try:
                    # Try to render a simplified template
                    test_template = """
                    {% if is_admin %}
                        {% set active_affiliates = namespace(count=0, ids=[]) %}
                        {% for i in range(3) %}
                            {% if i > 0 %}
                                {% set active_affiliates.count = active_affiliates.count + 1 %}
                                {% set _ = active_affiliates.ids.append(i) %}
                            {% endif %}
                        {% endfor %}
                        Admin Access: Yes
                        Count: {{ active_affiliates.count }}
                    {% else %}
                        Admin Access: No
                    {% endif %}
                    """
                    
                    # Render the test template
                    from flask import render_template_string
                    result = render_template_string(test_template, is_admin=admin_status)
                    logger.info("Test template rendered successfully")
                    logger.info(f"Result: {result.strip()}")
                    
                    # Now, try to render the billing.account_management route
                    logger.info("Attempting to render account management page...")
                    from billing import account_management
                    
                    # Call the account_management function directly
                    try:
                        response = account_management()
                        logger.info("Account management page rendered successfully")
                        return True
                    except Exception as e:
                        logger.error(f"Error rendering account management page: {e}")
                        
                        # Debug more information
                        if "Jinja" in str(e):
                            logger.error(f"Jinja template error details: {str(e)}")
                            
                        return False
                    
                except Exception as e:
                    logger.error(f"Error rendering test template: {e}")
                    return False
    
    except Exception as e:
        logger.error(f"Overall testing error: {e}")
        return False

if __name__ == "__main__":
    with app.app_context():
        success = test_account_page()
        if success:
            print("Test completed successfully")
            sys.exit(0)
        else:
            print("Test failed")
            sys.exit(1)