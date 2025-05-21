"""
Verify that affiliate routes are properly registered
"""

from app import app
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_routes():
    """Check all registered routes in the application"""
    print("Checking registered routes...")
    
    # Get all routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': rule.methods,
            'path': str(rule)
        })
    
    # Sort routes by endpoint
    routes.sort(key=lambda x: x['endpoint'])
    
    # Check for affiliate routes
    affiliate_routes = [r for r in routes if r['endpoint'].startswith('affiliate.')]
    
    print(f"Found {len(affiliate_routes)} affiliate routes:")
    for route in affiliate_routes:
        print(f"  {route['endpoint']} - {route['path']} ({', '.join(sorted(route['methods'] - {'HEAD', 'OPTIONS'}))})")
    
    # Specifically check for update_paypal_email route
    paypal_routes = [r for r in routes if 'paypal' in r['endpoint'].lower()]
    
    if paypal_routes:
        print("\nFound PayPal-related routes:")
        for route in paypal_routes:
            print(f"  {route['endpoint']} - {route['path']} ({', '.join(sorted(route['methods'] - {'HEAD', 'OPTIONS'}))})")
    else:
        print("\nNo PayPal-related routes found!")

if __name__ == "__main__":
    check_routes()