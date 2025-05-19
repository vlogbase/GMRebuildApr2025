"""
Main entry point for the application
This file imports the Flask app instance from app.py
"""
import os
import logging
from flask_session import Session
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set session configuration
logger.info("Configuring Flask session")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'gloria_mundo_session:'
app.config['SESSION_COOKIE_NAME'] = 'gloria_mundo_session'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')

# Initialize Flask-Session
Session(app)
logger.info("Flask session initialized")

# This ensures that the app is available for Gunicorn
# as specified in the .replit configuration file
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)