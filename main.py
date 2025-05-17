"""
Main module for GloriaMundo application

This file serves as an entry point for the application when deployed.
It simply imports the app instance from app.py for gunicorn to use.
"""
from app import app

# This allows gunicorn to find the app instance via 'main:app'
if __name__ == "__main__":
    # Run the app directly if this file is executed
    app.run(host='0.0.0.0', port=5000)