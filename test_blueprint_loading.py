"""
Test script to verify which affiliate blueprint is actually being loaded
"""

import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_blueprints():
    """Check which affiliate blueprint version is being loaded"""
    try:
        # Import the app
        from app import app
        
        # Check the registered blueprints
        for blueprint_name, blueprint in app.blueprints.items():
            logger.info(f"Blueprint: {blueprint_name} - {blueprint}")
            
            # If it's the affiliate blueprint, examine its routes
            if blueprint_name == 'affiliate':
                logger.info("Found affiliate blueprint, checking its view functions:")
                for rule in app.url_map.iter_rules():
                    if rule.endpoint.startswith('affiliate.'):
                        logger.info(f"  Route: {rule}, Endpoint: {rule.endpoint}")
                
                # Try to check the source file of a route function
                update_paypal_route = app.view_functions.get('affiliate.update_paypal_email')
                if update_paypal_route:
                    logger.info(f"PayPal update route: {update_paypal_route.__module__}.{update_paypal_route.__name__}")
                    logger.info(f"Function located in: {update_paypal_route.__code__.co_filename}")
                else:
                    logger.warning("Could not find affiliate.update_paypal_email in view functions")
        
        return True
    except Exception as e:
        logger.error(f"Error testing blueprints: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    test_blueprints()