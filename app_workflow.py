"""
Simple script to run the Flask application for testing in the Replit environment.
This is a wrapper script to start the app.py Flask application.
"""

import os
import sys

def run():
    """
    Run the Flask application.
    """
    # Set Flask development mode
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Import the app after setting environment variables
    from app import app
    
    # Run the app on port 3000 and listen on all interfaces
    app.run(host='0.0.0.0', port=3000, debug=True)

if __name__ == '__main__':
    run()