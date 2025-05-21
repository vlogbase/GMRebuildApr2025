"""
Simple script to check if affiliate routes are properly registered
"""

import logging
from app import app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Check affiliate routes in the application"""
    print("Checking registered routes in the application...")
    
    # Get all routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
            'path': str(rule)
        })
    
    # Filter for affiliate routes
    affiliate_routes = [r for r in routes if r['endpoint'].startswith('affiliate.')]
    
    print(f"\nFound {len(affiliate_routes)} affiliate routes:")
    for route in affiliate_routes:
        print(f"  {route['endpoint']} - {route['path']} ({', '.join(route['methods'])})")
    
    # Specifically check for update_paypal_email route
    paypal_routes = [r for r in routes if 'paypal' in r['endpoint'].lower()]
    
    if paypal_routes:
        print("\nFound PayPal-related routes:")
        for route in paypal_routes:
            print(f"  {route['endpoint']} - {route['path']} ({', '.join(route['methods'])})")
    else:
        print("\nNo PayPal-related routes found!")
        
if __name__ == "__main__":
    main()