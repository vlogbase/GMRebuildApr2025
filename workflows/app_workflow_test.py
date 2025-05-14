"""
Test workflow for the main app with mobile UI improvements.
"""
import sys
import os
import signal
import time
from flask import Flask

def run():
    """Run the Flask application for testing."""
    # Add the root directory to the Python path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Import the app
    try:
        from app import app
        
        # Set debug to False to avoid auto-reloader issues
        app.config['DEBUG'] = False
        
        # Run the Flask application
        print("\n=== Starting GloriaMundo Chat application ===\n")
        print("Access the application to test mobile features:\n")
        
        try:
            app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
        except KeyboardInterrupt:
            print("Server stopped by user")
        except Exception as e:
            print(f"Server error: {e}")
            
    except Exception as e:
        print(f"Error importing app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()