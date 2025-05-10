"""
Simple script to run the Flask application with admin dashboard functionality.
"""
import logging
import os
from app import app, db
from gm_admin import create_admin

def run():
    """
    Run the application with admin dashboard functionality
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("admin_app.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Set environment variables
    if 'ADMIN_EMAILS' not in os.environ:
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
        logger.info(f"Set ADMIN_EMAILS to: {os.environ['ADMIN_EMAILS']}")
    
    # Initialize Flask-Admin if not already done
    try:
        # Log registered routes before creating admin
        logger.info("Routes before admin initialization:")
        admin_routes_before = [rule.rule for rule in app.url_map.iter_rules() if 'admin' in str(rule)]
        logger.info(f"Admin routes before: {admin_routes_before}")
        
        # Check if admin interface is already initialized
        if not hasattr(app, 'extensions') or 'admin' not in app.extensions:
            logger.info("Admin interface not initialized. Initializing now...")
            admin = create_admin(app, db)
            if admin:
                logger.info("Admin interface initialized successfully in admin_app.py")
            else:
                logger.error("Failed to initialize admin interface in admin_app.py")
        else:
            logger.info("Admin interface already initialized in app.py")
        
        # Log registered routes after admin initialization
        logger.info("Routes after admin initialization:")
        admin_routes_after = [rule.rule for rule in app.url_map.iter_rules() if 'admin' in str(rule)]
        logger.info(f"Admin routes after: {admin_routes_after}")
    except Exception as e:
        logger.error(f"Error initializing admin: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Run the app
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"Starting Flask application with admin on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    run()