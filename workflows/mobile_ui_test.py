"""
Test workflow for the mobile UI improvements.
"""
import os
import sys
import time
from flask import Flask

def run():
    """
    Run the Flask application in debug mode.
    
    This will allow us to test the mobile features by accessing the application
    from a mobile device or using the browser's mobile emulation mode.
    """
    # Import the app to run it
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Print a message to help with testing
    print("\n=== MOBILE UI TEST WORKFLOW ===")
    print("1. Access this app from a mobile device or")
    print("2. Use your browser's dev tools to emulate a mobile device")
    print("3. Test the long-press on model preset buttons")
    print("4. Test the sidebar toggle and menu\n")
    
    # Import and run the app
    try:
        from app import app
        
        # Set some Flask configuration for testing
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        
        # Run the Flask application
        print("\n=== Starting Flask server... ===\n")
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
        
    except Exception as e:
        print(f"Error starting the Flask application: {e}")
        raise

if __name__ == "__main__":
    run()