"""
Simple script to check admin blueprint configuration.
"""
import os
import logging
from app import app
from flask import url_for

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """Check admin blueprint configuration"""
    admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com')
    logger.info(f"Admin access configured for: {admin_emails}")
    
    # Get all routes
    with app.test_request_context():
        all_routes = {}
        for rule in app.url_map.iter_rules():
            try:
                all_routes[rule.endpoint] = {
                    'methods': list(rule.methods),
                    'rule': rule.rule
                }
            except Exception as e:
                logger.error(f"Error processing route {rule}: {e}")
        
        # Find admin routes
        admin_routes = {endpoint: route for endpoint, route in all_routes.items() 
                      if 'admin' in endpoint.lower() or 'admin' in route['rule'].lower()}
        
        logger.info("======= ADMIN ROUTES =======")
        for endpoint, route in admin_routes.items():
            logger.info(f"Endpoint: {endpoint}")
            logger.info(f"  URL: {route['rule']}")
            logger.info(f"  Methods: {', '.join(route['methods'])}")
        
    return admin_routes
    
if __name__ == "__main__":
    run()