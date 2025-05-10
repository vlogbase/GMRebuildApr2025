"""
Simple script to test the admin functionality.
"""
import logging
import os
from app import app

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure admin emails are set
    if 'ADMIN_EMAILS' not in os.environ:
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
        print(f"Set ADMIN_EMAILS to: {os.environ['ADMIN_EMAILS']}")
    
    # Log available routes
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        if 'admin' in str(rule):
            print(f" - {rule.rule} (endpoint: {rule.endpoint})")
    
    # Set port from environment
    port = int(os.environ.get('PORT', 3000))
    print(f"Starting server on port {port}")
    
    # Run the app with debug mode
    app.run(host='0.0.0.0', port=port, debug=True)