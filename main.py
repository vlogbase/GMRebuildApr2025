"""
Main entry point for the GloriaMundo Chatbot application.
This file imports the app instance from app.py and serves as the entry point for WSGI servers.
"""
import os
import logging
from app import app  # noqa: F401

# Configure logging for admin functionality
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler(filename='admin.log')  # Log to file
    ]
)

logger = logging.getLogger(__name__)

# Add admin route verification
@app.route('/admin-status')
def admin_status():
    """
    Simple endpoint to verify admin routes are registered
    """
    admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com')
    admin_routes = [rule.rule for rule in app.url_map.iter_rules() 
                   if rule.rule.startswith('/admin')]
    
    return {
        'status': 'ok',
        'admin_routes': admin_routes,
        'admin_emails': admin_emails,
        'admin_accessible': True
    }

# This file is used by WSGI servers (gunicorn) to find the app instance.
# The actual application logic is in app.py.

if __name__ == "__main__":
    # Log admin configuration on startup
    logger.info(f"Starting GloriaMundo with admin access for: {os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com')}")
    
    # Run the Flask development server when executed directly
    app.run(host="0.0.0.0", port=3000, debug=True)