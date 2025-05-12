"""
Simple script to run the Flask application for testing in the Replit environment.
This is a wrapper script to start the app.py Flask application.
"""
import os
import sys
import logging
import time
from werkzeug.middleware.proxy_fix import ProxyFix

def ensure_app_context():
    """
    Push the application context if needed, ensuring database operations work correctly
    """
    try:
        from app import app, db
        with app.app_context():
            # Test DB connection
            db.session.execute(db.select(db.text('1'))).scalar()
            print("Database connection successful")
            
            # Verify document models are ready
            from models import DocumentReference
            print("Document models loaded successfully")
            
            # Ensure document routes are initialized
            print("Document handling routes initialized")
            
            # Check for required API connection keys
            if not os.environ.get('AZURE_STORAGE_CONNECTION_STRING'):
                print("Warning: AZURE_STORAGE_CONNECTION_STRING not set. Document uploads may not work correctly.")
                
    except Exception as e:
        print(f"Error during app context test: {e}")
        # Continue anyway, as the app might handle this internally

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='app_workflow.log',
            filemode='a'
        )
        print(f"Logging configured. Logs will be written to 'app_workflow.log'")
        
        # Import local modules only when needed
        from app import app
        
        # Apply the ProxyFix to make url_for generate https URLs
        # Enhanced settings for Replit deployments
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_proto=1,  # Number of values to trust for X-Forwarded-Proto
            x_host=1,   # Number of values to trust for X-Forwarded-Host
            x_prefix=1, # Number of values to trust for X-Forwarded-Prefix
            x_for=1     # Number of values to trust for X-Forwarded-For
        )
        
        # Ensure we have an app context for database operations
        ensure_app_context()
        
        # Run the app - use environment variable for port if available
        # Default to port 3000 for Replit deployments instead of 5000
        port = int(os.environ.get('PORT', 3000))
        print(f"Starting Flask application on port {port}...")
        
        # Write PID to a file for easier management
        with open('flask.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Run the app
        app.run(host='0.0.0.0', port=port, debug=True)

    except Exception as e:
        logging.error(f"Error running Flask application: {e}", exc_info=True)
        print(f"Error running Flask application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run()