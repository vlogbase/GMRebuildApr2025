"""
Simple test script to verify affiliate routes
"""

from flask import Flask

print("Creating test app")
app = Flask(__name__)

# Import and register the affiliate blueprint
from affiliate_blueprint_fix import init_app
init_app(app)

print("\nRoutes registered:")
affiliate_routes = []
for rule in app.url_map.iter_rules():
    if 'affiliate' in rule.endpoint:
        affiliate_routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
            'path': str(rule)
        })

# Display routes sorted by endpoint
for route in sorted(affiliate_routes, key=lambda x: x['endpoint']):
    print(f"  {route['endpoint']} - {route['path']} ({', '.join(route['methods'])})")

# Check specifically for PayPal-related routes
print("\nPayPal-related routes:")
for route in affiliate_routes:
    if 'paypal' in route['endpoint'].lower():
        print(f"  {route['endpoint']} - {route['path']} ({', '.join(route['methods'])})")

print("\nDone.")