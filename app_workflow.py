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
            db.session.execute(db.select(db.text('1'))).scalar()  # Test DB connection
            print("Database connection successful")
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
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
        
        # Ensure we have an app context for database operations
        ensure_app_context()
        
        # Run the app - use environment variable for port if available
        port = int(os.environ.get('PORT', 5000))
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