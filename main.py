"""
Main entry point for the application
This file imports the Flask app instance from app.py
"""
from app import app

# This ensures that the app is available for Gunicorn
# as specified in the .replit configuration file
if __name__ == "__main__":
    # Use port 3000 for both local development and deployment
    app.run(host='0.0.0.0', port=3000, debug=True)