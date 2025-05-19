"""
Main entry point for the application
This file imports the Flask app instance from app.py
"""
from app import app

# This ensures that the app is available for Gunicorn
# as specified in the .replit configuration file
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)