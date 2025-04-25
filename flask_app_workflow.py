"""
Simple script to run the Flask application for testing in the Replit environment.
This is a wrapper script to start the app.py Flask application.
"""
import os
import sys
from app import app

def run():
    """
    Run the Flask application.
    """
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()