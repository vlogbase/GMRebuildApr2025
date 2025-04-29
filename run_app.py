"""
Replit Workflow for the Flask chat application.
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
    
    # Run the app on port 5000 and listen on all interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    run()