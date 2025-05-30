#!/usr/bin/env python3
"""
Test workflow for the share conversation fix
"""

def run():
    """
    Run the Flask application to test the share conversation fix
    """
    import os
    import sys
    
    # Add current directory to Python path
    sys.path.insert(0, os.getcwd())
    
    # Import and run the Flask app
    from app import app
    
    print("Starting Flask app to test share conversation fix...")
    print("The fix includes:")
    print("- Better database session management")
    print("- Retry logic for unique constraint violations")
    print("- More robust error handling")
    print("- Proper rollback on failures")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()