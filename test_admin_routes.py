"""
Quick test script to check if admin routes are correctly registered in Flask.
"""

from app import app

if __name__ == "__main__":
    print("Checking Flask routes...")
    print("-" * 50)
    
    admin_routes = []
    other_routes = []
    
    # Get all the registered routes
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        url = str(rule)
        
        # Check if it's an admin route
        if 'gm_admin' in endpoint or 'admin' in url:
            admin_routes.append((url, endpoint))
        else:
            other_routes.append((url, endpoint))
    
    # Print admin routes
    print(f"Found {len(admin_routes)} admin-related routes:")
    for url, endpoint in sorted(admin_routes):
        print(f"URL: {url:<40} Endpoint: {endpoint}")
    
    # Print number of other routes
    print(f"\nFound {len(other_routes)} other routes (not showing them all)")
    print("Sample of other routes:")
    for url, endpoint in sorted(other_routes)[:5]:
        print(f"URL: {url:<40} Endpoint: {endpoint}")
    
    # Specific check for /gm-admin route
    gm_admin_found = any('/gm-admin' in url for url, _ in admin_routes)
    print("\nSpecific check:")
    print(f"/gm-admin route found: {'Yes' if gm_admin_found else 'No'}")
    
    # Check if admin was initialized
    print("\nChecking if admin module was initialized...")
    try:
        from flask_admin import Admin
        admin_instances = [v for v in app.extensions.values() if isinstance(v, Admin)]
        if admin_instances:
            admin = admin_instances[0]
            print(f"Admin instance found: {admin.name} at URL {admin.url}")
            print(f"Admin views registered: {len(admin._views)}")
            for view in admin._views:
                print(f" - {view.name} (endpoint: {view.endpoint})")
        else:
            print("No Flask-Admin instances found in app.extensions")
    except Exception as e:
        print(f"Error checking admin initialization: {e}")