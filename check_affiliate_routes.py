"""
Check if the simplified affiliate routes are properly registered
"""
import logging

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_routes():
    """Check if simplified affiliate routes are registered in app"""
    from app import app
    
    # Get all routes
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    
    # Check for affiliate routes
    affiliate_routes = [r for r in routes if r.startswith('/affiliate')]
    
    logger.info("=== SIMPLIFIED AFFILIATE ROUTES CHECK ===")
    logger.info(f"Total affiliate routes found: {len(affiliate_routes)}")
    
    if affiliate_routes:
        logger.info("\nAffiliate routes:")
        for route in sorted(affiliate_routes):
            logger.info(f"  {route}")
    else:
        logger.info("No affiliate routes found!")
    
    # Look for specific critical routes
    critical_routes = [
        '/affiliate/dashboard',
        '/affiliate/update_paypal_email', 
        '/affiliate/referral/<code>'
    ]
    
    logger.info("\nChecking critical routes:")
    for route in critical_routes:
        found = route in routes
        logger.info(f"  {route}: {'✓' if found else '✗'}")
    
    return affiliate_routes

if __name__ == "__main__":
    try:
        check_routes()
    except Exception as e:
        logger.error(f"Error checking routes: {e}")