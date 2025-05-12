"""
Admin Portal Workflow for GloriaMundo

This workflow runs the Flask application with the admin interface.
"""

import os
import sys
import logging
import traceback
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_app_context():
    """
    Push the application context if needed, ensuring database operations work correctly
    """
    try:
        from app import app
        if not app.app_context():
            app.app_context().push()
            logger.info("Application context pushed")
    except Exception as e:
        logger.error(f"Error pushing application context: {e}")

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        # Set environment variables
        os.environ['ADMIN_EMAIL'] = 'andy@sentigral.com'
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        
        # Ensure we're in the correct directory
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        
        # Import after setting environment variables
        from app import app
        
        # Apply the ProxyFix to make url_for generate https URLs
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
        
        # Ensure we have an app context for database operations
        ensure_app_context()
        
        # Log route information
        logger.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.info(f"  {rule.endpoint} - {rule.rule}")
        
        # Run the app
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting Flask application with admin interface on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    run()