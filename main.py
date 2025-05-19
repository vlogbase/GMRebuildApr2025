"""
Main entry point for the application
This file imports the Flask app instance from app.py
"""
import os
from app import app

# Set the session cookie name explicitly to fix deployment issues
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'gloria_mundo_session:'
app.session_cookie_name = 'gloria_mundo_session'

# This ensures that the app is available for Gunicorn
# as specified in the .replit configuration file
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)