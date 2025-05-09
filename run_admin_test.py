"""
Direct runner script for admin dashboard testing
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Setting up admin environment variables")
        
        # Set environment variables
        os.environ['FLASK_ENV'] = 'development'
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
        
        # Print debug information
        logger.info(f"ADMIN_EMAILS set to: {os.environ['ADMIN_EMAILS']}")
        logger.info(f"FLASK_ENV set to: {os.environ['FLASK_ENV']}")
        
        # Import and run the Flask application
        logger.info("Starting Flask application with admin access")
        import app
        from affiliate import is_admin
        
        # Log admin status check available in this context
        current_user_email = getattr(getattr(app, 'current_user', None), 'email', 'No user')
        logger.info(f"Current user email: {current_user_email}")
        logger.info(f"Admin check function result would be: {is_admin()}")
        
        # Create debug routes
        @app.app.route('/admin-debug')
        def admin_debug():
            """Debug endpoint for admin access"""
            from flask import jsonify
            from flask_login import current_user
            
            # Check admin status
            admin_status = is_admin()
            
            # Return debug information
            return jsonify({
                'admin_check': admin_status,
                'authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
                'user_email': current_user.email if hasattr(current_user, 'email') else 'Not authenticated',
                'admin_emails': os.environ.get('ADMIN_EMAILS', 'Not set'),
                'time': datetime.utcnow().isoformat()
            })
        
        # Run the app
        app.app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)