"""
Simple Flask server workflow to test the PayPal email update functionality
"""

import os
from app import app

def run():
    """
    Run the Flask application for testing the PayPal email update
    """
    # Clear any cached static files
    with app.app_context():
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    # Use 0.0.0.0 to make the server accessible externally
    # Use port 5000 by default or the environment's port
    port = int(os.environ.get('PORT', 5000))
    
    # Run the development server
    app.run(host='0.0.0.0', port=port, debug=True)