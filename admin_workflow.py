"""
Simple script to run the admin dashboard for testing.
"""
import logging
import os
from app import app

def run():
    """
    Run the application with admin dashboard for testing purposes
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("admin.log"),
            logging.StreamHandler()
        ]
    )
    
    # Log the state of key environment variables
    admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com')
    logging.info(f"Admin emails: {admin_emails}")
    
    # Log the registered routes
    logging.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        if 'admin' in str(rule):
            logging.info(f" - {rule.rule} (endpoint: {rule.endpoint})")
    
    # Run the app
    port = int(os.environ.get('PORT', 3000))
    logging.info(f"Starting admin dashboard on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    run()