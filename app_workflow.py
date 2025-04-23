"""
Simple script to run the Flask application for testing in the Replit environment.
This is a wrapper script to start the app.py Flask application.
"""

from flask import Flask
import threading
import app

def run():
    """
    Run the Flask application.
    """
    # The app is already created and configured in app.py
    # We just need to run it
    app.app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()