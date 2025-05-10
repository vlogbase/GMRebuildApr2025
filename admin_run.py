"""
Simple script to run the admin dashboard for testing.
"""
import os
import logging
from app import app

logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])

logger = logging.getLogger(__name__)

def run():
    """
    Run the application with admin dashboard functionality
    """
    # Set admin email to ensure access control is properly configured
    os.environ['ADMIN_EMAILS'] = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com')
    
    # Log admin configuration
    logger.info(f"Starting admin dashboard with access for: {os.environ['ADMIN_EMAILS']}")
    
    # List available admin routes
    admin_routes = [rule.rule for rule in app.url_map.iter_rules() 
                   if rule.rule.startswith('/admin')]
    logger.info(f"Admin routes: {admin_routes}")
    
    # Run the application
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"Starting admin server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    run()