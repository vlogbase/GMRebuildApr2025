"""
Simple script to run the Flask application with admin dashboard functionality.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Main execution function
def run():
    try:
        # Set admin emails environment variable if not already set
        if 'ADMIN_EMAILS' not in os.environ:
            os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
            logger.info(f"Set ADMIN_EMAILS environment variable to: {os.environ['ADMIN_EMAILS']}")
        
        # Import the Flask app and db
        from app import app, db
        
        # Import and initialize the admin interface
        from simple_admin import create_admin
        
        # Create and initialize the admin interface
        logger.info("Initializing Flask-Admin interface from simple_admin.py")
        admin = create_admin(app, db)
        
        # Log successful initialization
        if admin:
            logger.info("Flask-Admin interface successfully initialized")
            
            # List all registered routes for diagnostics
            admin_routes = [rule.rule for rule in app.url_map.iter_rules() if 'admin' in rule.rule]
            logger.info(f"Registered admin routes: {admin_routes}")
        else:
            logger.error("Flask-Admin initialization returned None")
        
        # Get the port from environment or use 3000 for deployment
        port = int(os.environ.get('PORT', 3000))
        
        # Run the app
        logger.info(f"Starting Flask application with admin interface on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application with admin: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run()